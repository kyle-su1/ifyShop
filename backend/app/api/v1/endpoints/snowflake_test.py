from fastapi import APIRouter, HTTPException
from app.core.snowflake import get_snowflake_session
from app.services.snowflake_vector import snowflake_vector_service
from snowflake.connector.errors import DatabaseError

router = APIRouter()

@router.get("/connection")
def test_snowflake_connection():
    """
    Tests the connection to Snowflake by running a simple query.
    """
    try:
        session = get_snowflake_session()
        # Run a simple query
        version = session.sql("SELECT current_version()").collect()[0][0]
        db = session.sql("SELECT current_database()").collect()[0][0]
        role = session.sql("SELECT current_role()").collect()[0][0]
        return {
            "status": "connected",
            "version": version,
            "database": db,
            "role": role
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snowflake connection failed: {str(e)}")

@router.get("/vector-search")
def test_vector_search():
    """
    Tests Snowflake Vector Search capabilities.
    """
    try:
        # 1. Insert a dummy product with a zero vector (just to test write)
        dummy_vector = [0.1] * 768
        success, msg = snowflake_vector_service.insert_product({
            "id": "test_product_1",
            "name": "Test Product",
            "description": "A test product for vector search",
            "price": 10.0
        }, dummy_vector)

        if not success:
            return {
                "status": "error", 
                "detail": f"Insert failed: {msg}",
                "row_count": -1
            }
        
        # 2. Check if it exists
        count = snowflake_vector_service.session.sql("SELECT COUNT(*) FROM products").collect()[0][0]
        
        # 3. Search for it
        results = snowflake_vector_service.search_similar_products(dummy_vector, limit=1)
        
        return {
            "status": "success",
            "inserted": True,
            "insert_msg": msg,
            "row_count": count,
            "search_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector Search failed: {str(e)}")


