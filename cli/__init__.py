# cli/__init__.py
"""
Fandom Scraper Command Line Interface package.

This package provides CLI commands for:
- Scraping character data from Fandom wikis
- Exporting data to various formats (CSV, JSON, Excel)
- Managing the character database
- Viewing statistics

Usage:
    python -m cli.main --help
    python -m cli.main scrape onepiece
    python -m cli.main export --format csv
    python -m cli.main stats
    python -m cli.main list-characters --anime "One Piece"
"""

from cli.main import app, main

__all__ = ["app", "main"]
