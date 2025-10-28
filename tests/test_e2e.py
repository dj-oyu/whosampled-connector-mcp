"""End-to-end tests for the MCP server."""
import pytest
from unittest.mock import AsyncMock, patch
from whosampled_connector.server import call_tool


@pytest.mark.asyncio
async def test_e2e_search_and_get_details(mock_search_html, mock_track_details_html, httpx_mock):
    """Test complete flow: search track and get details."""
    # Mock the search response (needed twice - once for search_track, once for get_track_samples)
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Daft+Punk+Harder+Better+Faster+Stronger",
        text=mock_search_html,
        status_code=200
    )
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Daft+Punk+Harder+Better+Faster+Stronger",
        text=mock_search_html,
        status_code=200
    )

    # Mock the details response
    httpx_mock.add_response(
        url="https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
        text=mock_track_details_html,
        status_code=200
    )

    # Step 1: Search for a track
    search_result = await call_tool("search_track", {
        "artist": "Daft Punk",
        "track": "Harder Better Faster Stronger"
    })

    assert len(search_result) == 1
    assert "Harder, Better, Faster, Stronger" in search_result[0].text
    assert "Daft Punk" in search_result[0].text

    # Step 2: Get detailed information
    details_result = await call_tool("get_track_samples", {
        "artist": "Daft Punk",
        "track": "Harder Better Faster Stronger",
        "include_youtube": False
    })

    assert len(details_result) == 1
    assert "Cola Bottle Baby" in details_result[0].text
    assert "Edwin Birdsong" in details_result[0].text
    assert "Kanye West" in details_result[0].text


@pytest.mark.asyncio
async def test_e2e_direct_url_lookup(mock_track_details_html, httpx_mock):
    """Test direct URL lookup flow."""
    test_url = "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/"

    # Mock the details response
    httpx_mock.add_response(
        url=test_url,
        text=mock_track_details_html,
        status_code=200
    )

    # Get details by URL
    result = await call_tool("get_track_details_by_url", {
        "url": test_url,
        "include_youtube": True
    })

    assert len(result) == 1
    assert "Harder, Better, Faster, Stronger" in result[0].text
    assert "YouTube" in result[0].text
    assert "Cola Bottle Baby" in result[0].text
    assert "Kanye West" in result[0].text


@pytest.mark.asyncio
async def test_e2e_track_with_covers_and_remixes(mock_search_html, mock_track_details_html, httpx_mock):
    """Test flow for track with covers and remixes."""
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Daft+Punk+Test",
        text=mock_search_html,
        status_code=200
    )

    httpx_mock.add_response(
        url="https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
        text=mock_track_details_html,
        status_code=200
    )

    result = await call_tool("get_track_samples", {
        "artist": "Daft Punk",
        "track": "Test",
        "include_youtube": False
    })

    assert len(result) == 1
    text = result[0].text

    # Check for all sections
    assert "SAMPLES" in text
    assert "SAMPLED BY" in text
    assert "COVERS" in text
    assert "COVERED BY" in text
    assert "REMIXES" in text
    assert "REMIXED BY" in text


@pytest.mark.asyncio
async def test_e2e_track_not_found():
    """Test flow when track is not found."""
    httpx_mock_instance = pytest.importorskip("pytest_httpx")

    with patch('whosampled_connector.server.scraper') as mock_scraper:
        mock_scraper.search_track = AsyncMock(return_value=None)

        result = await call_tool("search_track", {
            "artist": "Unknown Artist",
            "track": "Unknown Track"
        })

        assert len(result) == 1
        assert "No results found" in result[0].text


@pytest.mark.asyncio
async def test_e2e_multiple_searches_sequential(mock_search_html, mock_track_details_html, httpx_mock):
    """Test multiple sequential searches."""
    # Setup mocks for multiple tracks
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Daft+Punk+Track+1",
        text=mock_search_html,
        status_code=200
    )

    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Daft+Punk+Track+2",
        text=mock_search_html,
        status_code=200
    )

    # Search for first track
    result1 = await call_tool("search_track", {
        "artist": "Daft Punk",
        "track": "Track 1"
    })

    assert len(result1) == 1
    assert "Daft Punk" in result1[0].text

    # Search for second track
    result2 = await call_tool("search_track", {
        "artist": "Daft Punk",
        "track": "Track 2"
    })

    assert len(result2) == 1
    assert "Daft Punk" in result2[0].text


@pytest.mark.asyncio
async def test_e2e_error_handling_http_error(httpx_mock):
    """Test error handling for HTTP errors."""
    httpx_mock.add_response(
        url="https://www.whosampled.com/Invalid-Track/",
        status_code=404
    )

    result = await call_tool("get_track_details_by_url", {
        "url": "https://www.whosampled.com/Invalid-Track/",
        "include_youtube": False
    })

    assert len(result) == 1
    assert "Error" in result[0].text or "404" in result[0].text or len(result[0].text) > 0


@pytest.mark.asyncio
async def test_e2e_with_youtube_links(mock_search_html, mock_track_details_html, httpx_mock):
    """Test flow with YouTube link inclusion."""
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Daft+Punk+YouTube+Test",
        text=mock_search_html,
        status_code=200
    )

    httpx_mock.add_response(
        url="https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/",
        text=mock_track_details_html,
        status_code=200
    )

    result = await call_tool("get_track_samples", {
        "artist": "Daft Punk",
        "track": "YouTube Test",
        "include_youtube": True
    })

    assert len(result) == 1
    assert "YouTube" in result[0].text
    assert "youtube.com" in result[0].text


@pytest.mark.asyncio
async def test_e2e_empty_track(mock_search_html, mock_empty_track_html, httpx_mock):
    """Test flow for track with no samples/covers/remixes."""
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Artist+Obscure+Track",
        text="""
        <html>
            <body>
                <ul>
                    <li class="trackName">
                        <a href="/Some/Obscure-Track/">Some Obscure Track</a>
                        <span class="trackArtist">Artist</span>
                    </li>
                </ul>
            </body>
        </html>
        """,
        status_code=200
    )

    httpx_mock.add_response(
        url="https://www.whosampled.com/Some/Obscure-Track/",
        text=mock_empty_track_html,
        status_code=200
    )

    result = await call_tool("get_track_samples", {
        "artist": "Artist",
        "track": "Obscure Track",
        "include_youtube": False
    })

    assert len(result) == 1
    assert "No samples, covers, or remixes found" in result[0].text
