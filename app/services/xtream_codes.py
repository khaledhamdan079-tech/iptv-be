"""
Xtream Codes API Service
Handles Xtream Codes API calls for IPTV content
"""
import requests
from typing import Dict, List, Optional, Any
import json
from urllib.parse import urlparse, urljoin

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
        try:
            url = self._get_api_url("get_live_categories")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return []
    
    def get_live_streams(self, category_id: str = None) -> List[Dict[str, Any]]:
        """
        Get live TV streams
        
        Args:
            category_id: Optional category ID to filter streams
        """
        try:
            url = self._get_api_url("get_live_streams")
            if category_id:
                url += f"&category_id={category_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return []
    
    def get_vod_categories(self) -> List[Dict[str, Any]]:
        """
        Get VOD (Video on Demand) categories (Movies/Series)
        """
        try:
            url = self._get_api_url("get_vod_categories")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return []
    
    def get_vod_streams(self, category_id: str = None) -> List[Dict[str, Any]]:
        """
        Get VOD streams (Movies)
        
        Args:
            category_id: Optional category ID to filter streams
        """
        try:
            url = self._get_api_url("get_vod_streams")
            if category_id:
                url += f"&category_id={category_id}"
            # Increased timeout for large data fetches (30 seconds)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
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
        try:
            url = self._get_api_url("get_series_categories")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return []
    
    def get_series(self, category_id: str = None) -> List[Dict[str, Any]]:
        """
        Get series list
        
        Args:
            category_id: Optional category ID to filter series
        """
        try:
            url = self._get_api_url("get_series")
            if category_id:
                url += f"&category_id={category_id}"
            # Increased timeout for large data fetches (30 seconds)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
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
    
    def get_movie_stream_url(self, movie: Dict[str, Any] = None, stream_id: str = None) -> List[Dict[str, str]]:
        """
        Get all possible stream URLs for a movie with metadata
        
        Args:
            movie: Movie dictionary from get_vod_streams() or get_vod_info() (optional if stream_id provided)
            stream_id: Direct stream ID to use (takes precedence)
        
        Returns:
            List of dictionaries with stream URLs and metadata
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
        
        urls = []
        # Get container extension and direct source from movie if available
        container_ext = 'm3u8'
        direct_source = ''
        if movie:
            if 'info' in movie:
                movie_info = movie.get('info', {})
                container_ext = movie_info.get('container_extension', '') or container_ext
                direct_source = movie_info.get('direct_source', '') or direct_source
            else:
                container_ext = movie.get('container_extension', 'm3u8')
                direct_source = movie.get('direct_source', '')
        
        # Prioritize direct_source if available (usually the actual working URL)
        if direct_source:
            urls.append({
                "url": direct_source,
                "format": "direct",
                "type": "direct",
                "quality": "original",
                "is_direct": True
            })
        
        # IMPORTANT: Prioritize container_extension (e.g., mp4) over m3u8
        # Testing shows .mp4 works but .m3u8 returns empty HTML
        if container_ext and container_ext not in ['m3u8', 'ts']:
            urls.append({
                "url": f"{self.base_url}/movie/{self.username}/{self.password}/{stream_id}.{container_ext}",
                "format": container_ext,
                "type": "video" if container_ext in ['mp4', 'mkv', 'avi'] else "direct",
                "quality": "original",
                "is_direct": False
            })
        
        # Note: Segments-based m3u8 will be added by the route handler
        # We can't use backend URL here since we don't know it in the service
        # The route will add this option when returning stream URLs
        
        # Add direct m3u8 and ts as fallback options
        urls.append({
            "url": f"{self.base_url}/movie/{self.username}/{self.password}/{stream_id}.m3u8",
            "format": "m3u8",
            "type": "HLS",
            "quality": "adaptive",
            "is_direct": False
        })
        urls.append({
            "url": f"{self.base_url}/movie/{self.username}/{self.password}/{stream_id}.ts",
            "format": "ts",
            "type": "MPEG-TS",
            "quality": "standard",
            "is_direct": False
        })
        
        return urls
    
    def get_episode_stream_url(self, episode: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get all possible stream URLs for a series episode with metadata
        
        Args:
            episode: Episode dictionary from get_series_info()
        
        Returns:
            List of dictionaries with stream URLs and metadata
        """
        # Try different possible ID fields
        episode_id = episode.get('id', '') or episode.get('stream_id', '') or episode.get('episode_id', '')
        if not episode_id:
            return []
        
        urls = []
        container_ext = episode.get('container_extension', 'm3u8')
        direct_source = episode.get('direct_source', '')
        
        # Prioritize direct_source if available (usually the actual working URL)
        if direct_source:
            urls.append({
                "url": direct_source,
                "format": "direct",
                "type": "direct",
                "quality": "original",
                "is_direct": True
            })
        
        # IMPORTANT: Prioritize container_extension (e.g., mp4) over m3u8
        # Testing shows .mp4 works but .m3u8 returns empty HTML
        if container_ext and container_ext not in ['m3u8', 'ts']:
            urls.append({
                "url": f"{self.base_url}/series/{self.username}/{self.password}/{episode_id}.{container_ext}",
                "format": container_ext,
                "type": "video" if container_ext in ['mp4', 'mkv', 'avi'] else "direct",
                "quality": "original",
                "is_direct": False
            })
        
        # Note: Segments-based m3u8 will be added by the route handler
        # We can't use backend URL here since we don't know it in the service
        # The route will add this option when returning stream URLs
        
        # Add direct m3u8 and ts as fallback options
        urls.append({
            "url": f"{self.base_url}/series/{self.username}/{self.password}/{episode_id}.m3u8",
            "format": "m3u8",
            "type": "HLS",
            "quality": "adaptive",
            "is_direct": False
        })
        urls.append({
            "url": f"{self.base_url}/series/{self.username}/{self.password}/{episode_id}.ts",
            "format": "ts",
            "type": "MPEG-TS",
            "quality": "standard",
            "is_direct": False
        })
        
        return urls
    
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

