# tests/unit/test_api/test_schemas.py
"""
Unit tests for API schemas.

Tests Pydantic schema validation and serialization.
"""

import pytest
from datetime import datetime


class TestCharacterSchemas:
    """Tests for character-related schemas."""

    def test_character_status_enum(self):
        """Test CharacterStatus enum values."""
        from api.schemas.character import CharacterStatus

        assert CharacterStatus.ALIVE == "alive"
        assert CharacterStatus.DECEASED == "deceased"
        assert CharacterStatus.UNKNOWN == "unknown"

    def test_image_schema_creation(self):
        """Test ImageSchema creation."""
        from api.schemas.character import ImageSchema

        image = ImageSchema(
            url="https://example.com/image.jpg",
            image_type="portrait",
            is_primary=True,
            width=300,
            height=400,
        )

        assert image.url == "https://example.com/image.jpg"
        assert image.is_primary is True
        assert image.width == 300

    def test_relationship_schema_creation(self):
        """Test RelationshipSchema creation."""
        from api.schemas.character import RelationshipSchema

        rel = RelationshipSchema(
            character_name="Roronoa Zoro",
            relationship_type="crew_mate",
            description="First mate",
        )

        assert rel.character_name == "Roronoa Zoro"
        assert rel.relationship_type == "crew_mate"

    def test_character_base_schema(self):
        """Test CharacterBase schema with defaults."""
        from api.schemas.character import CharacterBase, CharacterStatus

        char = CharacterBase(
            name="Monkey D. Luffy",
            anime_name="One Piece",
        )

        assert char.name == "Monkey D. Luffy"
        assert char.anime_name == "One Piece"
        assert char.status == CharacterStatus.UNKNOWN
        assert char.description is None

    def test_character_response_schema(self):
        """Test CharacterResponse schema."""
        from api.schemas.character import CharacterResponse

        char = CharacterResponse(
            name="Monkey D. Luffy",
            anime_name="One Piece",
            character_id="abc123",
            source_url="https://onepiece.fandom.com/wiki/Luffy",
        )

        assert char.character_id == "abc123"
        assert char.images == []
        assert char.relationships == []

    def test_character_list_response(self):
        """Test CharacterListResponse schema."""
        from api.schemas.character import CharacterListResponse, CharacterResponse

        items = [
            CharacterResponse(
                name="Luffy",
                anime_name="One Piece",
                character_id="1",
                source_url="https://example.com/1",
            ),
            CharacterResponse(
                name="Zoro",
                anime_name="One Piece",
                character_id="2",
                source_url="https://example.com/2",
            ),
        ]

        response = CharacterListResponse(
            items=items,
            total=100,
            page=1,
            per_page=20,
            pages=5,
        )

        assert len(response.items) == 2
        assert response.total == 100
        assert response.pages == 5

    def test_character_create_request_validation(self):
        """Test CharacterCreateRequest validation."""
        from api.schemas.character import CharacterCreateRequest
        from pydantic import ValidationError

        # Valid request
        request = CharacterCreateRequest(
            name="Test Character",
            anime_name="Test Anime",
            source_url="https://example.com",
        )
        assert request.name == "Test Character"

        # Invalid - empty name
        with pytest.raises(ValidationError):
            CharacterCreateRequest(
                name="",
                anime_name="Test Anime",
                source_url="https://example.com",
            )

    def test_character_update_request_optional_fields(self):
        """Test CharacterUpdateRequest with optional fields."""
        from api.schemas.character import CharacterUpdateRequest

        # All fields optional
        request = CharacterUpdateRequest()
        assert request.name is None
        assert request.description is None

        # Partial update
        request = CharacterUpdateRequest(name="New Name")
        assert request.name == "New Name"
        assert request.description is None

    def test_search_request_validation(self):
        """Test SearchRequest validation."""
        from api.schemas.character import SearchRequest
        from pydantic import ValidationError

        request = SearchRequest(query="Luffy")
        assert request.query == "Luffy"
        assert request.anime_name is None

        # Invalid - empty query
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_stats_response(self):
        """Test StatsResponse schema."""
        from api.schemas.character import StatsResponse

        stats = StatsResponse(
            total_characters=1000,
            total_anime=10,
            characters_by_anime={"One Piece": 500, "Naruto": 300},
            quality_distribution={"high": 200, "medium": 500, "low": 300},
            recent_updates=50,
        )

        assert stats.total_characters == 1000
        assert stats.characters_by_anime["One Piece"] == 500

    def test_error_response(self):
        """Test ErrorResponse schema."""
        from api.schemas.character import ErrorResponse

        error = ErrorResponse(
            error="Not Found",
            detail="Character not found",
            status_code=404,
        )

        assert error.error == "Not Found"
        assert error.status_code == 404

    def test_success_response(self):
        """Test SuccessResponse schema."""
        from api.schemas.character import SuccessResponse

        success = SuccessResponse(
            message="Operation completed",
            data={"id": "123"},
        )

        assert success.message == "Operation completed"
        assert success.data["id"] == "123"
