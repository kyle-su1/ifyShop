from app.services.snowflake_vector import snowflake_vector_service
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

def verify_search():
    print("Verifying Snowflake Vector Search...")
    
    # 1. Embed query
    print("Embedding query: 'ergonomic office chair'...")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GOOGLE_API_KEY
    )
    query_vector = embeddings_model.embed_query("ergonomic office chair")
    
    # 2. Search
    print("Searching database...")
    results = snowflake_vector_service.search_similar_products(query_vector, limit=3)
    
    # 3. Print Results
    print(f"Found {len(results)} results:")
    for res in results:
        print(f"- {res['name']} (Score: {res['score']:.4f})")
        
if __name__ == "__main__":
    verify_search()
