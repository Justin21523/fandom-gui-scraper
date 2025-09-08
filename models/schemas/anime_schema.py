# models/schemas/anime_schema.py
"""
Anime series data schema definition using Pydantic for validation.

This module defines the data structure for anime series information
with comprehensive validation rules and metadata management.
"""

from pydantic import BaseModel, field_validator, Field, HttpUrl
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import re


class AnimeStatus(str, Enum):
    """Enumeration for anime series status."""

    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"
    CANCELLED = "cancelled"
    UPCOMING = "upcoming"
    UNKNOWN = "unknown"


class AnimeType(str, Enum):
    """Enumeration for anime series types."""

    TV_SERIES = "tv_series"
    MOVIE = "movie"
    OVA = "ova"
    ONA = "ona"
    SPECIAL = "special"
    MUSIC_VIDEO = "music_video"
    UNKNOWN = "unknown"


class AnimeSchema(BaseModel):
    """
    Pydantic schema for anime series data validation and serialization.

    This schema defines the structure for anime series information including
    metadata, production details, and statistical information.

    Attributes:
        title: Primary anime title (required)
        title_english: English title translation
        title_japanese: Original Japanese title
        title_romaji: Romanized Japanese title
        synopsis: Plot summary or description
        genres: List of genre classifications
        themes: List of thematic elements
        studio: Animation studio name
        producer: Production company
        director: Director name
        release_date: Initial release/air date
        end_date: Series completion date
        episode_count: Total number of episodes
        duration_minutes: Average episode duration
        anime_type: Type of anime production
        status: Current production status
        rating: Content rating (G, PG, PG-13, R, etc.)
        score: User rating score
        popularity_rank: Popularity ranking
        fandom_url: Fandom wiki URL
        official_url: Official website URL
        character_count: Number of characters scraped
        episode_data_count: Number of episodes with data
        last_scraped: Last scraping timestamp
        scraped_at: Initial scraping timestamp
        updated_at: Last update timestamp
        data_quality_score: Quality assessment score
        custom_tags: User-defined tags

    Example:
        >>> anime_data = {
        ...     "title": "One Piece",
        ...     "title_english": "One Piece",
        ...     "title_japanese": "ワンピース",
        ...     "synopsis": "Follows the adventures of Monkey D. Luffy...",
        ...     "genres": ["Action", "Adventure", "Comedy"],
        ...     "studio": "Toei Animation",
        ...     "status": "ongoing",
        ...     "episode_count": 1070
        ... }
        >>> anime = AnimeSchema(**anime_data)
        >>> print(anime.title)
        "One Piece"
    """

    # Title fields (required primary title)
    title: str = Field(
        ..., min_length=1, max_length=300, description="Primary anime title"
    )
    title_english: Optional[str] = Field(
        None, max_length=300, description="English title"
    )
    title_japanese: Optional[str] = Field(
        None, max_length=300, description="Japanese title"
    )
    title_romaji: Optional[str] = Field(
        None, max_length=300, description="Romanized title"
    )

    # Content information
    synopsis: Optional[str] = Field(None, max_length=10000, description="Plot synopsis")
    genres: List[str] = Field(default_factory=list, description="Genre classifications")
    themes: List[str] = Field(default_factory=list, description="Thematic elements")

    # Production information
    studio: Optional[str] = Field(None, max_length=200, description="Animation studio")
    producer: Optional[str] = Field(
        None, max_length=200, description="Production company"
    )
    director: Optional[str] = Field(None, max_length=200, description="Director name")

    # Release information
    release_date: Optional[Union[date, str]] = Field(None, description="Release date")
    end_date: Optional[Union[date, str]] = Field(None, description="End date")

    # Technical details
    episode_count: Optional[int] = Field(None, ge=0, description="Total episodes")
    duration_minutes: Optional[int] = Field(
        None, ge=1, le=300, description="Episode duration"
    )
    anime_type: AnimeType = Field(default=AnimeType.UNKNOWN, description="Anime type")
    status: AnimeStatus = Field(
        default=AnimeStatus.UNKNOWN, description="Production status"
    )

    # Ratings and rankings
    rating: Optional[str] = Field(None, max_length=10, description="Content rating")
    score: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="User rating score"
    )
    popularity_rank: Optional[int] = Field(None, ge=1, description="Popularity ranking")

    # URLs and references
    fandom_url: Union[str, HttpUrl] = Field(..., description="Fandom wiki URL")
    official_url: Optional[Union[str, HttpUrl]] = Field(
        None, description="Official website"
    )

    # Statistical data
    character_count: int = Field(default=0, ge=0, description="Number of characters")
    episode_data_count: int = Field(default=0, ge=0, description="Episodes with data")

    # Timestamps
    last_scraped: Optional[datetime] = Field(None, description="Last scraping time")
    scraped_at: datetime = Field(
        default_factory=datetime.utcnow, description="Initial scraping time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update time"
    )

    # Quality and organization
    data_quality_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Quality score"
    )
    custom_tags: List[str] = Field(
        default_factory=list, description="User-defined tags"
    )

    class Config:
        """Pydantic model configuration."""

        allow_mutation = True
        use_enum_values = True
        validate_assignment = True
        schema_extra = {
            "example": {
                "title": "One Piece",
                "title_english": "One Piece",
                "title_japanese": "ワンピース",
                "synopsis": "Follows the adventures of Monkey D. Luffy and his crew",
                "genres": ["Action", "Adventure", "Comedy", "Drama"],
                "studio": "Toei Animation",
                "status": "ongoing",
                "anime_type": "tv_series",
                "episode_count": 1070,
                "duration_minutes": 24,
                "score": 9.2,
                "fandom_url": "https://onepiece.fandom.com/wiki/One_Piece",
                "character_count": 1247,
                "data_quality_score": 0.95,
            }
        }

    @field_validator("title", "title_english", "title_japanese", "title_romaji")
    def clean_title_fields(cls, value):
        """
        Clean and normalize title fields.

        Args:
            value: Title string

        Returns:
            Cleaned title with normalized formatting
        """
        if value:
            # Remove extra whitespace
            cleaned = re.sub(r"\s+", " ", value.strip())
            # Remove special wiki markup
            cleaned = re.sub(r"\[\[|\]\]", "", cleaned)
            return cleaned
        return value

    @field_validator("synopsis")
    def clean_synopsis(cls, value):
        """
        Clean synopsis text content.

        Args:
            value: Synopsis text

        Returns:
            Cleaned synopsis text
        """
        if value:
            # Remove citation markers
            cleaned = re.sub(r"\[[\d\w\s]+\]", "", value)
            # Remove wiki markup
            cleaned = re.sub(r"\{\{[^}]+\}\}", "", cleaned)
            # Normalize whitespace
            cleaned = re.sub(r"\s+", " ", cleaned.strip())
            return cleaned
        return value

    @field_validator("genres", "themes")
    def clean_string_lists(cls, value):
        """
        Clean and deduplicate string lists.

        Args:
            value: List of strings

        Returns:
            Cleaned list without duplicates
        """
        if value:
            cleaned_list = []
            seen = set()

            for item in value:
                if isinstance(item, str) and item.strip():
                    cleaned = item.strip().title()  # Normalize to title case
                    if cleaned.lower() not in seen:
                        cleaned_list.append(cleaned)
                        seen.add(cleaned.lower())

            return cleaned_list
        return value

    @field_validator("release_date", "end_date")
    def validate_dates(cls, value):
        """
        Validate and normalize date fields.

        Args:
            value: Date string or date object

        Returns:
            Normalized date string or None
        """
        if value:
            if isinstance(value, date):
                return value.isoformat()
            elif isinstance(value, str):
                # Try to parse common date formats
                date_patterns = [
                    r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
                    r"(\d{1,2})/(\d{1,2})/(\d{4})",  # MM/DD/YYYY
                    r"(\d{4})",  # Just year
                ]

                for pattern in date_patterns:
                    match = re.search(pattern, value.strip())
                    if match:
                        if len(match.groups()) == 3:
                            try:
                                if pattern.startswith(r"(\d{4})"):  # YYYY-MM-DD
                                    year, month, day = match.groups()
                                else:  # MM/DD/YYYY
                                    month, day, year = match.groups()

                                # Validate date
                                test_date = date(int(year), int(month), int(day))
                                return test_date.isoformat()
                            except ValueError:
                                continue
                        elif len(match.groups()) == 1:  # Just year
                            year = match.group(1)
                            return f"{year}-01-01"

                # If no pattern matches, return original value
                return value.strip()
        return value

    @field_validator("score")
    def validate_score(cls, value):
        """
        Validate score is within acceptable range.

        Args:
            value: Score value

        Returns:
            Validated score rounded to 1 decimal place
        """
        if value is not None:
            return round(float(value), 1)
        return value

    def calculate_quality_score(self) -> float:
        """
        Calculate data quality score based on completeness and detail.

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0

        # Required fields
        if self.title and len(self.title.strip()) > 0:
            score += 0.2
        if self.fandom_url:
            score += 0.1

        # Important optional fields
        if self.synopsis and len(self.synopsis.strip()) > 50:
            score += 0.15
            # Bonus for detailed synopsis
            if len(self.synopsis) > 200:
                score += 0.05

        if self.genres and len(self.genres) > 0:
            score += 0.1

        if self.studio and self.studio.strip():
            score += 0.1

        # Production details
        detail_fields = [
            self.title_english,
            self.title_japanese,
            self.director,
            self.producer,
            self.release_date,
        ]
        filled_details = sum(1 for field in detail_fields if field)
        score += (filled_details / len(detail_fields)) * 0.15

        # Technical information
        if self.episode_count and self.episode_count > 0:
            score += 0.05
        if self.duration_minutes and self.duration_minutes > 0:
            score += 0.05
        if self.status != AnimeStatus.UNKNOWN:
            score += 0.05

        # Data richness bonuses
        if self.character_count and self.character_count > 10:
            score += 0.05
        if self.score and self.score > 0:
            score += 0.05

        return min(round(score, 3), 1.0)

    def update_character_count(self, count: int):
        """
        Update character count and refresh timestamp.

        Args:
            count: New character count
        """
        self.character_count = max(0, count)
        self.updated_at = datetime.utcnow()

    def update_scraping_timestamp(self):
        """Update the last scraped timestamp."""
        self.last_scraped = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_genre(self, genre: str):
        """
        Add a genre if it doesn't already exist.

        Args:
            genre: Genre to add
        """
        if genre and genre.strip():
            cleaned_genre = genre.strip().title()
            if cleaned_genre not in self.genres:
                self.genres.append(cleaned_genre)

    def add_custom_tag(self, tag: str):
        """
        Add a custom tag if it doesn't already exist.

        Args:
            tag: Tag to add
        """
        if tag and tag.strip() and tag not in self.custom_tags:
            self.custom_tags.append(tag.strip())

    def get_display_title(self) -> str:
        """
        Get the best available title for display purposes.

        Returns:
            Primary title, English title, or Japanese title in order of preference
        """
        return (
            self.title or self.title_english or self.title_japanese or "Unknown Anime"
        )

    def is_ongoing(self) -> bool:
        """Check if the anime is currently ongoing."""
        return self.status == AnimeStatus.ONGOING

    def is_completed(self) -> bool:
        """Check if the anime is completed."""
        return self.status == AnimeStatus.COMPLETED

    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """
        Convert model to dictionary format.

        Args:
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary representation of the anime
        """
        return self.dict(exclude_none=exclude_none, by_alias=True)

    def to_mongodb_doc(self) -> Dict[str, Any]:
        """
        Convert to MongoDB document format.

        Returns:
            Dictionary suitable for MongoDB storage
        """
        doc = self.to_dict(exclude_none=True)

        # Ensure quality score is calculated
        if not doc.get("data_quality_score"):
            doc["data_quality_score"] = self.calculate_quality_score()

        return doc


class AnimeSearchResult(BaseModel):
    """Schema for anime search results with metadata."""

    anime: AnimeSchema
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    matched_fields: List[str] = Field(default_factory=list)
    highlight_snippets: Dict[str, str] = Field(default_factory=dict)


class AnimeStatistics(BaseModel):
    """Schema for anime statistics and analytics."""

    anime_id: str = Field(..., description="Anime identifier")
    character_count: int = Field(default=0, description="Total characters")
    episode_count: int = Field(default=0, description="Total episodes")
    average_quality_score: float = Field(
        default=0.0, description="Average data quality"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    popular_characters: List[str] = Field(default_factory=list)
    genre_distribution: Dict[str, int] = Field(default_factory=dict)
