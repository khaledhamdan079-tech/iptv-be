"""
Maso API Routes
Separate endpoints for Maso API integration
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Literal
from app.services.maso_api import MasoAPIService

router = APIRouter(prefix="/api/maso", tags=["maso"])

# Default service instance (no credentials)
maso_service = MasoAPIService()

# Service with credentials and MAC address (for testing)
maso_service_auth = MasoAPIService(
    username="had130", 
    password="589548655",
    mac_address="90:BA:55:77:22:D3"
)


@router.get("/auth")
async def get_auth_config():
    """
    Get Maso API authentication and configuration
    Returns app settings, languages, trial info, playlist URLs, etc.
    The response is base64 encoded and will be automatically decoded.
    """
    result = maso_service.get_auth_config()
    
    if not result.get("success", True) and "error" in result:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch auth config"))
    
    return {
        "success": True,
        "data": result
    }


@router.get("/movies")
async def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    type: Literal["movies", "series", "all"] = Query("all", description="Content type filter"),
    use_auth: bool = Query(False, description="Use authenticated service with credentials and MAC address")
):
    """
    Get main movies/series from Maso API
    Note: This endpoint may return HTML instead of JSON and may need further investigation.
    The service will try to call movies.php if referenced in the HTML response.
    Set use_auth=true to use credentials and MAC address authentication.
    """
    service = maso_service_auth if use_auth else maso_service
    result = service.get_main_movies(page=page, limit=limit, content_type=type)
    
    if not result.get("success", True) and "error" in result:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch movies"))
    
    return {
        "success": True,
        "data": result
    }


@router.get("/playlists")
async def get_playlists():
    """
    Get playlists information from Maso API
    """
    result = maso_service.get_playlists()
    
    if not result.get("success", True) and "error" in result:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch playlists"))
    
    return {
        "success": True,
        "data": result
    }


@router.get("/playlist-urls")
async def get_playlist_urls():
    """
    Extract and return playlist URLs from auth config
    Returns list of available playlist configurations
    """
    urls = maso_service.get_playlist_urls()
    
    return {
        "success": True,
        "data": {
            "playlists": urls,
            "count": len(urls)
        }
    }


@router.get("/update")
async def check_update():
    """
    Check for app updates
    """
    result = maso_service.check_update()
    
    if not result.get("success", True) and "error" in result:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to check for updates"))
    
    return {
        "success": True,
        "data": result
    }


@router.get("/test")
async def test_all_endpoints():
    """
    Test all Maso API endpoints and return results
    Useful for debugging and understanding API responses
    """
    results = {
        "auth": maso_service.get_auth_config(),
        "movies": maso_service.get_main_movies(),
        "playlists": maso_service.get_playlists(),
        "update": maso_service.check_update(),
        "playlist_urls": maso_service.get_playlist_urls()
    }
    
    return {
        "success": True,
        "data": results
    }


@router.get("/try-movies-endpoint")
async def try_alternative_movies():
    """
    Try alternative approaches to get movies data
    Tests different endpoint variations
    """
    result = maso_service.try_alternative_movies_endpoint()
    
    return {
        "success": True,
        "data": result
    }
