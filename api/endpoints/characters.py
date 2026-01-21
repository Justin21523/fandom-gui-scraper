# api/endpoints/characters.py
"""
Character API endpoints.

Provides REST API endpoints for character CRUD operations and search.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from api.security.dependencies import require_auth
from api.schemas.character import (
    CharacterResponse,
    CharacterListResponse,
    CharacterCreateRequest,
    CharacterUpdateRequest,
    SearchRequest,
    StatsResponse,
    SuccessResponse,
)
from models.storage import DatabaseManager
from utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/characters", tags=["characters"])

# Database dependency
_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Get database manager instance."""
    global _db_manager
    if _db_manager is None:
        config = ConfigManager()
        config.load_config()
        _db_manager = DatabaseManager(
            connection_string=config.database.get_connection_string(),
            database_name=config.database.name or "fandom_scraper",
        )
        try:
            success = _db_manager.connect()
            if not success:
                logger.warning("Database connection failed, but continuing...")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            # 不拋出異常，允許 API 繼續運行
    return _db_manager


@router.get("/", response_model=CharacterListResponse)
async def list_characters(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    anime_name: Optional[str] = Query(None, description="Filter by anime name"),
    db: DatabaseManager = Depends(get_db),
):
    """
    List all characters with pagination.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **anime_name**: Optional filter by anime name
    """
    try:
        # 檢查資料庫是否連接
        if not db._is_connected:
            return CharacterListResponse(
                items=[],
                total=0,
                page=page,
                per_page=per_page,
                pages=1,
            )

        collection = db.get_collection("characters")

        # Build query filter
        query_filter = {}
        if anime_name:
            query_filter["anime_name"] = anime_name

        # Get total count
        total = collection.count_documents(query_filter)

        # Calculate pagination
        skip = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page if total > 0 else 1

        # Fetch characters
        cursor = collection.find(query_filter).skip(skip).limit(per_page)
        characters = list(cursor)

        # Convert to response format
        items = []
        for char in characters:
            char["character_id"] = char.get("_character_id", str(char.get("_id", "")))
            items.append(CharacterResponse(**char))

        return CharacterListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
    except Exception as e:
        logger.error(f"Error listing characters: {e}")
        # 返回空列表而不是錯誤
        return CharacterListResponse(
            items=[],
            total=0,
            page=page,
            per_page=per_page,
            pages=1,
        )


@router.get("/search", response_model=CharacterListResponse)
async def search_characters(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: DatabaseManager = Depends(get_db),
):
    """
    Search characters by name or description.

    - **q**: Search query (required)
    """
    try:
        collection = db.get_collection("characters")

        # Use text search
        query_filter = {"$text": {"$search": q}}

        total = collection.count_documents(query_filter)
        skip = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page if total > 0 else 1

        cursor = collection.find(query_filter).skip(skip).limit(per_page)
        characters = list(cursor)

        items = []
        for char in characters:
            char["character_id"] = char.get("_character_id", str(char.get("_id", "")))
            items.append(CharacterResponse(**char))

        return CharacterListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
    except Exception as e:
        logger.error(f"Error searching characters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: DatabaseManager = Depends(get_db)):
    """Get character statistics."""
    try:
        # 檢查資料庫是否連接
        if not db._is_connected:
            return StatsResponse(
                total_characters=0,
                total_anime=0,
                characters_by_anime={},
                quality_distribution={},
                recent_updates=0,
            )

        collection = db.get_collection("characters")

        # Total characters
        total_characters = collection.count_documents({})

        # Characters by anime
        pipeline = [
            {"$group": {"_id": "$anime_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ]
        anime_stats = list(collection.aggregate(pipeline))
        characters_by_anime = {
            item["_id"]: item["count"] for item in anime_stats if item["_id"]
        }

        # Quality distribution
        quality_pipeline = [
            {
                "$bucket": {
                    "groupBy": "$quality_score",
                    "boundaries": [0, 0.3, 0.6, 1.01],
                    "default": "unknown",
                    "output": {"count": {"$sum": 1}},
                }
            }
        ]
        try:
            quality_stats = list(collection.aggregate(quality_pipeline))
            quality_distribution = {}
            for item in quality_stats:
                if item["_id"] == 0:
                    quality_distribution["low"] = item["count"]
                elif item["_id"] == 0.3:
                    quality_distribution["medium"] = item["count"]
                elif item["_id"] == 0.6:
                    quality_distribution["high"] = item["count"]
                else:
                    quality_distribution["unknown"] = item["count"]
        except Exception:
            quality_distribution = {}

        return StatsResponse(
            total_characters=total_characters,
            total_anime=len(characters_by_anime),
            characters_by_anime=characters_by_anime,
            quality_distribution=quality_distribution,
            recent_updates=0,
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    db: DatabaseManager = Depends(get_db),
):
    """
    Get a specific character by ID.

    - **character_id**: Character's unique identifier
    """
    try:
        collection = db.get_collection("characters")

        character = collection.find_one({"_character_id": character_id})

        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        character["character_id"] = character.get("_character_id", "")
        return CharacterResponse(**character)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting character {character_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CharacterResponse, status_code=201)
async def create_character(
    request: CharacterCreateRequest,
    db: DatabaseManager = Depends(get_db),
    user: Dict[str, Any] = Depends(require_auth),
):
    """
    Create a new character.

    Requires authentication.
    """
    try:
        from models.document import AnimeCharacter

        # Create character model
        character = AnimeCharacter(
            name=request.name,
            anime_name=request.anime_name,
            source_url=request.source_url,
            description=request.description,
            japanese_name=request.japanese_name,
            age=request.age,
            gender=request.gender,
            occupation=request.occupation,
            status=request.status.value if request.status else "unknown",
            custom_tags=request.custom_tags,
        )

        # Convert to MongoDB document
        doc = character.to_mongodb_doc()

        collection = db.get_collection("characters")
        result = collection.insert_one(doc)

        # Fetch the created document
        created = collection.find_one({"_id": result.inserted_id})
        created["character_id"] = created.get("_character_id", "")

        return CharacterResponse(**created)
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    request: CharacterUpdateRequest,
    db: DatabaseManager = Depends(get_db),
    user: Dict[str, Any] = Depends(require_auth),
):
    """
    Update an existing character.

    Requires authentication.

    - **character_id**: Character's unique identifier
    """
    try:
        collection = db.get_collection("characters")

        # Check if character exists
        existing = collection.find_one({"_character_id": character_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Character not found")

        # Build update document
        update_data = {}
        for field, value in request.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == "status":
                    update_data[field] = value.value if hasattr(value, "value") else value
                else:
                    update_data[field] = value

        if update_data:
            from datetime import datetime
            update_data["updated_at"] = datetime.utcnow()
            collection.update_one(
                {"_character_id": character_id},
                {"$set": update_data}
            )

        # Fetch updated document
        updated = collection.find_one({"_character_id": character_id})
        updated["character_id"] = updated.get("_character_id", "")

        return CharacterResponse(**updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating character {character_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{character_id}", response_model=SuccessResponse)
async def delete_character(
    character_id: str,
    db: DatabaseManager = Depends(get_db),
    user: Dict[str, Any] = Depends(require_auth),
):
    """
    Delete a character.

    Requires authentication.

    - **character_id**: Character's unique identifier
    """
    try:
        collection = db.get_collection("characters")

        result = collection.delete_one({"_character_id": character_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Character not found")

        return SuccessResponse(
            message=f"Character {character_id} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting character {character_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
