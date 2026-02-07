"""
SearchPreference Model

Tracks user's past preference choices to learn scoring weights over time.
Each record represents a preference pattern the user selected during a search.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class SearchPreference(Base):
    """
    Records a user's preference choice for learning future recommendations.
    
    Example: User searched for headphones and chose the "cheaper" alternative.
    This gets stored so future searches can boost price_weight automatically.
    """
    __tablename__ = "search_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    
    # Type of preference: "cheaper", "premium", "eco-friendly", "balanced"
    preference_type = Column(String, index=True)
    
    # The product that was ultimately chosen (for context)
    product_chosen = Column(String, nullable=True)
    
    # The original product being compared against
    original_product = Column(String, nullable=True)
    
    # Additional context (scores, alternatives considered, etc.)
    context_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
