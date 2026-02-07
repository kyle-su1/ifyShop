# Load environment variables FIRST, before any imports that need them
import os
from pathlib import Path
from dotenv import load_dotenv

# Find the .env file in the backend directory (parent of 'app')
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

app = FastAPI(title="Shopping Suggester API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.db.session import engine
from app.db.base import Base
from app.api.api import api_router

# Import the agent graph
try:
    from app.agent.graph import agent_app
except Exception as e:
    import traceback
    print(f"CRITICAL ERROR: Could not import agent_app: {e}")
    traceback.print_exc()
    agent_app = None

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

class AnalyzeRequest(BaseModel):
    image: str  # base64 string
    user_preferences: Dict[str, float]
    user_query: str
    detect_only: bool = False  # Stage 1: Detect objects and stop
    skip_vision: bool = False  # Stage 2: Resume analysis (skip detection)
    product_name: str = ""     # Stage 2: Specific product to analyze

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    """
    Analyzes an uploaded image using the LangGraph agent.
    """
    if not agent_app:
        return {"error": "Agent not initialized"}

    print(f"Received request for image analysis. Query: {request.user_query}")
    print(f"   Flags: detect_only={request.detect_only}, skip_vision={request.skip_vision}, product={request.product_name}")
    
    # Initialize the state with inputs
    initial_state = {
        "user_query": request.user_query,
        "image_base64": request.image,
        "user_preferences": request.user_preferences,
        "detect_only": request.detect_only,
        "skip_vision": request.skip_vision,
        # Other state keys will be populated by the graph
    }
    
    # If skip_vision is True, we might want to manually inject the product_query
    if request.skip_vision and request.product_name:
        initial_state["product_query"] = {
            "canonical_name": request.product_name,
            "detected_objects": [], # Skipped detection
            "context": "User provided product name via Lens identification"
        }
    
    # Generate a unique thread_id for this request (required by MemorySaver)
    import uuid
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph asynchronously
    result = await agent_app.ainvoke(initial_state, config=config)
    
    # The result contains the final state.
    # In 'detect_only' mode, we won't have 'final_recommendation', but we will have 'product_query'.
    if request.detect_only:
        pq = result.get("product_query", {})
        print(f"DEBUG: Returning product_query: {pq.keys() if pq else 'None'}")
        if pq and 'detected_objects' in pq:
            print(f"DEBUG: detected_objects count: {len(pq['detected_objects'])}")
        return result.get("product_query", {"error": "No objects detected"})
        
    return result.get("final_recommendation", {"error": "No recommendation generated"})
