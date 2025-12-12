"""
Gallery and media data models for Fandom wikis.

This module defines Pydantic models for storing gallery images and media
scraped from Fandom wiki gallery pages.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl, Field, validator, computed_field
import hashlib


class GalleryImageCategory(str, Enum):
    """Gallery image category classification."""
    CONCEPT_ART = "concept_art"
    CHARACTER_DESIGN = "character_design"
    SCREENSHOT = "screenshot"
    PROMOTIONAL = "promotional"
    POSTER = "poster"
    WALLPAPER = "wallpaper"
    MANGA_PANEL = "manga_panel"
    MERCHANDISE = "merchandise"
    FANART = "fanart"
    BEHIND_THE_SCENES = "behind_the_scenes"
    OTHER = "other"


class ImageQuality(str, Enum):
    """Image quality classification."""
    HIGH = "high"  # HD or higher
    MEDIUM = "medium"  # SD
    LOW = "low"  # Thumbnail quality
    UNKNOWN = "unknown"


class GalleryImage(BaseModel):
    """
    Gallery image with extended metadata.

    This model stores comprehensive information about images from
    Fandom wiki gallery pages, including categorization, relationships,
    and metadata.
    """

    # Required fields
    url: HttpUrl
    anime_name: str = Field(..., min_length=1, max_length=200)
    source_url: HttpUrl = Field(..., description="URL of the gallery page")

    # Image identification
    filename: Optional[str] = None
    local_path: Optional[str] = None

    # Categorization
    category: GalleryImageCategory = GalleryImageCategory.OTHER
    tags: List[str] = Field(default_factory=list, description="User-defined tags")

    # Image properties
    width: Optional[int] = Field(None, ge=1)
    height: Optional[int] = Field(None, ge=1)
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    format: Optional[str] = None  # jpg, png, webp, etc.
    quality: ImageQuality = ImageQuality.UNKNOWN

    # Descriptive information
    caption: Optional[str] = Field(None, max_length=1000)
    alt_text: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)

    # Relationships
    related_character: Optional[str] = Field(None, max_length=200)
    related_episode: Optional[int] = Field(None, ge=1)
    related_chapter: Optional[int] = Field(None, ge=1)
    related_arc: Optional[str] = Field(None, max_length=200)

    # Upload metadata
    uploader: Optional[str] = Field(None, max_length=100)
    upload_date: Optional[datetime] = None

    # Copyright and licensing
    copyright_info: Optional[str] = Field(None, max_length=500)
    license: Optional[str] = None

    # Download tracking
    downloaded_at: Optional[datetime] = None
    download_success: bool = False
    download_error: Optional[str] = None

    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def url_hash(self) -> str:
        """Generate MD5 hash of URL for deduplication."""
        return hashlib.md5(str(self.url).encode()).hexdigest()

    @computed_field
    @property
    def image_id(self) -> str:
        """Generate unique image ID."""
        id_str = f"{self.anime_name}:{self.url_hash[:16]}"
        return hashlib.md5(id_str.encode()).hexdigest()

    @computed_field
    @property
    def aspect_ratio(self) -> Optional[float]:
        """
        Calculate aspect ratio (width/height).

        Returns:
            Aspect ratio or None if dimensions unknown
        """
        if self.width and self.height and self.height > 0:
            return round(self.width / self.height, 2)
        return None

    @computed_field
    @property
    def is_portrait(self) -> Optional[bool]:
        """
        Check if image is portrait orientation.

        Returns:
            True if portrait, False if landscape, None if unknown
        """
        if self.aspect_ratio is not None:
            return self.aspect_ratio < 1.0
        return None

    @computed_field
    @property
    def resolution_label(self) -> str:
        """
        Get resolution label (e.g., '1920x1080', 'HD', 'Unknown').

        Returns:
            Resolution description string
        """
        if self.width and self.height:
            # Check for common resolutions
            if self.width >= 3840:
                return f"{self.width}x{self.height} (4K)"
            elif self.width >= 1920:
                return f"{self.width}x{self.height} (Full HD)"
            elif self.width >= 1280:
                return f"{self.width}x{self.height} (HD)"
            else:
                return f"{self.width}x{self.height} (SD)"
        return "Unknown"

    @computed_field
    @property
    def file_size_label(self) -> str:
        """
        Get human-readable file size.

        Returns:
            File size string (e.g., '2.5 MB', 'Unknown')
        """
        if self.file_size is None:
            return "Unknown"

        # Convert to appropriate unit
        if self.file_size >= 1024 * 1024:  # MB
            return f"{self.file_size / (1024 * 1024):.2f} MB"
        elif self.file_size >= 1024:  # KB
            return f"{self.file_size / 1024:.2f} KB"
        else:  # Bytes
            return f"{self.file_size} bytes"

    @validator('upload_date', pre=True)
    def parse_upload_date(cls, v):
        """Parse upload date from various formats."""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try common datetime formats
            for fmt in [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%B %d, %Y',
            ]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        data = self.model_dump()
        # Add computed fields
        data['url_hash'] = self.url_hash
        data['image_id'] = self.image_id
        data['aspect_ratio'] = self.aspect_ratio
        data['is_portrait'] = self.is_portrait
        data['resolution_label'] = self.resolution_label
        data['file_size_label'] = self.file_size_label
        return data

    def to_mongodb_doc(self) -> Dict[str, Any]:
        """
        Convert to MongoDB document format.

        Returns:
            MongoDB-compatible document
        """
        doc = self.to_dict()
        # Convert HttpUrl to string
        doc['url'] = str(self.url)
        doc['source_url'] = str(self.source_url)
        return doc


class GalleryCollection(BaseModel):
    """
    Collection of gallery images with metadata.

    This model represents a gallery page or collection of related images.
    """

    # Required fields
    name: str = Field(..., min_length=1, max_length=200)
    anime_name: str = Field(..., min_length=1, max_length=200)
    source_url: HttpUrl

    # Description
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = None

    # Images in collection
    images: List[GalleryImage] = Field(default_factory=list)

    # Organization
    subcategories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    # Statistics
    total_images: int = 0
    downloaded_count: int = 0
    failed_count: int = 0

    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def collection_id(self) -> str:
        """Generate unique collection ID."""
        id_str = f"{self.anime_name}:{self.name}"
        return hashlib.md5(id_str.encode()).hexdigest()

    @computed_field
    @property
    def image_count(self) -> int:
        """Count of images in collection."""
        return len(self.images)

    @computed_field
    @property
    def download_success_rate(self) -> float:
        """
        Calculate download success rate.

        Returns:
            Success rate (0.0-1.0)
        """
        if self.total_images == 0:
            return 0.0
        return self.downloaded_count / self.total_images

    @computed_field
    @property
    def category_breakdown(self) -> Dict[str, int]:
        """
        Get count of images by category.

        Returns:
            Dictionary mapping category to count
        """
        breakdown = {}
        for image in self.images:
            category = image.category.value
            breakdown[category] = breakdown.get(category, 0) + 1
        return breakdown

    def add_image(self, image: GalleryImage):
        """
        Add image to collection.

        Args:
            image: GalleryImage to add
        """
        self.images.append(image)
        self.total_images = len(self.images)
        if image.download_success:
            self.downloaded_count += 1
        elif image.download_error:
            self.failed_count += 1

    def update_stats(self):
        """Update collection statistics based on current images."""
        self.total_images = len(self.images)
        self.downloaded_count = sum(1 for img in self.images if img.download_success)
        self.failed_count = sum(1 for img in self.images if img.download_error)
        self.updated_at = datetime.utcnow()

    def to_mongodb_doc(self) -> Dict[str, Any]:
        """
        Convert to MongoDB document format.

        Returns:
            MongoDB-compatible document
        """
        doc = self.model_dump()
        # Add computed fields
        doc['collection_id'] = self.collection_id
        doc['image_count'] = self.image_count
        doc['download_success_rate'] = self.download_success_rate
        doc['category_breakdown'] = self.category_breakdown

        # Convert HttpUrl to string
        doc['source_url'] = str(self.source_url)

        # Convert images
        doc['images'] = [img.to_mongodb_doc() for img in self.images]

        return doc


# Model registry for easy access
GALLERY_MODELS = {
    'image': GalleryImage,
    'collection': GalleryCollection,
}


def create_gallery_image(
    url: str,
    anime_name: str,
    source_url: str,
    category: str = "other",
    **kwargs
) -> GalleryImage:
    """
    Convenience function to create a GalleryImage instance.

    Args:
        url: Image URL
        anime_name: Name of anime/series
        source_url: Source gallery page URL
        category: Image category
        **kwargs: Additional fields

    Returns:
        GalleryImage instance
    """
    return GalleryImage(
        url=url,
        anime_name=anime_name,
        source_url=source_url,
        category=category,
        **kwargs
    )
