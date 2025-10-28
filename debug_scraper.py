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

        # Check for access denied
        if '403' in html or 'Access Denied' in html or 'Forbidden' in html:
            print("⚠️  ACCESS DENIED (403)")
            print("    The request was blocked.")
            return

        # Look for track results
        track_results = soup.select('li.trackName')
        print(f"  - Found {len(track_results)} elements with class 'trackName'")

        track_links = soup.select('li.trackName a')
        print(f"  - Found {len(track_links)} track links")

        if track_links:
            print("\n4. Found tracks:")
            print("-" * 80)
            for i, link in enumerate(track_links[:5], 1):  # Show first 5
                track_title = link.get_text(strip=True)
                track_href = link.get('href', '')
                print(f"  {i}. {track_title}")
                print(f"     URL: {track_href}")
        else:
            print("\n⚠️  NO TRACK RESULTS FOUND")
            print("    Possible reasons:")
            print("    1. Page structure has changed")
            print("    2. Search returned no results")
            print("    3. JavaScript-rendered content (not in static HTML)")
            print("    4. Still being blocked by anti-bot")

            # Look for any links
            all_links = soup.find_all('a', limit=10)
            print(f"\n    Found {len(soup.find_all('a'))} total links on page")
            if all_links:
                print("    First 10 links:")
                for i, link in enumerate(all_links[:10], 1):
                    print(f"      {i}. {link.get_text(strip=True)[:50]} - {link.get('href', '')[:50]}")

        # Check for specific CSS classes
        print("\n5. Checking for other common classes:")
        print("-" * 80)
        classes_to_check = ['.trackItem', '.sampleEntry', '.searchResult', '.result', '.track']
        for css_class in classes_to_check:
            elements = soup.select(css_class)
            print(f"  - {css_class}: {len(elements)} found")

        # Save HTML to file for inspection
        with open('/tmp/whosampled_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n6. Full HTML saved to: /tmp/whosampled_debug.html")
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
