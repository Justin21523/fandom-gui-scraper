"""
Brave Search API integration for discovering Fandom wikis.

This module provides functionality to search for Fandom wikis using the Brave Search API,
validate results, and rank them by relevance.
"""

import os
import re
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

import requests
from pydantic import BaseModel, HttpUrl, validator


@dataclass
class FandomSearchResult:
    """
    Represents a single Fandom wiki search result.

    Attributes:
        url: Full Fandom wiki URL
        domain: Wiki subdomain (e.g., "onepiece")
        title: Page title from search result
        description: Meta description snippet
        relevance_score: Calculated relevance score (0-100)
        is_main_page: Whether this is the wiki main page
        rank: Original search result rank (1-based)
    """
    url: str
    domain: str
    title: str
    description: str
    relevance_score: float
    is_main_page: bool = False
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.url,
            "domain": self.domain,
            "title": self.title,
            "description": self.description,
            "relevance_score": self.relevance_score,
            "is_main_page": self.is_main_page,
            "rank": self.rank,
        }


class BraveSearchCache:
    """Simple file-based cache for Brave Search results."""

    def __init__(self, cache_dir: str = ".cache/brave_search", ttl_hours: int = 24):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cached results in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file."""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached results for query.

        Args:
            query: Search query

        Returns:
            Cached results if available and not expired, None otherwise
        """
        cache_key = self._get_cache_key(query)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if expired
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                cache_path.unlink()  # Delete expired cache
                return None

            return data['results']
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, query: str, results: List[Dict[str, Any]]):
        """
        Cache search results.

        Args:
            query: Search query
            results: Search results to cache
        """
        cache_key = self._get_cache_key(query)
        cache_path = self._get_cache_path(cache_key)

        data = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'results': results
        }

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear(self):
        """Clear all cached results."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, calls_per_second: int = 15, calls_per_month: int = 2000):
        """
        Initialize rate limiter.

        Args:
            calls_per_second: Maximum calls per second
            calls_per_month: Maximum calls per month
        """
        self.calls_per_second = calls_per_second
        self.calls_per_month = calls_per_month
        self.tokens = calls_per_second
        self.last_refill = time.time()
        self.monthly_usage = 0
        self.month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)

    def _refill_tokens(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.calls_per_second
        self.tokens = min(self.calls_per_second, self.tokens + tokens_to_add)
        self.last_refill = now

    def _check_monthly_limit(self):
        """Check and reset monthly usage counter."""
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0)

        if month_start > self.month_start:
            # New month, reset counter
            self.monthly_usage = 0
            self.month_start = month_start

    def acquire(self) -> bool:
        """
        Attempt to acquire a token for an API call.

        Returns:
            True if token acquired, False if rate limit exceeded
        """
        self._refill_tokens()
        self._check_monthly_limit()

        # Check monthly limit
        if self.monthly_usage >= self.calls_per_month:
            return False

        # Check per-second limit
        if self.tokens < 1:
            return False

        self.tokens -= 1
        self.monthly_usage += 1
        return True

    def wait(self):
        """Wait until a token is available."""
        while not self.acquire():
            time.sleep(0.1)


class BraveSearchClient:
    """
    Client for Brave Search API with Fandom wiki discovery capabilities.

    Features:
    - Intelligent query construction for Fandom wikis
    - Result validation and filtering
    - Relevance ranking algorithm
    - Rate limiting and caching
    - Error handling and retries
    """

    # Fandom URL pattern
    FANDOM_URL_PATTERN = re.compile(r'^https?://([a-z0-9-]+)\.fandom\.com(/wiki/.*)?$', re.IGNORECASE)

    def __init__(
        self,
        api_key: Optional[str] = None,
        calls_per_second: int = 15,
        calls_per_month: int = 2000,
        cache_enabled: bool = True,
        cache_ttl_hours: int = 24,
    ):
        """
        Initialize Brave Search client.

        Args:
            api_key: Brave Search API key (defaults to BRAVE_API_KEY env var)
            calls_per_second: Rate limit per second
            calls_per_month: Rate limit per month
            cache_enabled: Enable result caching
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.api_key = api_key or os.getenv('BRAVE_API_KEY')
        if not self.api_key:
            raise ValueError("Brave Search API key not found. Set BRAVE_API_KEY environment variable.")

        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'X-Subscription-Token': self.api_key,
        })

        self.rate_limiter = RateLimiter(calls_per_second, calls_per_month)
        self.cache = BraveSearchCache(ttl_hours=cache_ttl_hours) if cache_enabled else None

    def _construct_query(self, anime_name: str) -> str:
        """
        Construct optimized search query for Fandom wiki.

        Args:
            anime_name: Name of anime/series

        Returns:
            Optimized search query string
        """
        # Primary strategy: use site: operator for precision
        return f'{anime_name} site:fandom.com wiki'

    def _validate_fandom_url(self, url: str) -> bool:
        """
        Validate that URL is a Fandom wiki.

        Args:
            url: URL to validate

        Returns:
            True if valid Fandom URL, False otherwise
        """
        return bool(self.FANDOM_URL_PATTERN.match(url))

    def _extract_domain(self, url: str) -> Optional[str]:
        """
        Extract subdomain from Fandom URL.

        Args:
            url: Fandom URL

        Returns:
            Subdomain (e.g., "onepiece") or None if invalid
        """
        match = self.FANDOM_URL_PATTERN.match(url)
        return match.group(1) if match else None

    def _is_main_page(self, url: str) -> bool:
        """
        Check if URL is likely the main wiki page.

        Args:
            url: URL to check

        Returns:
            True if likely main page
        """
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Main page indicators
        main_page_patterns = [
            '/wiki',
            '/wiki/',
            '/wiki/main_page',
            f'/wiki/{self._extract_domain(url)}_wiki',
        ]

        return any(path == pattern or path.endswith(pattern) for pattern in main_page_patterns)

    def _calculate_relevance_score(
        self,
        result: Dict[str, Any],
        query: str,
        rank: int
    ) -> float:
        """
        Calculate relevance score for search result.

        Scoring factors:
        - Title match: 40 points (exact) or 20 points (partial)
        - URL structure: 15 points if has /wiki/
        - Domain relevance: 15 points if anime name in domain
        - URL keywords: 10 points if contains "characters"
        - Search rank: 20 points * (1 / rank)

        Args:
            result: Search result dict
            query: Original search query
            rank: Search result rank (1-based)

        Returns:
            Relevance score (0-100)
        """
        score = 0.0
        title = result.get('title', '').lower()
        url = result.get('url', '').lower()
        description = result.get('description', '').lower()

        # Extract anime name from query (remove 'site:' etc.)
        anime_name = re.sub(r'\s*site:[\w.]+\s*', '', query, flags=re.IGNORECASE)
        anime_name = re.sub(r'\s*wiki\s*', '', anime_name, flags=re.IGNORECASE).strip().lower()

        # Title matching
        if anime_name in title:
            # Exact match in title
            if title.startswith(anime_name) or title.endswith(anime_name):
                score += 40
            else:
                score += 20

        # URL structure
        if '/wiki/' in url:
            score += 15

        # Domain relevance
        domain = self._extract_domain(result.get('url', ''))
        if domain and anime_name.replace(' ', '') in domain:
            score += 15

        # Keyword bonuses
        if any(keyword in url for keyword in ['characters', 'character']):
            score += 10

        # Rank penalty (prefer higher-ranked results)
        rank_score = 20 * (1 / rank) if rank > 0 else 0
        score += rank_score

        # Cap at 100
        return min(100.0, score)

    def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Perform search using Brave API.

        Args:
            query: Search query
            count: Number of results to fetch

        Returns:
            List of raw search results

        Raises:
            requests.RequestException: If API request fails
            ValueError: If rate limit exceeded
        """
        # Check cache first
        if self.cache:
            cached_results = self.cache.get(query)
            if cached_results is not None:
                return cached_results

        # Check rate limit
        if not self.rate_limiter.acquire():
            monthly_remaining = self.rate_limiter.calls_per_month - self.rate_limiter.monthly_usage
            raise ValueError(
                f"Rate limit exceeded. Monthly calls remaining: {monthly_remaining}. "
                f"Please try again later or provide a direct Fandom URL."
            )

        # Make API request
        params = {
            'q': query,
            'count': count,
            'safesearch': 'moderate',
        }

        response = self.session.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        results = data.get('web', {}).get('results', [])

        # Cache results
        if self.cache:
            self.cache.set(query, results)

        return results

    def find_fandom_wiki(
        self,
        anime_name: str,
        top_n: int = 5,
        min_score: float = 10.0
    ) -> List[FandomSearchResult]:
        """
        Find Fandom wikis for given anime/series name.

        Args:
            anime_name: Name of anime/series to search for
            top_n: Maximum number of results to return
            min_score: Minimum relevance score to include

        Returns:
            List of validated and ranked Fandom search results

        Raises:
            requests.RequestException: If API request fails
            ValueError: If rate limit exceeded
        """
        # Construct and execute search
        query = self._construct_query(anime_name)
        raw_results = self.search(query, count=top_n * 2)  # Get extra to filter

        # Filter and score results
        fandom_results = []
        for rank, result in enumerate(raw_results, start=1):
            url = result.get('url', '')

            # Validate URL
            if not self._validate_fandom_url(url):
                continue

            # Calculate relevance score
            score = self._calculate_relevance_score(result, query, rank)

            # Skip if below minimum score
            if score < min_score:
                continue

            # Extract domain
            domain = self._extract_domain(url)
            if not domain:
                continue

            # Create result object
            fandom_result = FandomSearchResult(
                url=url,
                domain=domain,
                title=result.get('title', ''),
                description=result.get('description', ''),
                relevance_score=score,
                is_main_page=self._is_main_page(url),
                rank=rank,
            )

            fandom_results.append(fandom_result)

        # Sort by relevance score (descending)
        fandom_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Return top N
        return fandom_results[:top_n]

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return {
            'monthly_usage': self.rate_limiter.monthly_usage,
            'monthly_limit': self.rate_limiter.calls_per_month,
            'monthly_remaining': self.rate_limiter.calls_per_month - self.rate_limiter.monthly_usage,
            'month_start': self.rate_limiter.month_start.isoformat(),
        }


# Convenience function
def search_fandom_wiki(anime_name: str, api_key: Optional[str] = None) -> List[FandomSearchResult]:
    """
    Convenience function to search for Fandom wiki.

    Args:
        anime_name: Name of anime/series
        api_key: Brave API key (optional, uses env var if not provided)

    Returns:
        List of Fandom search results
    """
    client = BraveSearchClient(api_key=api_key)
    return client.find_fandom_wiki(anime_name)


if __name__ == "__main__":
    # Test the module
    import sys

    if len(sys.argv) < 2:
        print("Usage: python brave_search.py <anime_name>")
        sys.exit(1)

    anime_name = " ".join(sys.argv[1:])

    try:
        print(f"Searching for '{anime_name}'...\n")
        results = search_fandom_wiki(anime_name)

        if not results:
            print("No Fandom wikis found.")
        else:
            print(f"Found {len(results)} Fandom wikis:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   Score: {result.relevance_score:.1f}/100")
                print(f"   Domain: {result.domain}")
                print(f"   Main Page: {result.is_main_page}")
                print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
