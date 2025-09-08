# models/__init__.py
"""
Models Package

This package contains all data models for the Fandom scraper application,
providing Pydantic-based validation and MongoDB integration.
"""

# Import all main models for easy access
from .document import (
    # Main models
    AnimeCharacter,
    AnimeSeriesInfo,
    # Component models
    CharacterImage,
    CharacterRelationship,
    CharacterAbility,
    CharacterAppearance,
    OnePieceSpecificData,
    # Enums
    DataQuality,
    CharacterStatus,
    ImageType,
    RelationshipType,
    # Utility functions
    get_model_class,
    validate_character_data,
    create_onepiece_character,
    MODEL_REGISTRY,
)

# Import storage functionality
from .storage import (
    DatabaseManager,
    CharacterRepository,
    AnimeRepository,
    MongoDBConnection,
)

__version__ = "1.0.0"

# Package metadata
__author__ = "Fandom Scraper Team"
__email__ = "contact@fandomscraper.com"
__description__ = "Data models and database management for Fandom scraper"

# Public API
__all__ = [
    # Main models
    "AnimeCharacter",
    "AnimeSeriesInfo",
    # Component models
    "CharacterImage",
    "CharacterRelationship",
    "CharacterAbility",
    "CharacterAppearance",
    "OnePieceSpecificData",
    # Enums
    "DataQuality",
    "CharacterStatus",
    "ImageType",
    "RelationshipType",
    # Storage classes
    "DatabaseManager",
    "CharacterRepository",
    "AnimeRepository",
    "MongoDBConnection",
    # Utility functions
    "get_model_class",
    "validate_character_data",
    "create_onepiece_character",
    "MODEL_REGISTRY",
]

# Default configurations
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "fandom_scraper",
    "collection_characters": "characters",
    "collection_anime": "anime_series",
    "connection_timeout": 30000,
    "server_selection_timeout": 5000,
}

# Model validation settings
VALIDATION_CONFIG = {
    "strict_mode": True,
    "allow_extra_fields": False,
    "validate_assignment": True,
    "use_enum_values": True,
}


def configure_models(config: dict = None):  # type: ignore
    """
    Configure global model settings.

    Args:
        config: Configuration dictionary
    """
    if config:
        VALIDATION_CONFIG.update(config)


def get_default_db_config() -> dict:
    """
    Get default database configuration.

    Returns:
        Default database configuration dictionary
    """
    return DEFAULT_DB_CONFIG.copy()


# Version information
def get_version_info() -> dict:
    """
    Get package version information.

    Returns:
        Version information dictionary
    """
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
    }
