# tests/unit/test_cli/test_cli.py
"""
Unit tests for CLI module.

Tests CLI command structure and argument validation.
"""

import pytest
from typer.testing import CliRunner


class TestCLIStructure:
    """Tests for CLI structure and commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def app(self):
        """Get CLI app."""
        from cli.main import app
        return app

    def test_app_exists(self, app):
        """Test that CLI app is created."""
        assert app is not None

    def test_help_command(self, runner, app):
        """Test --help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "CLI tool for scraping anime character data" in result.stdout

    def test_version_command(self, runner, app):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Fandom Scraper CLI" in result.stdout
        assert "Version" in result.stdout

    def test_scrape_help(self, runner, app):
        """Test scrape command help."""
        result = runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        assert "Scrape character data" in result.stdout
        assert "--limit" in result.stdout
        assert "--delay" in result.stdout

    def test_export_help(self, runner, app):
        """Test export command help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export character data" in result.stdout
        assert "--format" in result.stdout
        assert "--output" in result.stdout

    def test_stats_help(self, runner, app):
        """Test stats command help."""
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0
        assert "statistics" in result.stdout.lower()

    def test_list_characters_help(self, runner, app):
        """Test list-characters command help."""
        result = runner.invoke(app, ["list-characters", "--help"])
        assert result.exit_code == 0
        assert "--anime" in result.stdout
        assert "--limit" in result.stdout
        assert "--search" in result.stdout

    def test_delete_help(self, runner, app):
        """Test delete command help."""
        result = runner.invoke(app, ["delete", "--help"])
        assert result.exit_code == 0
        assert "character_id" in result.stdout.lower()
        assert "--force" in result.stdout


class TestExportFormat:
    """Tests for export format enum."""

    def test_export_format_values(self):
        """Test ExportFormat enum values."""
        from cli.main import ExportFormat

        assert ExportFormat.CSV == "csv"
        assert ExportFormat.JSON == "json"
        assert ExportFormat.EXCEL == "excel"


class TestAnimeType:
    """Tests for anime type enum."""

    def test_anime_type_values(self):
        """Test AnimeType enum values."""
        from cli.main import AnimeType

        assert AnimeType.ONEPIECE == "onepiece"
        assert AnimeType.NARUTO == "naruto"
        assert AnimeType.DRAGONBALL == "dragonball"
        assert AnimeType.CUSTOM == "custom"


class TestCLIValidation:
    """Tests for CLI argument validation."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def app(self):
        """Get CLI app."""
        from cli.main import app
        return app

    def test_scrape_requires_anime_type(self, runner, app):
        """Test that scrape requires anime type argument."""
        result = runner.invoke(app, ["scrape"])
        assert result.exit_code != 0

    def test_scrape_custom_requires_url(self, runner, app):
        """Test that custom scrape requires --url."""
        result = runner.invoke(app, ["scrape", "custom"])
        assert result.exit_code != 0
        assert "url" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_delete_requires_character_id(self, runner, app):
        """Test that delete requires character_id."""
        result = runner.invoke(app, ["delete"])
        assert result.exit_code != 0
