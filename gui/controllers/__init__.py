# gui/controllers/__init__.py
"""
GUI controllers package for Fandom Scraper.

Contains controller classes that manage business logic and coordinate
between the GUI components and the data/scraping layers.
"""

from gui.controllers.scraper_controller import ScraperController

__all__ = [
    "ScraperController",
]
