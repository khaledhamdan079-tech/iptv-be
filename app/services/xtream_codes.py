"""
Xtream Codes API Service
Handles Xtream Codes API calls for IPTV content
"""
import requests
from typing import Dict, List, Optional, Any
import json
from urllib.parse import urlparse, urljoin
from cachetools import TTLCache

# Cache for movies, series, and live TV lists (10 minutes = 600 seconds)
# Cache key format: "vod_{category_id}", "series_{category_id}", "live_{category_id}", or "live_categories"
_content_cache = TTLCache(maxsize=100, ttl=600)  # Increased maxsize for live TV

class XtreamCodesService:
    """Service for interacting with Xtream Codes API"""
    
    def __init__(self, base_url: str, username: str = "", password: str = ""):
        """
        Initialize Xtream Codes service
        
        Args:
            base_url: Base URL of the Xtream Codes server (e.g., http://ddgo770.live:2095)
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, */*',
        })
    
    def _get_api_url(self, action: str) -> str:
        """Build Xtream Codes API URL"""
        return f"{self.base_url}/player_api.php?username={self.username}&password={self.password}&action={action}"
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get user information and account status
        """
        try:
            url = self._get_api_url("get_user_info")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_live_categories(self) -> List[Dict[str, Any]]:
        """
        Get live TV categories
        """
        # Check cache first (categories change less frequently)
        cache_key = "live_categories"
        if cache_key in _content_cache:
            return _content_cache[cache_key]
        
        try:
            url = self._get_api_url("get_live_categories")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            categories = response.json()
            
            # Cache the result (30 minutes for categories)
            _content_cache[cache_key] = categories
            return categories
        except requests.exceptions.RequestException as e:
            return []
    
    def get_live_streams(self, category_id: str = None) -> List[Dict[str, Any]]:
        """
        Get live TV streams
        
        Args:
            category_id: Optional category ID to filter streams
        """
        # Check cache first
        cache_key = f"live_{category_id or 'all'}"
        if cache_key in _content_cache:
            return _content_cache[cache_key]
        
        try:
            url = self._get_api_url("get_live_streams")
            if category_id:
                url += f"&category_id={category_id}"
            response = self.session.get(url, timeout=30)  # Increased timeout for large lists
            response.raise_for_status()
            streams = response.json()
            
            # Cache the result
            _content_cache[cache_key] = streams
            return streams
        except requests.exceptions.RequestException as e:
            return []
    
    def get_live_info(self, stream_id: str) -> Dict[str, Any]:
        """
        Get information for a specific live TV stream
        
        Args:
            stream_id: Stream ID
        """
        try:
            url = self._get_api_url("get_live_info")
            url += f"&stream_id={stream_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {}
    
    def get_live_stream_url(self, stream_id: str, format: str = "m3u8") -> List[Dict[str, str]]:
        """
        Get stream URL for a live TV channel with token (as APK does)
        
        Live TV streams use m3u8 format and need token extraction like movies/series.
        
        Args:
            stream_id: Stream ID
            format: Preferred format (m3u8 or ts) - m3u8 is standard for live TV
        
        Returns:
            List with single dictionary containing the tokenized stream URL
        """
        # Get tokenized URL (m3u8 is standard for live TV)
        # Live TV also needs token extraction for authentication
        url_with_token = self.get_stream_url_with_token(stream_id, "live", "m3u8")
        
        return [{
            "url": url_with_token or f"{self.base_url}/live/{self.username}/{self.password}/{stream_id}.m3u8",
            "format": "m3u8",
            "type": "HLS",
            "quality": "adaptive",
            "is_direct": False,
            "has_token": url_with_token is not None and 'token=' in (url_with_token or '')
        }]
    
    def get_epg(self, stream_id: str = None) -> Dict[str, Any]:
        """
        Get EPG (Electronic Program Guide) data
        
        Args:
            stream_id: Optional stream ID to get EPG for specific channel
        
        Returns:
            EPG data (may be empty if not available)
        """
        try:
            if stream_id:
                # Get short EPG for specific stream
                url = self._get_api_url("get_short_epg")
                url += f"&stream_id={stream_id}"
            else:
                # Get all EPG data
                url = self._get_api_url("get_short_epg")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"epg_listings": []}
    
    def get_vod_categories(self) -> List[Dict[str, Any]]:
        """
        Get VOD (Video on Demand) categories (Movies/Series)
        """
        # Cache categories for longer (30 minutes)
        cache_key = f"vod_categories_{self.base_url}"
        if cache_key in _content_cache:
            return _content_cache[cache_key]
        
        try:
            url = self._get_api_url("get_vod_categories")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            categories = response.json()
            
            # Cache for 30 minutes (1800 seconds) - categories don't change often
            _content_cache[cache_key] = categories
            return categories
        except requests.exceptions.RequestException as e:
            return []
    
    def get_vod_streams(self, category_id: str = None) -> List[Dict[str, Any]]:
        """
        Get VOD streams (Movies)
        
        Args:
            category_id: Optional category ID to filter streams
        """
        # Check cache first
        cache_key = f"vod_{category_id or 'all'}_{self.base_url}"
        if cache_key in _content_cache:
            return _content_cache[cache_key]
        
        try:
            url = self._get_api_url("get_vod_streams")
            if category_id:
                url += f"&category_id={category_id}"
            # Increased timeout for large data fetches (30 seconds)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            movies = response.json()
            
            # Cache the result
            _content_cache[cache_key] = movies
            return movies
        except requests.exceptions.Timeout:
            print(f"Timeout fetching VOD streams (category: {category_id})")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching VOD streams: {e}")
            return []
    
    def get_series_categories(self) -> List[Dict[str, Any]]:
        """
        Get series categories
        """
        # Cache categories for longer (30 minutes)
        cache_key = f"series_categories_{self.base_url}"
        if cache_key in _content_cache:
            return _content_cache[cache_key]
        
        try:
            url = self._get_api_url("get_series_categories")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            categories = response.json()
            
            # Cache for 30 minutes (1800 seconds) - categories don't change often
            _content_cache[cache_key] = categories
            return categories
        except requests.exceptions.RequestException as e:
            return []
    
    def get_series(self, category_id: str = None) -> List[Dict[str, Any]]:
        """
        Get series list
        
        Args:
            category_id: Optional category ID to filter series
        """
        # Check cache first
        cache_key = f"series_{category_id or 'all'}_{self.base_url}"
        if cache_key in _content_cache:
            return _content_cache[cache_key]
        
        try:
            url = self._get_api_url("get_series")
            if category_id:
                url += f"&category_id={category_id}"
            # Increased timeout for large data fetches (30 seconds)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            series = response.json()
            
            # Cache the result
            _content_cache[cache_key] = series
            return series
        except requests.exceptions.Timeout:
            print(f"Timeout fetching series (category: {category_id})")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching series: {e}")
            return []
    
    def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Get series information including episodes
        
        Args:
            series_id: Series ID
        """
        try:
            url = self._get_api_url("get_series_info")
            url += f"&series_id={series_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {}
    
    def get_vod_info(self, vod_id: str) -> Dict[str, Any]:
        """
        Get VOD (movie) information
        
        Args:
            vod_id: VOD ID
        """
        try:
            url = self._get_api_url("get_vod_info")
            url += f"&vod_id={vod_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {}
    
    def search_vod(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for VOD content (movies)
        
        Args:
            query: Search query
        """
        try:
            url = self._get_api_url("get_vod_streams")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            all_vods = response.json()
            
            # Filter by query (case-insensitive)
            query_lower = query.lower()
            return [
                vod for vod in all_vods
                if query_lower in vod.get('name', '').lower() or 
                   query_lower in vod.get('title', '').lower()
            ]
        except requests.exceptions.RequestException as e:
            return []
    
    def search_series(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for series
        
        Args:
            query: Search query
        """
        try:
            url = self._get_api_url("get_series")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            all_series = response.json()
            
            # Filter by query (case-insensitive)
            query_lower = query.lower()
            return [
                series for series in all_series
                if query_lower in series.get('name', '').lower() or 
                   query_lower in series.get('title', '').lower()
            ]
        except requests.exceptions.RequestException as e:
            return []
    
    def get_stream_url(self, stream_id: str, stream_type: str = "movie", extension: str = None) -> str:
        """
        Get stream URL for playback
        
        Args:
            stream_id: Stream ID
            stream_type: Type of stream (movie, series, live, etc.)
            extension: File extension (m3u8, ts, etc.). If None, uses default or container_extension
        """
        ext = extension or self._get_extension()
        
        if stream_type == "movie":
            return f"{self.base_url}/movie/{self.username}/{self.password}/{stream_id}.{ext}"
        elif stream_type == "series":
            return f"{self.base_url}/series/{self.username}/{self.password}/{stream_id}.{ext}"
        else:
            return f"{self.base_url}/live/{self.username}/{self.password}/{stream_id}.{ext}"
    
    def get_stream_url_with_token(self, stream_id: str, stream_type: str = "movie", extension: str = None) -> Optional[str]:
        """
        Get stream URL with token for playback (as used by APK)
        
        The token is obtained by making a GET request to the stream URL,
        which returns a 302 redirect with the token in the Location header.
        
        Important: The redirect may point to a different IP address than the base URL.
        Example: Request to ddgo770.live:2095 redirects to 194.76.0.168:2095 with token.
        We must use the full URL from the Location header as-is.
        
        Args:
            stream_id: Stream ID
            stream_type: Type of stream (movie, series, live, etc.)
            extension: File extension (m3u8, ts, etc.). If None, uses default or container_extension
        
        Returns:
            Stream URL with token, or None if token cannot be obtained
        """
        # First, construct the base URL without token
        base_url = self.get_stream_url(stream_id, stream_type, extension)
        
        try:
            # Make GET request to get token via redirect
            # Note: Using GET (not HEAD) as some servers don't return Location header in HEAD requests
            response = self.session.get(
                base_url,
                allow_redirects=False,
                timeout=15,  # Increased from 5 to 15 seconds for slow servers
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                }
            )
            
            # If we get a redirect (302), extract token from Location header
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if location and 'token=' in location:
                    # IMPORTANT: Use the Location URL as-is (it may be a different IP)
                    # The redirect URL is already complete and absolute
                    if location.startswith('http://') or location.startswith('https://'):
                        print(f"✅ Token extracted successfully for {stream_id} ({stream_type})")
                        return location
                    else:
                        # Relative URL, make it absolute based on original request URL
                        from urllib.parse import urlparse, urljoin
                        absolute_location = urljoin(base_url, location)
                        print(f"✅ Token extracted successfully (relative) for {stream_id} ({stream_type})")
                        return absolute_location
                else:
                    print(f"⚠️ Redirect received but no token in Location header for {stream_id} ({stream_type})")
            elif response.status_code == 200:
                # Some servers return 200 with token in response body or headers
                # Check if token is in response headers
                location = response.headers.get('Location', '')
                if location and 'token=' in location:
                    if location.startswith('http://') or location.startswith('https://'):
                        print(f"✅ Token found in 200 response Location header for {stream_id} ({stream_type})")
                        return location
                print(f"⚠️ Got 200 response (no redirect) for {stream_id} ({stream_type}) - token may not be required")
            elif response.status_code == 401:
                # 401 - try with allow_redirects=True to follow redirects
                print(f"⚠️ Got 401, trying with allow_redirects=True for {stream_id} ({stream_type})")
                try:
                    redirect_response = self.session.get(
                        base_url,
                        allow_redirects=True,
                        timeout=15,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept': '*/*',
                        }
                    )
                    final_url = str(redirect_response.url)
                    if 'token=' in final_url:
                        print(f"✅ Token extracted via redirect for {stream_id} ({stream_type})")
                        redirect_response.close()
                        return final_url
                    redirect_response.close()
                except Exception as redirect_error:
                    print(f"⚠️ Redirect attempt failed: {redirect_error}")
            else:
                print(f"⚠️ Unexpected status code {response.status_code} for {stream_id} ({stream_type})")
            
            # If no redirect or no token, return base URL (fallback)
            print(f"⚠️ No token extracted for {stream_id} ({stream_type}), using base URL")
            return base_url
            
        except Exception as e:
            # If token extraction fails, return base URL without token
            # Log error for debugging but don't fail
            print(f"❌ Error extracting token for {base_url}: {e}")
            import traceback
            traceback.print_exc()
            return base_url
    
    def get_movie_stream_url(self, movie: Dict[str, Any] = None, stream_id: str = None) -> List[Dict[str, str]]:
        """
        Get stream URL for a movie using container_extension (as APK does)
        
        Simplified approach: Use direct URL pattern:
        {base_url}/movie/{username}/{password}/{stream_id}.{container_extension}
        Then extract token via 302 redirect.
        
        Args:
            movie: Movie dictionary from get_vod_streams() or get_vod_info() (optional if stream_id provided)
            stream_id: Direct stream ID to use (takes precedence)
        
        Returns:
            List with single dictionary containing the tokenized stream URL
        """
        # Use provided stream_id or extract from movie
        if not stream_id:
            if movie:
                # Handle both direct movie dict and nested info dict
                if 'info' in movie:
                    # From get_vod_info - stream_id is not in info, need to get from original call
                    # Try to get from movie_data if it's a dict
                    movie_data = movie.get('movie_data', {})
                    if isinstance(movie_data, dict):
                        stream_id = movie_data.get('stream_id', '')
                    else:
                        # movie_data might be a string or we need the original stream_id
                        # In this case, we should pass stream_id separately
                        pass
                else:
                    # Direct movie dict from get_vod_streams()
                    stream_id = movie.get('stream_id', '')
        
        if not stream_id:
            return []
        
        # Get container extension from movie info (can be mp4, mkv, avi, etc.)
        # IMPORTANT: container_extension is in movie_data (from get_vod_info response),
        # or in the movie object itself (from get_vod_streams list)
        container_ext = None
        if movie:
            # First, check movie_data (from get_vod_info - most reliable)
            movie_data = movie.get('movie_data', {})
            if isinstance(movie_data, dict):
                container_ext = movie_data.get('container_extension')
                if container_ext:
                    print(f"DEBUG: Found container_extension in movie_data: {container_ext}")
            
            # Fallback: check the movie object itself (from list)
            if not container_ext:
                container_ext = movie.get('container_extension')
                if container_ext:
                    print(f"DEBUG: Found container_extension in movie object: {container_ext}")
            
            # Last fallback: check info dict (though it usually doesn't have it)
            if not container_ext and 'info' in movie:
                movie_info = movie.get('info', {})
                container_ext = movie_info.get('container_extension')
                if container_ext:
                    print(f"DEBUG: Found container_extension in movie_info: {container_ext}")
        
        # Handle empty string, None, or whitespace - normalize to lowercase
        if container_ext:
            container_ext = str(container_ext).strip().lower()
            if not container_ext:  # Empty after strip
                container_ext = None
        
        # Debug: log what we're using
        print(f"DEBUG: Using container_extension: {container_ext}")
        
        # If no container_extension provided, default to mp4 (fallback)
        if not container_ext:
            print(f"DEBUG: No container_extension found, defaulting to 'mp4'")
            container_ext = 'mp4'
        
        # Construct direct URL: {base_url}/movie/{username}/{password}/{stream_id}.{container_extension}
        # Then get token via 302 redirect (as APK does)
        # container_ext can be mp4, mkv, avi, or any other format the API provides
        url_with_token = self.get_stream_url_with_token(stream_id, "movie", container_ext)
        
        return [{
            "url": url_with_token or f"{self.base_url}/movie/{self.username}/{self.password}/{stream_id}.{container_ext}",
            "format": container_ext,
            "type": "video",
            "quality": "original",
            "is_direct": False,
            "has_token": url_with_token is not None and 'token=' in (url_with_token or '')
        }]
    
    def get_episode_stream_url(self, episode: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get stream URL for a series episode using container_extension (as APK does)
        
        Simplified approach: Use direct URL pattern:
        {base_url}/series/{username}/{password}/{episode_id}.{container_extension}
        Then extract token via 302 redirect.
        
        Args:
            episode: Episode dictionary from get_series_info()
        
        Returns:
            List with single dictionary containing the tokenized stream URL
        """
        # Try different possible ID fields
        episode_id = episode.get('id', '') or episode.get('stream_id', '') or episode.get('episode_id', '')
        if not episode_id:
            return []
        
        # Get container extension from episode (can be mp4, mkv, avi, etc.)
        container_ext = episode.get('container_extension')
        # Handle empty string or None
        if container_ext:
            container_ext = str(container_ext).strip().lower()
            if not container_ext:
                container_ext = None
        
        # If no container_extension provided, default to mp4 (fallback)
        if not container_ext:
            container_ext = 'mp4'
        
        # Construct direct URL: {base_url}/series/{username}/{password}/{episode_id}.{container_extension}
        # Then get token via 302 redirect (as APK does)
        # container_ext can be mp4, mkv, avi, or any other format the API provides
        url_with_token = self.get_stream_url_with_token(episode_id, "series", container_ext)
        
        return [{
            "url": url_with_token or f"{self.base_url}/series/{self.username}/{self.password}/{episode_id}.{container_ext}",
            "format": container_ext,
            "type": "video",
            "quality": "original",
            "is_direct": False,
            "has_token": url_with_token is not None and 'token=' in (url_with_token or '')
        }]
    
    def test_stream_url(self, url: str) -> Dict[str, Any]:
        """
        Test if a stream URL is accessible and returns video content
        
        Args:
            url: Stream URL to test
        
        Returns:
            Dictionary with test results
        """
        try:
            response = self.session.get(url, timeout=5, stream=True, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '').lower()
            content_length = response.headers.get('Content-Length', '0')
            
            # Check if it's HTML (error page)
            if 'text/html' in content_type:
                return {
                    "valid": False,
                    "error": "Returns HTML instead of video",
                    "content_type": content_type,
                    "status_code": response.status_code
                }
            
            # Check if it's a video stream
            is_video = any(vtype in content_type for vtype in ['video/', 'application/vnd.apple.mpegurl', 'application/x-mpegurl'])
            
            return {
                "valid": is_video or response.status_code == 200,
                "content_type": content_type,
                "status_code": response.status_code,
                "content_length": content_length,
                "is_video": is_video
            }
        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _get_extension(self) -> str:
        """Get default stream extension"""
        return "m3u8"  # or "ts" depending on server

