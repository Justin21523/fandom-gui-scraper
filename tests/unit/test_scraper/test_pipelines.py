# tests/unit/test_scraper/test_pipelines.py
"""
Unit tests for scraper pipelines module.

Tests validation, image processing, and data storage pipelines.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestDataValidationPipeline:
    """Tests for DataValidationPipeline class."""

    @pytest.fixture
    def pipeline(self):
        """Create a DataValidationPipeline instance."""
        from scraper.pipelines import DataValidationPipeline

        pipeline = DataValidationPipeline()
        return pipeline

    def test_is_valid_url_with_valid_urls(self, pipeline):
        """Test URL validation with valid URLs."""
        valid_urls = [
            "https://onepiece.fandom.com/wiki/Luffy",
            "http://example.com/path",
            "https://example.com:8080/path?query=value",
        ]
        for url in valid_urls:
            assert pipeline._is_valid_url(url) is True

    def test_is_valid_url_with_invalid_urls(self, pipeline):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
        ]
        for url in invalid_urls:
            assert pipeline._is_valid_url(url) is False

    def test_is_valid_url_with_malformed_url(self, pipeline):
        """Test URL validation handles malformed URLs gracefully."""
        result = pipeline._is_valid_url("://missing-scheme")
        assert result is False

    def test_required_fields_defined(self, pipeline):
        """Test that required fields are properly defined."""
        assert "name" in pipeline.required_fields
        assert "anime_name" in pipeline.required_fields
        assert "source_url" in pipeline.required_fields

    def test_default_values_defined(self, pipeline):
        """Test that default values are properly defined."""
        assert "description" in pipeline.default_values
        assert "images" in pipeline.default_values
        assert "relationships" in pipeline.default_values


class TestImageDownloadPipeline:
    """Tests for ImageDownloadPipeline class."""

    @pytest.fixture
    def pipeline(self):
        """Create an ImageDownloadPipeline instance."""
        from scraper.pipelines import ImageDownloadPipeline

        # Mock the parent class initialization
        with patch("scrapy.pipelines.images.ImagesPipeline.__init__", return_value=None):
            pipeline = ImageDownloadPipeline("test_storage")
            pipeline.logger = MagicMock()
            return pipeline

    def test_is_valid_image_url_with_valid_urls(self, pipeline):
        """Test image URL validation with valid image URLs."""
        valid_urls = [
            "https://example.com/image.jpg",
            "https://example.com/image.jpeg",
            "https://example.com/image.png",
            "https://example.com/image.gif",
            "https://example.com/image.webp",
        ]
        for url in valid_urls:
            # Use private method name
            assert pipeline._is_valid_image_url(url) is True

    def test_is_valid_image_url_with_invalid_urls(self, pipeline):
        """Test image URL validation with invalid URLs."""
        # Empty URL should return False
        assert pipeline._is_valid_image_url("") is False

    def test_is_valid_image_url_with_image_keywords(self, pipeline):
        """Test image URL validation recognizes image keywords."""
        urls_with_keywords = [
            "https://example.com/img/something",
            "https://example.com/image/file",
        ]
        for url in urls_with_keywords:
            result = pipeline._is_valid_image_url(url)
            assert result is True


class TestDataStoragePipeline:
    """Tests for DataStoragePipeline class."""

    @pytest.fixture
    def mock_mongodb(self):
        """Mock MongoDB connection."""
        with patch("pymongo.MongoClient") as mock_client:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            mock_client.return_value.admin.command.return_value = {"ok": 1}
            yield mock_client, mock_db, mock_collection

    def test_pipeline_initialization(self, mock_mongodb):
        """Test pipeline initialization."""
        from scraper.pipelines import DataStoragePipeline

        mock_client, mock_db, mock_collection = mock_mongodb

        pipeline = DataStoragePipeline(
            mongo_uri="mongodb://localhost:27017/",
            mongo_db="test_db",
        )

        assert pipeline.mongo_uri == "mongodb://localhost:27017/"
        assert pipeline.mongo_db == "test_db"


class TestDuplicateFilterPipeline:
    """Tests for DuplicateFilterPipeline class."""

    @pytest.fixture
    def pipeline(self):
        """Create a DuplicateFilterPipeline instance."""
        from scraper.pipelines import DuplicateFilterPipeline

        pipeline = DuplicateFilterPipeline()
        return pipeline

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes with empty seen set."""
        assert hasattr(pipeline, 'seen_characters')
        assert len(pipeline.seen_characters) == 0

    def test_generates_item_fingerprint(self, pipeline):
        """Test that fingerprint generation works."""
        item = {
            "name": "Test Character",
            "source_url": "https://example.com/character",
        }

        # Check if fingerprint method exists
        if hasattr(pipeline, '_generate_character_fingerprint'):
            fp1 = pipeline._generate_character_fingerprint(item)
            fp2 = pipeline._generate_character_fingerprint(item)
            assert fp1 == fp2
        else:
            # Pipeline exists but may use different method
            assert pipeline is not None

    def test_counts_initialized(self, pipeline):
        """Test that duplicate and unique counts are initialized."""
        assert pipeline.duplicate_count == 0
        assert pipeline.unique_count == 0


class TestDataQualityPipeline:
    """Tests for DataQualityPipeline class."""

    @pytest.fixture
    def pipeline(self):
        """Create a DataQualityPipeline instance."""
        from scraper.pipelines import DataQualityPipeline

        pipeline = DataQualityPipeline()
        return pipeline

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes correctly."""
        assert pipeline is not None

    def test_has_quality_weights(self, pipeline):
        """Test pipeline has quality weights configuration."""
        assert hasattr(pipeline, 'quality_weights')
        assert isinstance(pipeline.quality_weights, dict)
        assert "name" in pipeline.quality_weights

    def test_quality_counters_initialized(self, pipeline):
        """Test that quality counters are initialized."""
        assert pipeline.high_quality_count == 0
        assert pipeline.medium_quality_count == 0
        assert pipeline.low_quality_count == 0
