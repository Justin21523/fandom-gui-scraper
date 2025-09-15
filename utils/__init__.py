# utils/__init__.py
"""
Utils package for the Fandom Scraper project.

This package provides comprehensive utilities for data processing, export,
visualization, and various helper functions for the scraper application.
"""

# Import existing utilities
from .config_manager import ConfigManager
from .logger import setup_logger, get_logger
from .normalizer import DataNormalizer
from .selectors import SelectorManager

# Import new core utilities
from .thread_manager import ThreadManager
from .file_manager import FileManager
from .network_utils import NetworkUtils

# Import data processing utilities
from .data_processing import (
    DataFusion,
    DeduplicationEngine,
    QualityScorer,
    TextProcessor,
    ImageProcessor,
)

# Import export utilities
from .export import JSONExporter, CSVExporter, ExcelExporter, PDFExporter

# Import visualization utilities
from .visualization import ChartGenerator, StatsCalculator, ReportGenerator

__all__ = [
    # Core utilities
    "ConfigManager",
    "setup_logger",
    "get_logger",
    "DataNormalizer",
    "SelectorManager",
    "ThreadManager",
    "FileManager",
    "NetworkUtils",
    # Data processing
    "DataFusion",
    "DeduplicationEngine",
    "QualityScorer",
    "TextProcessor",
    "ImageProcessor",
    # Export utilities
    "JSONExporter",
    "CSVExporter",
    "ExcelExporter",
    "PDFExporter",
    # Visualization
    "ChartGenerator",
    "StatsCalculator",
    "ReportGenerator",
]

__version__ = "1.0.0"
