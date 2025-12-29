"""
Search routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Literal
from app.services.scraper import scraper

router = APIRouter()


@router.get("/")
async def search_series(
    q: str = Query(..., description="Search query"),
    type: Literal["all", "movies", "series"] = Query(
        default="all", 
        description="Filter by content type: 'movies' for movies only, 'series' for series only, or 'all' for both"
    )
):
    """Search for series/movies
    
    - **q**: Search query (required)
    - **type**: Filter by type - "movies", "series", or "all" (default: "all")
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query is required")
    
    try:
        results = scraper.search_series(q.strip(), filter_type=type)
        
        return {
            "success": True,
            "query": q,
            "type": type,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

