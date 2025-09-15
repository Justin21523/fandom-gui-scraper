# utils/file_manager.py
"""
File management utilities for the scraper application.
Provides file operations, organization, and cleanup functionality.
"""

import os
import shutil
import hashlib
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta


class FileManager:
    """
    Comprehensive file manager for scraper operations.

    Features:
    - File organization and structure management
    - Duplicate file detection
    - Cleanup and archiving
    - Space management
    - File integrity verification
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize file manager.

        Args:
            config: Configuration dictionary with file management parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "base_path": "storage",
            "structure": {
                "images": "images",
                "documents": "documents",
                "exports": "exports",
                "backups": "backups",
                "temp": "temp",
                "logs": "logs",
            },
            "cleanup": {
                "auto_cleanup": True,
                "temp_file_retention_days": 7,
                "log_retention_days": 30,
                "backup_retention_days": 90,
            },
            "limits": {
                "max_storage_gb": 10,
                "max_file_size_mb": 100,
                "warn_threshold_percent": 80,
            },
        }

        if config:
            self.config.update(config)

        self.base_path = Path(self.config["base_path"])
        self._ensure_directory_structure()

    def organize_file(
        self, file_path: str, category: str, custom_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Organize file into appropriate directory structure.

        Args:
            file_path: Path to file to organize
            category: File category (images, documents, exports, etc.)
            custom_name: Optional custom filename

        Returns:
            Organization result with new file path
        """
        try:
            source_path = Path(file_path)

            if not source_path.exists():
                return {"success": False, "error": "Source file does not exist"}

            # Determine target directory
            if category not in self.config["structure"]:
                return {"success": False, "error": f"Unknown category: {category}"}

            target_dir = self.base_path / self.config["structure"][category]
            target_dir.mkdir(parents=True, exist_ok=True)

            # Generate target filename
            if custom_name:
                filename = custom_name
            else:
                # Use original filename with timestamp if needed
                base_name = source_path.stem
                extension = source_path.suffix
                filename = f"{base_name}{extension}"

                # Handle duplicate filenames
                counter = 1
                while (target_dir / filename).exists():
                    filename = f"{base_name}_{counter}{extension}"
                    counter += 1

            target_path = target_dir / filename

            # Copy or move file
            shutil.copy2(source_path, target_path)

            return {
                "success": True,
                "original_path": str(source_path),
                "new_path": str(target_path),
                "category": category,
                "filename": filename,
                "size_bytes": target_path.stat().st_size,
            }

        except Exception as e:
            self.logger.error(f"Failed to organize file {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def cleanup_old_files(self) -> Dict[str, Any]:
        """
        Clean up old temporary and log files based on retention policies.

        Returns:
            Cleanup result with statistics
        """
        if not self.config["cleanup"]["auto_cleanup"]:
            return {"success": True, "message": "Auto cleanup disabled"}

        cleanup_stats = {
            "temp_files_removed": 0,
            "log_files_removed": 0,
            "backup_files_removed": 0,
            "space_freed_mb": 0,
        }

        try:
            current_time = datetime.now()

            # Clean temp files
            temp_dir = self.base_path / self.config["structure"]["temp"]
            if temp_dir.exists():
                retention_days = self.config["cleanup"]["temp_file_retention_days"]
                cutoff_date = current_time - timedelta(days=retention_days)

                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            size_mb = file_path.stat().st_size / (1024 * 1024)
                            file_path.unlink()
                            cleanup_stats["temp_files_removed"] += 1
                            cleanup_stats["space_freed_mb"] += size_mb

            # Clean log files
            log_dir = self.base_path / self.config["structure"]["logs"]
            if log_dir.exists():
                retention_days = self.config["cleanup"]["log_retention_days"]
                cutoff_date = current_time - timedelta(days=retention_days)

                for file_path in log_dir.rglob("*.log"):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            size_mb = file_path.stat().st_size / (1024 * 1024)
                            file_path.unlink()
                            cleanup_stats["log_files_removed"] += 1
                            cleanup_stats["space_freed_mb"] += size_mb

            # Clean old backups
            backup_dir = self.base_path / self.config["structure"]["backups"]
            if backup_dir.exists():
                retention_days = self.config["cleanup"]["backup_retention_days"]
                cutoff_date = current_time - timedelta(days=retention_days)

                for file_path in backup_dir.rglob("*"):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            size_mb = file_path.stat().st_size / (1024 * 1024)
                            file_path.unlink()
                            cleanup_stats["backup_files_removed"] += 1
                            cleanup_stats["space_freed_mb"] += size_mb

            self.logger.info(
                f"Cleanup completed: freed {cleanup_stats['space_freed_mb']:.2f} MB"
            )

            return {"success": True, "statistics": cleanup_stats}

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return {"success": False, "error": str(e)}

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage usage information.

        Returns:
            Storage information and statistics
        """
        try:
            storage_info = {
                "base_path": str(self.base_path),
                "total_size_mb": 0,
                "categories": {},
            }

            # Calculate size for each category
            for category, subdir in self.config["structure"].items():
                category_path = self.base_path / subdir
                category_size = 0
                file_count = 0

                if category_path.exists():
                    for file_path in category_path.rglob("*"):
                        if file_path.is_file():
                            category_size += file_path.stat().st_size
                            file_count += 1

                category_size_mb = category_size / (1024 * 1024)
                storage_info["categories"][category] = {
                    "size_mb": category_size_mb,
                    "file_count": file_count,
                }
                storage_info["total_size_mb"] += category_size_mb

            # Check against limits
            max_storage_mb = self.config["limits"]["max_storage_gb"] * 1024
            usage_percent = (storage_info["total_size_mb"] / max_storage_mb) * 100
            warn_threshold = self.config["limits"]["warn_threshold_percent"]

            storage_info["usage_percent"] = usage_percent
            storage_info["needs_attention"] = usage_percent > warn_threshold
            storage_info["limit_mb"] = max_storage_mb

            return storage_info

        except Exception as e:
            self.logger.error(f"Failed to get storage info: {e}")
            return {"error": str(e)}

    def find_duplicate_files(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Find duplicate files based on content hash.

        Args:
            directory: Specific directory to scan (defaults to base path)

        Returns:
            Duplicate files information
        """
        try:
            scan_path = Path(directory) if directory else self.base_path

            if not scan_path.exists():
                return {"success": False, "error": "Scan directory does not exist"}

            file_hashes = {}
            duplicates = []

            self.logger.info(f"Scanning for duplicates in {scan_path}")

            for file_path in scan_path.rglob("*"):
                if file_path.is_file():
                    try:
                        file_hash = self._calculate_file_hash(file_path)

                        if file_hash in file_hashes:
                            # Found duplicate
                            original_file = file_hashes[file_hash]
                            duplicates.append(
                                {
                                    "original": str(original_file),
                                    "duplicate": str(file_path),
                                    "hash": file_hash,
                                    "size_bytes": file_path.stat().st_size,
                                }
                            )
                        else:
                            file_hashes[file_hash] = file_path

                    except Exception as e:
                        self.logger.warning(f"Failed to hash {file_path}: {e}")
                        continue

            total_duplicate_size = sum(dup["size_bytes"] for dup in duplicates)

            return {
                "success": True,
                "duplicates_found": len(duplicates),
                "duplicate_files": duplicates,
                "potential_space_savings_mb": total_duplicate_size / (1024 * 1024),
                "scan_path": str(scan_path),
            }

        except Exception as e:
            self.logger.error(f"Duplicate scan failed: {e}")
            return {"success": False, "error": str(e)}

    def remove_duplicate_files(
        self, duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Remove duplicate files, keeping the original.

        Args:
            duplicates: List of duplicate file information

        Returns:
            Removal result with statistics
        """
        try:
            removed_count = 0
            space_freed = 0
            errors = []

            for duplicate in duplicates:
                try:
                    duplicate_path = Path(duplicate["duplicate"])
                    if duplicate_path.exists():
                        space_freed += duplicate_path.stat().st_size
                        duplicate_path.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed duplicate: {duplicate_path}")
                except Exception as e:
                    error_msg = f"Failed to remove {duplicate['duplicate']}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            return {
                "success": True,
                "removed_count": removed_count,
                "space_freed_mb": space_freed / (1024 * 1024),
                "errors": errors,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_backup(
        self, source_path: str, backup_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create backup of files or directories.

        Args:
            source_path: Path to backup
            backup_name: Optional custom backup name

        Returns:
            Backup creation result
        """
        try:
            source = Path(source_path)
            if not source.exists():
                return {"success": False, "error": "Source path does not exist"}

            backup_dir = self.base_path / self.config["structure"]["backups"]
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate backup name
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{source.name}_backup_{timestamp}"

            backup_path = backup_dir / backup_name

            # Create backup
            if source.is_file():
                shutil.copy2(source, backup_path)
            else:
                shutil.copytree(source, backup_path)

            backup_size = self._get_directory_size(backup_path)

            return {
                "success": True,
                "source_path": str(source),
                "backup_path": str(backup_path),
                "backup_size_mb": backup_size / (1024 * 1024),
                "created_at": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return {"success": False, "error": str(e)}

    def _ensure_directory_structure(self):
        """Ensure all required directories exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)

            for category, subdir in self.config["structure"].items():
                dir_path = self.base_path / subdir
                dir_path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            self.logger.error(f"Failed to create directory structure: {e}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content."""
        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory."""
        total_size = 0

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size


def create_file_manager_config() -> Dict[str, Any]:
    """Create default configuration for file manager."""
    return {
        "base_path": "storage",
        "structure": {
            "images": "images",
            "documents": "documents",
            "exports": "exports",
            "backups": "backups",
            "temp": "temp",
            "logs": "logs",
        },
        "cleanup": {
            "auto_cleanup": True,
            "temp_file_retention_days": 7,
            "log_retention_days": 30,
            "backup_retention_days": 90,
        },
        "limits": {
            "max_storage_gb": 10,
            "max_file_size_mb": 100,
            "warn_threshold_percent": 80,
        },
    }
