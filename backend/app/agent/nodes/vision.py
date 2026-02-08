from typing import Dict, Any
import base64
from app.agent.state import AgentState
from app.services.lens_identify import identify_product_with_lens

def node_user_intent_vision(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: User Intent & Vision (The "Eye")
    
    Uses Google Lens (via SerpAPI) for accurate product identification.
    Provides knowledge graph matches, visual matches, and shopping results.
    
    Input: state['image_base64'], state['user_query']
    Output: state update with 'product_query'
    """
    log_file = "/app/debug_output.txt"
    
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except:
            pass

    log_debug("--- 1. Executing Vision Node (Google Lens Mode) ---")
    print("--- 1. Executing Vision Node (Google Lens Mode) ---")

    image_data = state.get("image_base64")
    user_query = state.get("user_query", "")

    if not image_data:
        return {"product_query": {"error": "No image provided"}}


    # CHECK FOR SKIP FLAG (Stage 2 of Two-Stage Pipeline)
    if state.get("skip_vision"):
        print("--- Vision Node: SKIPPING (Deep Analysis Mode) ---")
        return {} # Pass-through, no changes to state

    import time
    start_time = time.time()
    
    # Extract base64 (handle data URL)
    if "base64," in image_data:
        image_data = image_data.split("base64,")[1]
    
    # ---------------------------------------------------------
    # STAGE 1: FAST DETECTION (Gemini)
    # ---------------------------------------------------------
    # Helper for Gemini Vision (Fast Mode / Fallback)
    def _run_gemini_vision(image_b64):
        log_debug("--- Executing Vision: Gemini Mode ---")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            from app.core.config import settings
            import json
            
            if not settings.GOOGLE_API_KEY:
                 return {"product_query": {"error": "GOOGLE_API_KEY missing"}}

            llm = ChatGoogleGenerativeAI(
                model=settings.MODEL_VISION,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.4,
                max_output_tokens=1024
            )
            
            # Enhanced Prompt for Fallback & OCR
            prompt = """
            Analyze this image for a shopping assistant.
            1. Identify the main commercial product.
            2. Transcribe any visible TEXT, model numbers, or brand names (OCR).
            3. Detect visual attributes (color, material, style).
            
            CRITICAL NEGATIVE CONSTRAINTS:
            - DO NOT DETECT PEOPLE, FACES, BODY PARTS.
            - Ignore background clutter.
            
            Return JSON:
            {
                "detected_objects": [
                    {
                        "name": "Generic Name (e.g. 'Blue Running Shoes')",
                        "bounding_box": [ymin, xmin, ymax, xmax],
                        "confidence": 0.0-1.0
                    }
                ],
                "main_product_name": "Specific Model Name if visible, else Generic Name",
                "visual_attributes": "comma-separated keywords",
                "ocr_text": "extracted text"
            }
            """
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            )
            
            response = llm.invoke([message])
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            data = json.loads(content)
            
            # Map to State Structure
            return {
                "product_query": {
                    "canonical_name": data.get("main_product_name", "Unknown Product"),
                    "visual_attributes": data.get("visual_attributes", ""),
                    "detected_objects": data.get("detected_objects", []),
                    "ocr_text": data.get("ocr_text", ""),
                    "source": "gemini_vision"
                },
                "bounding_box": [0, 0, 1000, 1000]
            }
            
        except Exception as e:
            log_debug(f"Gemini Vision Error: {e}")
            return {"product_query": {"error": str(e)}}

    # ---------------------------------------------------------
    # STAGE 1: FAST DETECTION (Gemini)
    # ---------------------------------------------------------
    if state.get("detect_only"):
        return _run_gemini_vision(image_data)

    # ---------------------------------------------------------
    # STAGE 2: DEEP IDENTIFICATION (Google Lens)
    # ---------------------------------------------------------
    
    image_bytes = base64.b64decode(image_data)
    
    log_debug("Sending request to Google Lens via SerpAPI...")
    
    # Call Google Lens for product identification
    lens_result = identify_product_with_lens(image_bytes, extension="jpg")
    
    if "error" in lens_result:
        log_debug(f"Lens error: {lens_result['error']} -> FALLING BACK TO GEMINI")
        return _run_gemini_vision(image_data)
    
    product_name = lens_result.get("product_name", "Unknown Product")
    confidence = lens_result.get("confidence", 0.5)
    source = lens_result.get("source", "lens")
    
    log_debug(f"Google Lens identified: {product_name} (confidence: {confidence})")
    
    # Create a detected object from Lens result
    detected_objects = [{
        "name": product_name,
        "bounding_box": [0, 0, 1000, 1000],  # Full image as bounding box
        "confidence": confidence,
        "lens_status": "identified",
        "source": source,
        "link": lens_result.get("link")
    }]
    
    total_time = time.time() - start_time
    print(f"--- Vision Node: Total time {total_time:.2f}s ---")
    
    # Get existing timings and add this node's time
    existing_timings = state.get('node_timings', {}) or {}
    existing_timings['vision'] = total_time
    
    return {
        "product_query": {
            "canonical_name": product_name,
            "visual_attributes": "",  # Lens doesn't provide this directly
            "context": f"Identified via Google Lens ({source}). "
                       f"Visual matches: {lens_result.get('visual_matches_count', 0)}, "
                       f"Shopping results: {lens_result.get('shopping_results_count', 0)}",
            "detected_objects": detected_objects,
            "lens_confidence": confidence,
            "lens_source": source,
        },
        "bounding_box": [0, 0, 1000, 1000],
        "node_timings": existing_timings
    }
