# tests/unit/test_utils/test_backup.py
"""
Unit tests for backup utilities.

Tests backup creation, restoration, and management.
"""

import pytest
import json
import gzip
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestBackupMetadata:
    """Tests for BackupMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating BackupMetadata instance."""
        from utils.backup import BackupMetadata

        metadata = BackupMetadata(
            backup_id="test_backup_123",
            created_at="2023-12-01T10:00:00",
            database_name="test_db",
            collection_name="characters",
            document_count=100,
            backup_format="json",
            compressed=True,
            file_size_bytes=1024,
            checksum="abc123",
        )

        assert metadata.backup_id == "test_backup_123"
        assert metadata.document_count == 100
        assert metadata.compressed is True

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        from utils.backup import BackupMetadata

        metadata = BackupMetadata(
            backup_id="test",
            created_at="2023-12-01T10:00:00",
            database_name="db",
            collection_name="col",
            document_count=10,
            backup_format="json",
            compressed=False,
            file_size_bytes=100,
            checksum="hash",
        )

        result = metadata.to_dict()

        assert isinstance(result, dict)
        assert result["backup_id"] == "test"
        assert result["document_count"] == 10

    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        from utils.backup import BackupMetadata

        data = {
            "backup_id": "test",
            "created_at": "2023-12-01T10:00:00",
            "database_name": "db",
            "collection_name": "col",
            "document_count": 50,
            "backup_format": "json",
            "compressed": True,
            "file_size_bytes": 2048,
            "checksum": "xyz789",
            "version": "1.0",
        }

        metadata = BackupMetadata.from_dict(data)

        assert metadata.backup_id == "test"
        assert metadata.document_count == 50
        assert metadata.compressed is True


class TestBackupManager:
    """Tests for BackupManager class."""

    @pytest.fixture
    def backup_manager(self, tmp_path):
        """Create a BackupManager with temp directory."""
        from utils.backup import BackupManager

        return BackupManager(backup_dir=str(tmp_path), compress=False)

    @pytest.fixture
    def backup_manager_compressed(self, tmp_path):
        """Create a BackupManager with compression enabled."""
        from utils.backup import BackupManager

        return BackupManager(backup_dir=str(tmp_path), compress=True)

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db = MagicMock()
        db.is_connected.return_value = True
        db.database_name = "test_db"

        # Mock collection
        collection = MagicMock()
        collection.count_documents.return_value = 3
        collection.find.return_value = iter([
            {"_id": "1", "name": "Character 1", "anime_name": "Test"},
            {"_id": "2", "name": "Character 2", "anime_name": "Test"},
            {"_id": "3", "name": "Character 3", "anime_name": "Test"},
        ])

        db.get_collection.return_value = collection
        return db

    def test_backup_manager_initialization(self, backup_manager, tmp_path):
        """Test BackupManager initialization."""
        assert backup_manager.backup_dir == tmp_path
        assert backup_manager.compress is False
        assert backup_manager.chunk_size == 1000

    def test_backup_dir_created(self, tmp_path):
        """Test that backup directory is created."""
        from utils.backup import BackupManager

        new_dir = tmp_path / "new_backups"
        manager = BackupManager(backup_dir=str(new_dir))

        assert new_dir.exists()

    def test_create_backup(self, backup_manager, mock_db_manager):
        """Test creating a backup."""
        result = backup_manager.create_backup(
            mock_db_manager,
            collection_name="characters",
        )

        assert result is not None
        assert result.exists()
        assert str(result).endswith(".json")

    def test_create_backup_with_custom_name(self, backup_manager, mock_db_manager):
        """Test creating a backup with custom name."""
        result = backup_manager.create_backup(
            mock_db_manager,
            collection_name="characters",
            backup_name="my_custom_backup",
        )

        assert result is not None
        assert "my_custom_backup" in str(result)

    def test_create_compressed_backup(self, backup_manager_compressed, mock_db_manager):
        """Test creating a compressed backup."""
        result = backup_manager_compressed.create_backup(
            mock_db_manager,
            collection_name="characters",
        )

        assert result is not None
        assert str(result).endswith(".json.gz")

    def test_list_backups_empty(self, backup_manager):
        """Test listing backups when none exist."""
        backups = backup_manager.list_backups()
        assert backups == []

    def test_list_backups(self, backup_manager, mock_db_manager):
        """Test listing backups after creating some."""
        # Create a backup
        backup_manager.create_backup(mock_db_manager, collection_name="characters")

        backups = backup_manager.list_backups()

        assert len(backups) == 1
        assert "backup_id" in backups[0]
        assert "document_count" in backups[0]

    def test_get_backup_info(self, backup_manager, mock_db_manager):
        """Test getting backup information."""
        # Create a backup
        backup_manager.create_backup(
            mock_db_manager,
            collection_name="characters",
            backup_name="info_test",
        )

        backups = backup_manager.list_backups()
        backup_id = backups[0]["backup_id"]

        info = backup_manager.get_backup_info(backup_id)

        assert info is not None
        assert info["backup_id"] == backup_id

    def test_get_backup_info_not_found(self, backup_manager):
        """Test getting info for non-existent backup."""
        info = backup_manager.get_backup_info("nonexistent_backup")
        assert info is None

    def test_delete_backup(self, backup_manager, mock_db_manager):
        """Test deleting a backup."""
        # Create a backup
        backup_manager.create_backup(
            mock_db_manager,
            collection_name="characters",
            backup_name="delete_test",
        )

        backups = backup_manager.list_backups()
        backup_id = backups[0]["backup_id"]

        # Delete the backup
        result = backup_manager.delete_backup(backup_id)

        assert result is True
        assert len(backup_manager.list_backups()) == 0

    def test_delete_backup_not_found(self, backup_manager):
        """Test deleting non-existent backup."""
        result = backup_manager.delete_backup("nonexistent_backup")
        assert result is False

    def test_cleanup_old_backups(self, backup_manager, mock_db_manager):
        """Test cleanup of old backups."""
        # Create multiple backups
        for i in range(5):
            backup_manager.create_backup(
                mock_db_manager,
                collection_name="characters",
                backup_name=f"backup_{i}",
            )

        # Cleanup, keeping only 2
        deleted = backup_manager.cleanup_old_backups(keep_count=2)

        assert deleted == 3
        assert len(backup_manager.list_backups()) == 2


class TestRestoreBackup:
    """Tests for backup restoration."""

    @pytest.fixture
    def backup_file(self, tmp_path):
        """Create a test backup file."""
        backup_data = [
            {"name": "Test Character 1", "anime_name": "Test Anime"},
            {"name": "Test Character 2", "anime_name": "Test Anime"},
        ]

        backup_path = tmp_path / "test_backup.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f)

        return backup_path

    @pytest.fixture
    def compressed_backup_file(self, tmp_path):
        """Create a compressed test backup file."""
        backup_data = [
            {"name": "Test Character 1", "anime_name": "Test Anime"},
        ]

        backup_path = tmp_path / "test_backup.json.gz"
        with gzip.open(backup_path, "wt", encoding="utf-8") as f:
            json.dump(backup_data, f)

        return backup_path

    def test_restore_backup_file_not_found(self, tmp_path):
        """Test restore with non-existent file."""
        from utils.backup import BackupManager

        manager = BackupManager(backup_dir=str(tmp_path))
        mock_db = MagicMock()

        result = manager.restore_backup(mock_db, "/nonexistent/backup.json")

        assert result is False

    def test_restore_backup_basic(self, tmp_path, backup_file):
        """Test basic backup restoration."""
        from utils.backup import BackupManager

        manager = BackupManager(backup_dir=str(tmp_path))

        # Mock database
        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_collection = MagicMock()
        mock_collection.insert_many.return_value = MagicMock(
            inserted_ids=["1", "2"]
        )
        mock_db.get_collection.return_value = mock_collection

        result = manager.restore_backup(
            mock_db,
            str(backup_file),
            collection_name="characters",
            verify_checksum=False,
        )

        assert result is True
        mock_collection.insert_many.assert_called_once()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_quick_backup_import(self):
        """Test that create_quick_backup can be imported."""
        from utils.backup import create_quick_backup
        assert create_quick_backup is not None

    def test_restore_latest_backup_import(self):
        """Test that restore_latest_backup can be imported."""
        from utils.backup import restore_latest_backup
        assert restore_latest_backup is not None
