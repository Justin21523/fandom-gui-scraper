# utils/backup.py
"""
Data backup and restore utilities.

This module provides functionality for backing up and restoring
character data from MongoDB to various formats.
"""

import json
import gzip
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup file."""

    backup_id: str
    created_at: str
    database_name: str
    collection_name: str
    document_count: int
    backup_format: str
    compressed: bool
    file_size_bytes: int
    checksum: str
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(**data)


class BackupManager:
    """
    Manager for database backup and restore operations.

    Supports:
    - Full database backup
    - Collection-specific backup
    - Incremental backups
    - Compressed backups (gzip)
    - Multiple export formats (JSON, BSON)
    """

    def __init__(
        self,
        backup_dir: str = "backups",
        compress: bool = True,
        chunk_size: int = 1000,
    ):
        """
        Initialize BackupManager.

        Args:
            backup_dir: Directory to store backups
            compress: Whether to compress backups
            chunk_size: Number of documents to process at once
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.compress = compress
        self.chunk_size = chunk_size

        logger.info(f"BackupManager initialized with backup_dir: {self.backup_dir}")

    def create_backup(
        self,
        db_manager,
        collection_name: str = "characters",
        backup_name: Optional[str] = None,
        query_filter: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """
        Create a backup of the specified collection.

        Args:
            db_manager: Database manager instance
            collection_name: Name of collection to backup
            backup_name: Optional custom backup name
            query_filter: Optional filter to backup subset of data

        Returns:
            Path to backup file or None if failed
        """
        try:
            if not db_manager.is_connected():
                db_manager.connect()

            collection = db_manager.get_collection(collection_name)

            # Generate backup ID and filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{collection_name}_{timestamp}"

            if backup_name:
                backup_id = f"{backup_name}_{timestamp}"

            filename = f"{backup_id}.json"
            if self.compress:
                filename += ".gz"

            backup_path = self.backup_dir / filename
            metadata_path = self.backup_dir / f"{backup_id}_metadata.json"

            # Count documents
            filter_query = query_filter or {}
            total_docs = collection.count_documents(filter_query)

            logger.info(f"Starting backup of {total_docs} documents from {collection_name}")

            # Stream documents to file
            documents = []
            cursor = collection.find(filter_query)

            for doc in cursor:
                # Convert ObjectId to string
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                # Convert datetime objects
                doc = self._serialize_document(doc)
                documents.append(doc)

            # Calculate checksum
            json_data = json.dumps(documents, ensure_ascii=False, indent=2)
            checksum = hashlib.sha256(json_data.encode()).hexdigest()

            # Write backup file
            if self.compress:
                with gzip.open(backup_path, "wt", encoding="utf-8") as f:
                    f.write(json_data)
            else:
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(json_data)

            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                created_at=datetime.now().isoformat(),
                database_name=db_manager.database_name,
                collection_name=collection_name,
                document_count=total_docs,
                backup_format="json",
                compressed=self.compress,
                file_size_bytes=backup_path.stat().st_size,
                checksum=checksum,
            )

            # Save metadata
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, indent=2)

            logger.info(f"Backup completed: {backup_path} ({total_docs} documents)")
            return backup_path

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def restore_backup(
        self,
        db_manager,
        backup_path: str,
        collection_name: Optional[str] = None,
        drop_existing: bool = False,
        verify_checksum: bool = True,
    ) -> bool:
        """
        Restore a backup to the database.

        Args:
            db_manager: Database manager instance
            backup_path: Path to backup file
            collection_name: Target collection (uses original if not specified)
            drop_existing: Whether to drop existing collection
            verify_checksum: Whether to verify backup integrity

        Returns:
            True if restore successful, False otherwise
        """
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Load metadata
            metadata = self._load_metadata(backup_file)

            if collection_name is None and metadata:
                collection_name = metadata.collection_name
            elif collection_name is None:
                collection_name = "characters"

            logger.info(f"Restoring backup to collection: {collection_name}")

            # Read backup file
            if str(backup_file).endswith(".gz"):
                with gzip.open(backup_file, "rt", encoding="utf-8") as f:
                    json_data = f.read()
            else:
                with open(backup_file, "r", encoding="utf-8") as f:
                    json_data = f.read()

            # Verify checksum
            if verify_checksum and metadata:
                checksum = hashlib.sha256(json_data.encode()).hexdigest()
                if checksum != metadata.checksum:
                    logger.error("Checksum verification failed - backup may be corrupted")
                    return False
                logger.info("Checksum verified successfully")

            documents = json.loads(json_data)

            if not db_manager.is_connected():
                db_manager.connect()

            collection = db_manager.get_collection(collection_name)

            # Drop existing collection if requested
            if drop_existing:
                logger.warning(f"Dropping existing collection: {collection_name}")
                collection.drop()

            # Restore documents in chunks
            total_restored = 0
            for i in range(0, len(documents), self.chunk_size):
                chunk = documents[i : i + self.chunk_size]

                # Remove _id to let MongoDB generate new ones (avoid duplicates)
                for doc in chunk:
                    if "_id" in doc:
                        del doc["_id"]

                try:
                    result = collection.insert_many(chunk, ordered=False)
                    total_restored += len(result.inserted_ids)
                except Exception as e:
                    # Handle duplicate key errors for upsert behavior
                    if "duplicate key" in str(e).lower():
                        logger.warning(f"Some documents already exist, skipping duplicates")
                    else:
                        raise

            logger.info(f"Restore completed: {total_restored} documents restored")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.

        Returns:
            List of backup information dictionaries
        """
        backups = []

        for metadata_file in self.backup_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                # Find corresponding backup file
                backup_id = metadata.get("backup_id", "")
                backup_file = None

                for ext in [".json.gz", ".json"]:
                    candidate = self.backup_dir / f"{backup_id}{ext}"
                    if candidate.exists():
                        backup_file = candidate
                        break

                if backup_file:
                    metadata["file_path"] = str(backup_file)
                    metadata["exists"] = True
                else:
                    metadata["exists"] = False

                backups.append(metadata)

            except Exception as e:
                logger.warning(f"Error reading metadata {metadata_file}: {e}")

        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup and its metadata.

        Args:
            backup_id: Backup identifier

        Returns:
            True if deleted successfully
        """
        try:
            deleted = False

            # Delete backup files
            for pattern in [f"{backup_id}.json.gz", f"{backup_id}.json", f"{backup_id}_metadata.json"]:
                file_path = self.backup_dir / pattern
                if file_path.exists():
                    file_path.unlink()
                    deleted = True
                    logger.info(f"Deleted: {file_path}")

            return deleted

        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            return False

    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a backup.

        Args:
            backup_id: Backup identifier

        Returns:
            Backup information dictionary or None
        """
        metadata_path = self.backup_dir / f"{backup_id}_metadata.json"

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading backup info: {e}")
            return None

    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """
        Remove old backups, keeping only the most recent ones.

        Args:
            keep_count: Number of backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        deleted_count = 0

        if len(backups) <= keep_count:
            return 0

        # Delete oldest backups
        for backup in backups[keep_count:]:
            backup_id = backup.get("backup_id")
            if backup_id and self.delete_backup(backup_id):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count

    def _serialize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize document for JSON export.

        Args:
            doc: Document to serialize

        Returns:
            Serialized document
        """
        from datetime import datetime

        def serialize_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(v) for v in value]
            else:
                return value

        return {k: serialize_value(v) for k, v in doc.items()}

    def _load_metadata(self, backup_file: Path) -> Optional[BackupMetadata]:
        """
        Load metadata for a backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            BackupMetadata or None
        """
        # Derive metadata filename from backup filename
        if str(backup_file).endswith(".json.gz"):
            base_name = str(backup_file)[:-8]  # Remove .json.gz
        elif str(backup_file).endswith(".json"):
            base_name = str(backup_file)[:-5]  # Remove .json
        else:
            return None

        metadata_path = Path(f"{base_name}_metadata.json")

        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return BackupMetadata.from_dict(data)
            except Exception as e:
                logger.warning(f"Error loading metadata: {e}")

        return None


def create_quick_backup(db_manager, collection: str = "characters") -> Optional[str]:
    """
    Convenience function to create a quick backup.

    Args:
        db_manager: Database manager instance
        collection: Collection to backup

    Returns:
        Path to backup file or None
    """
    manager = BackupManager()
    result = manager.create_backup(db_manager, collection)
    return str(result) if result else None


def restore_latest_backup(db_manager, collection: str = "characters") -> bool:
    """
    Convenience function to restore the latest backup.

    Args:
        db_manager: Database manager instance
        collection: Target collection

    Returns:
        True if successful
    """
    manager = BackupManager()
    backups = manager.list_backups()

    if not backups:
        logger.warning("No backups found")
        return False

    latest = backups[0]
    backup_path = latest.get("file_path")

    if not backup_path:
        logger.error("Backup file path not found")
        return False

    return manager.restore_backup(db_manager, backup_path, collection)
