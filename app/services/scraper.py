"""
Web scraper service for Arabic translation sites
"""
import re
import time
import gzip
import requests
import json
from bs4 import BeautifulSoup
from cachetools import TTLCache
from typing import List, Dict, Optional
from requests.exceptions import RequestException, ConnectionError, Timeout, TooManyRedirects

# Try to import Playwright (optional - only if needed)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Cache for 1 hour (3600 seconds)
cache = TTLCache(maxsize=100, ttl=3600)


class ScraperService:
    """Service for scraping Arabic translation sites"""
    
    def __init__(self):
        # Primary site: TopCinema
        self.base_urls = {
            'topcinema': 'https://topcinema.media',
            # Alternative sites (if needed)
            'faselhd': 'https://faselhd.me',
            'faselhd_alt1': 'https://faselhd.com',
            'cimaleek': 'https://cimaleek.ws',
            'cimaleek_pro': 'https://pro.cimaleek.to',
            'cimaleek_art': 'https://cimalek.art',
            'mycima': 'https://mycima.host',
            # Add more sites here as needed
        }
        # Use TopCinema as primary domain
        self.primary_domain = 'topcinema'
        
        # Playwright browser instance (lazy loaded)
        self._playwright = None
        self._browser = None
        
        # More complete browser headers to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.google.com/',
        }
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.timeout = 30  # Increased timeout for slow sites
        # Create a session for connection pooling and cookie handling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_page(self, url: str, retry_count: int = 0) -> str:
        """Fetch HTML content from a URL with caching and retry logic"""
        try:
            cache_key = f"page_{url}"
            if cache_key in cache:
                return cache[cache_key]
            
            # Use session for better connection handling
            response = self.session.get(
                url, 
                timeout=self.timeout, 
                allow_redirects=True,
                verify=True  # SSL verification
            )
            response.raise_for_status()
            
            # Check if response is HTML
            content_type = response.headers.get('Content-Type', '').lower()
            if 'html' not in content_type and 'text' not in content_type:
                raise Exception(f"Unexpected content type: {content_type}")
            
            # Handle decompression - check if content is compressed
            content_encoding = response.headers.get('Content-Encoding', '').lower()
            content_bytes = response.content
            
            # Check for gzip magic number (1f 8b)
            is_gzipped = content_bytes[:2] == b'\x1f\x8b' if len(content_bytes) >= 2 else False
            
            if 'gzip' in content_encoding or is_gzipped:
                # Decompress gzip
                html = gzip.decompress(content_bytes).decode('utf-8', errors='ignore')
            elif 'deflate' in content_encoding:
                # Decompress deflate
                import zlib
                html = zlib.decompress(content_bytes).decode('utf-8', errors='ignore')
            elif 'br' in content_encoding:
                # Brotli compression
                try:
                    import brotli
                    html = brotli.decompress(content_bytes).decode('utf-8', errors='ignore')
                except (ImportError, Exception):
                    # Fallback: try response.text (requests might handle it)
                    html = response.text
            else:
                # Try response.text first (requests auto-decompresses)
                try:
                    html = response.text
                    # Verify it's actually text (not binary)
                    if len(html) > 0:
                        first_char = html[0]
                        # If first char is not printable ASCII and not common whitespace, might be binary
                        if ord(first_char) > 127 or (ord(first_char) < 32 and first_char not in ['\n', '\r', '\t', ' ']):
                            # Might be binary, try manual decode
                            html = content_bytes.decode('utf-8', errors='ignore')
                except:
                    # Fallback to manual decode
                    html = content_bytes.decode('utf-8', errors='ignore')
            
            cache[cache_key] = html
            return html
            
        except ConnectionError as e:
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg or "NameResolutionError" in error_msg:
                raise Exception(
                    f"DNS resolution failed for {url}. "
                    f"The website may be down, blocked, or the URL is incorrect. "
                    f"Please check if the site is accessible in your browser."
                )
            elif retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self.fetch_page(url, retry_count + 1)
            else:
                raise Exception(f"Connection error after {self.max_retries} retries: {error_msg}")
                
        except Timeout as e:
            if retry_count < self.max_retries:
                # Exponential backoff
                delay = self.retry_delay * (retry_count + 1)
                time.sleep(delay)
                return self.fetch_page(url, retry_count + 1)
            else:
                raise Exception(
                    f"Request timeout after {self.max_retries} retries. "
                    f"The site may be slow or blocking requests. "
                    f"Try checking the site manually or use an alternative domain."
                )
                
        except TooManyRedirects as e:
            error_msg = f"Too many redirects for {url}: {str(e)}"
            try:
                error_msg.encode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_msg = "Too many redirects for the requested URL"
            raise Exception(error_msg)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code} for {url}: {str(e)}"
            # Handle encoding errors
            try:
                error_msg.encode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_msg = f"HTTP error {e.response.status_code} for the requested URL"
            raise Exception(error_msg)
            
        except RequestException as e:
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self.fetch_page(url, retry_count + 1)
            else:
                raise Exception(f"Request failed after {self.max_retries} retries: {str(e)}")
                
        except Exception as e:
            error_msg = f"Failed to fetch page {url}: {str(e)}"
            try:
                error_msg.encode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_msg = "Failed to fetch the requested page"
            raise Exception(error_msg)
    
    def check_site_availability(self, site_key: str = 'cimaleek', quick_check: bool = False) -> Dict:
        """Check if a site is accessible"""
        if site_key not in self.base_urls:
            return {
                'available': False,
                'error': f'Site key "{site_key}" not found'
            }
        
        url = self.base_urls[site_key]
        timeout = 5 if quick_check else self.timeout  # Shorter timeout for quick checks
        try:
            response = self.session.get(url, timeout=timeout)
            return {
                'available': True,
                'status_code': response.status_code,
                'url': url,
                'response_time': response.elapsed.total_seconds()
            }
        except Timeout as e:
            return {
                'available': False,
                'error': f'Request timeout - site may be slow or blocking requests',
                'url': url,
                'suggestion': 'Try increasing timeout or check if site is accessible in browser'
            }
        except ConnectionError as e:
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg or "NameResolutionError" in error_msg:
                return {
                    'available': False,
                    'error': 'DNS resolution failed - site may be down or blocked',
                    'url': url,
                    'suggestion': 'Try alternative domains or check DNS settings'
                }
            return {
                'available': False,
                'error': str(e),
                'url': url
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'url': url
            }
    
    def find_working_domain(self) -> Optional[str]:
        """Try to find a working domain from available alternatives"""
        for site_key, url in self.base_urls.items():
            try:
                result = self.check_site_availability(site_key)
                if result.get('available'):
                    return url
            except:
                continue
        return None
    
    def get_base_url(self, check_availability: bool = False) -> str:
        """Get the base URL, trying alternatives if primary fails
        
        Args:
            check_availability: If True, check if site is accessible (may be slow)
        """
        primary_url = self.base_urls.get(self.primary_domain)
        
        # Only check availability if explicitly requested (to avoid blocking)
        if check_availability and primary_url:
            # Quick check with shorter timeout
            try:
                result = self.check_site_availability(self.primary_domain, quick_check=True)
                if result.get('available'):
                    return primary_url
            except:
                pass  # If check fails, just use primary
        
        # Return primary without checking (fast, non-blocking)
        return primary_url or list(self.base_urls.values())[0]
    
    def search_series(self, query: str, filter_type: str = "all") -> List[Dict]:
        """Search for series/movies on TopCinema
        
        Args:
            query: Search query
            filter_type: Filter by type - "movies", "series", or "all" (default: "all")
        """
        try:
            base_url = self.get_base_url()
            results = []
            seen_links = set()
            
            # Try AJAX search endpoint first (more accurate)
            ajax_url = f"{base_url}/wp-content/themes/movies2023/Ajaxat/Searching.php"
            ajax_headers = {
                'User-Agent': self.headers['User-Agent'],
                'Accept': '*/*',
                'Accept-Language': self.headers['Accept-Language'],
                'Referer': f'{base_url}/',
                'X-Requested-With': 'XMLHttpRequest',
            }
            
            # Prepare AJAX parameters
            # The site uses "search" parameter, not "s"
            ajax_params = {"search": query}
            if filter_type == "movies":
                ajax_params["type"] = "movie"
            elif filter_type == "series":
                ajax_params["type"] = "series"
            
            # Try AJAX endpoint first
            try:
                ajax_response = self.session.post(
                    ajax_url,
                    data=ajax_params,
                    headers=ajax_headers,
                    timeout=self.timeout
                )
                ajax_response.raise_for_status()
                
                # Parse AJAX response
                ajax_html = ajax_response.text
                ajax_soup = BeautifulSoup(ajax_html, 'lxml')
                
                # Extract results from AJAX response
                # AJAX returns HTML with structure: <ul class="Posts--List"> <div class="Small--Box"> <a>...
                ajax_links = ajax_soup.find_all('a', href=True, class_=lambda x: x and 'recent--block' in str(x))
                
                # Also try finding links in Small--Box containers
                if not ajax_links:
                    boxes = ajax_soup.find_all('div', class_='Small--Box')
                    for box in boxes:
                        link_elem = box.find('a', href=True)
                        if link_elem:
                            ajax_links.append(link_elem)
                
                if ajax_links:
                    # Process AJAX results
                    for link_elem in ajax_links:
                        link = link_elem.get('href', '')
                        if not link:
                            continue
                        
                        # Make link absolute
                        if not link.startswith('http'):
                            if link.startswith('/'):
                                link = f"{base_url}{link}"
                            else:
                                link = f"{base_url}/{link}"
                        
                        # Skip if already seen
                        if link in seen_links:
                            continue
                        
                        # Skip navigation links
                        skip_patterns = ['/category/', '/tag/', '/page/', '#', 'javascript:', 'mailto:', '/search', '/?s=']
                        if any(pattern in link for pattern in skip_patterns):
                            continue
                        
                        # Get title - prefer title attribute, fallback to text
                        title = link_elem.get('title', '').strip()
                        if not title:
                            title = link_elem.get_text(strip=True)
                        
                        # Clean title - remove extra info
                        if title:
                            import re
                            # Remove quality/resolution info
                            title = re.sub(r'\d+p\s*(WEB-DL|BluRay|HDTV)?', '', title, flags=re.IGNORECASE)
                            title = re.sub(r'\d+\.\d+', '', title)  # Remove ratings like 8.3
                            title = re.sub(r'\s+', ' ', title).strip()
                        
                        if not title or len(title) < 3:
                            continue
                        
                        # Filter by query - stricter matching to ensure relevance
                        query_lower = query.lower().strip()
                        title_lower = title.lower()
                        link_lower = link.lower()
                        decoded_link_lower = requests.utils.unquote(link).lower()
                        
                        # Extract meaningful words from query (remove common stop words)
                        stop_words = {'the', 'of', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can'}
                        query_words = [w for w in query_lower.split() if len(w) > 2 and w not in stop_words]
                        
                        # If no meaningful words after filtering, use original query
                        if not query_words:
                            query_words = [w for w in query_lower.split() if len(w) > 1]
                        
                        # Stricter matching: require at least 50% of query words to match
                        # OR the main query term must be present
                        matches_query = False
                        if query_words:
                            # Count how many query words match
                            matching_words = sum(
                                1 for word in query_words
                                if (word in title_lower or 
                                    word in link_lower or 
                                    word in decoded_link_lower)
                            )
                            
                            # Require at least 50% of words to match, or at least 1 word for short queries
                            min_matches = max(1, len(query_words) // 2) if len(query_words) > 1 else 1
                            
                            # Also check if the full query (or significant portion) is in title/URL
                            query_portion = ' '.join(query_words[:2])  # First 2 words
                            full_query_match = (
                                query_lower in title_lower or 
                                query_lower in link_lower or 
                                query_lower in decoded_link_lower or
                                query_portion in title_lower or
                                query_portion in link_lower
                            )
                            
                            matches_query = (matching_words >= min_matches) or full_query_match
                        else:
                            # For very short queries, check if query is in title or URL
                            matches_query = (
                                query_lower in title_lower or 
                                query_lower in link_lower or 
                                query_lower in decoded_link_lower
                            )
                        
                        if not matches_query:
                            continue
                        
                        # Check if this is an episode or season link (should be series page)
                        decoded_link = requests.utils.unquote(link)
                        is_episode = (
                            '/الحلقة-' in link or
                            '/الحلقة-' in decoded_link or
                            'الحلقة-' in decoded_link or
                            '/episode-' in link.lower() or
                            '/حلقة-' in link or
                            'حلقة-' in decoded_link
                        )
                        
                        # Check if it's a season link (الموسم-الاول, الموسم-الثاني, etc.)
                        # These should be converted to series links
                        is_season_link = (
                            '/الموسم-' in decoded_link or
                            'الموسم-' in decoded_link or
                            '/season-' in link.lower()
                        )
                        
                        # For series search, convert season/episode links to series page
                        if filter_type == "series" and (is_episode or is_season_link):
                            import re
                            # Extract series base URL
                            # Pattern: /series/مسلسل-{name}-الموسم-{season} or مسلسل-{name}-الموسم-{season}
                            if '/series/' in link:
                                # Extract series name from /series/مسلسل-{name}-الموسم-{season}
                                series_match = re.search(r'(/series/[^/]+)', link)
                                if series_match:
                                    # Get the series base without season
                                    series_path = series_match.group(1)
                                    # Remove season part if present
                                    series_path = re.sub(r'-الموسم-[^-/]+.*', '', series_path)
                                    link = f"{base_url}{series_path}/"
                                    decoded_link = requests.utils.unquote(link)
                                else:
                                    continue
                            elif 'الموسم-' in decoded_link:
                                # Pattern: مسلسل-{name}-الموسم-{season}
                                # Remove everything from الموسم- onwards
                                series_match = re.search(r'(.+?)-الموسم-', decoded_link)
                                if series_match:
                                    series_base = series_match.group(1)
                                    # Check if it should be /series/ or just the name
                                    if '/series/' in link:
                                        link = f"{base_url}/series/{requests.utils.quote(series_base)}/"
                                    else:
                                        link = f"{base_url}/{requests.utils.quote(series_base)}/"
                                    decoded_link = requests.utils.unquote(link)
                                else:
                                    continue
                            else:
                                continue
                        
                        # Filter out episodes for series search
                        if filter_type == "series" and is_episode and not is_season_link:
                            continue
                        
                        # Get image - look in parent container for img with data-src (lazy loading)
                        image = None
                        parent = link_elem.parent
                        if parent:
                            # Look for img in Poster div or nearby
                            poster = parent.find('div', class_='Poster')
                            if poster:
                                img_elem = poster.find('img')
                            else:
                                img_elem = parent.find('img')
                            
                            if img_elem:
                                # Prefer data-src (lazy loaded), then src
                                image = img_elem.get('data-src') or img_elem.get('src') or img_elem.get('data-lazy-src')
                        
                        image_url = None
                        if image:
                            if image.startswith('http'):
                                image_url = image
                            elif image.startswith('/'):
                                image_url = f"{base_url}{image}"
                            else:
                                image_url = f"{base_url}/{image}"
                        
                        seen_links.add(link)
                        results.append({
                            'id': self.extract_id_from_url(link),
                            'title': title,
                            'link': link,
                            'image': image_url,
                            'source': 'topcinema'
                        })
                    
                    # If AJAX returned results, return them
                    if results:
                        return results
            except Exception as e:
                print(f'AJAX search failed, falling back to HTML search: {str(e)}')
            
            # Fallback to regular HTML search
            search_urls = []
            if filter_type == "movies":
                search_urls = [
                    f"{base_url}/?s={requests.utils.quote(query)}&post_type=movie",
                    f"{base_url}/?s={requests.utils.quote(query)}&type=movie",
                ]
            elif filter_type == "series":
                search_urls = [
                    f"{base_url}/?s={requests.utils.quote(query)}&post_type=series",
                    f"{base_url}/?s={requests.utils.quote(query)}&type=series",
                ]
            else:
                search_urls = [
                    f"{base_url}/?s={requests.utils.quote(query)}",
                ]
            
            # Add fallback URLs
            search_urls.extend([
                f"{base_url}/search/{requests.utils.quote(query)}",
                f"{base_url}/?s={requests.utils.quote(query)}",
            ])
            
            for search_url in search_urls:
                try:
                    html = self.fetch_page(search_url)
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Use same approach as get_popular_series - process all links directly
                    all_links = soup.find_all('a', href=True)
                    
                    # Process links directly
                    for link_elem in all_links:
                        link = link_elem.get('href', '')
                        if not link or link in seen_links:
                            continue
                        
                        # Skip navigation links
                        skip_patterns = ['/category/', '/tag/', '/page/', '#', 'javascript:', 'mailto:', '/search', '/?s=', '/recent/', '/movies/', '/series/']
                        if any(pattern in link for pattern in skip_patterns):
                            continue
                        
                        # Only accept content links
                        if base_url not in link and not link.startswith('/'):
                            continue
                        
                        # Skip homepage and common pages
                        if link == base_url or link == f"{base_url}/":
                            continue
                        
                        # Make link absolute
                        if not link.startswith('http'):
                            if link.startswith('/'):
                                link = f"{base_url}{link}"
                            else:
                                link = f"{base_url}/{link}"
                        
                        # Get title from link text
                        title = link_elem.get_text(strip=True)
                        
                        # Skip if title is too short or is navigation
                        nav_words = ['الكل', 'افلام', 'مسلسلات', 'بحث', 'القائمة', 'الصفحة الرئيسية', 'topcinema', 'top cinema', 'المضاف حديثا', 'الاعلي تقييما']
                        if not title or len(title) < 3 or any(nav.lower() in title.lower() for nav in nav_words):
                            continue
                        
                        # Clean title
                        title = ' '.join(title.split())
                        
                        # Filter by query - only include results where query words appear
                        query_lower = query.lower().strip()
                        title_lower = title.lower()
                        link_lower = link.lower()
                        
                        # Decode URL to check for query words
                        try:
                            import urllib.parse
                            decoded_link = urllib.parse.unquote(link_lower)
                        except:
                            decoded_link = link_lower
                        
                        # Extract meaningful words from query
                        query_words = [w for w in query_lower.split() if len(w) > 2 and w not in ['the', 'of', 'a', 'an', 'in', 'on', 'at', 'to', 'for']]
                        
                        # Check if any query word appears in title or URL
                        matches_query = False
                        if query_words:
                            matches_query = any(word in title_lower or word in link_lower or word in decoded_link for word in query_words)
                        else:
                            # For short queries, check if query is in title or URL
                            matches_query = query_lower in title_lower or query_lower in link_lower or query_lower in decoded_link
                        
                        if not matches_query:
                            continue
                        
                        # Check if this is an episode link
                        decoded_link_check = requests.utils.unquote(link)
                        is_episode = (
                            '/الحلقة-' in link or
                            '/الحلقة-' in decoded_link_check or
                            'الحلقة-' in decoded_link_check or
                            '/episode-' in link.lower() or
                            '/حلقة-' in link or
                            '/حلقة-' in decoded_link_check or
                            'حلقة-' in decoded_link_check or
                            '/watch/' in link or
                            '/download/' in link
                        )
                        
                        # For series search, filter out episode links and extract series URLs
                        if filter_type == "series":
                            if is_episode:
                                # Try to extract series page URL from episode link
                                # Pattern: مسلسل-{series-name}-الموسم-{season}-الحلقة-{episode}
                                # Series page: مسلسل-{series-name}-الموسم-{season} or /series/{series-name}
                                import re
                                
                                # Check if there's a /series/ version
                                if '/series/' in link:
                                    # Already has series path, but might be episode
                                    # Extract series base
                                    series_match = re.search(r'(/series/[^/]+)', link)
                                    if series_match:
                                        series_base = series_match.group(1)
                                        link = f"{base_url}{series_base}/"
                                        decoded_link_check = requests.utils.unquote(link)
                                        is_episode = False
                                    else:
                                        continue  # Skip this episode
                                elif 'الحلقة-' in decoded_link_check:
                                    # Extract base series URL by removing episode part
                                    # Pattern: مسلسل-{name}-الموسم-{season}-الحلقة-{ep}
                                    episode_match = re.search(r'(.+?)-الحلقة-\d+', decoded_link_check)
                                    if episode_match:
                                        series_base = episode_match.group(1)
                                        # Reconstruct series page URL
                                        link = f"{base_url}/{requests.utils.quote(series_base)}/"
                                        decoded_link_check = requests.utils.unquote(link)
                                        is_episode = False
                                    else:
                                        continue  # Skip if we can't extract
                                else:
                                    continue  # Skip episode links we can't convert
                        
                        # Filter by type (movies, series, or all)
                        if filter_type != "all":
                            link_lower_check = link.lower()
                            
                            is_movie = (
                                '/فيلم-' in link or 
                                '/فيلم-' in decoded_link_check or 
                                'فيلم' in decoded_link_check or
                                ('/movie' in link_lower_check and '/movies/' not in link_lower_check)
                            )
                            
                            is_series = (
                                '/مسلسل-' in link or 
                                '/مسلسل-' in decoded_link_check or 
                                'مسلسل' in decoded_link_check or
                                '/series' in link_lower_check
                            )
                            
                            # Apply filter
                            if filter_type == "movies" and not is_movie:
                                continue
                            elif filter_type == "series" and not is_series:
                                continue
                        else:
                            # For "all", skip episode links to avoid clutter
                            if is_episode:
                                continue
                        
                        # Get image from nearby elements
                        image = None
                        parent = link_elem.parent
                        if parent:
                            img_elem = parent.find('img')
                            if img_elem:
                                image = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src') or img_elem.get('data-original')
                        
                        if title and len(title) > 2:
                            # For series search, clean up title if it contains episode info
                            if filter_type == "series" and is_episode == False:
                                # Remove episode-specific text from title
                                import re
                                # Remove patterns like "حلقة5", "الحلقة 5", "Episode 5", etc.
                                title = re.sub(r'حلقة\s*\d+', '', title, flags=re.IGNORECASE)
                                title = re.sub(r'الحلقة\s*\d+', '', title, flags=re.IGNORECASE)
                                title = re.sub(r'episode\s*\d+', '', title, flags=re.IGNORECASE)
                                title = re.sub(r'\s+', ' ', title).strip()
                            
                            # Make image absolute
                            image_url = None
                            if image:
                                if image.startswith('http'):
                                    image_url = image
                                elif image.startswith('/'):
                                    image_url = f"{base_url}{image}"
                                else:
                                    image_url = f"{base_url}/{image}"
                            
                            # For series search, use normalized link for deduplication
                            # (multiple episodes should map to one series entry)
                            dedup_key = link
                            if filter_type == "series":
                                # Use the series URL as dedup key
                                dedup_key = link
                            
                            if dedup_key not in seen_links:
                                seen_links.add(dedup_key)
                                results.append({
                                    'id': self.extract_id_from_url(link),
                                    'title': title,
                                    'link': link,
                                    'image': image_url,
                                    'source': 'topcinema'
                                })
                    
                    # If we found results, break
                    if results:
                        break
                        
                except Exception as e:
                    try:
                        print(f"Error with search URL {search_url}: {e}")
                    except:
                        pass  # Skip printing if encoding fails
                    continue
            
            return results
        except Exception as e:
            try:
                print(f'Error searching series: {str(e)}')
            except:
                pass  # Skip printing if encoding fails
            raise
    
    def get_series_details(self, series_url: str) -> Dict:
        """Get series details, seasons, and episodes for FaselHD"""
        try:
            base_url = self.get_base_url()
            # Ensure URL uses correct domain
            if not series_url.startswith('http'):
                if series_url.startswith('/'):
                    series_url = f"{base_url}{series_url}"
                else:
                    series_url = f"{base_url}/{series_url}"
            
            html = self.fetch_page(series_url)
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract series info
            title_elem = soup.select_one('h1, .title, .series-title, [class*="title"], article h1')
            desc_elem = soup.select_one('.description, .content, .plot, [class*="description"], article .content')
            image_elem = soup.select_one('.poster img, .cover img, .series-poster img, img[class*="poster"], article img')
            
            series_info = {
                'title': title_elem.get_text(strip=True) if title_elem else '',
                'description': desc_elem.get_text(strip=True) if desc_elem else '',
                'image': None,
                'seasons': []
            }
            
            # Get image
            if image_elem:
                image = image_elem.get('src') or image_elem.get('data-src') or image_elem.get('data-lazy-src')
                if image:
                    if not image.startswith('http'):
                        if image.startswith('/'):
                            series_info['image'] = f"{base_url}{image}"
                        else:
                            series_info['image'] = f"{base_url}/{image}"
                    else:
                        series_info['image'] = image
            
            # FaselHD: Look for episode/season links
            # Episodes might be in links or embedded in the page
            all_links = soup.find_all('a', href=True)
            seasons_dict = {}
            
            for link_elem in all_links:
                link = link_elem.get('href', '')
                text = link_elem.get_text(strip=True)
                
                # Look for episode indicators
                if any(keyword in text.lower() for keyword in ['حلقة', 'episode', 'موسم', 'season']):
                    # Make link absolute
                    if not link.startswith('http'):
                        if link.startswith('/'):
                            link = f"{base_url}{link}"
                        else:
                            link = f"{base_url}/{link}"
                    
                    # Extract episode number
                    ep_match = re.search(r'(\d+)', text)
                    if ep_match:
                        ep_num = int(ep_match.group(1))
                        # Default to season 1 if not specified
                        season_num = 1
                        
                        # Try to extract season number
                        season_match = re.search(r'موسم\s*(\d+)', text)
                        if season_match:
                            season_num = int(season_match.group(1))
                        
                        if season_num not in seasons_dict:
                            seasons_dict[season_num] = {
                                'season': season_num,
                                'episodes': []
                            }
                        
                        seasons_dict[season_num]['episodes'].append({
                            'number': ep_num,
                            'title': text,
                            'link': link,
                            'url': link,  # Add url field for compatibility
                            'id': self.extract_id_from_url(link)
                        })
            
            # If no episodes found, create a single "episode" for the movie/series itself
            if not seasons_dict:
                seasons_dict[1] = {
                    'season': 1,
                    'episodes': [{
                        'number': 1,
                        'title': 'Watch',
                        'link': series_url,
                        'url': series_url,  # Add url field for compatibility
                        'id': self.extract_id_from_url(series_url)
                    }]
                }
            
            # Sort episodes within each season and add season link
            for season_num in seasons_dict:
                seasons_dict[season_num]['episodes'].sort(key=lambda x: x['number'])
                # Add season link - use first episode link or construct from series URL
                if seasons_dict[season_num]['episodes']:
                    # Use first episode link as season link
                    seasons_dict[season_num]['link'] = seasons_dict[season_num]['episodes'][0]['link']
                else:
                    # If no episodes, use series URL
                    seasons_dict[season_num]['link'] = series_url
            
            # Convert to list and sort by season number
            series_info['seasons'] = [seasons_dict[season] for season in sorted(seasons_dict.keys())]
            
            return series_info
        except Exception as e:
            error_msg = str(e)
            # Handle encoding errors in error messages
            try:
                # Try to encode to check if it's valid UTF-8
                error_msg.encode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                # If encoding fails, use a safe message
                error_msg = "Error fetching series details from the website"
            # Use print with explicit encoding or skip printing
            try:
                print(f'Error getting series details: {error_msg}')
            except:
                pass  # Skip printing if encoding fails
            raise Exception(error_msg)
    
    def get_season_episodes(self, season_url: str) -> List[Dict]:
        """Get all episodes from a season link (usually a /list/ page)
        
        This method extracts all episode links from a season page,
        which is typically a /list/ page that shows all episodes for a season.
        """
        try:
            base_url = self.get_base_url()
            # Ensure URL uses correct domain
            if not season_url.startswith('http'):
                if season_url.startswith('/'):
                    season_url = f"{base_url}{season_url}"
                else:
                    season_url = f"{base_url}/{season_url}"
            
            html = self.fetch_page(season_url)
            soup = BeautifulSoup(html, 'lxml')
            
            episodes = []
            
            # Look for episode links - they typically have class 'recent--block' or similar
            episode_links = soup.find_all('a', href=True, class_=lambda x: x and ('recent--block' in str(x) or 'episode' in str(x).lower()))
            
            # If no specific class found, look for links that contain episode indicators
            if not episode_links:
                all_links = soup.find_all('a', href=True)
                for link_elem in all_links:
                    link = link_elem.get('href', '')
                    text = link_elem.get_text(strip=True)
                    
                    # Check if it's an episode link
                    if any(keyword in text.lower() for keyword in ['حلقة', 'episode']) or \
                       any(keyword in link.lower() for keyword in ['الحلقة', 'episode']):
                        # Make link absolute
                        if not link.startswith('http'):
                            if link.startswith('/'):
                                link = f"{base_url}{link}"
                            else:
                                link = f"{base_url}/{link}"
                        
                        # Extract episode number
                        ep_match = re.search(r'(\d+)', text)
                        ep_num = int(ep_match.group(1)) if ep_match else 0
                        
                        episodes.append({
                            'number': ep_num,
                            'title': text,
                            'link': link,
                            'url': link,
                            'id': self.extract_id_from_url(link)
                        })
            else:
                # Process links with episode class
                for link_elem in episode_links:
                    link = link_elem.get('href', '')
                    text = link_elem.get_text(strip=True)
                    
                    # Make link absolute
                    if not link.startswith('http'):
                        if link.startswith('/'):
                            link = f"{base_url}{link}"
                        else:
                            link = f"{base_url}/{link}"
                    
                    # Extract episode number from text or link
                    ep_match = re.search(r'(\d+)', text)
                    if not ep_match:
                        ep_match = re.search(r'الحلقة[-\s]*(\d+)', link)
                    ep_num = int(ep_match.group(1)) if ep_match else 0
                    
                    episodes.append({
                        'number': ep_num,
                        'title': text,
                        'link': link,
                        'url': link,
                        'id': self.extract_id_from_url(link)
                    })
            
            # Sort by episode number
            episodes.sort(key=lambda x: x['number'])
            
            return episodes
        except Exception as e:
            error_msg = str(e)
            try:
                error_msg.encode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_msg = "Error fetching season episodes from the website"
            try:
                print(f'Error getting season episodes: {error_msg}')
            except:
                pass
            raise Exception(error_msg)
    
    def get_episode_video_links(self, episode_url: str) -> Optional[List[Dict]]:
        """Get video links from episode page for TopCinema"""
        try:
            base_url = self.get_base_url()
            # Ensure URL uses correct domain and is properly formatted
            if not episode_url.startswith('http'):
                if episode_url.startswith('/'):
                    episode_url = f"{base_url}{episode_url}"
                else:
                    episode_url = f"{base_url}/{episode_url}"
            
            # Ensure URL ends with /
            if not episode_url.endswith('/'):
                episode_url += '/'
            
            # The URL should already be properly encoded, but ensure it's in the right format
            # requests library will handle encoding automatically
            html = self.fetch_page(episode_url)
            soup = BeautifulSoup(html, 'lxml')
            
            video_links = []
            
            # TopCinema has a separate /watch/ page for videos
            # Look for watch link
            watch_link = None
            watch_anchor = soup.find('a', class_='watch', href=True)
            if watch_anchor:
                watch_href = watch_anchor.get('href', '')
                if watch_href:
                    if watch_href.startswith('http'):
                        watch_link = watch_href
                    elif watch_href.startswith('/'):
                        watch_link = f"{base_url}{watch_href}"
                    else:
                        watch_link = f"{base_url}/{watch_href}"
            
            # Also check for download button (might have video links)
            download_link = None
            download_anchor = soup.find('a', class_='downloadFullSeason', href=True)
            if download_anchor:
                download_href = download_anchor.get('href', '')
                if download_href:
                    if download_href.startswith('http'):
                        download_link = download_href
                    elif download_href.startswith('/'):
                        download_link = f"{base_url}{download_href}"
                    else:
                        download_link = f"{base_url}/{download_href}"
            
            # If we found a watch link, fetch it to get the actual video
            if watch_link:
                try:
                    watch_html = self.fetch_page(watch_link)
                    watch_soup = BeautifulSoup(watch_html, 'lxml')
                    
                    # Check if watch_link is a /list/ page (episode list)
                    # If so, extract the first episode link from the list
                    if '/list/' in watch_link:
                        episode_links = watch_soup.find_all('a', href=True, class_=lambda x: x and 'recent--block' in str(x))
                        if episode_links:
                            # Get the first episode link (most recent)
                            first_episode_href = episode_links[0].get('href', '')
                            if first_episode_href:
                                if first_episode_href.startswith('http'):
                                    actual_episode_url = first_episode_href
                                elif first_episode_href.startswith('/'):
                                    actual_episode_url = f"{base_url}{first_episode_href}"
                                else:
                                    actual_episode_url = f"{base_url}/{first_episode_href}"
                                
                                # Use the actual episode page instead of the list page
                                watch_link = actual_episode_url
                                # Re-fetch the actual episode page
                                watch_html = self.fetch_page(watch_link)
                                watch_soup = BeautifulSoup(watch_html, 'lxml')
                    
                    # Look for iframes in the watch page (this is where the video player is)
                    iframes = watch_soup.find_all('iframe')
                    for iframe in iframes:
                        src = iframe.get('src', '')
                        if src:
                            video_links.append({
                                'type': 'iframe',
                                'url': src,
                                'quality': 'auto'
                            })
                    
                    # Look for video tags in watch page
                    videos = watch_soup.find_all('video')
                    for video in videos:
                        src = video.get('src', '')
                        if src:
                            video_links.append({
                                'type': 'direct',
                                'url': src if src.startswith('http') else f"{base_url}{src}",
                                'quality': 'auto'
                            })
                        # Check for source tags
                        sources = video.find_all('source')
                        for source in sources:
                            src = source.get('src', '')
                            if src:
                                video_links.append({
                                    'type': 'direct',
                                    'url': src if src.startswith('http') else f"{base_url}{src}",
                                    'quality': source.get('data-quality', 'auto')
                                })
                    
                    # Look for links to external video players (vidtube, embed, etc.)
                    # But exclude the watch/list page URL itself
                    all_links = watch_soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        # Exclude the watch/list page URL and episode page URLs
                        if href and href != watch_link and href != episode_url and not href.endswith('/list/'):
                            if href.startswith('http') and any(domain in href.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'iframe']):
                                # Make sure it's not a page URL, but an actual video/embed URL
                                if '/list/' not in href and '/series/' not in href:
                                    video_links.append({
                                        'type': 'iframe',
                                        'url': href,
                                        'quality': 'auto'
                                    })
                    
                    # Look for iframe URLs in scripts (some sites load iframes dynamically)
                    scripts = watch_soup.find_all('script')
                    for script in scripts:
                        script_text = script.string or ''
                        if script_text:
                            # Look for iframe src in scripts
                            import re
                            iframe_srcs = re.findall(r'iframe.*?src\s*[:=]\s*["\']([^"\']+)["\']', script_text, re.IGNORECASE | re.DOTALL)
                            for src in iframe_srcs:
                                if src.startswith('http'):
                                    video_links.append({
                                        'type': 'iframe',
                                        'url': src,
                                        'quality': 'auto'
                                    })
                            
                            # Look for embed URLs
                            embed_urls = re.findall(r'https?://[^\s"\'<>\)]+(?:embed|player|watch|video)[^\s"\'<>\)]*', script_text, re.IGNORECASE)
                            for url in embed_urls:
                                video_links.append({
                                    'type': 'iframe',
                                    'url': url,
                                    'quality': 'auto'
                                })
                            
                            # METHOD 1: Reverse Engineering - Look for API endpoints that return video URLs
                            # Pattern 1: AJAX/fetch calls with video-related endpoints
                            ajax_patterns = [
                                r'(?:ajax|fetch|\.get|\.post|axios\.(?:get|post))\s*\([^)]*["\']([^"\']*(?:video|player|embed|watch|stream|load)[^"\']*)["\']',
                                r'url\s*[:=]\s*["\']([^"\']*(?:video|player|embed|watch|stream|api)[^"\']*)["\']',
                                r'endpoint\s*[:=]\s*["\']([^"\']*(?:video|player|embed|watch|stream)[^"\']*)["\']',
                            ]
                            
                            for pattern in ajax_patterns:
                                ajax_urls = re.findall(pattern, script_text, re.IGNORECASE)
                                for url in ajax_urls:
                                    if url.startswith('http') or url.startswith('/'):
                                        # Try to call this API endpoint
                                        try:
                                            if url.startswith('/'):
                                                api_url = f"{base_url}{url}"
                                            else:
                                                api_url = url
                                            
                                            # Try GET request first
                                            try:
                                                api_response = self.session.get(api_url, headers=self.headers, timeout=10)
                                                if api_response.status_code == 200:
                                                    # Try to parse as JSON
                                                    try:
                                                        api_data = api_response.json()
                                                        # Look for video URLs in JSON response
                                                        video_urls_from_api = self._extract_video_urls_from_json(api_data)
                                                        for v_url in video_urls_from_api:
                                                            if v_url not in [v['url'] for v in video_links]:
                                                                video_links.append({
                                                                    'type': 'iframe',
                                                                    'url': v_url,
                                                                    'quality': 'auto'
                                                                })
                                                    except:
                                                        # If not JSON, try parsing as HTML
                                                        api_soup = BeautifulSoup(api_response.text, 'lxml')
                                                        api_iframes = api_soup.find_all('iframe')
                                                        for iframe in api_iframes:
                                                            iframe_src = iframe.get('src', '')
                                                            if iframe_src and iframe_src not in [v['url'] for v in video_links]:
                                                                video_links.append({
                                                                    'type': 'iframe',
                                                                    'url': iframe_src,
                                                                    'quality': 'auto'
                                                                })
                                            except:
                                                pass
                                        except:
                                            pass
                            
                            # Pattern 2: Look for POST requests with data
                            post_patterns = [
                                r'\.post\s*\([^)]*["\']([^"\']+)["\'][^)]*data\s*[:=]\s*({[^}]+})',
                                r'fetch\s*\(["\']([^"\']+)["\'][^)]*method\s*[:=]\s*["\']post["\']',
                            ]
                            
                            for pattern in post_patterns:
                                matches = re.findall(pattern, script_text, re.IGNORECASE | re.DOTALL)
                                for match in matches:
                                    if isinstance(match, tuple) and len(match) >= 1:
                                        api_url = match[0] if match[0] else ''
                                        post_data = match[1] if len(match) > 1 and match[1] else {}
                                    else:
                                        api_url = match if isinstance(match, str) else ''
                                        post_data = {}
                                    
                                    if api_url and (api_url.startswith('http') or api_url.startswith('/')):
                                        try:
                                            if api_url.startswith('/'):
                                                api_url = f"{base_url}{api_url}"
                                            
                                            # Try to parse post_data if it's a string
                                            if isinstance(post_data, str):
                                                try:
                                                    post_data = json.loads(post_data)
                                                except:
                                                    post_data = {}
                                            
                                            # Make POST request
                                            try:
                                                api_response = self.session.post(api_url, json=post_data, headers=self.headers, timeout=10)
                                                if api_response.status_code == 200:
                                                    try:
                                                        api_data = api_response.json()
                                                        video_urls_from_api = self._extract_video_urls_from_json(api_data)
                                                        for v_url in video_urls_from_api:
                                                            if v_url not in [v['url'] for v in video_links]:
                                                                video_links.append({
                                                                    'type': 'iframe',
                                                                    'url': v_url,
                                                                    'quality': 'auto'
                                                                })
                                                    except:
                                                        pass
                                            except:
                                                pass
                                        except:
                                            pass
                    
                    # Look for data attributes that might contain video URLs
                    elements_with_data = watch_soup.find_all(attrs=lambda x: x and any(k.startswith('data-') and isinstance(v, str) and 'http' in v for k, v in (x.items() if hasattr(x, 'items') else [])))
                    for elem in elements_with_data:
                        for attr, value in elem.attrs.items():
                            if isinstance(value, str) and attr.startswith('data-') and 'http' in value:
                                if any(domain in value.lower() for domain in ['embed', 'player', 'video', 'iframe']):
                                    video_links.append({
                                        'type': 'iframe',
                                        'url': value,
                                        'quality': 'auto'
                                    })
                    
                    # Look for multiple server options on the watch page
                    # Check for server selection buttons/links/tabs - be more aggressive in finding them
                    server_elements = watch_soup.find_all(['button', 'a', 'div', 'li', 'span'], 
                        class_=lambda x: x and any(kw in str(x).lower() for kw in ['server', 'source', 'quality', 'option', 'tab', 'btn', 'link', 'play']))
                    
                    # Also look for elements with server-related text
                    all_elements = watch_soup.find_all(['button', 'a', 'div', 'li', 'span'])
                    for elem in all_elements:
                        text = elem.get_text(strip=True).lower()
                        if any(kw in text for kw in ['server', 'مشغل', 'خادم', 'سيرفر', 'play', 'تشغيل', 'watch', 'مشاهدة']):
                            if elem not in server_elements:
                                server_elements.append(elem)
                    
                    # Check each server element
                    for server_elem in server_elements:
                        # Check if element has a link to another server
                        server_href = server_elem.get('href', '')
                        server_onclick = server_elem.get('onclick', '')
                        server_data = {k: v for k, v in server_elem.attrs.items() if isinstance(k, str) and k.startswith('data-')}
                        
                        # Extract URL from onclick if it contains one
                        if server_onclick and not server_href:
                            import re
                            onclick_urls = re.findall(r'https?://[^\s"\'<>\)]+', server_onclick)
                            if onclick_urls:
                                server_href = onclick_urls[0]
                        
                        # If it's a link to another server page, fetch it
                        if server_href and server_href.startswith('http') and server_href != watch_link:
                            try:
                                server_html = self.fetch_page(server_href)
                                server_soup = BeautifulSoup(server_html, 'lxml')
                                
                                # Look for iframes in this server page
                                server_iframes = server_soup.find_all('iframe')
                                for iframe in server_iframes:
                                    src = iframe.get('src', '')
                                    if src and src not in [v['url'] for v in video_links]:
                                        video_links.append({
                                            'type': 'iframe',
                                            'url': src,
                                            'quality': 'auto'
                                        })
                                
                                # Look for video links in this server page
                                server_video_links = server_soup.find_all('a', href=True)
                                for link in server_video_links:
                                    href = link.get('href', '')
                                    if href.startswith('http') and any(domain in href.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video']):
                                        if href not in [v['url'] for v in video_links] and href != server_href:
                                            video_links.append({
                                                'type': 'iframe',
                                                'url': href,
                                                'quality': 'auto'
                                            })
                                
                                # Check scripts on server page for video URLs
                                server_scripts = server_soup.find_all('script')
                                for script in server_scripts:
                                    script_text = script.string or ''
                                    if script_text:
                                        import re
                                        # Look for iframe src in server page scripts
                                        iframe_srcs = re.findall(r'iframe.*?src\s*[:=]\s*["\']([^"\']+)["\']', script_text, re.IGNORECASE | re.DOTALL)
                                        for src in iframe_srcs:
                                            if src.startswith('http') and src not in [v['url'] for v in video_links]:
                                                video_links.append({
                                                    'type': 'iframe',
                                                    'url': src,
                                                    'quality': 'auto'
                                                })
                            except:
                                pass  # Skip if server page fails
                        
                        # Check data attributes for video URLs
                        for attr, value in server_data.items():
                            if isinstance(value, str) and 'http' in value:
                                if any(domain in value.lower() for domain in ['vidtube', 'embed', 'player', 'video', 'iframe']):
                                    if value not in [v['url'] for v in video_links] and value != watch_link:
                                        video_links.append({
                                            'type': 'iframe',
                                            'url': value,
                                            'quality': 'auto'
                                        })
                    
                    # Also check for server containers that might have iframes inside
                    # Look for tab content, panels, and any divs that might contain server options
                    server_containers = watch_soup.find_all(['div', 'section', 'ul', 'ol'], 
                        class_=lambda x: x and any(kw in str(x).lower() for kw in ['server', 'source', 'tab-content', 'panel', 'content', 'list', 'options', 'players']))
                    
                    # Also check for containers with server-related IDs
                    server_containers_by_id = watch_soup.find_all(['div', 'section'], id=lambda x: x and any(kw in str(x).lower() for kw in ['server', 'source', 'tab', 'panel', 'player']))
                    server_containers.extend(server_containers_by_id)
                    
                    for container in server_containers:
                        # Check for iframes inside server containers
                        container_iframes = container.find_all('iframe')
                        for iframe in container_iframes:
                            src = iframe.get('src', '')
                            if src and src not in [v['url'] for v in video_links]:
                                video_links.append({
                                    'type': 'iframe',
                                    'url': src,
                                    'quality': 'auto'
                                })
                        
                        # Check for video links inside server containers
                        container_links = container.find_all('a', href=True)
                        for link in container_links:
                            href = link.get('href', '')
                            if href.startswith('http') and any(domain in href.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video']):
                                if href not in [v['url'] for v in video_links] and href != watch_link:
                                    video_links.append({
                                        'type': 'iframe',
                                        'url': href,
                                        'quality': 'auto'
                                    })
                        
                        # Check for buttons/divs with data attributes that might contain video URLs
                        container_buttons = container.find_all(['button', 'div', 'a'], attrs=lambda x: x and any(k.startswith('data-') for k in (x.keys() if hasattr(x, 'keys') else [])))
                        for btn in container_buttons:
                            for attr, value in btn.attrs.items():
                                if isinstance(attr, str) and attr.startswith('data-') and isinstance(value, str) and 'http' in value:
                                    if any(domain in value.lower() for domain in ['vidtube', 'embed', 'player', 'video', 'iframe']):
                                        if value not in [v['url'] for v in video_links] and value != watch_link:
                                            video_links.append({
                                                'type': 'iframe',
                                                'url': value,
                                                'quality': 'auto'
                                            })
                        
                        # Check scripts inside server containers
                        container_scripts = container.find_all('script')
                        for script in container_scripts:
                            script_text = script.string or ''
                            if script_text:
                                import re
                                # Look for iframe src in container scripts
                                iframe_srcs = re.findall(r'iframe.*?src\s*[:=]\s*["\']([^"\']+)["\']', script_text, re.IGNORECASE | re.DOTALL)
                                for src in iframe_srcs:
                                    if src.startswith('http') and src not in [v['url'] for v in video_links]:
                                        video_links.append({
                                            'type': 'iframe',
                                            'url': src,
                                            'quality': 'auto'
                                        })
                                
                                # Look for video URLs in container scripts
                                video_urls = re.findall(r'https?://[^\s"\'<>\)]+(?:vidtube|embed|player|stream|video|watch|iframe)[^\s"\'<>\)]*', script_text, re.IGNORECASE)
                                for url in video_urls:
                                    if url not in [v['url'] for v in video_links] and url != watch_link:
                                        video_links.append({
                                            'type': 'iframe',
                                            'url': url,
                                            'quality': 'auto'
                                        })
                    
                except Exception as e:
                    # If watch page fails, fall through to check episode page
                    try:
                        print(f'Error fetching watch page: {str(e)}')
                    except:
                        pass  # Skip printing if encoding fails
            
            # Also check episode page directly for iframes/videos (fallback)
            # Some sites load the video player directly on the episode page
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if src:
                    video_links.append({
                        'type': 'iframe',
                        'url': src,
                        'quality': 'auto'
                    })
            
            # Check episode page scripts for video URLs (in case video is loaded dynamically)
            episode_scripts = soup.find_all('script')
            for script in episode_scripts:
                script_text = script.string or ''
                if script_text:
                    import re
                    # Look for iframe src in episode page scripts
                    iframe_srcs = re.findall(r'iframe.*?src\s*[:=]\s*["\']([^"\']+)["\']', script_text, re.IGNORECASE | re.DOTALL)
                    for src in iframe_srcs:
                        if src.startswith('http') and src not in [v['url'] for v in video_links]:
                            video_links.append({
                                'type': 'iframe',
                                'url': src,
                                'quality': 'auto'
                            })
                    
                    # Look for video player URLs in episode page scripts
                    player_urls = re.findall(r'https?://[^\s"\'<>\)]+(?:vidtube|embed|player|watch|video)[^\s"\'<>\)]*', script_text, re.IGNORECASE)
                    for url in player_urls:
                        if url not in [v['url'] for v in video_links]:
                            video_links.append({
                                'type': 'iframe',
                                'url': url,
                                'quality': 'auto'
                            })
            
            # Look for direct video links
            video_sources = soup.select('video source, a[href*=".mp4"], a[href*=".m3u8"]')
            for source in video_sources:
                src = source.get('src') or source.get('href', '')
                quality = source.get('data-quality') or source.get_text(strip=True) or 'auto'
                
                if src and ('.mp4' in src or '.m3u8' in src):
                    url = src if src.startswith('http') else f"{base_url}{src}"
                    video_links.append({
                        'type': 'direct',
                        'url': url,
                        'quality': quality
                    })
            
            # Also check download page for playable video links (even if we found some from watch page)
            # Download pages often have direct video file links that can be played
            if download_link:
                try:
                    download_html = self.fetch_page(download_link)
                    download_soup = BeautifulSoup(download_html, 'lxml')
                    
                    # Look for video/download links on download page
                    download_links = download_soup.find_all('a', href=True)
                    for link in download_links:
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True).lower()
                        
                        # Check for direct video files or video hosting links
                        # Only add actual video links, not the download page itself
                        if href and href != download_link:
                            # Check if it's a direct video file (playable)
                            is_video_file = any(ext in href.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi', '.flv', '.webm', '.mov', '.wmv'])
                            # Check if it's a video hosting/embed link (playable)
                            is_video_host = any(domain in href.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video', 'watch', 'iframe', 'play'])
                            # Check if link text suggests it's a play/watch link (not just download)
                            is_play_link = any(kw in link_text for kw in ['play', 'watch', 'مشاهدة', 'تشغيل', 'video', 'stream', 'online'])
                            
                            # Only add playable video links, not download-only links
                            if (is_video_file or is_video_host or is_play_link):
                                if href not in [v['url'] for v in video_links]:
                                    video_links.append({
                                        'type': 'direct' if is_video_file else 'iframe',
                                        'url': href,
                                        'quality': 'auto'
                                    })
                    
                    # Also check for iframes on download page
                    download_iframes = download_soup.find_all('iframe')
                    for iframe in download_iframes:
                        src = iframe.get('src', '')
                        if src and src not in [v['url'] for v in video_links]:
                            video_links.append({
                                'type': 'iframe',
                                'url': src,
                                'quality': 'auto'
                            })
                    
                    # Check for video tags on download page
                    download_videos = download_soup.find_all('video')
                    for video in download_videos:
                        src = video.get('src', '')
                        if src:
                            if src not in [v['url'] for v in video_links]:
                                video_links.append({
                                    'type': 'direct',
                                    'url': src if src.startswith('http') else f"{base_url}{src}",
                                    'quality': 'auto'
                                })
                        # Check for source tags
                        sources = video.find_all('source')
                        for source in sources:
                            src = source.get('src', '')
                            if src and src not in [v['url'] for v in video_links]:
                                video_links.append({
                                    'type': 'direct',
                                    'url': src if src.startswith('http') else f"{base_url}{src}",
                                    'quality': source.get('data-quality', 'auto')
                                })
                    
                    # Check scripts on download page for video URLs
                    download_scripts = download_soup.find_all('script')
                    for script in download_scripts:
                        script_text = script.string or ''
                        if script_text:
                            import re
                            # Look for video file URLs in scripts (playable)
                            video_file_urls = re.findall(r'https?://[^\s"\'<>\)]+(?:\.mp4|\.m3u8|\.mkv|\.avi|\.flv|\.webm|\.mov|\.wmv)[^\s"\'<>\)]*', script_text, re.IGNORECASE)
                            for url in video_file_urls:
                                if url not in [v['url'] for v in video_links]:
                                    video_links.append({
                                        'type': 'direct',
                                        'url': url,
                                        'quality': 'auto'
                                    })
                            
                            # Look for video hosting/embed URLs in scripts (playable)
                            video_host_urls = re.findall(r'https?://[^\s"\'<>\)]+(?:vidtube|embed|player|stream|video|watch|iframe|play)[^\s"\'<>\)]*', script_text, re.IGNORECASE)
                            for url in video_host_urls:
                                if url not in [v['url'] for v in video_links] and url != download_link:
                                    video_links.append({
                                        'type': 'iframe',
                                        'url': url,
                                        'quality': 'auto'
                                    })
                            
                            # Look for iframe src assignments in scripts
                            iframe_srcs = re.findall(r'iframe.*?src\s*[:=]\s*["\']([^"\']+)["\']', script_text, re.IGNORECASE | re.DOTALL)
                            for src in iframe_srcs:
                                if src.startswith('http') and src not in [v['url'] for v in video_links]:
                                    video_links.append({
                                        'type': 'iframe',
                                        'url': src,
                                        'quality': 'auto'
                                    })
                    
                    # Check for data attributes that might contain video URLs
                    download_data_elements = download_soup.find_all(attrs=lambda x: x and any(k.startswith('data-') and isinstance(v, str) and 'http' in v for k, v in (x.items() if hasattr(x, 'items') else [])))
                    for elem in download_data_elements:
                        for attr, value in elem.attrs.items():
                            if isinstance(attr, str) and attr.startswith('data-') and isinstance(value, str) and 'http' in value:
                                if any(domain in value.lower() for domain in ['vidtube', 'embed', 'player', 'video', 'iframe']) or \
                                   any(ext in value.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi']):
                                    if value not in [v['url'] for v in video_links] and value != download_link:
                                        video_links.append({
                                            'type': 'direct' if any(ext in value.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi']) else 'iframe',
                                            'url': value,
                                            'quality': 'auto'
                                        })
                except Exception as e:
                    # If download page fails, continue to fallback
                    try:
                        print(f'Error fetching download page: {str(e)}')
                    except:
                        pass
            
            # Filter out any page URLs that might have been added (watch/list page, episode page, etc.)
            # Only keep actual video links (iframes, direct files, etc.)
            filtered_video_links = []
            for link in video_links:
                url = link.get('url', '')
                # Exclude page URLs - only include actual video/embed links
                if url and not url.endswith('/list/') and '/list/' not in url:
                    # Check if it's a video file or embed URL
                    is_video_file = any(ext in url.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi', '.flv', '.webm'])
                    is_embed_url = any(domain in url.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video', 'iframe'])
                    is_page_url = any(pattern in url.lower() for pattern in ['/series/', '/episode/', '/watch/', '/download/', '/list/'])
                    
                    if (is_video_file or is_embed_url) and not is_page_url:
                        filtered_video_links.append(link)
            
            video_links = filtered_video_links
            
            # If no video links found, try Playwright as fallback (for JavaScript-loaded content)
            if not video_links:
                # METHOD 2: Use Playwright to execute JavaScript and extract video links
                if watch_link:
                    playwright_links = self._extract_video_with_playwright(watch_link)
                    video_links.extend(playwright_links)
                
                # If still no links, try episode page with Playwright
                if not video_links:
                    playwright_links = self._extract_video_with_playwright(episode_url)
                    video_links.extend(playwright_links)
                
                # Filter Playwright results again
                if video_links:
                    filtered_playwright_links = []
                    for link in video_links:
                        url = link.get('url', '')
                        if url and not url.endswith('/list/') and '/list/' not in url:
                            is_video_file = any(ext in url.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi', '.flv', '.webm'])
                            is_embed_url = any(domain in url.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video', 'iframe'])
                            is_page_url = any(pattern in url.lower() for pattern in ['/series/', '/episode/', '/watch/', '/download/', '/list/'])
                            
                            if (is_video_file or is_embed_url) and not is_page_url:
                                filtered_playwright_links.append(link)
                    video_links = filtered_playwright_links
            
            return video_links if video_links else None
        except Exception as e:
            try:
                print(f'Error getting episode video links: {str(e)}')
            except:
                pass  # Skip printing if encoding fails
            raise
    
    def _extract_video_urls_from_json(self, data, found_urls=None):
        """Recursively extract video URLs from JSON data"""
        if found_urls is None:
            found_urls = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str) and any(kw in key.lower() for kw in ['url', 'src', 'link', 'embed', 'player', 'video', 'iframe']):
                    if isinstance(value, str) and value.startswith('http'):
                        if any(domain in value.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video', 'iframe']) or \
                           any(ext in value.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi']):
                            if value not in found_urls:
                                found_urls.append(value)
                self._extract_video_urls_from_json(value, found_urls)
        elif isinstance(data, list):
            for item in data:
                self._extract_video_urls_from_json(item, found_urls)
        elif isinstance(data, str) and data.startswith('http'):
            if any(domain in data.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video', 'iframe']) or \
               any(ext in data.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi']):
                if data not in found_urls:
                    found_urls.append(data)
        
        return found_urls
    
    def _get_playwright_browser(self):
        """Get or create Playwright browser instance (lazy loading)"""
        if not PLAYWRIGHT_AVAILABLE:
            return None
        
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
        
        return self._browser
    
    def _extract_video_with_playwright(self, url: str) -> List[Dict]:
        """Extract video links using Playwright (for JavaScript-loaded content)"""
        if not PLAYWRIGHT_AVAILABLE:
            return []
        
        video_links = []
        
        try:
            browser = self._get_playwright_browser()
            if browser is None:
                return []
            
            page = browser.new_page()
            
            # Set headers
            page.set_extra_http_headers({
                'User-Agent': self.headers.get('User-Agent', ''),
                'Accept-Language': self.headers.get('Accept-Language', ''),
            })
            
            # Intercept network requests to capture video URLs
            network_video_urls = []
            
            def handle_response(response):
                url = response.url
                # Check if response is a video or embed URL
                if any(domain in url.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video', 'iframe']) or \
                   any(ext in url.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi']):
                    if url not in network_video_urls:
                        network_video_urls.append(url)
            
            page.on('response', handle_response)
            
            # Navigate to page and wait for it to load
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for network to be idle
            try:
                page.wait_for_load_state('networkidle', timeout=30000)  # Increased timeout to 30 seconds
            except:
                pass  # Continue even if networkidle times out
            
            # Wait longer for JavaScript to execute and load content
            page.wait_for_timeout(15000)  # Increased wait time to 15 seconds
            
            # Try to interact with the page - look for play buttons or server selection
            try:
                # Look for play icons (these are server options)
                play_icons = page.query_selector_all('.playIcon, i.fa-brands.fa-google-play, i[class*="play"]')
                for icon in play_icons[:5]:  # Try first 5 play icons
                    try:
                        # Get parent element (button/link/div) and click it
                        # Click the icon or its parent
                        try:
                            icon.click()
                        except:
                            # If clicking icon fails, try parent
                            try:
                                parent_selector = icon.evaluate("el => el.closest('a, button, div')?.tagName + (el.closest('a, button, div')?.className ? '.' + el.closest('a, button, div').className.split(' ')[0] : '')")
                                if parent_selector:
                                    page.click(parent_selector, timeout=2000)
                            except:
                                pass
                        
                        # Wait for iframe to appear after click
                        try:
                            page.wait_for_selector('iframe[src]', timeout=15000, state='attached')
                        except:
                            pass
                        
                        page.wait_for_timeout(10000)  # Increased wait time to 10 seconds after click
                        
                        # Check if iframe appeared after click
                        new_iframes = page.evaluate("""
                            () => {
                                const iframes = Array.from(document.querySelectorAll('iframe'));
                                return iframes.map(iframe => iframe.src).filter(src => src && src.startsWith('http'));
                            }
                        """)
                        if new_iframes:
                            for src in new_iframes:
                                if src not in [v['url'] for v in video_links]:
                                    video_links.append({
                                        'type': 'iframe',
                                        'url': src,
                                        'quality': 'auto'
                                    })
                            break  # Found video, stop clicking
                    except:
                        pass
            except:
                pass
            
            # Wait again after interactions
            page.wait_for_timeout(10000)  # Increased wait time to 10 seconds
            
            # Look for iframes (including dynamically loaded ones)
            iframes = page.query_selector_all('iframe')
            for iframe in iframes:
                src = iframe.get_attribute('src')
                if src and src.startswith('http'):
                    if src not in [v['url'] for v in video_links]:
                        video_links.append({
                            'type': 'iframe',
                            'url': src,
                            'quality': 'auto'
                        })
            
            # Also check for iframes that might be in shadow DOM or dynamically added
            # Get all iframes including those added after page load
            try:
                iframe_srcs = page.evaluate("""
                    () => {
                        const iframes = Array.from(document.querySelectorAll('iframe'));
                        return iframes.map(iframe => iframe.src).filter(src => src && src.startsWith('http'));
                    }
                """)
                for src in iframe_srcs:
                    if src not in [v['url'] for v in video_links]:
                        video_links.append({
                            'type': 'iframe',
                            'url': src,
                            'quality': 'auto'
                        })
            except:
                pass
            
            # Look for video elements
            videos = page.query_selector_all('video')
            for video in videos:
                src = video.get_attribute('src')
                if src:
                    full_url = src if src.startswith('http') else f"{self.get_base_url()}{src}"
                    if full_url not in [v['url'] for v in video_links]:
                        video_links.append({
                            'type': 'direct',
                            'url': full_url,
                            'quality': 'auto'
                        })
            
            # Look for video source elements
            sources = page.query_selector_all('video source')
            for source in sources:
                src = source.get_attribute('src')
                if src:
                    full_url = src if src.startswith('http') else f"{self.get_base_url()}{src}"
                    if full_url not in [v['url'] for v in video_links]:
                        video_links.append({
                            'type': 'direct',
                            'url': full_url,
                            'quality': source.get_attribute('data-quality') or 'auto'
                        })
            
            # Check for video links in page content
            all_links = page.query_selector_all('a[href]')
            for link in all_links:
                href = link.get_attribute('href')
                if href and href.startswith('http'):
                    if any(domain in href.lower() for domain in ['vidtube', 'embed', 'player', 'stream', 'video']) or \
                       any(ext in href.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi']):
                        if href not in [v['url'] for v in video_links] and '/list/' not in href:
                            video_links.append({
                                'type': 'iframe' if 'embed' in href.lower() or 'player' in href.lower() else 'direct',
                                'url': href,
                                'quality': 'auto'
                            })
            
            # Check for server selection buttons/links and try clicking them
            try:
                server_buttons = page.query_selector_all('button[class*="server"], a[class*="server"], button[class*="source"], a[class*="source"], button[class*="tab"], a[class*="tab"]')
                for button in server_buttons[:5]:  # Try first 5 server buttons
                    try:
                        button.click()
                        try:
                            page.wait_for_selector('iframe[src]', timeout=15000, state='attached')
                        except:
                            pass
                        page.wait_for_timeout(10000)  # Increased wait time for content to load
                        
                        # Check for iframes after clicking
                        new_iframes = page.query_selector_all('iframe')
                        for iframe in new_iframes:
                            src = iframe.get_attribute('src')
                            if src and src.startswith('http') and src not in [v['url'] for v in video_links]:
                                video_links.append({
                                    'type': 'iframe',
                                    'url': src,
                                    'quality': 'auto'
                                })
                    except:
                        pass
            except:
                pass
            
            # Final check - get all iframes one more time
            try:
                final_iframes = page.evaluate("""
                    () => {
                        const iframes = Array.from(document.querySelectorAll('iframe'));
                        return iframes.map(iframe => iframe.src).filter(src => src && src.startsWith('http'));
                    }
                """)
                for src in final_iframes:
                    if src not in [v['url'] for v in video_links]:
                        video_links.append({
                            'type': 'iframe',
                            'url': src,
                            'quality': 'auto'
                        })
            except:
                pass
            
            # Add network-captured video URLs
            for url in network_video_urls:
                if url not in [v['url'] for v in video_links]:
                    video_links.append({
                        'type': 'iframe' if 'embed' in url.lower() or 'player' in url.lower() else 'direct',
                        'url': url,
                        'quality': 'auto'
                    })
            
            page.close()
            
        except Exception as e:
            try:
                print(f'Playwright error: {str(e)}')
            except:
                pass
        
        return video_links
    
    def extract_id_from_url(self, url: str) -> str:
        """Extract ID from URL"""
        match = re.search(r'/(\d+)/', url) or re.search(r'/([^/]+)/?$', url)
        return match.group(1) if match else url.split('/')[-1]
    
    def extract_episode_number(self, text: str) -> Optional[int]:
        """Extract episode number from text"""
        match = re.search(r'episode\s*(\d+)', text, re.IGNORECASE) or \
                re.search(r'ep\s*(\d+)', text, re.IGNORECASE) or \
                re.search(r'(\d+)', text)
        return int(match.group(1)) if match else None
    
    def get_popular_series(self) -> List[Dict]:
        """Get popular/top series from TopCinema"""
        try:
            base_url = self.get_base_url()
            
            # TopCinema homepage has popular content
            pages_to_try = [
                base_url,  # Homepage
                f"{base_url}/series/",  # Series page
                f"{base_url}/movies/",  # Movies page
            ]
            
            series = []
            seen_links = set()
            
            for url in pages_to_try:
                try:
                    html = self.fetch_page(url)
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # FaselHD: Find all content links
                    all_links = soup.find_all('a', href=True)
                    
                    for link_elem in all_links:
                        link = link_elem.get('href', '')
                        if not link or link in seen_links:
                            continue
                        
                        # Skip navigation links
                        skip_patterns = ['/category/', '/tag/', '/page/', '#', 'javascript:', 'mailto:', '/search', '/series/', '/movies/']
                        if any(pattern in link for pattern in skip_patterns):
                            continue
                        
                        # Only accept content links from FaselHD
                        if base_url not in link and not link.startswith('/'):
                            continue
                        
                        # Make link absolute
                        if not link.startswith('http'):
                            if link.startswith('/'):
                                link = f"{base_url}{link}"
                            else:
                                link = f"{base_url}/{link}"
                        
                        # Get title from link text
                        link_text = link_elem.get_text(strip=True)
                        
                        # Skip if title is too short or is navigation
                        nav_words = ['الكل', 'افلام', 'مسلسلات', 'بحث', 'القائمة', 'الصفحة الرئيسية', 'topcinema', 'top cinema']
                        if not link_text or len(link_text) < 3 or any(nav.lower() in link_text.lower() for nav in nav_words):
                            continue
                        
                        # Get image from nearby elements
                        image = None
                        parent = link_elem.parent
                        if parent:
                            img_elem = parent.find('img')
                            if img_elem:
                                image = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                        
                        # Make image absolute
                        image_url = None
                        if image:
                            if image.startswith('http'):
                                image_url = image
                            elif image.startswith('/'):
                                image_url = f"{base_url}{image}"
                            else:
                                image_url = f"{base_url}/{image}"
                        
                        seen_links.add(link)
                        series.append({
                            'id': self.extract_id_from_url(link),
                            'title': ' '.join(link_text.split()),
                            'link': link,
                            'image': image_url,
                            'source': 'topcinema'
                        })
                    
                    # If we found enough items, break
                    if len(series) >= 10:
                        break
                        
                except Exception as e:
                    try:
                        print(f"Error fetching {url}: {e}")
                    except:
                        pass  # Skip printing if encoding fails
                    continue
            
            # Remove duplicates and return top 20
            unique_series = []
            seen_titles = set()
            for item in series:
                if item['title'] not in seen_titles:
                    unique_series.append(item)
                    seen_titles.add(item['title'])
                    if len(unique_series) >= 20:
                        break
            
            return unique_series
        except Exception as e:
            try:
                print(f'Error getting popular series: {str(e)}')
            except:
                pass  # Skip printing if encoding fails
            raise


# Create singleton instance
scraper = ScraperService()

