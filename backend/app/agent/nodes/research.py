from typing import Dict, Any, List
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

    import time
    start_time = time.time()
    
    # 1. Tavily Search (Reviews)
    print(f"   [Runner] Searching reviews for: {product_name}")
    log_debug("Starting Tavily search...")
    try:
        tavily_start = time.time()
        reviews = find_review_snippets(product, trace_log)
        tavily_time = time.time() - tavily_start
        print(f"--- Research Node: Tavily took {tavily_time:.2f}s ---")
        
        # Convert Pydantic models to dicts for state serialization
        reviews_data = [r.dict() for r in reviews]
        log_debug(f"Tavily found {len(reviews_data)} reviews in {tavily_time:.2f}s")
    except Exception as e:
        print(f"   [Runner] Tavily Error: {e}")
        log_debug(f"Tavily Error: {e}")
        reviews_data = []

    # 2. SerpAPI Search (Pricing)
    print(f"   [Runner] Checking prices for: {product_name}")
    log_debug("Starting SerpAPI search...")
    try:
        serp_start = time.time()
        offers = get_shopping_offers(product, trace_log)
        serp_time = time.time() - serp_start
        print(f"--- Research Node: SerpAPI took {serp_time:.2f}s ---")
        
        # Convert Pydantic models to dicts for state serialization
        offers_data = [o.dict() for o in offers]
        log_debug(f"SerpAPI found {len(offers_data)} offers in {serp_time:.2f}s")
    except Exception as e:
        print(f"   [Runner] SerpAPI Error: {e}")
        log_debug(f"SerpAPI Error: {e}")
        offers_data = []
    
    # 3. Aggregate Data
    research_data = {
        "search_results": [r['snippet'] for r in reviews_data if 'snippet' in r], # Simplified list for simple prompts
        "reviews": reviews_data, 
        "competitor_prices": offers_data,
        "trace": trace_log
    }
    
    log_debug("Discovery Node Completed")
    return {"research_data": research_data}
