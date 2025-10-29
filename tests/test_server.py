"""Tests for MCP server tools."""

import pytest
from unittest.mock import AsyncMock, patch
from whosampled_connector.server import (
    call_tool,
    list_tools,
    _format_track_details,
    scraper,
)


@pytest.mark.asyncio
async def test_list_tools():
    """Test that all tools are listed."""
    tools = await list_tools()

    assert len(tools) == 4
    tool_names = [tool.name for tool in tools]
    assert "search_track" in tool_names
    assert "get_track_samples" in tool_names
    assert "get_track_details_by_url" in tool_names
    assert "get_youtube_links" in tool_names


@pytest.mark.asyncio
async def test_search_track_tool_success():
    """Test search_track tool with successful result."""
    mock_result = {
        "title": "Harder, Better, Faster, Stronger",
        "artist": "Daft Punk",
        "url": "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
    }

    with patch(
        "whosampled_connector.server.scraper.search_track", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_result

        result = await call_tool(
            "search_track",
            {"artist": "Daft Punk", "track": "Harder Better Faster Stronger"},
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Harder, Better, Faster, Stronger" in result[0].text
        assert "Daft Punk" in result[0].text
        assert "whosampled.com" in result[0].text


@pytest.mark.asyncio
async def test_search_track_tool_not_found():
    """Test search_track tool with no results."""
    with patch(
        "whosampled_connector.server.scraper.search_track", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = None

        result = await call_tool(
            "search_track", {"artist": "Unknown Artist", "track": "Unknown Track"}
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "No results found" in result[0].text


@pytest.mark.asyncio
async def test_search_track_tool_missing_params():
    """Test search_track tool with missing artist parameter."""
    result = await call_tool("search_track", {"track": "One More Time"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Error" in result[0].text
    assert "Artist name is required" in result[0].text


@pytest.mark.asyncio
async def test_search_track_tool_artist_only():
    """Test search_track tool with artist only (no track name)."""
    mock_result = {
        "title": "Some Track",
        "artist": "Daft Punk",
        "url": "https://www.whosampled.com/Daft-Punk/Some-Track/",
    }

    with patch.object(scraper, "search_track", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_result

        result = await call_tool("search_track", {"artist": "Daft Punk", "track": ""})

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Daft Punk" in result[0].text
        assert "Some Track" in result[0].text


@pytest.mark.asyncio
async def test_get_track_samples_tool_success():
    """Test get_track_samples tool with successful result."""
    mock_search_result = {
        "title": "Harder, Better, Faster, Stronger",
        "artist": "Daft Punk",
        "url": "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
    }

    mock_details = {
        "url": "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
        "title": "Harder, Better, Faster, Stronger",
        "samples": [
            {
                "track": "Cola Bottle Baby",
                "artist": "Edwin Birdsong",
                "url": "https://www.whosampled.com/Edwin-Birdsong/Cola-Bottle-Baby/",
            }
        ],
        "sampled_by": [
            {
                "track": "Stronger",
                "artist": "Kanye West",
                "url": "https://www.whosampled.com/Kanye-West/Stronger/",
            }
        ],
        "covers": [],
        "covered_by": [],
        "remixes": [],
        "remixed_by": [],
    }

    with (
        patch(
            "whosampled_connector.server.scraper.search_track", new_callable=AsyncMock
        ) as mock_search,
        patch(
            "whosampled_connector.server.scraper.get_track_details",
            new_callable=AsyncMock,
        ) as mock_get_details,
    ):
        mock_search.return_value = mock_search_result
        mock_get_details.return_value = mock_details

        result = await call_tool(
            "get_track_samples",
            {
                "artist": "Daft Punk",
                "track": "Harder Better Faster Stronger",
                "include_youtube": False,
            },
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Cola Bottle Baby" in result[0].text
        assert "Edwin Birdsong" in result[0].text
        assert "Kanye West" in result[0].text


@pytest.mark.asyncio
async def test_get_track_samples_with_youtube():
    """Test get_track_samples tool with YouTube link."""
    mock_search_result = {
        "title": "Harder, Better, Faster, Stronger",
        "artist": "Daft Punk",
        "url": "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
    }

    mock_details = {
        "url": "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
        "title": "Harder, Better, Faster, Stronger",
        "youtube_url": "https://www.youtube.com/watch?v=test123",
        "samples": [],
        "sampled_by": [],
        "covers": [],
        "covered_by": [],
        "remixes": [],
        "remixed_by": [],
    }

    with (
        patch(
            "whosampled_connector.server.scraper.search_track", new_callable=AsyncMock
        ) as mock_search,
        patch(
            "whosampled_connector.server.scraper.get_track_details",
            new_callable=AsyncMock,
        ) as mock_get_details,
    ):
        mock_search.return_value = mock_search_result
        mock_get_details.return_value = mock_details

        result = await call_tool(
            "get_track_samples",
            {
                "artist": "Daft Punk",
                "track": "Harder Better Faster Stronger",
                "include_youtube": True,
            },
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "YouTube" in result[0].text
        assert "youtube.com" in result[0].text


@pytest.mark.asyncio
async def test_get_track_details_by_url_tool():
    """Test get_track_details_by_url tool."""
    mock_details = {
        "url": "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
        "title": "Harder, Better, Faster, Stronger",
        "samples": [],
        "sampled_by": [],
        "covers": [],
        "covered_by": [],
        "remixes": [],
        "remixed_by": [],
    }

    with patch(
        "whosampled_connector.server.scraper.get_track_details", new_callable=AsyncMock
    ) as mock_get_details:
        mock_get_details.return_value = mock_details

        result = await call_tool(
            "get_track_details_by_url",
            {
                "url": "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
                "include_youtube": False,
            },
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "whosampled.com" in result[0].text


@pytest.mark.asyncio
async def test_get_track_details_by_url_missing_url():
    """Test get_track_details_by_url with missing URL."""
    result = await call_tool("get_track_details_by_url", {})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Error" in result[0].text
    assert "required" in result[0].text


@pytest.mark.asyncio
async def test_unknown_tool():
    """Test calling an unknown tool."""
    result = await call_tool("unknown_tool", {})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Unknown tool" in result[0].text


def test_format_track_details_with_all_sections():
    """Test formatting track details with all sections."""
    details = {
        "url": "https://www.whosampled.com/test/",
        "title": "Test Track",
        "youtube_url": "https://www.youtube.com/watch?v=test",
        "samples": [{"track": "Sample 1", "artist": "Artist 1", "url": "url1"}],
        "sampled_by": [{"track": "Sample 2", "artist": "Artist 2", "url": "url2"}],
        "covers": [{"track": "Cover 1", "artist": "Artist 3", "url": "url3"}],
        "covered_by": [{"track": "Cover 2", "artist": "Artist 4", "url": "url4"}],
        "remixes": [{"track": "Remix 1", "artist": "Artist 5", "url": "url5"}],
        "remixed_by": [{"track": "Remix 2", "artist": "Artist 6", "url": "url6"}],
    }

    result = _format_track_details(details)

    assert "Test Track" in result
    assert "YouTube" in result
    assert "SAMPLES" in result
    assert "SAMPLED BY" in result
    assert "COVERS" in result
    assert "COVERED BY" in result
    assert "REMIXES" in result
    assert "REMIXED BY" in result


def test_format_track_details_empty():
    """Test formatting track details with no connections."""
    details = {
        "url": "https://www.whosampled.com/test/",
        "title": "Test Track",
        "samples": [],
        "sampled_by": [],
        "covers": [],
        "covered_by": [],
        "remixes": [],
        "remixed_by": [],
    }

    result = _format_track_details(details)

    assert "Test Track" in result
    assert "No samples, covers, or remixes found" in result


def test_format_track_details_with_error():
    """Test formatting track details with error."""
    details = {
        "error": "HTTP error occurred",
        "url": "https://www.whosampled.com/test/",
    }

    result = _format_track_details(details)

    assert "Error" in result
    assert "HTTP error occurred" in result


@pytest.mark.asyncio
async def test_get_youtube_links_tool_success():
    """Test get_youtube_links tool with successful result."""
    mock_result = {
        "query": "Daft Punk One More Time",
        "top_hit": [
            {
                "track": "One More Time",
                "artist": "Daft Punk",
                "url": "https://www.whosampled.com/Daft-Punk/One-More-Time/",
                "youtube_url": "https://www.youtube.com/watch?v=test123",
            }
        ],
        "connections": [
            {
                "track": "Connection Track",
                "artist": "Connection Artist",
                "url": "https://www.whosampled.com/Connection/Track/",
                "youtube_url": "https://www.youtube.com/watch?v=connection",
            }
        ],
        "tracks": [
            {
                "track": "Related Track",
                "artist": "Related Artist",
                "url": "https://www.whosampled.com/Related/Track/",
                "youtube_url": None,
            }
        ],
    }

    with patch(
        "whosampled_connector.server.scraper.get_youtube_links_from_search",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_result

        result = await call_tool(
            "get_youtube_links",
            {"artist": "Daft Punk", "track": "One More Time", "max_per_section": 3},
        )

        assert len(result) == 1
        assert result[0].type == "text"
        text = result[0].text
        assert "TOP HIT" in text
        assert "One More Time" in text
        assert "youtube.com/watch?v=test123" in text
        assert "CONNECTIONS" in text
        assert "Connection Track" in text
        assert "TRACKS" in text
        assert "Related Track" in text


@pytest.mark.asyncio
async def test_get_youtube_links_tool_missing_params():
    """Test get_youtube_links tool with missing parameters."""
    # Missing track
    result = await call_tool("get_youtube_links", {"artist": "Daft Punk"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Error" in result[0].text
    assert "required" in result[0].text

    # Missing artist
    result = await call_tool("get_youtube_links", {"track": "One More Time"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Error" in result[0].text
    assert "required" in result[0].text


@pytest.mark.asyncio
async def test_get_youtube_links_tool_with_custom_max():
    """Test get_youtube_links tool with custom max_per_section."""
    mock_result = {
        "query": "Test Query",
        "top_hit": [],
        "connections": [],
        "tracks": [],
    }

    with patch(
        "whosampled_connector.server.scraper.get_youtube_links_from_search",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_result

        result = await call_tool(
            "get_youtube_links",
            {"artist": "Artist", "track": "Track", "max_per_section": 5},
        )

        # Verify the method was called with correct max_per_section
        mock_get.assert_called_once_with("Artist", "Track", 5)
        assert len(result) == 1


def test_format_youtube_links_with_all_sections():
    """Test formatting YouTube links with all sections."""
    from whosampled_connector.server import _format_youtube_links

    result_data = {
        "query": "Daft Punk One More Time",
        "top_hit": [
            {
                "track": "One More Time",
                "artist": "Daft Punk",
                "url": "https://www.whosampled.com/test1/",
                "youtube_url": "https://www.youtube.com/watch?v=1",
            }
        ],
        "connections": [
            {
                "track": "Connection",
                "artist": "Artist",
                "url": "https://www.whosampled.com/test2/",
                "youtube_url": "https://www.youtube.com/watch?v=2",
            }
        ],
        "tracks": [
            {
                "track": "Track",
                "artist": "Artist",
                "url": "https://www.whosampled.com/test3/",
                "youtube_url": None,
            }
        ],
    }

    result = _format_youtube_links(result_data)

    assert "Daft Punk One More Time" in result
    assert "TOP HIT" in result
    assert "One More Time" in result
    assert "youtube.com/watch?v=1" in result
    assert "CONNECTIONS" in result
    assert "Connection" in result
    assert "TRACKS" in result
    assert "Not found" in result  # For the track without YouTube link


def test_format_youtube_links_empty():
    """Test formatting YouTube links with no results."""
    from whosampled_connector.server import _format_youtube_links

    result_data = {
        "query": "Unknown Track",
        "top_hit": [],
        "connections": [],
        "tracks": [],
    }

    result = _format_youtube_links(result_data)

    assert "Unknown Track" in result
    assert "No tracks found" in result


def test_format_youtube_links_with_error():
    """Test formatting YouTube links with error."""
    from whosampled_connector.server import _format_youtube_links

    result_data = {"error": "Network error occurred", "query": "Test"}

    result = _format_youtube_links(result_data)

    assert "Error" in result
    assert "Network error occurred" in result
