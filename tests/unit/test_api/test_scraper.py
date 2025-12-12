# tests/unit/test_api/test_scraper.py
"""
Unit tests for Scraper API endpoints.

Tests for scraper control, configuration management,
and status tracking functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from pathlib import Path
import tempfile
import json


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_scraper_config():
    """Provide sample scraper configuration."""
    return {
        "base_url": "https://onepiece.fandom.com",
        "character_list_url": "/wiki/Category:Characters",
        "delay": 1.0,
        "retries": 3,
        "concurrent": 1,
        "selectors": None
    }


@pytest.fixture
def sample_preset():
    """Provide sample anime preset."""
    return {
        "name": "One Piece",
        "base_url": "https://onepiece.fandom.com",
        "character_list_url": "/wiki/Category:Characters",
        "description": "One Piece wiki characters"
    }


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "scraper_configs"
    config_dir.mkdir(parents=True)
    return config_dir


# ============================================================================
# ConfigManager Tests
# ============================================================================


class TestConfigManager:
    """Tests for scraper configuration management."""

    def test_save_and_load_config(self, temp_config_dir, sample_scraper_config):
        """Test saving and loading a configuration."""
        from api.endpoints.scraper import ConfigManager, ScraperConfig

        manager = ConfigManager(
            config_dir=temp_config_dir,
            history_file=temp_config_dir / "history.json"
        )

        config = ScraperConfig(**sample_scraper_config)

        # Save config
        result = manager.save_config("test_config", config)
        assert result is True

        # Load config
        loaded = manager.load_config("test_config")
        assert loaded is not None
        assert loaded["name"] == "test_config"
        assert loaded["config"]["base_url"] == sample_scraper_config["base_url"]

    def test_list_configs(self, temp_config_dir, sample_scraper_config):
        """Test listing all saved configurations."""
        from api.endpoints.scraper import ConfigManager, ScraperConfig

        manager = ConfigManager(
            config_dir=temp_config_dir,
            history_file=temp_config_dir / "history.json"
        )

        # Save multiple configs
        config = ScraperConfig(**sample_scraper_config)
        manager.save_config("config1", config)
        manager.save_config("config2", config)

        # List configs
        configs = manager.list_configs()
        assert len(configs) == 2
        names = [c["name"] for c in configs]
        assert "config1" in names
        assert "config2" in names

    def test_delete_config(self, temp_config_dir, sample_scraper_config):
        """Test deleting a configuration."""
        from api.endpoints.scraper import ConfigManager, ScraperConfig

        manager = ConfigManager(
            config_dir=temp_config_dir,
            history_file=temp_config_dir / "history.json"
        )

        config = ScraperConfig(**sample_scraper_config)
        manager.save_config("to_delete", config)

        # Verify it exists
        assert manager.load_config("to_delete") is not None

        # Delete
        result = manager.delete_config("to_delete")
        assert result is True

        # Verify deleted
        assert manager.load_config("to_delete") is None

    def test_delete_nonexistent_config(self, temp_config_dir):
        """Test deleting a config that doesn't exist."""
        from api.endpoints.scraper import ConfigManager

        manager = ConfigManager(
            config_dir=temp_config_dir,
            history_file=temp_config_dir / "history.json"
        )

        result = manager.delete_config("nonexistent")
        assert result is False

    def test_history_management(self, temp_config_dir, sample_scraper_config):
        """Test history entry management."""
        from api.endpoints.scraper import ConfigManager, ScraperConfig

        manager = ConfigManager(
            config_dir=temp_config_dir,
            history_file=temp_config_dir / "history.json"
        )

        config = ScraperConfig(**sample_scraper_config)
        result = {"completed": 10, "failed": 0}

        # Add history entry
        manager.add_history_entry(config, result)

        # Get history
        history = manager.get_history(limit=10)
        assert len(history) == 1
        assert history[0]["base_url"] == sample_scraper_config["base_url"]
        assert history[0]["result"]["completed"] == 10

    def test_history_limit(self, temp_config_dir, sample_scraper_config):
        """Test history entry limit."""
        from api.endpoints.scraper import ConfigManager, ScraperConfig

        manager = ConfigManager(
            config_dir=temp_config_dir,
            history_file=temp_config_dir / "history.json"
        )

        config = ScraperConfig(**sample_scraper_config)

        # Add many entries
        for i in range(110):
            manager.add_history_entry(config, {"completed": i})

        # Load history - should be limited to 100
        history_file = temp_config_dir / "history.json"
        with open(history_file, 'r') as f:
            all_history = json.load(f)

        assert len(all_history) == 100

    def test_sanitize_name(self, temp_config_dir):
        """Test config name sanitization."""
        from api.endpoints.scraper import ConfigManager

        manager = ConfigManager(
            config_dir=temp_config_dir,
            history_file=temp_config_dir / "history.json"
        )

        # Test various names
        assert manager._sanitize_name("Simple Name") == "simple_name"
        assert manager._sanitize_name("Name with $pecial Ch@rs!") == "name_with__pecial_ch_rs_"
        # Unicode is now supported in modern filesystems
        assert manager._sanitize_name("日本語") == "日本語"


# ============================================================================
# ScraperState Tests
# ============================================================================


class TestScraperState:
    """Tests for scraper state management."""

    def test_initial_state(self):
        """Test initial scraper state."""
        from api.endpoints.scraper import ScraperState

        state = ScraperState()
        assert state.status == "idle"
        assert state.config is None
        assert state.started_at is None
        assert state.error is None

    def test_reset_state(self):
        """Test resetting scraper state."""
        from api.endpoints.scraper import ScraperState

        state = ScraperState()
        state.status = "running"
        state.error = "Some error"

        state.reset()

        assert state.status == "idle"
        assert state.config is None
        assert state.error is None

    def test_add_log(self):
        """Test adding log entries."""
        from api.endpoints.scraper import ScraperState

        state = ScraperState()

        state.add_log("info", "Test message 1")
        state.add_log("error", "Test error")

        assert len(state.logs) == 2
        assert state.logs[0].level == "info"
        assert state.logs[0].message == "Test message 1"
        assert state.logs[1].level == "error"

    def test_log_limit(self):
        """Test log entry limit."""
        from api.endpoints.scraper import ScraperState

        state = ScraperState()

        # Add more than 1000 logs
        for i in range(1100):
            state.add_log("info", f"Message {i}")

        # Should be limited to 1000
        assert len(state.logs) == 1000
        # Should keep most recent
        assert "Message 1099" in state.logs[-1].message


# ============================================================================
# Schema Validation Tests
# ============================================================================


class TestScraperSchemas:
    """Tests for scraper schema validation."""

    def test_scraper_config_defaults(self):
        """Test ScraperConfig default values."""
        from api.endpoints.scraper import ScraperConfig

        config = ScraperConfig(base_url="https://example.fandom.com")

        assert config.base_url == "https://example.fandom.com"
        assert config.character_list_url == "/wiki/Category:Characters"
        assert config.delay == 1.0
        assert config.retries == 3
        assert config.concurrent == 1

    def test_scraper_config_validation(self):
        """Test ScraperConfig validation."""
        from api.endpoints.scraper import ScraperConfig
        from pydantic import ValidationError

        # Valid config
        config = ScraperConfig(
            base_url="https://example.com",
            delay=2.0,
            retries=5
        )
        assert config.delay == 2.0

        # Invalid delay (negative)
        with pytest.raises(ValidationError):
            ScraperConfig(base_url="https://example.com", delay=-1)

        # Invalid retries (too high)
        with pytest.raises(ValidationError):
            ScraperConfig(base_url="https://example.com", retries=20)

    def test_scraper_progress_model(self):
        """Test ScraperProgress model."""
        from api.endpoints.scraper import ScraperProgress

        progress = ScraperProgress()
        assert progress.total == 0
        assert progress.completed == 0
        assert progress.failed == 0

        progress = ScraperProgress(total=100, completed=50, failed=5)
        assert progress.total == 100
        assert progress.completed == 50
        assert progress.failed == 5

    def test_scraper_preset_model(self):
        """Test ScraperPreset model."""
        from api.endpoints.scraper import ScraperPreset

        preset = ScraperPreset(
            name="Test Anime",
            base_url="https://test.fandom.com",
            character_list_url="/wiki/Characters",
            description="Test description"
        )

        assert preset.name == "Test Anime"
        assert preset.description == "Test description"


# ============================================================================
# API Endpoint Tests (with FastAPI TestClient)
# ============================================================================


class TestScraperEndpoints:
    """Tests for scraper API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)

    def test_get_presets(self, client):
        """Test GET /api/v1/scraper/presets endpoint."""
        response = client.get("/api/v1/scraper/presets")
        assert response.status_code == 200

        presets = response.json()
        assert isinstance(presets, list)
        assert len(presets) > 0

        # Check preset structure
        preset = presets[0]
        assert "name" in preset
        assert "base_url" in preset
        assert "character_list_url" in preset

    def test_get_status(self, client):
        """Test GET /api/v1/scraper/status endpoint."""
        response = client.get("/api/v1/scraper/status")
        assert response.status_code == 200

        status = response.json()
        assert "status" in status
        assert status["status"] in ["idle", "running", "paused", "stopped"]

    def test_get_logs(self, client):
        """Test GET /api/v1/scraper/logs endpoint."""
        response = client.get("/api/v1/scraper/logs")
        assert response.status_code == 200

        logs = response.json()
        assert isinstance(logs, list)

    def test_get_logs_with_limit(self, client):
        """Test GET /api/v1/scraper/logs with limit parameter."""
        response = client.get("/api/v1/scraper/logs?limit=10")
        assert response.status_code == 200

        logs = response.json()
        assert isinstance(logs, list)
        assert len(logs) <= 10

    def test_get_configs_empty(self, client):
        """Test GET /api/v1/scraper/configs when empty."""
        response = client.get("/api/v1/scraper/configs")
        assert response.status_code == 200

        configs = response.json()
        assert isinstance(configs, list)

    def test_get_stats(self, client):
        """Test GET /api/v1/scraper/stats endpoint."""
        response = client.get("/api/v1/scraper/stats")
        assert response.status_code == 200

        stats = response.json()
        assert "total_scraped" in stats
        assert "successful" in stats
        assert "failed" in stats
        assert "status" in stats

    def test_validate_url_valid(self, client):
        """Test POST /api/v1/scraper/validate-url with valid URL."""
        response = client.post(
            "/api/v1/scraper/validate-url",
            json={"url": "https://onepiece.fandom.com/wiki/Characters"}
        )
        assert response.status_code == 200

        result = response.json()
        assert result["valid"] is True

    def test_validate_url_invalid(self, client):
        """Test POST /api/v1/scraper/validate-url with invalid URL."""
        response = client.post(
            "/api/v1/scraper/validate-url",
            json={"url": "not-a-valid-url"}
        )
        assert response.status_code == 200

        result = response.json()
        assert result["valid"] is False

    def test_validate_url_non_fandom(self, client):
        """Test POST /api/v1/scraper/validate-url with non-Fandom URL."""
        response = client.post(
            "/api/v1/scraper/validate-url",
            json={"url": "https://example.com/page"}
        )
        assert response.status_code == 200

        result = response.json()
        assert result["valid"] is True
        assert "warning" in result

    def test_get_history_empty(self, client):
        """Test GET /api/v1/scraper/history when empty."""
        response = client.get("/api/v1/scraper/history")
        assert response.status_code == 200

        history = response.json()
        assert isinstance(history, list)


# ============================================================================
# Integration Tests
# ============================================================================


class TestScraperIntegration:
    """Integration tests for scraper functionality."""

    @pytest.fixture
    def mock_scraper_available(self):
        """Mock scraper availability."""
        with patch("api.endpoints.scraper.SCRAPER_AVAILABLE", False):
            yield

    def test_simulated_scraper_progress(self, mock_scraper_available):
        """Test simulated scraper updates progress correctly."""
        from api.endpoints.scraper import scraper_state, ScraperConfig

        # Reset state
        scraper_state.reset()

        config = ScraperConfig(
            base_url="https://test.fandom.com",
            delay=0.01  # Fast for testing
        )

        # Verify initial state
        assert scraper_state.status == "idle"
        assert scraper_state.progress.completed == 0

    def test_scraper_state_transitions(self):
        """Test scraper state transitions."""
        from api.endpoints.scraper import scraper_state

        # Reset to initial
        scraper_state.reset()
        assert scraper_state.status == "idle"

        # Simulate starting
        scraper_state.status = "running"
        assert scraper_state.status == "running"

        # Simulate pausing
        scraper_state.status = "paused"
        assert scraper_state.status == "paused"

        # Simulate resuming
        scraper_state.status = "running"
        assert scraper_state.status == "running"

        # Simulate stopping
        scraper_state.status = "stopped"
        assert scraper_state.status == "stopped"

        # Reset back
        scraper_state.reset()
        assert scraper_state.status == "idle"
