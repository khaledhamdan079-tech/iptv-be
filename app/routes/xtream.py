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


@router.get("/vod/stream-url")
async def get_movie_stream_url(
    request: Request,
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
    
    # NEW: Add segments-based m3u8 playlist URL (working alternative to direct m3u8)
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    segments_m3u8_url = f"{base_url}/api/xtream/segments/m3u8?stream_id={vod_id}&type=movie&playlist_id={playlist_id}"
    # Insert after direct_source and container_ext, but before direct m3u8
    insert_index = len([u for u in stream_urls if u.get('is_direct') or (u.get('format') not in ['m3u8', 'ts'] and u.get('type') == 'video')])
    stream_urls.insert(insert_index, {
        "url": segments_m3u8_url,
        "format": "m3u8",
        "type": "HLS",
        "quality": "adaptive",
        "is_direct": False,
        "is_segments_based": True
    })
    
    # Find recommended URL (prioritize: direct_source, then container_ext like mp4, then segments m3u8, then direct m3u8)
    recommended = next((url for url in stream_urls if url.get('is_direct')), None)
    if not recommended:
        # Prefer container_extension (mp4, etc.) over m3u8
        recommended = next((url for url in stream_urls 
                           if url.get('format') not in ['m3u8', 'ts'] and url.get('type') == 'video'), None)
    if not recommended:
        # Prefer segments-based m3u8 over direct m3u8
        recommended = next((url for url in stream_urls if url.get('is_segments_based')), None)
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
    
    # NEW: Add segments-based m3u8 playlist URL (working alternative to direct m3u8)
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    segments_m3u8_url = f"{base_url}/api/xtream/segments/m3u8?stream_id={episode.get('id')}&type=series&playlist_id={playlist_id}"
    # Insert after direct_source and container_ext, but before direct m3u8
    insert_index = len([u for u in stream_urls if u.get('is_direct') or (u.get('format') not in ['m3u8', 'ts'] and u.get('type') == 'video')])
    stream_urls.insert(insert_index, {
        "url": segments_m3u8_url,
        "format": "m3u8",
        "type": "HLS",
        "quality": "adaptive",
        "is_direct": False,
        "is_segments_based": True
    })
    
    # Find recommended URL (prioritize: direct_source, then container_ext like mp4, then segments m3u8, then direct m3u8)
    recommended = next((url for url in stream_urls if url.get('is_direct')), None)
    if not recommended:
        # Prefer container_extension (mp4, etc.) over m3u8
        recommended = next((url for url in stream_urls 
                           if url.get('format') not in ['m3u8', 'ts'] and url.get('type') == 'video'), None)
    if not recommended:
        # Prefer segments-based m3u8 over direct m3u8
        recommended = next((url for url in stream_urls if url.get('is_segments_based')), None)
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
        
        # Determine if this is an m3u8 request
        is_m3u8 = '.m3u8' in url.lower() or url.endswith('.m3u8')
        
        # For m3u8, use HLS-specific headers; for other formats, use general video headers
        if is_m3u8:
            stream_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.apple.mpegurl, application/x-mpegURL, application/json, */*',
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
            timeout=30,
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
                    else:
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


@router.get("/segments/m3u8")
async def get_segments_m3u8(
    stream_id: str = Query(..., description="Stream ID (episode or movie ID)"),
    type: str = Query(..., description="Content type: 'series' or 'movie'"),
    playlist_id: int = Query(0, description="Playlist ID (default: 0)")
):
    """
    Generate an m3u8 playlist from TS segments
    
    This endpoint creates an HLS playlist by discovering available TS segments
    and generating a valid m3u8 playlist that references them.
    
    The segments are accessed from: /segments/{username}/{password}/{stream_id}/{segment_number}.ts
    """
    service = get_playlist_service(playlist_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="No playlists available")
    
    # Segments use the same path for both series and movies
    segments_base = f"{service.base_url}/segments/{service.username}/{service.password}/{stream_id}"
    
    # Discover available segments by checking segment URLs
    segments = []
    max_segments_to_check = 1000  # Reasonable limit
    
    print(f"Discovering segments for {stream_id}...")
    
    for i in range(max_segments_to_check):
        segment_url = f"{segments_base}/{i}.ts"
        try:
            # Use HEAD request to check if segment exists (faster than GET)
            response = service.session.head(segment_url, timeout=3, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                # Accept video/mp2t, application/octet-stream, or video/*
                if 'video' in content_type or 'mp2t' in content_type or 'octet-stream' in content_type:
                    segments.append(i)
                else:
                    # If we get a non-video response, we've probably reached the end
                    break
            elif response.status_code == 404:
                # Segment doesn't exist, we've reached the end
                break
            else:
                # Other status codes might indicate auth issues, but continue checking
                # We'll stop if we get too many non-200 responses
                if i > 10 and len(segments) == 0:
                    # If first 10 segments all fail, probably no segments available
                    break
        except Exception as e:
            # If request fails consistently, assume we've reached the end
            if i > 10 and len(segments) == 0:
                break
            continue
    
    if not segments:
        raise HTTPException(
            status_code=404,
            detail=f"No segments found for stream_id {stream_id}. The content may not have HLS segments available. Try using the mp4 format instead."
        )
    
    print(f"Found {len(segments)} segments")
    
    # Generate m3u8 playlist
    m3u8_content = "#EXTM3U\n"
    m3u8_content += "#EXT-X-VERSION:3\n"
    m3u8_content += "#EXT-X-TARGETDURATION:10\n"
    m3u8_content += "#EXT-X-MEDIA-SEQUENCE:0\n"
    m3u8_content += "#EXT-X-PLAYLIST-TYPE:VOD\n"
    
    # Add each segment
    for segment_num in segments:
        segment_url = f"{segments_base}/{segment_num}.ts"
        m3u8_content += f"#EXTINF:10.0,\n"
        m3u8_content += f"{segment_url}\n"
    
    m3u8_content += "#EXT-X-ENDLIST\n"
    
    return Response(
        content=m3u8_content,
        media_type="application/vnd.apple.mpegurl",
        headers={
            'Content-Type': 'application/vnd.apple.mpegurl',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache',
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

