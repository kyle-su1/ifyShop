from typing import List
from app.schemas.types import ProductQuery, ReviewSnippet, PriceOffer, SourceTrace

from .serpapi_client import get_shopping_offers
from .tavily_client import find_review_snippets


def fetch_prices(product: ProductQuery, trace: List[dict]) -> List[PriceOffer]:
    trace.append({"step": "get_prices", "detail": f"Fetching prices for {product.canonical_name}"})
    return get_shopping_offers(product, trace)


def fetch_reviews(product: ProductQuery, trace: List[dict]) -> List[ReviewSnippet]:
    trace.append({"step": "get_reviews", "detail": f"Fetching reviews for {product.canonical_name}"})
    return find_review_snippets(product, trace)
