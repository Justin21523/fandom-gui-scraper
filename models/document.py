# models/document.py
"""
Data Models Module

This module contains all data model definitions for the Fandom scraper,
including character, anime, image, and relationship models with full
Pydantic validation and MongoDB integration.
"""

import hashlib
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse

from pydantic import (
    HttpUrl,
    BaseModel,
    Field,
    field_validator,
    computed_field,
    ConfigDict,
)


class DataQuality(str, Enum):
    """Data quality levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class CharacterStatus(str, Enum):
    """Character status options."""

    ALIVE = "alive"
    DECEASED = "deceased"
    UNKNOWN = "unknown"
    MISSING = "missing"


class ImageType(str, Enum):
    """Character image types."""

    PORTRAIT = "portrait"
    FULL_BODY = "full_body"
    ACTION = "action"
    GROUP = "group"
    THUMBNAIL = "thumbnail"
    BOUNTY_POSTER = "bounty_poster"
    DEVIL_FRUIT = "devil_fruit"
    WEAPON = "weapon"
    GENERAL = "general"


class RelationshipType(str, Enum):
    """Character relationship types."""

    FAMILY = "family"
    FRIEND = "friend"
    ENEMY = "enemy"
    ALLY = "ally"
    CREW_MATE = "crew_mate"
    TEACHER = "teacher"
    STUDENT = "student"
    RIVAL = "rival"
    UNKNOWN = "unknown"


class CharacterImage(BaseModel):
    """
    Model for character images with metadata.

    Represents an image associated with a character, including
    URL, local path, type classification, and metadata.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, use_enum_values=True
    )

    # Image identification
    url: HttpUrl = Field(..., description="Original image URL")
    local_path: Optional[str] = Field(None, description="Local file path")
    filename: Optional[str] = Field(None, description="Generated filename")

    # Image classification
    image_type: ImageType = Field(
        ImageType.GENERAL, description="Image type classification"
    )
    width: Optional[int] = Field(None, ge=1, description="Image width in pixels")
    height: Optional[int] = Field(None, ge=1, description="Image height in pixels")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    format: Optional[str] = Field(None, description="Image format (jpg, png, etc.)")

    # Quality and metadata
    quality_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Image quality score"
    )
    is_primary: bool = Field(False, description="Is this the primary character image")
    alt_text: Optional[str] = Field(None, description="Alternative text description")
    caption: Optional[str] = Field(None, description="Image caption")

    # Download metadata
    downloaded_at: Optional[datetime] = Field(None, description="Download timestamp")
    download_success: bool = Field(False, description="Download success status")
    download_error: Optional[str] = Field(None, description="Download error message")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Validate image URL format."""
        if not str(v).startswith(("http://", "https://")):
            raise ValueError("Image URL must start with http:// or https://")
        return v

    @field_validator("local_path")
    @classmethod
    def validate_local_path(cls, v):
        """Validate local path format."""
        if v and not isinstance(v, str):
            raise ValueError("Local path must be a string")
        return v

    @computed_field
    @property
    def url_hash(self) -> str:
        """Generate hash of image URL for deduplication."""
        return hashlib.md5(str(self.url).encode()).hexdigest()

    @computed_field
    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate image aspect ratio."""
        if self.width and self.height and self.height > 0:
            return round(self.width / self.height, 2)
        return None

    def is_valid_size(self, min_width: int = 50, min_height: int = 50) -> bool:
        """Check if image meets minimum size requirements."""
        if not (self.width and self.height):
            return False
        return self.width >= min_width and self.height >= min_height


class CharacterRelationship(BaseModel):
    """
    Model for character relationships.

    Represents relationships between characters including
    family, friends, enemies, etc.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, use_enum_values=True
    )

    # Related character identification
    character_name: str = Field(
        ..., min_length=1, max_length=200, description="Related character name"
    )
    character_id: Optional[str] = Field(
        None, description="Related character database ID"
    )

    # Relationship details
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    description: Optional[str] = Field(
        None, max_length=500, description="Relationship description"
    )

    # Metadata
    confirmed: bool = Field(True, description="Is relationship confirmed in source")
    source_url: Optional[HttpUrl] = Field(
        None, description="Source URL for relationship"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    @field_validator("character_name")
    @classmethod
    def validate_character_name(cls, v):
        """Validate and clean character name."""
        if not v or not v.strip():
            raise ValueError("Character name cannot be empty")
        return v.strip()


class CharacterAbility(BaseModel):
    """
    Model for character abilities and powers.

    Represents special abilities, techniques, or powers
    that a character possesses.
    """

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # Ability identification
    name: str = Field(..., min_length=1, max_length=200, description="Ability name")
    category: Optional[str] = Field(
        None, max_length=100, description="Ability category"
    )

    # Ability details
    description: Optional[str] = Field(
        None, max_length=2000, description="Ability description"
    )
    power_level: Optional[str] = Field(
        None, max_length=50, description="Power level indicator"
    )

    # Classification
    is_innate: bool = Field(False, description="Is this an innate ability")
    is_learned: bool = Field(True, description="Is this a learned skill")
    is_devil_fruit: bool = Field(False, description="Is this a Devil Fruit power")
    is_haki: bool = Field(False, description="Is this a Haki ability")

    # Metadata
    first_shown: Optional[str] = Field(None, description="When ability was first shown")
    source_url: Optional[HttpUrl] = Field(
        None, description="Source URL for ability info"
    )


class CharacterAppearance(BaseModel):
    """
    Model for character appearances in episodes/chapters.

    Tracks when and where a character appears in the series.
    """

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # Appearance identification
    title: str = Field(
        ..., min_length=1, max_length=300, description="Episode/chapter title"
    )
    episode_number: Optional[int] = Field(None, ge=1, description="Episode number")
    chapter_number: Optional[int] = Field(None, ge=1, description="Chapter number")

    # Appearance details
    appearance_type: str = Field(
        "main", description="Type of appearance (main, cameo, mention)"
    )
    significance: Optional[str] = Field(None, description="Significance of appearance")

    # Metadata
    air_date: Optional[str] = Field(None, description="Air/publication date")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL")

    @field_validator("appearance_type")
    @classmethod
    def validate_appearance_type(cls, v):
        """Validate appearance type."""
        allowed_types = ["main", "supporting", "cameo", "mention", "flashback"]
        if v.lower() not in allowed_types:
            raise ValueError(f"Appearance type must be one of: {allowed_types}")
        return v.lower()


class OnePieceSpecificData(BaseModel):
    """
    One Piece specific character data.

    Contains fields specific to One Piece characters like
    Devil Fruit, bounty, crew affiliation, etc.
    """

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # One Piece specific fields
    epithet: Optional[str] = Field(
        None, max_length=200, description="Character epithet/nickname"
    )

    # Devil Fruit information
    devil_fruit_name: Optional[str] = Field(
        None, max_length=200, description="Devil Fruit name"
    )
    devil_fruit_type: Optional[str] = Field(
        None, max_length=100, description="Devil Fruit type"
    )
    devil_fruit_abilities: List[str] = Field(
        default_factory=list, description="Devil Fruit abilities"
    )

    # Bounty information
    current_bounty: Optional[int] = Field(
        None, ge=0, description="Current bounty amount"
    )
    bounty_currency: str = Field("berries", description="Bounty currency")
    bounty_history: List[int] = Field(
        default_factory=list, description="Historical bounty amounts"
    )

    # Affiliation
    crew_name: Optional[str] = Field(
        None, max_length=200, description="Pirate crew name"
    )
    crew_position: Optional[str] = Field(
        None, max_length=100, description="Position in crew"
    )
    marine_rank: Optional[str] = Field(
        None, max_length=100, description="Marine rank if applicable"
    )

    # Combat abilities
    haki_types: List[str] = Field(
        default_factory=list, description="Types of Haki user can use"
    )
    fighting_style: Optional[str] = Field(
        None, max_length=200, description="Fighting style"
    )
    weapons: List[str] = Field(default_factory=list, description="Weapons used")

    # Physical characteristics
    height_cm: Optional[float] = Field(None, ge=0, description="Height in centimeters")
    birthday: Optional[str] = Field(None, description="Character birthday")
    blood_type: Optional[str] = Field(None, max_length=5, description="Blood type")

    # Story information
    origin: Optional[str] = Field(None, max_length=200, description="Place of origin")
    first_appearance_episode: Optional[int] = Field(
        None, ge=1, description="First appearance episode"
    )
    first_appearance_chapter: Optional[int] = Field(
        None, ge=1, description="First appearance chapter"
    )

    @field_validator("haki_types")
    @classmethod
    def validate_haki_types(cls, v):
        """Validate Haki types."""
        valid_haki = [
            "observation",
            "armament",
            "conqueror",
            "advanced_observation",
            "advanced_armament",
        ]
        return [haki for haki in v if haki.lower().replace(" ", "_") in valid_haki]

    @computed_field
    @property
    def bounty_formatted(self) -> Optional[str]:
        """Format bounty amount with currency."""
        if self.current_bounty is not None:
            return f"฿{self.current_bounty:,}"
        return None


class AnimeCharacter(BaseModel):
    """
    Main character model with complete character information.

    This is the primary model for storing character data with
    all related information including images, relationships,
    abilities, and anime-specific data.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
    )

    # Primary identification
    name: str = Field(
        ..., min_length=1, max_length=200, description="Character full name"
    )
    anime_name: str = Field(
        ..., min_length=1, max_length=200, description="Source anime name"
    )

    # Basic character information
    description: Optional[str] = Field(
        None, max_length=5000, description="Character description"
    )
    age: Optional[str] = Field(None, max_length=50, description="Character age")
    gender: Optional[str] = Field(None, max_length=20, description="Character gender")
    occupation: Optional[str] = Field(
        None, max_length=200, description="Character occupation"
    )
    status: CharacterStatus = Field(
        CharacterStatus.UNKNOWN, description="Character status"
    )

    # Complex data relationships
    images: List[CharacterImage] = Field(
        default_factory=list, description="Character images"
    )
    relationships: List[CharacterRelationship] = Field(
        default_factory=list, description="Character relationships"
    )
    abilities: List[CharacterAbility] = Field(
        default_factory=list, description="Character abilities"
    )
    appearances: List[CharacterAppearance] = Field(
        default_factory=list, description="Character appearances"
    )

    # Anime-specific data
    onepiece_data: Optional[OnePieceSpecificData] = Field(
        None, description="One Piece specific data"
    )

    # Quality and metadata
    source_url: HttpUrl = Field(..., description="Original source URL")
    quality_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Data quality score"
    )
    quality_category: DataQuality = Field(
        DataQuality.UNKNOWN, description="Quality category"
    )

    # User customization
    custom_tags: List[str] = Field(
        default_factory=list, description="User-defined tags"
    )
    user_notes: Optional[str] = Field(None, max_length=2000, description="User notes")
    is_favorite: bool = Field(False, description="Is character marked as favorite")

    # Timestamps
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Scraping timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # Internal metadata
    scraper_version: str = Field("1.0", description="Scraper version used")
    extraction_method: str = Field("automated", description="Extraction method")

    @field_validator("name", "anime_name")
    @classmethod
    def validate_required_text(cls, v):
        """Validate required text fields."""
        if not v or not v.strip():
            raise ValueError("Required text field cannot be empty")
        # Clean up common text issues
        cleaned = re.sub(r"\s+", " ", v.strip())
        return cleaned

    @field_validator("custom_tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean custom tags."""
        if not v:
            return []
        # Remove duplicates and empty tags
        cleaned_tags = []
        for tag in v:
            if tag and tag.strip():
                clean_tag = tag.strip().lower()
                if clean_tag not in cleaned_tags:
                    cleaned_tags.append(clean_tag)
        return cleaned_tags

    @computed_field
    @property
    def character_id(self) -> str:
        """Generate unique character ID based on name and anime."""
        # Create a unique ID from name and anime
        source_text = f"{self.anime_name}:{self.name}".lower()
        return hashlib.md5(source_text.encode()).hexdigest()

    @computed_field
    @property
    def primary_image(self) -> Optional[CharacterImage]:
        """Get primary character image."""
        # Look for explicitly marked primary image
        primary_images = [img for img in self.images if img.is_primary]
        if primary_images:
            return primary_images[0]

        # Fall back to first portrait image
        portrait_images = [
            img for img in self.images if img.image_type == ImageType.PORTRAIT
        ]
        if portrait_images:
            return portrait_images[0]

        # Fall back to any image
        if self.images:
            return self.images[0]

        return None

    @computed_field
    @property
    def relationship_summary(self) -> Dict[str, int]:
        """Get summary of relationship types."""
        summary = {}
        for relationship in self.relationships:
            rel_type = relationship.relationship_type
            summary[rel_type] = summary.get(rel_type, 0) + 1
        return summary

    def calculate_quality_score(self) -> float:
        """
        Calculate comprehensive data quality score.

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0

        # Required fields (30% of score)
        if self.name and len(self.name.strip()) > 1:
            score += 0.15
        if self.anime_name and len(self.anime_name.strip()) > 1:
            score += 0.15

        # Description quality (20% of score)
        if self.description:
            if len(self.description) > 50:
                score += 0.10
            if len(self.description) > 200:
                score += 0.10

        # Basic information completeness (20% of score)
        basic_fields = [self.age, self.gender, self.occupation]
        filled_basic = sum(1 for field in basic_fields if field and field.strip())
        score += (filled_basic / len(basic_fields)) * 0.20

        # Complex data richness (20% of score)
        if self.images:
            score += min(0.08, len(self.images) * 0.02)  # Up to 0.08 for images
        if self.relationships:
            score += min(
                0.06, len(self.relationships) * 0.02
            )  # Up to 0.06 for relationships
        if self.abilities:
            score += min(0.06, len(self.abilities) * 0.02)  # Up to 0.06 for abilities

        # Source and metadata quality (10% of score)
        if self.source_url:
            score += 0.05
        if self.appearances:
            score += 0.05

        return min(1.0, round(score, 3))

    def update_quality_assessment(self):
        """Update quality score and category."""
        self.quality_score = self.calculate_quality_score()

        if self.quality_score >= 0.8:
            self.quality_category = DataQuality.HIGH
        elif self.quality_score >= 0.5:
            self.quality_category = DataQuality.MEDIUM
        else:
            self.quality_category = DataQuality.LOW

        self.updated_at = datetime.now(timezone.utc)

    def add_image(self, image: CharacterImage) -> bool:
        """
        Add an image to the character.

        Args:
            image: CharacterImage to add

        Returns:
            True if image was added, False if duplicate
        """
        # Check for duplicate URLs
        existing_urls = {img.url for img in self.images}
        if image.url in existing_urls:
            return False

        self.images.append(image)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def add_relationship(self, relationship: CharacterRelationship) -> bool:
        """
        Add a relationship to the character.

        Args:
            relationship: CharacterRelationship to add

        Returns:
            True if relationship was added, False if duplicate
        """
        # Check for duplicate relationships
        for existing in self.relationships:
            if (
                existing.character_name == relationship.character_name
                and existing.relationship_type == relationship.relationship_type
            ):
                return False

        self.relationships.append(relationship)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def add_ability(self, ability: CharacterAbility) -> bool:
        """
        Add an ability to the character.

        Args:
            ability: CharacterAbility to add

        Returns:
            True if ability was added, False if duplicate
        """
        # Check for duplicate abilities
        existing_names = {ab.name.lower() for ab in self.abilities}
        if ability.name.lower() in existing_names:
            return False

        self.abilities.append(ability)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def get_images_by_type(self, image_type: ImageType) -> List[CharacterImage]:
        """Get all images of a specific type."""
        return [img for img in self.images if img.image_type == image_type]

    def get_relationships_by_type(
        self, rel_type: RelationshipType
    ) -> List[CharacterRelationship]:
        """Get all relationships of a specific type."""
        return [rel for rel in self.relationships if rel.relationship_type == rel_type]

    def to_dict(
        self, exclude_none: bool = True, include_computed: bool = False
    ) -> Dict[str, Any]:
        """
        Convert character to dictionary format.

        Args:
            exclude_none: Exclude None values
            include_computed: Include computed fields

        Returns:
            Dictionary representation
        """
        data = self.model_dump(exclude_none=exclude_none, by_alias=True)

        if include_computed:
            data["character_id"] = self.character_id
            data["primary_image"] = (
                self.primary_image.model_dump() if self.primary_image else None
            )
            data["relationship_summary"] = self.relationship_summary

        return data

    def to_mongodb_doc(self) -> Dict[str, Any]:
        """
        Convert to MongoDB document format.

        Returns:
            Dictionary suitable for MongoDB storage
        """
        doc = self.to_dict(exclude_none=True, include_computed=True)

        # Ensure quality score is up to date
        if not doc.get("quality_score"):
            doc["quality_score"] = self.calculate_quality_score()

        # Add indexable fields
        doc["_character_id"] = self.character_id
        doc["_search_text"] = self._generate_search_text()

        return doc

    def _generate_search_text(self) -> str:
        """Generate searchable text from character data."""
        search_parts = [
            self.name,
            self.anime_name,
            self.description or "",
            self.occupation or "",
            " ".join(self.custom_tags),
        ]

        # Add ability names
        search_parts.extend([ability.name for ability in self.abilities])

        # Add relationship character names
        search_parts.extend([rel.character_name for rel in self.relationships])

        # Add One Piece specific data
        if self.onepiece_data:
            if self.onepiece_data.epithet:
                search_parts.append(self.onepiece_data.epithet)
            if self.onepiece_data.crew_name:
                search_parts.append(self.onepiece_data.crew_name)
            if self.onepiece_data.devil_fruit_name:
                search_parts.append(self.onepiece_data.devil_fruit_name)

        return " ".join(filter(None, search_parts)).lower()


class AnimeSeriesInfo(BaseModel):
    """
    Model for anime series information.

    Contains metadata about anime series including
    title, description, and character statistics.
    """

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # Basic series information
    title: str = Field(..., min_length=1, max_length=300, description="Anime title")
    title_english: Optional[str] = Field(
        None, max_length=300, description="English title"
    )
    title_japanese: Optional[str] = Field(
        None, max_length=300, description="Japanese title"
    )

    # Series details
    synopsis: Optional[str] = Field(
        None, max_length=10000, description="Anime synopsis"
    )
    genres: List[str] = Field(default_factory=list, description="Anime genres")
    studio: Optional[str] = Field(None, max_length=200, description="Animation studio")

    # Publication information
    release_date: Optional[str] = Field(None, description="Release date")
    end_date: Optional[str] = Field(None, description="End date (if completed)")
    episode_count: Optional[int] = Field(None, ge=1, description="Total episode count")
    season_count: Optional[int] = Field(None, ge=1, description="Number of seasons")

    # Status and metadata
    status: Optional[str] = Field(
        None, description="Series status (ongoing, completed, etc.)"
    )
    fandom_url: HttpUrl = Field(..., description="Fandom wiki URL")

    # Character statistics
    character_count: int = Field(
        default=0, ge=0, description="Number of characters scraped"
    )
    main_character_count: int = Field(
        default=0, ge=0, description="Number of main characters"
    )

    # Quality metrics
    data_completeness: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Data completeness score"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    @computed_field
    @property
    def series_id(self) -> str:
        """Generate unique series ID."""
        return hashlib.md5(self.title.lower().encode()).hexdigest()


# Model registry for easy access
MODEL_REGISTRY = {
    "character": AnimeCharacter,
    "anime": AnimeSeriesInfo,
    "image": CharacterImage,
    "relationship": CharacterRelationship,
    "ability": CharacterAbility,
    "appearance": CharacterAppearance,
    "onepiece_data": OnePieceSpecificData,
}


def get_model_class(model_name: str) -> Optional[BaseModel]:
    """
    Get model class by name.

    Args:
        model_name: Name of the model

    Returns:
        Model class or None if not found
    """
    return MODEL_REGISTRY.get(model_name)


def validate_character_data(data: Dict[str, Any]) -> AnimeCharacter:
    """
    Validate and create character from dictionary data.

    Args:
        data: Raw character data

    Returns:
        Validated AnimeCharacter instance

    Raises:
        ValidationError: If data is invalid
    """
    return AnimeCharacter(**data)


def create_onepiece_character(
    name: str,
    description: str = None,  # type: ignore
    epithet: str = None,  # type: ignore
    bounty: int = None,  # type: ignore
    devil_fruit: str = None,  # type: ignore
    crew: str = None,  # type: ignore
    **kwargs,
) -> AnimeCharacter:
    """
    Convenience function to create One Piece character.

    Args:
        name: Character name
        description: Character description
        epithet: Character epithet
        bounty: Current bounty
        devil_fruit: Devil Fruit name
        crew: Crew name
        **kwargs: Additional character data

    Returns:
        Configured AnimeCharacter with One Piece data
    """
    # Create One Piece specific data
    onepiece_data = OnePieceSpecificData()  # type: ignore
    if epithet:
        onepiece_data.epithet = epithet
    if bounty:
        onepiece_data.current_bounty = bounty
    if devil_fruit:
        onepiece_data.devil_fruit_name = devil_fruit
    if crew:
        onepiece_data.crew_name = crew

    # Create character
    character_data = {
        "name": name,
        "anime_name": "One Piece",
        "description": description,
        "onepiece_data": onepiece_data,
        "source_url": f'https://onepiece.fandom.com/wiki/{name.replace(" ", "_")}',
        **kwargs,
    }

    return AnimeCharacter(**character_data)
