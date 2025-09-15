# utils/data_processing/__init__.py
"""
Data processing utilities package.

This package provides comprehensive data processing tools for character data,
including fusion, deduplication, quality scoring, and text/image processing.
"""

from .data_fusion import DataFusion, create_default_fusion_config
from .deduplication import DeduplicationEngine, create_deduplication_config
from .quality_scorer import QualityScorer, create_quality_config
from .text_processor import TextProcessor, create_text_processor_config
from .image_processor import ImageProcessor, create_image_processor_config

__all__ = [
    "DataFusion",
    "DeduplicationEngine",
    "QualityScorer",
    "TextProcessor",
    "ImageProcessor",
    "create_default_fusion_config",
    "create_deduplication_config",
    "create_quality_config",
    "create_text_processor_config",
    "create_image_processor_config",
]

__version__ = "1.0.0"
