# utils/network_utils.py
"""
Network utilities for HTTP requests, rate limiting, and connection management.
Provides robust networking capabilities for the scraper application.
"""

import logging
import time
import random
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class NetworkUtils:
    """
    Comprehensive network utilities for web scraping.

    Features:
    - HTTP session management with retries
    - Rate limiting and backoff strategies
    - User agent rotation
    - Proxy support
    - Connection pooling
    - Request/response logging
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize network utilities.

        Args:
            config: Configuration dictionary with network parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "rate_limiting": {
                "requests_per_second": 2,
                "burst_limit": 5,
                "backoff_factor": 1.5,
                "max_delay": 60,
            },
            "retries": {
                "total": 3,
                "backoff_factor": 0.3,
                "status_forcelist": [500, 502, 503, 504, 408, 429],
            },
            "timeouts": {"connect": 10, "read": 30},
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
            ],
            "proxy": {"enabled": False, "proxies": [], "rotation": True},
        }

        if config:
            self.config.update(config)

        # Initialize session
        self.session = self._create_session()
        self.last_request_time = 0
        self.request_count = 0
        self.current_proxy_index = 0

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform GET request with rate limiting and retries.

        Args:
            url: Target URL
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        return self._make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Perform POST request with rate limiting and retries.

        Args:
            url: Target URL
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        return self._make_request("POST", url, **kwargs)

    def download_file(
        self, url: str, save_path: str, chunk_size: int = 8192
    ) -> Dict[str, Any]:
        """
        Download file with progress tracking.

        Args:
            url: File URL
            save_path: Local save path
            chunk_size: Download chunk size in bytes

        Returns:
            Download result with metadata
        """
        try:
            self._apply_rate_limiting()

            # Prepare headers
            headers = self._get_request_headers()

            response = self.session.get(
                url,
                headers=headers,
                stream=True,
                timeout=(
                    self.config["timeouts"]["connect"],
                    self.config["timeouts"]["read"],
                ),
            )
            response.raise_for_status()

            # Get file size if available
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

            return {
                "success": True,
                "url": url,
                "save_path": save_path,
                "size_bytes": downloaded_size,
                "content_type": response.headers.get("content-type"),
                "status_code": response.status_code,
            }

        except Exception as e:
            self.logger.error(f"Download failed for {url}: {e}")
            return {"success": False, "error": str(e), "url": url}

    def check_url_accessibility(self, url: str) -> Dict[str, Any]:
        """
        Check if URL is accessible.

        Args:
            url: URL to check

        Returns:
            Accessibility result
        """
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)

            return {
                "accessible": True,
                "status_code": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length"),
            }

        except requests.exceptions.RequestException as e:
            return {
                "accessible": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def batch_check_urls(self, urls: List[str]) -> Dict[str, Any]:
        """
        Check accessibility of multiple URLs.

        Args:
            urls: List of URLs to check

        Returns:
            Batch check results
        """
        results = []
        accessible_count = 0

        for url in urls:
            result = self.check_url_accessibility(url)
            result["url"] = url
            results.append(result)

            if result["accessible"]:
                accessible_count += 1

            # Apply rate limiting between checks
            self._apply_rate_limiting()

        return {
            "total_urls": len(urls),
            "accessible_urls": accessible_count,
            "inaccessible_urls": len(urls) - accessible_count,
            "success_rate": (accessible_count / len(urls)) * 100 if urls else 0,
            "results": results,
        }

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with all configured features."""
        self._apply_rate_limiting()

        # Prepare headers
        headers = kwargs.get("headers", {})
        headers.update(self._get_request_headers())
        kwargs["headers"] = headers

        # Set timeouts if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = (
                self.config["timeouts"]["connect"],
                self.config["timeouts"]["read"],
            )

        # Apply proxy if configured
        if self.config["proxy"]["enabled"]:
            kwargs["proxies"] = self._get_proxy()

        try:
            response = self.session.request(method, url, **kwargs)

            # Log successful request
            self.logger.debug(f"{method} {url} - {response.status_code}")

            # Handle rate limiting headers
            self._handle_rate_limit_headers(response)

            return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f"{method} {url} failed: {e}")
            raise

    def _create_session(self) -> requests.Session:
        """Create configured requests session."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config["retries"]["total"],
            backoff_factor=self.config["retries"]["backoff_factor"],
            status_forcelist=self.config["retries"]["status_forcelist"],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
        )

        # Mount adapters
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _apply_rate_limiting(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        min_interval = 1.0 / self.config["rate_limiting"]["requests_per_second"]

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            # Add some randomness to avoid thundering herd
            sleep_time += random.uniform(0, 0.1)
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def _get_request_headers(self) -> Dict[str, str]:
        """Get headers for request including rotated User-Agent."""
        headers = self.config["headers"].copy()

        # Rotate User-Agent
        if self.config["user_agents"]:
            user_agent = random.choice(self.config["user_agents"])
            headers["User-Agent"] = user_agent

        # Add common headers
        headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        return headers

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration with rotation."""
        if not self.config["proxy"]["enabled"] or not self.config["proxy"]["proxies"]:
            return None

        proxies = self.config["proxy"]["proxies"]

        if self.config["proxy"]["rotation"]:
            proxy = proxies[self.current_proxy_index % len(proxies)]
            self.current_proxy_index += 1
        else:
            proxy = random.choice(proxies)

        return {"http": proxy, "https": proxy}

    def _handle_rate_limit_headers(self, response: requests.Response):
        """Handle rate limiting headers from server."""
        # Check for rate limit headers
        rate_limit_headers = [
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ]

        for header in rate_limit_headers:
            if header in response.headers:
                if header == "Retry-After":
                    retry_after = int(response.headers[header])
                    if retry_after > 0:
                        self.logger.warning(
                            f"Rate limited. Waiting {retry_after} seconds"
                        )
                        time.sleep(retry_after)
                elif header == "X-RateLimit-Remaining":
                    remaining = int(response.headers[header])
                    if remaining <= 5:  # Low remaining requests
                        self.logger.warning(f"Low rate limit remaining: {remaining}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            "request_count": self.request_count,
            "current_proxy_index": self.current_proxy_index,
            "session_active": self.session is not None,
            "rate_limit_config": self.config["rate_limiting"],
        }

    def reset_session(self):
        """Reset session and counters."""
        self.session.close()
        self.session = self._create_session()
        self.request_count = 0
        self.current_proxy_index = 0
        self.last_request_time = 0

        self.logger.info("Network session reset")


def create_network_config() -> Dict[str, Any]:
    """Create default configuration for network utilities."""
    return {
        "rate_limiting": {
            "requests_per_second": 2,
            "burst_limit": 5,
            "backoff_factor": 1.5,
            "max_delay": 60,
        },
        "retries": {
            "total": 3,
            "backoff_factor": 0.3,
            "status_forcelist": [500, 502, 503, 504, 408, 429],
        },
        "timeouts": {"connect": 10, "read": 30},
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ],
        "proxy": {"enabled": False, "proxies": [], "rotation": True},
    }
