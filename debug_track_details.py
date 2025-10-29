"""Debug script to check track details page structure."""
import asyncio
from whosampled_connector.scraper import WhoSampledScraper
from bs4 import BeautifulSoup


async def debug_track_details():
    """Debug track details extraction."""
    scraper = WhoSampledScraper()

    # URL from user's request
    url = "https://www.whosampled.com/Yuki-Chiba/Team-Tomodachi/"

    print("=" * 80)
    print(f"Fetching: {url}")
    print("=" * 80)

    try:
        html = await scraper._fetch_page(url)
        soup = BeautifulSoup(html, 'lxml')

        print(f"\n✓ Page fetched: {len(html)} characters\n")

        # Check title
        title = soup.select_one('h1.trackName, h1')
        print(f"Title: {title.get_text(strip=True) if title else 'NOT FOUND'}\n")

        # Check for section IDs
        print("Checking for section IDs:")
        print("-" * 80)
        section_ids = ['samples', 'was-sampled', 'covers', 'was-covered', 'remixes', 'was-remixed']

        for section_id in section_ids:
            section = soup.find('section', {'id': section_id})
            if section:
                print(f"  ✓ Found section: #{section_id}")
                # Count entries
                entries = section.select('.trackItem, .sampleEntry, .coverEntry, .remixEntry, li')
                print(f"    Entries found: {len(entries)}")
                if entries:
                    first_entry_html = str(entries[0])[:200]
                    print(f"    First entry preview: {first_entry_html}...")
            else:
                print(f"  ✗ No section: #{section_id}")

        # Look for alternative section structures
        print("\n" + "=" * 80)
        print("Looking for alternative structures:")
        print("=" * 80)

        # Check all sections
        all_sections = soup.find_all('section')
        print(f"\nTotal sections found: {len(all_sections)}")
        for i, section in enumerate(all_sections[:10], 1):
            section_id = section.get('id', 'NO-ID')
            section_class = section.get('class', [])
            # Get section text preview
            text_preview = section.get_text(strip=True)[:100]
            print(f"  {i}. Section: id='{section_id}' class={section_class}")
            print(f"     Text: {text_preview}...")

            # Check for headers within section
            headers = section.find_all(['h2', 'h3', 'h4', 'div'], class_=['sectionHeader', 'section-header', 'header'])
            if headers:
                for header in headers:
                    print(f"     Header: {header.get_text(strip=True)}")

        # Look specifically for .section and .subsection
        print("\n" + "=" * 80)
        print("Analyzing .section and .subsection elements:")
        print("=" * 80)

        sections_by_class = soup.select('section.section, section.subsection')
        for i, section in enumerate(sections_by_class[:5], 1):
            section_class = section.get('class', [])
            # Get heading/title
            heading = section.find(['h2', 'h3', 'h4'])
            heading_text = heading.get_text(strip=True) if heading else "NO HEADING"

            # Count links
            links = section.find_all('a')

            print(f"\n  {i}. {section_class} - {heading_text}")
            print(f"     Links found: {len(links)}")

            # Show first few links
            for j, link in enumerate(links[:3], 1):
                link_text = link.get_text(strip=True)[:50]
                link_href = link.get('href', '')[:50]
                link_class = link.get('class', [])
                print(f"       {j}. {link_text} -> {link_href} (class={link_class})")

        # Check for common content patterns
        print("\n" + "=" * 80)
        print("Looking for keywords in page:")
        print("=" * 80)

        keywords = ['Contains samples', 'Sampled in', 'Covered by', 'Cover of', 'Remix of', 'Remixed by']
        for keyword in keywords:
            if keyword.lower() in html.lower():
                print(f"  ✓ Found keyword: '{keyword}'")
                # Try to find the element containing this
                elements = soup.find_all(string=lambda text: keyword.lower() in text.lower() if text else False)
                if elements:
                    print(f"    Occurrences: {len(elements)}")
                    for elem in elements[:2]:
                        parent = elem.parent
                        print(f"    Parent tag: {parent.name} class={parent.get('class', [])}")
            else:
                print(f"  ✗ Not found: '{keyword}'")

        # Check for divs with specific classes
        print("\nLooking for content containers:")
        containers = soup.select('.sectionHeader, .section-header, .list, .samplesList')
        print(f"  Found {len(containers)} potential containers")

        # Save HTML for manual inspection
        with open('/tmp/yuki_chiba_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n💾 Full HTML saved to: /tmp/yuki_chiba_debug.html")

        # Test actual method
        print("\n" + "=" * 80)
        print("Testing get_track_details():")
        print("=" * 80)
        result = await scraper.get_track_details(url, include_youtube=False)
        print(f"\nResult:")
        for key, value in result.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items")
                if value:
                    print(f"    First: {value[0]}")
            else:
                print(f"  {key}: {value}")

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
    asyncio.run(debug_track_details())
