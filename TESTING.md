# Testing Guide

## Automated Tests

### Current Test Status (Post-Playwright Migration)

Since the scraper now uses Playwright headless browser instead of HTTP requests:

✅ **Working Tests** (12 tests):
- `tests/test_server.py` - All MCP server tool tests pass
- These tests mock the scraper, so they work independently of the implementation

❌ **Requires Update** (16 tests):
- `tests/test_scraper.py` - Uses httpx_mock, incompatible with Playwright
- `tests/test_e2e.py` - Uses httpx_mock, incompatible with Playwright

These tests need to be rewritten to mock Playwright instead of httpx, or converted to integration tests.

### Running Tests

```bash
# Run working tests only
pytest tests/test_server.py -v

# Run all tests (some will fail)
pytest -v

# Skip failing tests
pytest -v -k "not scraper and not e2e"
```

## Verifying Mock HTML Against Live Site

Since WhoSampled uses anti-bot protection, automated verification is not possible. To manually verify that our mock HTML matches the actual site structure:

### Step 1: Check Search Results Page

1. Open your browser and navigate to:
   ```
   https://www.whosampled.com/search/?q=Daft+Punk+Harder+Better+Faster+Stronger
   ```

2. Open DevTools (F12) and inspect the search results

3. Verify the following structure exists:
   ```html
   <li class="trackName">
     <a href="/Artist-Name/Track-Name/">Track Title</a>
     <span class="trackArtist">Artist Name</span>
   </li>
   ```

### Step 2: Check Track Details Page

1. Click on a track from search results

2. Inspect the page structure and verify these elements:

   **Track Title:**
   ```html
   <h1 class="trackName">Track Name</h1>
   ```

   **YouTube Link:**
   ```html
   <a href="https://www.youtube.com/watch?v=...">YouTube</a>
   ```

   **Sections:**
   ```html
   <section id="samples">...</section>
   <section id="was-sampled">...</section>
   <section id="covers">...</section>
   <section id="was-covered">...</section>
   <section id="remixes">...</section>
   <section id="was-remixed">...</section>
   ```

   **Track Items:**
   ```html
   <div class="trackItem">
     <a class="trackName" href="...">Track Name</a>
     <span class="trackArtist">Artist Name</span>
   </div>
   ```

### Step 3: Update Tests if Needed

If the actual HTML structure differs from what's described above, update the mock fixtures in `tests/conftest.py`:

- `mock_search_html` - for search results
- `mock_track_details_html` - for track detail pages

### Current Selector Usage

Our scraper uses these CSS selectors:

**Search Results:**
- `li.trackName a` - track links
- `.trackArtist` - artist names

**Track Details:**
- `h1.trackName, h1` - track title
- `a[href*="youtube.com"], a[href*="youtu.be"]` - YouTube links
- `section#samples`, `section#was-sampled`, etc. - content sections
- `.trackItem, .sampleEntry, .coverEntry, .remixEntry, li` - track entries
- `a.trackName, a[href*="/sample/"]` - track links in sections
- `.trackArtist, .artistName` - artist names in sections

## Test Coverage

- **test_scraper.py** - 8 tests covering scraper functionality
- **test_server.py** - 11 tests covering MCP server tools
- **test_e2e.py** - 9 tests covering end-to-end workflows

Total: 28 tests
