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
            "reason": alt.get("reason", "")
        })
    
    # Initialize Speaker Agent with MODEL_RESPONSE
    llm = ChatGoogleGenerativeAI(
        model=settings.MODEL_RESPONSE, 
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7  # Slightly creative for friendly responses
    )
    
    prompt = f"""You are a friendly, empathetic shopping assistant. 
Your job is to analyze the product the user is looking at, and suggest alternatives.

=== MAIN PRODUCT (What the user is looking at) ===
Product Name: {analysis.get('recommended_product', 'Unknown')}
Compatibility Score: {analysis.get('match_score', 0)}/100 (how well it matches user preferences)
Scoring Breakdown: {json.dumps(analysis.get('scoring_breakdown', {}), indent=2)}

=== MAIN PRODUCT DETAILED ANALYSIS (from Skeptic) ===
{json.dumps([p for p in products_detail if 'Original' in p.get('reason', '')], indent=2)}

=== ALTERNATIVE PRODUCTS (Suggestions) ===
{json.dumps([p for p in products_detail if 'Original' not in p.get('reason', '')], indent=2)}

Products Ranked: {json.dumps(analysis.get('alternatives_ranked', []), indent=2)}

=== RISK REPORT (for Main Product) ===
Fake Review Likelihood: {risk_report.get('fake_review_likelihood', 'Unknown')}
Price Integrity: {risk_report.get('price_integrity', 'Unknown')}
Hidden Flaws: {json.dumps(risk_report.get('hidden_flaws', []))}

=== USER PREFERENCES ===
{json.dumps(analysis.get('applied_preferences', {}), indent=2)}

=== YOUR TASK ===
Create a response that:
1. Gives a DETAILED ANALYSIS of the MAIN PRODUCT (the one user is looking at)
   - Summary, pros, cons, review sentiment, trust level
2. Shows the main product's compatibility score (how well it fits their preferences)
3. For EACH ALTERNATIVE, include a short summary so users can decide for themselves

Return ONLY valid JSON (no markdown, no extra text):
{{
    "main_product": {{
        "name": "The product user is looking at",
        "compatibility_score": 85.5,
        "summary": "Detailed 2-3 sentence analysis of this product...",
        "pros": ["Pro 1", "Pro 2", "Pro 3"],
        "cons": ["Con 1", "Con 2"],
        "price_analysis": {{
            "verdict": "Good value / Overpriced / Great deal",
            "warnings": ["Any pricing concerns"]
        }},
        "community_sentiment": {{
            "trust_level": "High / Medium / Low",
            "summary": "What real users say about this product...",
            "red_flags": ["Any review concerns"]
        }}
    }},
    "alternatives": [
        {{
            "name": "Alternative Product Name",
            "compatibility_score": 75.0,
            "summary": "Short 1-2 sentence description so user can decide for themselves",
            "pros": ["Key strength 1", "Key strength 2"],
            "cons": ["Key weakness"],
            "why_consider": "Why this might be better for some users"
        }}
    ],
    "verdict": "Final recommendation: Should user buy the main product or consider alternatives?"
}}
"""
    
    try:
        logger.info(f"Generating response with {settings.MODEL_RESPONSE}...")
        response = llm.invoke(prompt)
        content = response.content
        
        # Clean up response - remove markdown code blocks if present
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        content = content.strip()
        final_payload = json.loads(content)
        
        # Inject Vision Data into Final Payload
        product_query = state.get('product_query', {})
        final_payload['active_product'] = {
            "name": final_payload.get('identified_product'),
            "bounding_box": state.get('bounding_box'),
            "detected_objects": product_query.get('detected_objects', [])
        }

        logger.info(f"Successfully generated response for: {final_payload.get('identified_product')}")
        log_debug(f"Response Node Payload: {final_payload}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parse Error: {e}")
        logger.error(f"Raw content: {content[:500] if content else 'Empty'}")
        # Fallback with available data
        final_payload = _build_fallback_response(analysis, alternatives_analysis, risk_report)
        
    except Exception as e:
        logger.error(f"Response Generation Error: {e}")
        # Use fallback instead of exposing error details to frontend
        final_payload = _build_fallback_response(analysis, alternatives_analysis, risk_report)
        final_payload["verdict"] = "error"
        final_payload["main_product"]["summary"] = "We encountered an issue generating your recommendation. Please try again."
    
    log_debug("Response Node Completed")
    return {"final_recommendation": final_payload}


def _build_fallback_response(analysis: dict, alternatives_analysis: list, risk_report: dict) -> dict:
    """
    Build a structured response from raw data when LLM fails.
    This ensures the frontend always gets a valid response.
    """
    main_product = analysis.get('recommended_product', 'Unknown Product')
    match_score = analysis.get('match_score', 0)
    
    # Build alternatives list with summaries (skip the main product)
    alternatives = []
    # Get details from alternatives_analysis if available
    alt_details = {a.get('name'): a for a in alternatives_analysis}
    
    for alt in analysis.get('alternatives_ranked', [])[1:4]:
        name = alt.get('name')
        detail = alt_details.get(name, {})
        alternatives.append({
            "name": name,
            "compatibility_score": alt.get('score', 0),
            "summary": detail.get('sentiment_summary', 'Alternative option worth considering'),
            "pros": ["Competitive option"],
            "cons": [],
            "why_consider": alt.get('reason', 'Could be a good fit depending on your priorities')
        })
    
    return {
        "main_product": {
            "name": main_product,
            "compatibility_score": match_score,
            "summary": f"Based on your preferences, this product is a {match_score:.0f}% match for you.",
            "pros": ["Good match for your criteria"],
            "cons": risk_report.get('hidden_flaws', []),
            "price_analysis": {
                "verdict": risk_report.get('price_integrity', 'Unknown'),
                "warnings": []
            },
            "community_sentiment": {
                "trust_level": "Medium",
                "summary": f"Review authenticity: {risk_report.get('fake_review_likelihood', 'Unknown')}",
                "red_flags": risk_report.get('hidden_flaws', [])
            }
        },
        "alternatives": alternatives,
        "verdict": "highly_recommended" if match_score >= 70 else "consider_alternatives"
    }

