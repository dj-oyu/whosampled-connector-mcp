"""
WhoSampled MCP Server
An MCP server for searching WhoSampled and discovering sampling sources, covers, and remixes.
"""

import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio

from .scraper import WhoSampledScraper


# Create server instance
app = Server("whosampled-connector")

# Create scraper instance
scraper = WhoSampledScraper()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_track",
            description="Find a track on WhoSampled. Use for queries like 'team tomodachi' (track only), 'chiba yuki' (artist only), or 'chiba yuki team tomodachi' (both). Use romaji for Japanese.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query: artist name, track name, or both (use romaji for Japanese)"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_track_samples",
            description="Discover what a song sampled, who sampled it, covers, and remixes. Use for: 'what did X sample?', 'find covers of X', 'who sampled X?'. Use romaji for Japanese.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query: artist name, track name, or both (use romaji for Japanese)"},
                    "include_youtube": {
                        "type": "boolean",
                        "description": "Whether to include YouTube links in the response",
                        "default": False,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_track_details_by_url",
            description="Get samples, covers, and remixes from a WhoSampled URL directly. Use when you already have the track's URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "WhoSampled track URL"},
                    "include_youtube": {
                        "type": "boolean",
                        "description": "Whether to include YouTube links in the response",
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_youtube_links",
            description="Get YouTube links from WhoSampled search results. Returns URLs for top matching tracks. Use romaji for Japanese.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query: artist name, track name, or both (use romaji for Japanese)"},
                    "max_per_section": {
                        "type": "integer",
                        "description": "Maximum number of tracks to get from each section (default: 3)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    if name == "search_track":
        query = arguments.get("query", "")

        if not query:
            return [TextContent(type="text", text="Error: Query is required")]

        result = await scraper.search_track(query)

        if result is None:
            return [
                TextContent(type="text", text=f"No results found for '{query}'")
            ]

        response = f"""Track found on WhoSampled:

Title: {result["title"]}
Artist: {result["artist"]}
URL: {result["url"]}

Use get_track_samples or get_track_details_by_url to get detailed information about samples, covers, and remixes.
"""

        return [TextContent(type="text", text=response)]

    elif name == "get_track_samples":
        query = arguments.get("query", "")
        include_youtube = arguments.get("include_youtube", False)

        if not query:
            return [
                TextContent(
                    type="text", text="Error: Query is required"
                )
            ]

        # First search for the track
        search_result = await scraper.search_track(query)

        if search_result is None:
            return [
                TextContent(
                    type="text", text=f"No results found for '{query}'"
                )
            ]

        # Get detailed information
        details = await scraper.get_track_details(search_result["url"], include_youtube)

        return [TextContent(type="text", text=_format_track_details(details))]

    elif name == "get_track_details_by_url":
        url = arguments.get("url", "")
        include_youtube = arguments.get("include_youtube", False)

        if not url:
            return [TextContent(type="text", text="Error: URL is required")]

        details = await scraper.get_track_details(url, include_youtube)

        return [TextContent(type="text", text=_format_track_details(details))]

    elif name == "get_youtube_links":
        query = arguments.get("query", "")
        max_per_section = arguments.get("max_per_section", 3)

        if not query:
            return [
                TextContent(
                    type="text", text="Error: Query is required"
                )
            ]

        result = await scraper.get_youtube_links_from_search(
            query, max_per_section
        )

        return [TextContent(type="text", text=_format_youtube_links(result))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def _format_youtube_links(result: dict) -> str:
    """Format YouTube links result into a readable string."""

    if "error" in result:
        return f"Error retrieving YouTube links: {result['error']}"

    lines = []
    lines.append(f"Search query: {result.get('query', 'N/A')}")
    lines.append("")

    # Top Hit section (highest priority)
    if result.get("top_hit"):
        lines.append("=== TOP HIT ===")
        for track in result["top_hit"]:
            lines.append(f"  • {track['track']} by {track['artist']}")
            lines.append(f"    WhoSampled: {track['url']}")
            if track.get("youtube_url"):
                lines.append(f"    YouTube: {track['youtube_url']}")
            else:
                lines.append("    YouTube: Not found")
        lines.append("")

    # Connections section
    if result.get("connections"):
        lines.append("=== CONNECTIONS ===")
        for track in result["connections"]:
            lines.append(f"  • {track['track']} by {track['artist']}")
            lines.append(f"    WhoSampled: {track['url']}")
            if track.get("youtube_url"):
                lines.append(f"    YouTube: {track['youtube_url']}")
            else:
                lines.append("    YouTube: Not found")
        lines.append("")

    # Tracks section
    if result.get("tracks"):
        lines.append("=== TRACKS ===")
        for track in result["tracks"]:
            lines.append(f"  • {track['track']} by {track['artist']}")
            lines.append(f"    WhoSampled: {track['url']}")
            if track.get("youtube_url"):
                lines.append(f"    YouTube: {track['youtube_url']}")
            else:
                lines.append("    YouTube: Not found")
        lines.append("")

    # Check if we have any content
    has_content = (
        result.get("top_hit") or result.get("connections") or result.get("tracks")
    )
    if not has_content:
        lines.append("No tracks found with YouTube links.")

    return "\n".join(lines)


def _format_track_details(details: dict) -> str:
    """Format track details into a readable string."""

    if "error" in details:
        return f"Error retrieving track details: {details['error']}"

    lines = []

    # Title
    if "title" in details:
        lines.append(f"Track: {details['title']}")
        lines.append("")

    # URL
    lines.append(f"URL: {details['url']}")
    lines.append("")

    # YouTube link
    if "youtube_url" in details:
        lines.append(f"YouTube: {details['youtube_url']}")
        lines.append("")

    # Samples (tracks this song sampled)
    if details.get("samples"):
        lines.append("=== SAMPLES (Tracks sampled by this song) ===")
        for sample in details["samples"]:
            lines.append(f"  • {sample['track']} by {sample['artist']}")
            lines.append(f"    {sample['url']}")
        lines.append("")

    # Sampled by (tracks that sampled this song)
    if details.get("sampled_by"):
        lines.append("=== SAMPLED BY (Tracks that sampled this song) ===")
        for track in details["sampled_by"]:
            lines.append(f"  • {track['track']} by {track['artist']}")
            lines.append(f"    {track['url']}")
        lines.append("")

    # Covers
    if details.get("covers"):
        lines.append("=== COVERS (Cover versions by this artist) ===")
        for cover in details["covers"]:
            lines.append(f"  • {cover['track']} by {cover['artist']}")
            lines.append(f"    {cover['url']}")
        lines.append("")

    # Covered by
    if details.get("covered_by"):
        lines.append("=== COVERED BY (Artists who covered this song) ===")
        for cover in details["covered_by"]:
            lines.append(f"  • {cover['track']} by {cover['artist']}")
            lines.append(f"    {cover['url']}")
        lines.append("")

    # Remixes
    if details.get("remixes"):
        lines.append("=== REMIXES (Remixes by this artist) ===")
        for remix in details["remixes"]:
            lines.append(f"  • {remix['track']} by {remix['artist']}")
            lines.append(f"    {remix['url']}")
        lines.append("")

    # Remixed by
    if details.get("remixed_by"):
        lines.append("=== REMIXED BY (Artists who remixed this song) ===")
        for remix in details["remixed_by"]:
            lines.append(f"  • {remix['track']} by {remix['artist']}")
            lines.append(f"    {remix['url']}")
        lines.append("")

    # Check if we have any content beyond URL and title
    has_content = (
        details.get("samples")
        or details.get("sampled_by")
        or details.get("covers")
        or details.get("covered_by")
        or details.get("remixes")
        or details.get("remixed_by")
    )

    if not has_content:
        lines.append("No samples, covers, or remixes found for this track.")

    return "\n".join(lines)


async def main():
    """Main entry point for the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def cli():
    """CLI entry point for uvx and pip installations."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
