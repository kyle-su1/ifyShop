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
    if state.get("detect_only"):
        log_debug("--- 1. Executing Vision Node (Gemini Fast Mode) ---")
        print("--- 1. Executing Vision Node (Gemini Fast Mode) ---", flush=True)
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            from app.core.config import settings
            import json
            
            log_debug("Sending request to Gemini...")
            print("Sending request to Gemini...", flush=True)
            
            # Check API Key
            if not settings.GOOGLE_API_KEY:
                 print("ERROR: GOOGLE_API_KEY is missing", flush=True)
                 raise ValueError("GOOGLE_API_KEY is missing")

            llm = ChatGoogleGenerativeAI(
                model=settings.MODEL_VISION,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.4,
                max_output_tokens=1024
            )
            
            prompt = """
            Identify the main commercial *products* in this image.
            
            CRITICAL NEGATIVE CONSTRAINTS (STRICTLY ENFORCED):
            - DO NOT DETECT PEOPLE, FACES, MEN, WOMEN, CHILDREN.
            - DO NOT DETECT BODY PARTS (hands, arms, legs, feet, fingers).
            - DO NOT bounding box a person holding an object; box ONLY the object itself.
            - If an object is held, the bounding box must exclude the hand/fingers.
            - Ignore background clutter, windows, and non-product elements.
            
            Return a JSON object with a key "detected_objects" containing a list of objects.
            Each object should have:
            - "name": generic name of the object (e.g. "shoes", "keyboard")
            - "bounding_box": [ymin, xmin, ymax, xmax] coordinates normalized to 0-1000 scale.
            - "confidence": score between 0.0 and 1.0.
            Limit to top 5 prominent objects.
            """
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            )
            
            response = llm.invoke([message])
            content = response.content.strip()
            
            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            gemini_data = json.loads(content)
            
            # Validate bounding boxes
            detected_objects = gemini_data.get('detected_objects', [])
            log_debug(f"Gemini detected {len(detected_objects)} objects")
            print(f"Gemini detected {len(detected_objects)} objects", flush=True)
            
            total_time = time.time() - start_time
            print(f"Gemini API took {total_time:.2f}s", flush=True)
            
            return {
                "product_query": {
                    "canonical_name": "Detected Objects",
                    "detected_objects": detected_objects # specific boxes
                },
                "bounding_box": [0, 0, 1000, 1000] # Fallback
            }
            
        except Exception as e:
            log_debug(f"Vision error: {str(e)}")
            print(f"Vision error: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            # Fallback to single box on error
            return {
                "product_query": {
                    "error": str(e),
                    "detected_objects": [{
                        "name": "Detection Failed",
                        "bounding_box": [0, 0, 1000, 1000],
                        "confidence": 0.0,
                        "lens_status": "error"
                    }]
                }
            }

    # ---------------------------------------------------------
    # STAGE 2: DEEP IDENTIFICATION (Google Lens)
    # ---------------------------------------------------------
    
    image_bytes = base64.b64decode(image_data)
    
    log_debug("Sending request to Google Lens via SerpAPI...")
    
    # Call Google Lens for product identification
    lens_result = identify_product_with_lens(image_bytes, extension="jpg")
    
    if "error" in lens_result:
        log_debug(f"Lens error: {lens_result['error']}")
        return {"product_query": {
            "error": lens_result["error"],
            "canonical_name": "Unknown Item",
            "detected_objects": []
        }}
    
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
