# tests/integration/test_api_integration.py
"""
Integration tests for the REST API.

Tests API endpoints with mocked database connections.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def get_auth_headers():
    """Get authentication headers for protected endpoints."""
    from api.security.auth import create_access_token

    token = create_access_token(data={"sub": "test_user", "is_admin": True})
    return {"Authorization": f"Bearer {token}"}


class TestAPIRootEndpoints:
    """Test root API endpoints (no DB required)."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from api.main import app
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Fandom Scraper API"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAPICharacterEndpoints:
    """Test character API endpoints with mocked DB."""

    @pytest.fixture
    def mock_collection(self):
        """Create a mock collection."""
        return MagicMock()

    @pytest.fixture
    def mock_db_manager(self, mock_collection):
        """Create a mock database manager."""
        mock_manager = MagicMock()
        mock_manager.is_connected.return_value = True
        mock_manager.database_name = "test_db"
        mock_manager.get_collection.return_value = mock_collection
        mock_manager.connect.return_value = True
        return mock_manager

    @pytest.fixture
    def client(self, mock_db_manager):
        """Create a test client with mocked database."""
        import api.endpoints.characters as char_module

        # Store original and replace with mock
        original_db = char_module._db_manager
        char_module._db_manager = mock_db_manager

        from api.main import app
        client = TestClient(app)

        yield client

        # Restore original
        char_module._db_manager = original_db

    def test_list_characters_empty(self, client, mock_collection):
        """Test listing characters when database is empty."""
        mock_collection.count_documents.return_value = 0
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        response = client.get("/api/v1/characters/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_characters_with_data(self, client, mock_collection):
        """Test listing characters with data."""
        mock_collection.count_documents.return_value = 2

        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {
                "_character_id": "char1",
                "name": "Luffy",
                "anime_name": "One Piece",
                "source_url": "https://example.com/1",
            },
            {
                "_character_id": "char2",
                "name": "Zoro",
                "anime_name": "One Piece",
                "source_url": "https://example.com/2",
            },
        ]
        mock_collection.find.return_value = mock_cursor

        response = client.get("/api/v1/characters/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_characters_pagination(self, client, mock_collection):
        """Test character list pagination."""
        mock_collection.count_documents.return_value = 100

        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        response = client.get("/api/v1/characters/?page=2&per_page=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["pages"] == 10

    def test_get_character_not_found(self, client, mock_collection):
        """Test getting non-existent character."""
        mock_collection.find_one.return_value = None

        response = client.get("/api/v1/characters/nonexistent")

        assert response.status_code == 404

    def test_get_character_success(self, client, mock_collection):
        """Test getting existing character."""
        mock_collection.find_one.return_value = {
            "_character_id": "char123",
            "name": "Naruto",
            "anime_name": "Naruto",
            "source_url": "https://example.com/naruto",
        }

        response = client.get("/api/v1/characters/char123")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Naruto"
        assert data["character_id"] == "char123"

    def test_delete_character_success(self, client, mock_collection):
        """Test deleting a character."""
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        response = client.delete(
            "/api/v1/characters/char123",
            headers=get_auth_headers(),
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

    def test_delete_character_not_found(self, client, mock_collection):
        """Test deleting non-existent character."""
        mock_collection.delete_one.return_value = MagicMock(deleted_count=0)

        response = client.delete(
            "/api/v1/characters/nonexistent",
            headers=get_auth_headers(),
        )

        assert response.status_code == 404


class TestAPIValidation:
    """Test API request validation."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from api.main import app
        return TestClient(app)

    def test_create_character_missing_required_fields(self, client):
        """Test creating character with missing required fields."""
        response = client.post(
            "/api/v1/characters/",
            json={"name": "Test"},  # Missing anime_name and source_url
            headers=get_auth_headers(),
        )

        assert response.status_code == 422  # Validation error

    def test_create_character_empty_name(self, client):
        """Test creating character with empty name."""
        response = client.post(
            "/api/v1/characters/",
            json={
                "name": "",
                "anime_name": "Test Anime",
                "source_url": "https://example.com",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == 422

    def test_pagination_invalid_page(self, client):
        """Test invalid page number."""
        response = client.get("/api/v1/characters/?page=0")
        assert response.status_code == 422

    def test_pagination_invalid_per_page(self, client):
        """Test invalid per_page value."""
        response = client.get("/api/v1/characters/?per_page=1000")
        assert response.status_code == 422
