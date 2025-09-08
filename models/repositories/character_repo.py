# models/repositories/character_repo.py
"""
Character repository for database operations.

This module provides high-level database operations for character data
using the Repository pattern to abstract database interactions.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError
from pymongo import ASCENDING, DESCENDING, TEXT
from bson import ObjectId
from bson.errors import InvalidId

from models.schemas.character_schema import CharacterSchema, CharacterSearchResult
from models.storage import get_database_manager

logger = logging.getLogger(__name__)


class CharacterRepository:
    """
    Repository class for character data persistence operations.

    This class handles all database interactions for character entities including
    CRUD operations, search functionality, batch operations, and data validation.

    Attributes:
        collection: MongoDB collection for characters

    Example:
        >>> repo = CharacterRepository()
        >>> character_data = {"name": "Luffy", "anime": "One Piece"}
        >>> character_id = repo.save_character(character_data)
        >>> character = repo.find_by_id(character_id)
    """

    def __init__(self, collection: Optional[Collection] = None):
        """
        Initialize repository with database collection.

        Args:
            collection: MongoDB collection instance (auto-created if None)
        """
        if collection:  # type: ignore
            self.collection = collection
        else:
            db_manager = get_database_manager()
            if not db_manager.is_connected():
                raise RuntimeError(
                    "Database not connected. Call initialize_database() first."
                )
            self.collection = db_manager.get_collection("characters")

    def save_character(self, character_data: Dict[str, Any]) -> Optional[str]:
        """
        Save character data with duplicate detection and validation.

        Args:
            character_data: Dictionary containing character information

        Returns:
            Character ID if successful, None if duplicate exists

        Raises:
            ValueError: If character data is invalid
            RuntimeError: If database operation fails
        """
        try:
            # Validate character data using Pydantic schema
            character = CharacterSchema(**character_data)

            # Calculate quality score if not provided
            if not character.data_quality_score:
                character.data_quality_score = character.calculate_quality_score()

            # Convert to MongoDB document format
            doc = character.to_mongodb_doc()

            # Attempt to insert new character
            result = self.collection.insert_one(doc)
            character_id = str(result.inserted_id)

            logger.info(
                f"Character saved successfully: {character.name} ({character_id})"
            )
            return character_id

        except DuplicateKeyError:
            # Handle duplicate character - update existing record
            logger.info(
                f"Duplicate character found: {character_data.get('name')} in {character_data.get('anime')}"
            )
            return self._handle_duplicate_character(character_data)

        except Exception as e:
            logger.error(f"Failed to save character: {e}")
            raise RuntimeError(f"Character save operation failed: {e}")

    def _handle_duplicate_character(
        self, character_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Handle duplicate character by updating existing record.

        Args:
            character_data: Character data dictionary

        Returns:
            Character ID of updated record
        """
        try:
            # Find existing character
            existing_character = self.collection.find_one(
                {"name": character_data["name"], "anime": character_data["anime"]}
            )

            if not existing_character:
                logger.warning("Duplicate key error but no existing character found")
                return None

            character_id = str(existing_character["_id"])

            # Validate new data
            character = CharacterSchema(**character_data)

            # Merge data intelligently
            merged_data = self._merge_character_data(
                existing_character, character.to_mongodb_doc()
            )

            # Update existing record
            self.collection.update_one(
                {"_id": existing_character["_id"]}, {"$set": merged_data}
            )

            logger.info(f"Character updated: {character.name} ({character_id})")
            return character_id

        except Exception as e:
            logger.error(f"Failed to handle duplicate character: {e}")
            return None

    def _merge_character_data(
        self, existing: Dict[str, Any], new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently merge character data, preserving the best information.

        Args:
            existing: Existing character data
            new: New character data

        Returns:
            Merged character data
        """
        merged = existing.copy()

        # Always update timestamp
        merged["updated_at"] = datetime.utcnow()

        # Merge simple fields (prefer non-empty values)
        simple_fields = ["description", "age", "gender", "occupation", "status"]
        for field in simple_fields:
            if new.get(field) and (
                not existing.get(field)
                or len(str(new[field])) > len(str(existing.get(field, "")))
            ):
                merged[field] = new[field]

        # Merge abilities (combine and deduplicate)
        existing_abilities = set(existing.get("abilities", []))
        new_abilities = set(new.get("abilities", []))
        merged["abilities"] = list(existing_abilities.union(new_abilities))

        # Merge relationships (combine dictionaries)
        existing_relationships = existing.get("relationships", {})
        new_relationships = new.get("relationships", {})
        merged["relationships"] = {**existing_relationships, **new_relationships}

        # Merge image URLs (combine and deduplicate)
        existing_images = set(existing.get("image_urls", []))
        new_images = set(new.get("image_urls", []))
        merged["image_urls"] = list(existing_images.union(new_images))

        # Merge custom tags
        existing_tags = set(existing.get("custom_tags", []))
        new_tags = set(new.get("custom_tags", []))
        merged["custom_tags"] = list(existing_tags.union(new_tags))

        # Update quality score based on merged data
        temp_character = CharacterSchema(**merged)
        merged["data_quality_score"] = temp_character.calculate_quality_score()

        return merged

    def find_by_id(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Find character by MongoDB ObjectId.

        Args:
            character_id: Character ObjectId as string

        Returns:
            Character data dictionary or None if not found
        """
        try:
            # Convert string to ObjectId
            object_id = ObjectId(character_id)

            # Find character document
            character_doc = self.collection.find_one({"_id": object_id})

            if character_doc:
                # Convert ObjectId to string for JSON serialization
                character_doc["_id"] = str(character_doc["_id"])
                return character_doc

            return None

        except InvalidId:
            logger.warning(f"Invalid character ID format: {character_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to find character by ID {character_id}: {e}")
            return None

    def find_by_name_and_anime(self, name: str, anime: str) -> Optional[Dict[str, Any]]:
        """
        Find character by name and anime series.

        Args:
            name: Character name
            anime: Anime series name

        Returns:
            Character data dictionary or None if not found
        """
        try:
            character_doc = self.collection.find_one({"name": name, "anime": anime})

            if character_doc:
                character_doc["_id"] = str(character_doc["_id"])
                return character_doc

            return None

        except Exception as e:
            logger.error(f"Failed to find character {name} from {anime}: {e}")
            return None

    def find_characters_by_anime(
        self, anime: str, page: int = 1, per_page: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Find all characters for a specific anime series with pagination.

        Args:
            anime: Anime series name
            page: Page number (1-based)
            per_page: Number of characters per page

        Returns:
            Tuple of (character list, total count)
        """
        try:
            # Calculate skip value for pagination
            skip = (page - 1) * per_page

            # Query with case-insensitive regex
            query = {"anime": {"$regex": f"^{anime}$", "$options": "i"}}

            # Get total count
            total_count = self.collection.count_documents(query)

            # Get paginated results
            cursor = (
                self.collection.find(query, {"_id": 0})
                .sort("name", ASCENDING)
                .skip(skip)
                .limit(per_page)
            )
            characters = list(cursor)

            return characters, total_count

        except Exception as e:
            logger.error(f"Failed to find characters for anime {anime}: {e}")
            return [], 0

    def search_characters(
        self, query: str, anime: Optional[str] = None, page: int = 1, per_page: int = 20
    ) -> Tuple[List[CharacterSearchResult], int]:
        """
        Perform full-text search across character data.

        Args:
            query: Search query string
            anime: Optional anime filter
            page: Page number (1-based)
            per_page: Number of results per page

        Returns:
            Tuple of (search results with scores, total count)
        """
        try:
            # Build search filter
            search_filter = {"$text": {"$search": query}}

            # Add anime filter if specified
            if anime:
                search_filter["anime"] = {"$regex": f"^{anime}$", "$options": "i"}

            # Calculate pagination
            skip = (page - 1) * per_page

            # Get total count
            total_count = self.collection.count_documents(search_filter)

            # Perform search with text score
            projection = {"score": {"$meta": "textScore"}, "_id": 0}

            cursor = (
                self.collection.find(search_filter, projection)
                .sort([("score", {"$meta": "textScore"})])
                .skip(skip)
                .limit(per_page)
            )

            # Convert to search results
            search_results = []
            for doc in cursor:
                score = doc.pop("score", 0.0)

                # Create search result with metadata
                search_result = CharacterSearchResult(
                    character=CharacterSchema(**doc),
                    relevance_score=min(score / 10.0, 1.0),  # Normalize score
                    matched_fields=self._identify_matched_fields(doc, query),
                    highlight_snippets=self._generate_highlights(doc, query),
                )
                search_results.append(search_result)

            return search_results, total_count

        except Exception as e:
            logger.error(f"Character search failed for query '{query}': {e}")
            return [], 0

    def _identify_matched_fields(
        self, character_doc: Dict[str, Any], query: str
    ) -> List[str]:
        """
        Identify which fields matched the search query.

        Args:
            character_doc: Character document
            query: Search query

        Returns:
            List of field names that matched
        """
        matched_fields = []
        query_lower = query.lower()

        # Check searchable fields
        searchable_fields = ["name", "description", "abilities", "occupation"]

        for field in searchable_fields:
            field_value = character_doc.get(field)
            if field_value:
                if isinstance(field_value, str) and query_lower in field_value.lower():
                    matched_fields.append(field)
                elif isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, str) and query_lower in item.lower():
                            matched_fields.append(field)
                            break

        return matched_fields

    def _generate_highlights(
        self, character_doc: Dict[str, Any], query: str
    ) -> Dict[str, str]:
        """
        Generate highlighted text snippets for search matches.

        Args:
            character_doc: Character document
            query: Search query

        Returns:
            Dictionary of field names to highlighted snippets
        """
        highlights = {}
        query_lower = query.lower()

        # Generate highlights for description
        description = character_doc.get("description", "")
        if description and query_lower in description.lower():
            # Find the query in description and create snippet
            start_pos = description.lower().find(query_lower)
            snippet_start = max(0, start_pos - 50)
            snippet_end = min(len(description), start_pos + len(query) + 50)
            snippet = description[snippet_start:snippet_end]

            # Add highlighting markup
            highlighted = snippet.replace(
                query, f"**{query}**", 1  # Replace only first occurrence in snippet
            )
            highlights["description"] = highlighted

        return highlights

    def update_character(self, character_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update existing character with new data.

        Args:
            character_id: Character ObjectId as string
            update_data: Dictionary containing fields to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Convert string to ObjectId
            object_id = ObjectId(character_id)

            # Add update timestamp
            update_data["updated_at"] = datetime.utcnow()

            # Validate update data by creating temporary character
            existing_character = self.find_by_id(character_id)
            if not existing_character:
                logger.warning(f"Character not found for update: {character_id}")
                return False

            # Merge update data with existing data for validation
            merged_data = {**existing_character, **update_data}
            try:
                CharacterSchema(**merged_data)  # Validate merged data
            except Exception as e:
                logger.error(f"Invalid update data for character {character_id}: {e}")
                return False

            # Perform update
            result = self.collection.update_one(
                {"_id": object_id}, {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Character updated successfully: {character_id}")
                return True
            else:
                logger.warning(f"No changes made to character: {character_id}")
                return False

        except InvalidId:
            logger.warning(f"Invalid character ID format: {character_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to update character {character_id}: {e}")
            return False

    def delete_character(self, character_id: str) -> bool:
        """
        Delete character by ID.

        Args:
            character_id: Character ObjectId as string

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Convert string to ObjectId
            object_id = ObjectId(character_id)

            # Perform deletion
            result = self.collection.delete_one({"_id": object_id})

            if result.deleted_count > 0:
                logger.info(f"Character deleted successfully: {character_id}")
                return True
            else:
                logger.warning(f"Character not found for deletion: {character_id}")
                return False

        except InvalidId:
            logger.warning(f"Invalid character ID format: {character_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete character {character_id}: {e}")
            return False

    def get_characters_by_quality_score(
        self,
        min_score: float,
        max_score: float = 1.0,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get characters filtered by quality score range.

        Args:
            min_score: Minimum quality score
            max_score: Maximum quality score
            page: Page number (1-based)
            per_page: Number of characters per page

        Returns:
            Tuple of (character list, total count)
        """
        try:
            # Build quality score filter
            query = {"data_quality_score": {"$gte": min_score, "$lte": max_score}}

            # Calculate pagination
            skip = (page - 1) * per_page

            # Get total count
            total_count = self.collection.count_documents(query)

            # Get results sorted by quality score (highest first)
            cursor = (
                self.collection.find(query, {"_id": 0})
                .sort("data_quality_score", DESCENDING)
                .skip(skip)
                .limit(per_page)
            )
            characters = list(cursor)

            return characters, total_count

        except Exception as e:
            logger.error(f"Failed to get characters by quality score: {e}")
            return [], 0

    def get_characters_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get characters filtered by custom tags.

        Args:
            tags: List of tags to search for
            match_all: If True, character must have all tags; if False, any tag
            page: Page number (1-based)
            per_page: Number of characters per page

        Returns:
            Tuple of (character list, total count)
        """
        try:
            # Build tag filter
            if match_all:
                # Character must have ALL specified tags
                query = {"custom_tags": {"$all": tags}}
            else:
                # Character must have ANY of the specified tags
                query = {"custom_tags": {"$in": tags}}

            # Calculate pagination
            skip = (page - 1) * per_page

            # Get total count
            total_count = self.collection.count_documents(query)

            # Get results
            cursor = (
                self.collection.find(query, {"_id": 0})
                .sort("name", ASCENDING)
                .skip(skip)
                .limit(per_page)
            )
            characters = list(cursor)

            return characters, total_count

        except Exception as e:
            logger.error(f"Failed to get characters by tags: {e}")
            return [], 0

    def get_character_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive character statistics.

        Returns:
            Dictionary containing various character statistics
        """
        try:
            stats = {}

            # Total character count
            stats["total_characters"] = self.collection.count_documents({})

            # Characters by anime (top 10)
            anime_pipeline = [
                {"$group": {"_id": "$anime", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            anime_stats = list(self.collection.aggregate(anime_pipeline))
            stats["top_anime_by_characters"] = [
                {"anime": item["_id"], "count": item["count"]} for item in anime_stats
            ]

            # Average quality score
            quality_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "avg_quality": {"$avg": "$data_quality_score"},
                    }
                }
            ]
            quality_result = list(self.collection.aggregate(quality_pipeline))
            stats["average_quality_score"] = (
                round(quality_result[0]["avg_quality"], 3) if quality_result else 0.0
            )

            # Quality score distribution
            quality_distribution = {}
            for threshold in [0.0, 0.2, 0.4, 0.6, 0.8]:
                count = self.collection.count_documents(
                    {"data_quality_score": {"$gte": threshold, "$lt": threshold + 0.2}}
                )
                quality_distribution[f"{threshold:.1f}-{threshold + 0.2:.1f}"] = count
            stats["quality_score_distribution"] = quality_distribution

            # Recently added characters (last 7 days)
            from datetime import timedelta

            week_ago = datetime.utcnow() - timedelta(days=7)
            stats["recent_characters"] = self.collection.count_documents(
                {"scraped_at": {"$gte": week_ago}}
            )

            # Most common abilities (top 10)
            abilities_pipeline = [
                {"$unwind": "$abilities"},
                {"$group": {"_id": "$abilities", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            abilities_stats = list(self.collection.aggregate(abilities_pipeline))
            stats["top_abilities"] = [
                {"ability": item["_id"], "count": item["count"]}
                for item in abilities_stats
            ]

            # Characters with images vs without
            with_images = self.collection.count_documents({"image_urls": {"$ne": []}})
            without_images = stats["total_characters"] - with_images
            stats["image_statistics"] = {
                "with_images": with_images,
                "without_images": without_images,
                "image_percentage": round(
                    (with_images / max(stats["total_characters"], 1)) * 100, 2
                ),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get character statistics: {e}")
            return {}

    def batch_update_quality_scores(self) -> int:
        """
        Recalculate and update quality scores for all characters.

        Returns:
            Number of characters updated
        """
        try:
            updated_count = 0

            # Process characters in batches to avoid memory issues
            batch_size = 100
            skip = 0

            while True:
                # Get batch of characters
                cursor = (
                    self.collection.find({}, {"_id": 1}).skip(skip).limit(batch_size)
                )
                character_ids = [doc["_id"] for doc in cursor]

                if not character_ids:
                    break  # No more characters

                # Update each character in the batch
                for character_id in character_ids:
                    character_doc = self.collection.find_one({"_id": character_id})
                    if character_doc:
                        try:
                            # Calculate new quality score
                            character = CharacterSchema(**character_doc)
                            new_score = character.calculate_quality_score()

                            # Update if score changed
                            if (
                                abs(
                                    character_doc.get("data_quality_score", 0)
                                    - new_score
                                )
                                > 0.001
                            ):
                                self.collection.update_one(
                                    {"_id": character_id},
                                    {
                                        "$set": {
                                            "data_quality_score": new_score,
                                            "updated_at": datetime.utcnow(),
                                        }
                                    },
                                )
                                updated_count += 1

                        except Exception as e:
                            logger.warning(
                                f"Failed to update quality score for character {character_id}: {e}"
                            )

                skip += batch_size

                # Log progress
                if updated_count % 100 == 0:
                    logger.info(
                        f"Updated quality scores for {updated_count} characters..."
                    )

            logger.info(
                f"Batch quality score update completed: {updated_count} characters updated"
            )
            return updated_count

        except Exception as e:
            logger.error(f"Batch quality score update failed: {e}")
            return 0

    def cleanup_duplicate_characters(self) -> int:
        """
        Find and remove duplicate characters (same name and anime).

        Returns:
            Number of duplicate characters removed
        """
        try:
            # Find duplicates using aggregation pipeline
            duplicate_pipeline = [
                {
                    "$group": {
                        "_id": {"name": "$name", "anime": "$anime"},
                        "ids": {"$push": "$_id"},
                        "count": {"$sum": 1},
                    }
                },
                {"$match": {"count": {"$gt": 1}}},
            ]

            duplicates = list(self.collection.aggregate(duplicate_pipeline))
            removed_count = 0

            for duplicate_group in duplicates:
                character_ids = duplicate_group["ids"]

                # Keep the first character (oldest) and remove others
                ids_to_remove = character_ids[1:]

                for character_id in ids_to_remove:
                    result = self.collection.delete_one({"_id": character_id})
                    if result.deleted_count > 0:
                        removed_count += 1

                logger.info(
                    f"Removed {len(ids_to_remove)} duplicates for character: {duplicate_group['_id']}"
                )

            logger.info(
                f"Duplicate cleanup completed: {removed_count} characters removed"
            )
            return removed_count

        except Exception as e:
            logger.error(f"Duplicate cleanup failed: {e}")
            return 0

    def export_characters_to_dict(
        self, anime: Optional[str] = None, quality_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Export characters to list of dictionaries for external use.

        Args:
            anime: Optional anime filter
            quality_threshold: Minimum quality score

        Returns:
            List of character dictionaries
        """
        try:
            # Build query
            query = {"data_quality_score": {"$gte": quality_threshold}}
            if anime:
                query["anime"] = {"$regex": f"^{anime}$", "$options": "i"}  # type: ignore

            # Get all matching characters
            cursor = (
                self.collection.find(query, {"_id": 0})
                .sort("anime", ASCENDING)
                .sort("name", ASCENDING)
            )
            characters = list(cursor)

            logger.info(f"Exported {len(characters)} characters")
            return characters

        except Exception as e:
            logger.error(f"Character export failed: {e}")
            return []
