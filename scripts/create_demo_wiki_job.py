from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scraper.mediawiki.repository import WikiSQLiteRepository
from scraper.mediawiki.target import normalize_wiki_target


DEMO_JOB_ID = "demo-onepiece-action-api-001"
DEMO_WIKI_URL = "https://onepiece.fandom.com"


PAGES = [
    {
        "pageid": 1001,
        "ns": 0,
        "title": "Monkey D. Luffy",
        "length": 4821,
        "touched": "2026-01-01T00:00:00Z",
        "text": "Monkey D. Luffy is the captain of the Straw Hat Pirates and searches for the One Piece.",
        "categories": ["Category:Characters", "Category:Pirates", "Category:Straw Hat Pirates"],
        "links": ["Roronoa Zoro", "Nami", "Straw Hat Pirates"],
        "templates": ["Template:Character", "Template:Infobox character"],
        "images": ["File:Luffy Portrait.png"],
        "infobox": {"Affiliation": "Straw Hat Pirates", "Occupation": "Pirate Captain", "Origin": "Foosha Village"},
        "revision": {"revid": 9001, "parentid": 8999, "timestamp": "2026-01-01T00:00:00Z", "user": "DemoEditor", "comment": "Demo snapshot", "size": 4821, "sha1": "demo-luffy"},
    },
    {
        "pageid": 1002,
        "ns": 0,
        "title": "Roronoa Zoro",
        "length": 3910,
        "touched": "2026-01-01T00:00:00Z",
        "text": "Roronoa Zoro is a swordsman of the Straw Hat Pirates and one of Luffy's first allies.",
        "categories": ["Category:Characters", "Category:Pirates", "Category:Swordsmen"],
        "links": ["Monkey D. Luffy", "Nami", "Straw Hat Pirates"],
        "templates": ["Template:Character", "Template:Infobox character"],
        "images": ["File:Zoro Portrait.png"],
        "infobox": {"Affiliation": "Straw Hat Pirates", "Occupation": "Swordsman", "Weapon": "Three swords"},
        "revision": {"revid": 9002, "parentid": 9000, "timestamp": "2026-01-01T00:05:00Z", "user": "DemoEditor", "comment": "Demo snapshot", "size": 3910, "sha1": "demo-zoro"},
    },
    {
        "pageid": 1003,
        "ns": 0,
        "title": "Nami",
        "length": 3640,
        "touched": "2026-01-01T00:00:00Z",
        "text": "Nami is the navigator of the Straw Hat Pirates and maps the world's seas.",
        "categories": ["Category:Characters", "Category:Pirates", "Category:Navigators"],
        "links": ["Monkey D. Luffy", "Roronoa Zoro", "Straw Hat Pirates"],
        "templates": ["Template:Character", "Template:Infobox character"],
        "images": ["File:Nami Portrait.png"],
        "infobox": {"Affiliation": "Straw Hat Pirates", "Occupation": "Navigator", "Goal": "Map the world"},
        "revision": {"revid": 9003, "parentid": 9001, "timestamp": "2026-01-01T00:10:00Z", "user": "DemoEditor", "comment": "Demo snapshot", "size": 3640, "sha1": "demo-nami"},
    },
]


def create_demo_job(output_root: str | Path, *, job_id: str = DEMO_JOB_ID, overwrite: bool = True) -> Dict[str, Any]:
    output_root = Path(output_root)
    job_dir = output_root / "jobs" / job_id
    if job_dir.exists() and overwrite:
        shutil.rmtree(job_dir)
    (job_dir / "data").mkdir(parents=True, exist_ok=True)

    db_path = job_dir / "wiki.db"
    _build_wiki_db(db_path)
    _write_jsonl(job_dir / "data" / "pages.jsonl", PAGES)
    manifest = _build_manifest(job_id, job_dir)
    (job_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (job_dir / "logs").mkdir(exist_ok=True)
    (job_dir / "logs" / "scrape.log").write_text(
        "\n".join(
            [
                "demo: normalized https://onepiece.fandom.com -> https://onepiece.fandom.com/api.php",
                "demo: robots policy allowed API requests",
                "demo: stored pages/categories/links/templates/images/revisions/infoboxes into wiki.db",
                "demo: exports available as CSV/JSON and optional Parquet",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {"job_id": job_id, "job_dir": str(job_dir), "manifest": manifest}


def _build_wiki_db(db_path: Path) -> None:
    repo = WikiSQLiteRepository(db_path)
    repo.initialize()
    wiki_id = repo.upsert_wiki(normalize_wiki_target(DEMO_WIKI_URL))
    run_id = repo.start_run(
        wiki_id,
        job_id=DEMO_JOB_ID,
        config={"mode": "offline-demo", "source": DEMO_WIKI_URL, "page_limit": len(PAGES)},
    )
    for page in PAGES:
        page_id = repo.upsert_page(wiki_id, page, page_text=page["text"])
        repo.replace_page_relations(page_id, "categories", [{"title": item} for item in page["categories"]])
        repo.replace_page_relations(page_id, "links", [{"title": item, "ns": 0} for item in page["links"]])
        repo.replace_page_relations(page_id, "templates", [{"title": item, "ns": 10} for item in page["templates"]])
        repo.replace_page_relations(page_id, "images", [{"title": item} for item in page["images"]])
        repo.replace_infobox_fields(
            page_id,
            [
                {"field_name": key, "field_value": value, "source": "demo_html_infobox"}
                for key, value in page["infobox"].items()
            ],
        )
        repo.upsert_revision(page_id, page["revision"])
    repo.finish_run(run_id, "finished")
    repo.close()


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _build_manifest(job_id: str, job_dir: Path) -> Dict[str, Any]:
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": "1.0",
        "job_id": job_id,
        "status": "finished",
        "created_at": created_at,
        "anime_name": "One Piece",
        "wiki_url": DEMO_WIKI_URL,
        "api_endpoint": f"{DEMO_WIKI_URL}/api.php",
        "mode": "offline-demo",
        "compliance": {
            "robots": "allowed",
            "rate_limit_seconds": 1.0,
            "user_agent": "fandom-gui-scraper demo",
            "blocked_requests": 0,
        },
        "outputs": {
            "pages_jsonl": "data/pages.jsonl",
            "wiki_db": "wiki.db",
        },
        "wiki_db": {
            "path": "wiki.db",
            "tables": ["pages", "page_categories", "page_links", "page_templates", "page_images", "revisions", "page_infobox_fields"],
        },
        "counts": {
            "pages": len(PAGES),
            "categories": sum(len(page["categories"]) for page in PAGES),
            "links": sum(len(page["links"]) for page in PAGES),
            "templates": sum(len(page["templates"]) for page in PAGES),
            "images": sum(len(page["images"]) for page in PAGES),
            "revisions": len(PAGES),
            "infoboxes": sum(len(page["infobox"]) for page in PAGES),
        },
        "output_root": str(job_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an offline demo job with a small wiki.db.")
    parser.add_argument("--output-root", default="sample_data", help="Root folder that will contain jobs/<job_id>")
    parser.add_argument("--job-id", default=DEMO_JOB_ID)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()
    result = create_demo_job(args.output_root, job_id=args.job_id, overwrite=not args.no_overwrite)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
