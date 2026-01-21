from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


API_BASE = os.getenv("API_BASE", "http://localhost:18000/api/v1")
API_ROOT = API_BASE.rsplit("/api/v1", 1)[0] if "/api/v1" in API_BASE else API_BASE


@dataclass
class JobRun:
    name: str
    url: str
    use_playwright: bool
    use_playwright_detail_pages: bool = False
    max_chars: int = 20


WIKIS: List[JobRun] = [
    JobRun("One Piece", "https://onepiece.fandom.com", use_playwright=False, max_chars=30),
    JobRun("Naruto", "https://naruto.fandom.com", use_playwright=False, max_chars=30),
    JobRun("Dragon Ball", "https://dragonball.fandom.com", use_playwright=False, max_chars=30),
    JobRun("Bleach", "https://bleach.fandom.com", use_playwright=False, max_chars=20),
    # Playwright run to validate CF/JS path (can be slower)
    JobRun("One Piece (Playwright detail)", "https://onepiece.fandom.com", use_playwright=False, use_playwright_detail_pages=True, max_chars=15),
]


def post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}", params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def wait_job(job_id: str, timeout_s: int = 1800) -> Dict[str, Any]:
    start = time.time()
    while True:
        job = get(f"/scraper/jobs/{job_id}")
        status = job.get("status")
        if status in ("finished", "failed", "stopped"):
            return job
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Job {job_id} timed out after {timeout_s}s")
        time.sleep(2)


def main() -> int:
    results: List[Dict[str, Any]] = []
    started_at = datetime.utcnow().isoformat() + "Z"

    # Ensure API is up
    r = requests.get(f"{API_ROOT}/health", timeout=10)
    r.raise_for_status()

    for run in WIKIS:
        payload = {
            "input_source": run.url,
            "input_type": "url",
            "crawl_characters": True,
            "crawl_episodes": False,
            "crawl_galleries": False,
            "crawl_chapters": False,
            "max_chars": run.max_chars,
            "max_episodes": 0,
            "max_gallery_images": 0,
            "max_chapters": 0,
            "delay": 0.5,
            "retries": 2,
            "use_playwright": run.use_playwright,
            "use_playwright_detail_pages": run.use_playwright_detail_pages,
            "download_images": False,
            "export_mode": "jsonl",
            "export_json_gzip": True,
        }

        created = post("/scraper/start-universal", payload)
        job_id = created.get("job_id")
        if not job_id:
            raise RuntimeError(f"No job_id returned for {run.name}: {created}")

        job = wait_job(job_id)
        stats = get(f"/scraper/jobs/{job_id}/output-stats")
        logs = get(f"/scraper/jobs/{job_id}/logs", params={"limit": 200})
        manifest = get(f"/scraper/jobs/{job_id}/manifest")

        preview = None
        try:
            outputs = (manifest.get("manifest") or {}).get("outputs") or {}
            character_out = outputs.get("character") or {}
            character_path = character_out.get("path")
            if character_path:
                preview = get(f"/scraper/jobs/{job_id}/file-preview", params={"path": character_path, "limit": 3})
        except Exception:
            preview = None

        results.append(
            {
                "name": run.name,
                "url": run.url,
                "use_playwright": run.use_playwright,
                "use_playwright_detail_pages": run.use_playwright_detail_pages,
                "job_id": job_id,
                "final_status": job.get("status"),
                "error": job.get("error"),
                "progress": job.get("progress"),
                "output_stats": stats.get("stats"),
                "manifest": manifest.get("manifest"),
                "preview": preview,
                "log_tail": (logs.get("logs") or [])[-80:],
            }
        )

    report = {
        "started_at": started_at,
        "api_base": API_BASE,
        "results": results,
    }

    os.makedirs("reports", exist_ok=True)
    out_path = os.path.join("reports", f"docker_smoke_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
