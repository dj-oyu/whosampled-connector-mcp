#!/usr/bin/env python3
"""Test script for the new get_youtube_links endpoint."""
import asyncio
from src.whosampled_connector.scraper import WhoSampledScraper


async def test_youtube_links():
    """Test the get_youtube_links_from_search method."""
    scraper = WhoSampledScraper()

    try:
        print("Testing YouTube link extraction...")
        print("=" * 60)

        # Test with a popular track
        artist = "Daft Punk"
        track = "One More Time"

        print(f"\nSearching for: '{track}' by '{artist}'")
        print("-" * 60)

        result = await scraper.get_youtube_links_from_search(artist, track, max_per_section=2)

        if "error" in result:
            print(f"Error: {result['error']}")
            return

        print(f"\nQuery: {result.get('query')}")
        print()

        # Display Top Hit
        if result.get("top_hit"):
            print("=== TOP HIT ===")
            for track_info in result["top_hit"]:
                print(f"  • {track_info['track']} by {track_info['artist']}")
                print(f"    WhoSampled: {track_info['url']}")
                print(f"    YouTube: {track_info.get('youtube_url', 'Not found')}")
                print()

        # Display Connections
        if result.get("connections"):
            print("=== CONNECTIONS ===")
            for track_info in result["connections"]:
                print(f"  • {track_info['track']} by {track_info['artist']}")
                print(f"    WhoSampled: {track_info['url']}")
                print(f"    YouTube: {track_info.get('youtube_url', 'Not found')}")
                print()

        # Display Tracks
        if result.get("tracks"):
            print("=== TRACKS ===")
            for track_info in result["tracks"]:
                print(f"  • {track_info['track']} by {track_info['artist']}")
                print(f"    WhoSampled: {track_info['url']}")
                print(f"    YouTube: {track_info.get('youtube_url', 'Not found')}")
                print()

        print("=" * 60)
        print("Test completed successfully!")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await scraper.aclose()


if __name__ == "__main__":
    asyncio.run(test_youtube_links())
