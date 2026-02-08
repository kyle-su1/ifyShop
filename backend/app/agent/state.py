from typing import TypedDict, List, Optional, Any, Annotated

class AgentState(TypedDict):
    """
    Represents the state of the shopping suggester agent workflow.
    This dict is passed between nodes in the graph, accumulating data.
    """
    # Initial Inputs
    user_query: str
    image_base64: str
    user_preferences: dict  # e.g. {'price': 0.8, 'quality': 0.9}
    user_id: Optional[str] # Auth0 User ID or Internal ID

    # Intermediary State - Populated by nodes as we go
    
    # Node 1: Vision (The Eye)
    product_query: Optional[dict] 
    # Structure: {
    #   'product_name': str,
    #   'bounding_box': list,
    #   'context': str 
    # }

    # Node 2a: Discovery (The Runner)
    research_data: Optional[dict]
    # Structure: {
    #   'search_results': list, 
    #   'reviews': list,
    #   'competitor_prices': list
    # }

    # Node 2b: Market Scout (The Explorer)
    market_scout_data: Optional[dict]
    # Structure: {
    #    'strategy': str,
    #    'raw_search_results': list
    # }

    # Node 3: Skeptic (Critique)
    risk_report: Optional[dict]
    # Structure: {
    #   'fake_review_likelihood': str,
    #   'price_integrity': str,
    #   'hidden_flaws': list
    # }

    # Node 4: Analysis (The Brain)
    analysis_object: Optional[dict]
    # Structure: {
    #   'match_score': float,
    #   'warnings': list, 
    #   'alternatives_scored': list
    # }
    
    # New: Detailed analysis of alternatives from Skeptic
    alternatives_analysis: Optional[List[dict]]
    # Structure: List of ReviewSentiment dicts corresponding to candidates

    
    # State-Aware Veto Control
    skeptic_loop_count: int = 0
    skeptic_decision: Optional[str] = "proceed" # 'veto' or 'proceed'
    skeptic_feedback_query: Optional[str] = None
    market_warning: Optional[str] = None

    # Node 6: Chat & Router

    # Node 6: Chat & Router
    session_id: Optional[str]
    chat_history: List[dict] # List of messages: {'role': 'user', 'content': '...'}
    router_decision: Optional[str] # 'vision_search', 'chat', 'update_preferences', 'market_scout_search'
    loop_step: Optional[str] # Control flow signal from Chat Node: 'analysis_node', 'market_scout_node', 'end'
    
    # Control Flags for Two-Stage Pipeline
    detect_only: bool = False # If True, stop after Vision Node
    skip_vision: bool = False # If True, skip Vision Node (used for Deep Analysis stage)

    # Node 5: Response (The Speaker) - Final Output
    final_recommendation: Optional[dict]
    
    # Performance Tracking
    node_timings: Annotated[dict, lambda a, b: {**(a or {}), **b}] # {node_name: time_seconds} for total runtime calculation
