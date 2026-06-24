from __future__ import annotations

import json

from scraper.mediawiki.infobox import parse_infobox_fields
from scraper.mediawiki.query import ParquetUnavailableError, WikiDBQueryService
from scraper.mediawiki.repository import WikiSQLiteRepository
from scraper.mediawiki.target import normalize_wiki_target


def build_wiki_db(path):
    repo = WikiSQLiteRepository(path)
    repo.initialize()
    wiki_id = repo.upsert_wiki(normalize_wiki_target("https://onepiece.fandom.com"))
    run_id = repo.start_run(wiki_id, job_id="job-1", config={"limit": 1})
    page_id = repo.upsert_page(
        wiki_id,
        {
            "pageid": 1,
            "ns": 0,
            "title": "Monkey D. Luffy",
            "length": 500,
            "revisions": [],
        },
        page_text="Luffy is a pirate captain with rubber powers.",
    )
    repo.replace_page_relations(page_id, "categories", [{"title": "Category:Characters"}])
    repo.replace_page_relations(page_id, "links", [{"title": "Roronoa Zoro", "ns": 0}])
    repo.replace_page_relations(page_id, "templates", [{"title": "Template:Character", "ns": 10}])
    repo.replace_page_relations(page_id, "images", [{"title": "File:Luffy.png"}])
    repo.replace_infobox_fields(page_id, [{"field_name": "Affiliation", "field_value": "Straw Hat Pirates", "source": "html_infobox"}])
    repo.upsert_revision(page_id, {"revid": 100, "timestamp": "2026-01-01T00:00:00Z", "user": "Editor"})
    repo.finish_run(run_id, "finished")
    repo.close()


def test_parse_infobox_fields_supports_portable_infobox():
    html = """
    <aside class="portable-infobox">
      <div class="pi-item">
        <h3 class="pi-data-label">Affiliation</h3>
        <div class="pi-data-value">Straw Hat Pirates</div>
      </div>
    </aside>
    """

    fields = parse_infobox_fields(html)

    assert fields == [
        {"field_name": "Affiliation", "field_value": "Straw Hat Pirates", "source": "html_infobox"}
    ]


def test_wiki_db_query_summary_table_analysis_and_export(tmp_path):
    db_path = tmp_path / "wiki.db"
    build_wiki_db(db_path)
    service = WikiDBQueryService(db_path)

    summary = service.summary()
    table = service.table("pages", q="Luffy")
    analysis = service.analysis()
    csv_path = service.export_dataset("pages", "csv")
    json_path = service.export_dataset("infoboxes", "json")

    assert summary["counts"]["pages"] == 1
    assert "csv" in summary["capabilities"]["export_formats"]
    assert table["total"] == 1
    assert table["items"][0]["title"] == "Monkey D. Luffy"
    assert analysis["category_counts"][0]["label"] == "Category:Characters"
    assert analysis["top_terms"][0]["term"] == "luffy"
    assert "Monkey D. Luffy" in csv_path.read_text(encoding="utf-8")
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["field_name"] == "Affiliation"

    try:
        parquet_path = service.export_dataset("pages", "parquet")
    except ParquetUnavailableError as exc:
        assert "pyarrow" in str(exc)
    else:
        assert parquet_path.suffix == ".parquet"


def test_wiki_db_query_rejects_unknown_dataset(tmp_path):
    db_path = tmp_path / "wiki.db"
    build_wiki_db(db_path)
    service = WikiDBQueryService(db_path)

    try:
        service.table("sqlite_master")
    except ValueError as exc:
        assert "Unsupported dataset" in str(exc)
    else:
        raise AssertionError("Expected unsupported dataset error")
