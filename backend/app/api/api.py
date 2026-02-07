from fastapi import APIRouter
from app.api.v1.endpoints import agent, search, users, history

api_router = APIRouter()
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
from app.api.v1.endpoints import snowflake_test
api_router.include_router(snowflake_test.router, prefix="/snowflake", tags=["snowflake"])
