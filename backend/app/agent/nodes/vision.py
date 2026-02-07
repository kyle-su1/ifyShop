from typing import Dict, Any
import os
import json
import base64
import google.generativeai as genai
from app.agent.state import AgentState

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def node_user_intent_vision(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: User Intent & Vision (The "Eye")
    
    Uses Gemini for FAST bounding box detection.
    Lens identification is done on-demand when user clicks a box.
    
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

    log_debug("--- 1. Executing Vision Node (Gemini Fast Mode) ---")
    print("--- 1. Executing Vision Node (Gemini Fast Mode) ---")

    image_data = state.get("image_base64")
    user_query = state.get("user_query", "")

    if not GOOGLE_API_KEY:
        return {"product_query": {"error": "GOOGLE_API_KEY not configured"}}

    if not image_data:
        return {"product_query": {"error": "No image provided"}}

    import time
    start_time = time.time()
    
    try:
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        image_bytes = base64.b64decode(image_data)
        
        model = genai.GenerativeModel('gemini-2.0-flash')

        prompt = """
        Analyze this image and detect all distinct objects or products.
        For EACH object, provide a brief name and bounding box.
        
        Return ONLY a JSON object:
        {
            "detected_objects": [
                {
                    "name": "Brief description",
                    "bounding_box": [ymin, xmin, ymax, xmax]
                }
            ],
            "primary_product": "Name of main/largest product",
            "context": "Any visible text like price, brand"
        }
        
        bounding_box coordinates are normalized 0-1000.
        """

        log_debug("Sending request to Gemini...")
        gemini_start = time.time()
        response = model.generate_content([
            {'mime_type': 'image/jpeg', 'data': image_bytes},
            prompt
        ])
        gemini_time = time.time() - gemini_start
        log_debug(f"Gemini API took {gemini_time:.2f}s")
        print(f"--- Vision Node: Gemini API took {gemini_time:.2f}s ---")
        
        content = response.text.replace('```json', '').replace('```', '').strip()
        gemini_data = json.loads(content)
        
        detected_objects = gemini_data.get('detected_objects', [])
        log_debug(f"Gemini detected {len(detected_objects)} objects")
        
        # Add pending status for Lens identification
        for obj in detected_objects:
            obj['lens_status'] = 'pending'  # Will be 'identified' after Lens call
            obj['confidence'] = 0.5  # Low confidence until Lens confirms
        
        total_time = time.time() - start_time
        print(f"--- Vision Node: Total time {total_time:.2f}s ---")
        
        return {
            "product_query": {
                "canonical_name": gemini_data.get('primary_product', 'Unknown'),
                "context": gemini_data.get('context', ''),
                "detected_objects": detected_objects,
            },
            "bounding_box": detected_objects[0].get('bounding_box') if detected_objects else None
        }

    except Exception as e:
        log_debug(f"Vision error: {str(e)}")
        total_time = time.time() - start_time
        print(f"--- Vision Node Failed after {total_time:.2f}s ---")
        return {"product_query": {
            "product_name": "Unknown Item",
            "context": f"Error: {str(e)}",
            "detected_objects": []
        }}


