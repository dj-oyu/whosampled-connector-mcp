# whosampled-connector

WhoSampledで検索して結果を返すMCPサーバー

アーティスト名、曲名などの文字列を受け取ってWhoSampled?で検索を実行し、その曲のサンプリングソースやカバー音源などを発見するためのMCPサーバーです。希望に応じてYouTubeのリンクも返します。

## Features

- アーティスト名と曲名でWhoSampledを検索
- サンプリング情報の取得（この曲がサンプリングした曲、この曲をサンプリングした曲）
- カバー情報の取得（この曲のカバー、この曲がカバーした曲）
- リミックス情報の取得
- オプションでYouTubeリンクの取得

## Installation

```bash
# Install dependencies
pip install -e .

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

```bash
# Run tests
pytest

# Install in editable mode
pip install -e ".[dev]"
```

## License

See LICENSE file for details.
