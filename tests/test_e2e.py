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


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_get_youtube_links():
    """Test get_youtube_links endpoint with real WhoSampled data."""
    result = await call_tool("get_youtube_links", {
        "artist": "Daft Punk",
        "track": "One More Time",
        "max_per_section": 3
    })

    assert len(result) == 1
    text = result[0].text

    # Should contain the query
    assert "Daft Punk" in text or "One More Time" in text

    # Should have section headers
    assert "TOP HIT" in text or "CONNECTIONS" in text or "TRACKS" in text

    # Should have WhoSampled URLs
    assert "whosampled.com" in text

    # Most popular tracks should have at least one YouTube link
    assert "youtube.com" in text.lower() or "youtu.be" in text.lower()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_get_youtube_links_with_custom_max():
    """Test get_youtube_links with custom max_per_section parameter."""
    result = await call_tool("get_youtube_links", {
        "artist": "Daft Punk",
        "track": "Harder Better Faster Stronger",
        "max_per_section": 2
    })

    assert len(result) == 1
    text = result[0].text

    # Should contain relevant information
    assert len(text) > 100

    # Should respect max_per_section limit
    # Count track items (each track has "WhoSampled:" in the output)
    track_count = text.count("WhoSampled:")
    # Should have at most 2 tracks per section (3 sections max = 6 total)
    assert track_count <= 6


@pytest.mark.asyncio
async def test_integration_get_youtube_links_no_results():
    """Test get_youtube_links with track that doesn't exist."""
    result = await call_tool("get_youtube_links", {
        "artist": "NonexistentArtistXYZ999",
        "track": "NonexistentTrackXYZ999",
        "max_per_section": 3
    })

    assert len(result) == 1
    text = result[0].text

    # Should handle gracefully - either show empty sections or "No tracks found"
    assert "NonexistentArtistXYZ999" in text or "No tracks found" in text


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_get_youtube_links_priority_order():
    """Test that get_youtube_links returns results in priority order."""
    result = await call_tool("get_youtube_links", {
        "artist": "Kanye West",
        "track": "Stronger",
        "max_per_section": 2
    })

    assert len(result) == 1
    text = result[0].text

    # Check that sections appear in priority order (if they exist)
    top_hit_pos = text.find("TOP HIT")
    connections_pos = text.find("CONNECTIONS")
    tracks_pos = text.find("TRACKS")

    # If TOP HIT exists, it should come before other sections
    if top_hit_pos != -1:
        if connections_pos != -1:
            assert top_hit_pos < connections_pos
        if tracks_pos != -1:
            assert top_hit_pos < tracks_pos

    # If CONNECTIONS exists, it should come before TRACKS
    if connections_pos != -1 and tracks_pos != -1:
        assert connections_pos < tracks_pos


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_get_youtube_links_missing_params():
    """Test get_youtube_links error handling for missing parameters."""
    # Missing artist
    result = await call_tool("get_youtube_links", {
        "track": "One More Time",
        "max_per_section": 3
    })

    assert len(result) == 1
    assert "Error" in result[0].text
    assert "required" in result[0].text.lower()

    # Missing track
    result = await call_tool("get_youtube_links", {
        "artist": "Daft Punk",
        "max_per_section": 3
    })

    assert len(result) == 1
    assert "Error" in result[0].text
    assert "required" in result[0].text.lower()
