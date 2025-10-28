"""Integration tests for the MCP server - tests against real WhoSampled site."""
import pytest
from whosampled_connector.server import call_tool


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_search_and_get_details():
    """Test complete flow: search track and get details using real WhoSampled."""
    # Step 1: Search for a well-known track
    search_result = await call_tool("search_track", {
        "artist": "Daft Punk",
        "track": "One More Time"
    })

    assert len(search_result) == 1
    assert "One More Time" in search_result[0].text
    assert "Daft Punk" in search_result[0].text
    assert "whosampled.com" in search_result[0].text

    # Step 2: Get detailed information
    details_result = await call_tool("get_track_samples", {
        "artist": "Daft Punk",
        "track": "One More Time",
        "include_youtube": False
    })

    assert len(details_result) == 1
    # The track has known samples, should have content
    assert len(details_result[0].text) > 100


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_direct_url_lookup():
    """Test direct URL lookup flow using real WhoSampled."""
    test_url = "https://www.whosampled.com/Daft-Punk/One-More-Time/"

    result = await call_tool("get_track_details_by_url", {
        "url": test_url,
        "include_youtube": True
    })

    assert len(result) == 1
    assert "One More Time" in result[0].text
    # Should have YouTube link
    assert "YouTube" in result[0].text or "youtube.com" in result[0].text


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_track_with_multiple_sections():
    """Test flow for track with samples, covers, and remixes using real data."""
    result = await call_tool("get_track_samples", {
        "artist": "Daft Punk",
        "track": "Harder Better Faster Stronger",
        "include_youtube": False
    })

    assert len(result) == 1
    text = result[0].text

    # This track is known to have samples
    assert "SAMPLES" in text or "samples" in text.lower()


@pytest.mark.asyncio
async def test_integration_track_not_found():
    """Test flow when track is not found."""
    result = await call_tool("search_track", {
        "artist": "NonexistentArtistXYZ123456",
        "track": "NonexistentTrackXYZ123456"
    })

    assert len(result) == 1
    assert "No results found" in result[0].text


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_artist_search():
    """Test artist search using real data - searches by artist only."""
    # Search for a well-known artist
    result = await call_tool("search_track", {
        "artist": "Daft Punk",
        "track": ""
    })

    assert len(result) == 1
    # Should either find a result or return "No results found" (not an error)
    assert "Error" not in result[0].text or "Artist name is required" not in result[0].text
    # Result should contain meaningful content
    assert len(result[0].text) > 30


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_with_youtube_links():
    """Test flow with YouTube link inclusion using real data."""
    result = await call_tool("get_track_samples", {
        "artist": "Daft Punk",
        "track": "One More Time",
        "include_youtube": True
    })

    assert len(result) == 1
    # Most popular tracks have YouTube links
    assert "YouTube" in result[0].text or "youtube.com" in result[0].text


@pytest.mark.asyncio
async def test_integration_error_handling_invalid_url():
    """Test error handling for invalid URLs."""
    result = await call_tool("get_track_details_by_url", {
        "url": "https://www.whosampled.com/Invalid-Track-That-Does-Not-Exist-XYZ123/",
        "include_youtube": False
    })

    assert len(result) == 1
    # Should handle gracefully - either error message or empty results
    assert len(result[0].text) > 0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_multiple_searches_sequential():
    """Test multiple sequential searches using real data."""
    # Search for first track
    result1 = await call_tool("search_track", {
        "artist": "Daft Punk",
        "track": "One More Time"
    })

    assert len(result1) == 1
    assert "Daft Punk" in result1[0].text

    # Search for second track
    result2 = await call_tool("search_track", {
        "artist": "Daft Punk",
        "track": "Around the World"
    })

    assert len(result2) == 1
    assert "Daft Punk" in result2[0].text
