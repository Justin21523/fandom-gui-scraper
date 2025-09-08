# gui/__init__.py
"""
GUI package for Fandom Scraper application.

This package contains all PyQt5-based user interface components including
the main window, dialogs, widgets, and controllers.
"""

__version__ = "1.0.0"
__author__ = "Fandom Scraper Team"

# Import main components for easy access
from gui.main_window import MainWindow
from gui.controllers.scraper_controller import ScraperController

__all__ = [
    "MainWindow",
    "ScraperController",
]
