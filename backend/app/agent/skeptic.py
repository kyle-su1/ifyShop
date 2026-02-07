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
                 summary="No reviews provided for analysis.",
                 trust_score=0.0,
                 sentiment_score=0.0,
                 red_flags=["Insufficient data"],
                 pros=[],
                 cons=[],
                 verdict="Insufficent Data"
             )

        # Format reviews for the prompt
        reviews_context = "\n---\n".join(
            [f"Source: {r.source}\nRating: {r.rating}/5\nDate: {r.date}\nContent: {r.text}" for r in reviews]
        )
        
        system_prompt = """You are 'The Skeptic', an expert product analyst and fraud detector. 
Your goal is to analyze product reviews to filter out noise, marketing fluff, and fake/paid inclusions.
You must determine the *true* quality of the product {product_name} based on the provided reviews.

Your analysis must be critical. Do not just summarize; evaluate the CREDIBILITY of the reviews.

LOOK FOR RED FLAGS:
- Vague, generic praise ("Great product", "Love it") without details.
- Repetitive sentence structures across different user names.
- A sudden influx of 5-star reviews in a short time period.
- Mismatches between the rating and the text.

SCORING:
- Trust Score (0-10): punish severely for red flags. 10 is reserved for established products with nuanced, verifiable user feedback.
- Sentiment Score (-1 to 1): The weighted average feeling of the *trustworthy* reviews.

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
def analyze_reviews(product_name: str, reviews_data: List[dict]) -> dict:
    """
    Wrapper to be called by API/LangGraph.
    Converts dicts -> Pydantic Models -> Analyzes -> Returns Dict
    """
    agent = SkepticAgent()
    
    # Validation/Conversion
    valid_reviews = []
    for r in reviews_data:
        try:
            valid_reviews.append(Review(**r))
        except Exception as e:
            logger.warning(f"Skipping malformed review: {e}")
            continue
            
    result = agent.analyze_reviews(product_name, valid_reviews)
    return result.model_dump()
