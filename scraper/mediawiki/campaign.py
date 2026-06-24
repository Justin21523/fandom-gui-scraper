from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

from .harvester import HarvestConfig, harvest_to_sqlite
from .query import WikiDBQueryService
from .target import normalize_wiki_target


DEFAULT_CAMPAIGN_ID = "portfolio-smoke"
DEFAULT_TARGETS = [
    "https://onepiece.fandom.com",
    "https://stardewvalley.fandom.com",
    "https://fallout.fandom.com",
    "https://starwars.fandom.com",
    "https://zelda.fandom.com",
]


@dataclass(frozen=True)
class CampaignConfig:
    campaign_id: str = DEFAULT_CAMPAIGN_ID
    targets: List[str] = field(default_factory=lambda: list(DEFAULT_TARGETS))
    output_root: str | Path = "sample_data"
    page_limit: int = 50
    batch_size: int = 25
    rate_delay: float = 1.0
    include_page_text: bool = True
    include_infobox_html: bool = True
    parse_html_limit: int = 10
    respect_robots: bool = True
    force: bool = False


def run_campaign(config: CampaignConfig) -> Dict[str, Any]:
    root = Path(config.output_root)
    campaign_dir = root / "campaigns" / _safe_id(config.campaign_id)
    jobs_root = root / "jobs"
    campaign_dir.mkdir(parents=True, exist_ok=True)
    jobs_root.mkdir(parents=True, exist_ok=True)
    events_path = campaign_dir / "campaign_events.jsonl"
    if config.force and events_path.exists():
        events_path.unlink()
    if config.force:
        expected_job_ids = {f"{_safe_id(config.campaign_id)}-{_wiki_slug(normalize_wiki_target(target).base_url)}" for target in config.targets}
        for stale_dir in jobs_root.glob(f"{_safe_id(config.campaign_id)}-*"):
            if stale_dir.is_dir() and stale_dir.name not in expected_job_ids:
                shutil.rmtree(stale_dir, ignore_errors=True)

    started_at = _utcnow()
    jobs = []
    summary = {
        "pages": 0,
        "categories": 0,
        "links": 0,
        "templates": 0,
        "images": 0,
        "revisions": 0,
        "infoboxes": 0,
        "errors": 0,
    }

    _append_event(events_path, config.campaign_id, None, None, "campaign_start", "running", "Campaign started")
    _write_campaign_manifest(campaign_dir, config, started_at, None, "running", summary, jobs)
    for target in config.targets:
        target_info = normalize_wiki_target(target)
        wiki_slug = _wiki_slug(target_info.base_url)
        job_id = f"{_safe_id(config.campaign_id)}-{wiki_slug}"
        job_dir = jobs_root / job_id
        db_path = job_dir / "wiki.db"
        manifest_path = job_dir / "manifest.json"
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "logs").mkdir(exist_ok=True)

        if not config.force and manifest_path.exists() and db_path.exists():
            manifest = _read_json(manifest_path)
            if manifest.get("status") == "finished":
                jobs.append(_job_summary_from_manifest(manifest, job_id, job_dir))
                _merge_counts(summary, (manifest.get("wiki_db") or {}).get("counts") or {})
                _append_event(events_path, config.campaign_id, job_id, target, "skip", "finished", "Existing finished job reused")
                _write_campaign_manifest(campaign_dir, config, started_at, None, "running", summary, jobs)
                continue

        _append_event(events_path, config.campaign_id, job_id, target, "normalize", "passed", f"Normalized to {target_info.api_url}")
        _append_event(events_path, config.campaign_id, job_id, target, "harvest", "running", "MediaWiki Action API harvest started")
        status = "finished"
        error = None
        result: Dict[str, Any] = {}
        try:
            result = harvest_to_sqlite(
                HarvestConfig(
                    target=target,
                    db_path=db_path,
                    job_id=job_id,
                    page_limit=config.page_limit,
                    batch_size=config.batch_size,
                    include_page_text=config.include_page_text,
                    resume=not config.force,
                    rate_delay=config.rate_delay,
                    respect_robots=config.respect_robots,
                    include_infobox_html=config.include_infobox_html,
                    parse_html_limit=config.parse_html_limit,
                )
            )
            status = result.get("status") or "finished"
            error = result.get("error")
            _append_event(events_path, config.campaign_id, job_id, target, "sqlite", status, "wiki.db written", result.get("counts") or {})
        except Exception as exc:
            status = "failed"
            error = str(exc)
            result = {"status": status, "counts": {}, "error": error, "db_path": str(db_path)}
            _append_event(events_path, config.campaign_id, job_id, target, "harvest", "failed", error)

        manifest = _build_job_manifest(config, job_id, job_dir, target_info, status, result, error)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (job_dir / "logs" / "scrape.log").write_text(_job_log_text(events_path, job_id), encoding="utf-8")
        job_summary = _job_summary_from_manifest(manifest, job_id, job_dir)
        jobs.append(job_summary)
        _merge_counts(summary, (manifest.get("wiki_db") or {}).get("counts") or {})
        _write_campaign_manifest(campaign_dir, config, started_at, None, "running", summary, jobs)

    finished_at = _utcnow()
    analysis = analyze_campaign(campaign_dir=campaign_dir, jobs=jobs)
    final_status = "finished" if all(job["status"] in {"finished", "stopped"} for job in jobs) else "partial"
    manifest = _write_campaign_manifest(campaign_dir, config, started_at, finished_at, final_status, summary, jobs, analysis)
    _append_event(events_path, config.campaign_id, None, None, "campaign_finish", manifest["status"], "Campaign finished", summary)
    return manifest


def list_campaigns(output_root: str | Path = "sample_data", limit: int = 20) -> List[Dict[str, Any]]:
    root = Path(output_root) / "campaigns"
    if not root.exists():
        return []
    campaigns = []
    for path in sorted(root.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        manifest = path / "campaign.json"
        if manifest.exists():
            campaigns.append(_read_json(manifest))
        if len(campaigns) >= limit:
            break
    return campaigns


def load_campaign(campaign_id: str, output_root: str | Path = "sample_data") -> Dict[str, Any]:
    path = Path(output_root) / "campaigns" / _safe_id(campaign_id) / "campaign.json"
    if not path.exists():
        raise FileNotFoundError(campaign_id)
    return _read_json(path)


def load_campaign_events(campaign_id: str, output_root: str | Path = "sample_data", limit: int = 500) -> List[Dict[str, Any]]:
    path = Path(output_root) / "campaigns" / _safe_id(campaign_id) / "campaign_events.jsonl"
    if not path.exists():
        return []
    events = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                events.append({"message": line})
    return events[-limit:]


def analyze_campaign(*, campaign_dir: Path, jobs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    per_wiki = []
    overview = {
        "pages": 0,
        "categories": 0,
        "links": 0,
        "templates": 0,
        "images": 0,
        "revisions": 0,
        "infoboxes": 0,
        "errors": 0,
    }
    top_categories: Dict[str, int] = {}
    network_nodes: Dict[str, int] = {}
    network_edges = []
    for job in jobs:
        db_path = Path(job["output_root"]) / "wiki.db"
        if not db_path.exists():
            per_wiki.append({"job_id": job["job_id"], "wiki": job.get("wiki_url"), "status": job.get("status"), "counts": {}, "quality": []})
            continue
        service = WikiDBQueryService(db_path)
        summary = service.summary()
        analysis = service.analysis()
        counts = summary.get("counts") or {}
        for key in overview:
            overview[key] += int(counts.get(key, 0) or 0)
        for item in analysis.get("category_counts") or []:
            top_categories[item["label"]] = top_categories.get(item["label"], 0) + int(item["value"])
        for node in (analysis.get("network") or {}).get("nodes") or []:
            network_nodes[node["id"]] = network_nodes.get(node["id"], 0) + int(node.get("degree") or 0)
        network_edges.extend(((analysis.get("network") or {}).get("edges") or [])[:20])
        per_wiki.append(
            {
                "job_id": job["job_id"],
                "wiki": job.get("wiki_url"),
                "status": job.get("status"),
                "counts": counts,
                "quality": analysis.get("quality") or [],
            }
        )
    return {
        "overview": overview,
        "per_wiki": per_wiki,
        "category_counts": [{"label": key, "value": value} for key, value in sorted(top_categories.items(), key=lambda item: item[1], reverse=True)[:20]],
        "network": {
            "nodes": [{"id": key, "degree": value} for key, value in sorted(network_nodes.items(), key=lambda item: item[1], reverse=True)[:30]],
            "edges": network_edges[:100],
        },
    }


def _write_campaign_manifest(
    campaign_dir: Path,
    config: CampaignConfig,
    started_at: str,
    finished_at: str | None,
    status: str,
    summary: Dict[str, int],
    jobs: List[Dict[str, Any]],
    analysis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    manifest = {
        "schema_version": "1.0",
        "campaign_id": config.campaign_id,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "targets": list(config.targets),
        "config": {
            "page_limit": config.page_limit,
            "batch_size": config.batch_size,
            "rate_delay": config.rate_delay,
            "parse_html_limit": config.parse_html_limit,
            "respect_robots": config.respect_robots,
        },
        "summary": dict(summary),
        "jobs": list(jobs),
        "analysis": analysis or {},
        "events_path": "campaign_events.jsonl",
    }
    (campaign_dir / "campaign.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return manifest


def _build_job_manifest(config: CampaignConfig, job_id: str, job_dir: Path, target_info: Any, status: str, result: Dict[str, Any], error: str | None) -> Dict[str, Any]:
    counts = _normalized_counts(result.get("counts") or {})
    return {
        "schema_version": "1.0",
        "job_id": job_id,
        "status": status,
        "created_at": _utcnow(),
        "finished_at": _utcnow(),
        "anime_name": target_info.host.split(".")[0].replace("-", " ").title(),
        "wiki_url": target_info.base_url,
        "api_endpoint": target_info.api_url,
        "mode": "campaign-live",
        "compliance": {
            "robots": "respected" if config.respect_robots else "disabled",
            "rate_limit_seconds": config.rate_delay,
            "user_agent": "FandomGuiScraper/1.0",
            "blocked_requests": counts.get("crawl_errors", 0),
        },
        "outputs": {"wiki_db": "wiki.db"},
        "wiki_db": {"path": "wiki.db", "status": status, "counts": counts, "error": error},
        "counts": counts,
        "output_root": str(job_dir),
    }


def _job_summary_from_manifest(manifest: Dict[str, Any], job_id: str, job_dir: Path) -> Dict[str, Any]:
    return {
        "job_id": manifest.get("job_id") or job_id,
        "wiki_url": manifest.get("wiki_url"),
        "api_endpoint": manifest.get("api_endpoint"),
        "status": manifest.get("status", "unknown"),
        "counts": (manifest.get("wiki_db") or {}).get("counts") or manifest.get("counts") or {},
        "error": (manifest.get("wiki_db") or {}).get("error") or manifest.get("error"),
        "output_root": str(job_dir),
        "wiki_db_path": str(job_dir / ((manifest.get("wiki_db") or {}).get("path") or "wiki.db")),
    }


def _append_event(path: Path, campaign_id: str, job_id: str | None, wiki_url: str | None, stage: str, status: str, message: str, details: Dict[str, Any] | None = None) -> None:
    event = {
        "time": _utcnow(),
        "campaign_id": campaign_id,
        "job_id": job_id,
        "wiki_url": wiki_url,
        "stage": stage,
        "status": status,
        "message": message,
        "details": details or {},
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def _job_log_text(events_path: Path, job_id: str) -> str:
    events = []
    if events_path.exists():
        with open(events_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    return "\n".join(
        f"{event.get('time')} [{event.get('status')}] {event.get('stage')}: {event.get('message')}"
        for event in events
        if event.get("job_id") == job_id
    ) + "\n"


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-").lower()
    if not safe:
        raise ValueError("campaign_id is required")
    return safe


def _wiki_slug(url: str) -> str:
    host = urlparse(url).netloc or urlparse(f"https://{url}").netloc
    return _safe_id(host.split(".")[0])


def _merge_counts(total: Dict[str, int], counts: Dict[str, Any]) -> None:
    counts = _normalized_counts(counts)
    for key, value in counts.items():
        if key in total:
            total[key] += int(value or 0)


def _normalized_counts(counts: Dict[str, Any]) -> Dict[str, int]:
    key_map = {
        "page_categories": "categories",
        "page_links": "links",
        "page_templates": "templates",
        "page_images": "images",
        "page_infobox_fields": "infoboxes",
        "crawl_errors": "errors",
    }
    normalized: Dict[str, int] = {}
    for key, value in counts.items():
        out_key = key_map.get(key, key)
        normalized[out_key] = normalized.get(out_key, 0) + int(value or 0)
    return normalized


def _read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
