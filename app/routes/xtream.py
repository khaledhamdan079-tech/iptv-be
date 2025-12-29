"""
Xtream Codes API Routes
Routes for accessing content via Xtream Codes playlists
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Literal
from app.services.xtream_codes import XtreamCodesService
from app.services.maso_api import MasoAPIService

router = APIRouter(prefix="/api/xtream", tags=["xtream"])

maso_service = MasoAPIService()


def get_playlist_service(playlist_id: int = 0) -> Optional[XtreamCodesService]:
    """Get Xtream Codes service from Maso playlist URLs"""
    playlists = maso_service.get_playlist_urls()
    
    if not playlists:
        return None
    
    if playlist_id >= len(playlists):
        playlist_id = 0
    
    playlist = playlists[playlist_id]
    url = playlist.get('url', '')
    
    # Parse Xtream Codes URL
    # Format: http://server:port/get.php?username=xxx&password=xxx&type=m3u_plus&output=ts
    from urllib.parse import urlparse, parse_qs
    
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    params = parse_qs(parsed.query)
    
    username = params.get('username', [''])[0]
    password = params.get('password', [''])[0]
    
    # If credentials are empty in URL, use Maso credentials
    if not username or not password:
        username = "had130"
        password = "589548655"
    
    return XtreamCodesService(base_url, username, password)


@router.get("/playlists")
async def get_playlists():
    """Get available Xtream Codes playlists from Maso API"""
    playlists = maso_service.get_playlist_urls()
    
    return {
        "success": True,
        "data": {
            "playlists": playlists,
            "count": len(playlists)
        }
    }


@router.get("/user-info")
async def get_user_info(playlist_id: int = Query(0, description="Playlist ID (default: 0)")):
    """Get user information from Xtream Codes API"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    info = service.get_user_info()
    
    if not info.get("success", True) and "error" in info:
        raise HTTPException(status_code=500, detail=info.get("error", "Failed to get user info"))
    
    return {
        "success": True,
        "data": info
    }


@router.get("/vod/categories")
async def get_vod_categories(playlist_id: int = Query(0, description="Playlist ID (default: 0)")):
    """Get VOD (Movies) categories"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    categories = service.get_vod_categories()
    
    return {
        "success": True,
        "data": categories,
        "count": len(categories)
    }


@router.get("/vod/movies")
async def get_vod_movies(
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    category_id: Optional[str] = Query(None, description="Category ID to filter")
):
    """Get VOD movies"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    movies = service.get_vod_streams(category_id)
    
    return {
        "success": True,
        "data": movies,
        "count": len(movies)
    }


@router.get("/vod/search")
async def search_vod(
    q: str = Query(..., description="Search query"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Search for VOD movies"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    results = service.search_vod(q)
    
    return {
        "success": True,
        "query": q,
        "data": results,
        "count": len(results)
    }


@router.get("/vod/info")
async def get_vod_info(
    vod_id: str = Query(..., description="VOD ID (stream_id)"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    include_stream_urls: bool = Query(False, description="Include stream URLs in response")
):
    """Get VOD (movie) information
    
    If include_stream_urls=true, also returns available stream URLs for playback.
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    info = service.get_vod_info(vod_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    result = {
        "success": True,
        "data": info
    }
    
    # Add stream URLs if requested
    if include_stream_urls and info.get('info'):
        # Use vod_id as stream_id
        stream_urls = service.get_movie_stream_url(movie=info, stream_id=vod_id)
        recommended = next((url for url in stream_urls if url.get('format') == 'm3u8'), None)
        if not recommended and stream_urls:
            recommended = stream_urls[0]
        
        result["stream_urls"] = stream_urls
        result["recommended_url"] = recommended.get('url') if recommended else None
    
    return result


@router.get("/series/categories")
async def get_series_categories(playlist_id: int = Query(0, description="Playlist ID (default: 0)")):
    """Get series categories"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    categories = service.get_series_categories()
    
    return {
        "success": True,
        "data": categories,
        "count": len(categories)
    }


@router.get("/series/list")
async def get_series_list(
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    category_id: Optional[str] = Query(None, description="Category ID to filter")
):
    """Get series list"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    series = service.get_series(category_id)
    
    return {
        "success": True,
        "data": series,
        "count": len(series)
    }


@router.get("/series/search")
async def search_series(
    q: str = Query(..., description="Search query"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Search for series"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    results = service.search_series(q)
    
    return {
        "success": True,
        "query": q,
        "data": results,
        "count": len(results)
    }


@router.get("/series/info")
async def get_series_info(
    series_id: str = Query(..., description="Series ID"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get series information including episodes
    
    Returns series details with all seasons and episodes.
    Use /series/episode/stream-url to get playable URLs for specific episodes.
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    info = service.get_series_info(series_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Series not found")
    
    return {
        "success": True,
        "data": info
    }


@router.get("/vod/stream-url")
async def get_movie_stream_url(
    vod_id: str = Query(..., description="VOD ID (stream_id)"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get stream URL(s) for a movie
    
    Returns multiple stream URL options (m3u8, ts, and container extension).
    Recommended: Use m3u8 for HLS streaming (best compatibility).
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    # Get movie info first (for metadata)
    vod_info = service.get_vod_info(vod_id)
    if not vod_info or not vod_info.get('info'):
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Get stream URLs using the vod_id as stream_id
    stream_urls = service.get_movie_stream_url(movie=vod_info, stream_id=vod_id)
    
    # Find recommended URL (prefer m3u8)
    recommended = next((url for url in stream_urls if url.get('format') == 'm3u8'), None)
    if not recommended and stream_urls:
        recommended = stream_urls[0]
    
    return {
        "success": True,
        "vod_id": vod_id,
        "stream_urls": stream_urls,
        "recommended_url": recommended.get('url') if recommended else None,
        "recommended_format": recommended.get('format') if recommended else None
    }


@router.get("/series/episode/stream-url")
async def get_episode_stream_url(
    series_id: str = Query(..., description="Series ID"),
    season_number: str = Query(..., description="Season number"),
    episode_number: str = Query(..., description="Episode number"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get stream URL(s) for a series episode
    
    Returns multiple stream URL options (m3u8, ts, and container extension).
    Recommended: Use m3u8 for HLS streaming (best compatibility).
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    # Get series info
    series_info = service.get_series_info(series_id)
    if not series_info:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Find the episode
    episodes = series_info.get('episodes', {})
    season_episodes = episodes.get(season_number, [])
    
    episode = None
    for ep in season_episodes:
        if str(ep.get('episode_num', '')) == str(episode_number):
            episode = ep
            break
    
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    # Get stream URLs
    stream_urls = service.get_episode_stream_url(episode)
    
    # Find recommended URL (prefer m3u8)
    recommended = next((url for url in stream_urls if url.get('format') == 'm3u8'), None)
    if not recommended and stream_urls:
        recommended = stream_urls[0]
    
    return {
        "success": True,
        "series_id": series_id,
        "season": season_number,
        "episode": episode_number,
        "stream_urls": stream_urls,
        "recommended_url": recommended.get('url') if recommended else None,
        "recommended_format": recommended.get('format') if recommended else None
    }


@router.get("/test")
async def test_playlist(playlist_id: int = Query(0, description="Playlist ID (default: 0)")):
    """Test playlist connection and get all available data"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    results = {
        "user_info": service.get_user_info(),
        "vod_categories": service.get_vod_categories(),
        "vod_count": len(service.get_vod_streams()),
        "series_categories": service.get_series_categories(),
        "series_count": len(service.get_series()),
        "live_categories": service.get_live_categories(),
        "live_count": len(service.get_live_streams()),
    }
    
    return {
        "success": True,
        "data": results
    }

