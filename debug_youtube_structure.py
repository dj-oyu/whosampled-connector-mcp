#!/usr/bin/env python3
"""
Debug script to investigate YouTube link structure on WhoSampled pages.
This will help us understand how to properly extract the actual track YouTube link
instead of the WhoSampled channel subscription link.
"""
import asyncio
from bs4 import BeautifulSoup
from src.whosampled_connector.scraper import WhoSampledScraper


async def debug_youtube_links(artist: str, track: str):
    """Debug YouTube links extraction from WhoSampled."""
    scraper = WhoSampledScraper()

    try:
        # First, search for the track
        print(f"Searching for: {artist} - {track}")
        print("=" * 80)

        search_result = await scraper.search_track(artist, track)
        if not search_result:
            print("Track not found!")
            return

        print(f"Found: {search_result['title']} by {search_result['artist']}")
        print(f"URL: {search_result['url']}")
        print("=" * 80)

        # Fetch the track page
        print("\nFetching track page HTML...")
        html = await scraper._fetch_page(search_result['url'])
        soup = BeautifulSoup(html, 'lxml')

        # Find ALL YouTube links on the page
        print("\n" + "=" * 80)
        print("ALL YOUTUBE LINKS FOUND ON PAGE:")
        print("=" * 80)

        youtube_links = soup.find_all('a', href=lambda x: x and ('youtube.com' in x or 'youtu.be' in x))

        if not youtube_links:
            print("No YouTube links found on the page!")
        else:
            for i, link in enumerate(youtube_links, 1):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                classes = link.get('class', [])

                print(f"\n--- Link #{i} ---")
                print(f"URL: {href}")
                print(f"Text: {text}")
                print(f"Classes: {classes}")

                # Get parent context
                parent = link.parent
                if parent:
                    print(f"Parent tag: {parent.name}")
                    print(f"Parent classes: {parent.get('class', [])}")
                    print(f"Parent text (first 100 chars): {parent.get_text(strip=True)[:100]}")

                # Print the surrounding HTML
                print("\nSurrounding HTML:")
                # Get the link element and its parent for context
                if parent:
                    print(str(parent)[:500])  # First 500 chars of parent HTML
                else:
                    print(str(link)[:500])
                print()

        # Check for specific patterns we might use
        print("\n" + "=" * 80)
        print("ANALYSIS:")
        print("=" * 80)

        # Try different selectors
        selectors_to_try = [
            ('a.playIcon[href*="youtube"]', 'Play icon with YouTube link'),
            ('div.trackDetails a[href*="youtube"]', 'YouTube link in track details'),
            ('div.player a[href*="youtube"]', 'YouTube link in player div'),
            ('a[title*="YouTube"][href*="youtube"]', 'YouTube link with YouTube in title'),
            ('a[href*="youtube.com/watch"]', 'YouTube watch URL'),
            ('a[href*="youtu.be/"]', 'YouTube short URL'),
            ('iframe[src*="youtube"]', 'YouTube iframe'),
        ]

        for selector, description in selectors_to_try:
            result = soup.select_one(selector)
            if result:
                print(f"\n✓ Found with selector: {selector}")
                print(f"  Description: {description}")
                if result.name == 'iframe':
                    print(f"  SRC: {result.get('src', '')}")
                else:
                    print(f"  HREF: {result.get('href', '')}")
                    print(f"  Text: {result.get_text(strip=True)}")
                    print(f"  Full HTML: {str(result)[:300]}")
            else:
                print(f"\n✗ Not found: {selector}")

        # Check for meta tags
        print("\n" + "=" * 80)
        print("META TAGS:")
        print("=" * 80)

        og_video = soup.find('meta', property='og:video:url')
        if og_video:
            print(f"og:video:url: {og_video.get('content', '')}")

        og_video_secure = soup.find('meta', property='og:video:secure_url')
        if og_video_secure:
            print(f"og:video:secure_url: {og_video_secure.get('content', '')}")

        # Check for any data attributes with YouTube
        print("\n" + "=" * 80)
        print("ELEMENTS WITH DATA-* ATTRIBUTES CONTAINING 'youtube':")
        print("=" * 80)

        for tag in soup.find_all(lambda t: any('youtube' in str(v).lower() for k, v in t.attrs.items() if k.startswith('data-'))):
            print(f"\nTag: {tag.name}")
            print(f"Attributes: {tag.attrs}")
            print(f"Text: {tag.get_text(strip=True)[:100]}")
            print(f"HTML: {str(tag)[:300]}")

    finally:
        await scraper.aclose()


if __name__ == "__main__":
    # Test with the problematic track
    artist = "Hololive English -Advent-"
    track = "Team Tomodachi"

    asyncio.run(debug_youtube_links(artist, track))
