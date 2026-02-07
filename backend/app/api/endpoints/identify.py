"""
On-demand product identification endpoint.
Called when user clicks a bounding box to get specific product info via SerpAPI Lens.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import base64

from app.services.image_crop import crop_to_bounding_box
from app.services.lens_identify import identify_product_with_lens

router = APIRouter()


class IdentifyRequest(BaseModel):
    """Request to identify a specific object in an image."""
    image_base64: str  # Full image as base64
    bounding_box: List[int]  # [ymin, xmin, ymax, xmax] normalized 0-1000
    object_index: int = 0  # Index of object being identified (for caching)


class IdentifyResponse(BaseModel):
    """Response with identified product information."""
    product_name: str
    confidence: float
    source: Optional[str] = None
    link: Optional[str] = None
    visual_matches_count: int = 0
    shopping_results_count: int = 0
    timing: Optional[Dict[str, float]] = None
    error: Optional[str] = None


@router.post("/identify", response_model=IdentifyResponse)
async def identify_object(request: IdentifyRequest):
    """
    Identify a specific object in an image using SerpAPI Google Lens.
    
    This endpoint is called on-demand when user clicks a bounding box,
    rather than processing all objects during initial analysis.
    """
    import time
    start_time = time.time()
    
    print(f"[Identify Endpoint] Called with bbox: {request.bounding_box}")
    
    try:
        # Clean base64 if needed
        image_data = request.image_base64
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        print(f"[Identify Endpoint] Image data length: {len(image_data)}")
        
        # Decode image
        decode_start = time.time()
        image_bytes = base64.b64decode(image_data)
        decode_time = time.time() - decode_start
        
        # Crop to bounding box
        crop_start = time.time()
        cropped_bytes = crop_to_bounding_box(image_bytes, request.bounding_box)
        crop_time = time.time() - crop_start
        print(f"[Identify Endpoint] Cropped image size: {len(cropped_bytes)} bytes")
        
        # Call SerpAPI Lens
        print("[Identify Endpoint] Calling Lens...")
        result = identify_product_with_lens(cropped_bytes, "jpg")
        print(f"[Identify Endpoint] Lens result: {result}")
        
        total_time = time.time() - start_time
        print(f"[Identify Endpoint] Total time: {total_time:.2f}s (Decode: {decode_time:.2f}s, Crop: {crop_time:.2f}s)")
        
        if "error" in result:
            return IdentifyResponse(
                product_name="Unknown",
                confidence=0.0,
                error=result["error"]
            )
        
        return IdentifyResponse(
            product_name=result.get("product_name", "Unknown"),
            confidence=result.get("confidence", 0.0),
            source=result.get("source"),
            link=result.get("link"),
            visual_matches_count=result.get("visual_matches_count", 0),
            shopping_results_count=result.get("shopping_results_count", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
