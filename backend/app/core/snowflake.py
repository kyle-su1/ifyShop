from functools import lru_cache
import os
from snowflake.snowpark import Session
from app.core.config import settings

@lru_cache()
def get_snowflake_session():
    """
    Creates and returns a Snowflake Snowpark session.
    Using lru_cache to maintain a single session instance if possible,
    though Snowpark sessions might need valid connection checks.
    """
    connection_params = {
        "account": settings.SNOWFLAKE_ACCOUNT,
        "user": settings.SNOWFLAKE_USER,
        "password": settings.SNOWFLAKE_PASSWORD,
        "warehouse": settings.SNOWFLAKE_WAREHOUSE,
        "database": settings.SNOWFLAKE_DATABASE,
        "schema": settings.SNOWFLAKE_SCHEMA,
    }
    
    # Check if credentials exist
    if not settings.SNOWFLAKE_ACCOUNT:
        return None

    # Filter out None values to allow optional params or defaults
    connection_params = {k: v for k, v in connection_params.items() if v}
    
    try:
        session = Session.builder.configs(connection_params).create()
        return session
    except Exception as e:
        print(f"Snowflake session creation failed: {e}")
        return None
