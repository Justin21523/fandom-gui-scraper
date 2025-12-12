"""
Unit tests for Episode and Chapter data models.

Tests cover:
- EpisodeInfo model creation and validation
- ChapterInfo model creation and validation
- EpisodeImage model
- Episode type enums
- Date parsing and validation
- Computed fields (IDs, codes, counts)
- MongoDB document conversion
"""

import pytest
from datetime import date, datetime
from typing import Dict, Any

from pydantic import ValidationError

from models.episode_model import (
    EpisodeInfo,
    ChapterInfo,
    EpisodeImage,
    EpisodeType,
    ChapterType,
)


# ============================================================================
# TEST: EpisodeType Enum
# ============================================================================

class TestEpisodeType:
    """Test EpisodeType enum."""

    def test_all_episode_types_valid(self):
        """Test all episode type values are valid."""
        valid_types = [
            EpisodeType.TV_EPISODE,
            EpisodeType.OVA,
            EpisodeType.MOVIE,
            EpisodeType.SPECIAL,
            EpisodeType.FILLER,
            EpisodeType.RECAP,
            EpisodeType.UNKNOWN,
        ]

        for ep_type in valid_types:
            assert isinstance(ep_type, EpisodeType)
            assert isinstance(ep_type.value, str)

    def test_episode_type_values(self):
        """Test episode type enum values."""
        assert EpisodeType.TV_EPISODE.value == "tv_episode"
        assert EpisodeType.OVA.value == "ova"
        assert EpisodeType.MOVIE.value == "movie"


# ============================================================================
# TEST: ChapterType Enum
# ============================================================================

class TestChapterType:
    """Test ChapterType enum."""

    def test_all_chapter_types_valid(self):
        """Test all chapter type values are valid."""
        valid_types = [
            ChapterType.MANGA_CHAPTER,
            ChapterType.LIGHT_NOVEL,
            ChapterType.WEB_NOVEL,
            ChapterType.ONE_SHOT,
            ChapterType.SPECIAL,
            ChapterType.UNKNOWN,
        ]

        for ch_type in valid_types:
            assert isinstance(ch_type, ChapterType)
            assert isinstance(ch_type.value, str)

    def test_chapter_type_values(self):
        """Test chapter type enum values."""
        assert ChapterType.MANGA_CHAPTER.value == "manga_chapter"
        assert ChapterType.LIGHT_NOVEL.value == "light_novel"


# ============================================================================
# TEST: EpisodeImage
# ============================================================================

class TestEpisodeImage:
    """Test EpisodeImage model."""

    def test_image_creation(self):
        """Test creating an episode image."""
        image = EpisodeImage(
            url="https://example.com/image.jpg",
            caption="Test image",
            is_thumbnail=True
        )

        assert str(image.url) == "https://example.com/image.jpg"
        assert image.caption == "Test image"
        assert image.is_thumbnail is True

    def test_url_hash_generation(self):
        """Test URL hash is generated correctly."""
        image = EpisodeImage(url="https://example.com/image.jpg")

        assert image.url_hash is not None
        assert isinstance(image.url_hash, str)
        assert len(image.url_hash) == 32  # MD5 hash length

    def test_timestamp_format(self):
        """Test timestamp field accepts various formats."""
        image1 = EpisodeImage(
            url="https://example.com/img.jpg",
            timestamp="12:34:56"
        )
        image2 = EpisodeImage(
            url="https://example.com/img.jpg",
            timestamp="34:56"
        )

        assert image1.timestamp == "12:34:56"
        assert image2.timestamp == "34:56"

    def test_optional_fields(self):
        """Test optional fields default to None."""
        image = EpisodeImage(url="https://example.com/image.jpg")

        assert image.local_path is None
        assert image.caption is None
        assert image.timestamp is None
        assert image.scene_description is None
        assert image.is_thumbnail is False


# ============================================================================
# TEST: EpisodeInfo
# ============================================================================

class TestEpisodeInfo:
    """Test EpisodeInfo model."""

    def test_model_creation_minimal(self):
        """Test creating episode with minimal required fields."""
        episode = EpisodeInfo(
            title="Test Episode",
            number=1,
            anime_name="Test Anime",
            source_url="https://example.com/episode1"
        )

        assert episode.title == "Test Episode"
        assert episode.number == 1
        assert episode.anime_name == "Test Anime"
        assert str(episode.source_url) == "https://example.com/episode1"

    def test_season_episode_code_with_season(self):
        """Test season/episode code generation with season."""
        episode = EpisodeInfo(
            title="Episode 5",
            number=5,
            season=1,
            anime_name="Test Anime",
            source_url="https://example.com/ep5"
        )

        assert episode.season_episode_code == "S01E05"

    def test_season_episode_code_without_season(self):
        """Test season/episode code generation without season."""
        episode = EpisodeInfo(
            title="Episode 23",
            number=23,
            anime_name="Test Anime",
            source_url="https://example.com/ep23"
        )

        assert episode.season_episode_code == "E23"

    def test_episode_id_generation(self):
        """Test unique episode ID generation."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="One Piece",
            source_url="https://example.com/ep1"
        )

        assert episode.episode_id is not None
        assert isinstance(episode.episode_id, str)
        assert len(episode.episode_id) == 32  # MD5 hash

    def test_episode_id_with_season(self):
        """Test episode ID includes season when available."""
        ep1 = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test Anime",
            source_url="https://example.com/ep1"
        )

        ep2 = EpisodeInfo(
            title="Test",
            number=1,
            season=1,
            anime_name="Test Anime",
            source_url="https://example.com/ep1"
        )

        # Different IDs because one has season
        assert ep1.episode_id != ep2.episode_id

    def test_required_fields_validation(self):
        """Test validation of required fields."""
        with pytest.raises(ValidationError) as exc_info:
            EpisodeInfo(
                title="",  # Empty title should fail
                number=1,
                anime_name="Test",
                source_url="https://example.com"
            )

        errors = exc_info.value.errors()
        assert any('title' in str(err) for err in errors)

    def test_episode_number_validation(self):
        """Test episode number must be >= 1."""
        with pytest.raises(ValidationError):
            EpisodeInfo(
                title="Test",
                number=0,  # Should fail
                anime_name="Test",
                source_url="https://example.com"
            )

    def test_optional_fields(self):
        """Test optional fields."""
        episode = EpisodeInfo(
            title="Test Episode",
            number=1,
            anime_name="Test Anime",
            source_url="https://example.com/ep1",
            synopsis="This is a test episode synopsis.",
            duration_minutes=24,
            director="Test Director",
            writer="Test Writer"
        )

        assert episode.synopsis == "This is a test episode synopsis."
        assert episode.duration_minutes == 24
        assert episode.director == "Test Director"
        assert episode.writer == "Test Writer"

    def test_characters_featured_list(self):
        """Test characters_featured list."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1",
            characters_featured=["Luffy", "Zoro", "Nami"]
        )

        assert len(episode.characters_featured) == 3
        assert "Luffy" in episode.characters_featured
        assert episode.character_count == 3

    def test_images_list(self):
        """Test episode images list."""
        img1 = EpisodeImage(url="https://example.com/img1.jpg")
        img2 = EpisodeImage(url="https://example.com/img2.jpg")

        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1",
            images=[img1, img2]
        )

        assert len(episode.images) == 2
        assert episode.image_count == 2

    def test_episode_type_default(self):
        """Test default episode type."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1"
        )

        assert episode.episode_type == EpisodeType.TV_EPISODE

    def test_episode_type_custom(self):
        """Test setting custom episode type."""
        episode = EpisodeInfo(
            title="OVA Special",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ova1",
            episode_type=EpisodeType.OVA
        )

        assert episode.episode_type == EpisodeType.OVA

    def test_date_parsing_from_string(self):
        """Test parsing air_date from string."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1",
            air_date="2023-05-15"
        )

        assert episode.air_date == date(2023, 5, 15)

    def test_date_parsing_various_formats(self):
        """Test date parsing supports multiple formats."""
        test_dates = [
            ("2023-05-15", date(2023, 5, 15)),
            ("05/15/2023", date(2023, 5, 15)),
            ("May 15, 2023", date(2023, 5, 15)),
        ]

        for date_str, expected_date in test_dates:
            episode = EpisodeInfo(
                title="Test",
                number=1,
                anime_name="Test",
                source_url="https://example.com/ep1",
                air_date=date_str
            )
            assert episode.air_date == expected_date

    def test_rating_validation(self):
        """Test rating must be between 0 and 10."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1",
            rating=8.5
        )

        assert episode.rating == 8.5

        with pytest.raises(ValidationError):
            EpisodeInfo(
                title="Test",
                number=1,
                anime_name="Test",
                source_url="https://example.com/ep1",
                rating=11.0  # Too high
            )

    def test_to_dict(self):
        """Test converting to dictionary."""
        episode = EpisodeInfo(
            title="Test Episode",
            number=1,
            anime_name="Test Anime",
            source_url="https://example.com/ep1"
        )

        data = episode.to_dict()

        assert isinstance(data, dict)
        assert data['title'] == "Test Episode"
        assert data['number'] == 1
        assert 'episode_id' in data
        assert 'season_episode_code' in data

    def test_to_mongodb_doc(self):
        """Test converting to MongoDB document."""
        img = EpisodeImage(url="https://example.com/img.jpg", caption="Test")

        episode = EpisodeInfo(
            title="Test Episode",
            number=1,
            anime_name="Test Anime",
            source_url="https://example.com/ep1",
            thumbnail_url="https://example.com/thumb.jpg",
            images=[img]
        )

        doc = episode.to_mongodb_doc()

        assert isinstance(doc, dict)
        assert isinstance(doc['source_url'], str)
        assert isinstance(doc['thumbnail_url'], str)
        assert isinstance(doc['images'], list)
        assert len(doc['images']) == 1
        assert isinstance(doc['images'][0], dict)
        assert 'url_hash' in doc['images'][0]


# ============================================================================
# TEST: ChapterInfo
# ============================================================================

class TestChapterInfo:
    """Test ChapterInfo model."""

    def test_manga_chapter_creation(self):
        """Test creating a manga chapter."""
        chapter = ChapterInfo(
            title="The Beginning",
            number=1,
            manga_name="Test Manga",
            source_url="https://example.com/chapter1"
        )

        assert chapter.title == "The Beginning"
        assert chapter.number == 1
        assert chapter.manga_name == "Test Manga"

    def test_volume_chapter_code_with_volume(self):
        """Test volume/chapter code generation with volume."""
        chapter = ChapterInfo(
            title="Chapter 23",
            number=23,
            volume=5,
            manga_name="Test Manga",
            source_url="https://example.com/ch23"
        )

        assert chapter.volume_chapter_code == "Vol05Ch023"

    def test_volume_chapter_code_without_volume(self):
        """Test volume/chapter code generation without volume."""
        chapter = ChapterInfo(
            title="Chapter 123",
            number=123,
            manga_name="Test Manga",
            source_url="https://example.com/ch123"
        )

        assert chapter.volume_chapter_code == "Ch123"

    def test_chapter_id_generation(self):
        """Test unique chapter ID generation."""
        chapter = ChapterInfo(
            title="Test Chapter",
            number=1,
            manga_name="One Piece",
            source_url="https://example.com/ch1"
        )

        assert chapter.chapter_id is not None
        assert isinstance(chapter.chapter_id, str)
        assert len(chapter.chapter_id) == 32  # MD5 hash

    def test_page_count_validation(self):
        """Test page count validation."""
        chapter = ChapterInfo(
            title="Test",
            number=1,
            manga_name="Test",
            source_url="https://example.com/ch1",
            page_count=20
        )

        assert chapter.page_count == 20

        with pytest.raises(ValidationError):
            ChapterInfo(
                title="Test",
                number=1,
                manga_name="Test",
                source_url="https://example.com/ch1",
                page_count=0  # Must be >= 1
            )

    def test_chapter_type_default(self):
        """Test default chapter type."""
        chapter = ChapterInfo(
            title="Test",
            number=1,
            manga_name="Test",
            source_url="https://example.com/ch1"
        )

        assert chapter.chapter_type == ChapterType.MANGA_CHAPTER

    def test_chapter_type_custom(self):
        """Test setting custom chapter type."""
        chapter = ChapterInfo(
            title="Light Novel Chapter",
            number=1,
            manga_name="Test",
            source_url="https://example.com/ch1",
            chapter_type=ChapterType.LIGHT_NOVEL
        )

        assert chapter.chapter_type == ChapterType.LIGHT_NOVEL

    def test_characters_introduced(self):
        """Test characters_introduced list."""
        chapter = ChapterInfo(
            title="Test",
            number=1,
            manga_name="Test",
            source_url="https://example.com/ch1",
            characters_introduced=["New Character 1", "New Character 2"]
        )

        assert len(chapter.characters_introduced) == 2
        assert "New Character 1" in chapter.characters_introduced

    def test_date_parsing_from_string(self):
        """Test parsing release_date from string."""
        chapter = ChapterInfo(
            title="Test",
            number=1,
            manga_name="Test",
            source_url="https://example.com/ch1",
            release_date="2023-06-20"
        )

        assert chapter.release_date == date(2023, 6, 20)

    def test_to_mongodb_doc(self):
        """Test converting chapter to MongoDB document."""
        img = EpisodeImage(url="https://example.com/page1.jpg")

        chapter = ChapterInfo(
            title="Test Chapter",
            number=1,
            manga_name="Test Manga",
            source_url="https://example.com/ch1",
            cover_image_url="https://example.com/cover.jpg",
            images=[img]
        )

        doc = chapter.to_mongodb_doc()

        assert isinstance(doc, dict)
        assert isinstance(doc['source_url'], str)
        assert isinstance(doc['cover_image_url'], str)
        assert 'chapter_id' in doc
        assert 'volume_chapter_code' in doc
        assert isinstance(doc['images'], list)

    def test_arc_information(self):
        """Test story arc information fields."""
        chapter = ChapterInfo(
            title="Arc Finale",
            number=50,
            manga_name="Test Manga",
            source_url="https://example.com/ch50",
            arc_name="Test Arc",
            arc_number=2
        )

        assert chapter.arc_name == "Test Arc"
        assert chapter.arc_number == 2

    def test_production_info(self):
        """Test author and illustrator fields."""
        chapter = ChapterInfo(
            title="Test",
            number=1,
            manga_name="Test Manga",
            source_url="https://example.com/ch1",
            author="Test Author",
            illustrator="Test Illustrator"
        )

        assert chapter.author == "Test Author"
        assert chapter.illustrator == "Test Illustrator"

    def test_statistics_fields(self):
        """Test read_count and rating fields."""
        chapter = ChapterInfo(
            title="Popular Chapter",
            number=100,
            manga_name="Test Manga",
            source_url="https://example.com/ch100",
            read_count=50000,
            rating=9.5
        )

        assert chapter.read_count == 50000
        assert chapter.rating == 9.5


# ============================================================================
# TEST: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_synopsis(self):
        """Test synopsis length limit."""
        long_synopsis = "A" * 5000  # Exactly at limit

        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1",
            synopsis=long_synopsis
        )

        assert len(episode.synopsis) == 5000

        # Too long should fail
        with pytest.raises(ValidationError):
            EpisodeInfo(
                title="Test",
                number=1,
                anime_name="Test",
                source_url="https://example.com/ep1",
                synopsis="A" * 5001
            )

    def test_invalid_url_format(self):
        """Test invalid URL raises validation error."""
        with pytest.raises(ValidationError):
            EpisodeInfo(
                title="Test",
                number=1,
                anime_name="Test",
                source_url="not-a-valid-url"
            )

    def test_voice_actors_dict(self):
        """Test voice_actors dictionary field."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1",
            voice_actors={
                "Luffy": "Mayumi Tanaka",
                "Zoro": "Kazuya Nakai"
            }
        )

        assert len(episode.voice_actors) == 2
        assert episode.voice_actors["Luffy"] == "Mayumi Tanaka"

    def test_metadata_timestamps(self):
        """Test scraped_at and updated_at timestamps."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1"
        )

        assert isinstance(episode.scraped_at, datetime)
        assert isinstance(episode.updated_at, datetime)

    def test_invalid_date_string_returns_none(self):
        """Test invalid date string returns None."""
        episode = EpisodeInfo(
            title="Test",
            number=1,
            anime_name="Test",
            source_url="https://example.com/ep1",
            air_date="invalid-date-format"
        )

        assert episode.air_date is None
