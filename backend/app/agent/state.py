from typing import TypedDict, List, Optional, Any

class AgentState(TypedDict):
    """
    Represents the state of the shopping suggester agent workflow.
    This dict is passed between nodes in the graph, accumulating data.
    """
    # Initial Inputs
    user_query: str
    image_base64: str
    user_preferences: dict  # e.g. {'price': 0.8, 'quality': 0.9}

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

    # Node 5: Response (The Speaker) - Final Output
    final_recommendation: Optional[dict]
