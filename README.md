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

### Available Tools

#### 1. search_track
アーティスト名と曲名でWhoSampledを検索し、基本情報とURLを返します。

```json
{
  "artist": "Daft Punk",
  "track": "Harder Better Faster Stronger"
}
```

#### 2. get_track_samples
アーティスト名と曲名で検索し、サンプリング、カバー、リミックスの詳細情報を取得します。

```json
{
  "artist": "Daft Punk",
  "track": "Harder Better Faster Stronger",
  "include_youtube": true
}
```

#### 3. get_track_details_by_url
WhoSampledのURLから直接、詳細情報を取得します。

```json
{
  "url": "https://www.whosampled.com/sample/...",
  "include_youtube": false
}
```

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
