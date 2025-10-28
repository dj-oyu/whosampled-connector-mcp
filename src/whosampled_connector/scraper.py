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
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
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
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        try:
            # Navigate to page
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait a bit for any dynamic content
            await page.wait_for_timeout(1000)

            # Get page content
            content = await page.content()

            return content

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
            track_result = soup.select_one('li.trackName a')
            if not track_result:
                return None

            track_url = self.BASE_URL + track_result.get('href', '')
            track_title = track_result.get_text(strip=True)

            # Extract artist name if available
            artist_elem = soup.select_one('li.trackName .trackArtist')
            artist_name = artist_elem.get_text(strip=True) if artist_elem else artist

            return {
                "title": track_title,
                "artist": artist_name,
                "url": track_url
            }

        except Exception as e:
            print(f"Error searching track: {e}")
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

            # Extract samples (tracks this song sampled)
            samples_section = soup.find('section', {'id': 'samples'})
            if samples_section:
                result["samples"] = self._extract_connections(samples_section)

            # Extract sampled by (tracks that sampled this song)
            sampled_by_section = soup.find('section', {'id': 'was-sampled'})
            if sampled_by_section:
                result["sampled_by"] = self._extract_connections(sampled_by_section)

            # Extract covers
            covers_section = soup.find('section', {'id': 'covers'})
            if covers_section:
                result["covers"] = self._extract_connections(covers_section)

            # Extract covered by
            covered_by_section = soup.find('section', {'id': 'was-covered'})
            if covered_by_section:
                result["covered_by"] = self._extract_connections(covered_by_section)

            # Extract remixes
            remixes_section = soup.find('section', {'id': 'remixes'})
            if remixes_section:
                result["remixes"] = self._extract_connections(remixes_section)

            # Extract remixed by
            remixed_by_section = soup.find('section', {'id': 'was-remixed'})
            if remixed_by_section:
                result["remixed_by"] = self._extract_connections(remixed_by_section)

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

        # Look for track entries in the section
        entries = section.select('.trackItem, .sampleEntry, .coverEntry, .remixEntry, li')

        for entry in entries:
            # Try to find track link and artist
            track_link = entry.select_one('a.trackName, a[href*="/sample/"]')
            if not track_link:
                continue

            track_name = track_link.get_text(strip=True)
            track_url = self.BASE_URL + track_link.get('href', '')

            # Try to find artist
            artist_elem = entry.select_one('.trackArtist, .artistName')
            artist_name = artist_elem.get_text(strip=True) if artist_elem else "Unknown"

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
