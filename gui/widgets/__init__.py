# gui/widgets/__init__.py
"""
GUI widgets package for Fandom Scraper.

Contains reusable PyQt5 widgets and custom components used throughout
the application interface.
"""

from gui.widgets.progress_dialog import ProgressDialog
from gui.widgets.scraper_config_widget import ScraperConfigWidget
from gui.widgets.data_viewer_widget import DataViewerWidget

__all__ = [
    "ProgressDialog",
    "ScraperConfigWidget",
    "DataViewerWidget",
]
