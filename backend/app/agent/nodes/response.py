from typing import Dict, Any
from app.agent.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

def node_response_formulation(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: Response Formulation (The "Speaker")
    
    Takes data from:
    - Node 3: risk_report (fake_review_likelihood, hidden_flaws)
    - Node 4: analysis_object (scores, rankings), alternatives_analysis (pros, cons, summary)
    
    Outputs a friendly, human-readable JSON for the frontend.
    """
    print("--- 5. Executing Response Node (The Speaker) ---")
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception:
            pass

    log_debug("--- 5. Executing Response Node (The Speaker) ---")
    
    # Get data from previous nodes
    analysis = state.get('analysis_object', {})
    alternatives_analysis = state.get('alternatives_analysis', [])
    risk_report = state.get('risk_report', {})
    
    # Build context from Node 4's detailed analysis
    products_detail = []
    for alt in alternatives_analysis:
        products_detail.append({
            "name": alt.get("name"),
            "score": alt.get("score_details", {}).get("total_score", 0),
            "summary": alt.get("sentiment_summary", ""),
            "reason": alt.get("reason", ""),
            "image": alt.get("image_url"),
            "link": alt.get("purchase_link"),
            "price_text": alt.get("score_details", {}).get("price_val", 0), # Raw value for LLM context
            "eco_score": alt.get("eco_score", 0.5),
            "eco_notes": alt.get("eco_notes", "")
        })
    
    # Initialize Speaker Agent with MODEL_RESPONSE
    llm = ChatGoogleGenerativeAI(
        model=settings.MODEL_RESPONSE, 
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7  # Slightly creative for friendly responses
    )
    
    # Extract key metrics for prompt context
    trust_score = risk_report.get('trust_score', 5.0)
    match_score = analysis.get('match_score', 50)
    
    prompt = f"""You are a friendly, helpful shopping assistant.
Your goal is to help the user make a confident purchase decision.

=== MAIN PRODUCT ===
Name: {analysis.get('recommended_product', 'Unknown')}
Match Score: {match_score}/100
Details: {json.dumps(analysis, indent=2)}
Risk Report: {json.dumps(risk_report, indent=2)}

=== ALTERNATIVES & COMPETITORS (Data) ===
{json.dumps(products_detail, indent=2)}

=== DECISION GUIDELINES ===
Choose the outcome based on match_score:
- "highly_recommended": Score >= 70 OR trust_score >= 7 (this is a solid choice!)
- "recommended": Score 50-69 (good option with minor caveats)
- "consider_alternatives": Score < 50 AND trust_score < 5 (significant concerns exist)

BE ENCOURAGING when the product is decent. Most products work fine for most users.
Only use "consider_alternatives" if there are MAJOR red flags or the score is truly low.

=== YOUR TASK ===
Generate a JSON object strictly matching the schema below.
IMPORTANT:
1. You MUST include up to 3 alternatives from the provided data in the 'alternatives' list. Do not filter them out unless they are duplicates.
2. Copy 'image' and 'link' fields from the data above exactly as provided. Do not invent links.

JSON OUTPUT FORMAT:
{{
    "outcome": "highly_recommended" OR "recommended" OR "consider_alternatives",
    "identified_product": "The specific product name",
    "summary": "2-3 positive, helpful sentences. Focus on what the product does well first, then any minor caveats.",
    "price_analysis": {{
        "price_score": 0.0 to 1.0 (1.0 = great value),
        "verdict": "Good Deal / Fair Price / Premium",
        "details": "Price context vs market"
    }},
    "community_sentiment": {{
        "trust_score": {trust_score},
        "summary": "What are users saying? Lead with positives.",
        "red_flags": {json.dumps(risk_report.get('hidden_flaws', [])[:3])}
    }},
    \"alternatives\": [
        {{
            \"name\": \"Alt Product Name\",
            \"score\": 0.0 to 100.0,
            \"reason\": \"Why consider this?\",
            \"image\": \"URL_FROM_DATA\",
            \"link\": \"URL_FROM_DATA\",
            \"price_text\": \"$123.00 CAD\",
            \"eco_score\": 0.0 to 1.0 (environmental friendliness)
        }}
    ]
}}
"""
    
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Generating response with {settings.MODEL_RESPONSE}...")
        llm_start = time.time()
        response = llm.invoke(prompt)
        llm_time = time.time() - llm_start
        print(f"--- Response Node: LLM Generation took {llm_time:.2f}s ---")
        
        content = response.content
        
        # Clean up response
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        content = content.strip()
        final_payload = json.loads(content)
        
        # Inject Vision Data & Main Product Link/Image into Final Payload
        # We need to find the main product's metadata from alternatives_analysis list
        main_prod_meta = next((item for item in alternatives_analysis if item.get("is_main")), {})
        
        product_query = state.get('product_query', {})
        detected_objects = product_query.get('detected_objects', [])
        bbox = detected_objects[0].get('bounding_box') if detected_objects else None
        
        final_payload['active_product'] = {
            "name": final_payload.get('identified_product'),
            "bounding_box": bbox,
            "detected_objects": detected_objects,
            "image_url": main_prod_meta.get("image_url"),     # New field
            "purchase_link": main_prod_meta.get("purchase_link"), # New field
            "price_text": f"${main_prod_meta.get('price_val', 0):.2f}" if main_prod_meta.get('price_val') else "Check Price",
            "eco_score": main_prod_meta.get("eco_score", 0.5), # Propagated field
            "eco_notes": main_prod_meta.get("eco_notes", "")   # Propagated field
        }

        # Double check alternatives have links (sometimes LLM hallucinates or drops them)
        # We enforce them from our source data just in case
        for alt in final_payload.get('alternatives', []):
            matching_source = next((p for p in products_detail if p['name'] == alt['name']), None)
            if matching_source:
                alt['image'] = matching_source.get('image')
                alt['link'] = matching_source.get('link')
        
        # Override alternatives with full data from analysis_object (includes score_breakdown)
        # This ensures all scoring data from Node 4 is preserved
        if analysis.get('alternatives'):
            final_payload['alternatives'] = analysis['alternatives']

        logger.info(f"Successfully generated response for: {final_payload.get('identified_product')}")
        log_debug(f"Response Node Payload: {final_payload}")
        
    except json.JSONDecodeError as e:
        print(f"   [Response] JSON Parse Error: {e}")
        # Fallback with available data
        final_payload = _build_fallback_response(analysis, alternatives_analysis, risk_report)
        
    except Exception as e:
        print(f"   [Response] Error: {e}")
        # Use fallback instead of exposing error details to frontend
        final_payload = _build_fallback_response(analysis, alternatives_analysis, risk_report)
        final_payload["outcome"] = "error"
        final_payload["summary"] = "We encountered an issue generating your recommendation. Please try again."
    
    total_time = time.time() - start_time
    print(f"--- Response Node: Total time {total_time:.2f}s ---")
    log_debug("Response Node Completed")
    
    # Get existing timings and add this node's time
    existing_timings = state.get('node_timings', {}) or {}
    existing_timings['response'] = total_time
    
    # Calculate Total Runtime (sequential: vision -> research -> scout, parallel: critique||analysis, then response)
    # Sequential path: vision + research + market_scout + max(critique, analysis) + response
    vision_time = existing_timings.get('vision', 0)
    research_time = existing_timings.get('research', 0)
    scout_time = existing_timings.get('market_scout', 0)
    critique_time = existing_timings.get('critique', 0)
    analysis_time = existing_timings.get('analysis', 0)
    response_time = existing_timings.get('response', 0)
    
    # Parallel nodes count as max of the two (they run simultaneously)
    parallel_time = max(critique_time, analysis_time)
    total_runtime = vision_time + research_time + scout_time + parallel_time + response_time
    
    existing_timings['total'] = total_runtime
    print(f"=== TOTAL AGENT RUNTIME: {total_runtime:.2f}s ===")
    print(f"    Vision: {vision_time:.2f}s | Research: {research_time:.2f}s | Scout: {scout_time:.2f}s")
    print(f"    Critique: {critique_time:.2f}s | Analysis: {analysis_time:.2f}s | Response: {response_time:.2f}s")
    
    # Add timing info to final payload for frontend
    final_payload['timing'] = existing_timings
    
    # --- REFINEMENT BADGE LOGIC ---
    skeptic_count = state.get('skeptic_loop_count', 0)
    market_warning = state.get('market_warning')
    
    if skeptic_count > 0:
        final_payload['was_refined'] = True
        final_payload['refinement_reason'] = "We detected low-quality initial results, so we automatically refined the search to find better options."
        
    if market_warning:
        # If there's a specific warning and we refined, append it
        final_payload['refinement_context'] = market_warning
        
    return {"final_recommendation": final_payload, "node_timings": existing_timings}


def _build_fallback_response(analysis: dict, alternatives_analysis: list, risk_report: dict) -> dict:
    """
    Build a structured response from raw data when LLM fails.
    This ensures the frontend always gets a valid response.
    """
    print("   [Response] Using Fail-Safe Fallback Response Generator")
    main_product = analysis.get('recommended_product', 'Unknown Product')
    match_score = analysis.get('match_score', 0)
    
    # Build alternatives list
    alternatives = []
    # Get details from alternatives_analysis if available
    alt_details = {a.get('name'): a for a in alternatives_analysis}
    
    for alt in analysis.get('alternatives_ranked', [])[:3]:
        name = alt.get('name')
        detail = alt_details.get(name, {})
        alternatives.append({
            "name": name,
            "score": alt.get('score', 0),
            "reason": alt.get('reason', 'Alternative option')
        })
    
    return {
        "outcome": "highly_recommended" if match_score >= 70 else "consider_alternatives",
        "identified_product": main_product,
        "summary": f"Based on your preferences, this product is a {match_score:.0f}% match for you.",
        "price_analysis": {
            "price_score": 0.5,
            "verdict": risk_report.get('price_integrity', 'Unknown'),
            "details": "Price analysis unavailable"
        },
        "community_sentiment": {
            "trust_score": 5.0,
            "summary": f"Review authenticity: {risk_report.get('fake_review_likelihood', 'Unknown')}",
            "red_flags": risk_report.get('hidden_flaws', [])
        },
        "alternatives": alternatives
    }
