from typing import Dict, Any, List
from app.agent.state import AgentState
from app.sources.tavily_client import find_review_snippets
from app.schemas.types import ProductQuery
from app.db.session import SessionLocal
from app.services.preference_service import get_user_explicit_preferences

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
    product_query_data = state.get('product_query', {})
    product_name = product_query_data.get('canonical_name') or product_query_data.get('product_name', '')
    
    # Load Preferences (Merge DB + State)
    state_prefs = state.get('user_preferences', {})
    try:
        state_id = state.get('user_id')
        user_id = int(state_id) if state_id else 1
        
        with SessionLocal() as db:
            db_prefs = get_user_explicit_preferences(db, user_id)
            user_prefs = {**db_prefs, **state_prefs} # State overrides DB
            print(f"   [Scout] 💾 Accessing Database... Retrieved User Prefs: {user_prefs}")
    except Exception as e:
        print(f"   [Scout] Warning: Failed to load DB prefs ({e}), using state only.")
        user_prefs = state_prefs

    search_criteria = state.get('search_criteria', {})  # From Chat Node (colors, brands, etc.)
    
    # 0. Merge Persistent DB Preferences into Search Criteria
    # If the user has "prefer_brands" saved in DB, but not in current turn's search_criteria, add them.
    if not search_criteria:
        search_criteria = {}
        
    if 'prefer_brands' in user_prefs and 'prefer_brands' not in search_criteria:
        search_criteria['prefer_brands'] = user_prefs['prefer_brands']
        print(f"   [Scout] 🔄 Applied 'prefer_brands' from DB: {user_prefs['prefer_brands']}")
        
    if 'exclude_brands' in user_prefs and 'exclude_brands' not in search_criteria:
        search_criteria['exclude_brands'] = user_prefs['exclude_brands']
    
    if 'prefer_colors' in user_prefs and 'prefer_colors' not in search_criteria:
        search_criteria['prefer_colors'] = user_prefs['prefer_colors']
    
    if not product_name or "Error" in product_name:
        return {"market_scout_data": {"error": "No valid product to scout"}}

    # Clean product name if it's too long or has garbage (e.g. from eBay titles)
    # "OnePlus 7 Pro | Grade A | GSM Unlocked" -> "OnePlus 7 Pro"
    clean_name = product_name.split('|')[0].split(' - ')[0].strip()
    if len(clean_name) < 3: # Too short, revert
        clean_name = product_name
    
    print(f"   [Scout] Raw Name: {product_name} -> Clean Name: {clean_name}")
    product_name = clean_name # Use cleaned name for queries

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
        
        # Handle color preferences
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
    else:
        print(f"   [Scout] No search_criteria provided. Using default balanced strategy.")

    # 2. Construct Queries with filters applied
    queries = []
    
    # Check for Veto Feedback Loop (Priority)
    feedback_query = state.get('skeptic_feedback_query')
    is_retry = state.get('skeptic_loop_count', 0) > 0
    
    if feedback_query:
        print(f"   [Scout] 🔄 Improving search with Veto Feedback: '{feedback_query}'")
        queries = [feedback_query]
        # Optimization: On retry, do NOT add extra variation. 1 Query is enough.
        if not is_retry: 
            queries.append(f"{feedback_query} review")
    elif visual_attrs:
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
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_query = {executor.submit(search_market_context, q): q for q in queries} # Run all queries
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
    
    context_text = "\n".join([f"- {r.get('title')}: {r.get('content')}" for r in unique_results[:25]]) # Expanded context
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    from app.core.config import settings
    import json
    
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY, temperature=0.1)
    
    # Build brand preference instruction for LLM
    brand_instruction = ""
    prefer_brands = search_criteria.get('prefer_brands', []) if search_criteria else []
    if prefer_brands:
        brand_instruction = f"\n    IMPORTANT: User STRONGLY prefers these brands: {', '.join(prefer_brands)}. ONLY include products from these brands. Do NOT include products from other brands."
    
    prompt = f"""You are a Market Scout. 
    Product: {product_name}
    Goal: Find 10 best {search_modifiers[0]} products.{brand_instruction}
    
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
        
        # Post-LLM filtering: Remove candidates that don't match preferred brands
        if prefer_brands and candidates:
            filtered_candidates = []
            for cand in candidates:
                cand_name = cand.get('name', '').lower()
                if any(brand.lower() in cand_name for brand in prefer_brands):
                    filtered_candidates.append(cand)
                else:
                    print(f"       -> Filtered out {cand.get('name')} (not preferred brand)")
            candidates = filtered_candidates
            print(f"   [Scout] After brand filtering: {len(candidates)} candidates remain")

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
            vector_results = snowflake_vector_service.search_similar_products(query_vector, limit=10)
            
            if vector_results:
                print(f"   [Scout] Found {len(vector_results)} matches in Snowflake.")
                for res in vector_results:
                    # Filter out results that match excluded colors/brands
                    res_name = res.get('name', '').lower()
                    exclude_colors = search_criteria.get('exclude_colors', [])
                    exclude_brands = search_criteria.get('exclude_brands', [])
                    prefer_brands = search_criteria.get('prefer_brands', [])
                    
                    # Skip if product matches exclusions
                    if any(color.lower() in res_name for color in exclude_colors):
                        print(f"       -> Skipping {res.get('name')} (excluded color)")
                        continue
                    if any(brand.lower() in res_name for brand in exclude_brands):
                        print(f"       -> Skipping {res.get('name')} (excluded brand)")
                        continue
                    
                    # If user has brand preferences, ONLY include products matching those brands
                    if prefer_brands:
                        if not any(brand.lower() in res_name for brand in prefer_brands):
                            print(f"       -> Skipping {res.get('name')} (not preferred brand)")
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
                    
                    if not name:
                        return
                    
                    # --- ENRICHMENT LOGIC ---
                    # 1. Try Google Shopping (SerpAPI) first for best prices/images
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
                                if not any(kw in title_lower for kw in bad_keywords):
                                    valid_offers.append(p)
                                else:
                                    print(f"       -> Skipped accessory: {p.title}")
                                    
                        # Fallback to all offers if filtering is too aggressive
                        if not valid_offers and price_offers:
                            valid_offers = price_offers
                            print(f"       -> Filtering removed all offers, reverting to original list.")
                    except Exception as e:
                        print(f"       -> Enrichment API failed: {e}")
                        price_offers = []
                        valid_offers = []
                    
                    try:
                        if not is_retry: # Only process offers if we fetched them
                            cand['prices'] = [
                                {
                                    "vendor": p.vendor, 
                                    "price": p.price_cents / 100, 
                                    "price_cents": p.price_cents,
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
                            
                            # Use Best Available Price (First Offer) to match Main Product logic
                            best_offer = valid_offers[0]
                            cand['estimated_price'] = f"${best_offer.price_cents / 100:.2f} {best_offer.currency or 'CAD'}"
                            cand['price_text'] = f"${best_offer.price_cents / 100:.2f}"
                            print(f"       -> {name}: {len(valid_offers)} valid prices found. Best: {cand['price_text']}")
                        else:
                            # --- FALLBACK: TARGETED TAVILY SEARCH ---
                            # If Google Shopping fails (Quota/Error), use Tavily to find price/image
                            print(f"       -> {name}: Google Shopping failed. Attempting Tavily Fallback Search...")
                            
                            try:
                                from app.sources.tavily_client import search_market_context
                                fallback_results = search_market_context(f"{name} price image")
                                
                                # 1. Extract Price from Fallback Results
                                extracted_price = None
                                import re
                                for r in fallback_results:
                                    # Look for price text pattern
                                    prices = re.findall(r'\$[\d,]+(?:\.\d{2})?', r.get('content', ''))
                                    if prices:
                                        extracted_price = prices[0]
                                        if 2 <= len(extracted_price) <= 10:
                                            break
                                        extracted_price = None
                                
                                if extracted_price:
                                    cand['estimated_price'] = f"{extracted_price} (Est.)"
                                    cand['price_text'] = extracted_price
                                    # Link to the result where we found price
                                    cand['purchase_link'] = r.get('url')
                                    print(f"       -> {name}: Recovered price: {extracted_price}")
                                else:
                                    cand['estimated_price'] = "Check Price"
                                    cand['price_text'] = "Check Price"
                                    # Fallback link
                                    import urllib.parse
                                    encoded_name = urllib.parse.quote(name)
                                    cand['purchase_link'] = f"https://www.google.com/search?q={encoded_name}"
        
                                # 2. Extract Image from Fallback Results
                                # Use the 'images' field if Tavily returned it, else placeholder
                                # We need to check if ANY result has an image or if global images exist
                                found_image = None
                                for r in fallback_results:
                                     # Sometimes Tavily results have inline images? (Rare)
                                     # Actually Tavily returns a global 'images' list usually.
                                     # Let's check the 'images' key in the RESULTDICT if we modified search_market_context
                                     pass
                                
                                # Our search_market_context appends a special dict for images
                                images_entry = next((r for r in fallback_results if r.get('title') == "Related Images"), None)
                                if images_entry and images_entry.get('images'):
                                     found_image = images_entry['images'][0]
                                
                                cand['image_url'] = found_image or "https://via.placeholder.com/150?text=No+Image"
                                
                            except Exception as e:
                                print(f"       -> Tavily Fallback failed: {e}")
                                cand['estimated_price'] = "Check Price"
                                cand['price_text'] = "Check Price"
                                cand['image_url'] = "https://via.placeholder.com/150?text=Error"

                        # Skip reviews for alternatives - the LLM already captured why each is recommended
                        # This saves ~3-4s per candidate by removing the Tavily API call
                        cand['reviews'] = []
                        
                    except Exception as inner_e:
                        print(f"       -> Error enriching {name}: {inner_e}")

                # Run enrichment in parallel, limit to 2 to avoid API rate limits
                # Latency Optimization: Limit to top 10 candidates total
                enrichment_start = time.time()
                candidates_to_process = candidates[:10]
                with ThreadPoolExecutor(max_workers=5) as executor:
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
            "candidates": candidates[:10]  # Only return enriched candidates
        },
        "node_timings": existing_timings
    }
