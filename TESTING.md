# Testing Guide

## Test Architecture

This project has two types of tests:

### 1. Unit Tests (Fast, Mocked)
- **test_server.py** - 19 tests covering MCP server tools
- **test_scraper.py** - 14 tests covering scraper functionality
- Use `unittest.mock.patch` to mock `_fetch_page` method
- Do not access real WhoSampled website
- Run quickly (~0.1s total)
- ✅ **Always passing** (33/33 tests)

### 2. Integration Tests (Slow, Real Access)
- **test_e2e.py** - 16 tests covering end-to-end workflows
- Actually access real WhoSampled website using Playwright
- Verify HTML structure hasn't changed
- Detect CSS selector issues
- Run slowly (~30-60s total)
- Require Playwright browsers installed
- **Includes performance benchmarks:**
  - Team Tomodachi track with YouTube links
  - Performance comparison (with vs without YouTube links)
  - YouTube link coverage verification
- ✅ **Pass when Playwright browsers are available**

## Running Tests

### Quick Test (Unit Tests Only)
```bash
# Run only unit tests (recommended for development)
uv run pytest -v -m "not integration"

# Result: 33 passed in ~0.1s
```

### Full Test Suite (Unit + Integration)
```bash
# First, install Playwright browsers (one-time setup)
uv run playwright install chromium

# Run all tests including integration tests
uv run pytest -v

# Result: 49 passed in ~30-60s
```

### Integration Tests Only (includes performance tests)
```bash
# Run all integration tests including Team Tomodachi performance tests
uv run pytest -v -m "integration"

# Result: 16 integration tests
```

### Team Tomodachi Performance Tests
```bash
# Run only Team Tomodachi tests with performance metrics
uv run pytest -v -m "integration" -k "team_tomodachi" -s

# Output includes:
#  - Elapsed time for fetching track with YouTube links
#  - Expected video IDs verification (c1UaGJlsw5g, 0LEc7es4_rE, acw_iA5IgTQ, 5DmLGUCmxD0)
#  - Performance comparison (with vs without YouTube links)
#  - Slowdown factor
#  - YouTube link statistics
```

### Specific Test Files
```bash
uv run pytest tests/test_server.py -v
uv run pytest tests/test_scraper.py -v
uv run pytest tests/test_e2e.py -v
```

## Integration Test Requirements

Integration tests require:
1. **Playwright browsers installed**: `uv run playwright install chromium`
2. **Network access** to https://www.whosampled.com
3. **Residential IP** (some cloud IPs may be blocked)

If integration tests fail due to network restrictions, you can still verify the unit tests pass.

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
   <!-- Top hit result -->
   <a class="trackTitle" href="/Artist-Name/Track-Name/">Track Title</a>
   <a href="/Artist-Name/">Artist Name</a>

   <!-- Other track results -->
   <a class="trackName" href="/Artist-Name/Track-Name/">Track Title</a>
   <a href="/Artist-Name/">Artist Name</a>
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
- `a.trackTitle` - top hit track link
- `a.trackName` - other track links
- Artist names extracted from parent container's second link

**Track Details:**
- `h1.trackName, h1` - track title
- `a[href*="youtube.com"], a[href*="youtu.be"]` - YouTube links
- `section#samples`, `section#was-sampled`, etc. - content sections
- `.trackItem, .sampleEntry, .coverEntry, .remixEntry, li` - track entries
- `a.trackName, a[href*="/sample/"]` - track links in sections
- `.trackArtist, .artistName` - artist names in sections

## Test Coverage

- **test_scraper.py** - 14 tests covering scraper functionality
  - Basic search and track details
  - YouTube link extraction
  - Connection extraction (with and without YouTube)
- **test_server.py** - 19 tests covering MCP server tools
  - All MCP tool endpoints
  - Response formatting
  - Error handling
- **test_e2e.py** - 16 tests covering end-to-end workflows
  - Basic integration tests (13 tests)
  - Team Tomodachi performance tests (3 tests):
    - YouTube link verification with expected video IDs
    - Performance comparison (with/without YouTube links)
    - All sections coverage verification

Total: 49 tests (all passing ✅)

### Performance Test Details

The Team Tomodachi performance tests provide detailed metrics:

1. **test_integration_team_tomodachi_with_youtube_links**
   - Verifies all expected YouTube video IDs are present
   - Checks performance (<60s timeout)
   - Reports found vs missing video IDs

2. **test_integration_team_tomodachi_performance**
   - Compares fetch time with and without YouTube links
   - Reports slowdown factor
   - Ensures both modes complete in reasonable time

3. **test_integration_team_tomodachi_all_sections**
   - Counts total YouTube links found
   - Reports which sections exist (SAMPLED BY, COVERED BY, REMIXED BY)
   - Verifies YouTube link coverage
