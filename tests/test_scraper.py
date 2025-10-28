"""Tests for WhoSampled scraper."""
import pytest
from unittest.mock import AsyncMock, patch
from whosampled_connector.scraper import WhoSampledScraper


@pytest.mark.asyncio
async def test_search_track_success(scraper, mock_search_html):
    """Test successful track search."""
    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_search_html

        result = await scraper.search_track("Daft Punk", "Harder Better Faster Stronger")

        assert result is not None
        assert result["title"] == "Harder, Better, Faster, Stronger"
        assert result["artist"] == "Daft Punk"
        assert "Harder,-Better,-Faster,-Stronger" in result["url"]


@pytest.mark.asyncio
async def test_search_track_not_found(scraper):
    """Test track search with no results."""
    empty_html = "<html><body></body></html>"

    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = empty_html

        result = await scraper.search_track("NonexistentArtist", "NonexistentTrack")

        assert result is None


@pytest.mark.asyncio
async def test_get_track_details_with_samples(scraper, mock_track_details_html):
    """Test getting track details with samples."""
    test_url = "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/"

    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_track_details_html

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
async def test_get_track_details_with_youtube(scraper, mock_track_details_html):
    """Test getting track details with YouTube link."""
    test_url = "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/"

    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_track_details_html

        result = await scraper.get_track_details(test_url, include_youtube=True)

        assert result is not None
        assert "youtube_url" in result
        assert "youtube.com" in result["youtube_url"]


@pytest.mark.asyncio
async def test_get_track_details_with_covers_and_remixes(scraper, mock_track_details_html):
    """Test getting track details including covers and remixes."""
    test_url = "https://www.whosampled.com/Daft-Punk/Harder,-Better,-Faster,-Stronger/"

    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_track_details_html

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
async def test_get_track_details_empty(scraper, mock_empty_track_html):
    """Test getting track details for track with no connections."""
    test_url = "https://www.whosampled.com/Some/Obscure-Track/"

    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_empty_track_html

        result = await scraper.get_track_details(test_url, include_youtube=False)

        assert result is not None
        assert "error" not in result
        assert result["title"] == "Some Obscure Track"
        assert len(result["samples"]) == 0
        assert len(result["sampled_by"]) == 0
        assert len(result["covers"]) == 0
        assert len(result["covered_by"]) == 0


@pytest.mark.asyncio
async def test_get_track_details_http_error(scraper):
    """Test handling of HTTP errors."""
    test_url = "https://www.whosampled.com/Invalid/Track/"

    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        # Simulate an error
        mock_fetch.side_effect = Exception("Network error")

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
