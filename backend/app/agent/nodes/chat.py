from typing import Dict, Any, List
from app.agent.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.preference_service import get_user_explicit_preferences, merge_weights
# from app.db.session import SessionLocal # Avoid circular import if possible, use dependency injection pattern or import inside
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
import json
import os
import logging

logger = logging.getLogger(__name__)

async def node_chat(state: AgentState) -> Dict[str, Any]:
    """
    Node 6: Chat
    Handles general conversation and preference updates.
    
    Routes based on router_decision:
    - chat: Respond and END
    - re_search: Extract visual prefs → Market Scout (Node 2)
    - re_analysis: Extract budget prefs → Analysis (Node 4)
    """
    logger.info("--- Executing Chat Node ---")
    
    user_query = state.get("user_query")
    router_decision = state.get("router_decision")
    chat_history = state.get("chat_history", [])
    session_id = state.get("session_id")
    
    # Initialize return values
    loop_step = "end"
    new_prefs = {}
    search_criteria = {}
    
    # 1. Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # 2. Handle Re-Analysis (Budget/Price preferences → Node 4)
    if router_decision == "re_analysis":
        logger.info("CHAT: Extracting budget preferences for re-analysis")
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Budget Preference Extractor. Analyze the user's message and extract budget-related preferences.

Return a JSON object with these possible keys:
- max_budget: number (if user mentions a dollar amount, e.g., "$120" → 120)
- price_sensitivity: float 0.0-1.0 (0.9 if user wants cheap, 0.1 if price doesn't matter)
- prefer_cheaper: boolean (true if user explicitly asks for cheaper options)

Examples:
- "I only have $120" → {{"max_budget": 120, "price_sensitivity": 0.9}}
- "Find eco-friendly ones" → {{"eco_friendly": 0.9, "price_sensitivity": 0.5}}
- "I care about sustainability" → {{"eco_friendly": 1.0}}
- "My budget is tight" → {{"price_sensitivity": 0.85}}
- "Show me the most affordable" → {{"price_sensitivity": 1.0, "prefer_cheaper": true}}

Return ONLY valid JSON, no markdown."""),
            ("human", "{user_query}")
        ])
        
        chain = extraction_prompt | llm | StrOutputParser()
        try:
            result = await chain.ainvoke({"user_query": user_query})
            cleaned_result = result.strip()
            if cleaned_result.startswith("```"):
                lines = cleaned_result.split("\n")
                if len(lines) >= 3:
                    cleaned_result = "\n".join(lines[1:-1])
            
            new_prefs = json.loads(cleaned_result)
            logger.info(f"CHAT: Extracted budget prefs: {new_prefs}")
            loop_step = "analysis_node"
            
        except Exception as e:
            logger.error(f"CHAT: Failed to extract budget prefs: {e}")
            new_prefs = {"price_sensitivity": 0.8}  # Default to price-conscious
            loop_step = "analysis_node"

    # 3. Handle Re-Search (Visual/Attribute preferences OR strict budget → Node 2)
    elif router_decision == "re_search":
        logger.info("CHAT: Extracting visual preferences for re-search")
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Preference Extractor for a Shopping Assistant. Analyze the user's message and extract ALL relevant preferences.

Return a JSON object with these possible keys:
- exclude_colors: list of colors to avoid
- prefer_colors: list of preferred colors
- prefer_brands: list of preferred brands
- exclude_brands: list of brands to avoid
- style_keywords: list of style descriptors (e.g., "modern", "minimalist")
- max_budget: number (if user mentions specific dollar amount)
- eco_friendly: float 0.0-1.0 (1.0 if user explicitly asks for sustainable/eco-friendly options)

Examples:
- "I don't like red" -> {{"exclude_colors": ["red"]}}
- "Show me blue ones" -> {{"prefer_colors": ["blue"]}}
- "I prefer Nike" -> {{"prefer_brands": ["Nike"]}}
- "I like Panasonic" -> {{"prefer_brands": ["Panasonic"]}}
- "Sony is better" -> {{"prefer_brands": ["Sony"]}}
- "I want sustainable products" -> {{"eco_friendly": 1.0}}
- "I only have $120" -> {{"max_budget": 120}}

Return ONLY valid JSON, no markdown."""),
            ("human", "{user_query}")
        ])
        
        chain = extraction_prompt | llm | StrOutputParser()
        try:
            result = await chain.ainvoke({"user_query": user_query})
            cleaned_result = result.strip()
            if cleaned_result.startswith("```"):
                lines = cleaned_result.split("\n")
                if len(lines) >= 3:
                    cleaned_result = "\n".join(lines[1:-1])
            
            search_criteria = json.loads(cleaned_result)
            logger.info(f"CHAT: Extracted search prefs: {search_criteria}")
            
            # If budget was extracted, also save it to new_prefs
            if search_criteria.get('max_budget'):
                new_prefs['max_budget'] = search_criteria['max_budget']
                new_prefs['price_sensitivity'] = 0.9  # User specified budget, so price-sensitive
            
            loop_step = "market_scout_node"
            
        except Exception as e:
            logger.error(f"CHAT: Failed to extract search prefs: {e}")
            loop_step = "market_scout_node"  # Still re-search, just without specific criteria

    # 4. Update Database with preferences (if any)
    if new_prefs:
        try:
            with SessionLocal() as db:
                from app.models.session import Session as SessionModel
                from app.models.user import User
                
                user_id = 1  # MVP hardcoded
                if session_id:
                    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
                    if session_obj and session_obj.user_id:
                        user_id = session_obj.user_id
                
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    current_prefs = user.preferences or {}
                    current_prefs.update(new_prefs)
                    user.preferences = current_prefs
                    db.commit()
                    logger.info(f"CHAT: Updated DB preferences for user {user_id}: {new_prefs}")
                    
        except Exception as e:
            logger.error(f"CHAT: Failed to update DB preferences: {e}")

    # 5. Generate Response
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    analysis = state.get("analysis_object")
    
    # Build context-aware system prompt
    if router_decision == "re_analysis":
        system_text = f"""You are a helpful Shopping Assistant. The user just updated their budget preferences.
        
Extracted preferences: {new_prefs}

Confirm that you understood their budget constraint and let them know you're re-analyzing the products with their new preferences. Be concise and helpful."""
    elif router_decision == "re_search":
        system_text = f"""You are a helpful Shopping Assistant. The user wants different products based on their preferences.
        
Extracted preferences: {search_criteria}

Confirm that you understood their preferences and let them know you're searching for new alternatives. Be concise and helpful."""
    else:
        system_text = """You are a helpful Shopping Assistant. 
You have access to the user's current analysis session.

If the user is asking a question about the product, answer it based on the analysis.
If the user is just chatting, be friendly.

Keep responses concise and helpful."""
    
    if analysis:
        system_text += f"\n\nCurrent Analysis Context: {str(analysis)[:500]}"  # Limit context size
    
    def map_message(role, content):
        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        return HumanMessage(content=content)

    messages = [SystemMessage(content=system_text)]
    for msg in chat_history[-5:]:
        messages.append(map_message(msg.get("role"), msg.get("content")))
    messages.append(HumanMessage(content=user_query))
    
    chain = llm | StrOutputParser()
    response = await chain.ainvoke(messages)
    
    # 6. Merge preferences into state for downstream nodes
    state_prefs = state.get("user_preferences", {})
    state_prefs.update(new_prefs)
    
    return {
        "chat_history": chat_history + [{"role": "user", "content": user_query}, {"role": "assistant", "content": response}],
        "final_recommendation": {"chat_response": response},
        "user_preferences": state_prefs,
        "search_criteria": search_criteria,  # For Market Scout
        "loop_step": loop_step
    }
