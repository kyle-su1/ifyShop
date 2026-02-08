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
    eco_score: float = Field(0.5, description="0.0 to 1.0 environmental friendliness score (1.0=very eco-friendly, 0.0=harmful)")
    eco_notes: str = Field("", description="Brief explanation of eco assessment (materials, durability, brand sustainability)")
    red_flags: List[str] = Field(default_factory=list, description="List of suspicious patterns detected (e.g., 'Repetitive phrasing', 'All 5-stars on same day')")
    pros: List[str] = Field(default_factory=list, description="Key advantages mentioned by real users")
    cons: List[str] = Field(default_factory=list, description="Key flaws mentioned by real users")
    verdict: str = Field(..., description="One-line final verdict (e.g., 'Solid buy', 'Avoid - Likely scams', 'Good but overpriced')")

class VetoDecision(BaseModel):
    decision: str = Field(..., description="'veto' or 'proceed'")
    better_search_query: Optional[str] = Field(None, description="A specific, mutated search query to find better results if vetoing (e.g., 'Sony WH-1000XM5 reddit reviews')")
    reason: str = Field(..., description="Why we are vetoing or proceeding")
    market_warning: Optional[str] = Field(None, description="Warning to display if we are forced to proceed despite low quality")

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

    def analyze_reviews(self, product_name: str, reviews: List[Review], eco_context: str = "") -> ReviewSentiment:
        """
        Analyzes a list of reviews to determine authenticity and sentiment.
        """
        # Analyzes a list of reviews to determine authenticity and sentiment.
        # Even if NO reviews are present, we still run the analysis to generate the Eco Score
        # and checking for inherent product flaws based on category/brand.

        reviews_context = ""
        if not reviews:
             reviews_context = "NO USER REVIEWS AVAILABLE. Focus analysis on Product Name/Brand for Eco Score and known category issues."
        else:
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

IF NO REVIEWS ARE AVAILABLE:
- Return "trust_score": 5.0 (Neutral)
- Return "sentiment_score": 0.0 (Neutral)
- Return "verdict": "No reviews found - assess based on specs/brand"
- BUT ***YOU MUST STILL EVALUATE THE ECO_SCORE*** based on the product name, brand, and category.

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

ENVIRONMENTAL FRIENDLINESS (eco_score 0-1):
Evaluate based on:
1. SUSTAINABILITY RESEARCH DATA (if provided below)
2. CORPORATE STATS (Net Zero, B Corp, ESG scores) - HIGH IMPACT
3. Mentions in reviews about durability/longevity  
4. Build quality and materials (recyclable, sustainable = higher)
5. Packaging and repairability

{eco_section}

Score 0.8+ for B Corps, Net Zero verification, or clearly eco-conscious products.
Score 0.3 or below for disposable/harmful products or unknowns with bad reputation.
Provide a brief eco_notes explanation, CITIING textual evidence if available.

BE FAIR. Most products deserve a trust score of 6-8 unless there are clear problems.
Output the result in the specified JSON format.
"""

        # Add eco research data if available
        if eco_context:
            eco_section = f"SUSTAINABILITY DATA FROM RESEARCH:\n{eco_context}"
        else:
            eco_section = """No specific sustainability research found. Use YOUR KNOWLEDGE to evaluate eco-friendliness based on:
- Product materials (wood=renewable, recycled materials=good, single-use plastic=bad)
- Brand reputation (IKEA, Patagonia, Apple = known sustainability programs)
- Product category (durable furniture > fast fashion, repairable electronics > disposable)
- Expected lifespan (longer-lasting products = more eco-friendly)

For this product, consider what you know about the brand and materials mentioned in the product name or reviews.
DO NOT default to 0.5 - make an educated assessment based on product type."""
        
        system_prompt = system_prompt.replace("{eco_section}", eco_section)

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

    def evaluate_candidates_for_veto(self, candidates: List[dict], user_prefs: dict, loop_count: int) -> VetoDecision:
        """
        State-Aware Veto Logic ("The Gatekeeper")
        """
        # 1. Fail Fast using Heuristics first? 
        # For now, we trust the LLM to be the judge as it needs to understand context (Droppshipping vs Budget Brand)
        
        candidates_context = "\n".join([
            f"- {c.get('name')} (Price: {c.get('price_text')})" for c in candidates
        ])
        
        pref_context = ""
        if user_prefs.get('price_sensitivity', 0) > 0.7:
             pref_context = "User is Price Sensitive (Budget Conscious). Do NOT veto items just because they are cheap generic brands, unless they are scams."
        elif user_prefs.get('quality', 0) > 0.7:
             pref_context = "User wants Quality/Premium. Veto cheap knockoffs diligently."
             
        system_prompt = f"""You are the 'Gatekeeper' for a Shopping Agent.
Your job is to decide if the products we found are good enough to show the user, or if we should try searching again.

Current Search Iteration: {loop_count} / 2 (Max 2)

CANDIDATES FOUND:
{candidates_context}

USER PREFERENCES:
{pref_context}

RULES:
1. LOOP 0 (First Try): Be Strict. faster to retry now than show bad results.
   - Veto if all products look like "dropshipped junk" (random all-caps brands, identical generic images).
   - Veto if products are completely irrelevant to the User's Intent.
2. LOOP 1 (Second Try): Be Lenient. Only veto if products are DANGEROUS or SCAMS.
   - Accept "mediocre" products if that's all the market has.
3. LOOP 2 (Final): FORCE PROCEED. Do not veto.
   - Set "decision": "proceed"
   - Add a "market_warning" if quality is low.

QUERY MUTATION:
If you VETO, you MUST provide a 'better_search_query'.
- If the issue was "Generic Junk", append "reddit", "best", or specific reputable brands.
- Example: "Wireless earbuds" -> "Best budget wireless earbuds under $50 reddit"

Output JSON adhering to VetoDecision schema.
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Evaluate these candidates.")
        ])
        
        parser = PydanticOutputParser(pydantic_object=VetoDecision)
        chain = prompt | self.llm | parser
        
        try:
             return chain.invoke({})
        except Exception as e:
             logger.error(f"Veto Analysis Failed: {e}")
             return VetoDecision(decision="proceed", reason="Error in Veto Logic", market_warning=None)

log_file = "/app/debug_output.txt"
def log_debug(message):
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{str(message)}\n")
    except Exception:
        pass

        return result.model_dump()
    except Exception as e:
        log_debug(f"Skeptic analysis CRASHED: {e}")
        import traceback
        log_debug(traceback.format_exc())
        raise e

def check_veto_status(candidates: List[dict], user_prefs: dict, loop_count: int) -> dict:
     agent = SkepticAgent()
     try:
         decision = agent.evaluate_candidates_for_veto(candidates, user_prefs, loop_count)
         return decision.model_dump()
     except Exception as e:
         logger.error(f"Check Veto Status Failed: {e}")
         return {"decision": "proceed", "reason": "Error"}
