# tests/conftest.py
"""
Pytest configuration and shared fixtures for Fandom GUI Scraper tests.

This module provides common fixtures, test configurations, and utilities
used across all test modules.
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Provide sample configuration for tests."""
    return {
        "database": {
            "host": "localhost",
            "port": 27017,
            "name": "fandom_scraper_test",
        },
        "scraping": {
            "delay": 0.1,
            "concurrent_requests": 2,
            "timeout": 5,
        },
        "storage": {
            "images_dir": "test_storage/images/",
            "exports_dir": "test_storage/exports/",
        },
    }


@pytest.fixture
def temp_storage_dir(tmp_path) -> Path:
    """Create temporary storage directory for tests."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True)
    (storage_dir / "images").mkdir()
    (storage_dir / "exports").mkdir()
    return storage_dir


# ============================================================================
# Data Fixtures
# ============================================================================


@pytest.fixture
def sample_character_data() -> Dict[str, Any]:
    """Provide sample character data for tests."""
    return {
        "name": "Monkey D. Luffy",
        "japanese_name": "モンキー・D・ルフィ",
        "aliases": ["Straw Hat", "Lucy"],
        "anime_source": "One Piece",
        "source_url": "https://onepiece.fandom.com/wiki/Monkey_D._Luffy",
        "description": "The captain of the Straw Hat Pirates",
        "status": "active",
        "affiliation": ["Straw Hat Pirates"],
        "images": [
            {
                "url": "https://example.com/luffy.jpg",
                "image_type": "portrait",
                "is_primary": True,
            }
        ],
        "relationships": [
            {
                "character_name": "Roronoa Zoro",
                "relationship_type": "crew_mate",
            }
        ],
    }


@pytest.fixture
def sample_anime_data() -> Dict[str, Any]:
    """Provide sample anime data for tests."""
    return {
        "name": "One Piece",
        "japanese_name": "ワンピース",
        "wiki_url": "https://onepiece.fandom.com/",
        "episode_count": 1000,
        "status": "ongoing",
        "genres": ["Action", "Adventure", "Comedy"],
    }


@pytest.fixture
def sample_image_urls() -> list:
    """Provide sample image URLs for tests."""
    return [
        "https://example.com/character1.jpg",
        "https://example.com/character2.png",
        "https://example.com/character3.webp",
    ]


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection for tests."""
    with patch("pymongo.MongoClient") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_client.return_value.admin.command.return_value = {"ok": 1}
        yield mock_client, mock_db


@pytest.fixture
def mock_scrapy_response():
    """Create a mock Scrapy response for spider tests."""
    from scrapy.http import HtmlResponse

    def _create_response(url: str, body: str) -> HtmlResponse:
        return HtmlResponse(
            url=url,
            body=body.encode("utf-8"),
            encoding="utf-8",
        )

    return _create_response


@pytest.fixture
def mock_network():
    """Mock network requests for tests."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"mock content"
        mock_get.return_value = mock_response
        yield mock_get


# ============================================================================
# HTML Fixtures for Spider Tests
# ============================================================================


@pytest.fixture
def sample_character_html() -> str:
    """Provide sample HTML for character page parsing tests."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Monkey D. Luffy | One Piece Wiki</title></head>
    <body>
        <article class="page-content">
            <h1 class="page-header__title">Monkey D. Luffy</h1>
            <aside class="portable-infobox">
                <figure class="pi-item pi-image">
                    <img src="https://example.com/luffy.jpg" alt="Luffy">
                </figure>
                <div class="pi-item pi-data" data-source="jname">
                    <h3>Japanese Name</h3>
                    <div class="pi-data-value">モンキー・D・ルフィ</div>
                </div>
                <div class="pi-item pi-data" data-source="status">
                    <h3>Status</h3>
                    <div class="pi-data-value">Alive</div>
                </div>
            </aside>
            <div class="mw-parser-output">
                <p>Monkey D. Luffy is the captain of the Straw Hat Pirates.</p>
            </div>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def sample_character_list_html() -> str:
    """Provide sample HTML for character list page parsing tests."""
    return """
    <!DOCTYPE html>
    <html>
    <body>
        <div class="category-page__members">
            <ul class="category-page__members-list">
                <li><a href="/wiki/Monkey_D._Luffy">Monkey D. Luffy</a></li>
                <li><a href="/wiki/Roronoa_Zoro">Roronoa Zoro</a></li>
                <li><a href="/wiki/Nami">Nami</a></li>
            </ul>
        </div>
    </body>
    </html>
    """


# ============================================================================
# Utility Functions
# ============================================================================


def assert_valid_character(data: Dict[str, Any]) -> None:
    """Assert that character data has required fields."""
    assert "name" in data and data["name"]
    assert "source_url" in data and data["source_url"]


def assert_valid_image_url(url: str) -> None:
    """Assert that URL is a valid image URL."""
    assert url.startswith(("http://", "https://"))
    assert any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"])


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_test_files(tmp_path):
    """Automatically clean up test files after each test."""
    yield
    # Cleanup happens automatically with tmp_path


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment once per session."""
    # Set environment variable to indicate test mode
    os.environ["FANDOM_SCRAPER_TEST_MODE"] = "1"
    yield
    # Cleanup
    os.environ.pop("FANDOM_SCRAPER_TEST_MODE", None)
