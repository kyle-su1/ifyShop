import sys
import os
import base64

# Add backend to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.graph import agent_app

def test_agent_flow():
    print("Starting Agent Flow Test...")
    
    # Mock data
    # In a real test, this would be a real base64 image strings
    mock_image_data = "base64_image_placeholder"
    mock_user_prefs = {"budget_limit": 150, "sustainability_focus": "high"}
    
    initial_state = {
        "image_data": mock_image_data,
        "user_preferences": mock_user_prefs,
        "search_results": [],
        "reviews": [],
        "parsed_item": None,
        "verification_result": None,
        "final_recommendation": None,
        "reviews_summary": None
    }
    
    print("Invoking Agent App...")
    try:
        # Since we don't have real API keys in this environment, the nodes handle specific exceptions 
        # or we might expect some errors if keys are missing but code doesn't catch all.
        # However, our nodes.py uses try-except for external calls, so it should flow through.
        result = agent_app.invoke(initial_state)
        
        print("\n--- Test Result ---")
        print("Parsed Item:", result.get("parsed_item"))
        print("Final Recommendation:", result.get("final_recommendation"))
        print("Flow completed successfully.")
        
    except Exception as e:
        print(f"Flow failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_flow()
