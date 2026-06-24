from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List


DATASETS: Dict[str, Dict[str, Any]] = {
    "pages": {
        "table": "pages",
        "columns": ["id", "pageid", "ns", "title", "length", "is_redirect", "touched", "updated_at"],
        "search": ["title", "page_text"],
    },
    "categories": {
        "table": "page_categories",
        "columns": ["page_id", "category_title"],
        "search": ["category_title"],
    },
    "links": {
        "table": "page_links",
        "columns": ["page_id", "target_title", "target_ns"],
        "search": ["target_title"],
    },
    "templates": {
        "table": "page_templates",
        "columns": ["page_id", "template_title", "template_ns"],
        "search": ["template_title"],
    },
    "images": {
        "table": "page_images",
        "columns": ["page_id", "image_title"],
        "search": ["image_title"],
    },
    "revisions": {
        "table": "revisions",
        "columns": ["id", "page_id", "revid", "parentid", "timestamp", "user", "comment", "size", "sha1"],
        "search": ["user", "comment", "sha1"],
    },
    "errors": {
        "table": "crawl_errors",
        "columns": ["id", "run_id", "error_type", "message", "created_at"],
        "search": ["error_type", "message"],
    },
    "checkpoints": {
        "table": "checkpoints",
        "columns": ["wiki_id", "key", "value_json", "updated_at"],
        "search": ["key", "value_json"],
    },
    "infoboxes": {
        "table": "page_infobox_fields",
        "columns": ["page_id", "field_name", "field_value", "source"],
        "search": ["field_name", "field_value"],
    },
}

STOP_WORDS = {
    "the", "and", "for", "that", "with", "this", "from", "are", "was", "were",
    "has", "have", "his", "her", "its", "wiki", "page", "they", "their", "not",
}


class ParquetUnavailableError(RuntimeError):
    pass


class WikiDBQueryService:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        uri = f"file:{self.db_path.resolve()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def summary(self) -> Dict[str, Any]:
        with self._connect() as conn:
            counts = {}
            for name, spec in DATASETS.items():
                counts[name] = self._count_table(conn, spec["table"])
            wiki = _row_to_dict(conn.execute("SELECT * FROM wikis ORDER BY id DESC LIMIT 1").fetchone())
            run = _row_to_dict(conn.execute("SELECT * FROM crawl_runs ORDER BY id DESC LIMIT 1").fetchone())
            return {
                "db_path": str(self.db_path),
                "wiki": wiki,
                "latest_run": run,
                "counts": counts,
                "capabilities": self.capabilities(),
            }

    def tables(self) -> Dict[str, Any]:
        return {"datasets": [{"name": name, "columns": spec["columns"]} for name, spec in DATASETS.items()]}

    def capabilities(self) -> Dict[str, Any]:
        parquet_available = _parquet_available()
        return {
            "export_formats": ["csv", "json", *(['parquet'] if parquet_available else [])],
            "parquet_available": parquet_available,
            "parquet_error": None if parquet_available else "Install pyarrow to enable Parquet export.",
        }

    def table(self, dataset: str, *, limit: int = 100, offset: int = 0, q: str | None = None) -> Dict[str, Any]:
        spec = self._spec(dataset)
        limit = max(1, min(limit, 1000))
        offset = max(0, offset)
        where, params = self._where(spec, q)
        columns = ", ".join(spec["columns"])
        with self._connect() as conn:
            total = conn.execute(f"SELECT COUNT(*) AS count FROM {spec['table']} {where}", params).fetchone()["count"]
            rows = conn.execute(
                f"SELECT {columns} FROM {spec['table']} {where} ORDER BY 1 LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
        return {
            "dataset": dataset,
            "columns": spec["columns"],
            "limit": limit,
            "offset": offset,
            "total": int(total),
            "items": [_row_to_dict(row) for row in rows],
        }

    def page_detail(self, page_id: int) -> Dict[str, Any]:
        with self._connect() as conn:
            page = _row_to_dict(conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone())
            if not page:
                raise KeyError(f"Page not found: {page_id}")
            relations = {
                "categories": self._relation_rows(conn, "page_categories", page_id),
                "links": self._relation_rows(conn, "page_links", page_id),
                "templates": self._relation_rows(conn, "page_templates", page_id),
                "images": self._relation_rows(conn, "page_images", page_id),
                "infoboxes": self._relation_rows(conn, "page_infobox_fields", page_id),
                "revisions": self._relation_rows(conn, "revisions", page_id),
            }
        return {"page": page, **relations}

    def analysis(self) -> Dict[str, Any]:
        with self._connect() as conn:
            counts = {name: self._count_table(conn, spec["table"]) for name, spec in DATASETS.items()}
            category_counts = self._top_counts(conn, "page_categories", "category_title")
            link_counts = self._top_counts(conn, "page_links", "target_title")
            template_counts = self._top_counts(conn, "page_templates", "template_title")
            terms = self._top_terms(conn)
            quality = self._quality(conn, counts)
            network = self._network(conn)
        return {
            "overview": counts,
            "category_counts": category_counts,
            "top_links": link_counts,
            "top_templates": template_counts,
            "top_terms": terms,
            "network": network,
            "quality": quality,
        }

    def export_dataset(self, dataset: str, fmt: str) -> Path:
        if fmt not in {"csv", "json", "parquet"}:
            raise ValueError("format must be csv, json, or parquet")
        data = self.table(dataset, limit=1000, offset=0)
        tmp = NamedTemporaryFile(delete=False, suffix=f".{fmt}")
        path = Path(tmp.name)
        tmp.close()
        if fmt == "json":
            path.write_text(json.dumps(data["items"], ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            return path
        if fmt == "parquet":
            return _write_parquet(data["items"], path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data["columns"])
            writer.writeheader()
            writer.writerows(data["items"])
        return path

    def _spec(self, dataset: str) -> Dict[str, Any]:
        if dataset not in DATASETS:
            raise ValueError(f"Unsupported dataset: {dataset}")
        return DATASETS[dataset]

    def _where(self, spec: Dict[str, Any], q: str | None) -> tuple[str, List[str]]:
        if not q:
            return "", []
        clauses = [f"{col} LIKE ?" for col in spec["search"]]
        return "WHERE " + " OR ".join(clauses), [f"%{q}%" for _ in clauses]

    def _count_table(self, conn: sqlite3.Connection, table: str) -> int:
        try:
            return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
        except sqlite3.OperationalError:
            return 0

    def _relation_rows(self, conn: sqlite3.Connection, table: str, page_id: int) -> List[Dict[str, Any]]:
        return [_row_to_dict(row) for row in conn.execute(f"SELECT * FROM {table} WHERE page_id = ?", (page_id,)).fetchall()]

    def _top_counts(self, conn: sqlite3.Connection, table: str, column: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            rows = conn.execute(
                f"SELECT {column} AS label, COUNT(*) AS value FROM {table} GROUP BY {column} ORDER BY value DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [_row_to_dict(row) for row in rows]
        except sqlite3.OperationalError:
            return []

    def _top_terms(self, conn: sqlite3.Connection, limit: int = 20) -> List[Dict[str, Any]]:
        rows = conn.execute("SELECT page_text FROM pages WHERE page_text IS NOT NULL LIMIT 500").fetchall()
        counter: Counter[str] = Counter()
        for row in rows:
            words = re.findall(r"[A-Za-z][A-Za-z0-9_'-]{2,}", row["page_text"] or "")
            counter.update(word.lower() for word in words if word.lower() not in STOP_WORDS)
        return [{"term": term, "count": count} for term, count in counter.most_common(limit)]

    def _quality(self, conn: sqlite3.Connection, counts: Dict[str, int]) -> List[Dict[str, Any]]:
        missing_text = conn.execute("SELECT COUNT(*) AS count FROM pages WHERE page_text IS NULL OR page_text = ''").fetchone()["count"]
        no_categories = conn.execute(
            "SELECT COUNT(*) AS count FROM pages p LEFT JOIN page_categories c ON c.page_id = p.id WHERE c.page_id IS NULL"
        ).fetchone()["count"]
        no_revisions = conn.execute(
            "SELECT COUNT(*) AS count FROM pages p LEFT JOIN revisions r ON r.page_id = p.id WHERE r.page_id IS NULL"
        ).fetchone()["count"]
        return [
            {"check": "Missing page text", "affected": int(missing_text), "status": "warning" if missing_text else "passed"},
            {"check": "Pages without categories", "affected": int(no_categories), "status": "warning" if no_categories else "passed"},
            {"check": "Pages without revisions", "affected": int(no_revisions), "status": "warning" if no_revisions else "passed"},
            {"check": "Crawl errors", "affected": counts.get("errors", 0), "status": "failed" if counts.get("errors", 0) else "passed"},
        ]

    def _network(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        rows = conn.execute(
            """
            SELECT p.title AS source, l.target_title AS target
            FROM page_links l
            JOIN pages p ON p.id = l.page_id
            LIMIT 100
            """
        ).fetchall()
        nodes = {}
        edges = []
        for row in rows:
            source = row["source"]
            target = row["target"]
            edges.append({"source": source, "target": target})
            nodes[source] = nodes.get(source, 0) + 1
            nodes[target] = nodes.get(target, 0) + 1
        return {"nodes": [{"id": key, "degree": value} for key, value in nodes.items()], "edges": edges}


def _row_to_dict(row: sqlite3.Row | None) -> Dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _parquet_available() -> bool:
    try:
        import pyarrow  # noqa: F401
        import pandas  # noqa: F401
        return True
    except ImportError:
        return False


def _write_parquet(rows: List[Dict[str, Any]], path: Path) -> Path:
    try:
        import pyarrow  # noqa: F401
        import pandas as pd
    except ImportError as exc:
        raise ParquetUnavailableError("Parquet export requires pyarrow. Install pyarrow or use CSV/JSON.") from exc
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path
