"""
Xtream Codes API Routes
Routes for accessing content via Xtream Codes playlists
"""
from fastapi import APIRouter, Query, HTTPException, Request, Response
from starlette.requests import Request
from fastapi.responses import StreamingResponse
from typing import Optional, Literal
import requests
import time
from cachetools import TTLCache
from app.services.xtream_codes import XtreamCodesService
from app.services.maso_api import MasoAPIService

# Cache for segment discovery results (5 minutes)
_segments_cache = TTLCache(maxsize=100, ttl=300)

router = APIRouter(prefix="/api/xtream", tags=["xtream"])

# Lazy-load maso_service to avoid blocking startup
_maso_service = None
_playlists_cache = None
_playlists_cache_time = None
_PLAYLISTS_CACHE_TTL = 300  # 5 minutes

def get_maso_service():
    """Lazy-load MasoAPIService to avoid blocking startup"""
    global _maso_service
    if _maso_service is None:
        _maso_service = MasoAPIService()
    return _maso_service

def get_playlist_service(playlist_id: int = 0) -> Optional[XtreamCodesService]:
    """Get Xtream Codes service from Maso playlist URLs"""
    import time
    
    global _playlists_cache, _playlists_cache_time
    
    # Check cache first
    current_time = time.time()
    if _playlists_cache is not None and _playlists_cache_time is not None:
        if current_time - _playlists_cache_time < _PLAYLISTS_CACHE_TTL:
            playlists = _playlists_cache
        else:
            # Cache expired
            _playlists_cache = None
            _playlists_cache_time = None
            playlists = None
    else:
        playlists = None
    
    # Fetch if not cached
    if playlists is None:
        try:
            maso_service = get_maso_service()
            playlists = maso_service.get_playlist_urls()
            # Cache the result
            _playlists_cache = playlists
            _playlists_cache_time = current_time
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            # Use cached data if available, even if expired
            if _playlists_cache is not None:
                playlists = _playlists_cache
            else:
                return None
    
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
    try:
        maso_service = get_maso_service()
        playlists = maso_service.get_playlist_urls()
        
        return {
            "success": True,
            "data": {
                "playlists": playlists,
                "count": len(playlists) if playlists else 0
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "playlists": [],
                "count": 0
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
    category_id: Optional[str] = Query(None, description="Category ID to filter"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page (max 500)")
):
    """Get VOD movies with pagination"""
    import asyncio
    
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    try:
        # Run the blocking call in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        movies = await loop.run_in_executor(None, service.get_vod_streams, category_id)
        
        # Calculate pagination
        total_count = len(movies)
        offset = (page - 1) * limit
        paginated_movies = movies[offset:offset + limit]
        
        return {
            "success": True,
            "data": paginated_movies,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 0,
                "has_next": offset + limit < total_count,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching movies: {str(e)}"
        )


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
    category_id: Optional[str] = Query(None, description="Category ID to filter"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page (max 500)")
):
    """Get series list with pagination"""
    import asyncio
    
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    try:
        # Run the blocking call in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        series = await loop.run_in_executor(None, service.get_series, category_id)
        
        # Calculate pagination
        total_count = len(series)
        offset = (page - 1) * limit
        paginated_series = series[offset:offset + limit]
        
        return {
            "success": True,
            "data": paginated_series,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 0,
                "has_next": offset + limit < total_count,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching series: {str(e)}"
        )


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


@router.get("/live/categories")
async def get_live_categories(playlist_id: int = Query(0, description="Playlist ID (default: 0)")):
    """Get live TV categories"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    categories = service.get_live_categories()
    
    return {
        "success": True,
        "data": categories,
        "count": len(categories)
    }


@router.get("/live/streams")
async def get_live_streams(
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    category_id: Optional[str] = Query(None, description="Category ID to filter"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page (max 500)")
):
    """Get live TV streams with pagination"""
    import asyncio
    
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    try:
        # Run the blocking call in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        streams = await loop.run_in_executor(None, service.get_live_streams, category_id)
        
        # Calculate pagination
        total_count = len(streams)
        offset = (page - 1) * limit
        paginated_streams = streams[offset:offset + limit]
        
        return {
            "success": True,
            "data": paginated_streams,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 0,
                "has_next": offset + limit < total_count,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching live streams: {str(e)}"
        )


@router.get("/live/info")
async def get_live_info(
    stream_id: str = Query(..., description="Live stream ID"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get live TV stream information"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    info = service.get_live_info(stream_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Live stream not found")
    
    return {
        "success": True,
        "data": info
    }


@router.get("/live/stream-url")
async def get_live_stream_url(
    request: Request,
    stream_id: str = Query(..., description="Live stream ID"),
    format: str = Query("m3u8", description="Stream format (m3u8 or ts)"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get stream URL for a live TV channel
    
    Returns tokenized m3u8 URL (with authentication token) for live TV streaming.
    Token is extracted via 302 redirect (as APK does).
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    # Get stream URL with token (m3u8 is standard for live TV)
    stream_urls = service.get_live_stream_url(stream_id, format)
    
    if not stream_urls:
        raise HTTPException(status_code=404, detail="Could not generate stream URL")
    
    # Return the single recommended URL (with token if available)
    recommended = stream_urls[0]
    
    return {
        "success": True,
        "stream_id": stream_id,
        "stream_urls": stream_urls,
        "recommended_url": recommended.get('url'),
        "recommended_format": recommended.get('format')
    }


@router.get("/live/epg")
async def get_epg(
    stream_id: Optional[str] = Query(None, description="Optional stream ID to get EPG for specific channel"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get EPG (Electronic Program Guide) data
    
    If stream_id is provided, returns EPG for that specific channel.
    Otherwise, returns all available EPG data.
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    epg_data = service.get_epg(stream_id)
    
    return {
        "success": True,
        "data": epg_data
    }


@router.get("/vod/stream-url")
async def get_movie_stream_url(
    request: Request,
    vod_id: str = Query(..., description="VOD ID (stream_id)"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get stream URL for a movie
    
    Simplified approach: Uses direct URL pattern with container_extension:
    {base_url}/movie/{username}/{password}/{stream_id}.{container_extension}
    Token is extracted via 302 redirect (as APK does).
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    # Get movie info first (includes movie_data with container_extension)
    vod_info = service.get_vod_info(vod_id)
    if not vod_info or not vod_info.get('info'):
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # NOTE: container_extension is in movie_data (from get_vod_info response)
    # get_movie_stream_url will automatically find it there
    
    # Get stream URL using the vod_id as stream_id
    # This will construct: {base_url}/movie/{username}/{password}/{vod_id}.{container_extension}
    # And extract token via 302 redirect
    stream_urls = service.get_movie_stream_url(movie=vod_info, stream_id=vod_id)
    
    if not stream_urls:
        raise HTTPException(status_code=404, detail="Could not generate stream URL")
    
    # Return the single recommended URL (with token if available)
    recommended = stream_urls[0]
    
    movie_info = vod_info.get('info', {})
    return {
        "success": True,
        "vod_id": vod_id,
        "movie_data": {
            "container_extension": movie_info.get('container_extension')
        },
        "stream_urls": stream_urls,
        "recommended_url": recommended.get('url'),
        "recommended_format": recommended.get('format')
    }


@router.get("/series/episode/stream-url")
async def get_episode_stream_url(
    request: Request,
    series_id: str = Query(..., description="Series ID"),
    season_number: str = Query(..., description="Season number"),
    episode_number: str = Query(..., description="Episode number"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Get stream URL for a series episode
    
    Simplified approach: Uses direct URL pattern with container_extension:
    {base_url}/series/{username}/{password}/{episode_id}.{container_extension}
    Token is extracted via 302 redirect (as APK does).
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
    
    # Get stream URL
    # This will construct: {base_url}/series/{username}/{password}/{episode_id}.{container_extension}
    # And extract token via 302 redirect
    stream_urls = service.get_episode_stream_url(episode)
    
    if not stream_urls:
        raise HTTPException(status_code=404, detail="Could not generate stream URL")
    
    # Return the single recommended URL (with token if available)
    recommended = stream_urls[0]
    
    return {
        "success": True,
        "series_id": series_id,
        "season": season_number,
        "episode": episode_number,
        "episode_data": {
            "id": episode.get('id'),
            "container_extension": episode.get('container_extension')
        },
        "stream_urls": stream_urls,
        "recommended_url": recommended.get('url'),
        "recommended_format": recommended.get('format')
    }


@router.get("/stream/proxy")
async def proxy_stream(
    url: str = Query(..., description="Stream URL to proxy"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Proxy stream URL through backend to handle authentication
    
    This endpoint fetches the stream from Xtream Codes and forwards it to the client.
    Use this when direct stream URLs return HTML instead of video.
    
    Note: Even if initial response is HTML, we'll try to forward it as the video player
    might handle redirects or the server might serve video after authentication.
    
    Resume Support:
    - Position parameters (position, seek, time, start, offset, resume, continue) are preserved
    - Server includes these in the token URL redirect automatically
    - Example: /stream/proxy?url=.../movie.mp4?position=1000
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    try:
        # Parse URL to get base for referrer
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Xtream Codes often returns 302 redirects with tokens
        # First, check for redirect without following (to get token URL)
        initial_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': base_url,
            'Origin': base_url,
        }
        
        initial_response = service.session.get(
            url,
            stream=False,
            timeout=30,  # Increased from 10 to 30 seconds for slow servers
            allow_redirects=False,
            headers=initial_headers
        )
        
        # If we get a redirect (302), follow it to get the token URL
        if initial_response.status_code == 302:
            redirect_url = initial_response.headers.get('Location')
            if redirect_url:
                # Use the redirect URL which contains the token
                if not redirect_url.startswith('http'):
                    redirect_url = f"{base_url}{redirect_url}" if redirect_url.startswith('/') else f"{base_url}/{redirect_url}"
                url = redirect_url
            initial_response.close()
        elif initial_response.status_code == 200:
            # If we get 200 directly, we can use it
            initial_response.close()
        else:
            initial_response.close()
            raise HTTPException(
                status_code=initial_response.status_code,
                detail=f"Stream server returned status {initial_response.status_code} on initial request."
            )
        
        # Determine content type from URL
        is_m3u8 = '.m3u8' in url.lower() or url.endswith('.m3u8')
        is_ts_segment = '.ts' in url.lower() or url.endswith('.ts')
        
        # For m3u8, use HLS-specific headers; for TS segments, use video headers; for other formats, use general video headers
        if is_m3u8:
            stream_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.apple.mpegurl, application/x-mpegURL, application/json, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': base_url,
                'Origin': base_url,
                'Cache-Control': 'no-cache',
            }
        elif is_ts_segment:
            # TS segments are binary video data - use video headers
            stream_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'video/mp2t, video/*, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': base_url,
                'Origin': base_url,
                'Cache-Control': 'no-cache',
            }
        else:
            stream_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': base_url,
                'Origin': base_url,
                'Range': 'bytes=0-',  # Request from start for progressive download
            }
        
        # Now fetch the stream with the token URL (or original if no redirect)
        response = service.session.get(
            url,
            stream=True,
            timeout=60,  # Increased from 30 to 60 seconds for slow streaming servers
            allow_redirects=True,
            headers=stream_headers
        )
        
        # Check status code (200 or 206 for partial content)
        if response.status_code not in [200, 206]:
            response.close()
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Stream server returned status {response.status_code}. The URL may require authentication or the stream may be unavailable."
            )
        
        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Always read first chunk to verify it's not HTML (some servers return HTML with wrong content-type)
        first_chunk = None
        try:
            # Read first chunk - some servers may take time to start streaming
            # Use a small timeout to avoid hanging
            iterator = response.iter_content(chunk_size=1024)
            
            # Try to get first chunk
            try:
                first_chunk = next(iterator, b'')
            except StopIteration:
                first_chunk = b''
            except Exception as read_error:
                # If reading fails, the stream might be empty or server error
                response.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"Error reading stream from server: {str(read_error)}. The server may require different authentication."
                )
            
            # If no chunk, check response details
            if not first_chunk or len(first_chunk) == 0:
                # Check response headers for clues
                content_length = response.headers.get('Content-Length', '')
                transfer_encoding = response.headers.get('Transfer-Encoding', '')
                
                # If chunked encoding, empty first chunk might be OK (wait for more)
                if transfer_encoding.lower() == 'chunked':
                    # For chunked encoding, try to read more
                    try:
                        first_chunk = next(iterator, b'')
                    except:
                        pass
                
                # If still empty after trying chunked, it's really empty
                if not first_chunk or len(first_chunk) == 0:
                    response.close()
                    # For m3u8, provide specific guidance
                    if is_m3u8:
                        error_detail = "m3u8 stream returned empty response. This server may not provide HLS streams for this content. Try using the mp4 format (container_extension) instead, which is available in the stream_urls list."
                    elif is_ts_segment:
                        error_detail = f"TS segment returned empty response. Status: {response.status_code}, Content-Type: {content_type}. The segment may not exist or may require different authentication."
                    else:
                        error_detail = f"Stream URL returned empty response. Status: {response.status_code}, Content-Type: {content_type}"
                        if content_length:
                            error_detail += f", Content-Length: {content_length}"
                        error_detail += ". The server may require different authentication or the stream may be unavailable."
                    raise HTTPException(status_code=400, detail=error_detail)
            
            # For TS segments, skip HTML checking (they're binary video data)
            # Only check for HTML in text-based formats (m3u8, etc.)
            if not is_ts_segment:
                # Check if it's HTML (regardless of content-type header)
                try:
                    content_preview = first_chunk.decode('utf-8', errors='ignore')
                    content_lower = content_preview.lower()
                    
                    if '<html' in content_lower or '<!doctype' in content_lower or content_lower.strip().startswith('<!'):
                        response.close()
                        # Log the actual response for debugging
                        preview = content_preview[:500].replace('\n', ' ').replace('\r', ' ')
                        # For m3u8, provide specific guidance
                        if is_m3u8:
                            raise HTTPException(
                                status_code=400,
                                detail="m3u8 stream returns HTML instead of playlist. This server may not provide HLS streams for this content. The episode likely only has mp4 format available. Check the stream_urls list for mp4 URLs (container_extension: 'mp4')."
                            )
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Stream URL returns HTML instead of video. Server response: {preview[:200]}... The URL may require different authentication. Please check if the episode has a direct_source URL available in the episode_data field."
                            )
                    
                    # Check if it's a valid m3u8 playlist
                    if is_m3u8:
                        content_stripped = content_preview.strip()
                        if not (content_stripped.startswith('#EXTM3U') or content_stripped.startswith('#EXT-X')):
                            # Not a valid m3u8, might be HTML or error message
                            response.close()
                            preview = content_preview[:300].replace('\n', ' ').replace('\r', ' ')
                            raise HTTPException(
                                status_code=400,
                                detail=f"m3u8 stream returned invalid content. Expected '#EXTM3U' or '#EXT-X' but got: {preview[:200]}... This server may not provide HLS streams. Try using the mp4 format instead (available in stream_urls with container_extension: 'mp4')."
                            )
                except UnicodeDecodeError:
                    # If we can't decode as UTF-8, it's likely binary (video data) - that's fine
                    pass
        except StopIteration:
            response.close()
            raise HTTPException(
                status_code=400,
                detail="Stream URL returned empty response"
            )
        except HTTPException:
            raise
        except Exception as e:
            # If we can't read, close and re-raise
            response.close()
            raise HTTPException(
                status_code=400,
                detail=f"Error reading stream: {str(e)}"
            )
        
        # Forward the stream
        def generate():
            try:
                # For m3u8 playlists, we need to rewrite relative URLs to absolute URLs
                # This ensures TS segments can be fetched correctly
                if is_m3u8:
                    # Read the entire playlist (m3u8 files are typically small)
                    playlist_content = first_chunk if first_chunk else b''
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            playlist_content += chunk
                    
                    # Decode and rewrite URLs
                    try:
                        playlist_text = playlist_content.decode('utf-8')
                        lines = playlist_text.split('\n')
                        rewritten_lines = []
                        
                        from urllib.parse import urljoin, urlparse
                        base_parsed = urlparse(url)
                        # For absolute paths (starting with /), use server root
                        # For relative paths, use the m3u8 directory
                        server_root = f"{base_parsed.scheme}://{base_parsed.netloc}"
                        m3u8_dir = f"{server_root}{'/'.join(base_parsed.path.split('/')[:-1])}/"
                        
                        # Extract token from original URL if present (for TS segments)
                        token_param = ''
                        if 'token=' in url:
                            from urllib.parse import parse_qs
                            query_params = parse_qs(base_parsed.query)
                            if 'token' in query_params:
                                token_param = f"?token={query_params['token'][0]}"
                        
                        for line in lines:
                            # Skip empty lines and comments (unless they contain URLs)
                            if not line.strip() or line.strip().startswith('#'):
                                # Check if comment line contains a URL that needs rewriting
                                if 'http://' in line or 'https://' in line:
                                    rewritten_lines.append(line)
                                else:
                                    rewritten_lines.append(line)
                            else:
                                # This is likely a URL line (TS segment or another playlist)
                                segment_url = line.strip()
                                if segment_url:
                                    # If relative URL, make it absolute
                                    # This ensures the player can fetch TS segments correctly
                                    if not segment_url.startswith('http://') and not segment_url.startswith('https://'):
                                        # Absolute paths (starting with /) use server root
                                        # Relative paths use m3u8 directory
                                        if segment_url.startswith('/'):
                                            absolute_url = urljoin(server_root, segment_url)
                                        else:
                                            absolute_url = urljoin(m3u8_dir, segment_url)
                                        
                                        # Add token to TS segment URLs if we have one
                                        if token_param and (segment_url.endswith('.ts') or '.ts?' in segment_url):
                                            # Check if URL already has query params
                                            if '?' in absolute_url:
                                                absolute_url += f"&{token_param.lstrip('?')}"
                                            else:
                                                absolute_url += token_param
                                        
                                        rewritten_lines.append(absolute_url)
                                    else:
                                        rewritten_lines.append(segment_url)
                        
                        rewritten_playlist = '\n'.join(rewritten_lines)
                        yield rewritten_playlist.encode('utf-8')
                    except Exception as rewrite_error:
                        # If rewriting fails, just forward original content
                        print(f"Warning: Could not rewrite m3u8 playlist URLs: {rewrite_error}")
                        if first_chunk:
                            yield first_chunk
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                yield chunk
                else:
                    # For non-m3u8 streams, forward as-is
                    if first_chunk:
                        yield first_chunk
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
            finally:
                response.close()
        
        # Determine content type - prefer video types
        media_type = content_type
        if not media_type or 'text/html' in media_type:
            # Try to determine from URL
            if is_m3u8:
                media_type = 'application/vnd.apple.mpegurl'
            elif is_ts_segment:
                media_type = 'video/mp2t'
            else:
                media_type = 'application/octet-stream'
        
        # Set headers
        headers = {
            'Content-Type': media_type,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': '*',
        }
        
        # Copy relevant headers from response
        for header in ['Content-Length', 'Accept-Ranges', 'Content-Range', 'Cache-Control']:
            if header in response.headers:
                headers[header] = response.headers[header]
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers=headers
        )
        
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stream: {str(e)}")


@router.get("/segments/{stream_id}.m3u8")
async def get_segments_m3u8_path(
    request: Request,
    stream_id: str,
    type: str = Query(..., description="Content type: 'series' or 'movie'"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Generate m3u8 playlist - path-based URL ending with .m3u8 for HLS detection"""
    return await get_segments_m3u8_impl(request, stream_id, type, playlist_id)

@router.get("/segments/m3u8")
async def get_segments_m3u8(
    request: Request,
    stream_id: str = Query(..., description="Stream ID (episode or movie ID)"),
    type: str = Query(..., description="Content type: 'series' or 'movie'"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Generate m3u8 playlist - query parameter version (for backwards compatibility)"""
    return await get_segments_m3u8_impl(request, stream_id, type, playlist_id)

async def get_segments_m3u8_impl(
    request: Request,
    stream_id: str,
    type: str,
    playlist_id: int
):
    """
    Generate an m3u8 playlist from TS segments
    
    This endpoint creates an HLS playlist by discovering available TS segments
    and generating a valid m3u8 playlist that references them.
    
    The segments are accessed from: /segments/{username}/{password}/{stream_id}/{segment_number}.ts
    """
    import asyncio
    import concurrent.futures
    
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    # Check cache first
    cache_key = f"segments_{stream_id}_{playlist_id}"
    if cache_key in _segments_cache:
        cached_segments = _segments_cache[cache_key]
        print(f"Using cached segments for {stream_id}: {len(cached_segments)} segments")
    else:
        cached_segments = None
    
    # Segments use the same path for both series and movies
    segments_base = f"{service.base_url}/segments/{service.username}/{service.password}/{stream_id}"
    
    # Use cached segments if available, otherwise discover
    if cached_segments is not None:
        segments = cached_segments
    else:
        # Use concurrent requests to discover segments faster
        def check_segment(segment_num: int) -> Optional[int]:
            """Check if a segment exists and is accessible, return segment number if it does
            
            IMPORTANT: We use GET (not HEAD) because some servers return 200 for HEAD
            but 404 for GET. We need to verify the segment actually exists and returns data.
            """
            segment_url = f"{segments_base}/{segment_num}.ts"
            try:
                # Use GET request with Range header to verify segment is actually accessible
                # Range: bytes=0-1023 to fetch just first 1KB (faster than full segment)
                headers = {
                    'Range': 'bytes=0-1023',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'video/mp2t, video/*, */*',
                }
                response = service.session.get(segment_url, timeout=0.5, allow_redirects=True, headers=headers, stream=False)
                
                # Must be 200 or 206 (partial content)
                if response.status_code not in [200, 206]:
                    return None
                
                # Must have actual content (not empty)
                if not response.content or len(response.content) == 0:
                    return None
                
                # Check content type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    # Server returned HTML (404 page) - segment doesn't exist
                    return None
                
                # Verify it's actually TS data (starts with 0x47 sync byte)
                # Some servers return HTML even with video/mp2t content-type
                if response.content[0] == 0x47:  # TS sync byte
                    return segment_num
                else:
                    # Check if it's HTML error page
                    try:
                        text = response.content.decode('utf-8', errors='ignore')[:100]
                        if '<html' in text.lower() or '404' in text.lower() or 'not found' in text.lower():
                            return None
                    except:
                        pass
                    # Not TS data and not HTML - might be valid but not TS format
                    # For now, we'll accept it if content-type suggests video
                    if 'video' in content_type or 'mp2t' in content_type or 'octet-stream' in content_type:
                        return segment_num
                
                return None
            except Exception as e:
                # Any exception means segment is not accessible
                return None
        
        # Check segments in batches concurrently with overall timeout
        segments = []
        max_segments_to_check = 200  # Reduced limit for faster discovery (200 segments = ~33 minutes of content)
        batch_size = 30  # Increased batch size for faster discovery
        min_segments_for_early_exit = 50  # If we find this many, it's probably enough
        
        print(f"Discovering segments for {stream_id}...")
        discovery_start_time = time.time()
        discovery_timeout = 8  # Overall timeout of 8 seconds for discovery
        
        # Use ThreadPoolExecutor for concurrent HEAD requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Check first batch to see if segments exist
            first_batch = list(range(min(30, max_segments_to_check)))
            futures = {executor.submit(check_segment, i): i for i in first_batch}
            
            found_any = False
            try:
                for future in concurrent.futures.as_completed(futures, timeout=3):
                    if time.time() - discovery_start_time > discovery_timeout:
                        print(f"Discovery timeout reached, using {len(segments)} segments found so far")
                        break
                    result = future.result()
                    if result is not None:
                        segments.append(result)
                        found_any = True
            except concurrent.futures.TimeoutError:
                pass
            
            # If we found segments in first batch, continue checking in batches
            if found_any and time.time() - discovery_start_time < discovery_timeout:
                # Sort segments found so far
                segments.sort()
                
                # Continue checking from where we left off
                for batch_start in range(30, max_segments_to_check, batch_size):
                    if time.time() - discovery_start_time > discovery_timeout:
                        print(f"Discovery timeout reached, using {len(segments)} segments found so far")
                        break
                    
                    # Early exit if we found enough segments
                    if len(segments) >= min_segments_for_early_exit:
                        # Fill in any gaps in the first min_segments_for_early_exit range
                        print(f"Found {len(segments)} segments, filling gaps...")
                        for i in range(min_segments_for_early_exit):
                            if i not in segments:
                                result = check_segment(i)
                                if result is not None:
                                    segments.append(result)
                        break
                    
                    batch_end = min(batch_start + batch_size, max_segments_to_check)
                    batch = list(range(batch_start, batch_end))
                    
                    futures = {executor.submit(check_segment, i): i for i in batch}
                    batch_found = False
                    
                    try:
                        for future in concurrent.futures.as_completed(futures, timeout=2):
                            if time.time() - discovery_start_time > discovery_timeout:
                                break
                            result = future.result()
                            if result is not None:
                                segments.append(result)
                                batch_found = True
                    except concurrent.futures.TimeoutError:
                        pass
                    
                    # If no segments found in this batch, we've probably reached the end
                    if not batch_found:
                        # Check a few more to be sure
                        for i in range(batch_end, min(batch_end + 5, max_segments_to_check)):
                            if time.time() - discovery_start_time > discovery_timeout:
                                break
                            result = check_segment(i)
                            if result is not None:
                                segments.append(result)
                            else:
                                break
                        break
    
    if not segments:
        # Segments don't exist for this content - return clear error
        raise HTTPException(
            status_code=404,
            detail=f"No TS segments found for stream_id {stream_id}. This server does not provide HLS segments at /segments/ path. Please use the MP4 format (container_extension) instead, which is available in the stream_urls list."
        )
    
    # Sort segments
    segments.sort()
    print(f"Found {len(segments)} segments (0-{segments[-1]})")
    
    # Cache the result
    if cached_segments is None:
        _segments_cache[cache_key] = segments
    
    # Generate m3u8 playlist with proxied segment URLs
    # Use proxy URLs so segments can be accessed by the Flutter app
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    m3u8_content = "#EXTM3U\n"
    m3u8_content += "#EXT-X-VERSION:3\n"
    m3u8_content += "#EXT-X-TARGETDURATION:10\n"
    m3u8_content += "#EXT-X-MEDIA-SEQUENCE:0\n"
    m3u8_content += "#EXT-X-PLAYLIST-TYPE:VOD\n"
    
    # Add each segment with proxied URL
    for segment_num in segments:
        # Direct segment URL from Xtream Codes
        direct_segment_url = f"{segments_base}/{segment_num}.ts"
        # Proxy URL for the segment
        from urllib.parse import quote
        proxied_segment_url = f"{base_url}/api/xtream/stream/proxy?url={quote(direct_segment_url)}&playlist_id={playlist_id}"
        
        m3u8_content += f"#EXTINF:10.0,\n"
        m3u8_content += f"{proxied_segment_url}\n"
    
    m3u8_content += "#EXT-X-ENDLIST\n"
    
    return Response(
        content=m3u8_content,
        media_type="application/vnd.apple.mpegurl",
        headers={
            'Content-Type': 'application/vnd.apple.mpegurl',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'no-cache',
            'X-Content-Type-Options': 'nosniff',
        }
    )


@router.get("/stream/test")
async def test_stream_url(
    url: str = Query(..., description="Stream URL to test"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """Test if a stream URL is accessible and returns video content"""
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    result = service.test_stream_url(url)
    
    return {
        "success": True,
        "url": url,
        "test_result": result
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

