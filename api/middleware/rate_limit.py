# api/middleware/rate_limit.py
"""
Rate limiting middleware for the API.

This module provides a sliding window rate limiter to prevent API abuse.
"""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, List, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using a sliding window algorithm.

    Limits the number of requests per client IP within a time window.
    """

    def __init__(
        self,
        app,
        requests_per_hour: int = 1000,
        requests_per_minute: int = 60,
        exclude_paths: List[str] = None,
    ):
        """
        Initialize the rate limiter.

        Args:
            app: The ASGI application
            requests_per_hour: Maximum requests allowed per hour per IP
            requests_per_minute: Maximum requests allowed per minute per IP
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.requests_per_hour = requests_per_hour
        self.requests_per_minute = requests_per_minute
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]

        # Store request timestamps per client IP
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check for X-Forwarded-For header (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_old_requests(self, client_ip: str, now: float):
        """Remove request timestamps older than 1 hour."""
        hour_ago = now - 3600
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > hour_ago
        ]

    def _check_rate_limit(self, client_ip: str) -> tuple[bool, Dict[str, int]]:
        """
        Check if client has exceeded rate limits.

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        self._cleanup_old_requests(client_ip, now)

        timestamps = self._requests[client_ip]
        minute_ago = now - 60

        # Count requests in last hour and minute
        requests_last_hour = len(timestamps)
        requests_last_minute = len([ts for ts in timestamps if ts > minute_ago])

        # Build rate limit info
        info = {
            "limit_per_hour": self.requests_per_hour,
            "remaining_per_hour": max(0, self.requests_per_hour - requests_last_hour),
            "limit_per_minute": self.requests_per_minute,
            "remaining_per_minute": max(0, self.requests_per_minute - requests_last_minute),
        }

        # Check limits
        if requests_last_minute >= self.requests_per_minute:
            return False, info
        if requests_last_hour >= self.requests_per_hour:
            return False, info

        return True, info

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the rate limiter."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        if os.getenv("FANDOM_DEMO_MODE", "false").lower() == "true" and request.url.path.startswith(("/api/v1/scraper", "/api/v1/characters", "/frontend")):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        is_allowed, rate_info = self._check_rate_limit(client_ip)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded. Please slow down.",
                    "retry_after_seconds": 60,
                },
                headers={
                    "X-RateLimit-Limit-Hour": str(rate_info["limit_per_hour"]),
                    "X-RateLimit-Remaining-Hour": str(rate_info["remaining_per_hour"]),
                    "X-RateLimit-Limit-Minute": str(rate_info["limit_per_minute"]),
                    "X-RateLimit-Remaining-Minute": str(rate_info["remaining_per_minute"]),
                    "Retry-After": "60",
                },
            )

        # Record this request
        self._requests[client_ip].append(time.time())

        # Process request and add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit-Hour"] = str(rate_info["limit_per_hour"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(rate_info["remaining_per_hour"])
        response.headers["X-RateLimit-Limit-Minute"] = str(rate_info["limit_per_minute"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(rate_info["remaining_per_minute"])

        return response
