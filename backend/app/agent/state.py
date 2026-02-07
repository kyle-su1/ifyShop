from typing import TypedDict, List, Optional, Any

class AgentState(TypedDict):
    image_data: str
    user_preferences: dict
    parsed_item: Optional[dict]
    verification_result: Optional[dict]
    search_results: List[dict]
    reviews: List[dict]
    reviews_summary: Optional[str]
    final_recommendation: Optional[str]
