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
    5. Enrich candidates with real-time prices, images, and purchase links.
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
    search_criteria = state.get('search_criteria', {})  # From Chat Node (colors, brands, etc.)
    
    if not product_name or "Error" in product_name:
        return {"market_scout_data": {"error": "No valid product to scout"}}

    # 1. Determine Strategy based on Preferences
    # Default strategy: "Balanced" (find similar quality)
    search_modifiers = ["best alternative", "competitor"]
    
    # Use visual attributes if available for similarity
    visual_attrs = product_query_data.get('visual_attributes', '')
    if visual_attrs:
        print(f"   [Scout] Using visual attributes: {visual_attrs}")
        
    # Adjust based on user preferences
    if user_prefs.get('price_sensitivity', 0) > 0.7:
        search_modifiers = ["cheaper alternative", "best budget alternative"]
    elif user_prefs.get('quality', 0) > 0.7:
        search_modifiers = ["premium alternative", "better than"]
    
    # 1b. Incorporate search_criteria from Chat Node (Feedback Loop)
    # These come from user requests like "I hate red" or "show me Nike"
    color_filter = ""
    brand_filter = ""
    style_filter = ""
    
    if search_criteria:
        print(f"   [Scout] Applying search_criteria from Chat: {search_criteria}")
        
        # Handle color exclusions
        exclude_colors = search_criteria.get('exclude_colors', [])
        prefer_colors = search_criteria.get('prefer_colors', [])
        if prefer_colors:
            color_filter = " " + " ".join(prefer_colors)
        
        # Handle brand preferences
        prefer_brands = search_criteria.get('prefer_brands', [])
        exclude_brands = search_criteria.get('exclude_brands', [])
        if prefer_brands:
            brand_filter = " " + " ".join(prefer_brands)
        
        # Handle style keywords
        style_keywords = search_criteria.get('style_keywords', [])
        if style_keywords:
            style_filter = " " + " ".join(style_keywords)

    # 2. Construct Queries with filters applied
    queries = []
    if visual_attrs:
        queries.append(f"{search_modifiers[0]} to {product_name} {visual_attrs}{color_filter}{brand_filter}{style_filter} 2026")
        queries.append(f"similar {visual_attrs} like {product_name}{color_filter}{brand_filter}")
    else:     
        queries = [
            f"{modifier} to {product_name}{color_filter}{brand_filter}{style_filter} 2026 reddit" 
            for modifier in search_modifiers
        ]
        queries.append(f"{product_name} vs competition 2026")

    print(f"   [Scout] Strategy: {search_modifiers[0]} | Queries: {queries}")
    
    import time
    start_time = time.time()
    
    # 3. Execute Search
    print(f"   [Scout] Executing search for alternatives...")
    from app.sources.tavily_client import search_market_context
    
    scout_results = []
    # Use parallel execution for search queries to speed up
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    search_start = time.time()
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_query = {executor.submit(search_market_context, q): q for q in queries[:2]} # Limit to 2 queries
        for future in as_completed(future_to_query):
            try:
                # Add timeout to search
                results = future.result(timeout=10)
                scout_results.extend(results)
            except Exception:
                pass
    search_time = time.time() - search_start
    print(f"   ⏱️  [Scout] Tavily search took {search_time:.2f}s")
                
    # Deduplicate results based on URL
    seen_urls = set()
    unique_results = []
    for r in scout_results:
        if r.get('url') and r.get('url') not in seen_urls:
            seen_urls.add(r.get('url'))
            unique_results.append(r)
    
    # 4b. Extract Images from Search Results (for fallback)
    fallback_images = []
    for r in scout_results:
        if r.get('images'):
            fallback_images.extend(r.get('images'))
            
    # 4. Extract Candidates using LLM
    print(f"   [Scout] Extracting candidates from {len(unique_results)} search results...")
    
    context_text = "\n".join([f"- {r.get('title')}: {r.get('content')}" for r in unique_results[:8]]) # Limit context
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    from app.core.config import settings
    import json
    
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY, temperature=0.1)
    
    prompt = f"""You are a Market Scout. 
    Product: {product_name}
    Goal: Find 3 best {search_modifiers[0]} products.
    
    Search Context:
    {context_text}
    
    Return a Strict JSON List of objects with keys: "name", "category", "reason".
    "name" MUST be the specific model name (e.g. "Sony WH-1000XM5", "BenQ TK700"), NOT just the brand.
    "category" should be the product type (e.g. "Headphones", "Projector").
    Example: [{{"name": "Competitor X Model Y", "category": "Smart Watch", "reason": "Better battery life"}}]
    """
    
    llm_extract_start = time.time()
    candidates = []
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
             content = content.split('```')[1].split('```')[0]
             
        candidates = json.loads(content)
        if not isinstance(candidates, list):
            candidates = []
        llm_extract_time = time.time() - llm_extract_start
        print(f"   ⏱️  [Scout] LLM extraction took {llm_extract_time:.2f}s")

        # --- Snowflake Vector Search Integration ---
        # Uses search_criteria to create a more targeted embedding query
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from app.services.snowflake_vector import snowflake_vector_service
            
            print("   [Scout] Checking Snowflake Vector DB for known alternatives...")
            
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001", 
                google_api_key=settings.GOOGLE_API_KEY
            )
            
            # Build enhanced query with search_criteria from Chat Node
            enhanced_query = product_name
            if search_criteria:
                criteria_parts = []
                if search_criteria.get('prefer_colors'):
                    criteria_parts.append(" ".join(search_criteria['prefer_colors']))
                if search_criteria.get('prefer_brands'):
                    criteria_parts.append(" ".join(search_criteria['prefer_brands']))
                if search_criteria.get('style_keywords'):
                    criteria_parts.append(" ".join(search_criteria['style_keywords']))
                if criteria_parts:
                    enhanced_query = f"{product_name} {' '.join(criteria_parts)}"
                    print(f"   [Scout] Enhanced vector query: '{enhanced_query}'")
            
            query_vector = embeddings.embed_query(enhanced_query)
            
            # Search Snowflake
            vector_results = snowflake_vector_service.search_similar_products(query_vector, limit=2)
            
            if vector_results:
                print(f"   [Scout] Found {len(vector_results)} matches in Snowflake.")
                for res in vector_results:
                    # Filter out results that match excluded colors/brands
                    res_name = res.get('name', '').lower()
                    exclude_colors = search_criteria.get('exclude_colors', [])
                    exclude_brands = search_criteria.get('exclude_brands', [])
                    
                    # Skip if product matches exclusions
                    if any(color.lower() in res_name for color in exclude_colors):
                        print(f"       -> Skipping {res.get('name')} (excluded color)")
                        continue
                    if any(brand.lower() in res_name for brand in exclude_brands):
                        print(f"       -> Skipping {res.get('name')} (excluded brand)")
                        continue
                    
                    # Convert to candidate format
                    cand = {
                        "name": res.get('name'),
                        "category": res.get('metadata', {}).get('category', ''), # Attempt to get category from metadata
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

        # 5. Enrich with Real-Time Prices, Images, and Reviews
        if candidates:
            try:
                from app.sources.serpapi_client import get_shopping_offers
                from app.sources.tavily_client import find_review_snippets
                from app.schemas.types import ProductQuery
                # ensure concurrent.futures is imported
                from concurrent.futures import ThreadPoolExecutor, as_completed

                def enrich_candidate(cand):
                    name = cand.get('name')
                    category = cand.get('category', '')
                    if not name:
                        return
                    
                    try:
                        # Construct a more specific query with category
                        search_query = f"{name} {category}".strip()
                        temp_query = ProductQuery(canonical_name=search_query)
                        temp_trace = []
                        
                        # Get prices
                        price_offers = get_shopping_offers(temp_query, temp_trace)

                        # Filter out accessories/parts based on title
                        valid_offers = []
                        if price_offers:
                            bad_keywords = ["lamp", "bulb", "remote", "mount", "bracket", "case", "bag", "filter", "adapter", "cable", "part", "replacement", "stand", "ceiling", "screen"]
                            
                            for p in price_offers:
                                title_lower = (p.title or "").lower()
                                # Check if title contains bad keywords BUT is not the main category itself (imperfect heuristic)
                                # e.g. "Replacement Lamp" -> Bad. "Projector with Lamp" -> Good?
                                # Simple check: if bad keyword exists, skip.
                                if not any(kw in title_lower for kw in bad_keywords):
                                    valid_offers.append(p)
                                else:
                                    print(f"       -> Skipped accessory: {p.title}")
                                    
                        # Fallback to all offers if filtering is too aggressive
                        if not valid_offers and price_offers:
                            valid_offers = price_offers
                            print(f"       -> Filtering removed all offers, reverting to original list.")
                        
                        cand['prices'] = [
                            {
                                "vendor": p.vendor, 
                                "price": p.price_cents / 100, 
                                "price_cents": p.price_cents, # Add for consistency with research.py
                                "currency": p.currency, 
                                "url": p.url,
                                "thumbnail": p.thumbnail
                            }
                            for p in valid_offers
                        ]
                        
                        # --- PRICE LOGGING (Summary Only) ---
                        try:
                            with open("/app/logs/price_debug.log", "a", encoding="utf-8") as f:
                                best_p = price_offers[0].price_cents / 100 if price_offers else 0
                                f.write(f"[Alt] {name} | {len(price_offers)} offers | Best: ${best_p:.2f} CAD\n")
                        except Exception:
                            pass
                        # ---------------------
                        
                        if valid_offers:
                            # Capture Image and Link from best offer
                            best_offer = valid_offers[0] 
                            cand['image_url'] = getattr(best_offer, 'thumbnail', None)
                            cand['purchase_link'] = best_offer.url
                            
                            sorted_prices = sorted([p.price_cents for p in valid_offers])
                            median_idx = len(sorted_prices) // 2
                            median_price = sorted_prices[median_idx] / 100
                            
                            # Use currency from best offer or default to CAD
                            currency_code = best_offer.currency if best_offer.currency else "CAD"
                            
                            cand['estimated_price'] = f"${median_price:.2f} {currency_code}"
                            cand['price_text'] = f"${median_price:.2f}"
                            print(f"       -> {name}: {len(valid_offers)} valid prices found.")
                            print(f"       -> {name}: {len(valid_offers)} valid prices found.")
                        else:
                            # Fallback Logic: Use Tavily data or Google Shopping Search
                            
                            # 1. Try to find a fallback image from Tavily results
                            # Simple heuristic: pick the first available fallback image
                            # In a real system, we might try to match semantic similarity or alt text
                            if fallback_images and not cand.get('image_url'):
                                cand['image_url'] = fallback_images[0] 
                            
                            # 2. Try to find a fallback link from Tavily results
                            # Match the candidate name to a search result URL if possible
                            fallback_link = None
                            for r in unique_results:
                                if name.lower() in r.get('title', '').lower():
                                    fallback_link = r.get('url')
                                    break
                            
                            if fallback_link:
                                cand['purchase_link'] = fallback_link
                            else:
                                # Create Google Shopping fallback if no direct link found
                                import urllib.parse
                                encoded_name = urllib.parse.quote(name)
                                cand['purchase_link'] = f"https://www.google.com/search?tbm=shop&q={encoded_name}"
                                
                            cand['estimated_price'] = "Check Price"
                            cand['price_text'] = "Check Price"
                            cand['image_url'] = cand.get('image_url') or "https://via.placeholder.com/150?text=No+Image" # Placeholder if no image
                            print(f"       -> {name}: No direct offers, using fallback link/image.")

                        # Skip reviews for alternatives - the LLM already captured why each is recommended
                        # This saves ~3-4s per candidate by removing the Tavily API call
                        cand['reviews'] = []
                        
                    except Exception as inner_e:
                        print(f"       -> Error enriching {name}: {inner_e}")

                # Run enrichment in parallel, limit to 2 to avoid API rate limits
                # Latency Optimization: Limit to top 2 candidates total to prevent massive fan-out
                enrichment_start = time.time()
                candidates_to_process = candidates[:2]
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [executor.submit(enrich_candidate, cand) for cand in candidates_to_process]
                    for future in as_completed(futures):
                        try:
                            future.result(timeout=15)
                        except Exception as exc:
                            print(f"   [Scout] Candidate enrichment failed: {exc}")
                enrichment_time = time.time() - enrichment_start
                print(f"   ⏱️  [Scout] Enrichment (prices/reviews) took {enrichment_time:.2f}s")
                    
            except Exception as e:
                print(f"       -> Enrichment setup failed: {e}")
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"   [Scout] LLM Extraction skipped or failed: {e}")
        # Fallback: just return empty candidates
        pass
        
    # --- FINAL DATA GUARANTEE ---
    # Ensure all candidates have the required keys for frontend display
    for cand in candidates:
        if not cand.get('image_url'):
            cand['image_url'] = "https://placehold.co/400x300?text=No+Image"
        if not cand.get('purchase_link'):
             # Create Google Shopping fallback
            import urllib.parse
            encoded_name = urllib.parse.quote(cand.get('name', 'Product'))
            cand['purchase_link'] = f"https://www.google.com/search?tbm=shop&q={encoded_name}"
        if not cand.get('price_text'):
            cand['price_text'] = "Check Price"
            
    total_time = time.time() - start_time
    print(f"--- Market Scout Node: Total time {total_time:.2f}s ---")
    log_debug("Market Scout Node Completed")
    
    # Get existing timings and add this node's time
    existing_timings = state.get('node_timings', {}) or {}
    existing_timings['market_scout'] = total_time
    
    return {
        "market_scout_data": {
            "strategy": search_modifiers[0],
            "raw_search_results": unique_results,
            "candidates": candidates[:2]  # Only return enriched candidates
        },
        "node_timings": existing_timings
    }
