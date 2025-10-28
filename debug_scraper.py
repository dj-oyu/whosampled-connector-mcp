"""Debug script to see what's actually being fetched from WhoSampled."""
import asyncio
from whosampled_connector.scraper import WhoSampledScraper
from bs4 import BeautifulSoup


async def analyze_search_page(scraper, query, save_file=None):
    """Analyze a search page and extract tracks by section."""
    search_url = f"https://www.whosampled.com/search/?q={query.replace(' ', '+')}"

    print(f"\n{'=' * 80}")
    print(f"Testing query: '{query}'")
    print(f"URL: {search_url}")
    print(f"{'=' * 80}")

    try:
        html = await scraper._fetch_page(search_url)

        print(f"\n✓ Page fetched successfully!")
        print(f"  HTML Length: {len(html)} characters")

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        # Check page title
        title = soup.find('title')
        print(f"  Page Title: {title.string if title else 'Not found'}")

        # Check for Cloudflare challenge
        if 'Checking your browser' in html or 'cf-browser-verification' in html:
            print("\n⚠️  CLOUDFLARE CHALLENGE DETECTED!")
            print("    The page is showing a browser verification challenge.")
            return None

        # Analyze sections
        print(f"\n{'─' * 80}")
        print("SECTION ANALYSIS:")
        print(f"{'─' * 80}")

        results = {
            'top_hit': None,
            'tracks': [],
            'connections': []
        }

        # Look for "Top hit" section
        print("\n1. TOP HIT Section:")
        print("   " + "-" * 76)
        top_hit_link = soup.select_one('a.trackTitle')
        if top_hit_link:
            title = top_hit_link.get_text(strip=True)
            href = top_hit_link.get('href', '')
            # Try to find artist
            parent = top_hit_link.parent
            artist = "Unknown"
            if parent:
                links = parent.find_all('a')
                if len(links) > 1:
                    artist = links[1].get_text(strip=True)

            results['top_hit'] = {
                'title': title,
                'artist': artist,
                'url': href
            }
            print(f"   ✓ Found: {title}")
            print(f"     Artist: {artist}")
            print(f"     URL: {href}")
        else:
            print("   ✗ No top hit found")

        # Look for "Tracks" section
        print("\n2. TRACKS Section:")
        print("   " + "-" * 76)
        track_name_links = soup.select('a.trackName')
        if track_name_links:
            print(f"   ✓ Found {len(track_name_links)} tracks")
            for i, link in enumerate(track_name_links[:5], 1):  # Show first 5
                title = link.get_text(strip=True)
                href = link.get('href', '')
                # Try to find artist
                parent = link.parent
                artist = "Unknown"
                if parent:
                    links = parent.find_all('a')
                    if len(links) > 1:
                        artist = links[1].get_text(strip=True)

                track_info = {
                    'title': title,
                    'artist': artist,
                    'url': href
                }
                results['tracks'].append(track_info)
                print(f"   {i}. {title}")
                print(f"      Artist: {artist}")
                print(f"      URL: {href}")

            if len(track_name_links) > 5:
                print(f"   ... and {len(track_name_links) - 5} more")
        else:
            print("   ✗ No tracks found")

        # Look for "Connections" section - this might be sampled_in relationships
        print("\n3. CONNECTIONS Section:")
        print("   " + "-" * 76)
        # Look for elements that might indicate connections (samples, covers, remixes)
        list_entries = soup.select('.listEntry')
        if list_entries:
            print(f"   ✓ Found {len(list_entries)} list entries (potential connections)")
            for i, entry in enumerate(list_entries[:5], 1):
                text = entry.get_text(strip=True)[:100]
                links = entry.find_all('a')
                if links:
                    main_link = links[0]
                    title = main_link.get_text(strip=True)
                    href = main_link.get('href', '')

                    connection_info = {
                        'title': title,
                        'url': href,
                        'context': text[:100]
                    }
                    results['connections'].append(connection_info)
                    print(f"   {i}. {title}")
                    print(f"      URL: {href}")
                    print(f"      Context: {text[:80]}...")

            if len(list_entries) > 5:
                print(f"   ... and {len(list_entries) - 5} more")
        else:
            print("   ✗ No connections found")

        # Save HTML if requested
        if save_file:
            with open(save_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n   💾 HTML saved to: {save_file}")

        return results

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_search_track_method(scraper, artist, track):
    """Test the search_track method directly."""
    print(f"\n{'=' * 80}")
    print(f"Testing search_track() method")
    print(f"Artist: '{artist}', Track: '{track}'")
    print(f"{'=' * 80}")

    try:
        result = await scraper.search_track(artist, track)
        if result:
            print(f"\n✓ SUCCESS!")
            print(f"  Title: {result.get('title')}")
            print(f"  Artist: {result.get('artist')}")
            print(f"  URL: {result.get('url')}")
            return result
        else:
            print(f"\n✗ search_track() returned None")
            return None
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def debug_fetch():
    """Debug the fetch process to see what's actually returned."""
    scraper = WhoSampledScraper()

    print("=" * 80)
    print("DEBUG: Testing WhoSampled scraper")
    print("=" * 80)

    try:
        # Test case 1: Daft Punk - One More Time
        print("\n" + "█" * 80)
        print("TEST CASE 1: Daft Punk - One More Time")
        print("█" * 80)

        await analyze_search_page(
            scraper,
            "Daft Punk One More Time",
            save_file='/tmp/whosampled_debug_daftpunk.html'
        )

        await test_search_track_method(scraper, 'Daft Punk', 'One More Time')

        # Test case 2: Yuki Chiba
        print("\n\n" + "█" * 80)
        print("TEST CASE 2: Yuki Chiba (Artist search)")
        print("Expected: Original tracks and covers")
        print("█" * 80)

        await analyze_search_page(
            scraper,
            "yuki chiba",
            save_file='/tmp/whosampled_debug_yukichiba.html'
        )

        # Test case 3: Yuki Chiba with a specific track if known
        print("\n\n" + "█" * 80)
        print("TEST CASE 3: Testing search_track() with Yuki Chiba")
        print("█" * 80)

        # Try searching for yuki chiba as artist with empty track name
        result = await test_search_track_method(scraper, 'yuki chiba', '')

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await scraper.aclose()
        print("\n" + "=" * 80)
        print("DEBUG: Complete")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(debug_fetch())
