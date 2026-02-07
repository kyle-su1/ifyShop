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
        }

        try:
            r = requests.post(TAVILY_URL, json=payload, timeout=10)
            data = r.json()
            
            if data.get("error"):
                 trace.append({"step": "tavily", "detail": f"API Error: {data.get('error')}"})
                 continue

            for item in data.get("results", []):
                url = item.get("url")
                if not url:
                    continue
                results.append(
                    ReviewSnippet(
                        source=item.get("title") or "",
                        url=url,
                        snippet=item.get("content") or "",
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
        "include_answer": True, # Get Tavily's generated answer if possible
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

        for item in data.get("results", []):
             results.append({
                 "title": item.get("title", ""),
                 "url": item.get("url", ""),
                 "content": item.get("content", "")
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
