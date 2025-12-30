"""
Xtream Codes API Routes
Routes for accessing content via Xtream Codes playlists
"""
from fastapi import APIRouter, Query, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from typing import Optional, Literal
import requests
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
    
    # Check if direct_source is available in movie info (usually the working URL)
    movie_info = vod_info.get('info', {})
    direct_source_url = movie_info.get('direct_source', '')
    container_ext = movie_info.get('container_extension', '')
    if direct_source_url and not any(url.get('url') == direct_source_url for url in stream_urls):
        # Add direct_source as first option if not already included
        stream_urls.insert(0, {
            "url": direct_source_url,
            "format": "direct",
            "type": "direct",
            "quality": "original",
            "is_direct": True
        })
    
    # Find recommended URL (prioritize: direct_source, then container_ext like mp4, then m3u8)
    # Testing shows container_ext (mp4) works, but m3u8 returns empty HTML
    recommended = next((url for url in stream_urls if url.get('is_direct')), None)
    if not recommended:
        # Prefer container_extension (mp4, etc.) over m3u8
        recommended = next((url for url in stream_urls 
                           if url.get('format') not in ['m3u8', 'ts'] and url.get('type') == 'video'), None)
    if not recommended:
        recommended = next((url for url in stream_urls if url.get('format') == 'm3u8'), None)
    if not recommended and stream_urls:
        recommended = stream_urls[0]
    
    return {
        "success": True,
        "vod_id": vod_id,
        "movie_data": {
            "direct_source": direct_source_url,
            "container_extension": movie_info.get('container_extension')
        },
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
    
    # Check if direct_source is available (usually the working URL)
    direct_source_url = episode.get('direct_source', '')
    container_ext = episode.get('container_extension', '')
    if direct_source_url and not any(url.get('url') == direct_source_url for url in stream_urls):
        # Add direct_source as first option if not already included
        stream_urls.insert(0, {
            "url": direct_source_url,
            "format": "direct",
            "type": "direct",
            "quality": "original",
            "is_direct": True
        })
    
    # Find recommended URL (prioritize: direct_source, then container_ext like mp4, then m3u8)
    # Testing shows container_ext (mp4) works, but m3u8 returns empty HTML
    recommended = next((url for url in stream_urls if url.get('is_direct')), None)
    if not recommended:
        # Prefer container_extension (mp4, etc.) over m3u8
        recommended = next((url for url in stream_urls 
                           if url.get('format') not in ['m3u8', 'ts'] and url.get('type') == 'video'), None)
    if not recommended:
        recommended = next((url for url in stream_urls if url.get('format') == 'm3u8'), None)
    if not recommended and stream_urls:
        recommended = stream_urls[0]
    
    return {
        "success": True,
        "series_id": series_id,
        "season": season_number,
        "episode": episode_number,
        "episode_data": {
            "id": episode.get('id'),
            "direct_source": direct_source_url,
            "container_extension": episode.get('container_extension')
        },
        "stream_urls": stream_urls,
        "recommended_url": recommended.get('url') if recommended else None,
        "recommended_format": recommended.get('format') if recommended else None
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
            timeout=10,
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
        
        # Now fetch the stream with the token URL (or original if no redirect)
        response = service.session.get(
            url,
            stream=True,
            timeout=30,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.apple.mpegurl, application/x-mpegURL, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': base_url,
                'Origin': base_url,
            }
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
                    error_detail = f"Stream URL returned empty response. Status: {response.status_code}, Content-Type: {content_type}"
                    if content_length:
                        error_detail += f", Content-Length: {content_length}"
                    error_detail += ". The server may require different authentication or the stream may be unavailable."
                    raise HTTPException(status_code=400, detail=error_detail)
            
            # Check if it's HTML (regardless of content-type header)
            content_preview = first_chunk.decode('utf-8', errors='ignore')
            content_lower = content_preview.lower()
            
            if '<html' in content_lower or '<!doctype' in content_lower or content_lower.strip().startswith('<!'):
                response.close()
                # Log the actual response for debugging
                preview = content_preview[:500].replace('\n', ' ').replace('\r', ' ')
                raise HTTPException(
                    status_code=400,
                    detail=f"Stream URL returns HTML instead of video. Server response: {preview[:200]}... The URL may require different authentication. Please check if the episode has a direct_source URL available in the episode_data field."
                )
            
            # Check if it's a valid m3u8 playlist
            if '.m3u8' in url or 'm3u8' in url.lower():
                content_stripped = content_preview.strip()
                if not (content_stripped.startswith('#EXTM3U') or content_stripped.startswith('#EXT-X')):
                    # Not a valid m3u8, might be HTML or error message
                    response.close()
                    preview = content_preview[:300].replace('\n', ' ').replace('\r', ' ')
                    raise HTTPException(
                        status_code=400,
                        detail=f"Stream URL returned invalid m3u8 content. Expected '#EXTM3U' or '#EXT-X' but got: {preview[:200]}..."
                    )
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
                # If we read first chunk, yield it first
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
            if '.m3u8' in url:
                media_type = 'application/vnd.apple.mpegurl'
            elif '.ts' in url:
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

