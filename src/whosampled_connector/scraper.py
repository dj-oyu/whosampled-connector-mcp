"""
WhoSampled scraper module using Playwright for anti-bot bypass.
"""
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import urllib.parse


class WhoSampledScraper:
    """Scraper for WhoSampled website using headless browser."""

    BASE_URL = "https://www.whosampled.com"
    SEARCH_URL = f"{BASE_URL}/search/"

    def __init__(self):
        self.playwright = None
        self.browser = None
        self._initialized = False

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not self._initialized:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            self._initialized = True

    async def _fetch_page(self, url: str) -> str:
        """
        Fetch a page using headless browser.

        Args:
            url: URL to fetch

        Returns:
            Page HTML content
        """
        await self._ensure_browser()

        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Upgrade-Insecure-Requests': '1'
            }
        )

        page = await context.new_page()

        # Inject stealth scripts before navigation
        await page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });

            // Override chrome property
            window.chrome = {
                runtime: {}
            };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        try:
            # Navigate to page with more lenient wait condition
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Wait for page to be ready
            await page.wait_for_load_state('domcontentloaded')

            # Wait a bit longer for dynamic content
            await page.wait_for_timeout(2000)

            # Get page content
            content = await page.content()

            return content

        except Exception as e:
            print(f"Error fetching page {url}: {e}")
            raise

        finally:
            await page.close()
            await context.close()

    async def search_track(self, artist: str, track: str) -> Optional[Dict]:
        """
        Search for a track on WhoSampled.

        Args:
            artist: Artist name
            track: Track name

        Returns:
            Dictionary with track information and URL, or None if not found
        """
        query = f"{artist} {track}"
        params = urllib.parse.urlencode({"q": query})
        search_url = f"{self.SEARCH_URL}?{params}"

        try:
            html = await self._fetch_page(search_url)
            soup = BeautifulSoup(html, 'lxml')

            # Find the first track result
            # Try both trackTitle and trackName classes
            track_result = soup.select_one('a.trackTitle') or soup.select_one('a.trackName')
            if not track_result:
                return None

            track_url = self.BASE_URL + track_result.get('href', '')
            track_title = track_result.get_text(strip=True)

            # Extract artist name - look for the next sibling link or parent's next link
            artist_name = artist
            parent = track_result.parent
            if parent:
                # Find all links in the parent container
                links = parent.find_all('a')
                # The artist is usually the second link
                if len(links) > 1:
                    artist_name = links[1].get_text(strip=True)

            return {
                "title": track_title,
                "artist": artist_name,
                "url": track_url
            }

        except Exception as e:
            print(f"Error searching track: {e}")
            return None

    async def get_youtube_links_from_search(self, artist: str, track: str, max_per_section: int = 3) -> Dict:
        """
        Get YouTube links from search results with priority: Top Hit > Connections > Tracks.

        Args:
            artist: Artist name
            track: Track name
            max_per_section: Maximum number of tracks to get from each section (default: 3)

        Returns:
            Dictionary with YouTube links organized by section priority
        """
        query = f"{artist} {track}"
        params = urllib.parse.urlencode({"q": query})
        search_url = f"{self.SEARCH_URL}?{params}"

        result = {
            "query": query,
            "top_hit": [],
            "connections": [],
            "tracks": []
        }

        try:
            html = await self._fetch_page(search_url)
            soup = BeautifulSoup(html, 'lxml')

            # Find sections in the search results
            # WhoSampled typically has: top result, connections, and tracks sections

            # Try to identify Top Hit (usually the first prominent result)
            top_hit_section = soup.select_one('div.topResult, div.top-result, section.topResult')
            if top_hit_section:
                tracks = await self._extract_tracks_with_youtube(top_hit_section, max_per_section)
                result["top_hit"] = tracks
            elif not top_hit_section:
                # If no specific top hit section, treat first track as top hit
                first_track = soup.select_one('a.trackTitle, a.trackName')
                if first_track:
                    tracks = await self._extract_tracks_with_youtube(soup, 1, start_from_first=True)
                    if tracks:
                        result["top_hit"] = tracks

            # Find Connections section
            connections_section = soup.find('section', string=lambda t: t and 'connection' in t.lower() if isinstance(t, str) else False)
            if not connections_section:
                # Try finding by header
                for header in soup.find_all(['h2', 'h3', 'h4']):
                    if header and 'connection' in header.get_text(strip=True).lower():
                        connections_section = header.find_parent('section')
                        break

            if connections_section:
                tracks = await self._extract_tracks_with_youtube(connections_section, max_per_section)
                result["connections"] = tracks

            # Find Tracks section (general results)
            # Usually all track results not in top hit or connections
            all_track_links = soup.select('a.trackTitle, a.trackName')

            # Filter out tracks already in top_hit or connections
            existing_urls = set()
            for section_tracks in [result["top_hit"], result["connections"]]:
                for t in section_tracks:
                    existing_urls.add(t["url"])

            tracks_to_process = []
            for track_link in all_track_links:
                track_url = self.BASE_URL + track_link.get('href', '')
                if track_url not in existing_urls and len(tracks_to_process) < max_per_section:
                    tracks_to_process.append(track_link)

            # Extract YouTube links for remaining tracks
            for track_link in tracks_to_process:
                track_info = await self._extract_single_track_with_youtube(track_link)
                if track_info:
                    result["tracks"].append(track_info)

            return result

        except Exception as e:
            print(f"Error getting YouTube links from search: {e}")
            return {"error": str(e), "query": query}

    async def _extract_tracks_with_youtube(self, section, max_count: int, start_from_first: bool = False) -> List[Dict]:
        """
        Extract tracks with YouTube links from a section.

        Args:
            section: BeautifulSoup section element
            max_count: Maximum number of tracks to extract
            start_from_first: If True, start from the first track in the section

        Returns:
            List of dictionaries with track information and YouTube links
        """
        tracks = []
        track_links = section.select('a.trackTitle, a.trackName')

        for i, track_link in enumerate(track_links):
            if i >= max_count:
                break

            track_info = await self._extract_single_track_with_youtube(track_link)
            if track_info:
                tracks.append(track_info)

        return tracks

    async def _extract_single_track_with_youtube(self, track_link) -> Optional[Dict]:
        """
        Extract a single track's information with YouTube link.

        Args:
            track_link: BeautifulSoup track link element

        Returns:
            Dictionary with track information and YouTube link, or None
        """
        try:
            track_name = track_link.get_text(strip=True)
            track_href = track_link.get('href', '')
            track_url = self.BASE_URL + track_href if track_href else ""

            # Extract artist name - check for span.trackArtist first, then <a> tag
            artist_name = "Unknown"

            # First, try to find span.trackArtist
            artist_span = track_link.find_next_sibling('span', class_='trackArtist')
            if artist_span:
                artist_name = artist_span.get_text(strip=True)
            else:
                # Try to find the next sibling <a> tag
                next_link = track_link.find_next_sibling('a')
                if next_link and 'trackName' not in next_link.get('class', []) and 'trackTitle' not in next_link.get('class', []):
                    artist_name = next_link.get_text(strip=True)
                else:
                    parent = track_link.parent
                    if parent:
                        all_links = parent.find_all('a')
                        try:
                            track_index = all_links.index(track_link)
                            if track_index + 1 < len(all_links):
                                artist_link = all_links[track_index + 1]
                                if 'trackName' not in artist_link.get('class', []) and 'trackTitle' not in artist_link.get('class', []):
                                    artist_name = artist_link.get_text(strip=True)
                        except ValueError:
                            pass

            track_info = {
                "track": track_name,
                "artist": artist_name,
                "url": track_url,
                "youtube_url": None
            }

            # Get YouTube link from track page
            if track_url:
                try:
                    html = await self._fetch_page(track_url)
                    soup = BeautifulSoup(html, 'lxml')
                    youtube_link = soup.select_one('a[href*="youtube.com"], a[href*="youtu.be"]')
                    if youtube_link:
                        track_info["youtube_url"] = youtube_link.get('href', '')
                except Exception as e:
                    print(f"Error fetching YouTube link for {track_url}: {e}")

            return track_info

        except Exception as e:
            print(f"Error extracting track with YouTube: {e}")
            return None

    async def get_track_details(self, track_url: str, include_youtube: bool = False) -> Dict:
        """
        Get detailed information about a track.

        Args:
            track_url: URL of the track page
            include_youtube: Whether to include YouTube links

        Returns:
            Dictionary with track details including samples, covers, remixes
        """
        try:
            html = await self._fetch_page(track_url)
            soup = BeautifulSoup(html, 'lxml')

            result = {
                "url": track_url,
                "samples": [],
                "sampled_by": [],
                "covers": [],
                "covered_by": [],
                "remixes": [],
                "remixed_by": []
            }

            # Get track title and artist
            title_elem = soup.select_one('h1.trackName, h1')
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

            # Get YouTube link if requested
            if include_youtube:
                youtube_link = soup.select_one('a[href*="youtube.com"], a[href*="youtu.be"]')
                if youtube_link:
                    result["youtube_url"] = youtube_link.get('href', '')

            # Find all subsections (WhoSampled uses section.subsection with headers)
            subsections = soup.select('section.subsection')

            for subsection in subsections:
                # Get the header to determine the type of connection
                header = subsection.find(['h2', 'h3', 'h4'])
                if not header:
                    continue

                header_text = header.get_text(strip=True).lower()

                # Determine connection type based on header text
                if 'contains sample' in header_text or ('sampled' in header_text and 'sampled in' not in header_text):
                    result["samples"] = self._extract_connections(subsection)
                elif 'sampled in' in header_text:
                    result["sampled_by"] = self._extract_connections(subsection)
                elif 'cover of' in header_text:
                    result["covers"] = self._extract_connections(subsection)
                elif 'covered in' in header_text or 'covered by' in header_text:
                    result["covered_by"] = self._extract_connections(subsection)
                elif 'remix of' in header_text:
                    result["remixes"] = self._extract_connections(subsection)
                elif 'remixed in' in header_text or 'remixed by' in header_text:
                    result["remixed_by"] = self._extract_connections(subsection)

            return result

        except Exception as e:
            print(f"Error getting track details: {e}")
            return {"error": str(e), "url": track_url}

    def _extract_connections(self, section) -> List[Dict]:
        """
        Extract track connections (samples, covers, remixes) from a section.

        Args:
            section: BeautifulSoup section element

        Returns:
            List of dictionaries with track information
        """
        connections = []

        # Find all track links (a.trackName elements)
        track_links = section.select('a.trackName')

        for track_link in track_links:
            track_name = track_link.get_text(strip=True)
            track_href = track_link.get('href', '')
            track_url = self.BASE_URL + track_href if track_href else ""

            # Find artist - check for span.trackArtist first, then <a> tag
            artist_name = "Unknown"

            # First, try to find span.trackArtist (common in test fixtures and some WhoSampled pages)
            artist_span = track_link.find_next_sibling('span', class_='trackArtist')
            if artist_span:
                artist_name = artist_span.get_text(strip=True)
            else:
                # Try to find the next sibling <a> tag
                next_link = track_link.find_next_sibling('a')
                if next_link:
                    # Make sure it's not another track link
                    if 'trackName' not in next_link.get('class', []):
                        artist_name = next_link.get_text(strip=True)
                else:
                    # If no sibling, look in the parent's children
                    parent = track_link.parent
                    if parent:
                        all_links = parent.find_all('a')
                        # Find the position of track_link
                        try:
                            track_index = all_links.index(track_link)
                            # Get the next link if it exists
                            if track_index + 1 < len(all_links):
                                artist_link = all_links[track_index + 1]
                                if 'trackName' not in artist_link.get('class', []):
                                    artist_name = artist_link.get_text(strip=True)
                        except ValueError:
                            pass

            connection = {
                "track": track_name,
                "artist": artist_name,
                "url": track_url
            }

            connections.append(connection)

        return connections

    async def aclose(self):
        """Close the browser and playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False

    def close(self):
        """Synchronous close wrapper."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.aclose())
            else:
                asyncio.run(self.aclose())
        except:
            pass
