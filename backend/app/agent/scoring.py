"""
Scoring Logic for Product Analysis

Provides quantitative scoring for products based on:
1. Trustworthiness (from Skeptic)
2. Sentiment (from Reviews)
3. Price Competitiveness (relative to market)
4. User Preference Weights (learned + explicit)
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import math

class ProductScore(BaseModel):
    """
    Quantitative breakdown of a product's fit for the user.
    """
    trust_score: float = Field(..., description="0-10 score from Skeptic agent")
    sentiment_score: float = Field(..., description="-1 to 1 sentiment from Reviews")
    price_score: float = Field(..., description="0-1 normalized score (higher is better/cheaper)")
    
    # Weighted sub-components
    weighted_price: float = 0.0
    weighted_quality: float = 0.0
    weighted_trust: float = 0.0
    
    # Final score
    total_score: float = Field(..., description="0-100 final match score")


def calculate_price_score(price: float, market_average: float) -> float:
    """
    Normalize price score relative to market average.
    Lower price = Higher score.
    
    Formula: Logistic-like curve where avg price = 0.5 score.
    """
    if price <= 0 or market_average <= 0:
        return 0.5
    
    ratio = price / market_average
    
    # Relaxed linear mapping:
    # 0.0x avg price -> 1.0 score (Free)
    # 1.0x avg price -> 0.5 score
    # 2.0x avg price -> 0.0 score
    # Formula: score = 1.0 - 0.5 * ratio
    score = 1.0 - (0.5 * ratio)
    return max(0.0, min(1.0, score))


def calculate_weighted_score(
    trust_score: float,      # 0-10
    sentiment_score: float,  # -1 to 1
    price_val: float,
    market_avg: float,
    weights: Dict[str, float]
) -> ProductScore:
    """
    Compute final weighted score based on user preferences.
    """
    # 1. Normalize Inputs to 0-1 scale
    norm_trust = trust_score / 10.0
    norm_sentiment = (sentiment_score + 1) / 2.0  # Map -1..1 to 0..1
    norm_price = calculate_price_score(price_val, market_avg)
    
    # 2. Get Weights (default to 0.5 if missing)
    w_price = weights.get("price_sensitivity", 0.5)
    w_quality = weights.get("quality", 0.5)
    w_brand = weights.get("brand_reputation", 0.5)
    
    # 3. Calculate Component Contributions
    # Quality is defined by Sentiment + Trust
    quality_component = (norm_sentiment * 0.7 + norm_trust * 0.3) * w_quality
    
    # Price is defined by Price Score
    price_component = norm_price * w_price
    
    # Trust/Safety is foundational
    trust_component = norm_trust * w_brand
    
    # 4. Total Score Calculation
    total_weight = w_price + w_quality + w_brand
    if total_weight == 0:
        total_weight = 1.0
        
    raw_score = (quality_component + price_component + trust_component) / total_weight
    final_score = raw_score * 100
    
    return ProductScore(
        trust_score=trust_score,
        sentiment_score=sentiment_score,
        price_score=norm_price,
        weighted_price=price_component,
        weighted_quality=quality_component,
        weighted_trust=trust_component,
        total_score=round(final_score, 1)
    )
