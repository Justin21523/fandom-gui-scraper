from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

from .target import WikiTarget


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


class WikiSQLiteRepository:
    """SQLite store for MediaWiki-native crawl data."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")

    def close(self) -> None:
        self.conn.close()

    def initialize(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS wikis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original TEXT NOT NULL,
                base_url TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                host TEXT NOT NULL,
                is_fandom INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS crawl_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wiki_id INTEGER NOT NULL REFERENCES wikis(id) ON DELETE CASCADE,
                job_id TEXT,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                error TEXT
            );

            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wiki_id INTEGER NOT NULL REFERENCES wikis(id) ON DELETE CASCADE,
                pageid INTEGER,
                ns INTEGER,
                title TEXT NOT NULL,
                touched TEXT,
                length INTEGER,
                is_redirect INTEGER NOT NULL DEFAULT 0,
                page_text TEXT,
                raw_json TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(wiki_id, pageid),
                UNIQUE(wiki_id, title)
            );

            CREATE TABLE IF NOT EXISTS page_categories (
                page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
                category_title TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                PRIMARY KEY(page_id, category_title)
            );

            CREATE TABLE IF NOT EXISTS page_links (
                page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
                target_title TEXT NOT NULL,
                target_ns INTEGER,
                raw_json TEXT NOT NULL,
                PRIMARY KEY(page_id, target_title)
            );

            CREATE TABLE IF NOT EXISTS page_templates (
                page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
                template_title TEXT NOT NULL,
                template_ns INTEGER,
                raw_json TEXT NOT NULL,
                PRIMARY KEY(page_id, template_title)
            );

            CREATE TABLE IF NOT EXISTS page_images (
                page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
                image_title TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                PRIMARY KEY(page_id, image_title)
            );

            CREATE TABLE IF NOT EXISTS page_infobox_fields (
                page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
                field_name TEXT NOT NULL,
                field_value TEXT NOT NULL,
                source TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                PRIMARY KEY(page_id, field_name, field_value)
            );

            CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
                revid INTEGER NOT NULL UNIQUE,
                parentid INTEGER,
                timestamp TEXT,
                user TEXT,
                comment TEXT,
                size INTEGER,
                sha1 TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS crawl_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES crawl_runs(id) ON DELETE CASCADE,
                error_type TEXT NOT NULL,
                message TEXT NOT NULL,
                context_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checkpoints (
                wiki_id INTEGER NOT NULL REFERENCES wikis(id) ON DELETE CASCADE,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(wiki_id, key)
            );

            CREATE INDEX IF NOT EXISTS idx_pages_wiki_title ON pages(wiki_id, title);
            CREATE INDEX IF NOT EXISTS idx_revisions_page ON revisions(page_id);
            CREATE INDEX IF NOT EXISTS idx_runs_wiki ON crawl_runs(wiki_id, started_at);
            """
        )
        self.conn.commit()

    def upsert_wiki(self, target: WikiTarget) -> int:
        now = _utcnow()
        self.conn.execute(
            """
            INSERT INTO wikis (original, base_url, api_url, host, is_fandom, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(base_url) DO UPDATE SET
                original=excluded.original,
                api_url=excluded.api_url,
                host=excluded.host,
                is_fandom=excluded.is_fandom,
                updated_at=excluded.updated_at
            """,
            (target.original, target.base_url, target.api_url, target.host, int(target.is_fandom), now, now),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM wikis WHERE base_url = ?", (target.base_url,)).fetchone()
        return int(row["id"])

    def start_run(self, wiki_id: int, *, job_id: str | None, config: Mapping[str, Any]) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO crawl_runs (wiki_id, job_id, status, config_json, started_at)
            VALUES (?, ?, 'running', ?, ?)
            """,
            (wiki_id, job_id, _json(dict(config)), _utcnow()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, status: str, error: str | None = None) -> None:
        self.conn.execute(
            "UPDATE crawl_runs SET status = ?, finished_at = ?, error = ? WHERE id = ?",
            (status, _utcnow(), error, run_id),
        )
        self.conn.commit()

    def record_error(self, run_id: int, error_type: str, message: str, context: Mapping[str, Any] | None = None) -> None:
        self.conn.execute(
            """
            INSERT INTO crawl_errors (run_id, error_type, message, context_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, error_type, message, _json(dict(context or {})), _utcnow()),
        )
        self.conn.commit()

    def upsert_page(self, wiki_id: int, page_payload: Mapping[str, Any], *, page_text: str | None = None) -> int:
        now = _utcnow()
        pageid = page_payload.get("pageid")
        title = str(page_payload.get("title") or "")
        if not title:
            raise ValueError("page title is required")

        self.conn.execute(
            """
            INSERT INTO pages (
                wiki_id, pageid, ns, title, touched, length, is_redirect,
                page_text, raw_json, first_seen_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(wiki_id, pageid) DO UPDATE SET
                ns=excluded.ns,
                title=excluded.title,
                touched=excluded.touched,
                length=excluded.length,
                is_redirect=excluded.is_redirect,
                page_text=excluded.page_text,
                raw_json=excluded.raw_json,
                updated_at=excluded.updated_at
            """,
            (
                wiki_id,
                pageid,
                page_payload.get("ns"),
                title,
                page_payload.get("touched"),
                page_payload.get("length"),
                int("redirect" in page_payload),
                page_text,
                _json(dict(page_payload)),
                now,
                now,
            ),
        )
        self.conn.commit()
        if pageid is not None:
            row = self.conn.execute("SELECT id FROM pages WHERE wiki_id = ? AND pageid = ?", (wiki_id, pageid)).fetchone()
        else:
            row = self.conn.execute("SELECT id FROM pages WHERE wiki_id = ? AND title = ?", (wiki_id, title)).fetchone()
        return int(row["id"])

    def replace_page_relations(self, page_id: int, relation_type: str, values: list[Mapping[str, Any]]) -> None:
        table_map = {
            "categories": ("page_categories", "category_title", "title", None),
            "links": ("page_links", "target_title", "title", "target_ns"),
            "templates": ("page_templates", "template_title", "title", "template_ns"),
            "images": ("page_images", "image_title", "title", None),
        }
        if relation_type not in table_map:
            raise ValueError(f"Unsupported relation type: {relation_type}")

        table, title_column, source_key, ns_column = table_map[relation_type]
        self.conn.execute(f"DELETE FROM {table} WHERE page_id = ?", (page_id,))
        for value in values:
            title = value.get(source_key)
            if not title:
                continue
            if ns_column:
                self.conn.execute(
                    f"INSERT OR REPLACE INTO {table} (page_id, {title_column}, {ns_column}, raw_json) VALUES (?, ?, ?, ?)",
                    (page_id, str(title), value.get("ns"), _json(dict(value))),
                )
            else:
                self.conn.execute(
                    f"INSERT OR REPLACE INTO {table} (page_id, {title_column}, raw_json) VALUES (?, ?, ?)",
                    (page_id, str(title), _json(dict(value))),
                )
        self.conn.commit()

    def replace_infobox_fields(self, page_id: int, fields: list[Mapping[str, Any]]) -> None:
        self.conn.execute("DELETE FROM page_infobox_fields WHERE page_id = ?", (page_id,))
        for field in fields:
            name = field.get("field_name")
            value = field.get("field_value")
            if not name or value is None:
                continue
            self.conn.execute(
                """
                INSERT OR REPLACE INTO page_infobox_fields
                    (page_id, field_name, field_value, source, raw_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    page_id,
                    str(name),
                    str(value),
                    str(field.get("source") or "html_infobox"),
                    _json(dict(field)),
                ),
            )
        self.conn.commit()

    def upsert_revision(self, page_id: int, revision_payload: Mapping[str, Any]) -> None:
        revid = revision_payload.get("revid")
        if revid is None:
            return
        self.conn.execute(
            """
            INSERT INTO revisions (
                page_id, revid, parentid, timestamp, user, comment, size, sha1, raw_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(revid) DO UPDATE SET
                page_id=excluded.page_id,
                parentid=excluded.parentid,
                timestamp=excluded.timestamp,
                user=excluded.user,
                comment=excluded.comment,
                size=excluded.size,
                sha1=excluded.sha1,
                raw_json=excluded.raw_json,
                updated_at=excluded.updated_at
            """,
            (
                page_id,
                revid,
                revision_payload.get("parentid"),
                revision_payload.get("timestamp"),
                revision_payload.get("user"),
                revision_payload.get("comment"),
                revision_payload.get("size"),
                revision_payload.get("sha1"),
                _json(dict(revision_payload)),
                _utcnow(),
            ),
        )
        self.conn.commit()

    def get_checkpoint(self, wiki_id: int, key: str) -> Dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT value_json FROM checkpoints WHERE wiki_id = ? AND key = ?",
            (wiki_id, key),
        ).fetchone()
        if not row:
            return None
        return json.loads(row["value_json"])

    def set_checkpoint(self, wiki_id: int, key: str, value: Mapping[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO checkpoints (wiki_id, key, value_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(wiki_id, key) DO UPDATE SET
                value_json=excluded.value_json,
                updated_at=excluded.updated_at
            """,
            (wiki_id, key, _json(dict(value)), _utcnow()),
        )
        self.conn.commit()

    def clear_checkpoint(self, wiki_id: int, key: str) -> None:
        self.conn.execute("DELETE FROM checkpoints WHERE wiki_id = ? AND key = ?", (wiki_id, key))
        self.conn.commit()

    def get_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for table in (
            "wikis",
            "crawl_runs",
            "pages",
            "page_categories",
            "page_links",
            "page_templates",
            "page_images",
            "page_infobox_fields",
            "revisions",
            "crawl_errors",
            "checkpoints",
        ):
            row = self.conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
            counts[table] = int(row["count"])
        return counts
