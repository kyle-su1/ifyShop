from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# --- Data Models ---

class Review(BaseModel):
    source: str = Field(..., description="Source of the review (e.g., Amazon, Reddit, YouTube)")
    text: str = Field(..., description="The content of the review")
    rating: Optional[float] = Field(None, description="Rating normalized to 1-5 scale if available")
    date: Optional[str] = Field(None, description="Date of the review")

class ReviewSentiment(BaseModel):
    summary: str = Field(..., description="Concise human-readable summary of the consensus (max 3 sentences)")
    trust_score: float = Field(..., description="0.0 to 10.0 score indicating how trustworthy the reviews are (10=authentic, 0=fake/bot)")
    sentiment_score: float = Field(..., description="-1.0 (Negative) to 1.0 (Positive) sentiment score")
    red_flags: List[str] = Field(default_factory=list, description="List of suspicious patterns detected (e.g., 'Repetitive phrasing', 'All 5-stars on same day')")
    pros: List[str] = Field(default_factory=list, description="Key advantages mentioned by real users")
    cons: List[str] = Field(default_factory=list, description="Key flaws mentioned by real users")
    verdict: str = Field(..., description="One-line final verdict (e.g., 'Solid buy', 'Avoid - Likely scams', 'Good but overpriced')")

# --- Agent Logic ---

from app.core.config import settings

class SkepticAgent:
    def __init__(self, model_name: Optional[str] = None):
        # Default to settings model if not provided
        self.model_name = model_name or settings.MODEL_REASONING
        api_key = settings.GOOGLE_API_KEY
        
        if not api_key:
             logger.warning("GOOGLE_API_KEY not set. Skeptic Agent will fail if invoked.")
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.1, # Low temperature for objective analysis
            google_api_key=api_key,
            max_retries=2,
        )
        
        self.parser = PydanticOutputParser(pydantic_object=ReviewSentiment)

    def analyze_reviews(self, product_name: str, reviews: List[Review]) -> ReviewSentiment:
        """
        Analyzes a list of reviews to determine authenticity and sentiment.
        """
        if not reviews:
             return ReviewSentiment(
                 summary="No reviews available for analysis.",
                 trust_score=5.0,  # Neutral, not suspicious
                 sentiment_score=0.0,
                 red_flags=[],
                 pros=[],
                 cons=[],
                 verdict="Needs more reviews"
             )

        # Format reviews for the prompt
        reviews_context = "\n---\n".join(
            [f"Source: {r.source}\nRating: {r.rating}/5\nDate: {r.date}\nContent: {r.text}" for r in reviews]
        )
        
        system_prompt = """You are 'The Skeptic', a fair and balanced product analyst.
Your goal is to analyze product reviews and provide an honest assessment of {product_name}.

Be BALANCED in your analysis - look for both genuine positives AND legitimate concerns.
Most products have both pros and cons. Your job is to surface them fairly, not to be pessimistic.

CONSIDER THESE FACTORS:
- Detailed, specific reviews (positive OR negative) are more trustworthy than vague ones.
- A mix of ratings (some 5-star, some 3-star) is normal and healthy.
- Look for consistent themes across multiple reviews.
- New products may have fewer reviews - this is not automatically suspicious.

RED FLAGS (only flag if clearly present):
- Obvious fake reviews with identical phrasing copy-pasted.
- Extreme mismatch between rating and text (5 stars but complaining).
- Clear evidence of paid/incentivized reviews stated in the text.

SCORING GUIDELINES:
- Trust Score (0-10): Start at 7 as baseline for normal products. Deduct for clear red flags, add for detailed authentic feedback.
  - 8-10: Well-reviewed, authentic feedback with specifics
  - 6-7: Normal product with typical review mix  
  - 4-5: Some concerns but usable feedback
  - 0-3: Clear evidence of manipulation
- Sentiment Score (-1 to 1): Weighted average of review sentiment.

BE FAIR. Most products deserve a trust score of 6-8 unless there are clear problems.
Output the result in the specified JSON format.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Here are the collected reviews for '{product_name}':\n\n{reviews_context}\n\n{format_instructions}")
        ])

        chain = prompt | self.llm | self.parser

        try:
            logger.info(f"Analyzing {len(reviews)} reviews for {product_name}...")
            result = chain.invoke({
                "product_name": product_name,
                "reviews_context": reviews_context,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"Skeptic Agent Analysis Failed: {e}")
            # Fallback for robustness
            return ReviewSentiment(
                summary="Error occurred during AI analysis of reviews.",
                trust_score=0.0,
                sentiment_score=0.0,
                red_flags=[f"System Error: {str(e)}"],
                msg="Analysis failed",
                pros=[],
                cons=[],
                verdict="Error"
            )

# Convenience function
log_file = "/app/debug_output.txt"
def log_debug(message):
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{str(message)}\n")
    except Exception:
        pass

def analyze_reviews(product_name: str, reviews_data: List[dict]) -> dict:
    """
    Wrapper to be called by API/LangGraph.
    Converts dicts -> Pydantic Models -> Analyzes -> Returns Dict
    """
    log_debug(f"--- 3. Executing Skeptic Node (The Critic) for {product_name} ---")
    
    agent = SkepticAgent()
    
    # Validation/Conversion
    valid_reviews = []
    for r in reviews_data:
        try:
            # Handle potential source/url field mismatches or missing fields
            # The Tavily client returns ReviewSnippet(source, url, snippet)
            # The Review model expects (source, text, rating, date)
            # Mapping snippet -> text
            review_dict = {
                "source": r.get("source", "Unknown"),
                "text": r.get("snippet", "") or r.get("text", ""),
                "rating": r.get("rating"),
                "date": r.get("date")
            }
            valid_reviews.append(Review(**review_dict))
        except Exception as e:
            logger.warning(f"Skipping malformed review: {e}")
            log_debug(f"Skipping malformed review: {e}")
            continue
            
    log_debug(f"Valid reviews count: {len(valid_reviews)}")
    
    try:
        result = agent.analyze_reviews(product_name, valid_reviews)
        log_debug("Skeptic analysis completed successfully.")
        return result.model_dump()
    except Exception as e:
        log_debug(f"Skeptic analysis CRASHED: {e}")
        import traceback
        log_debug(traceback.format_exc())
        raise e
