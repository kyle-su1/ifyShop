from typing import Dict, Any, List
from app.agent.state import AgentState
from app.sources.tavily_client import find_review_snippets
from app.schemas.types import ProductQuery

def node_market_scout(state: AgentState) -> Dict[str, Any]:
    """
    Node 2b: Market Scout (The "Explorer")
    
    Responsibilities:
    1. Analyze user preferences (or default to balanced).
    2. Generate search queries for finding ALTERNATIVE products.
    3. Search Tavily for "best X alternatives 2026" or "competitor to X".
    4. Parse results to identify 2-3 candidate product names.
    """
    print("--- 2b. Executing Market Scout Node (The Explorer) ---")
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception:
            pass

    log_debug("--- 2b. Executing Market Scout Node (The Explorer) ---")
    
    product_query_data = state.get('product_query', {})
    product_name = product_query_data.get('canonical_name') or product_query_data.get('product_name', '')
    user_prefs = state.get('user_preferences', {})
    
    if not product_name or "Error" in product_name:
        return {"market_scout_data": {"error": "No valid product to scout"}}

    # 1. Determine Strategy based on Preferences
    # Default strategy: "Balanced" (find similar quality)
    search_modifiers = ["best alternative", "competitor"]
    
    # Simple heuristic for demo (replace with LLM logic later)
    if user_prefs.get('price_sensitivity', 0) > 0.7:
        search_modifiers = ["cheaper alternative", "best budget alternative"]
    elif user_prefs.get('quality', 0) > 0.7:
        search_modifiers = ["premium alternative", "better than"]
    
    # 2. Construct Queries
    queries = [
        f"{modifier} to {product_name} 2026 reddit" 
        for modifier in search_modifiers
    ]
    # Add a general one
    queries.append(f"{product_name} vs competition 2026")

    print(f"   [Scout] Strategy: {search_modifiers[0]} | Queries: {queries}")

    # 3. Execute Search (Using Tavily)
    # We use a dummy ProductQuery to reuse the Tavily client, 
    # but we are effectively just using it to search for text strings.
    scout_results = []
    
    # We'll re-use the find_review_snippets function but hijack it 
    # slightly by passing these custom queries if we refactored tavily_client.
    # For now, let's just use the raw tavily client logic here or 
    # better yet, import a generic search function if one existed.
    # Since find_review_snippets is specific to a product, let's just 
    # construct a "Competitor Search" object for it.
    
    # Hack/Workaround: 
    # We will create a temporary 'ProductQuery' where canonical_name is actually the SEARCH QUERY.
    # The tavily_client appends " review Canada" etc, which might mess us up.
    # Ideally, we should add a `generic_search` to tavily_client.py.
    # But for now, let's try to pass the query as the product name 
    # and hope the client finds relevant results. 
    
    #Actually, let's assume we update tavily_client to have a generic_search.
    # I'll implement a `search_alternatives` function in tavily_client.py in the next step.
    # For this file, I'll assume it exists.
    
    # 3. Execute Search (Using Tavily)
    from app.sources.tavily_client import search_market_context

    main_query = queries[0]
    scout_results = search_market_context(main_query)

    if not scout_results:
        print(f"   [Scout] Primary query '{main_query}' returned no results. Trying backup...")
        # Fallback to broader query
        backup_query = f"best alternatives to {product_name} 2026"
        scout_results = search_market_context(backup_query)

    # 4. Extract Candidates using LLM
    print(f"   [Scout] Extracting candidates from {len(scout_results)} search results...")
    
    candidates = []
    
    # We use a try/except block because:
    # 1. The Google API key might not be enabled yet (User's current issue).
    # 2. Parsing might fail.
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
        from pydantic import BaseModel, Field
        from app.core.config import settings

        from app.schemas.types import ProductCandidate
        
        # Define Output Structure for Gemini
        class CandidateList(BaseModel):
            items: List[ProductCandidate] = Field(description="List of alternative products found")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        # Prepare context text from search results
        context_text = ""
        for res in scout_results[:5]: # Limit to top 5 results
            context_text += f"Source: {res.get('title')}\nContent: {res.get('content')}\n\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a market research assistant. Your goal is to identify alternative products based on search results."),
            ("human", "User Strategy: {strategy}\n\nSearch Results:\n{context}\n\nIdentify the top 3 alternative products mentioned. Return a list of candidates with fields: name, reason, estimated_price, pros, cons.")
        ])
        
        structured_llm = llm.with_structured_output(CandidateList)
        chain = prompt | structured_llm
        
        result = chain.invoke({"strategy": search_modifiers[0], "context": context_text})
        
        if result and result.items:
            # Convert Pydantic models to dicts for serialization
            candidates = [item.model_dump() for item in result.items]
            print(f"   [Scout] Successfully extracted {len(candidates)} candidates via Gemini.")

            # 5. Enrich with Real-Time Prices and Reviews (Node 2a logic for alternatives)
            print("   [Scout] Fetching prices and reviews for candidates...")
            
            # --- Snowflake Vector Search Integration ---
            # Checks for similar products already in our database
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                from app.services.snowflake_vector import snowflake_vector_service
                
                print("   [Scout] Checking Snowflake Vector DB for known alternatives...")
                
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001", 
                    google_api_key=settings.GOOGLE_API_KEY
                )
                query_vector = embeddings.embed_query(product_name)
                
                # Search Snowflake
                vector_results = snowflake_vector_service.search_similar_products(query_vector, limit=3)
                
                if vector_results:
                    print(f"   [Scout] Found {len(vector_results)} matches in Snowflake.")
                    for res in vector_results:
                        # Convert to candidate format
                        cand = {
                            "name": res.get('name'),
                            "reason": "Found in internal database (High Similarity)",
                            "estimated_price": f"${res.get('price')} (Historical)",
                            "pros": ["Verified Product"],
                            "cons": [],
                            "source": "Snowflake Vector DB"
                        }
                        # Add to candidates if not duplicate
                        if not any(c.get('name') == cand['name'] for c in candidates):
                            candidates.append(cand)
            except Exception as e:
                print(f"   [Scout] Snowflake Vector Search skipped: {e}")
            
            # --- End Snowflake Integration ---

            try:
                from app.sources.serpapi_client import get_shopping_offers
                from app.sources.tavily_client import find_review_snippets
                from app.schemas.types import ProductQuery
                
                for cand in candidates:
                    name = cand.get('name')
                    if not name:
                        continue
                    
                    # Create a temporary ProductQuery for this candidate
                    temp_query = ProductQuery(canonical_name=name)
                    temp_trace = []
                    
                    # Get all prices
                    price_offers = get_shopping_offers(temp_query, temp_trace)
                    cand['prices'] = [
                        {"vendor": p.vendor, "price": p.price_cents / 100, "currency": p.currency, "url": p.url}
                        for p in price_offers
                    ]
                    
                    # Calculate median price for display
                    if price_offers:
                        sorted_prices = sorted([p.price_cents for p in price_offers])
                        median_idx = len(sorted_prices) // 2
                        median_price = sorted_prices[median_idx] / 100
                        cand['estimated_price'] = f"${median_price:.2f} CAD"
                        print(f"       -> {name}: {len(price_offers)} prices found (median: ${median_price:.2f})")
                    
                    # Get reviews
                    review_snippets = find_review_snippets(temp_query, temp_trace)
                    cand['reviews'] = [
                        {"source": r.source, "snippet": r.snippet, "url": r.url}
                        for r in review_snippets
                    ]
                    print(f"       -> {name}: {len(review_snippets)} reviews found")
                    
            except Exception as e:
                print(f"       -> Enrichment failed: {e}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"   [Scout] LLM Extraction skipped or failed: {e}")
        # Fallback: just return empty candidates
        pass

    log_debug("Market Scout Node Completed")
    return {
        "market_scout_data": {
            "strategy": search_modifiers[0],
            "raw_search_results": scout_results,
            "candidates": candidates
        }
    }
