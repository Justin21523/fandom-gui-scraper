from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from .client import MediaWikiActionClient
from .errors import AccessRestrictedError, MediaWikiAPIError, RobotsDeniedError
from .infobox import parse_infobox_fields
from .repository import WikiSQLiteRepository
from .target import WikiTarget, normalize_wiki_target


CHECKPOINT_ALLPAGES = "allpages_continue"


@dataclass(frozen=True)
class HarvestConfig:
    target: str
    db_path: str | Path
    job_id: str | None = None
    page_limit: int = 200
    batch_size: int = 50
    include_page_text: bool = True
    resume: bool = True
    rate_delay: float = 1.0
    respect_robots: bool = True
    include_infobox_html: bool = True
    parse_html_limit: int = 25


class MediaWikiHarvester:
    """Harvest MediaWiki Action API records into SQLite."""

    def __init__(
        self,
        config: HarvestConfig,
        *,
        client: MediaWikiActionClient | None = None,
        repository: WikiSQLiteRepository | None = None,
    ):
        self.config = config
        self.target: WikiTarget = normalize_wiki_target(config.target)
        self.client = client or MediaWikiActionClient(
            self.target,
            rate_delay=config.rate_delay,
            respect_robots=config.respect_robots,
        )
        self.repository = repository or WikiSQLiteRepository(config.db_path)
        self._owns_repository = repository is None
        self._run_id: int | None = None
        self._parse_count = 0
        self._parse_disabled = False

    def run(self) -> Dict[str, Any]:
        self.repository.initialize()
        wiki_id = self.repository.upsert_wiki(self.target)
        run_id = self.repository.start_run(
            wiki_id,
            job_id=self.config.job_id,
            config={
                "target": self.config.target,
                "page_limit": self.config.page_limit,
                "batch_size": self.config.batch_size,
                "include_page_text": self.config.include_page_text,
                "resume": self.config.resume,
                "include_infobox_html": self.config.include_infobox_html,
                "parse_html_limit": self.config.parse_html_limit,
            },
        )
        self._run_id = run_id
        self._parse_count = 0
        self._parse_disabled = False

        pages_seen = 0
        seen_page_keys: set[str] = set()
        status = "finished"
        error: str | None = None
        try:
            continue_params = self.repository.get_checkpoint(wiki_id, CHECKPOINT_ALLPAGES) if self.config.resume else None
            while pages_seen < self.config.page_limit:
                params = self._build_allpages_params(
                    limit=min(self.config.batch_size, self.config.page_limit - pages_seen),
                    continue_params=continue_params,
                )
                payload = self.client.get(params)
                pages = self._extract_pages(payload)
                for page in pages:
                    key = str(page.get("pageid") or page.get("title") or "")
                    self._store_page(wiki_id, page)
                    if key and key not in seen_page_keys:
                        seen_page_keys.add(key)
                        pages_seen += 1

                next_continue = payload.get("continue")
                if not next_continue:
                    self.repository.clear_checkpoint(wiki_id, CHECKPOINT_ALLPAGES)
                    break
                self.repository.set_checkpoint(wiki_id, CHECKPOINT_ALLPAGES, dict(next_continue))
                continue_params = dict(next_continue)
                if not pages:
                    break

        except (RobotsDeniedError, AccessRestrictedError) as exc:
            status = "stopped"
            error = str(exc)
            self.repository.record_error(run_id, exc.__class__.__name__, str(exc), {"target": self.target.api_url})
        except Exception as exc:
            status = "failed"
            error = str(exc)
            self.repository.record_error(run_id, exc.__class__.__name__, str(exc), {"target": self.target.api_url})
        finally:
            self.repository.finish_run(run_id, status, error=error)
            counts = self.repository.get_counts()
            if self._owns_repository:
                self.repository.close()

        if status == "failed":
            raise MediaWikiAPIError(error or "MediaWiki harvest failed")

        return {
            "status": status,
            "run_id": run_id,
            "wiki_id": wiki_id,
            "target": self.target.base_url,
            "db_path": str(self.config.db_path),
            "pages_seen": pages_seen,
            "counts": counts,
            "error": error,
        }

    def _build_allpages_params(self, *, limit: int, continue_params: Mapping[str, Any] | None) -> Dict[str, Any]:
        rvprop = ["ids", "timestamp", "user", "comment", "size", "sha1"]
        if self.config.include_page_text:
            rvprop.append("content")

        params: Dict[str, Any] = {
            "action": "query",
            "generator": "allpages",
            "gapnamespace": 0,
            "gaplimit": max(1, min(500, limit)),
            "prop": "info|categories|links|templates|images|revisions",
            "cllimit": "max",
            "pllimit": "max",
            "tllimit": "max",
            "imlimit": "max",
            "rvprop": "|".join(rvprop),
            "gapfilterredir": "nonredirects",
        }
        if continue_params:
            params.update(dict(continue_params))
        return params

    @staticmethod
    def _extract_pages(payload: Mapping[str, Any]) -> list[Dict[str, Any]]:
        pages = (payload.get("query") or {}).get("pages") or []
        if isinstance(pages, dict):
            return [dict(page) for page in pages.values()]
        return [dict(page) for page in pages]

    def _store_page(self, wiki_id: int, page: Mapping[str, Any]) -> None:
        revisions = list(page.get("revisions") or [])
        page_text = self._extract_page_text(revisions[0]) if revisions else None
        page_id = self.repository.upsert_page(wiki_id, page, page_text=page_text)

        self.repository.replace_page_relations(page_id, "categories", list(page.get("categories") or []))
        self.repository.replace_page_relations(page_id, "links", list(page.get("links") or []))
        self.repository.replace_page_relations(page_id, "templates", list(page.get("templates") or []))
        self.repository.replace_page_relations(page_id, "images", list(page.get("images") or []))
        infobox_fields = self._extract_infobox_fields(page)
        if not infobox_fields:
            infobox_fields = self._fetch_parse_infobox_fields(page)
        self.repository.replace_infobox_fields(page_id, infobox_fields)

        for revision in revisions:
            self.repository.upsert_revision(page_id, revision)

    @staticmethod
    def _extract_page_text(revision: Mapping[str, Any]) -> str | None:
        if "content" in revision:
            return str(revision.get("content") or "")
        slots = revision.get("slots")
        if isinstance(slots, Mapping):
            main = slots.get("main")
            if isinstance(main, Mapping):
                if "content" in main:
                    return str(main.get("content") or "")
                if "*" in main:
                    return str(main.get("*") or "")
        if "*" in revision:
            return str(revision.get("*") or "")
        return None

    @staticmethod
    def _extract_infobox_fields(page: Mapping[str, Any]) -> list[Dict[str, str]]:
        html = page.get("html") or page.get("parse_html")
        parse = page.get("parse")
        if not html and isinstance(parse, Mapping):
            html = parse.get("text") or parse.get("html")
        if isinstance(html, Mapping):
            html = html.get("*")
        return parse_infobox_fields(str(html or ""))

    def _fetch_parse_infobox_fields(self, page: Mapping[str, Any]) -> list[Dict[str, str]]:
        if not self.config.include_infobox_html or self._parse_disabled:
            return []
        if self._parse_count >= max(0, self.config.parse_html_limit):
            return []
        pageid = page.get("pageid")
        if not pageid:
            return []
        try:
            payload = self.client.get(
                {
                    "action": "parse",
                    "pageid": pageid,
                    "prop": "text",
                    "disableeditsection": 1,
                    "disabletoc": 1,
                }
            )
            self._parse_count += 1
        except (RobotsDeniedError, AccessRestrictedError) as exc:
            self._parse_disabled = True
            self._record_parse_error(exc, pageid)
            return []
        except Exception as exc:
            self._record_parse_error(exc, pageid)
            return []

        parse = payload.get("parse") if isinstance(payload, Mapping) else None
        html = None
        if isinstance(parse, Mapping):
            html = parse.get("text") or parse.get("html")
        if isinstance(html, Mapping):
            html = html.get("*")
        return parse_infobox_fields(str(html or ""))

    def _record_parse_error(self, exc: Exception, pageid: Any) -> None:
        if self._run_id is None:
            return
        self.repository.record_error(
            self._run_id,
            exc.__class__.__name__,
            f"HTML parse fallback failed for pageid={pageid}: {exc}",
            {"pageid": pageid, "target": self.target.api_url, "fallback": "action=parse"},
        )


def harvest_to_sqlite(config: HarvestConfig) -> Dict[str, Any]:
    return MediaWikiHarvester(config).run()


def main() -> int:
    parser = argparse.ArgumentParser(description="Harvest MediaWiki Action API data into SQLite.")
    parser.add_argument("--target", required=True, help="Fandom URL or explicit MediaWiki api.php endpoint")
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--no-page-text", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--rate-delay", type=float, default=1.0)
    parser.add_argument("--ignore-robots", action="store_true")
    parser.add_argument("--no-infobox-html", action="store_true")
    parser.add_argument("--parse-html-limit", type=int, default=25)
    args = parser.parse_args()

    result = harvest_to_sqlite(
        HarvestConfig(
            target=args.target,
            db_path=args.db,
            job_id=args.job_id,
            page_limit=args.limit,
            batch_size=args.batch_size,
            include_page_text=not args.no_page_text,
            resume=not args.no_resume,
            rate_delay=args.rate_delay,
            respect_robots=not args.ignore_robots,
            include_infobox_html=not args.no_infobox_html,
            parse_html_limit=args.parse_html_limit,
        )
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
