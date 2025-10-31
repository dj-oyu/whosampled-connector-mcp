# whosampled-connector

WhoSampledで検索して結果を返すMCPサーバー

アーティスト名、曲名などの文字列を受け取ってWhoSampled?で検索を実行し、その曲のサンプリングソースやカバー音源などを発見するためのMCPサーバーです。希望に応じてYouTubeのリンクも返します。

## ✅ Anti-Bot Solution Implemented

**This project now uses Playwright headless browser to bypass WhoSampled's anti-bot protection.** The scraper has been rewritten to use a real browser instead of HTTP requests.

**Status**: Implementation complete. Ready for testing on local machines with residential IPs.

⚠️ **Note**: Cloud/datacenter IPs may still be blocked. Test from your local development environment.

## Quick Start

### Using uvx (Easiest - No Installation Required)

```bash
# First, install Playwright browsers (one-time setup)
uvx playwright install chromium

# Then run the MCP server directly from GitHub
uvx --from git+https://github.com/dj-oyu/whosampled-connector-mcp whosampled-connector
```

**Note**: The Playwright browser installation is separate from the package and only needs to be done once.

### Using uv (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/dj-oyu/whosampled-connector-mcp.git
cd whosampled-connector-mcp

# Sync dependencies (creates venv and installs all dependencies including dev tools)
uv sync

# Install Playwright browser
uv run playwright install chromium

# Run the MCP server
uv run whosampled-connector
# or
uv run python -m whosampled_connector
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/dj-oyu/whosampled-connector-mcp.git
cd whosampled-connector-mcp

# Install the package
pip install -e .

# Install Playwright browser
playwright install chromium

# Run the MCP server
whosampled-connector
# or
python -m whosampled_connector
```

## Features

- アーティスト名と曲名でWhoSampledを検索
- サンプリング情報の取得（この曲がサンプリングした曲、この曲をサンプリングした曲）
- カバー情報の取得（この曲のカバー、この曲がカバーした曲）
- リミックス情報の取得
- オプションでYouTubeリンクの取得

## Installation

**Requirements:**
- Python 3.10 or higher
- Internet access (for fetching data from WhoSampled)
- Playwright browser binaries

**Quick Option:** If you just want to try it out without cloning, see [Using uvx](#using-uvx-easiest---no-installation-required) in Quick Start.

### Option 1: Using uv (Recommended for Development)

```bash
# Install uv if you haven't already
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync all dependencies (creates venv and installs dev dependencies automatically)
uv sync

# Install Playwright browser (Chromium)
uv run playwright install chromium

# Note: uv sync automatically installs both runtime and dev dependencies (pytest, etc.)
```

### Option 2: Using pip

```bash
# Install dependencies
pip install -e .

# Install Playwright browser (Chromium)
playwright install chromium

# For development
pip install -e ".[dev]"
```

### Quick Test (Verify Installation)

After installation, test the scraper directly:

**With uv:**
```bash
uv run python -c "
from whosampled_connector.scraper import WhoSampledScraper
import asyncio

async def test():
    scraper = WhoSampledScraper()
    result = await scraper.search_track('Daft Punk', 'One More Time')
    print(result)
    await scraper.aclose()

asyncio.run(test())
"
```

**With pip:**
```bash
python -c "
from whosampled_connector.scraper import WhoSampledScraper
import asyncio

async def test():
    scraper = WhoSampledScraper()
    result = await scraper.search_track('Daft Punk', 'One More Time')
    print(result)
    await scraper.aclose()

asyncio.run(test())
"
```

If successful, you should see track information. If you get a 403 error, try:
- Testing from a different network (residential, not datacenter/cloud)
- Using a VPN
- Checking if your IP is blocked

## Usage

### Running the MCP Server

**With uvx (no installation):**
```bash
# First time only: install Playwright browsers
uvx playwright install chromium

# Run the server
uvx --from git+https://github.com/dj-oyu/whosampled-connector-mcp whosampled-connector
```

**With uv:**
```bash
uv run whosampled-connector
# or
uv run python -m whosampled_connector
```

**With pip:**
```bash
whosampled-connector
# or
python -m whosampled_connector
```

The server will start and listen for MCP protocol messages on stdin/stdout.

### Using with Claude Desktop App

To use this MCP server with Claude Desktop app, see the [Claude Desktop Configuration Guide](CLAUDE_DESKTOP_CONFIG.md) for detailed setup instructions.

**Quick Configuration (Windows example):**
```json
{
  "mcpServers": {
    "whosampled-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/dj-oyu/whosampled-connector-mcp",
        "whosampled-connector"
      ]
    }
  }
}
```

See the full guide for macOS/Linux configurations and troubleshooting.

### Example Usage

See `example_usage.py` for sample client interactions. Run it with:

```bash
python example_usage.py
```

### Available Tools

#### 1. search_track
検索クエリ（アーティスト名、曲名、または両方）でWhoSampledを検索し、基本情報とURLを返します。

**Input:**
```json
{
  "query": "Daft Punk Harder Better Faster Stronger"
}
```

または曲名のみ:
```json
{
  "query": "team tomodachi"
}
```

**Output:**
```
Track found on WhoSampled:

Title: Harder, Better, Faster, Stronger
Artist: Daft Punk
URL: https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/

Use get_track_samples or get_track_details_by_url to get detailed information about samples, covers, and remixes.
```

#### 2. get_track_samples
検索クエリ（アーティスト名、曲名、または両方）で検索し、サンプリング、カバー、リミックスの詳細情報を取得します。

**Input:**
```json
{
  "query": "Kanye West Stronger",
  "include_youtube": true
}
```

**Output:**
```
Track: Stronger

URL: https://www.whosampled.com/Kanye-West/Stronger/

YouTube: https://www.youtube.com/watch?v=...

=== SAMPLES (Tracks sampled by this song) ===
  • Harder, Better, Faster, Stronger by Daft Punk
    https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/

=== SAMPLED BY (Tracks that sampled this song) ===
  • [Various tracks that sampled Stronger]
    
=== COVERED BY (Artists who covered this song) ===
  • [Cover versions]
```

#### 3. get_track_details_by_url
WhoSampledのURLから直接、詳細情報を取得します。

**Input:**
```json
{
  "url": "https://www.whosampled.com/sample/123456/...",
  "include_youtube": false
}
```

**Output:**
Similar to get_track_samples, but retrieves information directly from the provided URL.

### Configuration for MCP Clients

Claude DesktopやCursorなどのMCPクライアントで使用する場合、設定ファイルに以下を追加してください：

#### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "whosampled": {
      "command": "python",
      "args": ["-m", "whosampled_connector"],
      "cwd": "/path/to/whosampled-connector-"
    }
  }
}
```

Windows: `%APPDATA%\Claude\claude_desktop_config.json`

#### Cursor

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "whosampled": {
      "command": "python",
      "args": ["-m", "whosampled_connector"]
    }
  }
}
```

## Development

### Installation for Development

**With uv (Recommended):**
```bash
# Sync dependencies (includes dev dependencies by default)
uv sync
```

**With pip:**
```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

This project has two types of tests:

**Unit Tests (Fast, Mocked)** - 33 tests:
- Test server and scraper logic with mocked data
- Do not access real WhoSampled
- Run in ~0.1 seconds

**Integration Tests (Slow, Real)** - 16 tests:
- Access real WhoSampled website
- Verify HTML structure and CSS selectors
- Require Playwright browsers installed
- Run in ~30-60 seconds
- Includes performance tests comparing with/without YouTube links

**Quick Test (Unit Tests Only - Recommended):**
```bash
# With uv
uv run pytest -v -m "not integration"

# With pip
pytest -v -m "not integration"

# Result: 33 passed in ~0.1s
```

**Full Test Suite (Unit + Integration):**
```bash
# First, install Playwright browsers (one-time setup)
uv run playwright install chromium

# Run all tests
uv run pytest -v

# Result: 49 passed in ~30-60s
```

**Integration Tests Only (includes all performance tests):**
```bash
# All integration tests including Team Tomodachi performance tests
uv run pytest -v -m "integration"

# Result: 16 integration tests including:
#  - Basic search and retrieval tests
#  - YouTube link tests
#  - Team Tomodachi specific tests with performance metrics
```

**Team Tomodachi Performance Tests:**
```bash
# Run only Team Tomodachi tests (performance + verification)
uv run pytest -v -m "integration" -k "team_tomodachi"

# These tests verify:
#  - Expected YouTube video IDs (c1UaGJlsw5g, 0LEc7es4_rE, acw_iA5IgTQ, 5DmLGUCmxD0)
#  - Performance comparison (with vs without YouTube links)
#  - YouTube link coverage for all track sections
```

**Specific Test Files:**
```bash
# Server tests (fast)
uv run pytest tests/test_server.py -v

# Scraper tests (fast, mocked)
uv run pytest tests/test_scraper.py -v

# Integration tests (slow, real WhoSampled access)
uv run pytest tests/test_e2e.py -v
```

**With Coverage:**
```bash
uv run pytest --cov=whosampled_connector --cov-report=html -m "not integration"
```

See [TESTING.md](TESTING.md) for more details.

### Test Structure

- `tests/test_scraper.py` - Unit tests for scraper (14 tests, mocked)
- `tests/test_server.py` - Unit tests for MCP server tools (19 tests, mocked)
- `tests/test_e2e.py` - Integration tests (16 tests, real WhoSampled access)
  - Includes Team Tomodachi performance benchmarks
  - Verifies YouTube link fetching for all related tracks
- `tests/conftest.py` - Shared test fixtures and configuration

**Total**: 49 tests (33 unit + 16 integration)

## License

See LICENSE file for details.
