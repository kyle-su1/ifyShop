from typing import Dict, Any, List
import time
from app.agent.state import AgentState
from app.schemas.types import ProductQuery
from app.sources.tavily_client import find_review_snippets
from app.sources.serpapi_client import get_shopping_offers

def node_discovery_runner(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Discovery & Research (The "Runner")
    
    Responsibilities:
    1. Search for official product pages and retail listings using Tavily.
    2. Scrape reviews (Reddit, YouTube, RTings) for specific context.
    3. Look up current pricing (SerpAPI).
    """
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception:
            pass

    log_debug("--- 2. Executing Discovery Node (The Runner) ---")
    print("--- 2. Executing Discovery Node (The Runner) ---")
    
    product_query_data = state.get('product_query', {})
    product_name = product_query_data.get('canonical_name') or product_query_data.get('product_name', '')
    
    log_debug(f"Researching Product: {product_name}")
    
    if not product_name or "Error" in product_name:
        log_debug("ERROR: No valid product to research")
        return {"research_data": {"error": "No valid product to research"}}

    # Create ProductQuery object for the source clients
    # parsing keywords or brand could be done by an LLM in a more advanced version
    product = ProductQuery(
        canonical_name=product_name,
        region="CA" # Defaulting to CA as per valid clients source code
    )
    
    trace_log = []

    # Execute Search and Price Check in Parallel
    print(f"   [Runner] Parallelizing search for: {product_name}")
    log_debug("Starting parallel research task...")

    from concurrent.futures import ThreadPoolExecutor
    
    reviews_data = []
    offers_data = []
    
    def fetch_reviews():
        try:
            log_debug("Starting Tavily search...")
            review_start = time.time()
            reviews = find_review_snippets(product, trace_log)
            review_time = time.time() - review_start
            print(f"   ⏱️  [Runner] Tavily reviews took {review_time:.2f}s")
            log_debug(f"Tavily found {len(reviews)} reviews")
            return [r.dict() for r in reviews]
        except Exception as e:
            print(f"   [Runner] Tavily Error: {e}")
            log_debug(f"Tavily Error: {e}")
            return []

    def fetch_prices():
        try:
            log_debug("Starting SerpAPI search...")
            price_start = time.time()
            offers = get_shopping_offers(product, trace_log)
            price_time = time.time() - price_start
            print(f"   ⏱️  [Runner] SerpAPI prices took {price_time:.2f}s")
            log_debug(f"SerpAPI found {len(offers)} offers")
            return [o.dict() for o in offers]
        except Exception as e:
            print(f"   [Runner] SerpAPI Error: {e}")
            log_debug(f"SerpAPI Error: {e}")
            return []

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_reviews = executor.submit(fetch_reviews)
        future_prices = executor.submit(fetch_prices)
        
        reviews_data = future_reviews.result()
        offers_data = future_prices.result()

    # Fallback if no offers found for main product
    if not offers_data:
        import urllib.parse
        encoded_name = urllib.parse.quote(product_name)
        fallback_url = f"https://www.google.com/search?tbm=shop&q={encoded_name}"
        
        # Try to find an image from reviews if available
        fallback_image = None
        for r in reviews_data:
             if r.get('images'):
                 fallback_image = r.get('images')[0]
                 break
                 
        offers_data.append({
            "vendor": "Google Shopping Search",
            "price": 0,
            "currency": "CAD",
            "url": fallback_url,
            "thumbnail": fallback_image # Use Tavily image if available
        })
        print(f"   [Runner] No direct offers, added fallback link (Image: {'Yes' if fallback_image else 'No'}).")
        
    # --- PRICE LOGGING (Summary Only) ---
    try:
        with open("/app/logs/price_debug.log", "a", encoding="utf-8") as f:
            if offers_data:
                best_price = offers_data[0].get('price_cents', 0) / 100.0 if offers_data[0].get('price_cents') else 0
                f.write(f"[Main] {product_name} | {len(offers_data)} offers | Best: ${best_price:.2f} CAD\n")
    except Exception:
        pass
    # ---------------------
    
    # Calculate total time for this node
    import time as time_module
    node_end = time_module.time()
    # Note: We need to track start time at the beginning of the function
    # Since parallel tasks are internal, we'll approximate from the task times
    node_time = max(review_time if 'review_time' in dir() else 0, price_time if 'price_time' in dir() else 0)
    
    # Get existing timings and add this node's time  
    existing_timings = state.get('node_timings', {}) or {}
    existing_timings['research'] = node_time
    
    # 3. Aggregate Data
    research_data = {
        "search_results": [r['snippet'] for r in reviews_data if 'snippet' in r], # Simplified list for simple prompts
        "reviews": reviews_data, 
        "competitor_prices": offers_data,
        "trace": trace_log
    }
    
    log_debug("Discovery Node Completed")
    return {"research_data": research_data, "node_timings": existing_timings}
