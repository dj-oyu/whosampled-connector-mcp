#!/usr/bin/env python3
"""
Simple debug script to investigate YouTube link structure.
Run this manually to see what YouTube links exist on WhoSampled pages.
"""
import asyncio
from bs4 import BeautifulSoup
from src.whosampled_connector.scraper import WhoSampledScraper


async def main():
    scraper = WhoSampledScraper()

    try:
        # Search for the track
        artist = "Hololive English -Advent-"
        track = "Team Tomodachi"

        print(f"=== Searching: {artist} - {track} ===\n")

        result = await scraper.search_track(artist, track)
        if not result:
            print("Track not found!")
            return

        print(f"Found: {result['title']} by {result['artist']}")
        print(f"URL: {result['url']}\n")

        # Fetch track page
        print("=== Fetching track page ===\n")
        html = await scraper._fetch_page(result['url'])
        soup = BeautifulSoup(html, 'lxml')

        # Find ALL YouTube links
        print("=== ALL YOUTUBE LINKS ===\n")
        youtube_links = soup.find_all('a', href=lambda x: x and ('youtube.com' in x or 'youtu.be' in x))

        for i, link in enumerate(youtube_links, 1):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            classes = link.get('class', [])

            print(f"Link #{i}:")
            print(f"  URL: {href}")
            print(f"  Text: {text}")
            print(f"  Classes: {classes}")

            # Parent info
            parent = link.parent
            if parent:
                print(f"  Parent: <{parent.name}> class={parent.get('class', [])}")

            print()

        # Try specific selectors
        print("\n=== TESTING SELECTORS ===\n")

        selectors = [
            'a[href*="youtube.com/watch"]',
            'a[href*="youtu.be/"]',
            'a.playIcon[href*="youtube"]',
            'div.trackDetails a[href*="youtube"]',
            'iframe[src*="youtube"]',
        ]

        for selector in selectors:
            elements = soup.select(selector)
            print(f"{selector}: {len(elements)} found")
            if elements:
                for elem in elements[:2]:  # Show first 2
                    if elem.name == 'iframe':
                        print(f"  -> {elem.get('src', '')[:100]}")
                    else:
                        print(f"  -> {elem.get('href', '')[:100]}")

    finally:
        await scraper.aclose()


if __name__ == "__main__":
    asyncio.run(main())
