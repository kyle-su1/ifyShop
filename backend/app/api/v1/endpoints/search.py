from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str
    price: str

@router.get("/", response_model=List[SearchResult])
async def search(query: str):
    # Placeholder for Tavily/Serpapi search
    return [
        {
            "title": f"Result for {query}",
            "link": "http://example.com/item",
            "snippet": "This is a placeholder search result from Tavily.",
            "price": "$19.99"
        },
        {
            "title": f"Another result for {query}",
            "link": "http://example.com/item2",
            "snippet": "Another placeholder result.",
            "price": "$29.99"
        }
    ]
