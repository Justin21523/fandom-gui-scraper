"""
Scrapy middlewares for request/response processing.

This module contains custom middlewares to handle anti-ban measures,
user agent rotation, retry logic, and response processing.
"""

import random
import time
import logging
from typing import Optional, Union
from scrapy import signals
from scrapy.http import HtmlResponse, Request
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.utils.python import global_object_name
from scrapy.utils.response import response_status_message

from scraper.utils.anti_ban import AntiBanManager, ProxyRotator

logger = logging.getLogger(__name__)


class RandomUserAgentMiddleware:
    """
    Rotate User-Agent headers to avoid detection.

    This middleware randomly selects user agents from a predefined list
    to make requests appear to come from different browsers.
    """

    def __init__(self, user_agent_list: Optional[list] = None):
        """
        Initialize the middleware.

        Args:
            user_agent_list: Custom list of user agents
        """
        self.user_agent_list = user_agent_list or [
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

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        user_agents = crawler.settings.getlist("USER_AGENT_LIST")
        return cls(user_agents)

    def process_request(self, request: Request, spider):
        """Process request and set random User-Agent."""
        ua = random.choice(self.user_agent_list)
        request.headers["User-Agent"] = ua
        logger.debug(f"Set User-Agent: {ua}")
        return None


class AntiBanMiddleware:
    """
    Comprehensive anti-ban middleware.

    This middleware implements various anti-ban strategies including
    rate limiting, request delays, and behavior mimicking.
    """

    def __init__(
        self, requests_per_minute: int = 30, enable_behavior_mimicking: bool = True
    ):
        """
        Initialize anti-ban middleware.

        Args:
            requests_per_minute: Rate limit for requests
            enable_behavior_mimicking: Whether to enable behavior mimicking
        """
        self.anti_ban_manager = AntiBanManager(
            requests_per_minute=requests_per_minute,
            enable_behavior_mimicking=enable_behavior_mimicking,
        )

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        settings = crawler.settings

        requests_per_minute = settings.getint("ANTI_BAN_REQUESTS_PER_MINUTE", 30)
        enable_behavior = settings.getbool("ANTI_BAN_BEHAVIOR_MIMICKING", True)

        middleware = cls(requests_per_minute, enable_behavior)

        # Connect spider signals
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)

        return middleware

    def spider_opened(self, spider):
        """Called when spider is opened."""
        logger.info(f"Anti-ban middleware activated for spider: {spider.name}")

    def spider_closed(self, spider):
        """Called when spider is closed."""
        stats = self.anti_ban_manager.get_stats()
        logger.info(f"Anti-ban stats for spider {spider.name}: {stats}")

    def process_request(self, request: Request, spider):
        """Process request with anti-ban measures."""
        url = request.url
        headers = dict(request.headers.to_unicode_dict())

        # Check if we should proceed with the request
        should_proceed, reason = self.anti_ban_manager.should_proceed_with_request(
            url, headers
        )
        if not should_proceed:
            logger.warning(f"Request blocked by anti-ban: {reason}")
            raise IgnoreRequest(f"Anti-ban: {reason}")

        # Apply anti-ban delays
        content_length = request.meta.get("previous_content_length")
        self.anti_ban_manager.wait_before_request(content_length)

        # Prepare headers with anti-ban measures
        modified_headers = self.anti_ban_manager.prepare_request(url, headers)

        # Update request headers
        for header_name, header_value in modified_headers.items():
            request.headers[header_name] = header_value

        return None

    def process_response(self, request: Request, response: HtmlResponse, spider):
        """Process response and update anti-ban state."""
        url = request.url
        headers = dict(request.headers.to_unicode_dict())
        response_headers = dict(response.headers.to_unicode_dict())

        # Extract response cookies
        response_cookies = {}
        if hasattr(response, "cookies"):
            for cookie in response.cookies:
                response_cookies[cookie.name] = cookie.value

        # Calculate content length
        content_length = len(response.body) if response.body else 0

        # Update anti-ban manager
        self.anti_ban_manager.process_response(
            url=url,
            headers=headers,
            response_code=response.status,
            response_headers=response_headers,
            response_cookies=response_cookies,
            content_length=content_length,
        )

        # Store content length for next request
        response.meta["content_length"] = content_length

        return response

    def process_exception(self, request: Request, exception: Exception, spider):
        """Process exceptions and update anti-ban state."""
        url = request.url
        headers = dict(request.headers.to_unicode_dict())

        # Treat exceptions as failed requests
        self.anti_ban_manager.process_response(
            url=url,
            headers=headers,
            response_code=500,  # Treat as server error
        )

        return None


class ProxyRotationMiddleware:
    """
    Rotate proxy servers to avoid IP-based bans.

    This middleware manages a pool of proxy servers and rotates
    through them for different requests.
    """

    def __init__(self, proxy_list: Optional[list] = None):
        """
        Initialize proxy rotation middleware.

        Args:
            proxy_list: List of proxy URLs
        """
        if not proxy_list:
            raise NotConfigured("No proxy list provided")

        self.proxy_rotator = ProxyRotator(proxy_list)

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        proxy_list = crawler.settings.getlist("PROXY_LIST")
        if not proxy_list:
            raise NotConfigured("PROXY_LIST setting is required")

        return cls(proxy_list)

    def process_request(self, request: Request, spider):
        """Process request and set proxy."""
        proxy = self.proxy_rotator.get_next_proxy()
        if proxy:
            request.meta["proxy"] = proxy
            logger.debug(f"Using proxy: {proxy}")

        return None

    def process_response(self, request: Request, response: HtmlResponse, spider):
        """Process response and update proxy stats."""
        proxy = request.meta.get("proxy")
        if proxy:
            success = 200 <= response.status < 400
            self.proxy_rotator.record_proxy_result(proxy, success)

        return response

    def process_exception(self, request: Request, exception: Exception, spider):
        """Process exceptions and update proxy stats."""
        proxy = request.meta.get("proxy")
        if proxy:
            self.proxy_rotator.record_proxy_result(proxy, False)

        return None


class SmartRetryMiddleware(RetryMiddleware):
    """
    Enhanced retry middleware with smart backoff strategies.

    This middleware extends the default retry middleware with
    exponential backoff and ban detection.
    """

    def __init__(self, settings):
        """Initialize smart retry middleware."""
        super().__init__(settings)
        self.initial_delay = settings.getfloat("RETRY_INITIAL_DELAY", 1.0)
        self.max_delay = settings.getfloat("RETRY_MAX_DELAY", 60.0)
        self.backoff_multiplier = settings.getfloat("RETRY_BACKOFF_MULTIPLIER", 2.0)

        # Ban detection settings
        self.ban_codes = set(settings.getlist("RETRY_BAN_CODES", [403, 429, 503, 999]))
        self.ban_delay = settings.getfloat("RETRY_BAN_DELAY", 300.0)  # 5 minutes

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        return cls(crawler.settings)

    def process_response(self, request: Request, response: HtmlResponse, spider):
        """Process response and handle retries."""
        if request.meta.get("dont_retry", False):
            return response

        # Check for ban responses
        if response.status in self.ban_codes:
            logger.warning(
                f"Ban detected (status {response.status}), delaying {self.ban_delay}s"
            )
            time.sleep(self.ban_delay)

        # Use parent retry logic
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response

    def process_exception(self, request: Request, exception: Exception, spider):
        """Process exceptions and handle retries."""
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get(
            "dont_retry", False
        ):
            return self._retry(request, exception, spider)

    def _retry(self, request: Request, reason: Union[str, Exception], spider):
        """Retry request with exponential backoff."""
        retries = request.meta.get("retry_times", 0) + 1

        if retries <= self.max_retry_times:
            # Calculate delay with exponential backoff
            delay = min(
                self.initial_delay * (self.backoff_multiplier ** (retries - 1)),
                self.max_delay,
            )

            logger.debug(
                f"Retrying {request.url} (attempt {retries}/{self.max_retry_times}) after {delay}s delay: {reason}"
            )

            # Apply delay
            time.sleep(delay)

            # Create retry request
            retry_req = request.copy()
            retry_req.meta["retry_times"] = retries
            retry_req.dont_filter = True
            retry_req.priority = request.priority + self.priority_adjust

            return retry_req
        else:
            logger.error(
                f"Gave up retrying {request.url} (failed {retries} times): {reason}"
            )


class ResponseValidationMiddleware:
    """
    Validate responses to detect blocked or invalid content.

    This middleware checks responses for signs of blocking,
    captchas, or other invalid content.
    """

    def __init__(self):
        """Initialize response validation middleware."""
        # Patterns that indicate blocked/invalid responses
        self.block_patterns = [
            b"access denied",
            b"blocked",
            b"captcha",
            b"bot detection",
            b"rate limit",
            b"too many requests",
            b"cloudflare",
            b"security check",
            b"forbidden",
        ]

        # Minimum content length for valid pages
        self.min_content_length = 100

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        return cls()

    def process_response(self, request: Request, response: HtmlResponse, spider):
        """Validate response content."""
        # Check response status
        if response.status >= 400:
            logger.warning(f"HTTP error {response.status} for {request.url}")

        # Check content length
        if len(response.body) < self.min_content_length:
            logger.warning(
                f"Response too short ({len(response.body)} bytes) for {request.url}"
            )

        # Check for block patterns
        body_lower = response.body.lower()
        for pattern in self.block_patterns:
            if pattern in body_lower:
                logger.warning(
                    f"Block pattern '{pattern.decode()}' detected in {request.url}"
                )
                # Could raise IgnoreRequest here if desired
                break

        # Check for expected content patterns (Fandom-specific)
        if "fandom.com" in request.url:
            if b"fandom" not in body_lower and b"wikia" not in body_lower:
                logger.warning(f"Expected Fandom content not found in {request.url}")

        return response


class HeaderEnhancementMiddleware:
    """
    Enhance requests with additional realistic headers.

    This middleware adds headers that make requests appear
    more like real browser requests.
    """

    def __init__(self):
        """Initialize header enhancement middleware."""
        self.accept_languages = [
            "en-US,en;q=0.9",
            "en-US,en;q=0.8,ja;q=0.7",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.5",
        ]

        self.accept_encodings = [
            "gzip, deflate, br",
            "gzip, deflate",
            "gzip",
        ]

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        return cls()

    def process_request(self, request: Request, spider):
        """Enhance request headers."""
        # Add Accept-Language if not present
        if "Accept-Language" not in request.headers:
            request.headers["Accept-Language"] = random.choice(self.accept_languages)

        # Add Accept-Encoding if not present
        if "Accept-Encoding" not in request.headers:
            request.headers["Accept-Encoding"] = random.choice(self.accept_encodings)

        # Add DNT (Do Not Track) header
        if "DNT" not in request.headers:
            request.headers["DNT"] = "1"

        # Add Connection header
        if "Connection" not in request.headers:
            request.headers["Connection"] = "keep-alive"

        # Add Cache-Control occasionally
        if random.random() < 0.2:  # 20% chance
            cache_controls = ["no-cache", "max-age=0", "no-store"]
            request.headers["Cache-Control"] = random.choice(cache_controls)

        # Add Sec-Fetch headers for modern browsers
        if random.random() < 0.8:  # 80% chance
            request.headers["Sec-Fetch-Dest"] = "document"
            request.headers["Sec-Fetch-Mode"] = "navigate"
            request.headers["Sec-Fetch-Site"] = "none"
            request.headers["Sec-Fetch-User"] = "?1"

        return None


class StatisticsMiddleware:
    """
    Collect statistics about requests and responses.

    This middleware tracks various metrics for monitoring
    and debugging purposes.
    """

    def __init__(self):
        """Initialize statistics middleware."""
        self.stats = {
            "requests_total": 0,
            "responses_total": 0,
            "responses_2xx": 0,
            "responses_3xx": 0,
            "responses_4xx": 0,
            "responses_5xx": 0,
            "exceptions_total": 0,
            "bytes_downloaded": 0,
            "avg_response_time": 0,
            "response_times": [],
        }

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def process_request(self, request: Request, spider):
        """Track request statistics."""
        request.meta["start_time"] = time.time()
        self.stats["requests_total"] += 1
        return None

    def process_response(self, request: Request, response: HtmlResponse, spider):
        """Track response statistics."""
        self.stats["responses_total"] += 1

        # Track by status code range
        status_range = f"{response.status // 100}xx"
        self.stats[f"responses_{status_range}"] += 1

        # Track bytes downloaded
        self.stats["bytes_downloaded"] += len(response.body)

        # Track response time
        start_time = request.meta.get("start_time")
        if start_time:
            response_time = time.time() - start_time
            self.stats["response_times"].append(response_time)

            # Update average
            if self.stats["response_times"]:
                self.stats["avg_response_time"] = sum(
                    self.stats["response_times"]
                ) / len(self.stats["response_times"])

        return response

    def process_exception(self, request: Request, exception: Exception, spider):
        """Track exception statistics."""
        self.stats["exceptions_total"] += 1
        return None

    def spider_closed(self, spider):
        """Log final statistics when spider closes."""
        logger.info("=== SCRAPING STATISTICS ===")
        for key, value in self.stats.items():
            if key != "response_times":  # Don't log the full list
                logger.info(f"{key}: {value}")

        # Calculate additional metrics
        if self.stats["responses_total"] > 0:
            success_rate = (
                self.stats["responses_2xx"] / self.stats["responses_total"] * 100
            )
            logger.info(f"success_rate: {success_rate:.2f}%")

        if self.stats["response_times"]:
            min_time = min(self.stats["response_times"])
            max_time = max(self.stats["response_times"])
            logger.info(f"response_time_min: {min_time:.3f}s")
            logger.info(f"response_time_max: {max_time:.3f}s")

        logger.info("=== END STATISTICS ===")
