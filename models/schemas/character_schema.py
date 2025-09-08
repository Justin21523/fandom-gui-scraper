# models/schemas/character_schema.py
"""
Character data schema definition using Pydantic for validation.

This module defines the data structure for anime character information
with comprehensive validation rules and data cleaning capabilities.
"""

from pydantic import BaseModel, field_validator, Field, HttpUrl
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import re


class CharacterSchema(BaseModel):
    """
    Pydantic schema for character data validation and serialization.

    This schema defines the structure and validation rules for character
    information extracted from Fandom wikis, ensuring data consistency
    and quality across the application.

    Attributes:
        name: Character's full name (required)
        anime: Source anime series name (required)
        description: Character description text
        age: Character age (as string to handle ranges like "17-19")
        gender: Character gender
        occupation: Character's job or role
        status: Character status (alive, deceased, unknown)
        abilities: List of character abilities or powers
        relationships: Dictionary of relationship types to character names
        image_urls: List of character image URLs
        local_image_paths: List of local file paths for downloaded images
        source_url: Original wiki page URL
        scraped_at: Timestamp when data was collected
        updated_at: Timestamp when data was last modified
        data_quality_score: Quality assessment score (0.0-1.0)
        custom_tags: User-defined tags for categorization

    Example:
        >>> character_data = {
        ...     "name": "Monkey D. Luffy",
        ...     "anime": "One Piece",
        ...     "age": "19",
        ...     "description": "Captain of the Straw Hat Pirates",
        ...     "abilities": ["Gomu Gomu no Mi", "Haki"],
        ...     "source_url": "https://onepiece.fandom.com/wiki/Monkey_D._Luffy"
        ... }
        >>> character = CharacterSchema(**character_data)
        >>> print(character.name)
        "Monkey D. Luffy"
    """

    # Required fields
    name: str = Field(
        ..., min_length=1, max_length=200, description="Character's full name"
    )
    anime: str = Field(
        ..., min_length=1, max_length=200, description="Source anime series"
    )

    # Basic information fields
    description: Optional[str] = Field(
        None, max_length=5000, description="Character description"
    )
    age: Optional[str] = Field(None, max_length=50, description="Character age")
    gender: Optional[str] = Field(None, max_length=20, description="Character gender")
    occupation: Optional[str] = Field(
        None, max_length=200, description="Character occupation"
    )
    status: Optional[str] = Field(None, max_length=50, description="Character status")

    # Complex data fields
    abilities: List[str] = Field(
        default_factory=list, description="Character abilities"
    )
    relationships: Dict[str, str] = Field(
        default_factory=dict, description="Character relationships"
    )

    # Media fields
    image_urls: List[Union[str, HttpUrl]] = Field(
        default_factory=list, description="Image URLs"
    )
    local_image_paths: List[str] = Field(
        default_factory=list, description="Local image paths"
    )

    # Metadata fields
    source_url: Union[str, HttpUrl] = Field(..., description="Original wiki page URL")
    scraped_at: datetime = Field(
        default_factory=datetime.utcnow, description="Scraping timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    data_quality_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Quality score"
    )
    custom_tags: List[str] = Field(
        default_factory=list, description="User-defined tags"
    )

    class Config:
        """Pydantic model configuration."""

        # Allow field updates after model creation
        allow_mutation = True
        # Use enum values instead of enum objects
        use_enum_values = True
        # Validate assignment
        validate_assignment = True
        # JSON schema extras
        schema_extra = {
            "example": {
                "name": "Monkey D. Luffy",
                "anime": "One Piece",
                "description": "Captain of the Straw Hat Pirates and protagonist of One Piece",
                "age": "19",
                "gender": "Male",
                "occupation": "Pirate Captain",
                "status": "Alive",
                "abilities": ["Gomu Gomu no Mi", "Haki", "Enhanced Physical Strength"],
                "relationships": {
                    "crew": "Straw Hat Pirates",
                    "brother": "Portgas D. Ace",
                    "grandfather": "Monkey D. Garp",
                },
                "source_url": "https://onepiece.fandom.com/wiki/Monkey_D._Luffy",
                "data_quality_score": 0.95,
                "custom_tags": ["protagonist", "main_character", "captain"],
            }
        }

    @field_validator("name", "anime")
    def clean_text_fields(cls, value):
        """
        Clean and normalize primary text fields.

        Args:
            value: Input text value

        Returns:
            Cleaned text with normalized whitespace
        """
        if value:
            # Remove extra whitespace and normalize
            cleaned = re.sub(r"\s+", " ", value.strip())
            # Remove unwanted characters but keep essential punctuation
            cleaned = re.sub(r"[^\w\s\.\-\'\(\)&]", "", cleaned)
            return cleaned
        return value

    @field_validator("description")
    def clean_description(cls, value):
        """
        Clean character description text.

        Args:
            value: Description text

        Returns:
            Cleaned description with normalized formatting
        """
        if value:
            # Remove citation markers like [1], [citation needed]
            cleaned = re.sub(r"\[[\d\w\s]+\]", "", value)
            # Normalize whitespace
            cleaned = re.sub(r"\s+", " ", cleaned.strip())
            # Remove empty parentheses and brackets
            cleaned = re.sub(r"\(\s*\)|\[\s*\]", "", cleaned)
            return cleaned
        return value

    @field_validator("age")
    def validate_age(cls, value):
        """
        Validate and normalize age information.

        Args:
            value: Age string

        Returns:
            Normalized age string

        Note:
            Accepts various formats: "19", "17-19", "Unknown", "Immortal"
        """
        if value:
            # Clean and normalize age string
            cleaned = value.strip()
            # Allow numeric ages, ranges, and special cases
            if re.match(
                r"^(\d+|\d+-\d+|Unknown|Immortal|Ageless)$", cleaned, re.IGNORECASE
            ):
                return cleaned
            # Extract numbers from complex age descriptions
            numbers = re.findall(r"\d+", cleaned)
            if numbers:
                if len(numbers) == 1:
                    return numbers[0]
                elif len(numbers) >= 2:
                    return f"{numbers[0]}-{numbers[1]}"
            return "Unknown"
        return value

    @field_validator("abilities")
    def clean_abilities(cls, abilities):
        """
        Clean and deduplicate abilities list.

        Args:
            abilities: List of ability strings

        Returns:
            Cleaned list with duplicates removed
        """
        if abilities:
            cleaned_abilities = []
            seen = set()

            for ability in abilities:
                if isinstance(ability, str) and ability.strip():
                    # Clean ability name
                    cleaned = re.sub(r"\s+", " ", ability.strip())
                    # Avoid duplicates (case-insensitive)
                    if cleaned.lower() not in seen:
                        cleaned_abilities.append(cleaned)
                        seen.add(cleaned.lower())

            return cleaned_abilities
        return abilities

    @field_validator("image_urls")
    def validate_image_urls(cls, urls):
        """
        Validate and clean image URLs.

        Args:
            urls: List of image URL strings

        Returns:
            List of valid URLs
        """
        if urls:
            valid_urls = []
            for url in urls:
                if isinstance(url, str) and url.strip():
                    url = url.strip()
                    # Basic URL validation
                    if url.startswith(("http://", "https://")) or url.startswith("/"):
                        valid_urls.append(url)
            return valid_urls
        return urls

    @field_validator("data_quality_score")
    def validate_quality_score(cls, score):
        """
        Ensure quality score is within valid range.

        Args:
            score: Quality score value

        Returns:
            Validated score or None
        """
        if score is not None:
            if 0.0 <= score <= 1.0:
                return round(score, 3)  # Round to 3 decimal places
            else:
                return None  # Invalid score becomes None
        return score

    def calculate_quality_score(self) -> float:
        """
        Calculate data quality score based on field completeness and content quality.

        Returns:
            Quality score between 0.0 and 1.0

        Algorithm:
            - Base score starts at 0.0
            - Each filled field adds points based on importance
            - Content quality factors (length, detail) provide bonuses
            - Maximum possible score is 1.0
        """
        score = 0.0

        # Required fields (base score)
        if self.name and len(self.name.strip()) > 0:
            score += 0.2
        if self.anime and len(self.anime.strip()) > 0:
            score += 0.2

        # Important optional fields
        if self.description and len(self.description.strip()) > 20:
            score += 0.15
            # Bonus for detailed descriptions
            if len(self.description) > 100:
                score += 0.05

        if self.age and self.age.strip().lower() != "unknown":
            score += 0.1

        # Additional information fields
        optional_fields = [self.gender, self.occupation, self.status]
        filled_optional = sum(1 for field in optional_fields if field and field.strip())
        score += (filled_optional / len(optional_fields)) * 0.15

        # Complex data bonuses
        if self.abilities and len(self.abilities) > 0:
            score += 0.05
            # Bonus for multiple abilities
            if len(self.abilities) >= 3:
                score += 0.05

        if self.relationships and len(self.relationships) > 0:
            score += 0.05

        if self.image_urls and len(self.image_urls) > 0:
            score += 0.05

        # Ensure score doesn't exceed 1.0
        return min(round(score, 3), 1.0)

    def update_timestamp(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.utcnow()

    def add_custom_tag(self, tag: str):
        """
        Add a custom tag if it doesn't already exist.

        Args:
            tag: Tag to add
        """
        if tag and tag.strip() and tag not in self.custom_tags:
            self.custom_tags.append(tag.strip())

    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """
        Convert model to dictionary format.

        Args:
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary representation of the character
        """
        return self.dict(exclude_none=exclude_none, by_alias=True)

    def to_mongodb_doc(self) -> Dict[str, Any]:
        """
        Convert to MongoDB document format.

        Returns:
            Dictionary suitable for MongoDB storage
        """
        doc = self.to_dict(exclude_none=True)

        # Convert datetime objects to MongoDB-compatible format
        if isinstance(doc.get("scraped_at"), datetime):
            doc["scraped_at"] = doc["scraped_at"]
        if isinstance(doc.get("updated_at"), datetime):
            doc["updated_at"] = doc["updated_at"]

        # Ensure quality score is calculated
        if not doc.get("data_quality_score"):
            doc["data_quality_score"] = self.calculate_quality_score()

        return doc


class CharacterSearchResult(BaseModel):
    """
    Schema for character search results with additional metadata.

    Used for search operations that return characters with relevance scores
    and highlighting information.
    """

    character: CharacterSchema
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Search relevance score"
    )
    matched_fields: List[str] = Field(
        default_factory=list, description="Fields that matched search"
    )
    highlight_snippets: Dict[str, str] = Field(
        default_factory=dict, description="Highlighted text snippets"
    )


class CharacterBatchOperation(BaseModel):
    """
    Schema for batch operations on multiple characters.

    Used for bulk create, update, or delete operations.
    """

    operation_type: str = Field(
        ..., pattern=r"^(create|update|delete)$", description="Operation type"
    )
    characters: List[CharacterSchema] = Field(..., description="Characters to process")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Operation options"
    )
