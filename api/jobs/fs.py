from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


def get_jobs_root() -> Path:
    return Path(os.getenv("FANDOM_DATA_ROOT", "/data")) / "jobs"


def get_job_dir(job_id: str) -> Path:
    # basic hardening
    safe = "".join(ch for ch in job_id if ch.isalnum() or ch in ("-", "_"))
    return get_jobs_root() / safe


def compute_output_stats(job_dir: Path) -> Dict[str, Any]:
    total_bytes = 0
    total_files = 0
    by_ext: Dict[str, Dict[str, int]] = {}

    if not job_dir.exists():
        return {"exists": False, "total_files": 0, "total_bytes": 0, "by_ext": {}}

    for path in job_dir.rglob("*"):
        if not path.is_file():
            continue
        total_files += 1
        size = path.stat().st_size
        total_bytes += size
        ext = path.suffix.lower() or "no_ext"
        bucket = by_ext.setdefault(ext, {"files": 0, "bytes": 0})
        bucket["files"] += 1
        bucket["bytes"] += size

    return {
        "exists": True,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "by_ext": by_ext,
    }


def list_files(job_dir: Path, max_entries: int = 2000) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not job_dir.exists():
        return items

    base = job_dir.resolve()
    for path in sorted(job_dir.rglob("*")):
        if len(items) >= max_entries:
            break
        try:
            resolved = path.resolve()
            if base not in resolved.parents and resolved != base:
                continue
        except Exception:
            continue

        rel = str(path.relative_to(job_dir))
        if path.is_dir():
            items.append({"path": rel, "type": "dir"})
        else:
            try:
                st = path.stat()
                items.append({"path": rel, "type": "file", "bytes": st.st_size})
            except Exception:
                items.append({"path": rel, "type": "file", "bytes": None})
    return items


def build_zip(job_dir: Path, zip_path: Path, include_images: bool = True) -> None:
    """
    Create a zip archive of job output. If include_images is False, skip any images/ folder.
    """
    base = job_dir.resolve()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in job_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                resolved = path.resolve()
                if base not in resolved.parents and resolved != base:
                    continue
            except Exception:
                continue

            rel = path.relative_to(job_dir)
            if not include_images and str(rel).startswith("images/"):
                continue
            zf.write(path, arcname=str(rel))

