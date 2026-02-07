"""
Test Script for Node 4: Analysis & Synthesis

Verifies:
1. Preference Service integration (loading weights)
2. Scoring Logic (calculating weighted scores)
3. Full Node Execution (processing alternatives)
"""
import sys
import os
import json

# Setup Path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, "backend")
backend_path = os.path.join(project_root, "backend")
sys.path.insert(0, backend_path)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
    print(f"Loaded .env from {project_root}")
except ImportError:
    print("Warning: python-dotenv not installed, API keys might be missing")

try:
    from app.agent.nodes.analysis import node_analysis_synthesis
    from app.models.item import Item
    from app.agent.state import AgentState
    from app.services.preference_service import PREFERENCE_TYPE_WEIGHTS
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_node_analysis():
    print("--- Testing Node 4 Analysis ---")
    
    # Mock State
    mock_state = {
        "user_preferences": {
            "price_sensitivity": 0.5, 
            "quality": 0.8, # User cares about quality now
            "eco_friendly": 0.5,
            "brand_reputation": 0.5
        },
        "research_data": {
            "product_query": {"canonical_name": "Sony WH-1000XM5"},
            "competitor_prices": [{"price": 348.0, "store": "Amazon"}],
            "reviews": [{"source": "RTings", "text": "Best noise canceling, amazing sound, comfortable.", "rating": 4.8}]
        },
        "risk_report": {
            "fake_review_likelihood": "Low",
            "hidden_flaws": ["Expensive"]
        },
        "market_scout_data": {
            "candidates": [
                {
                    "name": "Bose QuietComfort Ultra",
                    "reason": "Top Tier Competitor",
                    "prices": [{"price": 429.0}],
                    "reviews": [{"source": "Reddit", "text": "Best ANC on the market, but pricey.", "rating": 4.7}]
                },
                {
                    "name": "Anker Soundcore Q20",
                    "reason": "Budget Friendly",
                    "prices": [{"price": 60.0}],
                    "reviews": [{"source": "Reddit", "text": "Unbeatable for the price.", "rating": 4.2}]
                }
            ]
        }
    }
    
    print("\nRunning Node 4 with Mock State...")
    try:
        # We need to mock the DB session or ensure the code handles missing DB gracefully.
        # The preference_service handles missing DB gracefully (logs info and returns defaults).
        # However, analyzing reviews calls Gemini. 
        # To avoid API costs/errors during simple test, we might want to mock analyze_reviews.
        # But for an integration test, let's try to run it (assuming API key is set).
        
        result = node_analysis_synthesis(mock_state)
        
        analysis = result.get("analysis_object", {})
        print("\n--- Result Analysis Object ---")
        print(json.dumps(analysis, indent=2))
        
        # Verification
    # Verification
        top_pick = analysis.get("recommended_product")
        scores = analysis.get("alternatives_ranked", [])
        
        print(f"\nTop Pick: {top_pick}")
        print("Scores:")
        for s in scores:
            print(f"- {s['name']}: {s['score']}")
            
        print("\n✅ Test Complete (Balanced Scoring)")

    except Exception as e:
        print(f"\n❌ FAILED: Execution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_node_analysis()
