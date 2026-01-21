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

    progress = UniversalJobProgress()
    started = _utcnow()

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
            "HTTPCACHE_DIR": str(output_root / "cache" / "http"),
            "PLAYWRIGHT_CACHE_DIR": str(output_root / "cache" / "chromium"),
        }
    )

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
