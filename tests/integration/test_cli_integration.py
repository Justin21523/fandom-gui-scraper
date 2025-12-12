# tests/integration/test_cli_integration.py
"""
Integration tests for the CLI.

Tests CLI commands with mocked database connections.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from pathlib import Path

# Import the CLI app - this also loads the module
from cli.main import app as cli_app

# Get the actual module for patching
cli_module = sys.modules["cli.main"]


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def app():
    """Get CLI app."""
    return cli_app


class TestCLIBasicCommands:
    """Test basic CLI commands that don't require DB."""

    def test_help_command(self, runner, app):
        """Test --help displays help message."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "CLI tool for scraping" in result.stdout

    def test_version_command(self, runner, app):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Fandom Scraper CLI" in result.stdout
        assert "Version" in result.stdout

    def test_scrape_help(self, runner, app):
        """Test scrape --help."""
        result = runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        assert "Scrape character data" in result.stdout

    def test_export_help(self, runner, app):
        """Test export --help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export character data" in result.stdout

    def test_backup_help(self, runner, app):
        """Test backup --help."""
        result = runner.invoke(app, ["backup", "--help"])
        assert result.exit_code == 0
        assert "Create a backup" in result.stdout

    def test_restore_help(self, runner, app):
        """Test restore --help."""
        result = runner.invoke(app, ["restore", "--help"])
        assert result.exit_code == 0
        assert "Restore a backup" in result.stdout

    def test_list_backups_help(self, runner, app):
        """Test list-backups --help."""
        result = runner.invoke(app, ["list-backups", "--help"])
        assert result.exit_code == 0
        assert "List all available backups" in result.stdout


class TestCLIWithMockedDB:
    """Test CLI commands with mocked database."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database manager."""
        mock_manager = MagicMock()
        mock_manager.is_connected.return_value = True
        mock_manager.connect.return_value = True
        mock_manager.database_name = "test_db"

        mock_collection = MagicMock()
        mock_manager.get_collection.return_value = mock_collection

        return mock_manager, mock_collection

    def test_stats_command(self, runner, app, mock_db):
        """Test stats command."""
        mock_manager, mock_collection = mock_db

        mock_collection.count_documents.return_value = 100
        mock_collection.aggregate.return_value = [
            {"_id": "One Piece", "count": 50},
        ]

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0

    def test_list_characters_command(self, runner, app, mock_db):
        """Test list-characters command."""
        mock_manager, mock_collection = mock_db

        mock_collection.find.return_value.limit.return_value = [
            {
                "name": "Luffy",
                "anime_name": "One Piece",
                "status": "alive",
                "quality_score": 0.85,
            },
        ]

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(app, ["list-characters", "--limit", "10"])

        assert result.exit_code == 0

    def test_list_characters_empty(self, runner, app, mock_db):
        """Test list-characters when no characters found."""
        mock_manager, mock_collection = mock_db
        mock_collection.find.return_value.limit.return_value = []

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(app, ["list-characters"])

        assert result.exit_code == 0
        assert "No characters" in result.stdout

    def test_delete_cancelled(self, runner, app, mock_db):
        """Test delete command when user cancels."""
        mock_manager, mock_collection = mock_db
        mock_collection.find_one.return_value = {
            "_character_id": "char123",
            "name": "Test Character",
        }

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(app, ["delete", "char123"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.stdout

    def test_delete_with_force(self, runner, app, mock_db):
        """Test delete command with --force."""
        mock_manager, mock_collection = mock_db
        mock_collection.find_one.return_value = {
            "_character_id": "char123",
            "name": "Test Character",
        }
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(app, ["delete", "char123", "--force"])

        assert result.exit_code == 0
        assert "deleted" in result.stdout.lower()

    def test_delete_not_found(self, runner, app, mock_db):
        """Test delete command for non-existent character."""
        mock_manager, mock_collection = mock_db
        mock_collection.find_one.return_value = None

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(app, ["delete", "nonexistent", "--force"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


class TestCLIBackupCommands:
    """Test CLI backup commands."""

    def test_list_backups_empty(self, runner, app, tmp_path):
        """Test list-backups when no backups exist."""
        from utils.backup import BackupManager

        # Create a real manager with empty backup dir
        manager = BackupManager(backup_dir=str(tmp_path))

        with patch("utils.backup.BackupManager", return_value=manager):
            result = runner.invoke(app, ["list-backups"])

        assert result.exit_code == 0
        assert "No backups" in result.stdout

    def test_restore_file_not_found(self, runner, app):
        """Test restore command with non-existent file."""
        result = runner.invoke(
            app,
            ["restore", "/nonexistent/backup.json", "--force"],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_backup_command(self, runner, app, tmp_path):
        """Test backup command."""
        mock_manager = MagicMock()
        mock_manager.is_connected.return_value = True
        mock_manager.connect.return_value = True
        mock_manager.database_name = "test_db"

        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 2
        mock_collection.find.return_value = iter([
            {"_id": "1", "name": "Char 1"},
            {"_id": "2", "name": "Char 2"},
        ])
        mock_manager.get_collection.return_value = mock_collection

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(
                app,
                ["backup", "--output", str(tmp_path)],
            )

        assert result.exit_code == 0


class TestCLIExportCommands:
    """Test CLI export commands."""

    def test_export_empty_database(self, runner, app, tmp_path):
        """Test export command with empty database."""
        mock_manager = MagicMock()
        mock_manager.is_connected.return_value = True
        mock_manager.connect.return_value = True

        mock_collection = MagicMock()
        mock_collection.find.return_value = []
        mock_manager.get_collection.return_value = mock_collection

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(
                app,
                ["export", "--format", "csv"],
            )

        assert result.exit_code == 0
        assert "No characters" in result.stdout

    def test_export_csv(self, runner, app, tmp_path):
        """Test export command with CSV format."""
        mock_manager = MagicMock()
        mock_manager.is_connected.return_value = True
        mock_manager.connect.return_value = True

        mock_collection = MagicMock()
        mock_collection.find.return_value = [
            {
                "name": "Luffy",
                "anime_name": "One Piece",
                "description": "Captain",
                "status": "alive",
                "quality_score": 0.85,
                "source_url": "https://example.com",
            },
        ]
        mock_manager.get_collection.return_value = mock_collection

        output_file = tmp_path / "export.csv"

        with patch.object(cli_module, "get_db_manager", return_value=mock_manager):
            result = runner.invoke(
                app,
                ["export", "--format", "csv", "--output", str(output_file)],
            )

        assert result.exit_code == 0
        assert output_file.exists()
