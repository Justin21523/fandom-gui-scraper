from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any

from api.jobs.store import list_jobs, delete_job_metadata


def _dir_size_bytes(path: Path) -> int:
    total = 0
    try:
        for p in path.rglob("*"):
            try:
                if p.is_file():
                    total += p.stat().st_size
            except Exception:
                continue
    except Exception:
        return total
    return total


def _enforce_cache_limit(job_dir: Path, max_cache_bytes: int) -> Dict[str, Any]:
    cache_dir = job_dir / "cache"
    if not cache_dir.exists() or max_cache_bytes <= 0:
        return {"cache_deleted": False, "cache_bytes": 0}

    size = _dir_size_bytes(cache_dir)
    if size <= max_cache_bytes:
        return {"cache_deleted": False, "cache_bytes": size}

    try:
        shutil.rmtree(cache_dir)
        return {"cache_deleted": True, "cache_bytes": size}
    except Exception:
        return {"cache_deleted": False, "cache_bytes": size}


def cleanup_expired_jobs(now: datetime | None = None, limit: int = 500) -> Dict[str, Any]:
    """
    Cleanup job outputs with:
    - TTL per job (keep_job_days)
    - Global max total bytes across job outputs (JOBS_MAX_TOTAL_BYTES)
    - Per-job cache cap (JOB_CACHE_MAX_BYTES) by deleting cache/ when oversized
    """
    now = now or datetime.now(timezone.utc)
    jobs = list_jobs(limit=limit)

    deleted: List[str] = []
    kept: List[str] = []
    errors: Dict[str, str] = {}
    cache_evictions: Dict[str, Any] = {}

    base_root = Path(os.getenv("FANDOM_DATA_ROOT", "/data")) / "jobs"
    max_total_bytes = int(os.getenv("JOBS_MAX_TOTAL_BYTES", str(50 * 1024 * 1024 * 1024)))
    max_cache_bytes = int(os.getenv("JOB_CACHE_MAX_BYTES", str(1024 * 1024 * 1024)))

    # First: delete jobs past their keep_job_days
    for job in jobs:
        keep_days = job.config.keep_job_days
        cutoff = now - timedelta(days=keep_days)
        if job.created_at >= cutoff:
            kept.append(job.job_id)
            continue

        job_dir = base_root / job.job_id
        try:
            if job_dir.exists():
                shutil.rmtree(job_dir)
            delete_job_metadata(job.job_id)
            deleted.append(job.job_id)
        except Exception as e:
            errors[job.job_id] = str(e)

    # Second: enforce per-job cache limit for kept jobs
    for job_id in list(kept):
        job_dir = base_root / job_id
        try:
            cache_evictions[job_id] = _enforce_cache_limit(job_dir, max_cache_bytes=max_cache_bytes)
        except Exception as e:
            errors[job_id] = str(e)

    # Third: enforce global storage cap by deleting oldest kept jobs
    if max_total_bytes > 0:
        # Sort kept job_ids by created_at ascending (oldest first)
        kept_jobs = [j for j in jobs if j.job_id in kept]
        kept_jobs.sort(key=lambda j: j.created_at)

        total = 0
        sizes: Dict[str, int] = {}
        for j in kept_jobs:
            job_dir = base_root / j.job_id
            sizes[j.job_id] = _dir_size_bytes(job_dir) if job_dir.exists() else 0
            total += sizes[j.job_id]

        while total > max_total_bytes and kept_jobs:
            oldest = kept_jobs.pop(0)
            job_dir = base_root / oldest.job_id
            try:
                if job_dir.exists():
                    shutil.rmtree(job_dir)
                delete_job_metadata(oldest.job_id)
                deleted.append(oldest.job_id)
                kept.remove(oldest.job_id)
                total -= sizes.get(oldest.job_id, 0)
            except Exception as e:
                errors[oldest.job_id] = str(e)
                break

    return {
        "deleted": deleted,
        "kept": kept,
        "errors": errors,
        "cache_evictions": cache_evictions,
        "max_total_bytes": max_total_bytes,
        "max_cache_bytes": max_cache_bytes,
    }


if __name__ == "__main__":
    result = cleanup_expired_jobs()
    print(result)
