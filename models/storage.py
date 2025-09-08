"""
Database storage layer for MongoDB operations.

This module provides the main database connection management and
initialization functionality for the Fandom Scraper application.
"""

import logging
from typing import Dict, Any, Optional, List
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.database import Database
from pymongo.collection import Collection
import os
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Central database management class for MongoDB operations.

    This class handles database connections, collection management,
    and provides high-level database operations for the application.

    Attributes:
        client: MongoDB client instance
        database: MongoDB database instance
        connection_string: MongoDB connection string
        database_name: Name of the database

    Example:
        >>> db_manager = DatabaseManager(
        ...     connection_string="mongodb://localhost:27017/",
        ...     database_name="fandom_scraper"
        ... )
        >>> db_manager.connect()
        >>> characters_collection = db_manager.get_collection("characters")
    """

    def __init__(self, connection_string: str, database_name: str):
        """
        Initialize database manager with connection parameters.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self._is_connected = False

    def connect(self) -> bool:
        """
        Establish connection to MongoDB database.

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        try:
            logger.info(f"Connecting to MongoDB at {self.connection_string}")

            # Create MongoDB client with connection options
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second connect timeout
                socketTimeoutMS=30000,  # 30 second socket timeout
                maxPoolSize=10,  # Maximum connection pool size
                retryWrites=True,  # Enable retryable writes
            )

            # Test connection
            self.client.admin.command("ping")

            # Get database instance
            self.database = self.client[self.database_name]

            # Initialize collections and indexes
            self._initialize_collections()

            self._is_connected = True
            logger.info(f"Successfully connected to database: {self.database_name}")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {e}")
            self._is_connected = False
            return False

    def disconnect(self):
        """Close database connection and cleanup resources."""
        if self.client:
            try:
                self.client.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.client = None
                self.database = None
                self._is_connected = False

    def is_connected(self) -> bool:
        """
        Check if database connection is active.

        Returns:
            True if connected, False otherwise
        """
        if not self._is_connected or not self.client:
            return False

        try:
            # Test connection with ping
            self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.warning(f"Database connection test failed: {e}")
            self._is_connected = False
            return False

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection instance.

        Args:
            collection_name: Name of the collection

        Returns:
            MongoDB collection instance

        Raises:
            RuntimeError: If not connected to database
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to database. Call connect() first.")

        return self.database[collection_name]  # type: ignore

    def _initialize_collections(self):
        """Initialize collections and create necessary indexes."""
        try:
            # Characters collection indexes
            characters_collection = self.database.characters  # type: ignore

            # Unique compound index for character identification
            characters_collection.create_index(
                [("name", ASCENDING), ("anime", ASCENDING)],
                unique=True,
                name="unique_character_anime",
            )

            # Text search index
            characters_collection.create_index(
                [("name", TEXT), ("description", TEXT), ("abilities", TEXT)],
                name="character_text_search",
            )

            # Performance indexes
            characters_collection.create_index("anime", name="anime_index")
            characters_collection.create_index("scraped_at", name="scraped_at_index")
            characters_collection.create_index(
                "data_quality_score", name="quality_score_index"
            )
            characters_collection.create_index("custom_tags", name="tags_index")

            # Anime collection indexes
            anime_collection = self.database.anime  # type: ignore

            # Unique index for anime titles
            anime_collection.create_index(
                "title", unique=True, name="unique_anime_title"
            )
            anime_collection.create_index(
                "fandom_url", unique=True, name="unique_fandom_url"
            )

            # Text search index for anime
            anime_collection.create_index(
                [
                    ("title", TEXT),
                    ("title_english", TEXT),
                    ("title_japanese", TEXT),
                    ("synopsis", TEXT),
                    ("genres", TEXT),
                ],
                name="anime_text_search",
            )

            # Performance indexes for anime
            anime_collection.create_index("status", name="status_index")
            anime_collection.create_index("genres", name="genres_index")
            anime_collection.create_index("studio", name="studio_index")
            anime_collection.create_index("release_date", name="release_date_index")

            # Episodes collection indexes (for future use)
            episodes_collection = self.database.episodes  # type: ignore
            episodes_collection.create_index(
                [("anime", ASCENDING), ("episode_number", ASCENDING)],
                unique=True,
                name="unique_anime_episode",
            )

            episodes_collection.create_index("anime", name="episode_anime_index")
            episodes_collection.create_index("air_date", name="episode_air_date_index")

            # Scraping operations collection (for tracking scraping jobs)
            operations_collection = self.database.scraping_operations  # type: ignore
            operations_collection.create_index(
                "operation_id", unique=True, name="unique_operation_id"
            )
            operations_collection.create_index("status", name="operation_status_index")
            operations_collection.create_index(
                "created_at", name="operation_created_index"
            )

            logger.info("Database collections and indexes initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database collections: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive database health check.

        Returns:
            Dictionary containing health status information
        """
        health_info = {
            "connected": False,
            "database_name": self.database_name,
            "collections": {},
            "indexes": {},
            "stats": {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            if not self.is_connected():
                health_info["error"] = "Not connected to database"
                return health_info

            health_info["connected"] = True

            # Get database statistics
            db_stats = self.database.command("dbstats")  # type: ignore
            health_info["stats"] = {
                "collections": db_stats.get("collections", 0),
                "objects": db_stats.get("objects", 0),
                "data_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0),
                "indexes": db_stats.get("indexes", 0),
            }

            # Check collections
            collection_names = [
                "characters",
                "anime",
                "episodes",
                "scraping_operations",
            ]
            for name in collection_names:
                collection = self.database[name]  # type: ignore
                try:
                    count = collection.count_documents({})
                    indexes = list(collection.list_indexes())

                    health_info["collections"][name] = {
                        "exists": True,
                        "document_count": count,
                        "index_count": len(indexes),
                    }
                    health_info["indexes"][name] = [idx["name"] for idx in indexes]

                except Exception as e:
                    health_info["collections"][name] = {
                        "exists": False,
                        "error": str(e),
                    }

            logger.info("Database health check completed successfully")

        except Exception as e:
            health_info["error"] = str(e)
            logger.error(f"Database health check failed: {e}")

        return health_info

    def drop_database(self, confirm_database_name: str) -> bool:
        """
        Drop the entire database (use with extreme caution).

        Args:
            confirm_database_name: Must match the actual database name as confirmation

        Returns:
            True if database was dropped, False otherwise
        """
        if confirm_database_name != self.database_name:
            logger.error("Database name confirmation failed")
            return False

        try:
            if self.is_connected():
                self.client.drop_database(self.database_name)  # type: ignore
                logger.warning(f"Database {self.database_name} has been dropped")
                return True
            else:
                logger.error("Cannot drop database: not connected")
                return False

        except Exception as e:
            logger.error(f"Failed to drop database: {e}")
            return False

    def backup_collection(self, collection_name: str, backup_path: str) -> bool:
        """
        Create a backup of a specific collection.

        Args:
            collection_name: Name of collection to backup
            backup_path: File path for backup

        Returns:
            True if backup successful, False otherwise
        """
        try:
            import json

            if not self.is_connected():
                logger.error("Cannot backup: not connected to database")
                return False

            collection = self.get_collection(collection_name)
            documents = list(collection.find({}))

            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                # Convert datetime objects to ISO format
                for key, value in doc.items():
                    if isinstance(value, datetime):
                        doc[key] = value.isoformat()

            # Write backup file
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(documents, f, indent=2, ensure_ascii=False)

            logger.info(f"Backup created: {collection_name} -> {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Backup failed for collection {collection_name}: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.

        Returns:
            Dictionary containing database statistics
        """
        stats = {
            "connected": self.is_connected(),
            "collections": {},
            "total_documents": 0,
            "total_size": 0,
        }

        if not self.is_connected():
            return stats

        try:
            # Get stats for each collection
            collection_names = [
                "characters",
                "anime",
                "episodes",
                "scraping_operations",
            ]

            for name in collection_names:
                collection = self.database[name]  # type: ignore
                count = collection.count_documents({})

                # Get collection stats
                try:
                    coll_stats = self.database.command("collstats", name)  # type: ignore
                    size = coll_stats.get("size", 0)
                except:
                    size = 0

                stats["collections"][name] = {
                    "document_count": count,
                    "size_bytes": size,
                }

                stats["total_documents"] += count
                stats["total_size"] += size

            # Add database-level statistics
            db_stats = self.database.command("dbstats")  # type: ignore
            stats["database_info"] = {
                "collections": db_stats.get("collections", 0),
                "indexes": db_stats.get("indexes", 0),
                "data_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0),
                "index_size": db_stats.get("indexSize", 0),
            }

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            stats["error"] = str(e)

        return stats


def create_database_manager(
    connection_string: str = None, database_name: str = None  # type: ignore
) -> DatabaseManager:
    """
    Factory function to create a DatabaseManager instance.

    Args:
        connection_string: MongoDB connection string (defaults to env var or localhost)
        database_name: Database name (defaults to env var or 'fandom_scraper')

    Returns:
        Configured DatabaseManager instance
    """
    # Use environment variables or defaults
    if not connection_string:
        connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

    if not database_name:
        database_name = os.getenv("MONGODB_DATABASE", "fandom_scraper")

    return DatabaseManager(connection_string, database_name)


# Global database manager instance (initialized when needed)
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get or create the global database manager instance.

    Returns:
        Global DatabaseManager instance
    """
    global _db_manager

    if _db_manager is None:
        _db_manager = create_database_manager()

        # Attempt to connect
        if not _db_manager.connect():
            logger.warning("Failed to connect to database during initialization")

    return _db_manager


def initialize_database() -> bool:
    """
    Initialize the database connection and setup collections.

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        db_manager = get_database_manager()

        if not db_manager.is_connected():
            return db_manager.connect()

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def close_database_connection():
    """Close the global database connection."""
    global _db_manager

    if _db_manager:
        _db_manager.disconnect()
        _db_manager = None
