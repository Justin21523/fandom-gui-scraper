# scraper/utils/request_builder.py
"""
HTTP request builder utility for web scraping.

This module provides utilities to build and customize HTTP requests
with proper headers, user agents, and anti-detection measures.
"""

import random
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse
import scrapy
from scrapy import Request


class RequestBuilder:
    """
    Build customized HTTP requests with anti-detection features.

    This class helps create requests with rotating user agents,
    proper headers, and delays to avoid being blocked.
    """

    # Common user agents for different browsers
    USER_AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    # Common accept headers
    ACCEPT_HEADERS = {
        "html": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "json": "application/json, text/plain, */*",
        "image": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "css": "text/css,*/*;q=0.1",
        "js": "application/javascript, application/ecmascript, text/javascript, text/ecmascript",
    }

    def __init__(
        self,
        base_delay: float = 1.0,
        delay_variance: float = 0.5,
        custom_user_agents: Optional[List[str]] = None,
    ):
        """
        Initialize the RequestBuilder.

        Args:
            base_delay: Base delay between requests in seconds
            delay_variance: Random variance added to delay (±variance)
            custom_user_agents: Custom list of user agents to use
        """
        self.base_delay = base_delay
        self.delay_variance = delay_variance
        self.user_agents = custom_user_agents or self.USER_AGENTS
        self.last_request_time = 0
        self.request_count = 0

    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self.user_agents)

    def get_common_headers(
        self,
        content_type: str = "html",
        referer: Optional[str] = None,
        origin: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get common HTTP headers for requests.

        Args:
            content_type: Type of content being requested (html, json, image, etc.)
            referer: Referer URL to include in headers
            origin: Origin URL for CORS requests

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Accept": self.ACCEPT_HEADERS.get(
                content_type, self.ACCEPT_HEADERS["html"]
            ),
            "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        if referer:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "same-origin"

        if origin:
            headers["Origin"] = origin

        return headers

    def calculate_delay(self) -> float:
        """
        Calculate delay for next request with randomization.

        Returns:
            Delay in seconds
        """
        variance = random.uniform(-self.delay_variance, self.delay_variance)
        return max(0.1, self.base_delay + variance)

    def should_delay(self) -> bool:
        """
        Check if we should delay before making the next request.

        Returns:
            True if delay is needed
        """
        if self.last_request_time == 0:
            return False

        time_since_last = time.time() - self.last_request_time
        required_delay = self.calculate_delay()

        return time_since_last < required_delay

    def apply_delay(self):
        """Apply delay if needed before making request."""
        if self.should_delay():
            time_since_last = time.time() - self.last_request_time
            required_delay = self.calculate_delay()
            sleep_time = required_delay - time_since_last

            if sleep_time > 0:
                time.sleep(sleep_time)

    def build_request(
        self,
        url: str,
        callback=None,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        meta: Optional[Dict] = None,
        priority: int = 0,
        dont_filter: bool = False,
        content_type: str = "html",
        referer: Optional[str] = None,
        **kwargs,
    ) -> Request:
        """
        Build a Scrapy Request with proper headers and settings.

        Args:
            url: URL to request
            callback: Callback function for response
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers to include
            cookies: Cookies to send with request
            meta: Meta data for request
            priority: Request priority
            dont_filter: Skip duplicate filtering
            content_type: Type of content being requested
            referer: Referer URL
            **kwargs: Additional arguments for Request

        Returns:
            Configured Scrapy Request object
        """
        # Build headers
        request_headers = self.get_common_headers(content_type, referer)
        request_headers["User-Agent"] = self.get_random_user_agent()

        # Add custom headers
        if headers:
            request_headers.update(headers)

        # Build meta
        request_meta = {
            "download_delay": self.calculate_delay(),
            "request_count": self.request_count,
        }
        if meta:
            request_meta.update(meta)

        # Create request
        request = Request(
            url=url,
            callback=callback,
            method=method,
            headers=request_headers,
            cookies=cookies,
            meta=request_meta,
            priority=priority,
            dont_filter=dont_filter,
            **kwargs,
        )

        # Update tracking
        self.request_count += 1
        self.last_request_time = time.time()

        return request

    def build_ajax_request(
        self,
        url: str,
        callback=None,
        referer: Optional[str] = None,
        origin: Optional[str] = None,
        **kwargs,
    ) -> Request:
        """
        Build an AJAX request with appropriate headers.

        Args:
            url: URL to request
            callback: Callback function
            referer: Referer URL
            origin: Origin URL
            **kwargs: Additional arguments

        Returns:
            Configured AJAX Request
        """
        ajax_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        return self.build_request(
            url=url,
            callback=callback,
            headers=ajax_headers,
            content_type="json",
            referer=referer,
            **kwargs,
        )

    def build_image_request(
        self, url: str, callback=None, referer: Optional[str] = None, **kwargs
    ) -> Request:
        """
        Build a request for downloading images.

        Args:
            url: Image URL
            callback: Callback function
            referer: Referer URL
            **kwargs: Additional arguments

        Returns:
            Configured image Request
        """
        return self.build_request(
            url=url, callback=callback, content_type="image", referer=referer, **kwargs
        )

    def build_form_request(
        self,
        url: str,
        formdata: Dict[str, str],
        callback=None,
        referer: Optional[str] = None,
        **kwargs,
    ) -> scrapy.FormRequest:
        """
        Build a form submission request.

        Args:
            url: Form action URL
            formdata: Form data to submit
            callback: Callback function
            referer: Referer URL
            **kwargs: Additional arguments

        Returns:
            Configured FormRequest
        """
        headers = self.get_common_headers("html", referer)
        headers["User-Agent"] = self.get_random_user_agent()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        meta = {
            "download_delay": self.calculate_delay(),
            "request_count": self.request_count,
        }
        if "meta" in kwargs:
            meta.update(kwargs.pop("meta"))

        request = scrapy.FormRequest(
            url=url,
            formdata=formdata,  # type: ignore
            callback=callback,
            headers=headers,
            meta=meta,
            **kwargs,
        )

        self.request_count += 1
        self.last_request_time = time.time()

        return request


class FandomRequestBuilder(RequestBuilder):
    """
    Specialized request builder for Fandom wikis.

    This class extends RequestBuilder with Fandom-specific
    configurations and optimizations.
    """

    def __init__(self, wiki_domain: str, **kwargs):
        """
        Initialize Fandom request builder.

        Args:
            wiki_domain: Domain of the Fandom wiki (e.g., 'onepiece.fandom.com')
            **kwargs: Additional arguments for RequestBuilder
        """
        super().__init__(**kwargs)
        self.wiki_domain = wiki_domain
        self.wiki_origin = f"https://{wiki_domain}"

    def get_api_url(self, endpoint: str = "api.php") -> str:
        """
        Get Fandom API URL.

        Args:
            endpoint: API endpoint (default: api.php)

        Returns:
            Full API URL
        """
        return f"{self.wiki_origin}/{endpoint}"

    def build_api_request(
        self, params: Dict[str, str], callback=None, **kwargs
    ) -> Request:
        """
        Build a Fandom API request.

        Args:
            params: API parameters
            callback: Callback function
            **kwargs: Additional arguments

        Returns:
            Configured API Request
        """
        # Common API parameters
        api_params = {
            "format": "json",
            "formatversion": "2",
        }
        api_params.update(params)

        # Build URL with parameters
        api_url = self.get_api_url()
        param_string = "&".join([f"{k}={v}" for k, v in api_params.items()])
        full_url = f"{api_url}?{param_string}"

        return self.build_ajax_request(
            url=full_url,
            callback=callback,
            referer=self.wiki_origin,
            origin=self.wiki_origin,
            **kwargs,
        )

    def build_page_request(self, page_title: str, callback=None, **kwargs) -> Request:
        """
        Build a request for a Fandom wiki page.

        Args:
            page_title: Title of the wiki page
            callback: Callback function
            **kwargs: Additional arguments

        Returns:
            Configured page Request
        """
        # Build page URL
        page_url = f"{self.wiki_origin}/wiki/{page_title.replace(' ', '_')}"

        return self.build_request(
            url=page_url, callback=callback, referer=self.wiki_origin, **kwargs
        )

    def build_search_request(
        self, query: str, callback=None, limit: int = 50, **kwargs
    ) -> Request:
        """
        Build a search request for Fandom wiki.

        Args:
            query: Search query
            callback: Callback function
            limit: Maximum number of results
            **kwargs: Additional arguments

        Returns:
            Configured search Request
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(limit),
            "srprop": "titlesnippet|snippet|size|timestamp",
        }

        return self.build_api_request(params=params, callback=callback, **kwargs)

    def build_category_request(
        self, category: str, callback=None, limit: int = 500, **kwargs
    ) -> Request:
        """
        Build a request to get pages in a category.

        Args:
            category: Category name
            callback: Callback function
            limit: Maximum number of pages
            **kwargs: Additional arguments

        Returns:
            Configured category Request
        """
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": str(limit),
            "cmprop": "ids|title|type|timestamp",
        }

        return self.build_api_request(params=params, callback=callback, **kwargs)
