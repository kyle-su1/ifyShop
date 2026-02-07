import os
import base64
import json
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
from PIL import Image
from pillow_heif import register_heif_opener

# Enable HEIC support
register_heif_opener()

router = APIRouter()

# Lazy-loaded OpenAI client (via OpenRouter)
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENROUTER_OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_OPENAI_API_KEY not found in environment")
        _openai_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "ShoppingSuggester",
            },
        )
    return _openai_client


class ImageAnalysisRequest(BaseModel):
    imageBase64: str


class DetectedObject(BaseModel):
    name: str
    score: float
    openAiLabel: Optional[str] = None
    boundingPoly: Optional[dict] = None


class ImageAnalysisResponse(BaseModel):
    objects: List[DetectedObject]
    labels: List[dict] = []


@router.post("/analyze-image")
async def analyze_image(request: ImageAnalysisRequest):
    """
    Trigger the Full Agent Workflow:
    1. Vision (Gemini 2.0 Flash)
    2. Research (Tavily)
    3. Market Scout
    4. Skeptic Analysis
    5. Final Response
    """
    print("\n--- Starting Full Agent Workflow ---")
    
    if not request.imageBase64:
        raise HTTPException(status_code=400, detail="No image data provided")

    # Clean base64 string
    base64_data = request.imageBase64
    if "base64," in base64_data:
        base64_data = base64_data.split("base64,")[1]

    # Initialize Agent State
    initial_state = {
        "user_query": "Identify this product and find the best price and alternatives.",
        "image_base64": base64_data,
        "user_preferences": {},  # Default preferences
        "product_query": {},
        "research_data": {},
        "market_scout_data": {},
        "risk_report": {},
        "analysis_object": {},
        "alternatives_analysis": [],
        "final_recommendation": {}
    }

    try:
        # Import the graph here to avoid circular dependencies at module level if any
        from app.agent.graph import agent_app
        
        # Invoke the graph
        # This runs all nodes: Vision -> Research/Scout -> Skeptic -> Analysis -> Response
        final_state = await agent_app.ainvoke(initial_state)
        
        result = final_state.get("final_recommendation", {})
        
        if not result:
            print("WARNING: Graph completed but returned empty final_recommendation.")
            # Fallback
            return {
                "outcome": "error",
                "summary": "The agent completed analysis but returned no data.",
                "active_product": {"name": "Unknown", "detected_objects": []}
            }
            
        return result

    except Exception as e:
        print(f"Error executing agent workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")


class RecommendationRequest(BaseModel):
    user_preferences: dict
    current_item_context: Optional[dict] = None


class RecommendationResponse(BaseModel):
    items: List[dict]


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_items(request: RecommendationRequest):
    # This endpoint can be used for follow-up refinements
    # For now, it's a placeholder or can reuse the graph with updated preferences
    return {
        "items": []
    }
