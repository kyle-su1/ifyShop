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

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    """
    Analyzes an uploaded image using the LangGraph agent.
    """
    if not agent_app:
        return {"error": "Agent not initialized"}

    print(f"Received request for image analysis. Query: {request.user_query}")
    
    # Initialize the state with inputs
    initial_state = {
        "user_query": request.user_query,
        "image_base64": request.image,
        "user_preferences": request.user_preferences,
        # Other state keys will be populated by the graph
    }
    
    # Generate a unique thread_id for this request (required by MemorySaver)
    import uuid
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph asynchronously
    result = await agent_app.ainvoke(initial_state, config=config)
    
    # The result contains the final state, so we return the final_recommendation
    return result.get("final_recommendation", {"error": "No recommendation generated"})
