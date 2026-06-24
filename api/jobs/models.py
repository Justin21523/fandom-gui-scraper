from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Literal, Dict, Any

from pydantic import BaseModel, Field


class ExportMode(str, Enum):
    per_item = "per_item"
    jsonl = "jsonl"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    paused = "paused"
    finished = "finished"
    failed = "failed"
    stopped = "stopped"


class UniversalJobRequest(BaseModel):
    input_source: str = Field(..., description="Anime name or Fandom wiki URL")
    input_type: Literal["name", "url"] = Field(default="url")

    crawl_characters: bool = True
    crawl_episodes: bool = True
    crawl_galleries: bool = True
    crawl_chapters: bool = False

    max_chars: int = Field(default=100, ge=0)
    max_episodes: int = Field(default=50, ge=0)
    max_gallery_images: int = Field(default=200, ge=0)
    max_chapters: int = Field(default=50, ge=0)

    delay: float = Field(default=1.0, ge=0, le=10)
    retries: int = Field(default=3, ge=0, le=10)

    use_playwright: bool = False
    use_playwright_detail_pages: bool = False
    download_images: bool = False

    export_mode: ExportMode = ExportMode.jsonl
    export_json_gzip: bool = True

    enable_wiki_sqlite: bool = True
    mediawiki_page_limit: int = Field(default=200, ge=0)
    include_page_text: bool = True
    include_infobox_html: bool = True
    parse_html_limit: int = Field(default=25, ge=0, le=500)

    # retention
    keep_job_days: int = Field(default=14, ge=1, le=365)


class UniversalJobProgress(BaseModel):
    overall_completed: int = 0
    overall_total: int = 0
    characters_completed: int = 0
    episodes_completed: int = 0
    galleries_completed: int = 0
    chapters_completed: int = 0
    speed: Optional[float] = None
    eta: Optional[int] = None
    last_item: Optional[Dict[str, Any]] = None


class UniversalJobInfo(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    config: UniversalJobRequest
    progress: UniversalJobProgress = Field(default_factory=UniversalJobProgress)
    output_root: str
    error: Optional[str] = None
