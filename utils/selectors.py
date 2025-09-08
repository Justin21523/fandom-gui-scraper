# utils/selectors.py
"""
CSS/XPath selector configuration management for web scraping.

This module provides a centralized system for managing and loading
CSS selectors and XPath expressions used in web scraping operations.
"""

import logging
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SelectorType(str, Enum):
    """Enumeration for selector types."""

    CSS = "css"
    XPATH = "xpath"
    REGEX = "regex"


@dataclass
class SelectorConfig:
    """
    Configuration class for CSS/XPath selectors.

    Attributes:
        selector: The CSS selector or XPath expression
        selector_type: Type of selector (css, xpath, regex)
        attribute: HTML attribute to extract (for CSS selectors)
        multiple: Whether to extract multiple elements
        required: Whether this field is required
        fallback_selectors: List of fallback selectors to try
        post_process: Post-processing function name
        description: Human-readable description
    """

    selector: str
    selector_type: SelectorType = SelectorType.CSS
    attribute: Optional[str] = None
    multiple: bool = False
    required: bool = False
    fallback_selectors: List[str] = None  # type: ignore
    post_process: Optional[str] = None
    description: str = ""

    def __post_init__(self):
        """Initialize fallback selectors list if None."""
        if self.fallback_selectors is None:
            self.fallback_selectors = []


class SelectorManager:
    """
    Manager class for loading and managing selector configurations.

    This class handles loading selector configurations from YAML files,
    providing fallback mechanisms, and caching for performance.

    Attributes:
        config_dir: Directory containing selector configuration files
        cache: Cache for loaded configurations

    Example:
        >>> manager = SelectorManager()
        >>> selectors = manager.get_selectors("onepiece")
        >>> name_selector = selectors["character_page"]["name"]
        >>> print(name_selector.selector)
        "h1.page-header__title"
    """

    def __init__(self, config_dir: Union[str, Path] = None):  # type: ignore
        """
        Initialize selector manager with configuration directory.

        Args:
            config_dir: Path to directory containing selector configs
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to config/selector_configs in project root
            self.config_dir = (
                Path(__file__).parent.parent / "config" / "selector_configs"
            )

        self.cache: Dict[str, Dict[str, Any]] = {}
        self._ensure_config_directory()

    def _ensure_config_directory(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Create default configurations if they don't exist
        self._create_default_configs()

    def _create_default_configs(self):
        """Create default selector configurations for common anime wikis."""
        # Generic Fandom wiki selectors
        generic_config = {
            "selectors": {
                "character_list": {
                    "url_pattern": "https://{anime}.fandom.com/wiki/Category:Characters",
                    "character_links": {
                        "selector": ".category-page__members a",
                        "selector_type": "css",
                        "attribute": "href",
                        "multiple": True,
                        "description": "Links to individual character pages",
                    },
                    "next_page": {
                        "selector": ".category-page__pagination-next",
                        "selector_type": "css",
                        "attribute": "href",
                        "required": False,
                        "description": "Next page link for pagination",
                    },
                },
                "character_page": {
                    "name": {
                        "selector": "h1.page-header__title",
                        "selector_type": "css",
                        "required": True,
                        "fallback_selectors": [
                            ".page-header__title",
                            "h1",
                            ".mw-page-title-main",
                        ],
                        "description": "Character name from page header",
                    },
                    "infobox": {
                        "selector": ".portable-infobox",
                        "selector_type": "css",
                        "required": False,
                        "fallback_selectors": [".infobox", ".character-infobox"],
                        "description": "Main character information box",
                    },
                    "description": {
                        "selector": ".mw-parser-output > p:first-of-type",
                        "selector_type": "css",
                        "required": False,
                        "fallback_selectors": [
                            ".mw-content-text > p:first-of-type",
                            ".WikiaArticle p:first-of-type",
                        ],
                        "description": "Character description paragraph",
                    },
                    "main_image": {
                        "selector": ".pi-image img",
                        "selector_type": "css",
                        "attribute": "src",
                        "required": False,
                        "fallback_selectors": [".infobox img", ".character-image img"],
                        "description": "Main character image",
                    },
                    "gallery_images": {
                        "selector": ".wikia-gallery img",
                        "selector_type": "css",
                        "attribute": "src",
                        "multiple": True,
                        "required": False,
                        "description": "Gallery images of character",
                    },
                },
                "infobox_fields": {
                    "age": {
                        "selector": "[data-source='age'] .pi-data-value",
                        "selector_type": "css",
                        "required": False,
                        "fallback_selectors": [
                            ".age .pi-data-value",
                            ".infobox-data[data-source='age']",
                        ],
                        "description": "Character age from infobox",
                    },
                    "gender": {
                        "selector": "[data-source='gender'] .pi-data-value",
                        "selector_type": "css",
                        "required": False,
                        "fallback_selectors": [".gender .pi-data-value"],
                        "description": "Character gender",
                    },
                    "occupation": {
                        "selector": "[data-source='occupation'] .pi-data-value",
                        "selector_type": "css",
                        "required": False,
                        "fallback_selectors": [".occupation .pi-data-value"],
                        "description": "Character occupation",
                    },
                    "status": {
                        "selector": "[data-source='status'] .pi-data-value",
                        "selector_type": "css",
                        "required": False,
                        "description": "Character status (alive, deceased, etc.)",
                    },
                },
            },
            "data_extraction_rules": {
                "text_cleanup": [
                    "strip_whitespace",
                    "remove_citations",
                    "normalize_unicode",
                ],
                "image_processing": [
                    "resolve_relative_urls",
                    "filter_minimum_size",
                    "deduplicate_urls",
                ],
            },
            "fallback_strategies": {
                "character_name": {
                    "primary": "h1.page-header__title",
                    "secondary": ".page-header__title",
                    "tertiary": "h1",
                }
            },
        }

        # Save generic config
        generic_config_path = self.config_dir / "generic_fandom.yaml"
        if not generic_config_path.exists():
            with open(generic_config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    generic_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

        # One Piece specific configuration
        onepiece_config = {
            "extends": "generic_fandom",
            "selectors": {
                "character_list": {
                    "url_pattern": "https://onepiece.fandom.com/wiki/Category:Characters",
                    "character_links": {
                        "selector": ".category-page__members a[href*='/wiki/']:not([href*='Category:']):not([href*='File:'])",
                        "selector_type": "css",
                        "attribute": "href",
                        "multiple": True,
                        "description": "Character page links excluding categories and files",
                    },
                },
                "character_page": {
                    "name": {
                        "selector": "h1.page-header__title",
                        "selector_type": "css",
                        "required": True,
                        "post_process": "clean_character_name",
                        "description": "Character name with One Piece specific cleaning",
                    }
                },
                "infobox_fields": {
                    "bounty": {
                        "selector": "[data-source='bounty'] .pi-data-value",
                        "selector_type": "css",
                        "required": False,
                        "post_process": "parse_bounty",
                        "description": "Character bounty amount",
                    },
                    "devil_fruit": {
                        "selector": "[data-source='dfname'] .pi-data-value",
                        "selector_type": "css",
                        "required": False,
                        "description": "Devil fruit name",
                    },
                    "crew": {
                        "selector": "[data-source='crew'] .pi-data-value a",
                        "selector_type": "css",
                        "required": False,
                        "description": "Pirate crew affiliation",
                    },
                    "epithet": {
                        "selector": "[data-source='epithet'] .pi-data-value",
                        "selector_type": "css",
                        "required": False,
                        "description": "Character epithet or nickname",
                    },
                },
            },
            "anime_specific": {
                "name": "One Piece",
                "base_url": "https://onepiece.fandom.com",
                "special_categories": [
                    "Straw Hat Pirates",
                    "Marines",
                    "Pirates",
                    "Devil Fruit Users",
                ],
            },
        }

        # Save One Piece config
        onepiece_config_path = self.config_dir / "onepiece.yaml"
        if not onepiece_config_path.exists():
            with open(onepiece_config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    onepiece_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

        logger.info("Default selector configurations created")

    def get_selectors(self, anime_name: str) -> Dict[str, Any]:
        """
        Get selector configuration for specific anime.

        Args:
            anime_name: Name of the anime (e.g., 'onepiece', 'naruto')

        Returns:
            Dictionary containing selector configuration

        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If configuration is invalid
        """
        # Normalize anime name
        anime_key = anime_name.lower().replace(" ", "").replace("-", "")

        # Check cache first
        if anime_key in self.cache:
            return self.cache[anime_key]

        # Try to load specific configuration
        config_file = self.config_dir / f"{anime_key}.yaml"
        if not config_file.exists():
            # Fallback to generic configuration
            logger.warning(
                f"No specific configuration found for {anime_name}, using generic"
            )
            config_file = self.config_dir / "generic_fandom.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"No selector configuration found for {anime_name}")

        try:
            # Load configuration
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Handle configuration inheritance
            if "extends" in config:
                base_config = self._load_base_config(config["extends"])
                config = self._merge_configs(base_config, config)

            # Convert to SelectorConfig objects
            processed_config = self._process_config(config)

            # Cache the result
            self.cache[anime_key] = processed_config

            logger.info(f"Loaded selector configuration for {anime_name}")
            return processed_config

        except Exception as e:
            logger.error(f"Failed to load selector configuration for {anime_name}: {e}")
            raise ValueError(f"Invalid configuration for {anime_name}: {e}")

    def _load_base_config(self, base_name: str) -> Dict[str, Any]:
        """
        Load base configuration for inheritance.

        Args:
            base_name: Name of base configuration

        Returns:
            Base configuration dictionary
        """
        base_file = self.config_dir / f"{base_name}.yaml"
        if not base_file.exists():
            raise FileNotFoundError(f"Base configuration not found: {base_name}")

        with open(base_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _merge_configs(
        self, base_config: Dict[str, Any], child_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge child configuration with base configuration.

        Args:
            base_config: Base configuration dictionary
            child_config: Child configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        merged = base_config.copy()

        for key, value in child_config.items():
            if key == "extends":
                continue  # Skip the extends directive

            if (
                isinstance(value, dict)
                and key in merged
                and isinstance(merged[key], dict)
            ):
                # Recursively merge dictionaries
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Override with child value
                merged[key] = value

        return merged

    def _process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process configuration and convert selectors to SelectorConfig objects.

        Args:
            config: Raw configuration dictionary

        Returns:
            Processed configuration with SelectorConfig objects
        """
        processed = {}

        for section_name, section_data in config.items():
            if section_name == "selectors":
                processed[section_name] = self._process_selectors(section_data)
            else:
                processed[section_name] = section_data

        return processed

    def _process_selectors(self, selectors: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process selector section and create SelectorConfig objects.

        Args:
            selectors: Selector configuration dictionary

        Returns:
            Processed selectors with SelectorConfig objects
        """
        processed_selectors = {}

        for page_type, page_selectors in selectors.items():
            processed_selectors[page_type] = {}

            for field_name, field_config in page_selectors.items():
                if isinstance(field_config, dict) and "selector" in field_config:
                    # Convert to SelectorConfig object
                    selector_config = SelectorConfig(
                        selector=field_config["selector"],
                        selector_type=SelectorType(
                            field_config.get("selector_type", "css")
                        ),
                        attribute=field_config.get("attribute"),
                        multiple=field_config.get("multiple", False),
                        required=field_config.get("required", False),
                        fallback_selectors=field_config.get("fallback_selectors", []),
                        post_process=field_config.get("post_process"),
                        description=field_config.get("description", ""),
                    )
                    processed_selectors[page_type][field_name] = selector_config
                else:
                    # Keep non-selector configuration as-is
                    processed_selectors[page_type][field_name] = field_config

        return processed_selectors

    def get_selector(
        self, anime_name: str, page_type: str, field_name: str
    ) -> Optional[SelectorConfig]:
        """
        Get specific selector configuration.

        Args:
            anime_name: Name of the anime
            page_type: Type of page (e.g., 'character_page', 'character_list')
            field_name: Name of the field (e.g., 'name', 'description')

        Returns:
            SelectorConfig object or None if not found
        """
        try:
            selectors = self.get_selectors(anime_name)
            return selectors.get("selectors", {}).get(page_type, {}).get(field_name)
        except Exception as e:
            logger.error(
                f"Failed to get selector {anime_name}.{page_type}.{field_name}: {e}"
            )
            return None

    def validate_selectors(self, anime_name: str) -> Dict[str, List[str]]:
        """
        Validate selector configuration for an anime.

        Args:
            anime_name: Name of the anime to validate

        Returns:
            Dictionary with validation results (errors, warnings, info)
        """
        validation_results = {"errors": [], "warnings": [], "info": []}

        try:
            config = self.get_selectors(anime_name)
            selectors = config.get("selectors", {})

            # Check for required page types
            required_pages = ["character_list", "character_page"]
            for page_type in required_pages:
                if page_type not in selectors:
                    validation_results["errors"].append(
                        f"Missing required page type: {page_type}"
                    )

            # Validate character_page selectors
            if "character_page" in selectors:
                character_selectors = selectors["character_page"]

                # Check for required fields
                required_fields = ["name"]
                for field in required_fields:
                    if field not in character_selectors:
                        validation_results["errors"].append(
                            f"Missing required field: character_page.{field}"
                        )
                    elif isinstance(character_selectors[field], SelectorConfig):
                        if not character_selectors[field].selector:
                            validation_results["errors"].append(
                                f"Empty selector for required field: character_page.{field}"
                            )

                # Check selector syntax
                for field_name, selector_config in character_selectors.items():
                    if isinstance(selector_config, SelectorConfig):
                        if not self._validate_selector_syntax(selector_config):
                            validation_results["warnings"].append(
                                f"Potentially invalid selector syntax: {field_name}"
                            )

            # Check for fallback selectors
            for page_type, page_selectors in selectors.items():
                for field_name, selector_config in page_selectors.items():
                    if isinstance(selector_config, SelectorConfig):
                        if (
                            selector_config.required
                            and not selector_config.fallback_selectors
                        ):
                            validation_results["warnings"].append(
                                f"Required field {page_type}.{field_name} has no fallback selectors"
                            )

            validation_results["info"].append(
                f"Configuration loaded successfully for {anime_name}"
            )

        except Exception as e:
            validation_results["errors"].append(
                f"Failed to validate configuration: {e}"
            )

        return validation_results

    def _validate_selector_syntax(self, selector_config: SelectorConfig) -> bool:
        """
        Basic validation of selector syntax.

        Args:
            selector_config: SelectorConfig object to validate

        Returns:
            True if selector appears valid, False otherwise
        """
        selector = selector_config.selector

        if selector_config.selector_type == SelectorType.CSS:
            # Basic CSS selector validation
            if not selector or len(selector.strip()) == 0:
                return False

            # Check for common CSS selector patterns
            css_patterns = [
                ".",
                "#",
                "[",
                ":",
                "h1",
                "h2",
                "h3",
                "div",
                "span",
                "p",
                "a",
                "img",
            ]
            if not any(pattern in selector for pattern in css_patterns):
                return False

        elif selector_config.selector_type == SelectorType.XPATH:
            # Basic XPath validation
            if not selector.startswith(("/", "./", "//")):
                return False

        return True

    def list_available_configs(self) -> List[str]:
        """
        List all available selector configurations.

        Returns:
            List of available configuration names
        """
        configs = []

        try:
            for config_file in self.config_dir.glob("*.yaml"):
                config_name = config_file.stem
                configs.append(config_name)

            return sorted(configs)

        except Exception as e:
            logger.error(f"Failed to list configurations: {e}")
            return []

    def create_config_template(self, anime_name: str, base_url: str) -> bool:
        """
        Create a new selector configuration template.

        Args:
            anime_name: Name of the anime
            base_url: Base URL of the anime's Fandom wiki

        Returns:
            True if template created successfully, False otherwise
        """
        try:
            anime_key = anime_name.lower().replace(" ", "").replace("-", "")
            config_file = self.config_dir / f"{anime_key}.yaml"

            if config_file.exists():
                logger.warning(f"Configuration already exists for {anime_name}")
                return False

            # Create template configuration
            template = {
                "extends": "generic_fandom",
                "selectors": {
                    "character_list": {
                        "url_pattern": f"{base_url}/wiki/Category:Characters",
                        "character_links": {
                            "selector": ".category-page__members a[href*='/wiki/']:not([href*='Category:']):not([href*='File:'])",
                            "selector_type": "css",
                            "attribute": "href",
                            "multiple": True,
                            "description": "Character page links",
                        },
                    },
                    "character_page": {
                        "name": {
                            "selector": "h1.page-header__title",
                            "selector_type": "css",
                            "required": True,
                            "fallback_selectors": [".page-header__title", "h1"],
                            "description": "Character name from page header",
                        }
                    },
                    "infobox_fields": {
                        # Add anime-specific infobox fields here
                        "age": {
                            "selector": "[data-source='age'] .pi-data-value",
                            "selector_type": "css",
                            "required": False,
                            "description": "Character age",
                        }
                    },
                },
                "anime_specific": {
                    "name": anime_name,
                    "base_url": base_url,
                    "special_categories": [
                        # Add anime-specific categories here
                    ],
                },
            }

            # Save template
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    template, f, default_flow_style=False, allow_unicode=True, indent=2
                )

            logger.info(f"Created configuration template for {anime_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create configuration template for {anime_name}: {e}"
            )
            return False

    def reload_config(self, anime_name: str):
        """
        Reload configuration from file (clear cache).

        Args:
            anime_name: Name of the anime to reload
        """
        anime_key = anime_name.lower().replace(" ", "").replace("-", "")
        if anime_key in self.cache:
            del self.cache[anime_key]
            logger.info(f"Reloaded configuration for {anime_name}")

    def clear_cache(self):
        """Clear all cached configurations."""
        self.cache.clear()
        logger.info("Cleared selector configuration cache")


# Global selector manager instance
_selector_manager: Optional[SelectorManager] = None


def get_selector_manager() -> SelectorManager:
    """
    Get or create the global selector manager instance.

    Returns:
        Global SelectorManager instance
    """
    global _selector_manager

    if _selector_manager is None:
        _selector_manager = SelectorManager()

    return _selector_manager


def get_selectors(anime_name: str) -> Dict[str, Any]:
    """
    Convenience function to get selectors for an anime.

    Args:
        anime_name: Name of the anime

    Returns:
        Selector configuration dictionary
    """
    manager = get_selector_manager()
    return manager.get_selectors(anime_name)


def get_selector(
    anime_name: str, page_type: str, field_name: str
) -> Optional[SelectorConfig]:
    """
    Convenience function to get a specific selector.

    Args:
        anime_name: Name of the anime
        page_type: Type of page
        field_name: Name of the field

    Returns:
        SelectorConfig object or None
    """
    manager = get_selector_manager()
    return manager.get_selector(anime_name, page_type, field_name)


def validate_selectors(anime_name: str) -> Dict[str, List[str]]:
    """
    Convenience function to validate selectors for an anime.

    Args:
        anime_name: Name of the anime

    Returns:
        Validation results dictionary
    """
    manager = get_selector_manager()
    return manager.validate_selectors(anime_name)
