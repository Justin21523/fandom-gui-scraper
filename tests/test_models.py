# tests/test_models.py
"""
Test suite for data models

This module contains comprehensive tests for all data models
to ensure proper validation, serialization, and functionality.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from models.document import (
    AnimeCharacter,
    CharacterImage,
    CharacterRelationship,
    CharacterAbility,
    OnePieceSpecificData,
    ImageType,
    RelationshipType,
    CharacterStatus,
    DataQuality,
    create_onepiece_character,
    validate_character_data,
)


class TestCharacterImage:
    """Test CharacterImage model."""

    def test_valid_image_creation(self):
        """Test creating a valid character image."""
        image = CharacterImage(  # type: ignore
            url="https://example.com/image.jpg",
            image_type=ImageType.PORTRAIT,
            width=300,
            height=400,
            is_primary=True,
        )

        assert image.url == "https://example.com/image.jpg"
        assert image.image_type == ImageType.PORTRAIT
        assert image.aspect_ratio == 0.75
        assert image.is_primary is True
        assert image.is_valid_size()

    def test_invalid_url(self):
        """Test image with invalid URL."""
        with pytest.raises(ValueError):
            CharacterImage(url="invalid-url")  # type: ignore

    def test_url_hash_generation(self):
        """Test URL hash generation for deduplication."""
        image1 = CharacterImage(url="https://example.com/image.jpg")  # type: ignore
        image2 = CharacterImage(url="https://example.com/image.jpg")  # type: ignore
        image3 = CharacterImage(url="https://example.com/other.jpg")  # type: ignore

        assert image1.url_hash == image2.url_hash
        assert image1.url_hash != image3.url_hash

    def test_size_validation(self):
        """Test image size validation."""
        small_image = CharacterImage(
            url="https://example.com/small.jpg", width=30, height=30  # type: ignore
        )

        large_image = CharacterImage(
            url="https://example.com/large.jpg", width=500, height=600  # type: ignore
        )

        assert not small_image.is_valid_size()
        assert large_image.is_valid_size()


class TestCharacterRelationship:
    """Test CharacterRelationship model."""

    def test_valid_relationship(self):
        """Test creating a valid relationship."""
        relationship = CharacterRelationship(  # type: ignore
            character_name="Roronoa Zoro",
            relationship_type=RelationshipType.CREW_MATE,
            description="First mate of the Straw Hat Pirates",
        )

        assert relationship.character_name == "Roronoa Zoro"
        assert relationship.relationship_type == RelationshipType.CREW_MATE
        assert relationship.confirmed is True

    def test_name_validation(self):
        """Test character name validation."""
        with pytest.raises(ValueError):
            CharacterRelationship(  # type: ignore
                character_name="", relationship_type=RelationshipType.FRIEND
            )

        # Test name cleaning
        relationship = CharacterRelationship(  # type: ignore
            character_name="  Sanji  ", relationship_type=RelationshipType.CREW_MATE
        )
        assert relationship.character_name == "Sanji"


class TestOnePieceSpecificData:
    """Test One Piece specific data model."""

    def test_bounty_formatting(self):
        """Test bounty amount formatting."""
        data = OnePieceSpecificData(current_bounty=1500000000, epithet="Straw Hat")  # type: ignore

        assert data.bounty_formatted == "฿1,500,000,000"

    def test_haki_validation(self):
        """Test Haki types validation."""
        data = OnePieceSpecificData(
            haki_types=["observation", "armament", "invalid_haki", "conqueror"]  # type: ignore
        )

        # Invalid haki should be filtered out
        valid_haki = ["observation", "armament", "conqueror"]
        assert all(haki in valid_haki for haki in data.haki_types)

    def test_devil_fruit_info(self):
        """Test Devil Fruit information."""
        data = OnePieceSpecificData(  # type: ignore
            devil_fruit_name="Gomu Gomu no Mi",
            devil_fruit_type="Paramecia",
            devil_fruit_abilities=["Rubber body", "Gear techniques"],
        )

        assert data.devil_fruit_name == "Gomu Gomu no Mi"
        assert data.devil_fruit_type == "Paramecia"
        assert len(data.devil_fruit_abilities) == 2


class TestAnimeCharacter:
    """Test main AnimeCharacter model."""

    def test_minimal_character_creation(self):
        """Test creating character with minimal required data."""
        character = AnimeCharacter(  # type: ignore
            name="Monkey D. Luffy",
            anime_name="One Piece",
            source_url="https://onepiece.fandom.com/wiki/Monkey_D._Luffy",
        )

        assert character.name == "Monkey D. Luffy"
        assert character.anime_name == "One Piece"
        assert character.status == CharacterStatus.UNKNOWN
        assert character.quality_category == DataQuality.UNKNOWN
        assert len(character.character_id) == 32  # MD5 hash length

    def test_character_with_full_data(self):
        """Test creating character with comprehensive data."""
        # Create image
        image = CharacterImage(  # type: ignore
            url="https://example.com/luffy.jpg",
            image_type=ImageType.PORTRAIT,
            is_primary=True,
        )

        # Create relationship
        relationship = CharacterRelationship(  # type: ignore
            character_name="Roronoa Zoro", relationship_type=RelationshipType.CREW_MATE
        )

        # Create ability
        ability = CharacterAbility(  # type: ignore
            name="Gomu Gomu no Pistol", category="Devil Fruit", is_devil_fruit=True
        )

        # Create One Piece data
        onepiece_data = OnePieceSpecificData(  # type: ignore
            epithet="Straw Hat",
            current_bounty=3000000000,
            crew_name="Straw Hat Pirates",
            haki_types=["observation", "armament", "conqueror"],
        )

        # Create full character
        character = AnimeCharacter(  # type: ignore
            name="Monkey D. Luffy",
            anime_name="One Piece",
            description="Captain of the Straw Hat Pirates",
            age="19",
            gender="Male",
            occupation="Pirate Captain",
            status=CharacterStatus.ALIVE,
            images=[image],
            relationships=[relationship],
            abilities=[ability],
            onepiece_data=onepiece_data,
            source_url="https://onepiece.fandom.com/wiki/Monkey_D._Luffy",
            custom_tags=["main_character", "protagonist", "pirate"],
        )

        assert character.name == "Monkey D. Luffy"
        assert len(character.images) == 1
        assert len(character.relationships) == 1
        assert len(character.abilities) == 1
        assert character.onepiece_data is not None
        assert len(character.custom_tags) == 3

    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        # Minimal character should have low quality
        minimal_character = AnimeCharacter(  # type: ignore
            name="Test Character",
            anime_name="Test Anime",
            source_url="https://example.com/test",
        )
        minimal_score = minimal_character.calculate_quality_score()
        assert 0.0 <= minimal_score <= 0.5

        # Rich character should have higher quality
        rich_character = AnimeCharacter(  # type: ignore
            name="Detailed Character",
            anime_name="Test Anime",
            description="A very detailed character with lots of information and background story.",
            age="25",
            gender="Female",
            occupation="Warrior",
            images=[CharacterImage(url="https://example.com/image.jpg")],  # type: ignore
            relationships=[
                CharacterRelationship(  # type: ignore
                    character_name="Friend", relationship_type=RelationshipType.FRIEND
                )
            ],
            abilities=[CharacterAbility(name="Super Strength")],  # type: ignore
            source_url="https://example.com/test",
        )
        rich_score = rich_character.calculate_quality_score()
        assert rich_score > minimal_score
        assert rich_score >= 0.5

    def test_character_id_generation(self):
        """Test unique character ID generation."""
        char1 = AnimeCharacter(  # type: ignore
            name="Luffy", anime_name="One Piece", source_url="https://example.com/test"
        )

        char2 = AnimeCharacter(  # type: ignore
            name="Luffy", anime_name="One Piece", source_url="https://example.com/test"
        )

        char3 = AnimeCharacter(  # type: ignore
            name="Naruto", anime_name="Naruto", source_url="https://example.com/test"
        )

        # Same name and anime should generate same ID
        assert char1.character_id == char2.character_id

        # Different name or anime should generate different ID
        assert char1.character_id != char3.character_id

    def test_primary_image_selection(self):
        """Test primary image selection logic."""
        # Create images
        general_image = CharacterImage(  # type: ignore
            url="https://example.com/general.jpg", image_type=ImageType.GENERAL
        )

        portrait_image = CharacterImage(  # type: ignore
            url="https://example.com/portrait.jpg", image_type=ImageType.PORTRAIT
        )

        primary_image = CharacterImage(  # type: ignore
            url="https://example.com/primary.jpg",
            image_type=ImageType.FULL_BODY,
            is_primary=True,
        )

        character = AnimeCharacter(  # type: ignore
            name="Test Character",
            anime_name="Test Anime",
            images=[general_image, portrait_image, primary_image],
            source_url="https://example.com/test",
        )

        # Should return the explicitly marked primary image
        assert character.primary_image == primary_image

    def test_image_management(self):
        """Test image addition and management."""
        character = AnimeCharacter(  # type: ignore
            name="Test Character",
            anime_name="Test Anime",
            source_url="https://example.com/test",
        )

        image1 = CharacterImage(url="https://example.com/image1.jpg")  # type: ignore
        image2 = CharacterImage(url="https://example.com/image2.jpg")  # type: ignore
        duplicate_image = CharacterImage(url="https://example.com/image1.jpg")  # type: ignore

        # Should successfully add new images
        assert character.add_image(image1) is True
        assert character.add_image(image2) is True

        # Should reject duplicate URL
        assert character.add_image(duplicate_image) is False

        assert len(character.images) == 2

    def test_relationship_management(self):
        """Test relationship addition and management."""
        character = AnimeCharacter(  # type: ignore
            name="Test Character",
            anime_name="Test Anime",
            source_url="https://example.com/test",
        )

        rel1 = CharacterRelationship(  # type: ignore
            character_name="Friend", relationship_type=RelationshipType.FRIEND
        )

        rel2 = CharacterRelationship(  # type: ignore
            character_name="Enemy", relationship_type=RelationshipType.ENEMY
        )

        duplicate_rel = CharacterRelationship(  # type: ignore
            character_name="Friend", relationship_type=RelationshipType.FRIEND
        )

        # Should successfully add new relationships
        assert character.add_relationship(rel1) is True
        assert character.add_relationship(rel2) is True

        # Should reject duplicate relationship
        assert character.add_relationship(duplicate_rel) is False

        assert len(character.relationships) == 2

    def test_mongodb_document_conversion(self):
        """Test conversion to MongoDB document format."""
        character = AnimeCharacter(  # type: ignore
            name="Test Character",
            anime_name="Test Anime",
            description="Test description",
            source_url="https://example.com/test",
        )

        doc = character.to_mongodb_doc()

        # Should include required fields
        assert doc["name"] == "Test Character"
        assert doc["anime_name"] == "Test Anime"
        assert doc["_character_id"] == character.character_id
        assert "_search_text" in doc
        assert doc["quality_score"] is not None

    def test_search_text_generation(self):
        """Test search text generation."""
        character = AnimeCharacter(  # type: ignore
            name="Monkey D. Luffy",
            anime_name="One Piece",
            description="Pirate captain",
            occupation="Captain",
            custom_tags=["protagonist", "pirate"],
            source_url="https://example.com/test",
        )

        character.add_ability(CharacterAbility(name="Gomu Gomu no Mi"))  # type: ignore
        character.add_relationship(
            CharacterRelationship(  # type: ignore
                character_name="Zoro", relationship_type=RelationshipType.CREW_MATE
            )
        )

        doc = character.to_mongodb_doc()
        search_text = doc["_search_text"]

        # Should contain key information
        assert "monkey d. luffy" in search_text
        assert "one piece" in search_text
        assert "pirate captain" in search_text
        assert "gomu gomu no mi" in search_text
        assert "zoro" in search_text
        assert "protagonist" in search_text


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_onepiece_character(self):
        """Test One Piece character creation utility."""
        character = create_onepiece_character(
            name="Monkey D. Luffy",
            description="Captain of the Straw Hat Pirates",
            epithet="Straw Hat",
            bounty=3000000000,
            devil_fruit="Gomu Gomu no Mi",
            crew="Straw Hat Pirates",
        )

        assert character.name == "Monkey D. Luffy"
        assert character.anime_name == "One Piece"
        assert character.onepiece_data is not None
        assert character.onepiece_data.epithet == "Straw Hat"
        assert character.onepiece_data.current_bounty == 3000000000
        assert character.onepiece_data.devil_fruit_name == "Gomu Gomu no Mi"
        assert character.onepiece_data.crew_name == "Straw Hat Pirates"

    def test_validate_character_data(self):
        """Test character data validation utility."""
        valid_data = {
            "name": "Test Character",
            "anime_name": "Test Anime",
            "source_url": "https://example.com/test",
        }

        character = validate_character_data(valid_data)
        assert isinstance(character, AnimeCharacter)
        assert character.name == "Test Character"

        # Test invalid data
        invalid_data = {
            "name": "",  # Empty name should fail
            "anime_name": "Test Anime",
        }

        with pytest.raises(Exception):  # Should raise validation error
            validate_character_data(invalid_data)


def test_model_integration():
    """Test integration between different models."""
    # Create a complete character with all related models
    character = create_onepiece_character(
        name="Monkey D. Luffy",
        description="Captain of the Straw Hat Pirates",
        epithet="Straw Hat",
        bounty=3000000000,
    )

    # Add image
    image = CharacterImage(  # type: ignore
        url="https://example.com/luffy.jpg",
        image_type=ImageType.PORTRAIT,
        is_primary=True,
    )
    character.add_image(image)

    # Add relationship
    relationship = CharacterRelationship(  # type: ignore
        character_name="Roronoa Zoro", relationship_type=RelationshipType.CREW_MATE
    )
    character.add_relationship(relationship)

    # Add ability
    ability = CharacterAbility(name="Gomu Gomu no Pistol", is_devil_fruit=True)  # type: ignore
    character.add_ability(ability)

    # Update quality assessment
    character.update_quality_assessment()

    # Test that everything works together
    assert character.quality_score > 0.5  # type: ignore Should have good quality
    assert character.primary_image == image
    assert len(character.get_images_by_type(ImageType.PORTRAIT)) == 1
    assert len(character.get_relationships_by_type(RelationshipType.CREW_MATE)) == 1

    # Test MongoDB document conversion
    doc = character.to_mongodb_doc()
    assert doc is not None
    assert doc["quality_score"] > 0.5


if __name__ == "__main__":
    # Run basic tests if script is executed directly
    print("Running basic model tests...")

    # Test character creation
    character = create_onepiece_character(
        name="Monkey D. Luffy", epithet="Straw Hat", bounty=3000000000
    )

    print(f"Created character: {character.name}")
    print(f"Quality score: {character.calculate_quality_score()}")
    print(f"Character ID: {character.character_id}")

    # Test MongoDB document
    doc = character.to_mongodb_doc()
    print(f"MongoDB document keys: {list(doc.keys())}")

    print("Basic tests completed successfully!")
