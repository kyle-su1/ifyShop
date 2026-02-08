import requests
from typing import List, Dict, Any
from app.schemas.types import ProductQuery, PriceOffer
from app.core.config import settings

import hashlib
import json
from app.services.snowflake_cache import snowflake_cache_service

SERPAPI_URL = "https://serpapi.com/search.json"


def get_shopping_offers(product: ProductQuery, trace: list) -> List[PriceOffer]:
    # --- Check Cache ---
    cache_key = f"serpapi:offers:{hashlib.md5(product.canonical_name.encode()).hexdigest()}"
    cached_data = snowflake_cache_service.get(cache_key)
    
    if cached_data:
        trace.append({"step": "serpapi", "detail": f"Cache Hit ({len(cached_data)} offers)"})
        return [PriceOffer(**item) for item in cached_data]
    # -------------------

    api_key = settings.SERPAPI_API_KEY

    if not api_key:
        trace.append({"step": "serpapi", "detail": "Missing API key"})
        return []

    params = {
        "engine": "google_shopping",
        "q": product.canonical_name,
        "gl": "ca",
        "hl": "en",
        "location": "Canada",
        "num": 10,  # Limit results to 10 to reduce processing time
        "api_key": api_key,
    }

    try:
        r = requests.get(SERPAPI_URL, params=params, timeout=10)
        data = r.json()

        if "error" in data:
            msg = f"SerpAPI Error: {data['error']}"
            print(f"⚠️ {msg}")
            trace.append({"step": "serpapi", "detail": msg})
            return []

        offers = []

        for item in data.get("shopping_results", []):
            # SerpAPI uses "price" (e.g. "$5.88") or "extracted_price" (numeric)
            # SerpAPI uses "price" (e.g. "$5.88") or "extracted_price" (numeric)
            price_val = item.get("extracted_price")
            price_str = item.get("price")
            
            price_cents = 0
            # Priority 1: Use extracted_price if available (it's usually a reliable float)
            if isinstance(price_val, (int, float)):
                price_cents = int(round(price_val * 100))
            
            # Priority 2: Parse price string if extracted_price failed
            elif price_str:
                import re
                # Clean string: remove currency symbols, letters, etc. keep digits, dots, commas
                # Matches: $1,234.56 -> 1,234.56
                # Matches: CA$ 1200 -> 1200
                match = re.search(r'[\d,]+\.?\d*', str(price_str))
                if match:
                    clean_str = match.group(0).replace(",", "")
                    try:
                        price_cents = int(round(float(clean_str) * 100))
                    except (ValueError, TypeError):
                        pass

            if price_cents == 0:
                continue

            # SerpAPI Google Shopping uses "product_link", not "link"
            link = item.get("product_link") or item.get("link")
            if not link:
                continue

            offers.append(
                PriceOffer(
                    vendor=item.get("source") or "Unknown",
                    price_cents=price_cents,
                    currency="CAD",
                    url=link,
                    title=item.get("title") or item.get("source"), # Capture title
                    thumbnail=item.get("thumbnail") # Extract thumbnail
                )
            )

        trace.append({"step": "serpapi", "detail": f"Found {len(offers)} offers"})
        
        # --- Store in Cache ---
        if offers:
            # Cache for 15 minutes (prices change often)
            snowflake_cache_service.set(
                cache_key=cache_key,
                cache_type="serpapi_offers",
                params={"product": product.model_dump()},
                result=[o.model_dump() for o in offers],
                ttl_minutes=15
            )
        # ----------------------
        
        return offers
    except Exception as e:
        trace.append({"step": "serpapi", "detail": f"Request Failed: {e}"})
        return []


def check_single_price(query: str) -> str | None:
    """
    Quickly checks the price of a product query.
    Returns a formatted price string (e.g. '$149.99 CAD') or None.
    """
    temp_query = ProductQuery(canonical_name=query)
    offers = get_shopping_offers(temp_query, [])
    if offers:
        # Sort by price to get the lowest reasonable price
        offers.sort(key=lambda x: x.price_cents)
        best_offer = offers[0]
        return f"${best_offer.price_cents / 100:.2f} {best_offer.currency}"
    return None


from serpapi import GoogleSearch

def search_google_lens(image_path: str) -> Dict[str, Any]:
    """
    Performs a Google Lens search using SerpAPI.
    
    Args:
        image_path: Absolute path to the image file to upload.
        
    Returns:
        Dict containing 'visual_matches' and 'knowledge_graph' from the API response.
    """
    api_key = settings.SERPAPI_API_KEY
    if not api_key:
        print("Error: Missing SERPAPI_API_KEY")
        return {}
        
    params = {
        "engine": "google_lens",
        "api_key": api_key,
        "country": "ca",
        "hl": "en"
    }
    
    
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[SerpAPI] {str(message)}\n")
        except Exception:
            pass

    
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[SerpAPI] {str(message)}\n")
        except Exception:
            pass

    try:
        # The python client wrapper is failing on file upload. 
        # We will use requests directly to handle multipart/form-data.
        
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_lens",
            "api_key": api_key,
            "country": "ca",
            "hl": "en"
        }
        
        log_debug(f"Uploading image to SerpAPI Lens (Engine: google_lens)...")
        
        with open(image_path, 'rb') as f:
            files = {
                "image_file": (image_path, f, "image/jpeg")
            }
            response = requests.post(url, params=params, files=files, timeout=60)
            
        if response.status_code != 200:
            log_debug(f"HTTP Error: {response.status_code} - {response.text}")
            return {}
            
        results = response.json()
        
        log_debug(f"Lens Search Results Keys: {list(results.keys())}")
        if "error" in results:
             log_debug(f"API Error: {results['error']}")
        
        return results
    except Exception as e:
        print(f"SerpAPI Lens Error: {e}")
        log_debug(f"Lens Error: {e}")
        return {}
