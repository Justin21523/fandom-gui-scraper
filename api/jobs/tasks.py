from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from api.jobs.events import publish
from api.jobs.models import JobStatus, UniversalJobRequest, UniversalJobProgress
from api.jobs.store import update_status, update_progress, append_log, get_controls
from scraper.mediawiki import HarvestConfig, harvest_to_sqlite


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_json_parse(value: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(value)
    except Exception:
        return None


def _job_output_root(job_id: str) -> Path:
    base = Path(os.getenv("FANDOM_DATA_ROOT", "/data"))
    return base / "jobs" / job_id


def _merge_manifest(output_root: Path, updates: Dict[str, Any]) -> None:
    manifest_path = output_root / "manifest.json"
    manifest: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}
    manifest.update(updates)
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass


def _rotate_log_file(path: Path, max_bytes: int, backups: int) -> None:
    try:
        if not path.exists():
            return
        if path.stat().st_size < max_bytes:
            return
    except Exception:
        return

    try:
        # oldest -> drop
        oldest = path.with_suffix(path.suffix + f".{backups}")
        if oldest.exists():
            oldest.unlink()
    except Exception:
        pass

    # shift .(n-1) -> .n
    for i in range(backups - 1, 0, -1):
        src = path.with_suffix(path.suffix + f".{i}")
        dst = path.with_suffix(path.suffix + f".{i+1}")
        try:
            if src.exists():
                src.replace(dst)
        except Exception:
            pass

    try:
        path.replace(path.with_suffix(path.suffix + ".1"))
    except Exception:
        pass


def run_universal_job(job_id: str, config_dict: Dict[str, Any]) -> None:
    config = UniversalJobRequest.model_validate(config_dict)
    update_status(job_id, JobStatus.running)

    output_root = _job_output_root(job_id)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "logs").mkdir(parents=True, exist_ok=True)
    (output_root / "cache" / "http").mkdir(parents=True, exist_ok=True)
    (output_root / "cache" / "chromium").mkdir(parents=True, exist_ok=True)
    wiki_db_path = Path(os.getenv("WIKI_SQLITE_PATH", str(output_root / "wiki.db")))

    progress = UniversalJobProgress()
    started = _utcnow()
    wiki_harvest_result: Optional[Dict[str, Any]] = None

    def build_legacy_progress(status: str) -> Dict[str, Any]:
        return {
            "job_id": job_id,
            "status": status,
            "characters": {
                "enabled": config.crawl_characters,
                "total": 0,
                "completed": progress.characters_completed,
                "failed": 0,
                "max_limit": config.max_chars,
            },
            "episodes": {
                "enabled": config.crawl_episodes,
                "total": 0,
                "completed": progress.episodes_completed,
                "failed": 0,
                "max_limit": config.max_episodes,
            },
            "galleries": {
                "enabled": config.crawl_galleries,
                "total": 0,
                "completed": progress.galleries_completed,
                "failed": 0,
                "max_limit": config.max_gallery_images,
            },
            "chapters": {
                "enabled": config.crawl_chapters,
                "total": 0,
                "completed": progress.chapters_completed,
                "failed": 0,
                "max_limit": config.max_chapters,
            },
            "overall_completed": progress.overall_completed,
            "overall_total": progress.overall_total,
            "speed": progress.speed,
            "eta": progress.eta,
        }

    publish({"type": "universalScraperProgress", "channel": "scraping", "data": build_legacy_progress("running")})

    env = os.environ.copy()
    env.update(
        {
            "JOB_ID": job_id,
            "SCHEMA_VERSION": os.getenv("SCHEMA_VERSION", "1.0"),
            "ENABLE_FILE_EXPORT": "true",
            "FANDOM_DATA_ROOT": str(output_root),
            "DOWNLOAD_IMAGES": "true" if config.download_images else "false",
            "EXPORT_MODE": config.export_mode.value,
            "EXPORT_JSON_GZIP": "true" if config.export_json_gzip else "false",
            "ENABLE_WIKI_SQLITE": "true" if config.enable_wiki_sqlite else "false",
            "WIKI_SQLITE_PATH": str(wiki_db_path),
            "HTTPCACHE_DIR": str(output_root / "cache" / "http"),
            "PLAYWRIGHT_CACHE_DIR": str(output_root / "cache" / "chromium"),
        }
    )

    if config.enable_wiki_sqlite and config.mediawiki_page_limit > 0:
        if config.input_type == "url":
            try:
                append_log(job_id, f"Starting MediaWiki SQLite harvest: {config.input_source}")
                wiki_harvest_result = harvest_to_sqlite(
                    HarvestConfig(
                        target=config.input_source,
                        db_path=wiki_db_path,
                        job_id=job_id,
                        page_limit=config.mediawiki_page_limit,
                        include_page_text=config.include_page_text,
                        rate_delay=config.delay,
                        respect_robots=True,
                        include_infobox_html=config.include_infobox_html,
                        parse_html_limit=config.parse_html_limit,
                    )
                )
                append_log(job_id, f"MediaWiki SQLite harvest complete: {wiki_harvest_result}")
            except Exception as exc:
                wiki_harvest_result = {
                    "status": "failed",
                    "db_path": str(wiki_db_path),
                    "error": str(exc),
                    "counts": {},
                }
                append_log(job_id, f"MediaWiki SQLite harvest failed: {exc}")
        else:
            wiki_harvest_result = {
                "status": "skipped",
                "db_path": str(wiki_db_path),
                "error": "MediaWiki harvest requires input_type=url before wiki discovery is available",
                "counts": {},
            }
            append_log(job_id, "MediaWiki SQLite harvest skipped for input_type=name")

    cmd = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "universal_fandom",
        "-a",
        f"input_source={config.input_source}",
        "-a",
        f"input_type={config.input_type}",
        "-a",
        f"use_playwright={config.use_playwright}",
        "-a",
        f"use_playwright_detail_pages={config.use_playwright_detail_pages}",
        "-a",
        f"crawl_characters={config.crawl_characters}",
        "-a",
        f"crawl_episodes={config.crawl_episodes}",
        "-a",
        f"crawl_galleries={config.crawl_galleries}",
        "-a",
        f"crawl_chapters={config.crawl_chapters}",
        "-a",
        f"max_chars={config.max_chars}",
        "-a",
        f"max_episodes={config.max_episodes}",
        "-a",
        f"max_gallery_images={config.max_gallery_images}",
        "-a",
        f"max_chapters={config.max_chapters}",
        "-s",
        f"DOWNLOAD_DELAY={config.delay}",
        "-s",
        f"RETRY_TIMES={config.retries}",
        "-s",
        "FEEDS={}",  # avoid extra per-run exports; rely on FileExportPipeline
    ]

    if config.use_playwright_detail_pages:
        cmd.extend(
            [
                "-s",
                "AUTOTHROTTLE_TARGET_CONCURRENCY=1.0",
                "-s",
                "AUTOTHROTTLE_MAX_DELAY=60.0",
                "-s",
                "CONCURRENT_REQUESTS_PER_DOMAIN=2",
                "-s",
                "RETRY_BACKOFF_BASE=2",
                "-s",
                "RETRY_BACKOFF_MAX=60",
            ]
        )

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=Path(__file__).resolve().parents[2],  # repo root
        env=env,
    )

    paused = False
    last_publish = 0.0
    log_path = output_root / "logs" / "scrape.log"
    log_max_bytes = int(os.getenv("JOB_LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    log_backups = int(os.getenv("JOB_LOG_BACKUPS", "3"))

    def publish_progress(force: bool = False):
        nonlocal last_publish
        now = time.time()
        if not force and now - last_publish < 0.5:
            return
        last_publish = now
        elapsed = max(1e-3, (_utcnow() - started).total_seconds())
        progress.speed = progress.overall_completed / elapsed
        update_progress(job_id, progress)
        publish(
            {
                "type": "universalScraperProgress",
                "channel": "scraping",
                "data": build_legacy_progress("paused" if paused else "running"),
            }
        )

    try:
        assert process.stdout is not None
        for raw_line in process.stdout:
            line = raw_line.rstrip("\n")
            if line:
                _rotate_log_file(log_path, max_bytes=log_max_bytes, backups=log_backups)
                try:
                    with open(log_path, "a", encoding="utf-8") as lf:
                        lf.write(line + "\n")
                except Exception:
                    pass
                append_log(job_id, line)
                publish(
                    {
                        "type": "log",
                        "channel": "scraping",
                        "data": {
                            "job_id": job_id,
                            "timestamp": _utcnow().isoformat(),
                            "level": "info",
                            "message": line,
                        },
                    }
                )

            # Control polling
            controls = get_controls(job_id)
            if controls.get("stop") == "1":
                process.terminate()
                update_status(job_id, JobStatus.stopped)
                publish({"type": "universalScraperError", "channel": "scraping", "data": {"job_id": job_id, "message": "Stopped"}})
                return

            should_pause = controls.get("pause") == "1"
            if should_pause and not paused:
                try:
                    os.kill(process.pid, signal.SIGSTOP)
                    paused = True
                    update_status(job_id, JobStatus.paused)
                    publish({"type": "universalScraperProgress", "channel": "scraping", "data": build_legacy_progress("paused")})
                except Exception:
                    pass
            elif not should_pause and paused:
                try:
                    os.kill(process.pid, signal.SIGCONT)
                    paused = False
                    update_status(job_id, JobStatus.running)
                except Exception:
                    pass

            # Parse structured item events from spider logs
            if "EVENT item_scraped " in line:
                payload_text = line.split("EVENT item_scraped ", 1)[1].strip()
                payload = _safe_json_parse(payload_text)
                if payload:
                    content_type = payload.get("content_type")
                    progress.overall_completed += 1
                    progress.last_item = payload
                    if content_type == "character":
                        progress.characters_completed += 1
                    elif content_type == "episode":
                        progress.episodes_completed += 1
                    elif content_type == "gallery":
                        progress.galleries_completed += 1
                    elif content_type == "chapter":
                        progress.chapters_completed += 1
                    publish_progress()

        rc = process.wait()
        keep_cache = os.getenv("KEEP_JOB_CACHE", "false").lower() == "true"
        if rc == 0:
            if wiki_harvest_result:
                _merge_manifest(
                    output_root,
                    {
                        "wiki_db": {
                            "path": str(Path(wiki_harvest_result.get("db_path", wiki_db_path)).relative_to(output_root))
                            if str(wiki_harvest_result.get("db_path", wiki_db_path)).startswith(str(output_root))
                            else str(wiki_harvest_result.get("db_path", wiki_db_path)),
                            "status": wiki_harvest_result.get("status"),
                            "counts": wiki_harvest_result.get("counts", {}),
                            "error": wiki_harvest_result.get("error"),
                        }
                    },
                )
            update_status(job_id, JobStatus.finished)
            publish_progress(force=True)
            publish(
                {
                    "type": "universalScraperComplete",
                    "channel": "scraping",
                    "data": {"job_id": job_id, "overall_completed": progress.overall_completed},
                }
            )
            if not keep_cache:
                try:
                    shutil.rmtree(output_root / "cache")
                except Exception:
                    pass
        else:
            update_status(job_id, JobStatus.failed, error=f"Scraper exited with code {rc}")
            publish({"type": "universalScraperError", "channel": "scraping", "data": {"job_id": job_id, "message": f"Scraper exited with code {rc}"}})
            # Keep cache on failures unless explicitly disabled
            if not keep_cache:
                try:
                    shutil.rmtree(output_root / "cache")
                except Exception:
                    pass

    except Exception as e:
        try:
            process.kill()
        except Exception:
            pass
        update_status(job_id, JobStatus.failed, error=str(e))
        publish({"type": "universalScraperError", "channel": "scraping", "data": {"job_id": job_id, "message": str(e)}})
