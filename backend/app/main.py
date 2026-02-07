from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Shopping Suggester API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.db.session import engine
from app.db.base import Base
from app.api.api import api_router

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    """
    Analyzes an uploaded image using the LangGraph agent.
    """
    initial_state = {
        "image_data": request.image,
        "user_preferences": request.user_preferences,
        "search_results": [],
        "reviews": [],
        "parsed_item": None,
        "verification_result": None,
        "final_recommendation": None,
        "reviews_summary": None
    }
    
    result = agent_app.invoke(initial_state)
    
    return result
