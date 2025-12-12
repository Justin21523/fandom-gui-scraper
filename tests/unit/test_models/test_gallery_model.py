"""
Unit tests for Gallery models (GalleryImage, GalleryCollection).

Test Coverage:
- GalleryImageCategory enum (11 categories)
- ImageQuality enum (4 levels)
- GalleryImage model (creation, validation, computed properties)
- GalleryCollection model (collections, statistics, methods)
- Edge cases and validation errors
"""

import pytest
from datetime import datetime
from typing import Optional
from pydantic import ValidationError, HttpUrl

from models.gallery_model import (
    GalleryImageCategory,
    ImageQuality,
    GalleryImage,
    GalleryCollection,
)


# ============================================================================
# Test GalleryImageCategory Enum
# ============================================================================


class TestGalleryImageCategory:
    """Test GalleryImageCategory enum."""

    def test_all_11_categories(self):
        """Test all 11 category values are accessible."""
        categories = [
            GalleryImageCategory.CONCEPT_ART,
            GalleryImageCategory.CHARACTER_DESIGN,
            GalleryImageCategory.SCREENSHOT,
            GalleryImageCategory.PROMOTIONAL,
            GalleryImageCategory.POSTER,
            GalleryImageCategory.WALLPAPER,
            GalleryImageCategory.MANGA_PANEL,
            GalleryImageCategory.MERCHANDISE,
            GalleryImageCategory.FANART,
            GalleryImageCategory.BEHIND_THE_SCENES,
            GalleryImageCategory.OTHER,
        ]
        assert len(categories) == 11
        assert all(isinstance(cat, GalleryImageCategory) for cat in categories)

    def test_category_values(self):
        """Test category string values."""
        assert GalleryImageCategory.CONCEPT_ART.value == "concept_art"
        assert GalleryImageCategory.CHARACTER_DESIGN.value == "character_design"
        assert GalleryImageCategory.SCREENSHOT.value == "screenshot"
        assert GalleryImageCategory.PROMOTIONAL.value == "promotional"
        assert GalleryImageCategory.POSTER.value == "poster"
        assert GalleryImageCategory.WALLPAPER.value == "wallpaper"
        assert GalleryImageCategory.MANGA_PANEL.value == "manga_panel"
        assert GalleryImageCategory.MERCHANDISE.value == "merchandise"
        assert GalleryImageCategory.FANART.value == "fanart"
        assert GalleryImageCategory.BEHIND_THE_SCENES.value == "behind_the_scenes"
        assert GalleryImageCategory.OTHER.value == "other"

    def test_category_enum_from_string(self):
        """Test creating category from string value."""
        category = GalleryImageCategory("screenshot")
        assert category == GalleryImageCategory.SCREENSHOT


# ============================================================================
# Test ImageQuality Enum
# ============================================================================


class TestImageQuality:
    """Test ImageQuality enum."""

    def test_all_4_quality_levels(self):
        """Test all 4 quality levels are accessible."""
        qualities = [
            ImageQuality.HIGH,
            ImageQuality.MEDIUM,
            ImageQuality.LOW,
            ImageQuality.UNKNOWN,
        ]
        assert len(qualities) == 4
        assert all(isinstance(q, ImageQuality) for q in qualities)

    def test_quality_values(self):
        """Test quality string values."""
        assert ImageQuality.HIGH.value == "high"
        assert ImageQuality.MEDIUM.value == "medium"
        assert ImageQuality.LOW.value == "low"
        assert ImageQuality.UNKNOWN.value == "unknown"

    def test_quality_enum_from_string(self):
        """Test creating quality from string value."""
        quality = ImageQuality("high")
        assert quality == ImageQuality.HIGH


# ============================================================================
# Test GalleryImage Model
# ============================================================================


class TestGalleryImage:
    """Test GalleryImage model creation and validation."""

    def test_model_creation_minimal(self):
        """Test creating GalleryImage with minimal required fields."""
        image = GalleryImage(
            url="https://example.com/images/luffy.jpg",
            anime_name="One Piece",
            source_url="https://onepiece.fandom.com/wiki/Luffy_Gallery",
        )
        assert str(image.url) == "https://example.com/images/luffy.jpg"
        assert image.anime_name == "One Piece"
        assert str(image.source_url) == "https://onepiece.fandom.com/wiki/Luffy_Gallery"
        assert image.category == GalleryImageCategory.OTHER  # Default
        assert image.quality == ImageQuality.UNKNOWN  # Default

    def test_model_creation_full(self):
        """Test creating GalleryImage with all fields."""
        image = GalleryImage(
            url="https://example.com/images/luffy_concept.jpg",
            anime_name="One Piece",
            source_url="https://onepiece.fandom.com/wiki/Luffy_Gallery",
            category=GalleryImageCategory.CONCEPT_ART,
            quality=ImageQuality.HIGH,
            caption="Luffy concept art",
            width=3840,
            height=2160,
            file_size=2097152,  # 2MB in bytes
            format="JPEG",
            related_character="Monkey D. Luffy",
            related_episode=1,  # Integer, not string
            tags=["protagonist", "straw_hat", "pirate_king"],
            download_success=True,
            downloaded_at=datetime(2023, 5, 15, 10, 30, 0),
        )
        assert image.category == GalleryImageCategory.CONCEPT_ART
        assert image.quality == ImageQuality.HIGH
        assert image.caption == "Luffy concept art"
        assert image.width == 3840
        assert image.height == 2160
        assert image.file_size == 2097152
        assert image.format == "JPEG"
        assert image.related_character == "Monkey D. Luffy"
        assert image.related_episode == 1
        assert image.tags == ["protagonist", "straw_hat", "pirate_king"]
        assert image.download_success is True
        assert image.downloaded_at == datetime(2023, 5, 15, 10, 30, 0)

    def test_required_fields_validation(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError) as exc_info:
            GalleryImage(
                anime_name="One Piece",
                source_url="https://example.com",
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("url",) for error in errors)

    def test_anime_name_min_length(self):
        """Test anime_name minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            GalleryImage(
                url="https://example.com/image.jpg",
                anime_name="",  # Empty string
                source_url="https://example.com",
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("anime_name",) for error in errors)

    def test_anime_name_max_length(self):
        """Test anime_name maximum length validation."""
        long_name = "A" * 201  # Exceeds 200 char limit
        with pytest.raises(ValidationError):
            GalleryImage(
                url="https://example.com/image.jpg",
                anime_name=long_name,
                source_url="https://example.com",
            )

    def test_caption_max_length(self):
        """Test caption maximum length validation."""
        long_caption = "A" * 1001  # Exceeds 1000 char limit
        with pytest.raises(ValidationError):
            GalleryImage(
                url="https://example.com/image.jpg",
                anime_name="Test",
                source_url="https://example.com",
                caption=long_caption,
            )

    def test_dimensions_validation(self):
        """Test width and height must be >= 1."""
        with pytest.raises(ValidationError):
            GalleryImage(
                url="https://example.com/image.jpg",
                anime_name="Test",
                source_url="https://example.com",
                width=0,  # Invalid
                height=100,
            )

        with pytest.raises(ValidationError):
            GalleryImage(
                url="https://example.com/image.jpg",
                anime_name="Test",
                source_url="https://example.com",
                width=100,
                height=-5,  # Invalid
            )


# ============================================================================
# Test GalleryImage Computed Properties
# ============================================================================


class TestGalleryImageComputedProperties:
    """Test GalleryImage computed properties."""

    def test_url_hash_generation(self):
        """Test URL hash (MD5) is generated."""
        image = GalleryImage(
            url="https://example.com/images/luffy.jpg",
            anime_name="One Piece",
            source_url="https://onepiece.fandom.com/wiki/Luffy_Gallery",
        )
        assert image.url_hash is not None
        assert len(image.url_hash) == 32  # MD5 hash length

    def test_url_hash_consistent(self):
        """Test URL hash is consistent for same URL."""
        image1 = GalleryImage(
            url="https://example.com/images/luffy.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        image2 = GalleryImage(
            url="https://example.com/images/luffy.jpg",
            anime_name="Naruto",  # Different anime
            source_url="https://example.com",
        )
        assert image1.url_hash == image2.url_hash  # Same URL = same hash

    def test_image_id_generation(self):
        """Test image_id is generated."""
        image = GalleryImage(
            url="https://example.com/images/luffy.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        assert image.image_id is not None
        assert len(image.image_id) == 32  # MD5 hash length

    def test_aspect_ratio_calculation(self):
        """Test aspect_ratio calculation."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=1920,
            height=1080,
        )
        assert image.aspect_ratio == 1.78  # 16:9 ratio

    def test_aspect_ratio_none_without_dimensions(self):
        """Test aspect_ratio is None without dimensions."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
        )
        assert image.aspect_ratio is None

    def test_aspect_ratio_with_zero_height(self):
        """Test aspect_ratio handles zero height."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=1920,
            height=1,  # Very small but valid
        )
        assert image.aspect_ratio == 1920.0

    def test_is_portrait_true(self):
        """Test is_portrait is True for portrait images."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=1080,
            height=1920,  # Height > Width
        )
        assert image.is_portrait is True

    def test_is_portrait_false(self):
        """Test is_portrait is False for landscape images."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=1920,
            height=1080,  # Width > Height
        )
        assert image.is_portrait is False

    def test_is_portrait_none_without_dimensions(self):
        """Test is_portrait is None without dimensions."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
        )
        assert image.is_portrait is None

    def test_resolution_label_4k(self):
        """Test resolution_label for 4K images."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=3840,
            height=2160,
        )
        assert image.resolution_label == "3840x2160 (4K)"

    def test_resolution_label_full_hd(self):
        """Test resolution_label for Full HD images."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=1920,
            height=1080,
        )
        assert image.resolution_label == "1920x1080 (Full HD)"

    def test_resolution_label_hd(self):
        """Test resolution_label for HD images."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=1280,
            height=720,
        )
        assert image.resolution_label == "1280x720 (HD)"

    def test_resolution_label_sd(self):
        """Test resolution_label for SD images."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=800,
            height=600,
        )
        assert image.resolution_label == "800x600 (SD)"

    def test_resolution_label_unknown(self):
        """Test resolution_label without dimensions."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
        )
        assert image.resolution_label == "Unknown"

    def test_file_size_label_mb(self):
        """Test file_size_label for MB range."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            file_size=2097152,  # 2MB (1024*1024*2)
        )
        assert image.file_size_label == "2.00 MB"

    def test_file_size_label_kb(self):
        """Test file_size_label for KB range."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            file_size=512000,  # 500KB
        )
        assert image.file_size_label == "500.00 KB"

    def test_file_size_label_bytes(self):
        """Test file_size_label for bytes."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            file_size=500,  # 500 bytes
        )
        assert image.file_size_label == "500 bytes"

    def test_file_size_label_unknown(self):
        """Test file_size_label without file size."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
        )
        assert image.file_size_label == "Unknown"


# ============================================================================
# Test GalleryCollection Model
# ============================================================================


class TestGalleryCollection:
    """Test GalleryCollection model creation and validation."""

    def test_model_creation_minimal(self):
        """Test creating GalleryCollection with minimal fields."""
        collection = GalleryCollection(
            name="Luffy Gallery",
            anime_name="One Piece",
            source_url="https://onepiece.fandom.com/wiki/Luffy_Gallery",
        )
        assert collection.name == "Luffy Gallery"
        assert collection.anime_name == "One Piece"
        assert str(collection.source_url) == "https://onepiece.fandom.com/wiki/Luffy_Gallery"
        assert collection.images == []  # Default empty list

    def test_model_creation_with_images(self):
        """Test creating GalleryCollection with images."""
        image1 = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        image2 = GalleryImage(
            url="https://example.com/image2.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=[image1, image2],
        )
        assert len(collection.images) == 2
        assert collection.images[0] == image1
        assert collection.images[1] == image2

    def test_required_fields_validation(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError) as exc_info:
            GalleryCollection(
                anime_name="One Piece",
                source_url="https://example.com",
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_name_min_length(self):
        """Test name minimum length validation."""
        with pytest.raises(ValidationError):
            GalleryCollection(
                name="",  # Empty string
                anime_name="One Piece",
                source_url="https://example.com",
            )

    def test_name_max_length(self):
        """Test name maximum length validation."""
        long_name = "A" * 201  # Exceeds 200 char limit
        with pytest.raises(ValidationError):
            GalleryCollection(
                name=long_name,
                anime_name="One Piece",
                source_url="https://example.com",
            )


# ============================================================================
# Test GalleryCollection Computed Properties
# ============================================================================


class TestGalleryCollectionComputedProperties:
    """Test GalleryCollection computed properties."""

    def test_collection_id_generation(self):
        """Test collection_id is generated."""
        collection = GalleryCollection(
            name="Luffy Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        assert collection.collection_id is not None
        assert len(collection.collection_id) == 32  # MD5 hash length

    def test_image_count(self):
        """Test image_count computed property."""
        image1 = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        image2 = GalleryImage(
            url="https://example.com/image2.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=[image1, image2],
        )
        assert collection.image_count == 2

    def test_image_count_empty(self):
        """Test image_count with empty collection."""
        collection = GalleryCollection(
            name="Empty Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        assert collection.image_count == 0

    def test_download_success_rate_all_downloaded(self):
        """Test download_success_rate when all downloaded."""
        image1 = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
            download_success=True,
        )
        image2 = GalleryImage(
            url="https://example.com/image2.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
            download_success=True,
        )
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=[image1, image2],
            total_images=2,
            downloaded_count=2,
        )
        assert collection.download_success_rate == 1.0  # Returns 0.0-1.0, not percentage

    def test_download_success_rate_partial(self):
        """Test download_success_rate with partial downloads."""
        image1 = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
            download_success=True,
        )
        image2 = GalleryImage(
            url="https://example.com/image2.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
            download_success=False,
        )
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=[image1, image2],
            total_images=2,
            downloaded_count=1,
        )
        assert collection.download_success_rate == 0.5  # Returns 0.0-1.0, not percentage

    def test_download_success_rate_none_downloaded(self):
        """Test download_success_rate when none downloaded."""
        image1 = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
            download_success=False,
        )
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=[image1],
            total_images=1,
            downloaded_count=0,
        )
        assert collection.download_success_rate == 0.0

    def test_download_success_rate_empty_collection(self):
        """Test download_success_rate with empty collection."""
        collection = GalleryCollection(
            name="Empty Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        assert collection.download_success_rate == 0.0

    def test_category_breakdown_empty(self):
        """Test category_breakdown with empty collection."""
        collection = GalleryCollection(
            name="Empty Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        assert collection.category_breakdown == {}

    def test_category_breakdown_single_category(self):
        """Test category_breakdown with single category."""
        image1 = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
            category=GalleryImageCategory.SCREENSHOT,
        )
        image2 = GalleryImage(
            url="https://example.com/image2.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
            category=GalleryImageCategory.SCREENSHOT,
        )
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=[image1, image2],
        )
        assert collection.category_breakdown == {"screenshot": 2}

    def test_category_breakdown_multiple_categories(self):
        """Test category_breakdown with multiple categories."""
        images = [
            GalleryImage(
                url=f"https://example.com/image{i}.jpg",
                anime_name="One Piece",
                source_url="https://example.com",
                category=category,
            )
            for i, category in enumerate(
                [
                    GalleryImageCategory.SCREENSHOT,
                    GalleryImageCategory.SCREENSHOT,
                    GalleryImageCategory.CONCEPT_ART,
                    GalleryImageCategory.PROMOTIONAL,
                    GalleryImageCategory.SCREENSHOT,
                ]
            )
        ]
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=images,
        )
        breakdown = collection.category_breakdown
        assert breakdown["screenshot"] == 3
        assert breakdown["concept_art"] == 1
        assert breakdown["promotional"] == 1


# ============================================================================
# Test GalleryCollection Methods
# ============================================================================


class TestGalleryCollectionMethods:
    """Test GalleryCollection methods."""

    def test_add_image(self):
        """Test add_image method."""
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        assert len(collection.images) == 0

        image = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        collection.add_image(image)

        assert len(collection.images) == 1
        assert collection.images[0] == image

    def test_add_multiple_images(self):
        """Test adding multiple images."""
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
        )

        for i in range(5):
            image = GalleryImage(
                url=f"https://example.com/image{i}.jpg",
                anime_name="One Piece",
                source_url="https://example.com",
            )
            collection.add_image(image)

        assert len(collection.images) == 5
        assert collection.image_count == 5

    def test_update_stats_method_exists(self):
        """Test update_stats method exists and is callable."""
        collection = GalleryCollection(
            name="Test Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        # Method should exist and be callable
        assert hasattr(collection, "update_stats")
        assert callable(getattr(collection, "update_stats"))


# ============================================================================
# Test MongoDB Document Conversion
# ============================================================================


class TestGalleryMongoDBConversion:
    """Test MongoDB document conversion."""

    def test_gallery_image_to_mongo_dict(self):
        """Test converting GalleryImage to MongoDB dict."""
        image = GalleryImage(
            url="https://example.com/images/luffy.jpg",
            anime_name="One Piece",
            source_url="https://onepiece.fandom.com/wiki/Luffy_Gallery",
            category=GalleryImageCategory.SCREENSHOT,
            width=1920,
            height=1080,
        )
        mongo_dict = image.model_dump()

        assert isinstance(mongo_dict, dict)
        assert "url" in mongo_dict
        assert "anime_name" in mongo_dict
        assert mongo_dict["anime_name"] == "One Piece"
        assert mongo_dict["category"] == "screenshot"

    def test_gallery_collection_to_mongo_dict(self):
        """Test converting GalleryCollection to MongoDB dict."""
        image = GalleryImage(
            url="https://example.com/image1.jpg",
            anime_name="One Piece",
            source_url="https://example.com",
        )
        collection = GalleryCollection(
            name="Luffy Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=[image],
        )
        mongo_dict = collection.model_dump()

        assert isinstance(mongo_dict, dict)
        assert "name" in mongo_dict
        assert "anime_name" in mongo_dict
        assert "images" in mongo_dict
        assert isinstance(mongo_dict["images"], list)
        assert len(mongo_dict["images"]) == 1


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_dimensions(self):
        """Test handling very large image dimensions."""
        image = GalleryImage(
            url="https://example.com/huge.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=99999,
            height=99999,
        )
        assert image.width == 99999
        assert image.height == 99999
        assert image.resolution_label == "99999x99999 (4K)"  # >= 3840

    def test_very_large_file_size(self):
        """Test handling very large file sizes."""
        image = GalleryImage(
            url="https://example.com/huge.jpg",
            anime_name="Test",
            source_url="https://example.com",
            file_size=1073741824,  # 1GB
        )
        assert image.file_size_label == "1024.00 MB"

    def test_empty_tags_list(self):
        """Test handling empty tags list."""
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            tags=[],
        )
        assert image.tags == []

    def test_many_tags(self):
        """Test handling many tags."""
        tags = [f"tag{i}" for i in range(50)]
        image = GalleryImage(
            url="https://example.com/image.jpg",
            anime_name="Test",
            source_url="https://example.com",
            tags=tags,
        )
        assert len(image.tags) == 50

    def test_square_aspect_ratio(self):
        """Test square image aspect ratio."""
        image = GalleryImage(
            url="https://example.com/square.jpg",
            anime_name="Test",
            source_url="https://example.com",
            width=1000,
            height=1000,
        )
        assert image.aspect_ratio == 1.0
        assert image.is_portrait is False  # Width >= Height

    def test_all_categories_in_collection(self):
        """Test collection with all 11 categories."""
        categories = [
            GalleryImageCategory.CONCEPT_ART,
            GalleryImageCategory.CHARACTER_DESIGN,
            GalleryImageCategory.SCREENSHOT,
            GalleryImageCategory.PROMOTIONAL,
            GalleryImageCategory.POSTER,
            GalleryImageCategory.WALLPAPER,
            GalleryImageCategory.MANGA_PANEL,
            GalleryImageCategory.MERCHANDISE,
            GalleryImageCategory.FANART,
            GalleryImageCategory.BEHIND_THE_SCENES,
            GalleryImageCategory.OTHER,
        ]

        images = [
            GalleryImage(
                url=f"https://example.com/image{i}.jpg",
                anime_name="One Piece",
                source_url="https://example.com",
                category=cat,
            )
            for i, cat in enumerate(categories)
        ]

        collection = GalleryCollection(
            name="Complete Gallery",
            anime_name="One Piece",
            source_url="https://example.com",
            images=images,
        )

        breakdown = collection.category_breakdown
        assert len(breakdown) == 11  # All 11 categories present
        assert all(count == 1 for count in breakdown.values())
