from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/app"
    
    # Auth0
    AUTH0_DOMAIN: str = "dev-g1477nceu00mfa60.us.auth0.com"
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_AUDIENCE: Optional[str] = None
    AUTH0_ALGORITHM: str = "RS256"
    
    # API Keys
    GOOGLE_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    OPENROUTER_OPENAI_API_KEY: Optional[str] = None

    # Snowflake
    SNOWFLAKE_ACCOUNT: Optional[str] = None
    SNOWFLAKE_USER: Optional[str] = None
    SNOWFLAKE_PASSWORD: Optional[str] = None
    SNOWFLAKE_WAREHOUSE: Optional[str] = None
    SNOWFLAKE_DATABASE: Optional[str] = None
    SNOWFLAKE_SCHEMA: Optional[str] = None
    
    # Models
    MODEL_VISION: str = "gemini-2.0-flash"
    MODEL_REASONING: str = "gemini-2.0-flash"
    MODEL_ANALYSIS: str = "gemini-2.0-flash"
    MODEL_RESPONSE: str = "gemini-2.0-flash"  # Node 5 - Response Formulation

    class Config:
        env_file = ".env"
        extra = "ignore" # Allow other env vars

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
