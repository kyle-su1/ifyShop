"""
SerpAPI Google Lens integration for product identification.
Uses ImgBB for fast, reliable image hosting.
"""
import requests
import base64
from typing import Dict, Any, Optional
from app.core.config import settings


def upload_to_imgbb(image_bytes: bytes) -> Optional[str]:
    """
    Upload image to ImgBB and get a public URL.
    
    ImgBB is fast and doesn't require ngrok.
    Get a free API key at: https://api.imgbb.com/
    """
    api_key = getattr(settings, 'IMGBB_API_KEY', None) or "YOUR_IMGBB_KEY"
    
    # If no API key, fall back to our own hosting
    if not api_key or api_key == "YOUR_IMGBB_KEY":
        return None
    
    try:
        # ImgBB accepts base64
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": api_key,
                "image": b64_image,
                "expiration": 600  # 10 minutes
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("url")
    except Exception as e:
        print(f"ImgBB upload failed: {e}")
    
    return None


def identify_product_with_lens(image_bytes: bytes, extension: str = "jpg") -> Dict[str, Any]:
    """
    Upload image and call SerpAPI Google Lens to identify the product.
    """
    log_file = "/app/debug_output.txt"
    
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[Lens] {str(message)}\n")
        except:
            pass
    
    api_key = settings.SERPAPI_API_KEY
    if not api_key:
        log_debug("Skipping Lens - No SERPAPI_API_KEY")
        return {"error": "SERPAPI_API_KEY not configured"}
    
    import time
    
    try:
        start_time = time.time()
        
        # Try ImgBB first (faster, more reliable)
        upload_start = time.time()
        public_url = upload_to_imgbb(image_bytes)
        upload_time = time.time() - upload_start
        log_debug(f"Image upload took {upload_time:.2f}s")
        
        if not public_url:
            # Fall back to our hosting
            from app.services.image_hosting import store_temp_image, get_public_image_url
            
            if "localhost" in settings.PUBLIC_BASE_URL:
                log_debug("Skipping Lens - PUBLIC_BASE_URL is localhost and no ImgBB key")
                return {"error": "No external image hosting available"}
            
            image_id = store_temp_image(image_bytes, extension)
            public_url = get_public_image_url(image_id)
        
        log_debug(f"Image stored: {public_url}")
        
        # Call SerpAPI Lens with retry
        params = {
            "engine": "google_lens",
            "url": public_url,
            "api_key": api_key,
            "hl": "en",
            "country": "ca"
        }
        
        # Retry logic for connection issues
        max_retries = 3
        response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                lens_start = time.time()
                response = requests.get(
                    "https://serpapi.com/search.json",
                    params=params,
                    timeout=60
                )
                lens_time = time.time() - lens_start
                log_debug(f"Lens API call took {lens_time:.2f}s (attempt {attempt + 1})")
                break  # Success, exit retry loop
            except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                last_error = e
                log_debug(f"Lens connection error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
        
        if response is None:
            log_debug(f"Lens API failed after {max_retries} retries: {last_error}")
            return {"error": f"Connection failed after {max_retries} retries"}
        
        if response.status_code != 200:
            log_debug(f"Lens API error: {response.status_code}")
            return {"error": f"API returned {response.status_code}"}
        
        results = response.json()
        
        if "error" in results:
            log_debug(f"Lens error: {results['error']}")
            return {"error": results["error"]}
        
        # Extract best product name
        product_name = None
        confidence = 0.0
        source = None
        link = None
        
        # Try knowledge_graph first
        if "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            product_name = kg.get("title")
            confidence = 0.95
            source = "knowledge_graph"
            log_debug(f"KG match: {product_name}")
        
        # Try visual_matches
        if not product_name and "visual_matches" in results:
            vm = results["visual_matches"]
            # Log top 5 matches for debugging
            log_debug(f"Visual matches ({len(vm)} total):")
            for i, match in enumerate(vm[:5]):
                log_debug(f"  #{i+1}: {match.get('title', 'No title')} (source: {match.get('source', '?')})")
            if vm:
                product_name = vm[0].get("title")
                confidence = 0.8
                source = vm[0].get("source", "visual_matches")
                link = vm[0].get("link")
                log_debug(f"Visual match selected: {product_name}")
        
        # Try shopping_results
        if not product_name and "shopping_results" in results:
            sr = results["shopping_results"]
            if sr:
                product_name = sr[0].get("title")
                confidence = 0.85
                source = sr[0].get("source", "shopping")
                link = sr[0].get("link")
                log_debug(f"Shopping match: {product_name}")
        
        total_time = time.time() - start_time
        
        return {
            "product_name": product_name or "Unknown Product",
            "confidence": confidence,
            "source": source,
            "link": link,
            "visual_matches_count": len(results.get("visual_matches", [])),
            "shopping_results_count": len(results.get("shopping_results", [])),
            "timing": {
                "upload_time_s": round(upload_time, 2),
                "lens_api_time_s": round(lens_time, 2),
                "total_time_s": round(total_time, 2)
            }
        }
        
    except Exception as e:
        log_debug(f"Lens exception: {str(e)}")
        return {"error": str(e)}
