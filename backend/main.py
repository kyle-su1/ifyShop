import os
import base64
import json
import io
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from pillow_heif import register_heif_opener

# Initialize environment and HEIC support
load_dotenv()
register_heif_opener()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Client
openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_OPENAI_API_KEY"),
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "VisionBackend",
    },
)

class AnalyzeRequest(BaseModel):
    imageBase64: str

@app.post("/api/analyze")
async def analyze_image(request: AnalyzeRequest):
    print("\n--- New Request Received (Python Backend) ---")
    
    if not openai_client.api_key:
        raise HTTPException(status_code=500, detail="API Key not found. Please check your .env file.")

    if not request.imageBase64:
        raise HTTPException(status_code=400, detail="No image data provided")

    try:
        # 1. Decode and Process Image
        # Strip header if present
        base64_data = request.imageBase64
        if "base64," in base64_data:
            base64_data = base64_data.split("base64,")[1]
            
        image_data = base64.b64decode(base64_data)
        
        # Open image using Pillow (supports HEIC via pillow_heif)
        image = Image.open(io.BytesIO(image_data))
        print(f"Original Image Format: {image.format}, Size: {image.size}")

        # Convert to RGB (standardize)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize if too large (max 2048x2048)
        max_dimension = 2048
        if max(image.size) > max_dimension:
            image.thumbnail((max_dimension, max_dimension))
            print(f"Resized to: {image.size}")

        # Save to JPEG buffer
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=85)
        optimized_base64 = base64.b64encode(output_buffer.getvalue()).decode("utf-8")
        
        print(f"Image optimized. Sending to OpenRouter (gpt-4o)...")

        # 2. Call OpenAI / OpenRouter
        system_prompt = """
            You are an expert object detection and identification system.
            
            TASK: Detect ALL objects in the image and identify them with maximum specificity.
            
            For EACH object:
            1. "name": Look for visible text, logos, or distinctive features to identify:
               - BEST: Exact brand + model (e.g., "Boston Dynamics Spot", "DeWalt DCD771C2 Drill")
               - GOOD: Brand + type (e.g., "DeWalt Cordless Drill", "WEN Band Saw")
               - FALLBACK: Descriptive name only if no branding visible (e.g., "Yellow Robotic Dog", "Red Fire Extinguisher")
            
            2. "confidence": Your confidence in the detection (0.0 to 1.0):
               - 0.95-1.0 = Very clear, unobstructed, well-lit object
               - 0.85-0.94 = Clear but partially occluded or at angle
               - 0.70-0.84 = Visible but small, distant, or unclear
               - Below 0.70 = Uncertain identification
            
            3. "box": Bounding box in STANDARD CV FORMAT [y_min, x_min, y_max, x_max] where:
               - ALL values are decimals from 0.0 to 1.0 (normalized coordinates)
               - y_min = distance from TOP edge to TOP of box (0.0 = top of image)
               - x_min = distance from LEFT edge to LEFT of box (0.0 = left of image)
               - y_max = distance from TOP edge to BOTTOM of box (1.0 = bottom of image)
               - x_max = distance from LEFT edge to RIGHT of box (1.0 = right of image)
            
            Return ONLY valid JSON: {"objects": [{"name": "...", "confidence": 0.95, "box": [y_min, x_min, y_max, x_max]}]}
        """

        response = openai_client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Detect and identify all objects."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{optimized_base64}",
                                "detail": "high"
                            },
                        },
                    ],
                },
            ],
            max_tokens=1500,
        )

        content = response.choices[0].message.content
        print("OpenAI Raw Response (truncated):", content[:200] + "...")

        # 3. Parse and Map Response
        clean_content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_content)
        
        mapped_objects = []
        for obj in result.get("objects", []):
            # Handle box format
            box = obj.get("box") or obj.get("box_2d")
            ymin, xmin, ymax, xmax = box
            
            # Normalize if needed (0-1000 scale)
            if ymin > 1 or xmin > 1 or ymax > 1 or xmax > 1:
                ymin /= 1000; xmin /= 1000; ymax /= 1000; xmax /= 1000

            # Clamp
            ymin = max(0, min(1, ymin))
            xmin = max(0, min(1, xmin))
            ymax = max(0, min(1, ymax))
            xmax = max(0, min(1, xmax))

            mapped_objects.append({
                "name": obj["name"],
                "score": obj.get("confidence", 0.95),
                "openAiLabel": obj["name"],
                "boundingPoly": {
                    "normalizedVertices": [
                        { "x": xmin, "y": ymin },
                        { "x": xmax, "y": ymin },
                        { "x": xmax, "y": ymax },
                        { "x": xmin, "y": ymax }
                    ]
                }
            })

        print(f"Successfully mapped {len(mapped_objects)} objects.")
        
        return {
            "objects": mapped_objects,
            "labels": []
        }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Clean start
    print("Starting FastAPI Backend on port 3001...")
    uvicorn.run(app, host="0.0.0.0", port=3001)
