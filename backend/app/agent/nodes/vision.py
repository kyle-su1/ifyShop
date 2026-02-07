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
    
    try:
        # Extract base64 data if it includes the data URL prefix
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

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
            "bounding_box": [0, 0, 1000, 1000]
        }

    except Exception as e:
        log_debug(f"Vision error: {str(e)}")
        total_time = time.time() - start_time
        print(f"--- Vision Node Failed after {total_time:.2f}s ---")
        return {"product_query": {
            "canonical_name": "Unknown Item",
            "context": f"Error: {str(e)}",
            "detected_objects": []
        }}
