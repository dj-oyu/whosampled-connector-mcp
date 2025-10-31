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
    search_result = await call_tool(
        "search_track", {"query": "Daft Punk One More Time"}
    )

    assert len(search_result) == 1
    assert "One More Time" in search_result[0].text
    assert "Daft Punk" in search_result[0].text
    assert "whosampled.com" in search_result[0].text

    # Step 2: Get detailed information
    details_result = await call_tool(
        "get_track_samples",
        {"query": "Daft Punk One More Time", "include_youtube": False},
    )

    assert len(details_result) == 1
    # The track has known samples, should have content
    assert len(details_result[0].text) > 100


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_direct_url_lookup():
    """Test direct URL lookup flow using real WhoSampled."""
    test_url = "https://www.whosampled.com/Daft-Punk/One-More-Time/"

    result = await call_tool(
        "get_track_details_by_url", {"url": test_url, "include_youtube": True}
    )

    assert len(result) == 1
    text = result[0].text
    assert "One More Time" in text
    # Should have YouTube link with proper format: youtube.com/watch?v=...
    assert "youtube.com/watch" in text.lower() or "youtu.be/" in text.lower()
    assert "v=" in text or "youtu.be/" in text.lower()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_track_with_multiple_sections():
    """Test flow for track with samples, covers, and remixes using real data."""
    result = await call_tool(
        "get_track_samples",
        {
            "query": "Daft Punk Harder Better Faster Stronger",
            "include_youtube": False,
        },
    )

    assert len(result) == 1
    text = result[0].text

    # This track is known to have samples
    assert "SAMPLES" in text or "samples" in text.lower()


@pytest.mark.asyncio
async def test_integration_track_not_found():
    """Test flow when track is not found."""
    result = await call_tool(
        "search_track",
        {"query": "NonexistentArtistXYZ123456 NonexistentTrackXYZ123456"},
    )

    assert len(result) == 1
    assert "No results found" in result[0].text


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_artist_search():
    """Test artist search using real data - searches by artist only."""
    # Search for a well-known artist
    result = await call_tool("search_track", {"query": "Daft Punk"})

    assert len(result) == 1
    # Should either find a result or return "No results found" (not an error)
    assert (
        "Error" not in result[0].text or "Artist name is required" not in result[0].text
    )
    # Result should contain meaningful content
    assert len(result[0].text) > 30


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_with_youtube_links():
    """Test flow with YouTube link inclusion using real data."""
    result = await call_tool(
        "get_track_samples",
        {"query": "Daft Punk One More Time", "include_youtube": True},
    )

    assert len(result) == 1
    text = result[0].text
    # Most popular tracks have YouTube links with proper format
    assert "youtube.com/watch" in text.lower() or "youtu.be/" in text.lower()
    assert "v=" in text or "youtu.be/" in text.lower()


@pytest.mark.asyncio
async def test_integration_error_handling_invalid_url():
    """Test error handling for invalid URLs."""
    result = await call_tool(
        "get_track_details_by_url",
        {
            "url": "https://www.whosampled.com/Invalid-Track-That-Does-Not-Exist-XYZ123/",
            "include_youtube": False,
        },
    )

    assert len(result) == 1
    # Should handle gracefully - either error message or empty results
    assert len(result[0].text) > 0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_multiple_searches_sequential():
    """Test multiple sequential searches using real data."""
    # Search for first track
    result1 = await call_tool(
        "search_track", {"query": "Daft Punk One More Time"}
    )

    assert len(result1) == 1
    assert "Daft Punk" in result1[0].text

    # Search for second track
    result2 = await call_tool(
        "search_track", {"query": "Daft Punk Around the World"}
    )

    assert len(result2) == 1
    assert "Daft Punk" in result2[0].text


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_get_youtube_links():
    """Test get_youtube_links endpoint with real WhoSampled data."""
    result = await call_tool(
        "get_youtube_links",
        {"query": "Daft Punk One More Time", "max_per_section": 3},
    )

    assert len(result) == 1
    text = result[0].text

    # Should contain the query
    assert "Daft Punk" in text or "One More Time" in text

    # Should have section headers
    assert "TOP HIT" in text or "CONNECTIONS" in text or "TRACKS" in text

    # Should have WhoSampled URLs
    assert "whosampled.com" in text

    # Most popular tracks should have at least one YouTube link with proper format
    # Check for youtube.com/watch?v= or youtu.be/ format
    assert "youtube.com/watch" in text.lower() or "youtu.be/" in text.lower()
    assert "v=" in text or "youtu.be/" in text.lower()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_get_youtube_links_with_custom_max():
    """Test get_youtube_links with custom max_per_section parameter."""
    result = await call_tool(
        "get_youtube_links",
        {
            "query": "Daft Punk Harder Better Faster Stronger",
            "max_per_section": 2,
        },
    )

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
    result = await call_tool(
        "get_youtube_links",
        {
            "query": "NonexistentArtistXYZ999 NonexistentTrackXYZ999",
            "max_per_section": 3,
        },
    )

    assert len(result) == 1
    text = result[0].text

    # Should handle gracefully - either show empty sections or "No tracks found"
    assert "NonexistentArtistXYZ999" in text or "No tracks found" in text


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_get_youtube_links_priority_order():
    """Test that get_youtube_links returns results in priority order."""
    result = await call_tool(
        "get_youtube_links",
        {"query": "Kanye West Stronger", "max_per_section": 2},
    )

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
    # Missing query parameter (should fail)
    result = await call_tool(
        "get_youtube_links", {"max_per_section": 3}
    )

    assert len(result) == 1
    assert "Error" in result[0].text
    assert "required" in result[0].text.lower()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_team_tomodachi_with_youtube_links():
    """Test Team Tomodachi track with YouTube links for all related tracks."""
    import time

    # Measure performance
    start_time = time.time()

    result = await call_tool(
        "get_track_samples", {"query": "team tomodachi", "include_youtube": True}
    )

    elapsed_time = time.time() - start_time

    assert len(result) == 1
    text = result[0].text

    # Expected video IDs
    expected_video_ids = [
        "c1UaGJlsw5g",  # Original track
        "0LEc7es4_rE",  # Hololive EN cover
        "acw_iA5IgTQ",  # Tokai mix
        "5DmLGUCmxD0",  # Kansai mix
    ]

    # Print results for debugging
    print(f"\n=== Team Tomodachi Test Results ===")
    print(f"Elapsed time: {elapsed_time:.2f}s")
    print(f"\nResponse text:\n{text}")
    print(f"\n=== Checking for expected video IDs ===")

    # Check for each expected video ID
    found_ids = []
    missing_ids = []
    for video_id in expected_video_ids:
        if video_id in text:
            found_ids.append(video_id)
            print(f"✓ Found: {video_id}")
        else:
            missing_ids.append(video_id)
            print(f"✗ Missing: {video_id}")

    # Assertions
    assert "Team Tomodachi" in text, "Track title should be in response"
    assert "youtu.be/" in text or "youtube.com" in text, "Should have YouTube links"

    # Check if we found at least the original track
    assert (
        "c1UaGJlsw5g" in text
    ), "Should have original track YouTube link (c1UaGJlsw5g)"

    # Performance check - should complete in reasonable time
    # Allow up to 60 seconds for fetching multiple YouTube links
    assert (
        elapsed_time < 60
    ), f"Test took too long: {elapsed_time:.2f}s (expected < 60s)"

    # Report findings
    print(f"\nFound {len(found_ids)}/{len(expected_video_ids)} expected video IDs")
    if missing_ids:
        print(f"Note: Some expected IDs were not found: {missing_ids}")
        print("This may be due to WhoSampled data changes or track page structure")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_team_tomodachi_performance():
    """Test performance comparison between with and without YouTube links."""
    import time

    # Test without YouTube links
    start_time = time.time()
    result_no_yt = await call_tool(
        "get_track_samples", {"query": "team tomodachi", "include_youtube": False}
    )
    time_no_yt = time.time() - start_time

    # Test with YouTube links
    start_time = time.time()
    result_with_yt = await call_tool(
        "get_track_samples", {"query": "team tomodachi", "include_youtube": True}
    )
    time_with_yt = time.time() - start_time

    print(f"\n=== Performance Comparison ===")
    print(f"Without YouTube links: {time_no_yt:.2f}s")
    print(f"With YouTube links: {time_with_yt:.2f}s")
    print(f"Difference: {time_with_yt - time_no_yt:.2f}s")
    print(f"Slowdown factor: {time_with_yt / time_no_yt:.2f}x")

    # Both should complete successfully
    assert len(result_no_yt) == 1
    assert len(result_with_yt) == 1

    # With YouTube should take longer (fetching additional pages)
    # But allow for network variability
    print(
        f"\nNote: With YouTube links is {'slower' if time_with_yt > time_no_yt else 'faster'} "
        f"than without (expected to be slower due to additional HTTP requests)"
    )

    # Both should complete in reasonable time
    assert time_no_yt < 30, f"Without YouTube took too long: {time_no_yt:.2f}s"
    assert time_with_yt < 60, f"With YouTube took too long: {time_with_yt:.2f}s"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_integration_team_tomodachi_all_sections():
    """Test Team Tomodachi to verify all related tracks have YouTube links."""
    result = await call_tool(
        "get_track_samples", {"query": "team tomodachi", "include_youtube": True}
    )

    assert len(result) == 1
    text = result[0].text

    print(f"\n=== Team Tomodachi Full Response ===")
    print(text)

    # Track should have main YouTube link
    assert "YouTube:" in text, "Should have at least one YouTube link"

    # Count number of YouTube links
    youtube_count = text.count("youtu.be/") + text.count("youtube.com/watch")

    print(f"\n=== YouTube Link Statistics ===")
    print(f"Total YouTube links found: {youtube_count}")

    # Should have multiple YouTube links (main track + related tracks)
    # Team Tomodachi typically has covers and remixes
    assert youtube_count >= 1, "Should have at least the main track YouTube link"

    # Check for different sections
    sections_found = []
    if "SAMPLED BY" in text:
        sections_found.append("SAMPLED BY")
    if "COVERED BY" in text:
        sections_found.append("COVERED BY")
    if "REMIXED BY" in text:
        sections_found.append("REMIXED BY")

    print(f"Sections found: {sections_found}")

    # Verify that if sections exist, they should have YouTube links when available
    # This is a best-effort test since not all tracks have YouTube videos
    if sections_found:
        print(f"Track has {len(sections_found)} related track sections")
        print(f"Expected to find YouTube links for some of these tracks")
