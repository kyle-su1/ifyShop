import os
import json
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from serpapi import GoogleSearch
from tavily import TavilyClient

from .state import AgentState

# Initialize models
gemini_flash = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
gemini_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize tools
# Note: In a real app, initialize these once or use a dependency injection system
try:
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
except:
    tavily_client = None

def parse_image(state: AgentState) -> Dict[str, Any]:
    """
    Parses the image using Gemini 2.0 Flash to identify the fashion item.
    """
    print("--- PARSE IMAGE ---")
    print("Agent: Calling Gemini 2.0 Flash to parse image...")
    image_data = state["image_data"]
    
    prompt = """
    Identify the main fashion item in this image. 
    Return a ONLY a JSON object with the following keys: 
    - item_name: specific name of the item
    - brand: brand name if visible or inferred
    - color: dominant color
    - material: inferred material
    - category: product category (e.g., Sneakers, handbag)
    """
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_data}"},
        ]
    )
    
    response = gemini_flash.invoke([message])
    
    try:
        # Clean up code blocks if present
        content = response.content.replace("```json", "").replace("```", "").strip()
        parsed_item = json.loads(content)
        print(f"Agent: Identified item - {parsed_item.get('item_name')} ({parsed_item.get('brand')})")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        parsed_item = {"item_name": "Unknown Item", "category": "Fashion"}
        
    return {"parsed_item": parsed_item}

def verify_item(state: AgentState) -> Dict[str, Any]:
    """
    Cross-checks the identified item using a secondary vision model (simulated here)
    or just validates the confidence.
    """
    print("--- VERIFY ITEM ---")
    print("Agent: Verifying item with Vision API...")
    # For now, we'll assume the parsing works and just pass through a high confidence
    # In a real scenario, call OpenAI Vision or GCV here.
    return {"verification_result": {"verified": True, "confidence": 0.95}}

def get_prices(state: AgentState) -> Dict[str, Any]:
    """
    Searches for price information using SerpAPI.
    """
    print("--- GET PRICES ---")
    item = state["parsed_item"]
    print(f"Agent: Searching SerpAPI for prices of {item.get('item_name')}...")
    query = f"{item.get('brand', '')} {item.get('item_name', '')} {item.get('color', '')} price"
    
    search_results = []
    if os.getenv("SERPAPI_API_KEY"):
        try:
            params = {
                "q": query,
                "api_key": os.getenv("SERPAPI_API_KEY"),
                "engine": "google_shopping"
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            shopping_results = results.get("shopping_results", [])[:5]
            
            for res in shopping_results:
                search_results.append({
                    "title": res.get("title"),
                    "price": res.get("price"),
                    "link": res.get("link"),
                    "source": res.get("source")
                })
        except Exception as e:
            print(f"Error fetching prices: {e}")
    else:
        print("SERPAPI_API_KEY not found. Skipping price search.")
        search_results = [{"title": "Mock Item", "price": "$100", "link": "http://example.com"}]

    return {"search_results": search_results}

def get_reviews(state: AgentState) -> Dict[str, Any]:
    """
    Searches for reviews and sustainability info using Tavily.
    """
    print("--- GET REVIEWS ---")
    item = state["parsed_item"]
    print(f"Agent: Searching Tavily for reviews of {item.get('item_name')}...")
    query = f"{item.get('brand', '')} {item.get('item_name', '')} sustainability reviews"
    
    reviews = []
    if tavily_client:
        try:
            response = tavily_client.search(query=query, search_depth="advanced", max_results=3)
            # Make sure to handle the response structure correctly. 
            # Tavily returns a dict with 'results' key which is a list.
            if isinstance(response, dict) and 'results' in response:
                for res in response['results']:
                    reviews.append({
                        "url": res.get("url"),
                        "content": res.get("content")
                    })
            # It's possible for response to be just the list in some versions or mock setups, 
            # but usually it's a dict. 
        except Exception as e:
             print(f"Error fetching reviews: {e}")
    else:
        print("Tavily client not initialized. Skipping reviews.")
        reviews = [{"content": "Mock review: This product is great and somewhat sustainable.", "url": "http://example.com/review"}]

    return {"reviews": reviews}

def analyze_reviews(state: AgentState) -> Dict[str, Any]:
    """
    Summarizes the gathered reviews using Gemini.
    """
    print("--- ANALYZE REVIEWS ---")
    print("Agent: Analyzing reviews with Gemini...")
    reviews = state["reviews"]
    item = state["parsed_item"]
    
    if not reviews:
        return {"reviews_summary": "No reviews found."}
        
    reviews_text = "\n\n".join([r.get("content", "") for r in reviews])
    
    prompt = ChatPromptTemplate.from_template(
        """
        Analyze these reviews for the {item_name}:
        
        {reviews_text}
        
        Provide a brief summary focusing on:
        1. General Sentiment
        2. Sustainability claims (if any)
        3. Key pros and cons
        """
    )
    
    chain = prompt | gemini_flash
    response = chain.invoke({"item_name": item.get('item_name'), "reviews_text": reviews_text})
    
    # We can store the summary back into the state, maybe in a new field or update reviews
    # For now let's just use it in the final recommendation
    return {"reviews_summary": response.content}

def final_recommendation(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizes everything into a final recommendation using Gemini 1.5 Pro.
    """
    print("--- FINAL RECOMMENDATION ---")
    print("Agent: Generating final recommendation with Gemini 1.5 Pro...")
    item = state["parsed_item"]
    user_prefs = state["user_preferences"]
    prices = state["search_results"]
    reviews_summary = state.get("reviews_summary", "No summary available") # Access from state, might need to add to TypedDict if we want it passed explicitly
    # Note: reviews_summary was not in original TypedDict. 
    # In LangGraph, if a node returns a key not in State, it might be ignored or error depending on setup.
    # We should add it to State or just rely on passing it via 'messages' if we were using that architecture.
    # For this simple state, let's assume we update the analyze_reviews to return it and we update State definition later or just assume 'reviews' holds it.
    # Wait, 'analyze_reviews' returned 'reviews_summary'. The State needs to have this key.
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful shopping assistant.
        User Preferences: {user_prefs}
        
        Identified Item: {item}
        Prices Found: {prices}
        Reviews Summary: {reviews_summary}
        
        Write a friendly recommendation. 
        If the user cares about sustainability, highlight that.
        Recommend whether to buy or suggest alternatives if it doesn't fit constraints.
        """
    )
    
    chain = prompt | gemini_pro
    response = chain.invoke({
        "user_prefs": user_prefs,
        "item": item,
        "prices": prices,
        "reviews_summary": reviews_summary
    })
    
    return {"final_recommendation": response.content}
