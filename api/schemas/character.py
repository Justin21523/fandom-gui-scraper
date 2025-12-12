# api/schemas/character.py
"""
Pydantic schemas for API responses.

These schemas define the structure of data returned by API endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class CharacterStatus(str, Enum):
    """Character status enumeration."""
    ALIVE = "alive"
    DECEASED = "deceased"
    UNKNOWN = "unknown"


class ImageSchema(BaseModel):
    """Schema for character image data."""
    url: str
    image_type: Optional[str] = None
    is_primary: bool = False
    width: Optional[int] = None
    height: Optional[int] = None

    class Config:
        from_attributes = True


class RelationshipSchema(BaseModel):
    """Schema for character relationship data."""
    character_name: str
    relationship_type: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class AbilitySchema(BaseModel):
    """Schema for character ability data."""
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    is_devil_fruit: bool = False

    class Config:
        from_attributes = True


class CharacterBase(BaseModel):
    """Base schema for character data."""
    name: str
    anime_name: str
    description: Optional[str] = None
    japanese_name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    status: CharacterStatus = CharacterStatus.UNKNOWN


class CharacterResponse(CharacterBase):
    """Full character response schema."""
    character_id: str
    source_url: str
    images: List[ImageSchema] = []
    relationships: List[RelationshipSchema] = []
    abilities: List[AbilitySchema] = []
    custom_tags: List[str] = []
    quality_score: Optional[float] = None
    scraped_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CharacterListResponse(BaseModel):
    """Paginated list of characters."""
    items: List[CharacterResponse]
    total: int
    page: int
    per_page: int
    pages: int


class CharacterCreateRequest(BaseModel):
    """Request schema for creating a character."""
    name: str = Field(..., min_length=1, max_length=200)
    anime_name: str = Field(..., min_length=1, max_length=200)
    source_url: str
    description: Optional[str] = None
    japanese_name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    status: CharacterStatus = CharacterStatus.UNKNOWN
    custom_tags: List[str] = []


class CharacterUpdateRequest(BaseModel):
    """Request schema for updating a character."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    japanese_name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    status: Optional[CharacterStatus] = None
    custom_tags: Optional[List[str]] = None


class SearchRequest(BaseModel):
    """Request schema for searching characters."""
    query: str = Field(..., min_length=1)
    anime_name: Optional[str] = None
    status: Optional[CharacterStatus] = None
    tags: Optional[List[str]] = None
    min_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class StatsResponse(BaseModel):
    """Response schema for statistics."""
    total_characters: int
    total_anime: int
    characters_by_anime: Dict[str, int]
    quality_distribution: Dict[str, int]
    recent_updates: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


class SuccessResponse(BaseModel):
    """Standard success response."""
    message: str
    data: Optional[Dict[str, Any]] = None
