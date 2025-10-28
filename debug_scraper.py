"""Debug script to see what's actually being fetched from WhoSampled."""
import asyncio
from whosampled_connector.scraper import WhoSampledScraper
from bs4 import BeautifulSoup


async def debug_fetch():
    """Debug the fetch process to see what's actually returned."""
    scraper = WhoSampledScraper()

    print("=" * 80)
    print("DEBUG: Testing WhoSampled scraper")
    print("=" * 80)

    try:
        # Test search
        query = "Daft Punk One More Time"
        search_url = f"https://www.whosampled.com/search/?q={query.replace(' ', '+')}"

        print(f"\n1. Fetching URL: {search_url}")
        print("-" * 80)

        html = await scraper._fetch_page(search_url)

        print(f"✓ Page fetched successfully!")
        print(f"  HTML Length: {len(html)} characters")
        print(f"  First 500 characters:")
        print("-" * 80)
        print(html[:500])
        print("-" * 80)

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        # Check page title
        title = soup.find('title')
        print(f"\n2. Page Title: {title.string if title else 'Not found'}")

        # Look for various elements
        print("\n3. Looking for expected elements:")
        print("-" * 80)

        # Check for Cloudflare challenge
        if 'Checking your browser' in html or 'cf-browser-verification' in html:
            print("⚠️  CLOUDFLARE CHALLENGE DETECTED!")
            print("    The page is showing a browser verification challenge.")
            return

        # Look for track results with updated selectors
        track_title_links = soup.select('a.trackTitle')
        track_name_links = soup.select('a.trackName')
        print(f"  - Found {len(track_title_links)} elements with 'a.trackTitle'")
        print(f"  - Found {len(track_name_links)} elements with 'a.trackName'")

        # Try the actual search_track method FIRST
        print("\n4. Testing actual search_track() method:")
        print("-" * 80)
        result = await scraper.search_track('Daft Punk', 'One More Time')
        if result:
            print(f"  ✓ SUCCESS!")
            print(f"    Title: {result.get('title')}")
            print(f"    Artist: {result.get('artist')}")
            print(f"    URL: {result.get('url')}")
        else:
            print(f"  ✗ search_track() returned None")
            print(f"    This means CSS selector isn't matching correctly")

            print("\n5. Debugging selector issue...")
            print("-" * 80)

            # Try different selectors
            alternatives = [
                ('a.trackTitle', 'Links with class trackTitle'),
                ('a.trackName', 'Links with class trackName'),
                ('.trackName', 'Any element with class trackName'),
                ('li a', 'Any link in a list item'),
                ('.listEntry', 'Elements with class listEntry'),
            ]

            for selector, description in alternatives:
                elements = soup.select(selector)
                print(f"  - {selector:20} ({description}): {len(elements)} found")
                if elements and len(elements) > 0:
                    first = elements[0]
                    print(f"    First element: {first.get_text(strip=True)[:100]}")
                    print(f"    First href: {first.get('href', 'N/A')[:100]}")

            # Look for any links
            all_links = soup.find_all('a', limit=20)
            print(f"\n    Found {len(soup.find_all('a'))} total links on page")
            if all_links:
                print("    First 20 links:")
                for i, link in enumerate(all_links[:20], 1):
                    text = link.get_text(strip=True)[:50]
                    href = link.get('href', '')[:50]
                    classes = link.get('class', [])
                    print(f"      {i}. {text} | {href} | classes: {classes}")

        # Save HTML to file for inspection
        with open('/tmp/whosampled_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n\n6. Full HTML saved to: /tmp/whosampled_debug.html")
        print("   You can inspect this file to see the actual page content.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await scraper.aclose()
        print("\n" + "=" * 80)
        print("DEBUG: Complete")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(debug_fetch())
