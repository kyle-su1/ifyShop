from typing import Dict, Any, List
from app.agent.state import AgentState
from app.db.session import SessionLocal
from app.services.preference_service import get_learned_weights, merge_weights, save_choice, get_user_explicit_preferences
from app.agent.scoring import calculate_weighted_score
from app.agent.skeptic import SkepticAgent
from app.core.config import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

def node_analysis_synthesis(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Analysis & Synthesis (The "Brain")
    
    Responsibilities:
    1. Load user preferences (explicit + learned).
    2. Run Skeptic analysis on alternatives (if not done in Node 3).
    3. Calculate weighted scores for all products (Main + Alternatives).
    4. Rank products and generate final analysis.
    5. Save preference context (optional, happens on final choice usually, 
       but we can prep the data here).
    """
    print("--- 4. Executing Analysis Node (The Brain) ---")
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception:
            pass

    log_debug("--- 4. Executing Analysis Node (The Brain) ---")
    
    # Inputs
    research = state.get('research_data', {})
    risk = state.get('risk_report', {})
    market_scout = state.get('market_scout_data', {})
    user_id = 1 # TODO: Get from state when Auth is fully wired across graph
    
    # 1. Load User Preferences
    db = SessionLocal()
    final_weights = {}
    try:
        # Get explicit quals (from DB or State)
        state_prefs = state.get('user_preferences', {})
        
        # Determine User ID - try state, then session lookup, then default
        # user_id is hardcoded to 1 in many places for MVP
        db_prefs = get_user_explicit_preferences(db, user_id)
        
        # Merge explicit (State > DB)
        # If State has params, they override DB (e.g. current session tweaks)
        explicit_prefs = {**db_prefs, **state_prefs}
        
        # Get learned weights from past behavior
        learned_weights = get_learned_weights(db, user_id)
        
        # Merge everything
        final_weights = merge_weights(explicit_prefs, learned_weights)
        print(f"   [Analysis] Final Weights: {final_weights}")
        
    except Exception as e:
        print(f"   [Analysis] Error loading preferences: {e}")
        # Fallback
        state_prefs = state.get('user_preferences', {})
        final_weights = merge_weights(state_prefs, {})
        
    finally:
        db.close()
    print(f"   [Analysis] Final Weights (DB Skipped): {final_weights}")
        
    # 2. Analyze Alternatives (if available)
    alternatives = market_scout.get('candidates', [])
    
    # 2b. Add Main Product to analysis list
    # We construct a 'candidate-like' object for the main product to unify logic
    product_query = state.get('product_query', {})
    main_product_name = product_query.get('canonical_name') or product_query.get('product_name') or "Main Product"
    
    # Extract price for main product
    main_prices = research.get('competitor_prices', [])
    main_price_val = 0.0
    if main_prices:
         try:
             # competitor_prices from Node 2 structure: PriceOffer.dict()
             # PriceOffer uses 'price_cents' (integer in cents), NOT 'price'
             price_cents = main_prices[0].get('price_cents', 0)
             main_price_val = float(price_cents) / 100.0  # Convert cents to dollars
         except:
             pass
    
    # Extract reviews for main product
    main_reviews = research.get('reviews', [])

    # Try to find main product image/link from research prices or context
    main_image = None
    main_link = None
    if main_prices:
        main_image = main_prices[0].get('thumbnail') # SerpAPI often has this
        main_link = main_prices[0].get('url')

    # --- MAIN PRODUCT FALLBACKS ---
    # 1. Fallback Image from Reviews (if main has no image)
    if not main_image:
        # Check reviews for images
        for r in main_reviews:
            # r is a dict here (ReviewSnippet.dict())
            if r.get('images'):
                main_image = r['images'][0]
                print(f"   [Analysis] Used fallback image from reviews for Main Product.")
                break

    # 2. Main Price Text
    main_price_text = "Check Price"
    if main_price_val > 0:
        # Assuming CAD for now or extracting from first price offer
        curr = main_prices[0].get('currency', 'CAD') if main_prices else 'CAD'
        main_price_text = f"${main_price_val:.2f} {curr}"
    # ------------------------------

    if main_product_name:
        alternatives.append({
            "name": main_product_name,
            "reason": "Original Selection",
            "prices": [{"price": main_price_val}],
            "reviews": main_reviews,
            "is_main": True,
            "image_url": main_image,
            "purchase_link": main_link,
            "price_text": main_price_text
        })

    alternatives_scored = []
    
    # Get eco_context from research data
    eco_data = state.get('research_data', {}).get('eco_data', {})
    eco_context = eco_data.get('eco_context', '')
    if eco_context:
        print(f"   [Analysis] Eco data available ({len(eco_context)} chars)")
    
    print(f"   [Analysis] Scoring {len(alternatives)} candidates (including Main Product)...")
    log_debug(f"Scoring {len(alternatives)} candidates...")
    
    # Calculate Market Average Price across all candidates
    all_prices = []
    for alt in alternatives:
        prices_list = alt.get('prices', [])
        p_str = prices_list[0].get('price', 0) if prices_list else 0
        try:
            val = float(p_str)
            if val > 0:
                all_prices.append(val)
        except:
            pass
            
    market_avg = sum(all_prices) / len(all_prices) if all_prices else 0.0
    print(f"   [Analysis] Market Average Price: ${market_avg:.2f}")

    def process_candidate(alt):
        from app.agent.skeptic import Review, SkepticAgent
        # Initialize agent INSIDE the thread/process to avoid pickling issues with gRPC
        local_skeptic_agent = SkepticAgent(model_name=settings.MODEL_ANALYSIS)

        # Run Skeptic on alternative (Quantitative)
        reviews_data = alt.get('reviews', [])
        # Convert to Review objects
        valid_reviews = []
        for r in reviews_data:
            try:
                # Map ReviewSnippet fields to Review model
                review_dict = {
                    "source": r.get("source", "Unknown"),
                    "text": r.get("snippet", "") or r.get("text", ""),
                    "rating": r.get("rating"),
                    "date": r.get("date")
                }
                valid_reviews.append(Review(**review_dict))
            except Exception as e:
                # logger.warning(f"Skipping review: {e}")
                pass
        
        # Optimization: Limit to top 5 reviews to reduce LLM latency and token usage
        valid_reviews = valid_reviews[:5]
        
        sentiment_result = local_skeptic_agent.analyze_reviews(alt.get('name'), valid_reviews, eco_context)
        sentiment_data = sentiment_result.model_dump()
        
        # Extract features for scoring
        prices_list = alt.get('prices', [])
        price_str = prices_list[0].get('price', 0) if prices_list else 0
        try:
            price = float(price_str)
        except:
            price = 0.0
            
        score_obj = calculate_weighted_score(
            trust_score=sentiment_data.get('trust_score', 5.0),
            sentiment_score=sentiment_data.get('sentiment_score', 0.0),
            price_val=price,
            market_avg=market_avg, 
            weights=final_weights,
            eco_score=sentiment_data.get('eco_score', 0.5)
        )
        
        return {
            "name": alt.get('name'),
            "score_details": score_obj.model_dump(),
            "sentiment_summary": sentiment_data.get('summary'),
            "reason": alt.get('reason'),
            "image_url": alt.get('image_url'),          # Standard backend key
            "purchase_link": alt.get('purchase_link'),   # Standard backend key
            "image": alt.get('image_url'),          # Mapped for frontend (Alternatives)
            "link": alt.get('purchase_link'),       # Mapped for frontend (Alternatives)
            "price_text": alt.get('price_text'),    # Pass through for frontend
            "is_main": alt.get('is_main', False),       # Pass through for identification
            "price_val": price,                          # Pass through for display
            "eco_score": sentiment_data.get('eco_score', 0.5),  # Environmental friendliness
            "eco_notes": sentiment_data.get('eco_notes', '')     # Eco explanation
        }

    # Execute in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time

    start_time = time.time()
    print(f"   [Analysis] Processing {len(alternatives)} candidates in parallel...")
    
    # Reduce max_workers to 3 to avoid hitting Gemini Rate Limits (RPM) which cause exponential backoff
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_alt = {executor.submit(process_candidate, alt): alt for alt in alternatives}
        for future in as_completed(future_to_alt):
            try:
                result = future.result(timeout=20)
                alternatives_scored.append(result)
            except Exception as exc:
                alt = future_to_alt[future]
                print(f"   [Analysis] Error processing {alt.get('name')}: {exc}")
                log_debug(f"Error processing {alt.get('name')}: {exc}")

    # Sort by Total Score (for alternatives ranking)
    alternatives_scored.sort(key=lambda x: x['score_details']['total_score'], reverse=True)
    
    # Find the main product (user's selected item) - this should always be the "recommended_product"
    main_product = next((a for a in alternatives_scored if a.get('is_main')), None)
    
    # Top score (could be main or alternative)
    top_pick = alternatives_scored[0] if alternatives_scored else None
    
    # Use main product as the recommended product, fall back to top_pick if no main found
    display_product = main_product if main_product else top_pick
    
    # 3. Construct Analysis Object
    
    # Determine Verdict
    verdict = "Fair Price"
    if display_product:
        price_val = display_product.get('price_val', 0)
        if price_val > 0 and market_avg > 0:
            if price_val < market_avg * 0.9:
                verdict = "Great Deal"
            elif price_val > market_avg * 1.1:
                verdict = "Premium Price"

    analysis_object = {
        "match_score": display_product['score_details']['total_score'] if display_product else 0.0,
        "recommended_product": display_product['name'] if display_product else "None",
        "scoring_breakdown": display_product['score_details'] if display_product else {},
        "identified_product": display_product['name'] if display_product else "Unknown",
        "summary": display_product.get('sentiment_summary') if display_product else "Analysis complete.",
        
        # ACTIVE PRODUCT (Main Card) - Ensure keys match DashboardPage.jsx expectations
        "active_product": {
            "name": display_product['name'] if display_product else "Unknown",
            "image_url": display_product.get('image_url') if display_product else None,
            "purchase_link": display_product.get('purchase_link') if display_product else None,
            "price_text": display_product.get('price_text') if display_product else "Check Price",
            "detected_objects": [] # Populated by Vision/Lens if available, kept empty here
        },
        
        # PRICE ANALYSIS (Verdict)
        "price_analysis": {
            "verdict": verdict,
            "market_average": f"${market_avg:.2f}",
            "price_difference": f"{((display_product.get('price_val', 0) - market_avg) / market_avg * 100):.0f}%" if display_product and market_avg > 0 else "0%"
        },
        
        # Flag if a better alternative exists
        "better_alternative_exists": top_pick and main_product and top_pick['name'] != main_product['name'],
        "best_alternative": top_pick['name'] if top_pick and main_product and top_pick['name'] != main_product['name'] else None,
        "alternatives_ranked": [
            {
                "name": a['name'], 
                "score": a['score_details']['total_score'],
                "reason": a['reason'],
                "image": a.get('image_url'), # Hybrid key
                "link": a.get('purchase_link'), # Hybrid key
                "price_text": a.get('price_text')
            } 
            for a in alternatives_scored if not a.get('is_main')  # Exclude main from alternatives list
        ],
        "alternatives": [ # DashboardPage.jsx uses 'alternatives' for the mapping, NOT 'alternatives_ranked'
            {
               "name": a['name'],
               "score": a['score_details']['total_score'],
               "reason": a['reason'],
               "image": a.get('image_url'),
               "link": a.get('purchase_link'),
               "price_text": a.get('price_text')
            }
            for a in alternatives_scored if not a.get('is_main')
        ],
        "applied_preferences": final_weights
    }
    
    total_time = time.time() - start_time
    print(f"--- Analysis Node: Total time {total_time:.2f}s ---")
    log_debug("Analysis Node Completed")
    
    # Get existing timings and add this node's time
    existing_timings = state.get('node_timings', {}) or {}
    existing_timings['analysis'] = total_time
    
    return {
        "analysis_object": analysis_object, 
        "alternatives_analysis": alternatives_scored,
        "node_timings": existing_timings
    }
