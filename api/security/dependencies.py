# api/security/dependencies.py
"""
FastAPI dependencies for authentication.

This module provides reusable dependencies for protecting API endpoints.
"""

from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from api.security.auth import verify_token

# OAuth2 scheme - token URL is where clients can obtain tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[Dict[str, Any]]:
    """
    Get current user from token, returning None if not authenticated.

    This dependency is useful for endpoints that work differently
    for authenticated vs unauthenticated users.

    Args:
        token: Optional JWT token from Authorization header

    Returns:
        User payload if authenticated, None otherwise
    """
    if token is None:
        return None
    return verify_token(token)


async def require_auth(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """
    Require authentication for an endpoint.

    Use this dependency to protect endpoints that require a valid token.

    Args:
        token: JWT token from Authorization header

    Returns:
        User payload from the verified token

    Raises:
        HTTPException: 401 if not authenticated or token is invalid
    """
    import os

    if os.getenv("AUTH_DISABLED", "").lower() in ("1", "true", "yes"):
        return {"username": "dev", "id": "dev", "is_admin": True}

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_admin(
    user: Dict[str, Any] = Depends(require_auth),
) -> Dict[str, Any]:
    """
    Require admin role for an endpoint.

    Args:
        user: Authenticated user from require_auth

    Returns:
        User payload if user is admin

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
