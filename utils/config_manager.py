# utils/config_manager.py
"""
Configuration management system for the Fandom Scraper application.

This module provides centralized configuration management with support for
environment variables, file-based configs, and runtime configuration updates.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str = "localhost"
    port: int = 27017
    name: str = "fandom_scraper"
    username: Optional[str] = None
    password: Optional[str] = None
    uri: Optional[str] = None

    def get_connection_string(self) -> str:
        """Build MongoDB connection string."""
        if self.uri:
            return self.uri

        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
        else:
            return f"mongodb://{self.host}:{self.port}/"


@dataclass
class ScrapingConfig:
    """Web scraping configuration."""

    delay: float = 1.0
    concurrent_requests: int = 8
    retry_times: int = 3
    timeout: int = 30
    user_agent: str = "FandomScraper/1.0 (+https://github.com/user/fandom-scraper)"
    respect_robots_txt: bool = True
    enable_auto_throttling: bool = True
    download_delay_range: tuple = (0.5, 1.5)
    max_concurrent_requests_per_domain: int = 1


@dataclass
class StorageConfig:
    """File storage configuration."""

    images_dir: str = "storage/images/"
    documents_dir: str = "storage/documents/"
    exports_dir: str = "storage/exports/"
    backups_dir: str = "storage/backups/"
    max_image_size_mb: int = 10
    allowed_image_formats: List[str] = None  # type: ignore

    def __post_init__(self):
        if self.allowed_image_formats is None:
            self.allowed_image_formats = [".jpg", ".jpeg", ".png", ".gif", ".webp"]


@dataclass
class GUIConfig:
    """GUI application configuration."""

    theme: str = "dark"
    window_width: int = 1000
    window_height: int = 700
    auto_save_interval: int = 300
    show_splash_screen: bool = True
    remember_window_position: bool = True
    enable_animations: bool = True
    update_check_interval_days: int = 7


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file_path: str = "logs/app.log"
    max_file_size_mb: int = 50
    backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_console_logging: bool = True
    enable_file_logging: bool = True


@dataclass
class APIConfig:
    """API server configuration."""

    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    cors_enabled: bool = True
    rate_limit_requests: int = 1000
    rate_limit_window_hours: int = 1
    enable_docs: bool = True


class ConfigManager:
    """
    Centralized configuration management system.

    This class handles loading, validation, and management of application
    settings from multiple sources including files, environment variables,
    and runtime updates.

    Example:
        >>> config = ConfigManager()
        >>> config.load_config()
        >>> db_host = config.database.host
        >>> print(db_host)
        "localhost"
    """

    def __init__(self, config_dir: Union[str, Path] = None):  # type: ignore
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent.parent / "config"

        # Initialize configuration objects with defaults
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.storage = StorageConfig()
        self.gui = GUIConfig()
        self.logging = LoggingConfig()
        self.api = APIConfig()

        # Additional settings
        self.debug_mode = False
        self.development_mode = False
        self.custom_settings = {}

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration on initialization
        self.load_config()

    def load_config(self) -> bool:
        """
        Load configuration from all sources.

        Priority order:
        1. Environment variables (highest)
        2. User configuration file
        3. Default configuration file
        4. Built-in defaults (lowest)

        Returns:
            True if configuration loaded successfully, False otherwise
        """
        try:
            logger.info("Loading application configuration...")

            # Load default configuration
            self._load_default_config()

            # Load user configuration (overrides defaults)
            self._load_user_config()

            # Load environment variables (overrides all)
            self._load_environment_config()

            # Validate configuration
            validation_result = self.validate_config()
            if not validation_result["valid"]:
                logger.warning(
                    f"Configuration validation warnings: {validation_result['warnings']}"
                )

            # Create necessary directories
            self._create_directories()

            logger.info("Configuration loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def _load_default_config(self):
        """Load default configuration from file."""
        default_config_file = self.config_dir / "default_config.yaml"

        # Create default config file if it doesn't exist
        if not default_config_file.exists():
            self._create_default_config_file()

        try:
            with open(default_config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            self._apply_config_data(config_data)
            logger.debug("Default configuration loaded")

        except Exception as e:
            logger.warning(f"Failed to load default configuration: {e}")

    def _load_user_config(self):
        """Load user configuration from file."""
        user_config_file = self.config_dir / "user_config.yaml"

        if user_config_file.exists():
            try:
                with open(user_config_file, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

                self._apply_config_data(config_data)
                logger.debug("User configuration loaded")

            except Exception as e:
                logger.warning(f"Failed to load user configuration: {e}")

    def _load_environment_config(self):
        """Load configuration from environment variables."""
        # Database configuration
        if os.getenv("MONGODB_URI"):
            self.database.uri = os.getenv("MONGODB_URI")
        if os.getenv("MONGODB_HOST"):
            self.database.host = os.getenv("MONGODB_HOST")  # type: ignore
        if os.getenv("MONGODB_PORT"):
            self.database.port = int(os.getenv("MONGODB_PORT"))  # type: ignore
        if os.getenv("MONGODB_DATABASE"):
            self.database.name = os.getenv("MONGODB_DATABASE")  # type: ignore
        if os.getenv("MONGODB_USERNAME"):
            self.database.username = os.getenv("MONGODB_USERNAME")
        if os.getenv("MONGODB_PASSWORD"):
            self.database.password = os.getenv("MONGODB_PASSWORD")

        # Scraping configuration
        if os.getenv("SCRAPER_DELAY"):
            self.scraping.delay = float(os.getenv("SCRAPER_DELAY"))  # type: ignore
        if os.getenv("SCRAPER_CONCURRENT_REQUESTS"):
            self.scraping.concurrent_requests = int(
                os.getenv("SCRAPER_CONCURRENT_REQUESTS")  # type: ignore
            )
        if os.getenv("SCRAPER_USER_AGENT"):
            self.scraping.user_agent = os.getenv("SCRAPER_USER_AGENT")  # type: ignore

        # Storage configuration
        if os.getenv("STORAGE_IMAGES_DIR"):
            self.storage.images_dir = os.getenv("STORAGE_IMAGES_DIR")  # type: ignore
        if os.getenv("STORAGE_EXPORTS_DIR"):
            self.storage.exports_dir = os.getenv("STORAGE_EXPORTS_DIR")  # type: ignore

        # General settings
        if os.getenv("DEBUG"):
            self.debug_mode = os.getenv("DEBUG").lower() in ("true", "1", "yes")  # type: ignore
        if os.getenv("DEVELOPMENT"):
            self.development_mode = os.getenv("DEVELOPMENT").lower() in (  # type: ignore
                "true",
                "1",
                "yes",
            )

        # Logging level
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL").upper()  # type: ignore

        logger.debug("Environment configuration loaded")

    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to config objects."""
        if not config_data:
            return

        # Database configuration
        if "database" in config_data:
            db_config = config_data["database"]
            for key, value in db_config.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)

        # Scraping configuration
        if "scraping" in config_data:
            scraping_config = config_data["scraping"]
            for key, value in scraping_config.items():
                if hasattr(self.scraping, key):
                    setattr(self.scraping, key, value)

        # Storage configuration
        if "storage" in config_data:
            storage_config = config_data["storage"]
            for key, value in storage_config.items():
                if hasattr(self.storage, key):
                    setattr(self.storage, key, value)

        # GUI configuration
        if "gui" in config_data:
            gui_config = config_data["gui"]
            for key, value in gui_config.items():
                if hasattr(self.gui, key):
                    setattr(self.gui, key, value)

        # Logging configuration
        if "logging" in config_data:
            logging_config = config_data["logging"]
            for key, value in logging_config.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)

        # API configuration
        if "api" in config_data:
            api_config = config_data["api"]
            for key, value in api_config.items():
                if hasattr(self.api, key):
                    setattr(self.api, key, value)

        # Custom settings
        if "custom" in config_data:
            self.custom_settings.update(config_data["custom"])

    def _create_default_config_file(self):
        """Create default configuration file."""
        default_config = {
            "database": asdict(DatabaseConfig()),
            "scraping": asdict(ScrapingConfig()),
            "storage": asdict(StorageConfig()),
            "gui": asdict(GUIConfig()),
            "logging": asdict(LoggingConfig()),
            "api": asdict(APIConfig()),
        }

        default_config_file = self.config_dir / "default_config.yaml"

        try:
            with open(default_config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    default_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

            logger.info("Created default configuration file")

        except Exception as e:
            logger.error(f"Failed to create default configuration file: {e}")

    def save_user_config(self) -> bool:
        """
        Save current configuration to user config file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            user_config = {
                "database": asdict(self.database),
                "scraping": asdict(self.scraping),
                "storage": asdict(self.storage),
                "gui": asdict(self.gui),
                "logging": asdict(self.logging),
                "api": asdict(self.api),
                "custom": self.custom_settings,
            }

            user_config_file = self.config_dir / "user_config.yaml"

            with open(user_config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    user_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

            logger.info("User configuration saved")
            return True

        except Exception as e:
            logger.error(f"Failed to save user configuration: {e}")
            return False

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration.

        Returns:
            Dictionary containing validation results
        """
        validation_result = {"valid": True, "errors": [], "warnings": []}

        # Validate database configuration
        if self.database.port < 1 or self.database.port > 65535:
            validation_result["errors"].append(
                "Database port must be between 1 and 65535"
            )
            validation_result["valid"] = False

        if not self.database.name or len(self.database.name.strip()) == 0:
            validation_result["errors"].append("Database name cannot be empty")
            validation_result["valid"] = False

        # Validate scraping configuration
        if self.scraping.delay < 0:
            validation_result["warnings"].append("Scraping delay should be positive")

        if self.scraping.concurrent_requests < 1:
            validation_result["errors"].append("Concurrent requests must be at least 1")
            validation_result["valid"] = False

        if self.scraping.timeout < 1:
            validation_result["errors"].append("Timeout must be at least 1 second")
            validation_result["valid"] = False

        # Validate storage configuration
        if self.storage.max_image_size_mb < 1:
            validation_result["warnings"].append(
                "Maximum image size should be at least 1MB"
            )

        # Validate GUI configuration
        if self.gui.window_width < 800 or self.gui.window_height < 600:
            validation_result["warnings"].append(
                "Window size might be too small for optimal experience"
            )

        # Validate logging configuration
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_log_levels:
            validation_result["errors"].append(
                f"Invalid log level: {self.logging.level}"
            )
            validation_result["valid"] = False

        return validation_result

    def _create_directories(self):
        """Create necessary directories based on configuration."""
        directories = [
            self.storage.images_dir,
            self.storage.documents_dir,
            self.storage.exports_dir,
            self.storage.backups_dir,
            os.path.dirname(self.logging.file_path),
        ]

        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create directory {directory}: {e}")

    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path to setting (e.g., 'database.host')
            default: Default value if setting not found

        Returns:
            Configuration value or default
        """
        try:
            keys = key_path.split(".")

            # Get the main config section
            section_name = keys[0]
            if section_name == "database":
                config_obj = self.database
            elif section_name == "scraping":
                config_obj = self.scraping
            elif section_name == "storage":
                config_obj = self.storage
            elif section_name == "gui":
                config_obj = self.gui
            elif section_name == "logging":
                config_obj = self.logging
            elif section_name == "api":
                config_obj = self.api
            elif section_name == "custom":
                config_obj = self.custom_settings
            else:
                return default

            # Navigate to the specific setting
            if len(keys) == 1:
                return config_obj

            value = config_obj
            for key in keys[1:]:
                if hasattr(value, key):
                    value = getattr(value, key)
                elif isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

        except Exception as e:
            logger.warning(f"Failed to get setting {key_path}: {e}")
            return default

    def set_setting(self, key_path: str, value: Any) -> bool:
        """
        Set configuration value using dot notation.

        Args:
            key_path: Dot-separated path to setting
            value: Value to set

        Returns:
            True if setting was updated successfully, False otherwise
        """
        try:
            keys = key_path.split(".")

            # Get the main config section
            section_name = keys[0]
            if section_name == "database":
                config_obj = self.database
            elif section_name == "scraping":
                config_obj = self.scraping
            elif section_name == "storage":
                config_obj = self.storage
            elif section_name == "gui":
                config_obj = self.gui
            elif section_name == "logging":
                config_obj = self.logging
            elif section_name == "api":
                config_obj = self.api
            elif section_name == "custom":
                config_obj = self.custom_settings
            else:
                return False

            # Set the value
            if len(keys) == 1:
                # Cannot replace entire config object
                return False
            elif len(keys) == 2:
                # Direct attribute or dict key
                if hasattr(config_obj, keys[1]):
                    setattr(config_obj, keys[1], value)
                elif isinstance(config_obj, dict):
                    config_obj[keys[1]] = value
                else:
                    return False
            else:
                # Navigate to parent and set child
                parent = config_obj
                for key in keys[1:-1]:
                    if hasattr(parent, key):
                        parent = getattr(parent, key)
                    elif isinstance(parent, dict) and key in parent:
                        parent = parent[key]
                    else:
                        return False

                # Set final value
                final_key = keys[-1]
                if hasattr(parent, final_key):
                    setattr(parent, final_key, value)
                elif isinstance(parent, dict):
                    parent[final_key] = value
                else:
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to set setting {key_path}: {e}")
            return False

    def export_config(self, file_path: Union[str, Path]) -> bool:
        """
        Export current configuration to file.

        Args:
            file_path: Path to export file

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            config_data = {
                "database": asdict(self.database),
                "scraping": asdict(self.scraping),
                "storage": asdict(self.storage),
                "gui": asdict(self.gui),
                "logging": asdict(self.logging),
                "api": asdict(self.api),
                "custom": self.custom_settings,
                "exported_at": datetime.utcnow().isoformat(),
            }

            file_path = Path(file_path)

            if file_path.suffix.lower() == ".json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        config_data,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )

            logger.info(f"Configuration exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False

    def import_config(self, file_path: Union[str, Path]) -> bool:
        """
        Import configuration from file.

        Args:
            file_path: Path to import file

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                logger.error(f"Configuration file not found: {file_path}")
                return False

            if file_path.suffix.lower() == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

            # Remove metadata
            config_data.pop("exported_at", None)

            # Apply imported configuration
            self._apply_config_data(config_data)

            # Validate imported configuration
            validation_result = self.validate_config()
            if not validation_result["valid"]:
                logger.warning(
                    f"Imported configuration has issues: {validation_result['errors']}"
                )

            logger.info(f"Configuration imported from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False

    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.storage = StorageConfig()
        self.gui = GUIConfig()
        self.logging = LoggingConfig()
        self.api = APIConfig()
        self.custom_settings = {}

        logger.info("Configuration reset to defaults")

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.

        Returns:
            Dictionary containing configuration summary
        """
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "has_auth": bool(self.database.username),
            },
            "scraping": {
                "delay": self.scraping.delay,
                "concurrent_requests": self.scraping.concurrent_requests,
                "respect_robots_txt": self.scraping.respect_robots_txt,
            },
            "storage": {
                "images_dir": self.storage.images_dir,
                "max_image_size_mb": self.storage.max_image_size_mb,
            },
            "gui": {
                "theme": self.gui.theme,
                "window_size": f"{self.gui.window_width}x{self.gui.window_height}",
            },
            "logging": {
                "level": self.logging.level,
                "file_logging": self.logging.enable_file_logging,
            },
            "debug_mode": self.debug_mode,
            "development_mode": self.development_mode,
        }


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get or create the global configuration manager instance.

    Returns:
        Global ConfigManager instance
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager()

    return _config_manager


def get_setting(key_path: str, default: Any = None) -> Any:
    """
    Convenience function to get a configuration setting.

    Args:
        key_path: Dot-separated path to setting
        default: Default value if setting not found

    Returns:
        Configuration value or default
    """
    return get_config_manager().get_setting(key_path, default)


def set_setting(key_path: str, value: Any) -> bool:
    """
    Convenience function to set a configuration setting.

    Args:
        key_path: Dot-separated path to setting
        value: Value to set

    Returns:
        True if setting was updated successfully, False otherwise
    """
    return get_config_manager().set_setting(key_path, value)


def save_config() -> bool:
    """
    Convenience function to save current configuration.

    Returns:
        True if saved successfully, False otherwise
    """
    return get_config_manager().save_user_config()
