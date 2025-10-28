"""
Example client to demonstrate MCP server usage.
This simulates how an MCP client would interact with the server.
"""
import asyncio
import json
from whosampled_connector.server import app


async def simulate_client():
    """Simulate client interactions with the MCP server."""
    print("=== MCP Server Example Usage ===\n")
    
    # Example 1: Search for a track
    print("Example 1: Search for a track")
    print("-" * 40)
    print("Input: search_track")
    print('Arguments: {"artist": "Daft Punk", "track": "Harder Better Faster Stronger"}')
    print()
    
    # Example 2: Get track samples with YouTube links
    print("Example 2: Get track details with YouTube links")
    print("-" * 40)
    print("Input: get_track_samples")
    print('Arguments: {')
    print('  "artist": "Kanye West",')
    print('  "track": "Stronger",')
    print('  "include_youtube": true')
    print('}')
    print()
    
    # Example 3: Get details by URL
    print("Example 3: Get track details by URL")
    print("-" * 40)
    print("Input: get_track_details_by_url")
    print('Arguments: {')
    print('  "url": "https://www.whosampled.com/sample/...",')
    print('  "include_youtube": false')
    print('}')
    print()
    
    print("\nNote: This server requires internet access to fetch data from WhoSampled.")
    print("In a real MCP client (like Claude Desktop or Cursor), these tools would")
    print("be available for the AI to use when searching for music samples and covers.")


if __name__ == "__main__":
    asyncio.run(simulate_client())
