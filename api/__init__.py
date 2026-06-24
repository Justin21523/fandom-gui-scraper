# api/__init__.py
"""Fandom Scraper REST API package.

Import `api.main:app` directly when an ASGI app instance is needed.
Keeping this package initializer light avoids importing the full API stack
when tests or tools only need a submodule.
"""

__all__: list[str] = []
