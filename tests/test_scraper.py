"""Tests for WhoSampled scraper."""
import pytest
import httpx
from whosampled_connector.scraper import WhoSampledScraper


@pytest.mark.asyncio
async def test_search_track_success(scraper, mock_search_html, httpx_mock):
    """Test successful track search."""
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=Daft+Punk+Harder+Better+Faster+Stronger",
        text=mock_search_html,
        status_code=200
    )

    result = await scraper.search_track("Daft Punk", "Harder Better Faster Stronger")

    assert result is not None
    assert result["title"] == "Harder, Better, Faster, Stronger"
    assert result["artist"] == "Daft Punk"
    assert "Harder,-Better,-Faster,-Stronger" in result["url"]


@pytest.mark.asyncio
async def test_search_track_not_found(scraper, httpx_mock):
    """Test track search with no results."""
    httpx_mock.add_response(
        url="https://www.whosampled.com/search/?q=NonexistentArtist+NonexistentTrack",
        text="<html><body><ul></ul></body></html>",
        status_code=200
    )

    result = await scraper.search_track("NonexistentArtist", "NonexistentTrack")

    assert result is None


@pytest.mark.asyncio
async def test_get_track_details_with_samples(scraper, mock_track_details_html, httpx_mock):
    """Test getting track details with samples."""
    test_url = "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/"
    httpx_mock.add_response(
        url=test_url,
        text=mock_track_details_html,
        status_code=200
    )

    result = await scraper.get_track_details(test_url, include_youtube=False)

    assert result is not None
    assert "error" not in result
    assert result["title"] == "Harder, Better, Faster, Stronger"
    assert len(result["samples"]) == 1
    assert result["samples"][0]["track"] == "Cola Bottle Baby"
    assert result["samples"][0]["artist"] == "Edwin Birdsong"
    assert len(result["sampled_by"]) == 1
    assert result["sampled_by"][0]["track"] == "Stronger"
    assert result["sampled_by"][0]["artist"] == "Kanye West"


@pytest.mark.asyncio
async def test_get_track_details_with_youtube(scraper, mock_track_details_html, httpx_mock):
    """Test getting track details with YouTube link."""
    test_url = "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/"
    httpx_mock.add_response(
        url=test_url,
        text=mock_track_details_html,
        status_code=200
    )

    result = await scraper.get_track_details(test_url, include_youtube=True)

    assert result is not None
    assert "youtube_url" in result
    assert "youtube.com" in result["youtube_url"]


@pytest.mark.asyncio
async def test_get_track_details_with_covers_and_remixes(scraper, mock_track_details_html, httpx_mock):
    """Test getting track details including covers and remixes."""
    test_url = "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/"
    httpx_mock.add_response(
        url=test_url,
        text=mock_track_details_html,
        status_code=200
    )

    result = await scraper.get_track_details(test_url, include_youtube=False)

    assert result is not None
    assert len(result["covers"]) == 1
    assert result["covers"][0]["track"] == "Cover Version"
    assert len(result["covered_by"]) == 1
    assert result["covered_by"][0]["track"] == "Another Cover"
    assert len(result["remixes"]) == 1
    assert result["remixes"][0]["track"] == "Remix Version"
    assert len(result["remixed_by"]) == 1
    assert result["remixed_by"][0]["track"] == "Another Remix"


@pytest.mark.asyncio
async def test_get_track_details_empty(scraper, mock_empty_track_html, httpx_mock):
    """Test getting track details for track with no connections."""
    test_url = "https://www.whosampled.com/Some/Obscure-Track/"
    httpx_mock.add_response(
        url=test_url,
        text=mock_empty_track_html,
        status_code=200
    )

    result = await scraper.get_track_details(test_url, include_youtube=False)

    assert result is not None
    assert "error" not in result
    assert result["title"] == "Some Obscure Track"
    assert len(result["samples"]) == 0
    assert len(result["sampled_by"]) == 0
    assert len(result["covers"]) == 0
    assert len(result["covered_by"]) == 0


@pytest.mark.asyncio
async def test_get_track_details_http_error(scraper, httpx_mock):
    """Test handling of HTTP errors."""
    test_url = "https://www.whosampled.com/Invalid/Track/"
    httpx_mock.add_response(
        url=test_url,
        status_code=404
    )

    result = await scraper.get_track_details(test_url, include_youtube=False)

    assert "error" in result
    assert result["url"] == test_url


@pytest.mark.asyncio
async def test_extract_connections():
    """Test the _extract_connections method."""
    scraper = WhoSampledScraper()

    html = """
    <section id="samples">
        <div class="trackItem">
            <a class="trackName" href="/Sample-1/">Sample Track 1</a>
            <span class="trackArtist">Artist 1</span>
        </div>
        <div class="trackItem">
            <a class="trackName" href="/Sample-2/">Sample Track 2</a>
            <span class="trackArtist">Artist 2</span>
        </div>
    </section>
    """

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    section = soup.find('section', {'id': 'samples'})

    connections = scraper._extract_connections(section)

    assert len(connections) == 2
    assert connections[0]["track"] == "Sample Track 1"
    assert connections[0]["artist"] == "Artist 1"
    assert connections[1]["track"] == "Sample Track 2"
    assert connections[1]["artist"] == "Artist 2"

    await scraper.aclose()
