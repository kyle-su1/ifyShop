from typing import Dict, Any
from app.agent.state import AgentState

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
import json

def node_skeptic_critique(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: The Skeptic (Critique & Verification)
    """
    print("--- 3. Executing Critique Node (The Skeptic) ---")
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception:
            pass

    log_debug("--- 3. Executing Critique Node (The Skeptic) ---")
    
    research_results = state.get('research_data', {})
    
    # --- Check Cache ---
    import hashlib
    from app.services.snowflake_cache import snowflake_cache_service
    
    # Generate stable key from research data
    data_str = json.dumps(research_results, sort_keys=True)
    items_hash = hashlib.md5(data_str.encode()).hexdigest()
    cache_key = f"skeptic:analysis:{items_hash}"
    
    cached_report = snowflake_cache_service.get(cache_key)
    if cached_report:
        log_debug(f"Critique Cache Hit! ({cache_key})")
        return {"risk_report": cached_report}
    # -------------------

    # Initialize Skeptic Agent
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY)
    
    prompt = f"""
    You are a cynical, skeptical shopping assistant. Your job is to find flaws, fake reviews, and pricing tricks.
    
    Analyze this research data:
    {json.dumps(research_results, indent=2)}
    
    Return a JSON object:
    {{
        "fake_review_likelihood": "High/Medium/Low + explanation",
        "price_integrity": "Is it a real deal or markup?",
        "hidden_flaws": ["List of specific complaints found"]
    }}
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content.replace('```json', '').replace('```', '').strip()
        risk_report = json.loads(content)
        log_debug(f"Critique Output: {risk_report}")
        
        # --- Store in Cache ---
        snowflake_cache_service.set(
            cache_key=cache_key,
            cache_type="skeptic_analysis",
            params={"data_hash": items_hash}, # Don't store full input if huge
            result=risk_report,
            ttl_minutes=30 
        )
        # ----------------------
        
    except Exception as e:
        print(f"Skeptic Error: {e}")
        log_debug(f"Skeptic Error: {e}")
        risk_report = {
            "fake_review_likelihood": "Unknown",
            "hidden_flaws": ["Could not analyze risks due to error"]
        }
    
    log_debug("Critique Node Completed")
    return {"risk_report": risk_report}
