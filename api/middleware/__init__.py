# api/middleware/__init__.py
"""
API middleware components.
"""

from api.middleware.rate_limit import RateLimitMiddleware

__all__ = ["RateLimitMiddleware"]
