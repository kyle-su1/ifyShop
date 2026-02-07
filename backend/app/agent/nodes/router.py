from typing import Dict, Any
from app.agent.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import logging

logger = logging.getLogger(__name__)

async def node_router(state: AgentState) -> Dict[str, Any]:
    """
    Classifies the user's intent to route to the appropriate node.
    """
    logger.info("ROUTER: Determining intent...")
    
    user_query = state.get("user_query", "")
    image_base64 = state.get("image_base64")
    chat_history = state.get("chat_history", [])
    
    # 1. New Visual Search (Image + No History/First Message)
    if image_base64 and (not chat_history or len(chat_history) == 0):
        logger.info("ROUTER: New image detected -> vision_search")
        return {"router_decision": "vision_search"}

    # 2. Use LLM to classify intent for text/follow-ups
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    system_prompt = """You are the Router for a Shopping Assistant. Classify the user's latest message into one of these categories:

    1. 'vision_search': User uploaded an image or wants to analyze a product in an image (if image is present).
    2. 'chat': General conversation, questions about the product, or small talk.
    3. 'update_preferences': User explicitly states a preference (e.g., "I hate red", "I prefer Nike", "My budget is $100").
    4. 'market_scout_search': User wants to find DIFFERENT products, alternatives, or modify the search filters (e.g., "Find cheaper ones", "Show me blue ones instead").
    
    Output ONLY the category name.
    """
    
    human_prompt = f"""
    User Message: {user_query}
    Has Image: {bool(image_base64)}
    Chat History Length: {len(chat_history)}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        decision = await chain.ainvoke({})
        decision = decision.strip().lower()
        
        # Fallback for safety
        valid_decisions = ["vision_search", "chat", "update_preferences", "market_scout_search"]
        if decision not in valid_decisions:
            logger.warning(f"ROUTER: Invalid decision '{decision}', defaulting to 'chat'")
            decision = "chat"
            
        logger.info(f"ROUTER: Decision -> {decision}")
        return {"router_decision": decision}
        
    except Exception as e:
        logger.error(f"ROUTER: Error in classification: {e}")
        return {"router_decision": "chat"} # Default fallback
