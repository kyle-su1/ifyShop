from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    parse_image,
    verify_item,
    get_prices,
    get_reviews,
    analyze_reviews,
    final_recommendation
)

def create_agent_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("parse_image", parse_image)
    workflow.add_node("verify_item", verify_item)
    workflow.add_node("get_prices", get_prices)
    workflow.add_node("get_reviews", get_reviews)
    workflow.add_node("analyze_reviews", analyze_reviews)
    workflow.add_node("final_recommendation", final_recommendation)

    # Define edges
    # For now, it's a linear flow
    workflow.set_entry_point("parse_image")
    workflow.add_edge("parse_image", "verify_item")
    workflow.add_edge("verify_item", "get_prices")
    workflow.add_edge("get_prices", "get_reviews")
    workflow.add_edge("get_reviews", "analyze_reviews")
    workflow.add_edge("analyze_reviews", "final_recommendation")
    workflow.add_edge("final_recommendation", END)

    # Compile the graph
    app = workflow.compile()
    
    return app

agent_app = create_agent_graph()
