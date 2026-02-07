"""
Preference Service

Handles learning user preferences from past choices and merging with explicit settings.
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


# Default weights for new users
DEFAULT_WEIGHTS = {
    "price_sensitivity": 0.5,
    "quality": 0.5,
    "eco_friendly": 0.3,
    "brand_reputation": 0.4,
}

# Preference type to weight mapping
PREFERENCE_TYPE_WEIGHTS = {
    "cheaper": {"price_sensitivity": 1.0, "quality": 0.3},
    "premium": {"price_sensitivity": 0.2, "quality": 1.0, "brand_reputation": 0.8},
    "eco-friendly": {"eco_friendly": 1.0, "price_sensitivity": 0.4},
    "balanced": {"price_sensitivity": 0.5, "quality": 0.5},
}


def get_learned_weights(db: Optional[Session], user_id: Optional[int]) -> Dict[str, float]:
    """
    Calculate weights based on user's past preference choices.
    
    Returns a dict like: {"price_sensitivity": 0.8, "quality": 0.3, ...}
    based on historical patterns.
    """
    if not db or not user_id:
        logger.info("No DB or user_id provided, returning default weights")
        return DEFAULT_WEIGHTS.copy()
    
    try:
        from app.models.search_preference import SearchPreference
        
        # Count preference types for this user
        prefs = db.query(
            SearchPreference.preference_type,
            func.count(SearchPreference.id).label('count')
        ).filter(
            SearchPreference.user_id == user_id
        ).group_by(
            SearchPreference.preference_type
        ).all()
        
        if not prefs:
            logger.info(f"No past preferences for user {user_id}, using defaults")
            return DEFAULT_WEIGHTS.copy()
        
        # Calculate weighted average based on frequency
        total_count = sum(p.count for p in prefs)
        learned = DEFAULT_WEIGHTS.copy()
        
        for pref_type, count in prefs:
            weight_contribution = count / total_count
            type_weights = PREFERENCE_TYPE_WEIGHTS.get(pref_type, {})
            
            for key, value in type_weights.items():
                if key in learned:
                    # Blend the learned weight with the type's ideal weight
                    learned[key] = learned[key] * (1 - weight_contribution) + value * weight_contribution
        
        logger.info(f"Learned weights for user {user_id}: {learned}")
        return learned
        
    except Exception as e:
        logger.warning(f"Error getting learned weights: {e}")
        return DEFAULT_WEIGHTS.copy()


def merge_weights(
    explicit: Dict[str, float], 
    learned: Dict[str, float],
    explicit_priority: float = 0.7
) -> Dict[str, float]:
    """
    Merge explicit user preferences with learned preferences.
    
    Args:
        explicit: User-set preferences (from User.preferences)
        learned: Calculated from past choices
        explicit_priority: How much to weight explicit vs learned (0.7 = 70% explicit)
    
    Returns:
        Merged weight dictionary
    """
    merged = DEFAULT_WEIGHTS.copy()
    
    for key in merged:
        explicit_val = explicit.get(key, DEFAULT_WEIGHTS[key])
        learned_val = learned.get(key, DEFAULT_WEIGHTS[key])
        merged[key] = explicit_val * explicit_priority + learned_val * (1 - explicit_priority)
    
    return merged


def save_choice(
    db: Optional[Session],
    user_id: Optional[int],
    preference_type: str,
    product_chosen: str,
    original_product: str,
    metadata: Optional[Dict] = None
) -> bool:
    """
    Record a user's preference choice for future learning.
    
    Returns True if saved successfully, False otherwise.
    """
    if not db or not user_id:
        logger.info("No DB or user_id, skipping preference save")
        return False
    
    try:
        from app.models.search_preference import SearchPreference
        
        pref = SearchPreference(
            user_id=user_id,
            preference_type=preference_type,
            product_chosen=product_chosen,
            original_product=original_product,
            context_data=metadata or {}
        )
        db.add(pref)
        db.commit()
        logger.info(f"Saved preference: user={user_id}, type={preference_type}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving preference: {e}")
        db.rollback()
        return False


def get_user_explicit_preferences(db: Optional[Session], user_id: Optional[int]) -> Dict[str, float]:
    """
    Load explicit preferences from User.preferences JSON column.
    """
    if not db or not user_id:
        return DEFAULT_WEIGHTS.copy()
    
    try:
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.preferences:
            return {**DEFAULT_WEIGHTS, **user.preferences}
        return DEFAULT_WEIGHTS.copy()
    except Exception as e:
        logger.warning(f"Error loading user preferences: {e}")
        return DEFAULT_WEIGHTS.copy()
