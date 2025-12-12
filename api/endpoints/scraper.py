# api/endpoints/scraper.py
"""
Scraper control API endpoints.

Provides endpoints for controlling the web scraper:
- Start/stop/pause scraping operations
- Get scraper status and progress
- Configure scraping parameters
- View scraping history
"""

import asyncio
import logging
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from api.security.jwt import get_current_user

# Import scraper modules
try:
    from scraper.runner import SpiderRunner, create_spider_runner
    from scraper.fandom_spider import FandomSpider
    SCRAPER_AVAILABLE = True
except ImportError as e:
    SCRAPER_AVAILABLE = False
    logging.warning(f"Scraper modules not available: {e}")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["scraper"])


# --- Schemas ---

class ScraperConfig(BaseModel):
    """Scraper configuration."""
    base_url: str = Field(..., description="Base URL of the Fandom wiki")
    character_list_url: str = Field(default="/wiki/Category:Characters", description="Path to character list")
    delay: float = Field(default=1.0, ge=0, le=10, description="Delay between requests in seconds")
    retries: int = Field(default=3, ge=0, le=10, description="Number of retries on failure")
    concurrent: int = Field(default=1, ge=1, le=5, description="Number of concurrent requests")
    selectors: Optional[dict] = Field(default=None, description="Custom CSS selectors")


class ScraperPreset(BaseModel):
    """Anime preset configuration."""
    name: str
    base_url: str
    character_list_url: str
    description: Optional[str] = None


class ScraperStatus(BaseModel):
    """Scraper status response."""
    status: str  # idle, running, paused, stopped
    started_at: Optional[datetime] = None
    progress: Optional[dict] = None
    current_url: Optional[str] = None
    error: Optional[str] = None


class ScraperProgress(BaseModel):
    """Scraper progress information."""
    total: int = 0
    completed: int = 0
    failed: int = 0
    speed: Optional[float] = None
    eta: Optional[int] = None


class ScraperLog(BaseModel):
    """Scraper log entry."""
    timestamp: datetime
    level: str
    message: str


class UrlValidation(BaseModel):
    """URL validation request."""
    url: str


class SelectorTest(BaseModel):
    """Selector test request."""
    url: str
    selectors: dict


# --- Universal Scraper Schemas ---

class AnimeSearchRequest(BaseModel):
    """Request to search for anime wiki."""
    anime_name: str = Field(..., description="Name of the anime to search for")
    top_n: int = Field(default=5, ge=1, le=10, description="Number of top results to return")


class FandomSearchResult(BaseModel):
    """Single Fandom search result."""
    url: str
    domain: str
    title: str
    description: Optional[str] = None
    relevance_score: float
    is_main_page: bool


class UniversalScraperConfig(BaseModel):
    """Configuration for Universal Fandom Scraper."""
    input_source: str = Field(..., description="Anime name or Fandom wiki URL")
    input_type: str = Field(default="name", description="Type of input: 'name' or 'url'")

    # Category toggles
    crawl_characters: bool = Field(default=True, description="Crawl character pages")
    crawl_episodes: bool = Field(default=True, description="Crawl episode pages")
    crawl_galleries: bool = Field(default=True, description="Crawl gallery pages")
    crawl_chapters: bool = Field(default=False, description="Crawl chapter pages (manga)")

    # Per-category limits
    max_chars: int = Field(default=100, ge=0, description="Max characters to scrape (0 = unlimited)")
    max_episodes: int = Field(default=50, ge=0, description="Max episodes to scrape")
    max_gallery_images: int = Field(default=200, ge=0, description="Max gallery images")
    max_chapters: int = Field(default=50, ge=0, description="Max chapters to scrape")

    # General settings
    delay: float = Field(default=1.0, ge=0, le=10, description="Delay between requests in seconds")
    retries: int = Field(default=3, ge=0, le=10, description="Number of retries on failure")


class CategoryProgress(BaseModel):
    """Progress for a specific category."""
    enabled: bool
    total: int
    completed: int
    failed: int
    max_limit: int


class UniversalScraperProgress(BaseModel):
    """Progress information for Universal Scraper."""
    characters: CategoryProgress
    episodes: CategoryProgress
    galleries: CategoryProgress
    chapters: CategoryProgress
    overall_completed: int
    overall_total: int
    speed: Optional[float] = None
    eta: Optional[int] = None


class UniversalScraperStatus(BaseModel):
    """Status for Universal Scraper."""
    status: str  # idle, running, paused, stopped
    started_at: Optional[datetime] = None
    anime_name: Optional[str] = None
    wiki_url: Optional[str] = None
    progress: Optional[UniversalScraperProgress] = None
    error: Optional[str] = None


# --- Global State ---

# Config persistence directory
CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "scraper_configs"
HISTORY_FILE = Path(__file__).parent.parent.parent / "config" / "scraper_history.json"


class ScraperState:
    """Global scraper state management."""

    def __init__(self):
        self.status = "idle"
        self.config: Optional[ScraperConfig] = None
        self.started_at: Optional[datetime] = None
        self.progress = ScraperProgress()
        self.current_url: Optional[str] = None
        self.error: Optional[str] = None
        self.logs: list[ScraperLog] = []
        self._task: Optional[asyncio.Task] = None

    def reset(self):
        """Reset scraper state."""
        self.status = "idle"
        self.config = None
        self.started_at = None
        self.progress = ScraperProgress()
        self.current_url = None
        self.error = None

    def add_log(self, level: str, message: str):
        """Add a log entry."""
        self.logs.append(ScraperLog(
            timestamp=datetime.now(),
            level=level,
            message=message
        ))
        # Keep only last 1000 logs
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]


scraper_state = ScraperState()


# --- Config Persistence ---

class ConfigManager:
    """Manage scraper configuration persistence."""

    def __init__(self, config_dir: Path = CONFIG_DIR, history_file: Path = HISTORY_FILE):
        self.config_dir = config_dir
        self.history_file = history_file
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure config directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def save_config(self, name: str, config: ScraperConfig) -> bool:
        """Save a scraper configuration to file."""
        try:
            config_path = self.config_dir / f"{self._sanitize_name(name)}.json"
            config_data = {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "config": config.model_dump()
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved config: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config {name}: {e}")
            return False

    def load_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a scraper configuration from file."""
        try:
            config_path = self.config_dir / f"{self._sanitize_name(name)}.json"
            if not config_path.exists():
                return None
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config {name}: {e}")
            return None

    def list_configs(self) -> List[Dict[str, Any]]:
        """List all saved configurations."""
        configs = []
        try:
            for config_path in self.config_dir.glob("*.json"):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        configs.append({
                            "name": data.get("name", config_path.stem),
                            "created_at": data.get("created_at"),
                            "base_url": data.get("config", {}).get("base_url", "")
                        })
                except Exception as e:
                    logger.warning(f"Failed to read config {config_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to list configs: {e}")
        return configs

    def delete_config(self, name: str) -> bool:
        """Delete a saved configuration."""
        try:
            config_path = self.config_dir / f"{self._sanitize_name(name)}.json"
            if config_path.exists():
                config_path.unlink()
                logger.info(f"Deleted config: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete config {name}: {e}")
            return False

    def add_history_entry(self, config: ScraperConfig, result: Dict[str, Any]):
        """Add a scraping history entry."""
        try:
            history = self._load_history()
            entry = {
                "timestamp": datetime.now().isoformat(),
                "base_url": config.base_url,
                "config": config.model_dump(),
                "result": result
            }
            history.insert(0, entry)
            # Keep only last 100 entries
            history = history[:100]
            self._save_history(history)
        except Exception as e:
            logger.error(f"Failed to add history entry: {e}")

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get scraping history."""
        history = self._load_history()
        return history[:limit]

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
        return []

    def _save_history(self, history: List[Dict[str, Any]]):
        """Save history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def _sanitize_name(self, name: str) -> str:
        """Sanitize config name for use as filename."""
        import re
        return re.sub(r'[^\w\-_]', '_', name).lower()


config_manager = ConfigManager()


# --- Presets ---

ANIME_PRESETS = [
    ScraperPreset(
        name="Dragon Ball",
        base_url="https://dragonball.fandom.com",
        character_list_url="/wiki/Category:Characters",
        description="Dragon Ball wiki characters"
    ),
    ScraperPreset(
        name="Naruto",
        base_url="https://naruto.fandom.com",
        character_list_url="/wiki/Category:Characters",
        description="Naruto wiki characters"
    ),
    ScraperPreset(
        name="One Piece",
        base_url="https://onepiece.fandom.com",
        character_list_url="/wiki/Category:Characters",
        description="One Piece wiki characters"
    ),
    ScraperPreset(
        name="Bleach",
        base_url="https://bleach.fandom.com",
        character_list_url="/wiki/Category:Characters",
        description="Bleach wiki characters"
    ),
    ScraperPreset(
        name="My Hero Academia",
        base_url="https://myheroacademia.fandom.com",
        character_list_url="/wiki/Category:Characters",
        description="My Hero Academia wiki characters"
    ),
    ScraperPreset(
        name="Demon Slayer",
        base_url="https://kimetsu-no-yaiba.fandom.com",
        character_list_url="/wiki/Category:Characters",
        description="Demon Slayer wiki characters"
    ),
]


# --- Endpoints ---

@router.get("/presets", response_model=list[ScraperPreset])
async def get_presets():
    """Get available anime presets."""
    return ANIME_PRESETS


@router.get("/status", response_model=ScraperStatus)
async def get_status():
    """Get current scraper status."""
    return ScraperStatus(
        status=scraper_state.status,
        started_at=scraper_state.started_at,
        progress=scraper_state.progress.model_dump() if scraper_state.progress else None,
        current_url=scraper_state.current_url,
        error=scraper_state.error
    )


@router.post("/start")
async def start_scraper(
    config: ScraperConfig,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start the scraper with the given configuration."""
    if scraper_state.status == "running":
        raise HTTPException(status_code=400, detail="Scraper is already running")

    scraper_state.config = config
    scraper_state.status = "running"
    scraper_state.started_at = datetime.now()
    scraper_state.progress = ScraperProgress()
    scraper_state.error = None
    scraper_state.add_log("info", f"Starting scraper for {config.base_url}")

    # Start scraping in background
    background_tasks.add_task(run_scraper, config)

    return {
        "status": "started",
        "message": f"Scraper started for {config.base_url}"
    }


@router.post("/stop")
async def stop_scraper(current_user: dict = Depends(get_current_user)):
    """Stop the running scraper."""
    if scraper_state.status not in ("running", "paused"):
        raise HTTPException(status_code=400, detail="Scraper is not running")

    scraper_state.status = "stopped"
    scraper_state.add_log("info", "Scraper stopped by user")

    if scraper_state._task and not scraper_state._task.done():
        scraper_state._task.cancel()

    return {"status": "stopped", "message": "Scraper stopped"}


@router.post("/pause")
async def pause_scraper(current_user: dict = Depends(get_current_user)):
    """Pause the running scraper."""
    if scraper_state.status != "running":
        raise HTTPException(status_code=400, detail="Scraper is not running")

    scraper_state.status = "paused"
    scraper_state.add_log("info", "Scraper paused")

    return {"status": "paused", "message": "Scraper paused"}


@router.post("/resume")
async def resume_scraper(current_user: dict = Depends(get_current_user)):
    """Resume the paused scraper."""
    if scraper_state.status != "paused":
        raise HTTPException(status_code=400, detail="Scraper is not paused")

    scraper_state.status = "running"
    scraper_state.add_log("info", "Scraper resumed")

    return {"status": "running", "message": "Scraper resumed"}


@router.get("/logs", response_model=list[ScraperLog])
async def get_logs(
    limit: int = 100,
    level: Optional[str] = None
):
    """Get scraper logs."""
    logs = scraper_state.logs

    if level and level != "all":
        logs = [log for log in logs if log.level == level]

    return logs[-limit:]


@router.post("/validate-url")
async def validate_url(data: UrlValidation):
    """Validate a URL for scraping."""
    import re
    from urllib.parse import urlparse

    url = data.url
    parsed = urlparse(url)

    # Check if it's a valid URL
    if not parsed.scheme or not parsed.netloc:
        return {"valid": False, "error": "Invalid URL format"}

    # Check if it's a Fandom wiki
    if "fandom.com" not in parsed.netloc and "wikia.com" not in parsed.netloc:
        return {
            "valid": True,
            "warning": "URL is not a Fandom wiki. Scraping may not work correctly."
        }

    return {"valid": True, "message": "URL is valid"}


@router.post("/test-selectors")
async def test_selectors(data: SelectorTest):
    """Test CSS selectors on a page."""
    # This would normally fetch the page and test selectors
    # For now, return a mock response
    return {
        "success": True,
        "results": {
            "name": "Found 1 match",
            "description": "Found 1 match",
            "image": "Found 3 matches"
        }
    }


@router.get("/stats")
async def get_scraper_stats():
    """Get scraping statistics."""
    return {
        "total_scraped": scraper_state.progress.completed + scraper_state.progress.failed,
        "successful": scraper_state.progress.completed,
        "failed": scraper_state.progress.failed,
        "last_run": scraper_state.started_at,
        "status": scraper_state.status
    }


@router.get("/history")
async def get_scraper_history(limit: int = 10):
    """Get scraping history."""
    return config_manager.get_history(limit)


@router.post("/configs")
async def save_config(
    name: str,
    config: ScraperConfig,
    current_user: dict = Depends(get_current_user)
):
    """Save a scraper configuration."""
    success = config_manager.save_config(name, config)
    if success:
        return {"status": "saved", "name": name}
    raise HTTPException(status_code=500, detail="Failed to save configuration")


@router.get("/configs")
async def get_configs():
    """Get saved scraper configurations."""
    return config_manager.list_configs()


@router.get("/configs/{name}")
async def get_config(name: str):
    """Get a specific saved configuration."""
    config_data = config_manager.load_config(name)
    if config_data:
        return config_data
    raise HTTPException(status_code=404, detail="Configuration not found")


@router.delete("/configs/{name}")
async def delete_config(
    name: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a saved configuration."""
    success = config_manager.delete_config(name)
    if success:
        return {"status": "deleted", "name": name}
    raise HTTPException(status_code=404, detail="Configuration not found")


# --- Background Task ---

async def run_scraper(config: ScraperConfig):
    """Run the scraper in the background."""
    try:
        scraper_state.add_log("info", f"Connecting to {config.base_url}")

        if SCRAPER_AVAILABLE:
            # Use real scraper
            await run_real_scraper(config)
        else:
            # Fallback to simulation mode
            await run_simulated_scraper(config)

    except asyncio.CancelledError:
        scraper_state.add_log("warning", "Scraper task cancelled")
        scraper_state.status = "stopped"
    except Exception as e:
        logger.error(f"Scraper error: {e}", exc_info=True)
        scraper_state.status = "stopped"
        scraper_state.error = str(e)
        scraper_state.add_log("error", f"Scraper error: {e}")


async def run_real_scraper(config: ScraperConfig):
    """Run the actual Scrapy spider."""
    from urllib.parse import urlparse

    scraper_state.add_log("info", "Starting real scraper engine...")

    # Extract anime name from URL
    parsed = urlparse(config.base_url)
    anime_name = parsed.netloc.split('.')[0].replace('-', ' ').title()

    # Prepare spider settings
    settings = {
        'DOWNLOAD_DELAY': config.delay,
        'RETRY_TIMES': config.retries,
        'CONCURRENT_REQUESTS': config.concurrent,
        'LOG_LEVEL': 'INFO',
        # Enable JSON output
        'FEEDS': {
            'output/characters.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 2,
            }
        }
    }

    # Add custom selectors if provided
    if config.selectors:
        settings['CUSTOM_SELECTORS'] = config.selectors

    scraper_state.add_log("info", f"Spider configured for: {anime_name}")
    scraper_state.progress.total = 100  # Estimated

    # Run spider in a thread to not block asyncio
    def spider_thread():
        try:
            runner = create_spider_runner(settings)

            # Set up progress callback
            def progress_callback(message: str, progress: Optional[float]):
                scraper_state.add_log("info", message)
                if progress is not None:
                    scraper_state.progress.completed = int(progress)

            # Run the spider
            spider_kwargs = {
                'anime_name': anime_name,
                'max_characters': 100,  # Configurable limit
            }

            runner.run_spider('fandom', spider_kwargs, blocking=True)

            # Update final status
            scraper_state.add_log("info", "Scraping completed successfully")

        except Exception as e:
            logger.error(f"Spider error: {e}", exc_info=True)
            scraper_state.error = str(e)
            scraper_state.add_log("error", f"Spider error: {e}")

    # Start spider thread
    thread = threading.Thread(target=spider_thread, daemon=True)
    thread.start()

    # Monitor progress
    while thread.is_alive():
        if scraper_state.status == "stopped":
            scraper_state.add_log("warning", "Stopping spider...")
            break

        while scraper_state.status == "paused":
            await asyncio.sleep(0.5)
            if scraper_state.status == "stopped":
                break

        await asyncio.sleep(1)

    # Wait for thread to complete
    thread.join(timeout=5)

    if scraper_state.status != "stopped":
        scraper_state.status = "idle"


async def run_simulated_scraper(config: ScraperConfig):
    """Run simulated scraping for demo purposes."""
    scraper_state.add_log("warning", "Running in simulation mode (Scrapy not available)")

    # Mock character data
    mock_characters = [
        {"name": "Goku", "anime": "Dragon Ball"},
        {"name": "Vegeta", "anime": "Dragon Ball"},
        {"name": "Naruto Uzumaki", "anime": "Naruto"},
        {"name": "Sasuke Uchiha", "anime": "Naruto"},
        {"name": "Monkey D. Luffy", "anime": "One Piece"},
        {"name": "Roronoa Zoro", "anime": "One Piece"},
        {"name": "Ichigo Kurosaki", "anime": "Bleach"},
        {"name": "Izuku Midoriya", "anime": "My Hero Academia"},
        {"name": "Tanjiro Kamado", "anime": "Demon Slayer"},
        {"name": "Nezuko Kamado", "anime": "Demon Slayer"},
    ]

    total_items = len(mock_characters)
    scraper_state.progress.total = total_items

    for i, char in enumerate(mock_characters):
        # Check if stopped
        if scraper_state.status == "stopped":
            break

        # Wait while paused
        while scraper_state.status == "paused":
            await asyncio.sleep(0.5)
            if scraper_state.status == "stopped":
                break

        if scraper_state.status == "stopped":
            break

        # Simulate processing
        await asyncio.sleep(config.delay)

        scraper_state.progress.completed += 1
        scraper_state.current_url = f"{config.base_url}/wiki/{char['name'].replace(' ', '_')}"
        scraper_state.add_log("info", f"Scraped: {char['name']} ({char['anime']}) [{i+1}/{total_items}]")

    if scraper_state.status != "stopped":
        scraper_state.status = "idle"
        scraper_state.add_log("info", f"Simulation completed. {scraper_state.progress.completed} characters scraped.")


# ========================================
# UNIVERSAL FANDOM SCRAPER ENDPOINTS
# ========================================

class UniversalScraperState:
    """Global state management for Universal Scraper."""

    def __init__(self):
        self.status = "idle"
        self.config: Optional[UniversalScraperConfig] = None
        self.started_at: Optional[datetime] = None
        self.anime_name: Optional[str] = None
        self.wiki_url: Optional[str] = None
        self.progress: Optional[UniversalScraperProgress] = None
        self.error: Optional[str] = None
        self.logs: list[ScraperLog] = []
        self._task: Optional[asyncio.Task] = None
        self._process = None  # For subprocess management

    def reset(self):
        """Reset scraper state."""
        self.status = "idle"
        self.config = None
        self.started_at = None
        self.anime_name = None
        self.wiki_url = None
        self.progress = None
        self.error = None

    def add_log(self, level: str, message: str):
        """Add a log entry."""
        self.logs.append(ScraperLog(
            timestamp=datetime.now(),
            level=level,
            message=message
        ))
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]


universal_scraper_state = UniversalScraperState()


@router.post("/search-anime", response_model=List[FandomSearchResult])
async def search_anime(request: AnimeSearchRequest):
    """
    Search for anime Fandom wiki using Brave Search API.

    Returns top N search results with relevance scoring.
    """
    try:
        from utils.brave_search import BraveSearchClient

        client = BraveSearchClient()
        results = client.find_fandom_wiki(request.anime_name, top_n=request.top_n)

        # Convert to response model
        return [
            FandomSearchResult(
                url=r.url,
                domain=r.domain,
                title=r.title,
                description=r.description,
                relevance_score=r.relevance_score,
                is_main_page=r.is_main_page
            )
            for r in results
        ]

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Brave Search integration not available. Please check BRAVE_API_KEY environment variable."
        )
    except Exception as e:
        logger.error(f"Anime search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/start-universal")
async def start_universal_scraper(
    config: UniversalScraperConfig,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start the Universal Fandom Scraper with multi-category support.

    Supports:
    - Anime name or direct URL input
    - Multi-category crawling (characters, episodes, galleries, chapters)
    - Per-category limits
    - Real-time progress tracking
    """
    if universal_scraper_state.status == "running":
        raise HTTPException(status_code=400, detail="Universal scraper is already running")

    # Initialize state
    universal_scraper_state.config = config
    universal_scraper_state.status = "running"
    universal_scraper_state.started_at = datetime.now()
    universal_scraper_state.error = None

    # Initialize progress
    universal_scraper_state.progress = UniversalScraperProgress(
        characters=CategoryProgress(
            enabled=config.crawl_characters,
            total=0,
            completed=0,
            failed=0,
            max_limit=config.max_chars
        ),
        episodes=CategoryProgress(
            enabled=config.crawl_episodes,
            total=0,
            completed=0,
            failed=0,
            max_limit=config.max_episodes
        ),
        galleries=CategoryProgress(
            enabled=config.crawl_galleries,
            total=0,
            completed=0,
            failed=0,
            max_limit=config.max_gallery_images
        ),
        chapters=CategoryProgress(
            enabled=config.crawl_chapters,
            total=0,
            completed=0,
            failed=0,
            max_limit=config.max_chapters
        ),
        overall_completed=0,
        overall_total=0
    )

    universal_scraper_state.add_log("info", f"Starting Universal Scraper for: {config.input_source}")

    # Start scraping in background
    background_tasks.add_task(run_universal_scraper, config)

    return {
        "status": "started",
        "message": f"Universal scraper started for {config.input_source}",
        "input_type": config.input_type
    }


@router.get("/universal-status", response_model=UniversalScraperStatus)
async def get_universal_status():
    """Get current Universal Scraper status with per-category progress."""
    return UniversalScraperStatus(
        status=universal_scraper_state.status,
        started_at=universal_scraper_state.started_at,
        anime_name=universal_scraper_state.anime_name,
        wiki_url=universal_scraper_state.wiki_url,
        progress=universal_scraper_state.progress,
        error=universal_scraper_state.error
    )


@router.post("/stop-universal")
async def stop_universal_scraper(current_user: dict = Depends(get_current_user)):
    """Stop the running Universal Scraper."""
    if universal_scraper_state.status not in ("running", "paused"):
        raise HTTPException(status_code=400, detail="Universal scraper is not running")

    universal_scraper_state.status = "stopped"
    universal_scraper_state.add_log("info", "Universal scraper stopped by user")

    # Terminate subprocess if running
    if universal_scraper_state._process:
        try:
            universal_scraper_state._process.terminate()
            universal_scraper_state._process.wait(timeout=5)
        except:
            universal_scraper_state._process.kill()

    if universal_scraper_state._task and not universal_scraper_state._task.done():
        universal_scraper_state._task.cancel()

    return {"status": "stopped", "message": "Universal scraper stopped"}


@router.post("/pause-universal")
async def pause_universal_scraper(current_user: dict = Depends(get_current_user)):
    """Pause the running Universal Scraper."""
    if universal_scraper_state.status != "running":
        raise HTTPException(status_code=400, detail="Universal scraper is not running")

    universal_scraper_state.status = "paused"
    universal_scraper_state.add_log("info", "Universal scraper paused")

    return {"status": "paused", "message": "Universal scraper paused"}


@router.post("/resume-universal")
async def resume_universal_scraper(current_user: dict = Depends(get_current_user)):
    """Resume the paused Universal Scraper."""
    if universal_scraper_state.status != "paused":
        raise HTTPException(status_code=400, detail="Universal scraper is not paused")

    universal_scraper_state.status = "running"
    universal_scraper_state.add_log("info", "Universal scraper resumed")

    return {"status": "running", "message": "Universal scraper resumed"}


@router.get("/universal-logs", response_model=list[ScraperLog])
async def get_universal_logs(
    limit: int = 100,
    level: Optional[str] = None
):
    """Get Universal Scraper logs."""
    logs = universal_scraper_state.logs

    if level and level != "all":
        # Handle both dict and object access for logs
        logs = [
            log for log in logs
            if (log.get("level") if isinstance(log, dict) else log.level) == level
        ]

    return logs[-limit:]


async def run_universal_scraper(config: UniversalScraperConfig):
    """
    Run the Universal Fandom Scraper in the background.

    This function spawns the UniversalFandomSpider using Scrapy's API
    and tracks progress by category.
    """
    import subprocess
    import sys

    try:
        universal_scraper_state.add_log("info", "Initializing Universal Scraper...")

        # Discover wiki URL if needed
        if config.input_type == "name":
            try:
                from utils.brave_search import BraveSearchClient
                client = BraveSearchClient()
                results = client.find_fandom_wiki(config.input_source, top_n=1)

                if not results:
                    raise ValueError(f"No Fandom wiki found for: {config.input_source}")

                universal_scraper_state.wiki_url = results[0].url
                universal_scraper_state.anime_name = config.input_source

            except Exception as e:
                universal_scraper_state.error = f"Wiki discovery failed: {str(e)}"
                universal_scraper_state.status = "stopped"
                universal_scraper_state.add_log("error", str(universal_scraper_state.error))
                return
        else:
            universal_scraper_state.wiki_url = config.input_source
            # Extract anime name from URL
            from urllib.parse import urlparse
            parsed = urlparse(config.input_source)
            universal_scraper_state.anime_name = parsed.netloc.split('.')[0].replace('-', ' ').title()

        universal_scraper_state.add_log("info", f"Wiki URL: {universal_scraper_state.wiki_url}")
        universal_scraper_state.add_log("info", f"Anime: {universal_scraper_state.anime_name}")

        # Build scrapy command
        cmd = [
            sys.executable,
            "-m", "scrapy", "crawl", "universal_fandom",
            "-a", f"input_source={universal_scraper_state.wiki_url}",
            "-a", f"input_type=url",
            "-a", f"crawl_characters={config.crawl_characters}",
            "-a", f"crawl_episodes={config.crawl_episodes}",
            "-a", f"crawl_galleries={config.crawl_galleries}",
            "-a", f"crawl_chapters={config.crawl_chapters}",
            "-a", f"max_chars={config.max_chars}",
            "-a", f"max_episodes={config.max_episodes}",
            "-a", f"max_gallery_images={config.max_gallery_images}",
            "-a", f"max_chapters={config.max_chapters}",
        ]

        universal_scraper_state.add_log("info", "Starting spider process...")

        # Start subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=Path(__file__).parent.parent.parent
        )

        universal_scraper_state._process = process

        # Monitor output
        for line in process.stdout:
            line = line.strip()
            if line:
                universal_scraper_state.add_log("info", line)

                # Parse progress from scrapy logs
                # This is simplified - real implementation would parse structured logs
                if "Scraped" in line:
                    universal_scraper_state.progress.overall_completed += 1

        # Wait for completion
        return_code = process.wait()

        if return_code == 0:
            universal_scraper_state.add_log("info", "Universal scraping completed successfully")
            universal_scraper_state.status = "idle"
        else:
            universal_scraper_state.error = f"Scraper exited with code {return_code}"
            universal_scraper_state.status = "stopped"
            universal_scraper_state.add_log("error", universal_scraper_state.error)

    except asyncio.CancelledError:
        universal_scraper_state.add_log("warning", "Universal scraper task cancelled")
        universal_scraper_state.status = "stopped"
    except Exception as e:
        logger.error(f"Universal scraper error: {e}", exc_info=True)
        universal_scraper_state.status = "stopped"
        universal_scraper_state.error = str(e)
        universal_scraper_state.add_log("error", f"Error: {e}")
