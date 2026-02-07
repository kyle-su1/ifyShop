from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import AgentState
from app.agent.nodes import (
    node_user_intent_vision,
    node_discovery_runner,
    node_market_scout,
    node_skeptic_critique, 
    node_analysis_synthesis,
    node_response_formulation
)
from app.agent.nodes.router import node_router
from app.agent.nodes.chat import node_chat

# 1. Define the Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes (direct, no wrappers for now)
workflow.add_node("router_node", node_router)
workflow.add_node("vision_node", node_user_intent_vision)
workflow.add_node("research_node", node_discovery_runner)
workflow.add_node("market_scout_node", node_market_scout)
workflow.add_node("chat_node", node_chat)
workflow.add_node("skeptic_node", node_skeptic_critique)
workflow.add_node("analysis_node", node_analysis_synthesis)
workflow.add_node("response_node", node_response_formulation)

# 3. Define Edges (The Flow)

# Entry Point -> Router
workflow.set_entry_point("router_node")

# Router Logic
def route_intent(state: AgentState):
    """
    Routes based on router decision:
    - vision_search → Vision Node (full pipeline)
    - chat → Chat Node (respond only)
    - re_search → Chat Node (extracts prefs, then → Market Scout)
    - re_analysis → Chat Node (extracts prefs, then → Analysis)
    """
    decision = state.get("router_decision")
    if decision == "vision_search":
        return "vision_node"
    elif decision in ["chat", "re_search", "re_analysis"]:
        return "chat_node"  # Chat node handles all conversation types
    return "chat_node"  # Default fallback

workflow.add_conditional_edges(
    "router_node",
    route_intent,
    {
        "vision_node": "vision_node",
        "chat_node": "chat_node"
    }
)

# Chat Node Logic (Feedback Loop)
# Routes to downstream nodes based on loop_step set by chat node
def route_chat_loop(state: AgentState):
    """
    After chat node processes the message, route based on loop_step:
    - analysis_node: Re-analyze with new budget preferences
    - market_scout_node: Re-search with new visual preferences  
    - end: Just respond, no further processing
    """
    loop = state.get("loop_step", "end")
    if loop == "analysis_node":
        return "analysis_node"
    elif loop == "market_scout_node":
        return "market_scout_node"
    return END

workflow.add_conditional_edges(
    "chat_node",
    route_chat_loop,
    {
        "analysis_node": "analysis_node",
        "market_scout_node": "market_scout_node",
        END: END
    }
)

# Vision -> Research & Scout OR End (if detect_only)
def route_vision(state: AgentState):
    if state.get("detect_only"):
        return END
    return ["research_node", "market_scout_node"]

workflow.add_conditional_edges(
    "vision_node",
    route_vision,
    {
        "research_node": "research_node",
        "market_scout_node": "market_scout_node",
        END: END
    }
)

# Research -> Market Scout
workflow.add_edge("research_node", "market_scout_node")

# Market Scout -> Skeptic
workflow.add_edge("market_scout_node", "skeptic_node")

# Skeptic -> Analysis
workflow.add_edge("skeptic_node", "analysis_node")

# Analysis -> Response
workflow.add_edge("analysis_node", "response_node")

# Response -> End
workflow.add_edge("response_node", END)

# 4. Compile the Graph with Persistence
checkpointer = MemorySaver()
agent_app = workflow.compile(checkpointer=checkpointer)
