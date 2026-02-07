import os
import requests
from typing import List
from app.schemas.types import ProductQuery, PriceOffer


SERPAPI_URL = "https://serpapi.com/search.json"


def get_shopping_offers(product: ProductQuery, trace: list) -> List[PriceOffer]:
    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        trace.append({"step": "serpapi", "detail": "Missing API key"})
        return []

    params = {
        "engine": "google_shopping",
        "q": product.canonical_name,
        "gl": "ca",
        "hl": "en",
        "location": "Canada",
        "api_key": api_key,
    }

    r = requests.get(SERPAPI_URL, params=params, timeout=10)
    data = r.json()

    offers = []

    for item in data.get("shopping_results", []):
        # SerpAPI uses "price" (e.g. "$5.88") or "extracted_price" (numeric)
        price_str = item.get("price") or item.get("extracted_price") or ""
        if isinstance(price_str, (int, float)):
            price_cents = int(price_str * 100)
        else:
            price_str = str(price_str).replace("$", "").replace(",", "").strip()
            try:
                price_cents = int(float(price_str) * 100)
            except (ValueError, TypeError):
                continue

        # SerpAPI Google Shopping uses "product_link", not "link"
        link = item.get("product_link") or item.get("link")
        if not link:
            continue
        offers.append(
            PriceOffer(
                vendor=item.get("source") or "Unknown",
                price_cents=price_cents,
                currency="CAD",
                url=link,
            )
        )

    trace.append({"step": "serpapi", "detail": f"Found {len(offers)} offers"})
    return offers
