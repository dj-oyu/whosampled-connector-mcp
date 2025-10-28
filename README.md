# whosampled-connector

WhoSampledで検索して結果を返すMCPサーバー

アーティスト名、曲名などの文字列を受け取ってWhoSampled?で検索を実行し、その曲のサンプリングソースやカバー音源などを発見するためのMCPサーバーです。希望に応じてYouTubeのリンクも返します。

## ✅ Anti-Bot Solution Implemented

**This project now uses Playwright headless browser to bypass WhoSampled's anti-bot protection.** The scraper has been rewritten to use a real browser instead of HTTP requests.

**Status**: Implementation complete. Ready for testing on local machines with residential IPs.

⚠️ **Note**: Cloud/datacenter IPs may still be blocked. Test from your local development environment.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dj-oyu/whosampled-connector-.git
cd whosampled-connector-

# Install the package
pip install -e .

# Run the MCP server
python -m whosampled_connector

# Or run the example usage
python example_usage.py
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

```bash
# Install dependencies
pip install -e .

# Install Playwright browser (Chromium)
playwright install chromium

# For development
pip install -e ".[dev]"
```

## Usage

### Running the MCP Server

```bash
python -m whosampled_connector
```

The server will start and listen for MCP protocol messages on stdin/stdout.

### Example Usage

See `example_usage.py` for sample client interactions. Run it with:

```bash
python example_usage.py
```

### Available Tools

#### 1. search_track
アーティスト名と曲名でWhoSampledを検索し、基本情報とURLを返します。

**Input:**
```json
{
  "artist": "Daft Punk",
  "track": "Harder Better Faster Stronger"
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
アーティスト名と曲名で検索し、サンプリング、カバー、リミックスの詳細情報を取得します。

**Input:**
```json
{
  "artist": "Kanye West",
  "track": "Stronger",
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

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=whosampled_connector --cov-report=html

# Run specific test file
pytest tests/test_scraper.py

# Run specific test
pytest tests/test_scraper.py::test_search_track_success

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Test Structure

- `tests/test_scraper.py` - Unit tests for the WhoSampled scraper
- `tests/test_server.py` - Integration tests for MCP server tools
- `tests/test_e2e.py` - End-to-end workflow tests
- `tests/conftest.py` - Shared test fixtures and configuration

## License

See LICENSE file for details.
