"""
Maso API Service
Handles API calls to maso1001.xyz endpoints extracted from Master2024.apk
"""
import requests
from typing import Dict, List, Optional, Any
import json
import re
from bs4 import BeautifulSoup

class MasoAPIService:
    """Service for interacting with Maso API endpoints"""
    
    BASE_URL = "https://maso1001.xyz/maso/api"
    
    def __init__(self, username: str = None, password: str = None, mac_address: str = None):
        self.username = username
        self.password = password
        self.mac_address = mac_address
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://maso1001.xyz/',
            'Origin': 'https://maso1001.xyz'
        })
        
        # Add credentials to session if provided
        if username and password:
            self.session.auth = (username, password)
        
        # Add MAC address to headers if provided
        if mac_address:
            self.session.headers['X-MAC-Address'] = mac_address
            self.session.headers['MAC-Address'] = mac_address
    
    def get_auth_config(self) -> Dict[str, Any]:
        """
        Get authentication and configuration data
        Returns app settings, languages, trial info, playlist URLs, etc.
        """
        try:
            url = f"{self.BASE_URL}/auth"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                data = response.json()
                # Check if data contains base64 encoded string
                if isinstance(data, dict) and "data" in data and isinstance(data["data"], str):
                    import base64
                    try:
                        # Try to decode base64
                        decoded = base64.b64decode(data["data"]).decode('utf-8')
                        decoded_json = json.loads(decoded)
                        # Replace the base64 string with decoded JSON
                        # Return the decoded JSON directly (it contains all the config)
                        return decoded_json
                    except Exception as e:
                        # If decoding fails, return original with error info
                        return {
                            **data,
                            "decode_error": str(e),
                            "note": "Response contains base64 data that could not be decoded"
                        }
                return data
            except json.JSONDecodeError:
                # If not JSON, return as text
                return {
                    "success": False,
                    "error": "Response is not valid JSON",
                    "raw_response": response.text[:500]
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_main_movies(self, page: int = 1, limit: int = 20, content_type: str = "all", username: str = None, password: str = None, mac_address: str = None) -> Dict[str, Any]:
        """
        Get main movies/series
        Note: This endpoint currently returns HTML, may need further investigation
        
        Args:
            page: Page number
            limit: Number of results per page
            content_type: 'movies', 'series', or 'all'
        """
        try:
            url = f"{self.BASE_URL}/main_movies.php"
            
            # Use provided credentials or instance credentials
            auth_username = username or self.username
            auth_password = password or self.password
            auth_mac = mac_address or self.mac_address
            
            # Try GET first
            params = {
                'page': page,
                'limit': limit,
            }
            
            # Add credentials to params if available
            if auth_username:
                params['username'] = auth_username
            if auth_password:
                params['password'] = auth_password
            if auth_mac:
                params['mac'] = auth_mac
                params['mac_address'] = auth_mac
                params['device_mac'] = auth_mac
            
            if content_type != "all":
                params['type'] = content_type
            
            # Also add MAC to headers
            headers = {}
            if auth_mac:
                headers['X-MAC-Address'] = auth_mac
                headers['MAC-Address'] = auth_mac
                headers['Device-MAC'] = auth_mac
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Check if response is JSON
            content_type_header = response.headers.get('Content-Type', '')
            if 'application/json' in content_type_header:
                return response.json()
            
            # If HTML, try to extract data from it
            html_content = response.text
            
            # Check if HTML references movies.php - try that endpoint with AJAX headers
            if 'movies.php' in html_content:
                try:
                    movies_url = f"{self.BASE_URL}/movies.php"
                    # Add AJAX headers (X-Requested-With)
                    ajax_headers = {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, text/javascript, */*; q=0.01'
                    }
                    movies_response = self.session.get(movies_url, params=params, headers=ajax_headers, timeout=10)
                    movies_response.raise_for_status()
                    
                    # Check if movies.php returns JSON
                    if 'application/json' in movies_response.headers.get('Content-Type', ''):
                        return movies_response.json()
                    
                    # Try to parse as JSON anyway
                    try:
                        return movies_response.json()
                    except:
                        pass
                except:
                    pass
                
                    # Try POST with AJAX headers and MAC
                try:
                    post_data = params.copy()
                    ajax_headers = headers.copy()
                    ajax_headers.update({
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    })
                    movies_response = self.session.post(movies_url, data=post_data, headers=ajax_headers, timeout=10)
                    movies_response.raise_for_status()
                    
                    if 'application/json' in movies_response.headers.get('Content-Type', ''):
                        return movies_response.json()
                    
                    try:
                        return movies_response.json()
                    except:
                        pass
                except:
                    pass
            
            # Try POST with credentials and MAC
            if auth_username and auth_password:
                try:
                    post_data = {
                        'username': auth_username,
                        'password': auth_password,
                        'page': page,
                        'limit': limit,
                    }
                    if auth_mac:
                        post_data['mac'] = auth_mac
                        post_data['mac_address'] = auth_mac
                        post_data['device_mac'] = auth_mac
                    if content_type != "all":
                        post_data['type'] = content_type
                    
                    post_headers = headers.copy()
                    post_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    
                    post_response = self.session.post(url, data=post_data, headers=post_headers, timeout=10)
                    post_response.raise_for_status()
                    
                    if 'application/json' in post_response.headers.get('Content-Type', ''):
                        return post_response.json()
                    
                    try:
                        return post_response.json()
                    except:
                        pass
                except:
                    pass
            
            # Try with just MAC address (no username/password)
            if auth_mac and not (auth_username and auth_password):
                try:
                    mac_params = {
                        'mac': auth_mac,
                        'mac_address': auth_mac,
                        'device_mac': auth_mac,
                        'page': page,
                        'limit': limit,
                    }
                    if content_type != "all":
                        mac_params['type'] = content_type
                    
                    mac_response = self.session.get(url, params=mac_params, headers=headers, timeout=10)
                    mac_response.raise_for_status()
                    
                    if 'application/json' in mac_response.headers.get('Content-Type', ''):
                        return mac_response.json()
                    
                    try:
                        return mac_response.json()
                    except:
                        pass
                except:
                    pass
            
            # Try to find JSON in script tags
            soup = BeautifulSoup(html_content, 'html.parser')
            scripts = soup.find_all('script')
            
            json_data = None
            for script in scripts:
                if script.string:
                    # Look for JSON objects in script
                    json_matches = re.findall(r'\{[^{}]*\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict) and len(data) > 2:
                                json_data = data
                                break
                        except:
                            continue
                    if json_data:
                        break
            
            # Try POST request if GET didn't work
            if not json_data:
                try:
                    post_response = self.session.post(url, json=params, timeout=10)
                    post_response.raise_for_status()
                    
                    if 'application/json' in post_response.headers.get('Content-Type', ''):
                        return post_response.json()
                    
                    # Try to parse POST response
                    try:
                        return post_response.json()
                    except:
                        pass
                except:
                    pass
            
            # Return HTML analysis
            return {
                "success": True,
                "content_type": "html",
                "html_length": len(html_content),
                "preview": html_content[:500],
                "extracted_json": json_data,
                "note": "Endpoint returns HTML that references movies.php. Tried movies.php endpoint but may need authentication or different parameters."
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_playlists(self) -> Dict[str, Any]:
        """
        Get playlists information
        """
        try:
            url = f"{self.BASE_URL}/playlists"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Response is not valid JSON",
                    "raw_response": response.text[:500]
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_update(self) -> Dict[str, Any]:
        """
        Check for app updates
        """
        try:
            url = f"{self.BASE_URL}/update"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Update endpoint may return empty or minimal response
            if response.text.strip():
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "message": "Update check completed",
                        "raw_response": response.text[:500]
                    }
            else:
                return {
                    "success": True,
                    "message": "No update available or endpoint returns empty"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_playlist_urls(self) -> List[Dict[str, Any]]:
        """
        Extract playlist URLs from auth config
        Returns list of playlist configurations
        """
        config = self.get_auth_config()
        
        if not config.get("success", True) and "error" in config:
            return []
        
        # Extract URLs from config
        urls = config.get("urls", [])
        return urls if isinstance(urls, list) else []
    
    def try_alternative_movies_endpoint(self) -> Dict[str, Any]:
        """
        Try alternative approaches to get movies data
        """
        results = {}
        
        # Try different endpoints
        alternative_endpoints = [
            "movies.php",
            "get_movies.php",
            "api/movies",
            "api/get_movies"
        ]
        
        for endpoint in alternative_endpoints:
            try:
                url = f"{self.BASE_URL}/{endpoint}"
                response = self.session.get(url, timeout=5)
                results[endpoint] = {
                    "status": response.status_code,
                    "content_type": response.headers.get('Content-Type', ''),
                    "length": len(response.text),
                    "preview": response.text[:200]
                }
            except Exception as e:
                results[endpoint] = {"error": str(e)}
        
        return results
