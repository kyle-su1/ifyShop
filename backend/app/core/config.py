from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Shopping Suggester"
    
    # Database
    DATABASE_URL: str
    
    # Auth0
    AUTH0_DOMAIN: str
    AUTH0_API_AUDIENCE: str
    AUTH0_ALGORITHM: str = "RS256"

    # External APIs (Optional for now)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
