# scraper/utils/anti_ban
"""
Anti-ban utilities and strategies for web scraping.

This module provides utilities to avoid being detected and banned
while scraping websites, including rate limiting, IP rotation,
and behavior mimicking.
"""

import random
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiting utility to control request frequency.

    This class helps manage request timing to avoid overwhelming
    target servers and reduce the risk of being banned.
    """

    def __init__(
        self,
        requests_per_minute: int = 30,
        burst_delay: float = 2.0,
        adaptive: bool = True,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst_delay: Delay after rapid requests (seconds)
            adaptive: Whether to adapt based on response codes
        """
        self.requests_per_minute = requests_per_minute
        self.burst_delay = burst_delay
        self.adaptive = adaptive

        self.request_times = []
        self.consecutive_errors = 0
        self.last_error_time = 0
        self.current_delay_multiplier = 1.0

        # Calculate base delay
        self.base_delay = 60.0 / requests_per_minute

    def should_delay(self) -> Tuple[bool, float]:
        """
        Check if a delay is needed before the next request.

        Returns:
            Tuple of (should_delay, delay_seconds)
        """
        current_time = time.time()

        # Clean old request times (older than 1 minute)
        self.request_times = [t for t in self.request_times if current_time - t < 60]

        # Check if we've exceeded rate limit
        if len(self.request_times) >= self.requests_per_minute:
            oldest_time = min(self.request_times)
            delay_needed = 60 - (current_time - oldest_time)
            return True, max(0, delay_needed)

        # Check for burst protection
        if self.request_times:
            time_since_last = current_time - max(self.request_times)
            min_delay = self.base_delay * self.current_delay_multiplier

            if time_since_last < min_delay:
                return True, min_delay - time_since_last

        # Check for error-based backoff
        if self.consecutive_errors > 0:
            error_delay = self.calculate_error_delay()
            if current_time - self.last_error_time < error_delay:
                return True, error_delay - (current_time - self.last_error_time)

        return False, 0.0

    def wait_if_needed(self):
        """Wait if rate limiting is required."""
        should_delay, delay_time = self.should_delay()

        if should_delay and delay_time > 0:
            logger.info(f"Rate limiting: waiting {delay_time:.2f} seconds")
            time.sleep(delay_time)

    def record_request(self, success: bool = True, response_code: Optional[int] = None):
        """
        Record a request for rate limiting tracking.

        Args:
            success: Whether the request was successful
            response_code: HTTP response code
        """
        current_time = time.time()
        self.request_times.append(current_time)

        if not success or (response_code and response_code >= 400):
            self.consecutive_errors += 1
            self.last_error_time = current_time

            # Adaptive delay adjustment
            if self.adaptive:
                if response_code == 429:  # Too Many Requests
                    self.current_delay_multiplier *= 2.0
                elif response_code in [503, 504]:  # Server errors
                    self.current_delay_multiplier *= 1.5

                # Cap the multiplier
                self.current_delay_multiplier = min(self.current_delay_multiplier, 10.0)
        else:
            # Successful request - reset error tracking
            self.consecutive_errors = 0
            if self.adaptive and self.current_delay_multiplier > 1.0:
                self.current_delay_multiplier *= 0.9  # Gradually reduce delay
                self.current_delay_multiplier = max(self.current_delay_multiplier, 1.0)

    def calculate_error_delay(self) -> float:
        """
        Calculate delay based on consecutive errors (exponential backoff).

        Returns:
            Delay in seconds
        """
        if self.consecutive_errors == 0:
            return 0.0

        # Exponential backoff: 2^(errors-1) seconds, max 5 minutes
        delay = min(2 ** (self.consecutive_errors - 1), 300)
        return delay


class SessionManager:
    """
    Manage session state and cookies to maintain consistency.

    This class helps maintain session consistency across requests
    to avoid triggering anti-bot measures.
    """

    def __init__(self):
        """Initialize session manager."""
        self.session_cookies = {}
        self.session_headers = {}
        self.last_referer = None
        self.user_agent_rotation_count = 0

    def update_cookies(self, response_cookies: Dict[str, str]):
        """
        Update session cookies from response.

        Args:
            response_cookies: Cookies from response
        """
        self.session_cookies.update(response_cookies)

        # Remove expired or unwanted cookies
        cookies_to_remove = []
        for name, value in self.session_cookies.items():
            if not value or value.lower() in ["deleted", "expired"]:
                cookies_to_remove.append(name)

        for name in cookies_to_remove:
            del self.session_cookies[name]

    def get_session_cookies(self) -> Dict[str, str]:
        """
        Get current session cookies.

        Returns:
            Dictionary of session cookies
        """
        return self.session_cookies.copy()

    def update_referer(self, url: str):
        """
        Update the referer for the next request.

        Args:
            url: Current page URL to use as referer
        """
        self.last_referer = url

    def get_referer(self) -> Optional[str]:
        """
        Get the current referer URL.

        Returns:
            Referer URL or None
        """
        return self.last_referer


class BehaviorMimicker:
    """
    Mimic human browsing behavior to avoid detection.

    This class implements various strategies to make requests
    appear more human-like.
    """

    def __init__(
        self,
        reading_time_min: float = 2.0,
        reading_time_max: float = 10.0,
        scroll_simulation: bool = True,
    ):
        """
        Initialize behavior mimicker.

        Args:
            reading_time_min: Minimum simulated reading time
            reading_time_max: Maximum simulated reading time
            scroll_simulation: Whether to simulate scrolling delays
        """
        self.reading_time_min = reading_time_min
        self.reading_time_max = reading_time_max
        self.scroll_simulation = scroll_simulation
        self.last_page_visit_time = 0
        self.pages_visited = 0

    def simulate_reading_time(self, content_length: Optional[int] = None) -> float:
        """
        Calculate simulated reading time based on content.

        Args:
            content_length: Length of page content in characters

        Returns:
            Simulated reading time in seconds
        """
        if content_length:
            # Rough estimate: 200 words per minute, 5 chars per word
            reading_time = (content_length / 5) / 200 * 60
            # Add some randomness
            reading_time *= random.uniform(0.8, 1.2)
            # Clamp to reasonable bounds
            reading_time = max(
                self.reading_time_min, min(reading_time, self.reading_time_max)
            )
        else:
            reading_time = random.uniform(self.reading_time_min, self.reading_time_max)

        return reading_time

    def simulate_human_delay(self, content_length: Optional[int] = None):
        """
        Simulate human-like delay before next request.

        Args:
            content_length: Length of page content
        """
        delay = self.simulate_reading_time(content_length)

        # Add scroll simulation delays
        if self.scroll_simulation:
            scroll_delays = random.randint(2, 5)
            for _ in range(scroll_delays):
                scroll_delay = random.uniform(0.5, 2.0)
                time.sleep(scroll_delay)
                delay -= scroll_delay
                if delay <= 0:
                    break

        if delay > 0:
            time.sleep(delay)

        self.last_page_visit_time = time.time()
        self.pages_visited += 1

    def should_take_break(self) -> bool:
        """
        Determine if we should take a longer break to mimic human behavior.

        Returns:
            True if a break is recommended
        """
        # Take breaks after certain number of pages
        if self.pages_visited > 0 and self.pages_visited % random.randint(15, 25) == 0:
            return True

        # Take breaks after certain time periods
        if self.last_page_visit_time > 0:
            time_since_start = time.time() - self.last_page_visit_time
            if time_since_start > random.randint(300, 600):  # 5-10 minutes
                return True

        return False

    def take_break(self):
        """Take a longer break to mimic human behavior."""
        break_time = random.uniform(30, 120)  # 30 seconds to 2 minutes
        logger.info(f"Taking human-like break for {break_time:.1f} seconds")
        time.sleep(break_time)


class RequestFingerprinter:
    """
    Manage request fingerprinting to avoid detection.

    This class helps vary request characteristics to avoid
    being fingerprinted as a bot.
    """

    def __init__(self):
        """Initialize request fingerprinter."""
        self.request_history = []
        self.max_history = 100

    def generate_request_id(self, url: str, headers: Dict[str, str]) -> str:
        """
        Generate a unique ID for a request.

        Args:
            url: Request URL
            headers: Request headers

        Returns:
            Unique request ID
        """
        # Create a hash of URL and key headers
        key_headers = ["User-Agent", "Accept", "Accept-Language"]
        header_string = "".join([headers.get(h, "") for h in key_headers])

        fingerprint = f"{url}:{header_string}"
        return hashlib.md5(fingerprint.encode()).hexdigest()

    def is_duplicate_request(self, url: str, headers: Dict[str, str]) -> bool:
        """
        Check if this request pattern has been used recently.

        Args:
            url: Request URL
            headers: Request headers

        Returns:
            True if this is a duplicate pattern
        """
        request_id = self.generate_request_id(url, headers)

        # Check recent history
        recent_requests = self.request_history[-10:]  # Last 10 requests
        return request_id in recent_requests

    def record_request(self, url: str, headers: Dict[str, str]):
        """
        Record a request in the fingerprint history.

        Args:
            url: Request URL
            headers: Request headers
        """
        request_id = self.generate_request_id(url, headers)
        self.request_history.append(request_id)

        # Maintain history size
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history :]


class AntiBanManager:
    """
    Comprehensive anti-ban management system.

    This class coordinates all anti-ban strategies including
    rate limiting, session management, and behavior mimicking.
    """

    def __init__(
        self,
        requests_per_minute: int = 30,
        enable_behavior_mimicking: bool = True,
        enable_session_management: bool = True,
    ):
        """
        Initialize anti-ban manager.

        Args:
            requests_per_minute: Rate limit for requests
            enable_behavior_mimicking: Whether to use behavior mimicking
            enable_session_management: Whether to manage sessions
        """
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.session_manager = SessionManager() if enable_session_management else None
        self.behavior_mimicker = (
            BehaviorMimicker() if enable_behavior_mimicking else None
        )
        self.fingerprinter = RequestFingerprinter()

        self.total_requests = 0
        self.failed_requests = 0
        self.ban_detected = False
        self.last_ban_detection_time = 0

    def prepare_request(self, url: str, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Prepare request headers with anti-ban measures.

        Args:
            url: Request URL
            headers: Original headers

        Returns:
            Modified headers with anti-ban measures
        """
        modified_headers = headers.copy()

        # Add session cookies if available
        if self.session_manager:
            session_cookies = self.session_manager.get_session_cookies()
            if session_cookies:
                cookie_string = "; ".join(
                    [f"{k}={v}" for k, v in session_cookies.items()]
                )
                modified_headers["Cookie"] = cookie_string

            # Add referer if available
            referer = self.session_manager.get_referer()
            if referer:
                modified_headers["Referer"] = referer

        # Add realistic headers
        if "Accept-Language" not in modified_headers:
            modified_headers["Accept-Language"] = "en-US,en;q=0.9"

        if "Accept-Encoding" not in modified_headers:
            modified_headers["Accept-Encoding"] = "gzip, deflate, br"

        if "DNT" not in modified_headers:
            modified_headers["DNT"] = "1"

        if "Connection" not in modified_headers:
            modified_headers["Connection"] = "keep-alive"

        # Vary some headers slightly to avoid fingerprinting
        if random.random() < 0.3:  # 30% chance
            modified_headers["Cache-Control"] = random.choice(
                ["no-cache", "max-age=0", "no-store", "must-revalidate"]
            )

        return modified_headers

    def should_proceed_with_request(
        self, url: str, headers: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if we should proceed with the request.

        Args:
            url: Request URL
            headers: Request headers

        Returns:
            Tuple of (should_proceed, reason_if_not)
        """
        # Check if we're currently banned
        if self.ban_detected:
            time_since_ban = time.time() - self.last_ban_detection_time
            if time_since_ban < 300:  # Wait 5 minutes after ban detection
                return False, "Waiting after ban detection"
            else:
                self.ban_detected = False  # Reset ban status

        # Check rate limiting
        should_delay, delay_time = self.rate_limiter.should_delay()
        if should_delay and delay_time > 60:  # If delay is more than 1 minute
            return False, f"Rate limit exceeded, need to wait {delay_time:.1f} seconds"

        # Check for duplicate request patterns
        if self.fingerprinter.is_duplicate_request(url, headers):
            return False, "Duplicate request pattern detected"

        return True, None

    def wait_before_request(self, content_length: Optional[int] = None):
        """
        Execute all necessary delays before making a request.

        Args:
            content_length: Length of previous page content
        """
        # Rate limiting delay
        self.rate_limiter.wait_if_needed()

        # Human behavior simulation
        if self.behavior_mimicker:
            if self.behavior_mimicker.should_take_break():
                self.behavior_mimicker.take_break()
            elif content_length:
                self.behavior_mimicker.simulate_human_delay(content_length)

    def process_response(
        self,
        url: str,
        headers: Dict[str, str],
        response_code: int,
        response_headers: Optional[Dict[str, str]] = None,
        response_cookies: Optional[Dict[str, str]] = None,
        content_length: Optional[int] = None,
    ):
        """
        Process response and update anti-ban state.

        Args:
            url: Request URL
            headers: Request headers
            response_code: HTTP response code
            response_headers: Response headers
            response_cookies: Response cookies
            content_length: Response content length
        """
        self.total_requests += 1

        # Record request for rate limiting
        success = 200 <= response_code < 400
        self.rate_limiter.record_request(success, response_code)

        # Record request fingerprint
        self.fingerprinter.record_request(url, headers)

        # Update session state
        if self.session_manager:
            if response_cookies:
                self.session_manager.update_cookies(response_cookies)
            self.session_manager.update_referer(url)

        # Check for ban indicators
        if self.is_ban_response(response_code, response_headers):
            self.ban_detected = True
            self.last_ban_detection_time = time.time()
            logger.warning(f"Ban detected! Response code: {response_code}")

        # Track failures
        if not success:
            self.failed_requests += 1

    def is_ban_response(
        self, response_code: int, response_headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Check if response indicates we've been banned.

        Args:
            response_code: HTTP response code
            response_headers: Response headers

        Returns:
            True if ban is detected
        """
        # Common ban response codes
        ban_codes = [403, 429, 503, 999]
        if response_code in ban_codes:
            return True

        # Check response headers for ban indicators
        if response_headers:
            for header_name, header_value in response_headers.items():
                header_name_lower = header_name.lower()
                header_value_lower = header_value.lower()

                # Common ban indicators in headers
                ban_indicators = [
                    "rate limit",
                    "too many requests",
                    "blocked",
                    "banned",
                    "access denied",
                    "forbidden",
                    "captcha",
                    "cloudflare",
                ]

                for indicator in ban_indicators:
                    if indicator in header_value_lower:
                        return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about requests and anti-ban measures.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.total_requests - self.failed_requests)
            / max(1, self.total_requests),
            "ban_detected": self.ban_detected,
            "consecutive_errors": self.rate_limiter.consecutive_errors,
            "current_delay_multiplier": self.rate_limiter.current_delay_multiplier,
        }

        if self.behavior_mimicker:
            stats["pages_visited"] = self.behavior_mimicker.pages_visited

        return stats

    def reset_stats(self):
        """Reset all statistics and state."""
        self.total_requests = 0
        self.failed_requests = 0
        self.ban_detected = False
        self.last_ban_detection_time = 0
        self.rate_limiter.consecutive_errors = 0
        self.rate_limiter.current_delay_multiplier = 1.0
        self.rate_limiter.request_times = []

        if self.behavior_mimicker:
            self.behavior_mimicker.pages_visited = 0
            self.behavior_mimicker.last_page_visit_time = 0


class ProxyRotator:
    """
    Rotate through proxy servers to avoid IP-based bans.

    This class manages a pool of proxy servers and rotates
    through them to distribute requests.
    """

    def __init__(self, proxy_list: Optional[List[str]] = None):
        """
        Initialize proxy rotator.

        Args:
            proxy_list: List of proxy URLs (e.g., ['http://proxy1:8080', ...])
        """
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
        self.proxy_stats = {}
        self.failed_proxies = set()

    def add_proxy(self, proxy_url: str):
        """
        Add a proxy to the rotation list.

        Args:
            proxy_url: Proxy URL
        """
        if proxy_url not in self.proxy_list:
            self.proxy_list.append(proxy_url)
            self.proxy_stats[proxy_url] = {"requests": 0, "failures": 0}

    def get_next_proxy(self) -> Optional[str]:
        """
        Get the next proxy in rotation.

        Returns:
            Proxy URL or None if no proxies available
        """
        if not self.proxy_list:
            return None

        # Skip failed proxies
        attempts = 0
        while attempts < len(self.proxy_list):
            proxy = self.proxy_list[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(
                self.proxy_list
            )

            if proxy not in self.failed_proxies:
                return proxy

            attempts += 1

        # If all proxies failed, reset and try again
        if attempts >= len(self.proxy_list):
            self.failed_proxies.clear()
            return self.proxy_list[0] if self.proxy_list else None

        return None

    def record_proxy_result(self, proxy_url: str, success: bool):
        """
        Record the result of using a proxy.

        Args:
            proxy_url: Proxy URL
            success: Whether the request was successful
        """
        if proxy_url in self.proxy_stats:
            self.proxy_stats[proxy_url]["requests"] += 1
            if not success:
                self.proxy_stats[proxy_url]["failures"] += 1

                # Mark proxy as failed if failure rate is too high
                stats = self.proxy_stats[proxy_url]
                failure_rate = stats["failures"] / stats["requests"]
                if failure_rate > 0.5 and stats["requests"] > 5:
                    self.failed_proxies.add(proxy_url)
                    logger.warning(
                        f"Proxy {proxy_url} marked as failed (failure rate: {failure_rate:.2f})"
                    )

    def get_proxy_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all proxies.

        Returns:
            Dictionary with proxy statistics
        """
        return self.proxy_stats.copy()
