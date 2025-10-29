"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from whosampled_connector.scraper import WhoSampledScraper
import socket


def check_internet_connection():
    """Check if internet connection is available."""
    try:
        # Try to resolve whosampled.com
        socket.gethostbyname('www.whosampled.com')
        return True
    except (socket.gaierror, socket.error):
        return False


@pytest.fixture(scope="function", autouse=True)
def skip_if_no_internet(request):
    """Skip integration tests if no internet connection is available."""
    if "integration" in request.keywords:
        if not check_internet_connection():
            pytest.skip("Integration test requires internet connection to whosampled.com")


@pytest_asyncio.fixture
async def scraper():
    """Create a scraper instance for testing."""
    scraper = WhoSampledScraper()
    yield scraper
    await scraper.aclose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_global_scraper(request):
    """Clean up global scraper after each integration test."""
    # Only run for integration tests
    if "integration" in request.keywords:
        yield
        # After test, clean up the global scraper
        from whosampled_connector import server
        if server.scraper._initialized:
            await server.scraper.aclose()
            # Reset the scraper state
            server.scraper._initialized = False
            server.scraper.browser = None
            server.scraper.playwright = None
    else:
        yield


@pytest.fixture
def mock_search_html():
    """Mock HTML response for search results with actual WhoSampled structure."""
    return """
    <html>
        <body>
            <div class="topResult">
                <a class="trackTitle" href="/Daft-Punk/Harder,-Better,-Faster,-Stronger/">
                    Harder, Better, Faster, Stronger
                </a>
                <a href="/Daft-Punk/">Daft Punk</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_track_details_html():
    """Mock HTML response for track details page with new WhoSampled structure."""
    return """
    <html>
        <body>
            <h1 class="trackName">Harder, Better, Faster, Stronger</h1>
            <a href="https://www.youtube.com/watch?v=gAjR4_CbPpQ">YouTube</a>

            <section class="subsection" id="samples">
                <h3>Contains samples</h3>
                <div class="trackItem">
                    <a class="trackName" href="/Cola-Bottle-Baby/">Cola Bottle Baby</a>
                    <a href="/Edwin-Birdsong/">Edwin Birdsong</a>
                </div>
            </section>

            <section class="subsection" id="was-sampled">
                <h3>Was sampled in</h3>
                <div class="trackItem">
                    <a class="trackName" href="/Kanye-West/Stronger/">Stronger</a>
                    <a href="/Kanye-West/">Kanye West</a>
                </div>
            </section>

            <section class="subsection" id="covers">
                <h3>Cover of</h3>
                <div class="trackItem">
                    <a class="trackName" href="/Some-Cover/">Cover Version</a>
                    <a href="/Cover-Artist/">Cover Artist</a>
                </div>
            </section>

            <section class="subsection" id="was-covered">
                <h3>Covered by</h3>
                <div class="trackItem">
                    <a class="trackName" href="/Another-Cover/">Another Cover</a>
                    <a href="/Another-Artist/">Another Artist</a>
                </div>
            </section>

            <section class="subsection" id="remixes">
                <h3>Remix of</h3>
                <div class="trackItem">
                    <a class="trackName" href="/Some-Remix/">Remix Version</a>
                    <a href="/Remix-Artist/">Remix Artist</a>
                </div>
            </section>

            <section class="subsection" id="was-remixed">
                <h3>Remixed by</h3>
                <div class="trackItem">
                    <a class="trackName" href="/Another-Remix/">Another Remix</a>
                    <a href="/Remixer/">Remixer</a>
                </div>
            </section>
        </body>
    </html>
    """


@pytest.fixture
def mock_empty_track_html():
    """Mock HTML response for track with no samples/covers/remixes."""
    return """
    <html>
        <body>
            <h1 class="trackName">Some Obscure Track</h1>
        </body>
    </html>
    """
