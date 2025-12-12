# api/__init__.py
"""
Fandom Scraper REST API package.

This package provides a FastAPI-based REST API for accessing
scraped anime character data.

Usage:
    uvicorn api.main:app --reload --port 8000

Endpoints:
    GET /api/v1/characters - List characters
    GET /api/v1/characters/{id} - Get character by ID
    GET /api/v1/characters/search - Search characters
    GET /api/v1/characters/stats - Get statistics
    POST /api/v1/characters - Create character
    PATCH /api/v1/characters/{id} - Update character
    DELETE /api/v1/characters/{id} - Delete character
"""

from api.main import app

__all__ = ["app"]
