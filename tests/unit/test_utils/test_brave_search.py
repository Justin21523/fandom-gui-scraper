"""
Unit tests for Brave Search API client.

Tests cover:
- BraveSearchClient initialization and configuration
- Rate limiting with token bucket algorithm
- File-based caching with expiration
- URL validation and domain extraction
- Relevance scoring algorithm
- Search query construction
- API error handling
"""

import os
import json
import time
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from utils.brave_search import (
    BraveSearchClient,
    BraveSearchCache,
    RateLimiter,
    FandomSearchResult,
    search_fandom_wiki,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_brave_api_key():
    """Mock API key for testing."""
    return "test_api_key_12345"


@pytest.fixture
def sample_brave_response():
    """Sample Brave Search API response."""
    return {
        "web": {
            "results": [
                {
                    "title": "One Piece Wiki | Fandom",
                    "url": "https://onepiece.fandom.com/wiki/Main_Page",
                    "description": "Welcome to the One Piece Wiki, the encyclopedia for the manga and anime One Piece.",
                },
                {
                    "title": "Characters - One Piece Wiki",
                    "url": "https://onepiece.fandom.com/wiki/Category:Characters",
                    "description": "List of all characters in One Piece universe.",
                },
                {
                    "title": "Monkey D. Luffy - One Piece Wiki",
                    "url": "https://onepiece.fandom.com/wiki/Monkey_D._Luffy",
                    "description": "Monkey D. Luffy is the main protagonist of One Piece.",
                },
                {
                    "title": "Not a Fandom URL",
                    "url": "https://example.com/onepiece",
                    "description": "This should be filtered out",
                },
            ]
        }
    }


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return str(cache_dir)


# ============================================================================
# TEST: FandomSearchResult
# ============================================================================

class TestFandomSearchResult:
    """Test FandomSearchResult dataclass."""

    def test_model_creation(self):
        """Test creating a FandomSearchResult instance."""
        result = FandomSearchResult(
            url="https://onepiece.fandom.com/wiki/Main_Page",
            domain="onepiece",
            title="One Piece Wiki",
            description="Official wiki",
            relevance_score=95.5,
            is_main_page=True,
            rank=1,
        )

        assert result.url == "https://onepiece.fandom.com/wiki/Main_Page"
        assert result.domain == "onepiece"
        assert result.title == "One Piece Wiki"
        assert result.description == "Official wiki"
        assert result.relevance_score == 95.5
        assert result.is_main_page is True
        assert result.rank == 1

    def test_relevance_score_range(self):
        """Test relevance score is within valid range."""
        result = FandomSearchResult(
            url="https://test.fandom.com/wiki",
            domain="test",
            title="Test",
            description="Test",
            relevance_score=75.0,
        )

        assert 0 <= result.relevance_score <= 100

    def test_is_main_page_detection(self):
        """Test main page flag."""
        result_main = FandomSearchResult(
            url="https://onepiece.fandom.com/wiki/Main_Page",
            domain="onepiece",
            title="Main",
            description="Main",
            relevance_score=50.0,
            is_main_page=True,
        )

        result_not_main = FandomSearchResult(
            url="https://onepiece.fandom.com/wiki/Characters",
            domain="onepiece",
            title="Characters",
            description="Characters",
            relevance_score=50.0,
            is_main_page=False,
        )

        assert result_main.is_main_page is True
        assert result_not_main.is_main_page is False

    def test_domain_extraction_from_url(self):
        """Test domain is correctly extracted."""
        result = FandomSearchResult(
            url="https://dragonball.fandom.com/wiki/Goku",
            domain="dragonball",
            title="Goku",
            description="Character",
            relevance_score=80.0,
        )

        assert result.domain == "dragonball"

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = FandomSearchResult(
            url="https://test.fandom.com/wiki",
            domain="test",
            title="Test Wiki",
            description="A test",
            relevance_score=50.0,
            is_main_page=False,
            rank=2,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["url"] == "https://test.fandom.com/wiki"
        assert result_dict["domain"] == "test"
        assert result_dict["title"] == "Test Wiki"
        assert result_dict["description"] == "A test"
        assert result_dict["relevance_score"] == 50.0
        assert result_dict["is_main_page"] is False
        assert result_dict["rank"] == 2


# ============================================================================
# TEST: BraveSearchCache
# ============================================================================

class TestBraveSearchCache:
    """Test file-based caching system."""

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache directory creation."""
        cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=24)

        assert cache.cache_dir.exists()
        assert cache.cache_dir.is_dir()
        assert cache.ttl == timedelta(hours=24)

    def test_cache_hit(self, temp_cache_dir):
        """Test retrieving cached results."""
        cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=24)

        query = "one piece site:fandom.com wiki"
        results = [{"url": "https://onepiece.fandom.com", "title": "One Piece"}]

        # Set cache
        cache.set(query, results)

        # Get from cache
        cached_results = cache.get(query)

        assert cached_results is not None
        assert cached_results == results

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss returns None."""
        cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=24)

        result = cache.get("non_existent_query")

        assert result is None

    def test_cache_expiration_24h(self, temp_cache_dir):
        """Test cache expiration after TTL."""
        cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=1)

        query = "test query"
        results = [{"test": "data"}]

        # Set cache
        cache.set(query, results)

        # Manually modify cache file timestamp to be expired
        cache_key = cache._get_cache_key(query)
        cache_path = cache._get_cache_path(cache_key)

        with open(cache_path, 'r') as f:
            data = json.load(f)

        # Set timestamp to 2 hours ago
        expired_time = datetime.now() - timedelta(hours=2)
        data['timestamp'] = expired_time.isoformat()

        with open(cache_path, 'w') as f:
            json.dump(data, f)

        # Try to get expired cache
        cached_results = cache.get(query)

        assert cached_results is None
        assert not cache_path.exists()  # Cache file should be deleted

    def test_cache_file_creation(self, temp_cache_dir):
        """Test cache file is created correctly."""
        cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=24)

        query = "naruto wiki"
        results = [{"url": "https://naruto.fandom.com"}]

        cache.set(query, results)

        cache_key = cache._get_cache_key(query)
        cache_path = cache._get_cache_path(cache_key)

        assert cache_path.exists()

        with open(cache_path, 'r') as f:
            data = json.load(f)

        assert 'timestamp' in data
        assert 'query' in data
        assert 'results' in data
        assert data['query'] == query
        assert data['results'] == results

    def test_cache_cleanup_old_entries(self, temp_cache_dir):
        """Test clearing all cached entries."""
        cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=24)

        # Add multiple cache entries
        cache.set("query1", [{"result": 1}])
        cache.set("query2", [{"result": 2}])
        cache.set("query3", [{"result": 3}])

        # Verify files exist
        cache_files = list(cache.cache_dir.glob("*.json"))
        assert len(cache_files) == 3

        # Clear cache
        cache.clear()

        # Verify all files deleted
        cache_files = list(cache.cache_dir.glob("*.json"))
        assert len(cache_files) == 0

    def test_invalid_cache_file_handling(self, temp_cache_dir):
        """Test handling of corrupted cache files."""
        cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=24)

        # Create invalid cache file
        cache_key = cache._get_cache_key("test_query")
        cache_path = cache._get_cache_path(cache_key)

        with open(cache_path, 'w') as f:
            f.write("invalid json {{{")

        # Try to get from corrupted cache
        result = cache.get("test_query")

        assert result is None
        assert not cache_path.exists()  # Should be deleted


# ============================================================================
# TEST: RateLimiter
# ============================================================================

class TestRateLimiter:
    """Test token bucket rate limiter."""

    def test_token_bucket_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(calls_per_second=15, calls_per_month=2000)

        assert limiter.calls_per_second == 15
        assert limiter.calls_per_month == 2000
        assert limiter.tokens == 15  # Starts with full bucket
        assert limiter.monthly_usage == 0

    def test_rate_limit_15_per_second(self):
        """Test per-second rate limiting."""
        limiter = RateLimiter(calls_per_second=5, calls_per_month=10000)

        # Should be able to acquire 5 tokens immediately
        for i in range(5):
            assert limiter.acquire() is True

        # 6th call should fail (bucket empty)
        assert limiter.acquire() is False

    def test_rate_limit_2000_per_month(self):
        """Test monthly rate limiting."""
        limiter = RateLimiter(calls_per_second=100, calls_per_month=10)

        # Patch _check_monthly_limit to prevent reset
        with patch.object(limiter, '_check_monthly_limit'):
            # Acquire 10 times to reach monthly limit
            for i in range(10):
                acquired = limiter.acquire()
                assert acquired is True, f"Expected True for call {i+1}/10"

            # Verify we've reached the limit
            assert limiter.monthly_usage == 10

            # 11th call should fail due to monthly limit (even with tokens available)
            acquired = limiter.acquire()
            assert acquired is False, "Expected False after reaching monthly limit"

    def test_wait_when_rate_exceeded(self):
        """Test wait method blocks until token available."""
        limiter = RateLimiter(calls_per_second=10, calls_per_month=1000)

        # Exhaust tokens
        for i in range(10):
            limiter.acquire()

        # wait() should block briefly then succeed
        start_time = time.time()
        limiter.wait()
        elapsed = time.time() - start_time

        # Should have waited at least 0.1 seconds (refill time)
        assert elapsed >= 0.1

    def test_reset_after_time_window(self):
        """Test monthly usage reset."""
        limiter = RateLimiter(calls_per_second=10, calls_per_month=50)

        # Set usage to 50
        limiter.monthly_usage = 50

        # Simulate month change
        limiter.month_start = datetime.now().replace(day=1) - timedelta(days=31)

        # Check monthly limit (should reset)
        limiter._check_monthly_limit()

        assert limiter.monthly_usage == 0

    def test_token_refill_over_time(self):
        """Test tokens refill based on time elapsed."""
        limiter = RateLimiter(calls_per_second=10, calls_per_month=1000)

        # Exhaust tokens
        for i in range(10):
            limiter.acquire()

        # Wait for refill
        time.sleep(0.5)  # Should refill 5 tokens

        # Should be able to acquire again
        assert limiter.acquire() is True


# ============================================================================
# TEST: BraveSearchClient
# ============================================================================

class TestBraveSearchClient:
    """Test Brave Search API client."""

    def test_initialization(self, mock_brave_api_key):
        """Test client initialization with API key."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            assert client.api_key == mock_brave_api_key
            assert client.base_url == "https://api.search.brave.com/res/v1/web/search"
            assert client.rate_limiter is not None
            assert client.cache is not None

    def test_api_key_loading_from_env(self, mock_brave_api_key):
        """Test API key loaded from environment variable."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            assert client.api_key == mock_brave_api_key

    def test_api_key_missing_raises_error(self):
        """Test error raised when API key not provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Brave Search API key not found"):
                BraveSearchClient()

    def test_search_query_construction(self, mock_brave_api_key):
        """Test search query is constructed correctly."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            query = client._construct_query("One Piece")

            assert "One Piece" in query
            assert "site:fandom.com" in query
            assert "wiki" in query

    def test_url_validation_valid_fandom_urls(self, mock_brave_api_key):
        """Test validation of valid Fandom URLs."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            valid_urls = [
                "https://onepiece.fandom.com/wiki/Main_Page",
                "https://naruto.fandom.com/wiki/Naruto_Uzumaki",
                "https://dragonball.fandom.com/wiki/Goku",  # Must have path after /wiki
                "https://my-hero-academia.fandom.com/wiki/Characters",
            ]

            for url in valid_urls:
                assert client._validate_fandom_url(url) is True

    def test_url_validation_invalid_urls(self, mock_brave_api_key):
        """Test validation rejects invalid URLs."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            invalid_urls = [
                "https://example.com/wiki",
                "https://fandom.com",  # No subdomain
                "https://onepiece.wikia.com",  # Old Wikia domain
                "https://onepiece.fandom.net",  # Wrong TLD
                "not-a-url",
                "",
            ]

            for url in invalid_urls:
                assert client._validate_fandom_url(url) is False

    def test_domain_extraction(self, mock_brave_api_key):
        """Test extracting subdomain from Fandom URL."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            test_cases = [
                ("https://onepiece.fandom.com/wiki/Main_Page", "onepiece"),
                ("https://dragon-ball.fandom.com/wiki/Goku", "dragon-ball"),
                ("https://my-hero-academia.fandom.com/wiki/Main_Page", "my-hero-academia"),
                ("https://example.com", None),  # Invalid URL (not fandom.com)
            ]

            for url, expected_domain in test_cases:
                domain = client._extract_domain(url)
                assert domain == expected_domain

    def test_relevance_scoring_algorithm(self, mock_brave_api_key):
        """Test relevance score calculation."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            query = "one piece site:fandom.com wiki"

            # High relevance: exact title match, wiki in URL
            high_score_result = {
                "url": "https://onepiece.fandom.com/wiki/Main_Page",
                "title": "One Piece Wiki | Fandom",
                "description": "Official wiki",
            }

            score_high = client._calculate_relevance_score(high_score_result, query, rank=1)

            # Low relevance: no title match, no wiki in URL
            low_score_result = {
                "url": "https://random.fandom.com/page",
                "title": "Random Page",
                "description": "Some page",
            }

            score_low = client._calculate_relevance_score(low_score_result, query, rank=10)

            assert score_high > score_low
            assert 0 <= score_high <= 100
            assert 0 <= score_low <= 100

    @patch('utils.brave_search.requests.Session.get')
    def test_find_fandom_wiki_success(self, mock_get, mock_brave_api_key, sample_brave_response):
        """Test successful Fandom wiki search."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = sample_brave_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = BraveSearchClient(cache_enabled=False)
            results = client.find_fandom_wiki("One Piece", top_n=5)

            assert len(results) > 0
            assert all(isinstance(r, FandomSearchResult) for r in results)
            assert all(r.domain == "onepiece" for r in results)
            assert all(0 <= r.relevance_score <= 100 for r in results)

            # Results should be sorted by score (descending)
            scores = [r.relevance_score for r in results]
            assert scores == sorted(scores, reverse=True)

    @patch('utils.brave_search.requests.Session.get')
    def test_find_fandom_wiki_no_results(self, mock_get, mock_brave_api_key):
        """Test search with no valid results."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            # Mock empty response
            mock_response = Mock()
            mock_response.json.return_value = {"web": {"results": []}}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = BraveSearchClient(cache_enabled=False)
            results = client.find_fandom_wiki("NonExistentAnime", top_n=5)

            assert len(results) == 0

    @patch('utils.brave_search.requests.Session.get')
    def test_search_with_cache(self, mock_get, mock_brave_api_key, sample_brave_response, temp_cache_dir):
        """Test search uses cache on second call."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = sample_brave_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = BraveSearchClient(cache_enabled=True)
            client.cache = BraveSearchCache(cache_dir=temp_cache_dir, ttl_hours=24)

            # First call - should hit API
            results1 = client.find_fandom_wiki("One Piece", top_n=3)
            assert mock_get.call_count == 1

            # Second call - should use cache
            results2 = client.find_fandom_wiki("One Piece", top_n=3)
            assert mock_get.call_count == 1  # No additional API call

            assert len(results1) == len(results2)

    @patch('utils.brave_search.requests.Session.get')
    def test_rate_limit_exceeded_error(self, mock_get, mock_brave_api_key):
        """Test error when rate limit exceeded."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            # Don't need to mock the response since we won't get that far
            client = BraveSearchClient(
                calls_per_second=10,
                calls_per_month=5,
                cache_enabled=False
            )

            # Patch _check_monthly_limit and set monthly usage to limit
            with patch.object(client.rate_limiter, '_check_monthly_limit'):
                client.rate_limiter.monthly_usage = 5

                # Should raise ValueError due to monthly limit (before hitting API)
                with pytest.raises(ValueError, match="Rate limit exceeded"):
                    client.search("test query")

                # Verify we never called the API
                mock_get.assert_not_called()

    def test_get_usage_stats(self, mock_brave_api_key):
        """Test getting API usage statistics."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            client = BraveSearchClient()

            stats = client.get_usage_stats()

            assert 'monthly_usage' in stats
            assert 'monthly_limit' in stats
            assert 'monthly_remaining' in stats
            assert 'month_start' in stats
            assert stats['monthly_limit'] == 2000
            assert stats['monthly_remaining'] <= 2000


# ============================================================================
# TEST: Convenience Functions
# ============================================================================

class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch('utils.brave_search.BraveSearchClient.find_fandom_wiki')
    def test_search_fandom_wiki_function(self, mock_find, mock_brave_api_key):
        """Test convenience function for searching wikis."""
        with patch.dict(os.environ, {'BRAVE_API_KEY': mock_brave_api_key}):
            # Mock return value
            mock_results = [
                FandomSearchResult(
                    url="https://onepiece.fandom.com/wiki",
                    domain="onepiece",
                    title="One Piece Wiki",
                    description="Official",
                    relevance_score=95.0,
                )
            ]
            mock_find.return_value = mock_results

            results = search_fandom_wiki("One Piece")

            assert results == mock_results
            mock_find.assert_called_once_with("One Piece")
