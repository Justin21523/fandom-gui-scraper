# scraper/utils/url_manager.py
"""
URL management utilities for web scraping.

This module provides utilities for URL handling, validation,
normalization, and queue management for systematic crawling.
"""

import re
import hashlib
import time
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
from urllib.robotparser import RobotFileParser
import logging

logger = logging.getLogger(__name__)


class URLNormalizer:
    """
    Normalize URLs for consistent handling and deduplication.

    This class provides methods to clean and standardize URLs
    to avoid crawling duplicate content.
    """

    def __init__(
        self,
        remove_fragments: bool = True,
        remove_query_params: Optional[List[str]] = None,
        lowercase_scheme_host: bool = True,
    ):
        """
        Initialize URL normalizer.

        Args:
            remove_fragments: Whether to remove URL fragments (#section)
            remove_query_params: Query parameters to remove
            lowercase_scheme_host: Whether to lowercase scheme and host
        """
        self.remove_fragments = remove_fragments
        self.remove_query_params = remove_query_params or []
        self.lowercase_scheme_host = lowercase_scheme_host

    def normalize(self, url: str) -> str:
        """
        Normalize a URL according to configured rules.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        if not url:
            return url

        try:
            parsed = urlparse(url.strip())

            # Normalize scheme and host
            scheme = (
                parsed.scheme.lower() if self.lowercase_scheme_host else parsed.scheme
            )
            netloc = (
                parsed.netloc.lower() if self.lowercase_scheme_host else parsed.netloc
            )

            # Remove default ports
            if ":80" in netloc and scheme == "http":
                netloc = netloc.replace(":80", "")
            elif ":443" in netloc and scheme == "https":
                netloc = netloc.replace(":443", "")

            # Normalize path
            path = parsed.path
            if not path:
                path = "/"

            # Handle query parameters
            query = parsed.query
            if self.remove_query_params and query:
                params = parse_qs(query)
                for param in self.remove_query_params:
                    params.pop(param, None)
                query = urlencode(params, doseq=True)

            # Remove fragment if configured
            fragment = "" if self.remove_fragments else parsed.fragment

            normalized = urlunparse(
                (scheme, netloc, path, parsed.params, query, fragment)
            )
            return normalized

        except Exception as e:
            logger.warning(f"Error normalizing URL '{url}': {e}")
            return url

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs belong to the same domain.

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            True if same domain
        """
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except:
            return False

    def get_domain(self, url: str) -> Optional[str]:
        """
        Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain or None if invalid URL
        """
        try:
            return urlparse(url).netloc.lower()
        except:
            return None


class URLValidator:
    """
    Validate URLs against various criteria.

    This class provides methods to check if URLs are valid
    and meet specific crawling criteria.
    """

    def __init__(
        self,
        allowed_schemes: Optional[List[str]] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        allowed_extensions: Optional[List[str]] = None,
        blocked_extensions: Optional[List[str]] = None,
    ):
        """
        Initialize URL validator.

        Args:
            allowed_schemes: Allowed URL schemes (http, https)
            allowed_domains: List of allowed domains
            blocked_domains: List of blocked domains
            allowed_extensions: Allowed file extensions
            blocked_extensions: Blocked file extensions
        """
        self.allowed_schemes = allowed_schemes or ["http", "https"]
        self.allowed_domains = [d.lower() for d in (allowed_domains or [])]
        self.blocked_domains = [d.lower() for d in (blocked_domains or [])]
        self.allowed_extensions = [e.lower() for e in (allowed_extensions or [])]
        self.blocked_extensions = [e.lower() for e in (blocked_extensions or [])]

    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid according to configured rules.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        if not url or not isinstance(url, str):
            return False

        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme.lower() not in self.allowed_schemes:
                return False

            # Check if URL has valid structure
            if not parsed.netloc:
                return False

            # Check domain restrictions
            domain = parsed.netloc.lower()

            if self.blocked_domains and any(
                bd in domain for bd in self.blocked_domains
            ):
                return False

            if self.allowed_domains and not any(
                ad in domain for ad in self.allowed_domains
            ):
                return False

            # Check file extension restrictions
            path = parsed.path.lower()
            if "." in path:
                extension = path.split(".")[-1]

                if self.blocked_extensions and extension in self.blocked_extensions:
                    return False

                if self.allowed_extensions and extension not in self.allowed_extensions:
                    return False

            return True

        except Exception as e:
            logger.warning(f"Error validating URL '{url}': {e}")
            return False

    def is_crawlable_url(self, url: str) -> bool:
        """
        Check if URL points to crawlable content.

        Args:
            url: URL to check

        Returns:
            True if URL is crawlable
        """
        if not self.is_valid_url(url):
            return False

        # Check for non-crawlable patterns
        non_crawlable_patterns = [
            r"\.(?:css|js|ico|png|jpg|jpeg|gif|svg|pdf|zip|rar|exe|dmg)$",
            r"mailto:",
            r"javascript:",
            r"tel:",
            r"#",  # Fragment-only URLs
        ]

        for pattern in non_crawlable_patterns:
            if re.search(pattern, url.lower()):
                return False

        return True


class URLQueue:
    """
    Manage a queue of URLs for systematic crawling.

    This class provides priority-based URL queue management
    with deduplication and filtering capabilities.
    """

    def __init__(
        self,
        normalizer: Optional[URLNormalizer] = None,
        validator: Optional[URLValidator] = None,
    ):
        """
        Initialize URL queue.

        Args:
            normalizer: URL normalizer instance
            validator: URL validator instance
        """
        self.normalizer = normalizer or URLNormalizer()
        self.validator = validator or URLValidator()

        self.queue = []  # List of (priority, url, metadata)
        self.seen_urls = set()  # Set of normalized URLs we've seen
        self.completed_urls = set()  # Set of URLs we've processed
        self.failed_urls = {}  # Dict of failed URLs with error counts

        self.max_retries = 3
        self.queue_size_limit = 10000

    def add_url(
        self, url: str, priority: int = 0, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add URL to the queue.

        Args:
            url: URL to add
            priority: Priority (higher numbers = higher priority)
            metadata: Additional metadata for the URL

        Returns:
            True if URL was added, False if skipped
        """
        if not url:
            return False

        # Validate URL
        if not self.validator.is_crawlable_url(url):
            return False

        # Normalize URL
        normalized_url = self.normalizer.normalize(url)

        # Check if we've already seen this URL
        if normalized_url in self.seen_urls:
            return False

        # Check if URL failed too many times
        if normalized_url in self.failed_urls:
            if self.failed_urls[normalized_url] >= self.max_retries:
                return False

        # Check queue size limit
        if len(self.queue) >= self.queue_size_limit:
            logger.warning(f"Queue size limit reached ({self.queue_size_limit})")
            return False

        # Add to queue
        self.queue.append((-priority, normalized_url, metadata or {}))
        self.seen_urls.add(normalized_url)

        # Keep queue sorted by priority
        self.queue.sort(key=lambda x: x[0])

        return True

    def add_urls(
        self, urls: List[Union[str, Tuple[str, int]]], default_priority: int = 0
    ) -> int:
        """
        Add multiple URLs to the queue.

        Args:
            urls: List of URLs or (url, priority) tuples
            default_priority: Default priority for URLs without priority

        Returns:
            Number of URLs successfully added
        """
        added_count = 0

        for url_item in urls:
            if isinstance(url_item, tuple):
                url, priority = url_item
            else:
                url, priority = url_item, default_priority

            if self.add_url(url, priority):
                added_count += 1

        return added_count

    def get_next_url(self) -> Optional[Tuple[str, Dict]]:
        """
        Get the next URL from the queue.

        Returns:
            Tuple of (url, metadata) or None if queue is empty
        """
        if not self.queue:
            return None

        _, url, metadata = self.queue.pop(0)
        return url, metadata

    def mark_completed(self, url: str):
        """
        Mark URL as completed.

        Args:
            url: URL that was completed
        """
        normalized_url = self.normalizer.normalize(url)
        self.completed_urls.add(normalized_url)

        # Remove from failed URLs if it was there
        self.failed_urls.pop(normalized_url, None)

    def mark_failed(self, url: str, error: Optional[str] = None):
        """
        Mark URL as failed.

        Args:
            url: URL that failed
            error: Error message
        """
        normalized_url = self.normalizer.normalize(url)
        self.failed_urls[normalized_url] = self.failed_urls.get(normalized_url, 0) + 1

        logger.warning(f"URL failed ({self.failed_urls[normalized_url]} times): {url}")
        if error:
            logger.warning(f"Error: {error}")

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.queue) == 0

    def size(self) -> int:
        """Get current queue size."""
        return len(self.queue)

    def get_stats(self) -> Dict[str, int]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        return {
            "queue_size": len(self.queue),
            "seen_urls": len(self.seen_urls),
            "completed_urls": len(self.completed_urls),
            "failed_urls": len(self.failed_urls),
            "total_failures": sum(self.failed_urls.values()),
        }

    def clear(self):
        """Clear all URLs from the queue."""
        self.queue.clear()
        self.seen_urls.clear()
        self.completed_urls.clear()
        self.failed_urls.clear()


class FandomURLManager:
    """
    Specialized URL manager for Fandom wikis.

    This class provides Fandom-specific URL handling including
    page type detection and URL generation.
    """

    def __init__(self, wiki_domain: str):
        """
        Initialize Fandom URL manager.

        Args:
            wiki_domain: Domain of the Fandom wiki
        """
        self.wiki_domain = wiki_domain
        self.base_url = f"https://{wiki_domain}"

        # Initialize components
        validator = URLValidator(
            allowed_domains=[wiki_domain],
            blocked_extensions=["css", "js", "ico", "png", "jpg", "jpeg", "gif"],
        )

        normalizer = URLNormalizer(
            remove_query_params=["action", "oldid", "diff", "printable"]
        )

        self.queue = URLQueue(normalizer, validator)

    def get_page_type(self, url: str) -> str:
        """
        Determine the type of Fandom page from URL.

        Args:
            url: Page URL

        Returns:
            Page type ('article', 'category', 'file', 'special', 'user', etc.)
        """
        try:
            parsed = urlparse(url)
            path = parsed.path

            if "/wiki/" not in path:
                return "unknown"

            page_part = path.split("/wiki/")[-1]

            # Check for namespace prefixes
            if ":" in page_part:
                namespace = page_part.split(":")[0].lower()

                namespace_map = {
                    "category": "category",
                    "file": "file",
                    "image": "file",
                    "user": "user",
                    "special": "special",
                    "template": "template",
                    "help": "help",
                    "mediawiki": "mediawiki",
                }

                return namespace_map.get(namespace, "article")

            return "article"

        except Exception:
            return "unknown"

    def build_page_url(self, page_title: str) -> str:
        """
        Build URL for a wiki page.

        Args:
            page_title: Title of the page

        Returns:
            Full page URL
        """
        # Replace spaces with underscores
        safe_title = page_title.replace(" ", "_")
        return f"{self.base_url}/wiki/{safe_title}"

    def build_category_url(self, category_name: str) -> str:
        """
        Build URL for a category page.

        Args:
            category_name: Name of the category

        Returns:
            Category page URL
        """
        return self.build_page_url(f"Category:{category_name}")

    def build_api_url(self, params: Dict[str, str]) -> str:
        """
        Build API URL with parameters.

        Args:
            params: API parameters

        Returns:
            API URL with parameters
        """
        base_api_url = f"{self.base_url}/api.php"
        param_string = urlencode(params)
        return f"{base_api_url}?{param_string}"

    def build_search_url(self, query: str, limit: int = 50) -> str:
        """
        Build search URL for the wiki.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Search URL
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(limit),
            "format": "json",
        }
        return self.build_api_url(params)

    def extract_page_title(self, url: str) -> Optional[str]:
        """
        Extract page title from Fandom URL.

        Args:
            url: Fandom page URL

        Returns:
            Page title or None if not extractable
        """
        try:
            parsed = urlparse(url)
            path = parsed.path

            if "/wiki/" not in path:
                return None

            page_title = path.split("/wiki/")[-1]
            # Replace underscores with spaces
            return page_title.replace("_", " ")

        except Exception:
            return None

    def is_character_page(self, url: str) -> bool:
        """
        Heuristic to determine if URL is a character page.

        Args:
            url: Page URL

        Returns:
            True if likely a character page
        """
        page_title = self.extract_page_title(url)
        if not page_title:
            return False

        # Common character page indicators
        character_indicators = [
            "character",
            "protagonist",
            "antagonist",
            "villain",
            "hero",
            "member",
            "captain",
            "admiral",
            "king",
            "queen",
            "prince",
            "princess",
        ]

        title_lower = page_title.lower()

        # Check if title contains character indicators
        for indicator in character_indicators:
            if indicator in title_lower:
                return True

        # Check if it's not clearly a non-character page
        non_character_indicators = [
            "episode",
            "chapter",
            "arc",
            "saga",
            "volume",
            "season",
            "list of",
            "category:",
            "file:",
            "template:",
            "gallery",
        ]

        for indicator in non_character_indicators:
            if indicator in title_lower:
                return False

        # If no clear indicators, assume it might be a character
        return True

    def add_character_urls(self, character_names: List[str], priority: int = 10) -> int:
        """
        Add character page URLs to the queue.

        Args:
            character_names: List of character names
            priority: Priority for these URLs

        Returns:
            Number of URLs added
        """
        urls = []
        for name in character_names:
            url = self.build_page_url(name)
            metadata = {"page_type": "character", "character_name": name}
            urls.append((url, priority, metadata))

        added_count = 0
        for url, prio, meta in urls:
            if self.queue.add_url(url, prio, meta):
                added_count += 1

        return added_count

    def add_category_urls(self, category_names: List[str], priority: int = 5) -> int:
        """
        Add category page URLs to the queue.

        Args:
            category_names: List of category names
            priority: Priority for these URLs

        Returns:
            Number of URLs added
        """
        urls = []
        for name in category_names:
            url = self.build_category_url(name)
            metadata = {"page_type": "category", "category_name": name}
            urls.append((url, priority, metadata))

        added_count = 0
        for url, prio, meta in urls:
            if self.queue.add_url(url, prio, meta):
                added_count += 1

        return added_count


class RobotsChecker:
    """
    Check robots.txt compliance for URLs.

    This class helps ensure crawling respects robots.txt rules.
    """

    def __init__(self, user_agent: str = "*"):
        """
        Initialize robots checker.

        Args:
            user_agent: User agent string to check rules for
        """
        self.user_agent = user_agent
        self.robots_cache = {}  # Cache robots.txt by domain
        self.cache_timeout = 3600  # 1 hour cache timeout

    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if URL can be fetched
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Get robots.txt for domain
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"

            # Check cache first
            current_time = time.time()
            if domain in self.robots_cache:
                robots_parser, cache_time = self.robots_cache[domain]
                if current_time - cache_time < self.cache_timeout:
                    return robots_parser.can_fetch(self.user_agent, url)

            # Fetch and parse robots.txt
            robots_parser = RobotFileParser()
            robots_parser.set_url(robots_url)

            try:
                robots_parser.read()
                self.robots_cache[domain] = (robots_parser, current_time)
                return robots_parser.can_fetch(self.user_agent, url)
            except Exception as e:
                logger.warning(f"Error reading robots.txt for {domain}: {e}")
                # If robots.txt can't be read, assume crawling is allowed
                return True

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get crawl delay from robots.txt.

        Args:
            url: URL to check

        Returns:
            Crawl delay in seconds or None
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            if domain in self.robots_cache:
                robots_parser, _ = self.robots_cache[domain]
                return robots_parser.crawl_delay(self.user_agent)

        except Exception:
            pass

        return None


class SitemapParser:
    """
    Parse XML sitemaps to discover URLs.

    This class helps discover pages through sitemap files.
    """

    def __init__(self):
        """Initialize sitemap parser."""
        self.discovered_urls = set()

    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Parse sitemap and extract URLs.

        Args:
            sitemap_url: URL of the sitemap

        Returns:
            List of discovered URLs
        """
        urls = []

        try:
            import xml.etree.ElementTree as ET
            import requests

            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            # Handle different sitemap formats
            namespaces = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Look for URL entries
            for url_elem in root.findall(".//sitemap:url", namespaces):
                loc_elem = url_elem.find("sitemap:loc", namespaces)
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text.strip())

            # Look for sitemap index entries
            for sitemap_elem in root.findall(".//sitemap:sitemap", namespaces):
                loc_elem = sitemap_elem.find("sitemap:loc", namespaces)
                if loc_elem is not None and loc_elem.text:
                    # Recursively parse sub-sitemaps
                    sub_urls = self.parse_sitemap(loc_elem.text.strip())
                    urls.extend(sub_urls)

            self.discovered_urls.update(urls)

        except Exception as e:
            logger.warning(f"Error parsing sitemap {sitemap_url}: {e}")

        return urls

    def discover_sitemaps(self, domain: str) -> List[str]:
        """
        Discover sitemap URLs for a domain.

        Args:
            domain: Domain to check for sitemaps

        Returns:
            List of sitemap URLs
        """
        sitemap_urls = []

        # Common sitemap locations
        common_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemaps.xml",
            "/sitemap.txt",
        ]

        base_url = f"https://{domain}"

        for path in common_paths:
            sitemap_url = f"{base_url}{path}"
            try:
                import requests

                response = requests.head(sitemap_url, timeout=10)
                if response.status_code == 200:
                    sitemap_urls.append(sitemap_url)
            except Exception:
                continue

        # Check robots.txt for sitemap declarations
        try:
            import requests

            robots_url = f"{base_url}/robots.txt"
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                for line in response.text.split("\n"):
                    if line.strip().lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        if sitemap_url not in sitemap_urls:
                            sitemap_urls.append(sitemap_url)
        except Exception:
            pass

        return sitemap_urls
