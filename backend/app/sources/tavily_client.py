import os
import requests
from typing import List
from app.schemas.types import ProductQuery, ReviewSnippet


TAVILY_URL = "https://api.tavily.com/search"


def find_review_snippets(product: ProductQuery, trace: list) -> List[ReviewSnippet]:
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        trace.append({"step": "tavily", "detail": "Missing API key"})
        return []

    queries = [
        f"{product.canonical_name} review Canada",
        f"{product.canonical_name} review reddit Canada",
        f"site:reddit.com {product.canonical_name} worth it Canada",
    ]

    results = []

    for q in queries:
        payload = {
            "api_key": api_key,
            "query": q,
            "search_depth": "basic",
        }

        r = requests.post(TAVILY_URL, json=payload, timeout=10)
        data = r.json()

        for item in data.get("results", []):
            url = item.get("url")
            if not url:
                continue
            results.append(
                ReviewSnippet(
                    source=item.get("title") or "",
                    url=url,
                    snippet=item.get("content") or "",
                )
            )

    trace.append({"step": "tavily", "detail": f"Found {len(results)} review snippets"})
    return results
