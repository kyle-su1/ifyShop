import requests
from typing import List, Dict
from app.schemas.types import ProductQuery, ReviewSnippet
from app.core.config import settings

import hashlib
import json
from app.services.snowflake_cache import snowflake_cache_service

TAVILY_URL = "https://api.tavily.com/search"


def find_review_snippets(product: ProductQuery, trace: list) -> List[ReviewSnippet]:
    # --- Check Cache ---
    cache_key = f"tavily:reviews:{hashlib.md5(product.canonical_name.encode()).hexdigest()}"
    cached_data = snowflake_cache_service.get(cache_key)
    
    if cached_data:
        trace.append({"step": "tavily", "detail": f"Cache Hit ({len(cached_data)} items)"})
        return [ReviewSnippet(**item) for item in cached_data]
    # --- End Cache Check ---

    api_key = settings.TAVILY_API_KEY

    if not api_key:
        trace.append({"step": "tavily", "detail": "Missing API key"})
        return []

    queries = [
        f"{product.canonical_name} review Canada",
        f"{product.canonical_name} review reddit Canada",
        f"site:reddit.com {product.canonical_name} worth it Canada",
    ]

    results = []

    for q in queries:
        payload = {
            "api_key": api_key,
            "query": q,
            "search_depth": "basic",
            "include_images": True,
        }

        try:
            r = requests.post(TAVILY_URL, json=payload, timeout=10)
            data = r.json()
            
            if data.get("error"):
                 trace.append({"step": "tavily", "detail": f"API Error: {data.get('error')}"})
                 continue
            
            # Extract images from the main response if available
            main_images = data.get("images", [])

            for item in data.get("results", []):
                url = item.get("url")
                if not url:
                    continue
                results.append(
                    ReviewSnippet(
                        source=item.get("title") or "",
                        url=url,
                        snippet=item.get("content") or "",
                        images=main_images # Attach general search images to snippets for now as fallback context
                    )
                )
        except Exception as e:
            trace.append({"step": "tavily", "detail": f"Request Failed: {e}"})

    trace.append({"step": "tavily", "detail": f"Found {len(results)} review snippets"})
    
    # --- Store in Cache ---
    if results:
        # Cache for 60 minutes
        snowflake_cache_service.set(
            cache_key=cache_key,
            cache_type="tavily_reviews",
            params={"product": product.model_dump()},
            result=[r.model_dump() for r in results],
            ttl_minutes=60
        )
    # --- End Cache Store ---
    
    return results


def search_market_context(query: str) -> List[Dict[str, str]]:
    """
    Performs a general context search using Tavily.
    Used by Market Scout to find alternatives/competitors.
    """
    # --- Check Cache ---
    cache_key = f"tavily:search:{hashlib.md5(query.encode()).hexdigest()}"
    cached_data = snowflake_cache_service.get(cache_key)
    
    if cached_data:
        return cached_data
    # -------------------

    api_key = settings.TAVILY_API_KEY
    if not api_key:
        return []

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "include_images": True, # Request images from Tavily
    }

    try:
        r = requests.post(TAVILY_URL, json=payload, timeout=10)
        data = r.json()
        
        if data.get("error"):
             return []

        results = []
        # Tavily sometimes returns an 'answer' block
        if data.get("answer"):
            results.append({"title": "Tavily AI Summary", "url": "", "content": data.get("answer")})

        # Process main results
        for item in data.get("results", []):
             results.append({
                 "title": item.get("title", ""),
                 "url": item.get("url", ""),
                 "content": item.get("content", "")
             })
             
        # Extract images if available (usually in a separate 'images' key or inside results)
        # Tavily response format for images: {"images": ["url1", "url2", ...]}
        images = data.get("images", [])
        
        # Attach images to the FIRST result just to pass them along, 
        # or we can return them separately. 
        # For simplicity in the current architecture, we'll embed them in a special result entry
        # or rely on the fact that we return a list of dicts.
        # Let's add a special entry for images so Market Scout can find them.
        if images:
            results.append({
                "title": "Related Images",
                "url": "",
                "content": "",
                "images": images # List of URL strings
            })
        
        # --- Store in Cache ---
        if results:
            snowflake_cache_service.set(
                cache_key=cache_key,
                cache_type="tavily_search",
                params={"query": query},
                result=results,
                ttl_minutes=60
            ) 
        # ----------------------
        
        return results
    except Exception as e:
        print(f"Tavily Market Search Error: {e}")
        return []


def search_eco_sustainability(product_name: str) -> Dict[str, any]:
    """
    Search for product sustainability and environmental impact info.
    Returns eco data for the Skeptic agent to evaluate.
    """
    # --- Check Cache ---
    cache_key = f"tavily:eco:{hashlib.md5(product_name.encode()).hexdigest()}"
    cached_data = snowflake_cache_service.get(cache_key)
    
    if cached_data:
        print(f"   [Eco] Cache hit for {product_name[:30]}")
        return cached_data
    # -------------------

    api_key = settings.TAVILY_API_KEY
    if not api_key:
        print("   [Eco] No API key!")
        return {"eco_context": "", "found": False}

    # Simpler, broader eco search query
    eco_query = f'{product_name} sustainability environmental impact eco-friendly'
    print(f"   [Eco] Searching: {eco_query[:60]}...")

    payload = {
        "api_key": api_key,
        "query": eco_query,
        "search_depth": "basic",
        "include_answer": True,
        "max_results": 5,
    }

    try:
        r = requests.post(TAVILY_URL, json=payload, timeout=8)
        data = r.json()
        
        if data.get("error"):
            print(f"   [Eco] API Error: {data.get('error')}")
            return {"eco_context": "", "found": False}

        eco_snippets = []
        
        # Get AI summary if available
        if data.get("answer"):
            eco_snippets.append(f"Summary: {data.get('answer')}")
            print(f"   [Eco] Got AI summary ({len(data.get('answer'))} chars)")

        # Extract relevant content from results
        for item in data.get("results", []):
            content = item.get("content", "")
            title = item.get("title", "")
            if content:
                eco_snippets.append(f"{title}: {content[:300]}")
        
        print(f"   [Eco] Found {len(eco_snippets)} eco snippets")
        
        # --- Fallback Search Strategy ---
        if not eco_snippets:
            # Try a broader search with just the first few words of the product name
            # e.g., "GLAMBERGET extendable bed" instead of the full 20-word description
            simple_name = " ".join(product_name.split()[:4])
            if simple_name != product_name:
                print(f"   [Eco] Specific search failed. Trying fallback: {simple_name}...")
                fallback_query = f'{simple_name} material sustainability eco-friendly reviews'
                
                payload["query"] = fallback_query
                try:
                    r2 = requests.post(TAVILY_URL, json=payload, timeout=8)
                    data2 = r2.json()
                    
                    if not data2.get("error"):
                         if data2.get("answer"):
                             eco_snippets.append(f"Summary (Broad): {data2.get('answer')}")
                         
                         for item in data2.get("results", []):
                             title = item.get("title", "")
                             content = item.get("content", "")
                             if content:
                                 eco_snippets.append(f"{title}: {content[:300]}")
                                 
                         print(f"   [Eco] Fallback found {len(eco_snippets)} snippets")
                except Exception as e2:
                    print(f"   [Eco] Fallback failed: {e2}")
        # --------------------------------

        eco_context = "\n".join(eco_snippets[:5])  # Limit to 5 snippets
        
        result = {
            "eco_context": eco_context,
            "found": bool(eco_snippets)
        }
        
        # --- Store in Cache ---
        if result["found"]:
            snowflake_cache_service.set(
                cache_key=cache_key,
                cache_type="tavily_eco",
                params={"product": product_name},
                result=result,
                ttl_minutes=120  # Cache eco data longer (2 hours)
            ) 
        # ----------------------
        
        return result
    except Exception as e:
        print(f"   [Eco] Search Error: {e}")
        return {"eco_context": "", "found": False}
