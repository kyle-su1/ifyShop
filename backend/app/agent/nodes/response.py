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
    
    # Extract key metrics for prompt context
    trust_score = risk_report.get('trust_score', 5.0)
    
    prompt = f"""You are a friendly, empathetic shopping assistant. 
Your goal is to populate the dashboard with a final analysis.

=== MAIN PRODUCT ===
Name: {analysis.get('recommended_product', 'Unknown')}
Details: {json.dumps(analysis, indent=2)}
Risk Report: {json.dumps(risk_report, indent=2)}

=== ALTERNATIVES & COMPETITORS ===
{json.dumps(products_detail, indent=2)}

=== YOUR TASK ===
Generate a JSON object strictly matching the following schema. 
Do not include Markdown. Do not include 'main_product' wrapper key.
The root keys must trigger the specific frontend visualizers.

STRICT JSON OUTPUT FORMAT:
{{
    "outcome": "highly_recommended" OR "consider_alternatives",
    "identified_product": "The specific product name identified",
    "summary": "2-3 sentences. Is this a buy or pass? Explain why.",
    "price_analysis": {{
        "price_score": 0.0 to 1.0 (1.0 = great value),
        "verdict": "Good Deal / Overpriced / Standard",
        "details": "Price context vs market"
    }},
    "community_sentiment": {{
        "trust_score": {trust_score} (0-10 float),
        "summary": "What are users saying?",
        "red_flags": {json.dumps(risk_report.get('hidden_flaws', []))}
    }},
    "alternatives": [
        {{
            "name": "Alt Product Name",
            "score": 0.0 to 100.0,
            "reason": "Why consider this?"
        }}
    ]
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
        final_payload["outcome"] = "error"
        final_payload["summary"] = "We encountered an issue generating your recommendation. Please try again."
    
    log_debug("Response Node Completed")
    return {"final_recommendation": final_payload}


def _build_fallback_response(analysis: dict, alternatives_analysis: list, risk_report: dict) -> dict:
    """
    Build a structured response from raw data when LLM fails.
    This ensures the frontend always gets a valid response.
    """
    main_product = analysis.get('recommended_product', 'Unknown Product')
    match_score = analysis.get('match_score', 0)
    
    # Build alternatives list
    alternatives = []
    # Get details from alternatives_analysis if available
    alt_details = {a.get('name'): a for a in alternatives_analysis}
    
    for alt in analysis.get('alternatives_ranked', [])[1:4]:
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
