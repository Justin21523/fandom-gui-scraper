# api/endpoints/auth.py
"""
Authentication endpoints for the API.

This module provides endpoints for user authentication and token management.
"""

import os
from datetime import timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.security.auth import (
    create_access_token,
    verify_password,
    hash_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from api.security.dependencies import require_auth

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Simple in-memory user store for demo purposes
# In production, this should be replaced with a database
_demo_users: Dict[str, Dict[str, Any]] = {}
_demo_users_initialized = False


def _init_demo_users():
    """Initialize demo users lazily to avoid startup issues."""
    global _demo_users_initialized
    if _demo_users_initialized:
        return

    _demo_admin_username = os.getenv("API_ADMIN_USERNAME", "admin")
    _demo_admin_password = os.getenv("API_ADMIN_PASSWORD", "admin")
    if _demo_admin_username and _demo_admin_password:
        _demo_users[_demo_admin_username] = {
            "username": _demo_admin_username,
            "hashed_password": hash_password(_demo_admin_password),
            "is_admin": True,
        }
    _demo_users_initialized = True


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""

    username: str
    is_admin: bool = False


class UserCreate(BaseModel):
    """User creation request model."""

    username: str
    password: str


class UserResponse(BaseModel):
    """User response model (without password)."""

    username: str
    is_admin: bool = False


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Obtain an access token using username and password.

    This endpoint follows the OAuth2 password flow.
    """
    _init_demo_users()
    user = _demo_users.get(form_data.username)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user["username"],
            "is_admin": user.get("is_admin", False),
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user: Dict[str, Any] = Depends(require_auth),
) -> UserResponse:
    """
    Get information about the currently authenticated user.
    """
    return UserResponse(
        username=user.get("sub", "unknown"),
        is_admin=user.get("is_admin", False),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate) -> UserResponse:
    """
    Register a new user.

    Note: In production, this should be protected or disabled.
    """
    if user_data.username in _demo_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    _demo_users[user_data.username] = {
        "username": user_data.username,
        "hashed_password": hash_password(user_data.password),
        "is_admin": False,
    }

    return UserResponse(username=user_data.username, is_admin=False)
