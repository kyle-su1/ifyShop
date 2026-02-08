import os
import base64
import json
import io
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.core.security import get_current_user
from app.models.user import User
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
async def analyze_image(request: ImageAnalysisRequest, current_user: User = Depends(get_current_user)):
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
        "user_id": str(current_user.id),  # Authenticated User ID
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


class ChatAnalyzeRequest(BaseModel):
    """Request for chat-based targeted object analysis."""
    image_base64: str
    user_query: str
    chat_history: List[dict] = []
    user_id: Optional[str] = None # Auth0 User ID


class ChatAnalyzeResponse(BaseModel):
    """Response with targeted object info and chat response."""
    chat_response: str
    targeted_object_name: Optional[str] = None
    targeted_bounding_box: Optional[List[float]] = None  # [ymin, xmin, ymax, xmax]
    confidence: Optional[float] = None
    analysis: Optional[dict] = None
    thread_id: Optional[str] = None  # For follow-up conversations
    session_state: Optional[dict] = None  # Prior analysis state for follow-ups


@router.post("/chat-analyze", response_model=ChatAnalyzeResponse)
async def chat_analyze(request: ChatAnalyzeRequest, current_user: User = Depends(get_current_user)):
    """
    Chat-based targeted object analysis with FULL pipeline.
    
    Flow:
    1. Gemini Vision finds target object + bounding box
    2. Crop image to bounding box
    3. SerpAPI Lens identifies exact product
    4. Invoke full agent workflow (Market Scout → Skeptic → Analysis → Response)
    5. Return complete recommendation in chat
    """
    import os
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    from app.services.image_crop import crop_to_bounding_box
    from app.services.lens_identify import identify_product_with_lens
    from app.services.snowflake_cache import snowflake_cache_service
    
    print(f"\n[ChatAnalyze] Query: {request.user_query}")
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    # Clean base64 string
    base64_data = request.image_base64
    if "base64," in base64_data:
        base64_data = base64_data.split("base64,")[1]
    
    try:
        # =====================================================
        # STEP 1: Use Gemini Vision to find target object
        # =====================================================
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        system_prompt = """You are a visual shopping assistant. The user is asking about a specific item in an image.

Task:
1. Identify the object the user is asking about
2. Return its bounding box location

Return JSON with:
- "target_object": descriptive name of the object
- "bounding_box": [y_min, x_min, y_max, x_max] as values 0-1000 (normalized)
- "confidence": 0.0-1.0

Return ONLY valid JSON, no markdown."""

        message = HumanMessage(
            content=[
                {"type": "text", "text": f"{system_prompt}\n\nUser Query: {request.user_query}"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}
                }
            ]
        )
        
        response = await llm.ainvoke([message])
        response_text = response.content.strip()
        
        # Clean markdown
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) >= 3 else response_text
        
        vision_result = json.loads(response_text)
        target_name = vision_result.get("target_object", "Unknown")
        bbox = vision_result.get("bounding_box")
        
        print(f"[ChatAnalyze] Target: {target_name}, BBox: {bbox}")
        
        if not bbox:
            return ChatAnalyzeResponse(
                chat_response=f"I couldn't find '{request.user_query}' in the image. Could you describe it differently?",
                targeted_object_name=None,
                targeted_bounding_box=None
            )
        
        # =====================================================
        # STEP 2: Crop image and identify with Google Lens
        # =====================================================
        image_bytes = base64.b64decode(base64_data)
        
        # Convert bbox from 0-1 to 0-1000 if needed
        if all(0 <= v <= 1 for v in bbox):
            bbox = [int(v * 1000) for v in bbox]
        
        cropped_bytes = crop_to_bounding_box(image_bytes, bbox)
        lens_result = identify_product_with_lens(cropped_bytes, "jpg")
        
        product_name = lens_result.get("product_name", target_name)
        print(f"[ChatAnalyze] Lens ID: {product_name}")
        
        # =====================================================
        # STEP 2b: Check Snowflake Cache
        # =====================================================
        cached_result = None
        if product_name and product_name != "Unknown":
            cache_key = snowflake_cache_service.generate_key(product_name)
            print(f"[ChatAnalyze] Checking cache for: {cache_key}")
            cached_result = snowflake_cache_service.get(cache_key)
            print(f"[ChatAnalyze] Cache Get Result: {'HIT' if cached_result else 'MISS'}")
            print(f"[ChatAnalyze] Cache Get Result: {'HIT' if cached_result else 'MISS'}")
            
        if cached_result:
            try:
                print(f"[ChatAnalyze] CACHE HIT! Processing stored analysis.")
                if not isinstance(cached_result, dict):
                    raise ValueError(f"Cached result is not a dict: {type(cached_result)}")
                
                full_result = cached_result
                
                # Inject current specific vision data into the cached result 
                if 'active_product' in full_result and isinstance(full_result['active_product'], dict):
                     full_result['active_product']['bounding_box'] = bbox
                     full_result['active_product']['detected_objects'] = [{
                        "name": product_name, 
                        "bounding_box": bbox,
                        "lens_result": lens_result
                     }]
                
                # Synthesize final state wrapper for response formatting
                import uuid
                thread_id = str(uuid.uuid4()) # Fake thread ID for cache hit
                
                final_state = {
                    "final_recommendation": full_result,
                    "market_scout_data": {}, 
                    "research_data": {},
                    "risk_report": {},
                    "analysis_object": {},
                    "product_query": {
                        "canonical_name": product_name,
                        "detected_objects": [{
                            "name": product_name,
                            "bounding_box": bbox,
                            "lens_result": lens_result
                        }],
                        "context": "User identified via chat + Lens"
                    }
                }
            except Exception as e:
                print(f"[ChatAnalyze] Error processing cache hit: {e}")
                cached_result = None # Fallback to miss
                
        if not cached_result:
            print(f"[ChatAnalyze] Cache Miss (or Error). Invoking full agent workflow.")
            
            # =====================================================
            # STEP 3: Invoke full agent workflow
            # =====================================================
            from app.agent.graph import agent_app
            import uuid
            
            initial_state = {
                "user_query": f"Find the best deals for: {product_name}",
                "image_base64": base64_data,
                "user_preferences": {},
                "user_id": str(current_user.id), # Authenticated User ID
                "product_query": {
                    "canonical_name": product_name,
                    "detected_objects": [{
                        "name": product_name,
                        "bounding_box": bbox,
                        "lens_result": lens_result
                    }],
                    "context": "User identified via chat + Lens"
                },
                "skip_vision": True  # Skip vision node, we already have product
            }
            
            # Generate unique thread_id (required by MemorySaver)
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            
            final_state = await agent_app.ainvoke(initial_state, config=config)
            full_result = final_state.get("final_recommendation", {})
        
        print(f"[ChatAnalyze] Pipeline complete. Outcome: {full_result.get('outcome', 'unknown')}")
        
        # =====================================================
        # STEP 4: Format response for chat
        # =====================================================
        summary = full_result.get("summary", f"I found the {product_name}!")
        
        # Build chat response with key info
        chat_response = f"**{product_name}**\n\n{summary}"
        
        if full_result.get("active_product", {}).get("price"):
            chat_response += f"\n\n💰 Price: {full_result['active_product']['price']}"
        
        # Normalize bbox back to 0-1 for frontend
        normalized_bbox = [v / 1000.0 for v in bbox] if bbox else None
        
        # Build session state for follow-ups (includes data needed for re-analysis)
        session_state = {
            "product_query": final_state.get("product_query"),
            "market_scout_data": final_state.get("market_scout_data"),
            "research_data": final_state.get("research_data"),
            "risk_report": final_state.get("risk_report"),
            "analysis_object": final_state.get("analysis_object"),
        }
        
        return ChatAnalyzeResponse(
            chat_response=chat_response,
            targeted_object_name=product_name,
            targeted_bounding_box=normalized_bbox,
            confidence=lens_result.get("confidence", 0.8),
            analysis=full_result,
            thread_id=thread_id,  # Return for follow-up persistence
            session_state=session_state  # Prior state for re-analysis
        )
        
    except json.JSONDecodeError as e:
        print(f"[ChatAnalyze] JSON parse error: {e}")
        return ChatAnalyzeResponse(
            chat_response="I had trouble understanding the image. Please try again.",
            targeted_object_name=None,
            targeted_bounding_box=None
        )
    except Exception as e:
        print(f"[ChatAnalyze] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================================
# CHAT FOLLOW-UP ENDPOINT (Node 6: Conversational Loop)
# ============================================================

class ChatFollowupRequest(BaseModel):
    """Request for follow-up questions after initial analysis."""
    user_query: str
    thread_id: str  # Required for state persistence
    session_state: dict  # Prior analysis state (from initial chat-analyze)
    chat_history: List[dict] = []
    user_id: Optional[str] = None # Auth0 User ID


class ChatFollowupResponse(BaseModel):
    """Response from follow-up with potentially updated analysis."""
    chat_response: str
    analysis: Optional[dict] = None  # Updated analysis if re-scored
    intent: str  # What the router decided: 're_analysis', 're_search', 'chat'


@router.post("/chat-followup", response_model=ChatFollowupResponse)
async def chat_followup(request: ChatFollowupRequest, current_user: User = Depends(get_current_user)):
    """
    Handle follow-up questions after initial analysis.
    
    Routes based on intent:
    - re_analysis: User wants cheaper/different scoring → Re-run Node 4
    - re_search: User wants different products (color, brand) → Re-run Node 2
    - chat: General question → Just respond
    """
    from app.agent.graph import agent_app
    import uuid
    
    print(f"\n[ChatFollowup] Query: {request.user_query}")
    print(f"[ChatFollowup] Thread: {request.thread_id}")
    
    try:
        # Build state from prior session
        initial_state = {
            "user_query": request.user_query,
            "image_base64": "",  # No new image
            "user_preferences": {},
            "user_id": str(current_user.id), # Authenticated User ID
            "chat_history": request.chat_history,
            # Restore prior analysis state
            "product_query": request.session_state.get("product_query", {}),
            "market_scout_data": request.session_state.get("market_scout_data", {}),
            "research_data": request.session_state.get("research_data", {}),
            "risk_report": request.session_state.get("risk_report", {}),
            "analysis_object": request.session_state.get("analysis_object", {}),
            # Skip vision - we already have the product
            "skip_vision": True,
        }
        
        # Use same thread_id for state continuity
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Invoke the graph (starts at Router Node)
        final_state = await agent_app.ainvoke(initial_state, config=config)
        
        # Extract results
        router_decision = final_state.get("router_decision", "chat")
        final_rec = final_state.get("final_recommendation", {})
        
        print(f"[ChatFollowup] Final State Keys: {final_state.keys()}")
        print(f"[ChatFollowup] Final Recommendation Keys: {final_rec.keys()}")
        
        chat_response = final_rec.get("chat_response", "")
        
        # If re-analysis occurred, get the updated analysis
        updated_analysis = None
        if router_decision in ["re_analysis", "re_search"]:
            updated_analysis = final_rec
            if not chat_response:
                chat_response = "I've updated the recommendations based on your preferences."
        
        if not chat_response:
            chat_response = "I'm not sure how to help with that. Can you rephrase?"
        
        print(f"[ChatFollowup] Intent: {router_decision}")
        print(f"[ChatFollowup] Has Updated Analysis: {bool(updated_analysis)}")
        
        return ChatFollowupResponse(
            chat_response=chat_response,
            analysis=updated_analysis,
            intent=router_decision
        )
        
    except Exception as e:
        print(f"[ChatFollowup] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Follow-up failed: {str(e)}")
