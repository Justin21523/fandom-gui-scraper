"""
Episode/Chapter data models for anime/manga series.

This module defines Pydantic models for storing episode and chapter information
scraped from Fandom wikis.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl, Field, validator, computed_field
import hashlib


class EpisodeType(str, Enum):
    """Episode type classification."""
    TV_EPISODE = "tv_episode"
    OVA = "ova"
    MOVIE = "movie"
    SPECIAL = "special"
    FILLER = "filler"
    RECAP = "recap"
    UNKNOWN = "unknown"


class ChapterType(str, Enum):
    """Chapter type classification."""
    MANGA_CHAPTER = "manga_chapter"
    LIGHT_NOVEL = "light_novel"
    WEB_NOVEL = "web_novel"
    ONE_SHOT = "one_shot"
    SPECIAL = "special"
    UNKNOWN = "unknown"


class EpisodeImage(BaseModel):
    """
    Episode screenshot or promotional image.

    Attributes:
        url: Image URL
        local_path: Path to downloaded image
        caption: Image caption/description
        is_thumbnail: Whether this is a thumbnail image
        timestamp: Timestamp in episode (if screenshot)
        scene_description: Description of the scene
    """
    url: HttpUrl
    local_path: Optional[str] = None
    caption: Optional[str] = None
    is_thumbnail: bool = False
    timestamp: Optional[str] = None  # Format: "HH:MM:SS" or "MM:SS"
    scene_description: Optional[str] = None

    @computed_field
    @property
    def url_hash(self) -> str:
        """Generate MD5 hash of URL for deduplication."""
        return hashlib.md5(str(self.url).encode()).hexdigest()


class EpisodeInfo(BaseModel):
    """
    Episode information model for anime series.

    This model stores comprehensive information about anime episodes
    including metadata, characters, and images.
    """

    # Required fields
    title: str = Field(..., min_length=1, max_length=500)
    number: int = Field(..., ge=1, description="Episode number")
    anime_name: str = Field(..., min_length=1, max_length=200)
    source_url: HttpUrl

    # Optional basic info
    season: Optional[int] = Field(None, ge=1, description="Season number")
    episode_type: EpisodeType = EpisodeType.TV_EPISODE
    air_date: Optional[date] = None
    synopsis: Optional[str] = Field(None, max_length=5000)
    duration_minutes: Optional[int] = Field(None, ge=1, le=300)

    # Story arc information
    arc_name: Optional[str] = Field(None, max_length=200)
    arc_number: Optional[int] = Field(None, ge=1)

    # Characters and cast
    characters_featured: List[str] = Field(default_factory=list)
    main_characters: List[str] = Field(default_factory=list)
    voice_actors: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of character name to voice actor"
    )

    # Images and media
    images: List[EpisodeImage] = Field(default_factory=list)
    thumbnail_url: Optional[HttpUrl] = None

    # Production info
    director: Optional[str] = None
    writer: Optional[str] = None
    animation_director: Optional[str] = None

    # Episode codes
    production_code: Optional[str] = None
    japanese_title: Optional[str] = None
    japanese_air_date: Optional[date] = None

    # Statistics
    view_count: Optional[int] = Field(None, ge=0)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0)

    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def episode_id(self) -> str:
        """Generate unique episode ID."""
        id_str = f"{self.anime_name}:ep{self.number}"
        if self.season:
            id_str = f"{self.anime_name}:s{self.season}e{self.number}"
        return hashlib.md5(id_str.encode()).hexdigest()

    @computed_field
    @property
    def season_episode_code(self) -> str:
        """
        Generate season/episode code (e.g., 'S01E05').

        Returns:
            Season/episode code string
        """
        if self.season:
            return f"S{self.season:02d}E{self.number:02d}"
        return f"E{self.number:02d}"

    @computed_field
    @property
    def character_count(self) -> int:
        """Count of featured characters."""
        return len(self.characters_featured)

    @computed_field
    @property
    def image_count(self) -> int:
        """Count of episode images."""
        return len(self.images)

    @validator('air_date', 'japanese_air_date', pre=True)
    def parse_date(cls, v):
        """Parse date from various formats."""
        if v is None or isinstance(v, date):
            return v
        if isinstance(v, str):
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for MongoDB storage.

        Returns:
            Dictionary representation
        """
        data = self.model_dump()
        # Add computed fields
        data['episode_id'] = self.episode_id
        data['season_episode_code'] = self.season_episode_code
        data['character_count'] = self.character_count
        data['image_count'] = self.image_count
        return data

    def to_mongodb_doc(self) -> Dict[str, Any]:
        """
        Convert to MongoDB document format.

        Returns:
            MongoDB-compatible document
        """
        doc = self.to_dict()
        # Convert HttpUrl to string
        doc['source_url'] = str(self.source_url)
        if self.thumbnail_url:
            doc['thumbnail_url'] = str(self.thumbnail_url)

        # Convert images
        doc['images'] = [
            {
                'url': str(img.url),
                'local_path': img.local_path,
                'caption': img.caption,
                'is_thumbnail': img.is_thumbnail,
                'timestamp': img.timestamp,
                'scene_description': img.scene_description,
                'url_hash': img.url_hash,
            }
            for img in self.images
        ]

        return doc


class ChapterInfo(BaseModel):
    """
    Chapter information model for manga/light novel series.

    This model stores comprehensive information about manga/novel chapters.
    """

    # Required fields
    title: str = Field(..., min_length=1, max_length=500)
    number: int = Field(..., ge=1, description="Chapter number")
    manga_name: str = Field(..., min_length=1, max_length=200)
    source_url: HttpUrl

    # Optional basic info
    volume: Optional[int] = Field(None, ge=1, description="Volume number")
    chapter_type: ChapterType = ChapterType.MANGA_CHAPTER
    release_date: Optional[date] = None
    synopsis: Optional[str] = Field(None, max_length=5000)
    page_count: Optional[int] = Field(None, ge=1, le=300)

    # Story arc information
    arc_name: Optional[str] = Field(None, max_length=200)
    arc_number: Optional[int] = Field(None, ge=1)

    # Characters
    characters_featured: List[str] = Field(default_factory=list)
    characters_introduced: List[str] = Field(default_factory=list)

    # Images
    images: List[EpisodeImage] = Field(default_factory=list)  # Reuse EpisodeImage
    cover_image_url: Optional[HttpUrl] = None

    # Production info
    author: Optional[str] = None
    illustrator: Optional[str] = None

    # Chapter codes
    japanese_title: Optional[str] = None
    japanese_release_date: Optional[date] = None

    # Statistics
    read_count: Optional[int] = Field(None, ge=0)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0)

    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def chapter_id(self) -> str:
        """Generate unique chapter ID."""
        id_str = f"{self.manga_name}:ch{self.number}"
        if self.volume:
            id_str = f"{self.manga_name}:vol{self.volume}ch{self.number}"
        return hashlib.md5(id_str.encode()).hexdigest()

    @computed_field
    @property
    def volume_chapter_code(self) -> str:
        """
        Generate volume/chapter code (e.g., 'Vol05Ch023').

        Returns:
            Volume/chapter code string
        """
        if self.volume:
            return f"Vol{self.volume:02d}Ch{self.number:03d}"
        return f"Ch{self.number:03d}"

    @validator('release_date', 'japanese_release_date', pre=True)
    def parse_date(cls, v):
        """Parse date from various formats."""
        if v is None or isinstance(v, date):
            return v
        if isinstance(v, str):
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        return None

    def to_mongodb_doc(self) -> Dict[str, Any]:
        """
        Convert to MongoDB document format.

        Returns:
            MongoDB-compatible document
        """
        doc = self.model_dump()
        # Add computed fields
        doc['chapter_id'] = self.chapter_id
        doc['volume_chapter_code'] = self.volume_chapter_code

        # Convert HttpUrl to string
        doc['source_url'] = str(self.source_url)
        if self.cover_image_url:
            doc['cover_image_url'] = str(self.cover_image_url)

        # Convert images
        doc['images'] = [
            {
                'url': str(img.url),
                'local_path': img.local_path,
                'caption': img.caption,
                'is_thumbnail': img.is_thumbnail,
                'timestamp': img.timestamp,
                'scene_description': img.scene_description,
                'url_hash': img.url_hash,
            }
            for img in self.images
        ]

        return doc
