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
            description="Search for a track on WhoSampled by artist and track name. Returns basic track information and URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist": {
                        "type": "string",
                        "description": "Artist name"
                    },
                    "track": {
                        "type": "string",
                        "description": "Track/song name"
                    }
                },
                "required": ["artist", "track"]
            }
        ),
        Tool(
            name="get_track_samples",
            description="Get detailed information about a track including samples it used, tracks that sampled it, covers, and remixes. Optionally includes YouTube links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist": {
                        "type": "string",
                        "description": "Artist name"
                    },
                    "track": {
                        "type": "string",
                        "description": "Track/song name"
                    },
                    "include_youtube": {
                        "type": "boolean",
                        "description": "Whether to include YouTube links in the response",
                        "default": False
                    }
                },
                "required": ["artist", "track"]
            }
        ),
        Tool(
            name="get_track_details_by_url",
            description="Get detailed information about a track using its WhoSampled URL. Returns samples, covers, remixes, and optionally YouTube links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "WhoSampled track URL"
                    },
                    "include_youtube": {
                        "type": "boolean",
                        "description": "Whether to include YouTube links in the response",
                        "default": False
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_youtube_links",
            description="Get YouTube links from search results with priority: Top Hit > Connections > Tracks. Returns up to 3 tracks per section.",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist": {
                        "type": "string",
                        "description": "Artist name"
                    },
                    "track": {
                        "type": "string",
                        "description": "Track/song name"
                    },
                    "max_per_section": {
                        "type": "integer",
                        "description": "Maximum number of tracks to get from each section (default: 3)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["artist", "track"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "search_track":
        artist = arguments.get("artist", "")
        track = arguments.get("track", "")

        if not artist:
            return [TextContent(
                type="text",
                text="Error: Artist name is required"
            )]

        result = await scraper.search_track(artist, track)

        if result is None:
            search_query = f"'{track}' by '{artist}'" if track else f"artist '{artist}'"
            return [TextContent(
                type="text",
                text=f"No results found for {search_query}"
            )]
        
        response = f"""Track found on WhoSampled:

Title: {result['title']}
Artist: {result['artist']}
URL: {result['url']}

Use get_track_samples or get_track_details_by_url to get detailed information about samples, covers, and remixes.
"""
        
        return [TextContent(type="text", text=response)]
    
    elif name == "get_track_samples":
        artist = arguments.get("artist", "")
        track = arguments.get("track", "")
        include_youtube = arguments.get("include_youtube", False)
        
        if not artist or not track:
            return [TextContent(
                type="text",
                text="Error: Both artist and track name are required"
            )]
        
        # First search for the track
        search_result = await scraper.search_track(artist, track)
        
        if search_result is None:
            return [TextContent(
                type="text",
                text=f"No results found for '{track}' by '{artist}'"
            )]
        
        # Get detailed information
        details = await scraper.get_track_details(search_result['url'], include_youtube)
        
        return [TextContent(type="text", text=_format_track_details(details))]
    
    elif name == "get_track_details_by_url":
        url = arguments.get("url", "")
        include_youtube = arguments.get("include_youtube", False)

        if not url:
            return [TextContent(
                type="text",
                text="Error: URL is required"
            )]

        details = await scraper.get_track_details(url, include_youtube)

        return [TextContent(type="text", text=_format_track_details(details))]

    elif name == "get_youtube_links":
        artist = arguments.get("artist", "")
        track = arguments.get("track", "")
        max_per_section = arguments.get("max_per_section", 3)

        if not artist or not track:
            return [TextContent(
                type="text",
                text="Error: Both artist and track name are required"
            )]

        result = await scraper.get_youtube_links_from_search(artist, track, max_per_section)

        return [TextContent(type="text", text=_format_youtube_links(result))]

    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


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
    has_content = result.get("top_hit") or result.get("connections") or result.get("tracks")
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
    has_content = (details.get("samples") or details.get("sampled_by") or
                   details.get("covers") or details.get("covered_by") or
                   details.get("remixes") or details.get("remixed_by"))

    if not has_content:
        lines.append("No samples, covers, or remixes found for this track.")

    return "\n".join(lines)


async def main():
    """Main entry point for the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def cli():
    """CLI entry point for uvx and pip installations."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
