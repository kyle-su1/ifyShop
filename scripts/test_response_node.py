"""
Test Script for Node 5: Response Formulation

Tests the response formatting with:
- Main product: The item user is looking at (detailed analysis)
- Alternatives: Suggested products with compatibility comparison
"""
import sys
import os
import json

# Setup Path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, "backend")
sys.path.insert(0, backend_path)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
    print(f"Loaded .env from {project_root}")
except ImportError:
    print("Warning: python-dotenv not installed")

try:
    from app.agent.nodes.response import node_response_formulation
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)


def test_node_response():
    print("=" * 60)
    print("Testing Node 5: Response Formulation")
    print("=" * 60)
    print()
    print("SCENARIO: User is looking at Sony WH-1000XM5 headphones")
    print("GOAL: Analyze main product + suggest alternatives")
    print()
    
    # Mock state simulating Node 3 + Node 4 output
    mock_state = {
        # Node 3: Risk Report (Skeptic analysis of MAIN product)
        "risk_report": {
            "fake_review_likelihood": "Low - Reviews appear authentic",
            "price_integrity": "Good value - Competitive with market",
            "hidden_flaws": [
                "Bluetooth disconnection reported by some users",
                "Ear cushions may wear after 2 years"
            ]
        },
        
        # Node 4: Analysis Object (scores for all products)
        "analysis_object": {
            "match_score": 85.5,
            "recommended_product": "Sony WH-1000XM5",  # This is the MAIN product user is viewing
            "scoring_breakdown": {
                "trust_score": 8.5,
                "sentiment_score": 0.85,
                "price_score": 0.72,
                "total_score": 85.5
            },
            "alternatives_ranked": [
                {"name": "Sony WH-1000XM5", "score": 85.5, "reason": "Original Selection"},
                {"name": "Bose QuietComfort Ultra", "score": 78.2, "reason": "Top Tier Competitor"},
                {"name": "Anker Soundcore Q20", "score": 72.1, "reason": "Budget Friendly"}
            ],
            "applied_preferences": {
                "price_sensitivity": 0.5,
                "quality": 0.8
            }
        },
        
        # Node 4: Detailed analysis from Skeptic runs
        "alternatives_analysis": [
            {
                "name": "Sony WH-1000XM5",
                "score_details": {"total_score": 85.5},
                "sentiment_summary": "Excellent noise cancellation, premium build, comfortable for long sessions.",
                "reason": "Original Selection"
            },
            {
                "name": "Bose QuietComfort Ultra",
                "score_details": {"total_score": 78.2},
                "sentiment_summary": "Strong competitor with slightly better comfort but higher price.",
                "reason": "Top Tier Competitor"
            },
            {
                "name": "Anker Soundcore Q20",
                "score_details": {"total_score": 72.1},
                "sentiment_summary": "Best value for money. Good ANC but lower build quality.",
                "reason": "Budget Friendly"
            }
        ]
    }
    
    print("Running Node 5...")
    print("-" * 60)
    
    try:
        result = node_response_formulation(mock_state)
        final_rec = result.get("final_recommendation", {})
        
        print("\n--- Response JSON ---")
        print(json.dumps(final_rec, indent=2))
        
        # Validate structure
        print("\n--- Validation ---")
        
        if "main_product" in final_rec:
            mp = final_rec["main_product"]
            print(f"✅ Main Product: {mp.get('name')}")
            print(f"   Compatibility: {mp.get('compatibility_score')}%")
            print(f"   Pros: {len(mp.get('pros', []))} items")
            print(f"   Cons: {len(mp.get('cons', []))} items")
        else:
            print("❌ Missing main_product")
            
        if "alternatives" in final_rec:
            alts = final_rec["alternatives"]
            print(f"✅ Alternatives: {len(alts)} suggestions")
            for alt in alts:
                print(f"   - {alt.get('name')}: {alt.get('compatibility_score')}%")
        else:
            print("❌ Missing alternatives")
            
        if "verdict" in final_rec:
            print(f"✅ Verdict: {final_rec['verdict']}")
        
        print("\n" + "=" * 60)
        print("✅ Test Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_node_response()
