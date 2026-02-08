from typing import Dict, Any
from app.agent.state import AgentState

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
import json

def node_skeptic_veto(state: AgentState) -> Dict[str, Any]:
    """
    Node 2.5: The Veto Check (Fail Fast)
    Before running expensive analysis, check if we should even proceed.
    """
    print("--- 2.5 Executing Veto Check (The Gatekeeper) ---")
    
    # --- VETO CHECK (State-Aware) ---
    from app.agent.skeptic import check_veto_status
    
    # We need candidates from Market Scout to perform Veto
    market_scout_data = state.get('market_scout_data', {})
    candidates = market_scout_data.get('candidates', [])
    user_prefs = state.get('user_preferences', {})
    loop_count = state.get('skeptic_loop_count', 0)
    
    veto_result = check_veto_status(candidates, user_prefs, loop_count)
    print(f"   [Veto] Decision: {veto_result.get('decision')} (Reason: {veto_result.get('reason')})")
    
    if veto_result.get('decision') == 'veto':
         print(f"   [Veto] 🛑 VETO TRIGGERED. Loop: {loop_count}. Mutation: {veto_result.get('better_search_query')}")
         # Return Veto Signal to State
         return {
             "skeptic_decision": "veto", 
             "skeptic_feedback_query": veto_result.get('better_search_query'),
             "skeptic_loop_count": loop_count + 1,
             "market_warning": None 
         }
    else:
         # Propagate warning if any
         market_warning = veto_result.get('market_warning')
         if market_warning:
              print(f"   [Veto] ⚠️ Proceeding with Market Warning: {market_warning}")
         
         return {
             "skeptic_decision": "proceed",
             "market_warning": market_warning
         }

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
    
    import time
    start_time = time.time()
    
    research_results = state.get('research_data', {})
    market_warning = state.get('market_warning') # Get warning from Veto node
    
    # --- Check Cache ---
    import hashlib
    from app.services.snowflake_cache import snowflake_cache_service
    
    # Generate stable key from research data
    data_str = json.dumps(research_results, sort_keys=True)
    items_hash = hashlib.md5(data_str.encode()).hexdigest()
    cache_key = f"skeptic:analysis:{items_hash}"
    
    cache_start = time.time()
    cached_report = snowflake_cache_service.get(cache_key)
    cache_time = time.time() - cache_start
    
    if cached_report:
        log_debug(f"Critique Cache Hit! ({cache_key})")
        print(f"--- Critique Node: Cache Hit in {cache_time:.2f}s ---")
        return {"risk_report": cached_report}
    # -------------------

    # Initialize Skeptic Agent

    # Initialize Skeptic Agent
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY)
    
    prompt = f"""
    You are a fair and balanced shopping analyst. Your job is to provide an honest assessment that helps users make informed decisions.
    
    Analyze this research data and look for BOTH positives and legitimate concerns:
    {json.dumps(research_results, indent=2)}
    
    GUIDELINES:
    - Most products are legitimate. Start with baseline trust score of 7.
    - Only flag genuine red flags with clear evidence.
    - A mix of positive and negative reviews is NORMAL and healthy.
    - Detailed, specific reviews (positive OR negative) are more trustworthy.
    - Price variations between retailers are normal market behavior.
    
    Return a JSON object:
    {{
        "trust_score": 7.0 (float 0-10, start at 7, adjust based on evidence. 8-10=excellent, 6-7=normal, below 5=real concerns),
        "fake_review_likelihood": "Low/Medium/High + brief explanation (only High if clear evidence)",
        "price_integrity": "Fair assessment of pricing - is it competitive for the category?",
        "hidden_flaws": ["Only list REAL concerns backed by review data, not speculation"]
    }}
    """
    
    try:
        llm_start = time.time()
        response = llm.invoke(prompt)
        llm_time = time.time() - llm_start
        print(f"--- Critique Node: LLM Analysis took {llm_time:.2f}s ---")
        
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
    
    total_time = time.time() - start_time
    print(f"--- Critique Node: Total time {total_time:.2f}s ---")
    
    log_debug("Critique Node Completed")
    
    # Get existing timings and add this node's time
    existing_timings = state.get('node_timings', {}) or {}
    existing_timings['critique'] = total_time
    
    return {
        "risk_report": risk_report, 
        "node_timings": existing_timings,
        "skeptic_decision": "proceed",
        "market_warning": market_warning if 'market_warning' in locals() else None
    }
