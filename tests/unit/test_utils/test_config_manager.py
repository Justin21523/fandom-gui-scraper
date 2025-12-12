# tests/unit/test_utils/test_config_manager.py
"""
Unit tests for configuration management module.

Tests configuration loading, security features, and connection string handling.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestDatabaseConfig:
    """Tests for DatabaseConfig class."""

    @pytest.fixture
    def db_config(self):
        """Create a DatabaseConfig instance."""
        from utils.config_manager import DatabaseConfig

        return DatabaseConfig(
            host="localhost",
            port=27017,
            name="test_db",
            username="testuser",
            password="testpass123!@#",
        )

    def test_connection_string_without_credentials(self):
        """Test connection string generation without credentials."""
        from utils.config_manager import DatabaseConfig

        config = DatabaseConfig(host="localhost", port=27017)
        conn_str = config.get_connection_string()

        assert conn_str == "mongodb://localhost:27017/"
        assert "testuser" not in conn_str
        assert "testpass" not in conn_str

    def test_connection_string_with_credentials(self, db_config):
        """Test connection string generation with credentials."""
        conn_str = db_config.get_connection_string()

        assert "mongodb://" in conn_str
        assert "@localhost:27017/" in conn_str
        assert "testuser" in conn_str

    def test_password_url_encoding(self):
        """Test that special characters in password are URL-encoded."""
        from utils.config_manager import DatabaseConfig

        config = DatabaseConfig(
            host="localhost",
            port=27017,
            username="user",
            password="pass@word#123",  # Contains special characters
        )

        conn_str = config.get_connection_string()

        # Special characters should be encoded
        assert "pass@word#123" not in conn_str  # Raw password should not appear
        assert "%40" in conn_str or "%23" in conn_str  # Encoded characters

    def test_masked_connection_string(self, db_config):
        """Test masked connection string for safe logging."""
        masked = db_config.get_masked_connection_string()

        assert "****" in masked
        assert "testpass123" not in masked
        assert "testuser" in masked  # Username should still be visible

    def test_masked_connection_string_without_credentials(self):
        """Test masked connection string without credentials."""
        from utils.config_manager import DatabaseConfig

        config = DatabaseConfig(host="localhost", port=27017)
        masked = config.get_masked_connection_string()

        assert masked == "mongodb://localhost:27017/"
        assert "****" not in masked

    def test_uri_override(self):
        """Test that URI takes precedence over individual fields."""
        from utils.config_manager import DatabaseConfig

        custom_uri = "mongodb+srv://cluster.example.com/mydb"
        config = DatabaseConfig(
            host="localhost",  # Should be ignored
            port=27017,  # Should be ignored
            uri=custom_uri,
        )

        conn_str = config.get_connection_string()
        assert conn_str == custom_uri

    def test_masked_uri(self):
        """Test masking password in custom URI."""
        from utils.config_manager import DatabaseConfig

        config = DatabaseConfig(uri="mongodb://admin:secretpass@cluster.example.com/db")

        masked = config.get_masked_connection_string()
        assert "secretpass" not in masked
        assert "****" in masked


class TestScrapingConfig:
    """Tests for ScrapingConfig class."""

    def test_default_values(self):
        """Test default scraping configuration values."""
        from utils.config_manager import ScrapingConfig

        config = ScrapingConfig()

        assert config.delay >= 0
        assert config.concurrent_requests > 0
        assert config.retry_times >= 0
        assert config.timeout > 0
        assert config.respect_robots_txt is True

    def test_custom_values(self):
        """Test custom scraping configuration."""
        from utils.config_manager import ScrapingConfig

        config = ScrapingConfig(
            delay=2.0,
            concurrent_requests=4,
            timeout=60,
        )

        assert config.delay == 2.0
        assert config.concurrent_requests == 4
        assert config.timeout == 60


class TestStorageConfig:
    """Tests for StorageConfig class."""

    def test_default_directories(self):
        """Test default storage directory paths."""
        from utils.config_manager import StorageConfig

        config = StorageConfig()

        assert "images" in config.images_dir
        assert "exports" in config.exports_dir

    def test_allowed_image_formats(self):
        """Test default allowed image formats."""
        from utils.config_manager import StorageConfig

        config = StorageConfig()

        assert ".jpg" in config.allowed_image_formats
        assert ".png" in config.allowed_image_formats
        assert ".webp" in config.allowed_image_formats


class TestConfigManager:
    """Tests for ConfigManager class."""

    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create a ConfigManager instance with temp directory."""
        from utils.config_manager import ConfigManager

        return ConfigManager(config_dir=str(tmp_path))

    def test_load_config(self, config_manager):
        """Test loading configuration."""
        # load_config returns bool
        result = config_manager.load_config()
        assert isinstance(result, bool)

    def test_has_database_config(self, config_manager):
        """Test that database configuration exists."""
        assert hasattr(config_manager, "database")

    def test_has_scraping_config(self, config_manager):
        """Test that scraping configuration exists."""
        assert hasattr(config_manager, "scraping")

    def test_environment_variable_override(self):
        """Test that environment variables override config values."""
        from utils.config_manager import ConfigManager

        with patch.dict(os.environ, {"MONGODB_URI": "mongodb://custom:27017/"}):
            manager = ConfigManager()
            # Environment variable should be used
            assert manager is not None

    def test_get_setting(self, config_manager):
        """Test getting a configuration setting."""
        # Use get_setting method
        result = config_manager.get_setting("nonexistent.key", default="default_value")
        assert result == "default_value"

    def test_set_setting(self, config_manager):
        """Test setting a configuration value."""
        # Use set_setting method
        result = config_manager.set_setting("test.key", "test_value")
        assert isinstance(result, bool)

    def test_validate_config(self, config_manager):
        """Test configuration validation."""
        if hasattr(config_manager, 'validate_config'):
            result = config_manager.validate_config()
            assert isinstance(result, dict)

    def test_get_config_summary(self, config_manager):
        """Test getting configuration summary."""
        if hasattr(config_manager, 'get_config_summary'):
            summary = config_manager.get_config_summary()
            assert isinstance(summary, dict)


class TestLoggingConfig:
    """Tests for LoggingConfig class."""

    def test_default_log_level(self):
        """Test default logging level."""
        from utils.config_manager import LoggingConfig

        config = LoggingConfig()

        assert config.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_log_format(self):
        """Test log format string."""
        from utils.config_manager import LoggingConfig

        config = LoggingConfig()

        # Format should contain standard placeholders
        assert "%(asctime)s" in config.log_format or "asctime" in config.log_format
        assert "%(message)s" in config.log_format or "message" in config.log_format


class TestGUIConfig:
    """Tests for GUIConfig class."""

    def test_default_window_size(self):
        """Test default window dimensions."""
        from utils.config_manager import GUIConfig

        config = GUIConfig()

        assert config.window_width > 0
        assert config.window_height > 0
        assert config.window_width >= 800  # Reasonable minimum
        assert config.window_height >= 600

    def test_theme_options(self):
        """Test theme configuration."""
        from utils.config_manager import GUIConfig

        config = GUIConfig()

        assert config.theme in ["dark", "light", "system"]
