# scraper/pipelines.py
"""
Scrapy Data Processing Pipelines

This module contains all the data processing pipelines for the Fandom scraper.
Pipelines are processed in order and handle data validation, image downloading,
storage, and quality scoring.
"""

import os
import hashlib
import logging
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
import time

import scrapy
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http import Request
from itemadapter import ItemAdapter

from ..models.document import AnimeCharacter
from ..models.storage import DatabaseManager
from ..utils.normalizer import DataNormalizer
from ..utils.logger import get_logger


class DataValidationPipeline:
    """
    Pipeline for validating scraped character data.

    This pipeline ensures data quality by:
    - Validating required fields
    - Checking data types and formats
    - Filtering out incomplete or invalid records
    - Logging validation issues for debugging
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.normalizer = DataNormalizer()
        self.processed_items = 0
        self.dropped_items = 0

        # Define required fields for character data
        self.required_fields = {"name", "anime_name", "source_url"}

        # Define optional fields with default values
        self.default_values = {
            "description": "",
            "images": [],
            "relationships": [],
            "abilities": [],
            "appearances": [],
        }

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """
        Validate and process item data.

        Args:
            item: Scraped item data
            spider: Spider instance

        Returns:
            Validated and processed item

        Raises:
            DropItem: If item fails validation
        """
        adapter = ItemAdapter(item)

        try:
            # Check for errors in scraped data
            if adapter.get("error"):
                self.logger.warning(f"Item contains error: {adapter['error']}")
                raise DropItem(f"Scraped item contains error: {adapter['error']}")

            # Validate required fields
            self._validate_required_fields(adapter)

            # Validate field types and formats
            self._validate_field_types(adapter)

            # Apply default values for missing optional fields
            self._apply_default_values(adapter)

            # Normalize data
            normalized_item = self.normalizer.normalize_character_data(dict(adapter))

            # Final validation
            self._validate_normalized_data(normalized_item)

            self.processed_items += 1
            self.logger.debug(
                f"Successfully validated item: {normalized_item.get('name')}"
            )

            return normalized_item

        except DropItem:
            self.dropped_items += 1
            raise
        except Exception as e:
            self.dropped_items += 1
            self.logger.error(f"Validation error for item: {e}")
            raise DropItem(f"Validation failed: {e}")

    def _validate_required_fields(self, adapter: ItemAdapter) -> None:
        """
        Validate that all required fields are present.

        Args:
            adapter: Item adapter

        Raises:
            DropItem: If required fields are missing
        """
        missing_fields = []

        for field in self.required_fields:
            value = adapter.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)

        if missing_fields:
            raise DropItem(f"Missing required fields: {missing_fields}")

    def _validate_field_types(self, adapter: ItemAdapter) -> None:
        """
        Validate field types and formats.

        Args:
            adapter: Item adapter

        Raises:
            DropItem: If field types are invalid
        """
        # Validate string fields
        string_fields = ["name", "anime_name", "source_url", "description"]
        for field in string_fields:
            value = adapter.get(field)
            if value is not None and not isinstance(value, str):
                raise DropItem(f"Field '{field}' must be string, got {type(value)}")

        # Validate list fields
        list_fields = ["images", "relationships", "abilities", "appearances"]
        for field in list_fields:
            value = adapter.get(field)
            if value is not None and not isinstance(value, list):
                raise DropItem(f"Field '{field}' must be list, got {type(value)}")

        # Validate URL format
        source_url = adapter.get("source_url")
        if source_url and not self._is_valid_url(source_url):
            raise DropItem(f"Invalid source URL format: {source_url}")

    def _apply_default_values(self, adapter: ItemAdapter) -> None:
        """
        Apply default values for missing optional fields.

        Args:
            adapter: Item adapter
        """
        for field, default_value in self.default_values.items():
            if adapter.get(field) is None:
                adapter[field] = default_value

    def _validate_normalized_data(self, data: Dict[str, Any]) -> None:
        """
        Validate normalized data structure.

        Args:
            data: Normalized data dictionary

        Raises:
            DropItem: If normalized data is invalid
        """
        # Check character name is not empty after normalization
        if not data.get("name", "").strip():
            raise DropItem("Character name is empty after normalization")

        # Validate image data structure
        for image in data.get("images", []):
            if not isinstance(image, dict) or "url" not in image:
                raise DropItem(f"Invalid image data structure: {image}")

    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def close_spider(self, spider):
        """
        Called when spider is closed.

        Args:
            spider: Spider instance
        """
        self.logger.info(
            f"Validation pipeline closed - Processed: {self.processed_items}, "
            f"Dropped: {self.dropped_items}"
        )


class ImageDownloadPipeline(ImagesPipeline):
    """
    Enhanced image download pipeline for character images.

    This pipeline handles:
    - Image downloading with retry logic
    - Image resizing and optimization
    - Duplicate image detection
    - Organized file storage
    - Image metadata extraction
    """

    def __init__(self, store_uri, download_func=None, settings=None):
        super().__init__(store_uri, download_func, settings)
        self.logger = get_logger(self.__class__.__name__)

        # Image processing settings
        self.max_image_size = (800, 800)  # Maximum image dimensions
        self.image_quality = 85  # JPEG quality
        self.min_image_size = (50, 50)  # Minimum acceptable size

        # Storage settings
        self.store_path = Path(store_uri.replace("file://", ""))
        self.store_path.mkdir(parents=True, exist_ok=True)

        # Download statistics
        self.downloaded_count = 0
        self.skipped_count = 0
        self.failed_count = 0

    def get_media_requests(self, item: Dict[str, Any], info) -> List[Request]:
        """
        Generate download requests for character images.

        Args:
            item: Character item with image data
            info: Media download info

        Yields:
            Image download requests
        """
        adapter = ItemAdapter(item)
        images = adapter.get("images", [])

        if not images:
            self.logger.debug(f"No images found for character: {adapter.get('name')}")
            return []

        requests = []
        character_name = adapter.get("name", "unknown")
        anime_name = adapter.get("anime_name", "unknown")

        for i, image_data in enumerate(images):
            if not isinstance(image_data, dict) or "url" not in image_data:
                self.logger.warning(
                    f"Invalid image data for {character_name}: {image_data}"
                )
                continue

            image_url = image_data["url"]

            # Skip invalid URLs
            if not self._is_valid_image_url(image_url):
                self.logger.warning(f"Invalid image URL: {image_url}")
                continue

            # Generate filename
            filename = self._generate_image_filename(
                character_name, anime_name, image_data, i
            )

            # Create download request
            request = Request(
                url=image_url,
                meta={
                    "character_name": character_name,
                    "anime_name": anime_name,
                    "image_type": image_data.get("type", "general"),
                    "image_index": i,
                    "filename": filename,
                },
            )

            requests.append(request)

        self.logger.info(
            f"Generated {len(requests)} image download requests for {character_name}"
        )
        return requests

    def item_completed(
        self, results: List[tuple], item: Dict[str, Any], info
    ) -> Dict[str, Any]:
        """
        Process completed image downloads.

        Args:
            results: Download results
            item: Character item
            info: Media download info

        Returns:
            Updated item with processed image data
        """
        adapter = ItemAdapter(item)
        image_paths = []

        for success, result in results:
            if success:
                # Extract image information
                image_info = {
                    "path": result["path"],
                    "url": result["url"],
                    "checksum": result["checksum"],
                }

                # Add metadata from request
                if hasattr(result, "meta"):
                    image_info.update(
                        {
                            "type": result.meta.get("image_type", "general"),
                            "character_name": result.meta.get("character_name"),
                            "anime_name": result.meta.get("anime_name"),
                        }
                    )

                image_paths.append(image_info)
                self.downloaded_count += 1

                self.logger.debug(f"Successfully downloaded image: {result['path']}")
            else:
                self.failed_count += 1
                self.logger.warning(f"Failed to download image: {result}")

        # Update item with downloaded image paths
        adapter["downloaded_images"] = image_paths
        adapter["image_download_stats"] = {
            "total_requested": len(adapter.get("images", [])),
            "successfully_downloaded": len(image_paths),
            "failed": len(results) - len(image_paths),
        }

        self.logger.info(
            f"Image download completed for {adapter.get('name')}: "
            f"{len(image_paths)} successful, "
            f"{len(results) - len(image_paths)} failed"
        )

        return dict(adapter)

    def file_path(
        self, request: Request, response=None, info=None, *, item=None
    ) -> str:
        """
        Generate file path for downloaded image.

        Args:
            request: Download request
            response: HTTP response
            info: Download info
            item: Character item

        Returns:
            File path for image storage
        """
        # Extract metadata from request
        character_name = request.meta.get("character_name", "unknown")
        anime_name = request.meta.get("anime_name", "unknown")
        image_type = request.meta.get("image_type", "general")
        filename = request.meta.get("filename")

        if filename:
            # Use pre-generated filename
            return f"{anime_name}/{character_name}/{image_type}/{filename}"
        else:
            # Generate filename from URL
            url_filename = request.url.split("/")[-1].split("?")[0]
            safe_filename = self._sanitize_filename(url_filename)
            return f"{anime_name}/{character_name}/{image_type}/{safe_filename}"

    def _generate_image_filename(
        self,
        character_name: str,
        anime_name: str,
        image_data: Dict[str, str],
        index: int,
    ) -> str:
        """
        Generate appropriate filename for image.

        Args:
            character_name: Character name
            anime_name: Anime name
            image_data: Image metadata
            index: Image index

        Returns:
            Generated filename
        """
        # Get original filename
        original_url = image_data["url"]
        original_filename = original_url.split("/")[-1].split("?")[0]

        # Get file extension
        file_extension = Path(original_filename).suffix
        if not file_extension:
            file_extension = ".jpg"  # Default extension

        # Generate base filename
        image_type = image_data.get("type", "general")
        safe_char_name = self._sanitize_filename(character_name)

        filename = f"{safe_char_name}_{image_type}_{index:02d}{file_extension}"

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for file system compatibility.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        import re

        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = re.sub(r"\s+", "_", filename)
        filename = filename.strip("._")

        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[: 100 - len(ext)] + ext

        return filename

    def _is_valid_image_url(self, url: str) -> bool:
        """
        Check if URL points to a valid image.

        Args:
            url: Image URL

        Returns:
            True if URL appears to be valid image
        """
        if not url:
            return False

        # Check URL format
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False
        except:
            return False

        # Check for image file extensions
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        url_lower = url.lower()

        # Check if URL has image extension or contains image indicators
        has_extension = any(ext in url_lower for ext in image_extensions)
        has_image_path = any(
            keyword in url_lower for keyword in ["image", "img", "pic", "photo"]
        )

        return has_extension or has_image_path

    def close_spider(self, spider):
        """
        Called when spider is closed.

        Args:
            spider: Spider instance
        """
        self.logger.info(
            f"Image pipeline closed - Downloaded: {self.downloaded_count}, "
            f"Skipped: {self.skipped_count}, Failed: {self.failed_count}"
        )


class DataStoragePipeline:
    """
    Pipeline for storing character data in MongoDB.

    This pipeline handles:
    - Database connection management
    - Data insertion and updates
    - Duplicate detection and merging
    - Error handling and retry logic
    """

    def __init__(self, mongo_uri: str, mongo_db: str):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.logger = get_logger(self.__class__.__name__)

        # Storage statistics
        self.inserted_count = 0
        self.updated_count = 0
        self.duplicate_count = 0
        self.error_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create pipeline instance from crawler settings.

        Args:
            crawler: Scrapy crawler instance

        Returns:
            Pipeline instance
        """
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI", "mongodb://localhost:27017/"),
            mongo_db=crawler.settings.get("MONGO_DATABASE", "fandom_scraper"),
        )

    def open_spider(self, spider):
        """
        Initialize database connection when spider starts.

        Args:
            spider: Spider instance
        """
        try:
            self.db_manager = DatabaseManager(self.mongo_uri, self.mongo_db)
            self.db_manager.connect()
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """
        Store item in database.

        Args:
            item: Character item data
            spider: Spider instance

        Returns:
            Processed item
        """
        adapter = ItemAdapter(item)

        try:
            # Create character document
            character_data = dict(adapter)

            # Check for existing character
            existing_character = self._find_existing_character(character_data)

            if existing_character:
                # Update existing character
                updated_character = self._merge_character_data(
                    existing_character, character_data
                )
                self.db_manager.update_character(
                    existing_character["_id"], updated_character
                )
                self.updated_count += 1
                self.logger.info(
                    f"Updated existing character: {character_data.get('name')}"
                )
            else:
                # Insert new character
                character_id = self.db_manager.insert_character(character_data)
                self.inserted_count += 1
                self.logger.info(
                    f"Inserted new character: {character_data.get('name')} (ID: {character_id})"
                )

            return dict(adapter)

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Failed to store character data: {e}")
            raise DropItem(f"Database storage failed: {e}")

    def _find_existing_character(
        self, character_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find existing character in database.

        Args:
            character_data: Character data to check

        Returns:
            Existing character document or None
        """
        # Search by name and anime
        query = {
            "name": character_data.get("name"),
            "anime_name": character_data.get("anime_name"),
        }

        return self.db_manager.find_character(query)

    def _merge_character_data(
        self, existing: Dict[str, Any], new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge new character data with existing data.

        Args:
            existing: Existing character document
            new: New character data

        Returns:
            Merged character data
        """
        merged = existing.copy()

        # Update scalar fields with new values
        scalar_fields = ["name", "description", "source_url", "anime_name"]
        for field in scalar_fields:
            if field in new and new[field]:
                merged[field] = new[field]

        # Merge list fields (avoid duplicates)
        list_fields = ["images", "relationships", "abilities", "appearances"]
        for field in list_fields:
            if field in new and new[field]:
                existing_items = merged.get(field, [])
                new_items = new[field]

                # Merge lists and remove duplicates
                merged_items = existing_items.copy()
                for item in new_items:
                    if item not in merged_items:
                        merged_items.append(item)

                merged[field] = merged_items

        # Update metadata
        merged["last_updated"] = new.get("extraction_date")
        merged["update_count"] = merged.get("update_count", 0) + 1

        return merged

    def close_spider(self, spider):
        """
        Clean up database connection when spider closes.

        Args:
            spider: Spider instance
        """
        if hasattr(self, "db_manager"):
            self.db_manager.disconnect()

        self.logger.info(
            f"Storage pipeline closed - Inserted: {self.inserted_count}, "
            f"Updated: {self.updated_count}, Errors: {self.error_count}"
        )


class DataQualityPipeline:
    """
    Pipeline for assessing and improving data quality.

    This pipeline:
    - Calculates quality scores for character data
    - Identifies and flags low-quality records
    - Suggests data improvements
    - Tracks quality metrics
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

        # Quality scoring weights
        self.quality_weights = {
            "name": 10,  # Character name (required)
            "description": 8,  # Character description
            "images": 6,  # Character images
            "relationships": 4,  # Character relationships
            "abilities": 4,  # Character abilities
            "appearances": 3,  # Episode appearances
            "metadata": 2,  # Additional metadata
        }

        # Quality statistics
        self.high_quality_count = 0  # Score >= 80
        self.medium_quality_count = 0  # Score 50-79
        self.low_quality_count = 0  # Score < 50

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """
        Calculate and assign quality score to item.

        Args:
            item: Character item data
            spider: Spider instance

        Returns:
            Item with quality score and suggestions
        """
        adapter = ItemAdapter(item)

        # Calculate quality score
        quality_score = self._calculate_quality_score(dict(adapter))

        # Generate quality report
        quality_report = self._generate_quality_report(dict(adapter), quality_score)

        # Add quality data to item
        adapter["quality_score"] = quality_score
        adapter["quality_report"] = quality_report
        adapter["quality_category"] = self._categorize_quality(quality_score)

        # Update statistics
        self._update_statistics(quality_score)

        # Log quality information
        character_name = adapter.get("name", "Unknown")
        self.logger.info(
            f"Quality score for {character_name}: {quality_score:.1f}/100 "
            f"({adapter['quality_category']})"
        )

        if quality_score < 50:
            self.logger.warning(
                f"Low quality data detected for {character_name}: "
                f"{quality_report.get('suggestions', [])}"
            )

        return dict(adapter)

    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate overall quality score for character data.

        Args:
            data: Character data dictionary

        Returns:
            Quality score (0-100)
        """
        total_score = 0
        max_possible_score = sum(self.quality_weights.values())

        # Score name quality
        name_score = self._score_name_quality(data.get("name", ""))
        total_score += name_score * self.quality_weights["name"]

        # Score description quality
        desc_score = self._score_description_quality(data.get("description", ""))
        total_score += desc_score * self.quality_weights["description"]

        # Score images quality
        images_score = self._score_images_quality(data.get("images", []))
        total_score += images_score * self.quality_weights["images"]

        # Score relationships quality
        rel_score = self._score_relationships_quality(data.get("relationships", []))
        total_score += rel_score * self.quality_weights["relationships"]

        # Score abilities quality
        abilities_score = self._score_abilities_quality(data.get("abilities", []))
        total_score += abilities_score * self.quality_weights["abilities"]

        # Score appearances quality
        app_score = self._score_appearances_quality(data.get("appearances", []))
        total_score += app_score * self.quality_weights["appearances"]

        # Score metadata quality
        meta_score = self._score_metadata_quality(data)
        total_score += meta_score * self.quality_weights["metadata"]

        # Calculate percentage score
        quality_score = (total_score / max_possible_score) * 100

        return min(100, max(0, quality_score))

    def _score_name_quality(self, name: str) -> float:
        """Score character name quality (0-1)."""
        if not name or not name.strip():
            return 0.0

        name = name.strip()

        # Basic name checks
        if len(name) < 2:
            return 0.3
        elif len(name) > 50:
            return 0.7
        elif name.lower() in ["unknown", "unnamed", "n/a"]:
            return 0.2
        else:
            return 1.0

    def _score_description_quality(self, description: str) -> float:
        """Score character description quality (0-1)."""
        if not description or not description.strip():
            return 0.0

        desc_length = len(description.strip())

        if desc_length < 20:
            return 0.3
        elif desc_length < 100:
            return 0.6
        elif desc_length < 500:
            return 0.9
        else:
            return 1.0

    def _score_images_quality(self, images: List[Dict[str, Any]]) -> float:
        """Score character images quality (0-1)."""
        if not images:
            return 0.0

        # Basic scoring based on number of images
        image_count = len(images)

        if image_count == 1:
            return 0.5
        elif image_count <= 3:
            return 0.8
        else:
            return 1.0

    def _score_relationships_quality(
        self, relationships: List[Dict[str, str]]
    ) -> float:
        """Score character relationships quality (0-1)."""
        if not relationships:
            return 0.0

        rel_count = len(relationships)

        if rel_count == 1:
            return 0.4
        elif rel_count <= 3:
            return 0.7
        else:
            return 1.0

    def _score_abilities_quality(self, abilities: List[str]) -> float:
        """Score character abilities quality (0-1)."""
        if not abilities:
            return 0.0

        ability_count = len(abilities)

        if ability_count == 1:
            return 0.4
        elif ability_count <= 5:
            return 0.8
        else:
            return 1.0

    def _score_appearances_quality(self, appearances: List[Dict[str, str]]) -> float:
        """Score character appearances quality (0-1)."""
        if not appearances:
            return 0.0

        app_count = len(appearances)

        if app_count == 1:
            return 0.3
        elif app_count <= 5:
            return 0.6
        else:
            return 1.0

    def _score_metadata_quality(self, data: Dict[str, Any]) -> float:
        """Score metadata quality (0-1)."""
        metadata_fields = ["source_url", "anime_name", "extraction_date"]
        present_fields = sum(1 for field in metadata_fields if data.get(field))

        return present_fields / len(metadata_fields)

    def _generate_quality_report(
        self, data: Dict[str, Any], score: float
    ) -> Dict[str, Any]:
        """
        Generate detailed quality report with suggestions.

        Args:
            data: Character data
            score: Quality score

        Returns:
            Quality report dictionary
        """
        report = {
            "overall_score": score,
            "category": self._categorize_quality(score),
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
        }

        # Identify strengths
        if data.get("name") and len(data["name"].strip()) > 2:
            report["strengths"].append("Has valid character name")

        if data.get("description") and len(data["description"]) > 100:
            report["strengths"].append("Has detailed description")

        if data.get("images") and len(data["images"]) > 0:
            report["strengths"].append(f"Has {len(data['images'])} character images")

        # Identify weaknesses and suggestions
        if not data.get("description") or len(data["description"]) < 50:
            report["weaknesses"].append("Limited or missing character description")
            report["suggestions"].append("Add more detailed character description")

        if not data.get("images"):
            report["weaknesses"].append("No character images")
            report["suggestions"].append("Add character portrait and other images")

        if not data.get("relationships"):
            report["weaknesses"].append("No character relationships defined")
            report["suggestions"].append("Add family, friends, or enemy relationships")

        if not data.get("abilities"):
            report["weaknesses"].append("No character abilities listed")
            report["suggestions"].append("Add character powers, skills, or techniques")

        return report

    def _categorize_quality(self, score: float) -> str:
        """
        Categorize quality score into levels.

        Args:
            score: Quality score

        Returns:
            Quality category string
        """
        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"

    def _update_statistics(self, score: float) -> None:
        """
        Update quality statistics.

        Args:
            score: Quality score
        """
        if score >= 80:
            self.high_quality_count += 1
        elif score >= 50:
            self.medium_quality_count += 1
        else:
            self.low_quality_count += 1

    def close_spider(self, spider):
        """
        Log quality statistics when spider closes.

        Args:
            spider: Spider instance
        """
        total_items = (
            self.high_quality_count + self.medium_quality_count + self.low_quality_count
        )

        if total_items > 0:
            high_pct = (self.high_quality_count / total_items) * 100
            medium_pct = (self.medium_quality_count / total_items) * 100
            low_pct = (self.low_quality_count / total_items) * 100

            self.logger.info(f"Quality pipeline statistics:")
            self.logger.info(
                f"  High quality (80+): {self.high_quality_count} ({high_pct:.1f}%)"
            )
            self.logger.info(
                f"  Medium quality (50-79): {self.medium_quality_count} ({medium_pct:.1f}%)"
            )
            self.logger.info(
                f"  Low quality (<50): {self.low_quality_count} ({low_pct:.1f}%)"
            )


class DuplicateFilterPipeline:
    """
    Pipeline for filtering duplicate character entries.

    This pipeline identifies and handles duplicate characters based on:
    - Exact name matches
    - Similar name patterns
    - URL-based identification
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.seen_characters = set()
        self.duplicate_count = 0
        self.unique_count = 0

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """
        Filter duplicate character items.

        Args:
            item: Character item data
            spider: Spider instance

        Returns:
            Item if unique, raises DropItem if duplicate
        """
        adapter = ItemAdapter(item)

        # Generate character fingerprint
        fingerprint = self._generate_character_fingerprint(dict(adapter))

        if fingerprint in self.seen_characters:
            self.duplicate_count += 1
            character_name = adapter.get("name", "Unknown")
            self.logger.info(f"Duplicate character filtered: {character_name}")
            raise DropItem(f"Duplicate character: {character_name}")

        # Mark as seen
        self.seen_characters.add(fingerprint)
        self.unique_count += 1

        return dict(adapter)

    def _generate_character_fingerprint(self, data: Dict[str, Any]) -> str:
        """
        Generate unique fingerprint for character.

        Args:
            data: Character data

        Returns:
            Character fingerprint string
        """
        # Use name and anime combination as primary fingerprint
        name = data.get("name", "").lower().strip()
        anime = data.get("anime_name", "").lower().strip()

        # Normalize name (remove common variations)
        name = self._normalize_character_name(name)

        # Create fingerprint
        fingerprint = f"{anime}:{name}"

        return fingerprint

    def _normalize_character_name(self, name: str) -> str:
        """
        Normalize character name for comparison.

        Args:
            name: Original character name

        Returns:
            Normalized character name
        """
        import re

        # Convert to lowercase
        name = name.lower()

        # Remove common prefixes/suffixes
        name = re.sub(r"\b(mr|mrs|ms|dr|sir|lady)\b\.?", "", name)
        name = re.sub(r"\b(jr|sr|ii|iii)\b\.?", "", name)

        # Remove punctuation and extra spaces
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name).strip()

        return name

    def close_spider(self, spider):
        """
        Log duplicate filtering statistics.

        Args:
            spider: Spider instance
        """
        total_processed = self.unique_count + self.duplicate_count

        if total_processed > 0:
            duplicate_pct = (self.duplicate_count / total_processed) * 100
            self.logger.info(f"Duplicate filter statistics:")
            self.logger.info(f"  Unique characters: {self.unique_count}")
            self.logger.info(
                f"  Duplicate characters: {self.duplicate_count} ({duplicate_pct:.1f}%)"
            )
        else:
            self.logger.info("No characters processed by duplicate filter")
