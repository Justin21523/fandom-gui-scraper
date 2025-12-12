# api/security/jwt.py
"""
JWT authentication convenience imports.

This module re-exports authentication dependencies for easier importing.
"""

from api.security.dependencies import require_auth

# Alias for backward compatibility
get_current_user = require_auth

__all__ = ["get_current_user", "require_auth"]
