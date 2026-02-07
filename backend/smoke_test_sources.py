import os

from dotenv import load_dotenv

# Load .env so API keys are available (run from backend/)
load_dotenv(".env")

from app.schemas.types import ProductQuery
from app.sources import fetch_prices, fetch_reviews

def main():
    # Turn on sample mode so you can test with zero API keys
    os.environ["USE_SAMPLE_DATA"] = "true"

    trace = []
    pq = ProductQuery(canonical_name="Sony WH-1000XM5", brand="Sony")

    prices = fetch_prices(pq, trace=trace)
    reviews = fetch_reviews(pq, trace=trace)

    print("\nTRACE:")
    for t in trace:
        print("-", t)

    print("\nPRICES (first 3):")
    for p in prices[:3]:
        print("-", p.model_dump())

    print("\nREVIEWS (first 3):")
    for r in reviews[:3]:
        print("-", r.model_dump())

if __name__ == "__main__":
    main()
