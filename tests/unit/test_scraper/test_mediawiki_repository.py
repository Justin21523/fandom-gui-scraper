from __future__ import annotations

import sqlite3

import pytest

from scraper.mediawiki import AccessRestrictedError, HarvestConfig, MediaWikiHarvester, WikiSQLiteRepository
from scraper.mediawiki.target import normalize_wiki_target


class FakeClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []

    def get(self, params):
        self.calls.append(dict(params))
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return payload


def sample_page(pageid=1, title="Page A"):
    return {
        "pageid": pageid,
        "ns": 0,
        "title": title,
        "touched": "2026-01-01T00:00:00Z",
        "length": 128,
        "categories": [{"title": "Category:Characters"}],
        "links": [{"ns": 0, "title": "Linked Page"}],
        "templates": [{"ns": 10, "title": "Template:Infobox"}],
        "images": [{"title": "File:Image.png"}],
        "revisions": [
            {
                "revid": 100,
                "parentid": 99,
                "timestamp": "2026-01-01T00:00:00Z",
                "user": "Editor",
                "comment": "Latest",
                "size": 128,
                "sha1": "abc",
                "content": "Page text",
            }
        ],
    }


def test_repository_initializes_schema_and_upserts_idempotently(tmp_path):
    repo = WikiSQLiteRepository(tmp_path / "wiki.db")
    repo.initialize()
    wiki_id = repo.upsert_wiki(normalize_wiki_target("https://onepiece.fandom.com"))
    run_id = repo.start_run(wiki_id, job_id="job-1", config={"limit": 1})

    page_id = repo.upsert_page(wiki_id, sample_page(), page_text="Page text")
    repo.replace_page_relations(page_id, "categories", [{"title": "Category:Characters"}])
    repo.replace_page_relations(page_id, "links", [{"ns": 0, "title": "Linked Page"}])
    repo.replace_page_relations(page_id, "templates", [{"ns": 10, "title": "Template:Infobox"}])
    repo.replace_page_relations(page_id, "images", [{"title": "File:Image.png"}])
    repo.upsert_revision(page_id, sample_page()["revisions"][0])

    page_id_again = repo.upsert_page(wiki_id, sample_page(), page_text="Page text")
    repo.upsert_revision(page_id_again, sample_page()["revisions"][0])
    repo.finish_run(run_id, "finished")

    counts = repo.get_counts()
    assert counts["wikis"] == 1
    assert counts["crawl_runs"] == 1
    assert counts["pages"] == 1
    assert counts["page_categories"] == 1
    assert counts["page_links"] == 1
    assert counts["page_templates"] == 1
    assert counts["page_images"] == 1
    assert counts["revisions"] == 1
    repo.close()


def test_repository_checkpoint_roundtrip(tmp_path):
    repo = WikiSQLiteRepository(tmp_path / "wiki.db")
    repo.initialize()
    wiki_id = repo.upsert_wiki(normalize_wiki_target("https://onepiece.fandom.com"))

    repo.set_checkpoint(wiki_id, "allpages_continue", {"continue": "||", "gapcontinue": "Page B"})

    assert repo.get_checkpoint(wiki_id, "allpages_continue") == {"continue": "||", "gapcontinue": "Page B"}
    repo.close()


def test_harvester_follows_continuation_and_stores_pages(tmp_path):
    client = FakeClient(
        [
            {
                "query": {"pages": [sample_page(1, "Page A")]},
                "continue": {"continue": "||", "gapcontinue": "Page B"},
            },
            {"query": {"pages": [sample_page(2, "Page B")]}},
        ]
    )
    config = HarvestConfig(
        target="https://onepiece.fandom.com",
        db_path=tmp_path / "wiki.db",
        page_limit=2,
        batch_size=1,
        rate_delay=0,
        respect_robots=False,
        include_infobox_html=False,
    )

    result = MediaWikiHarvester(config, client=client).run()

    assert result["status"] == "finished"
    assert result["counts"]["pages"] == 2
    assert client.calls[1]["gapcontinue"] == "Page B"

    con = sqlite3.connect(tmp_path / "wiki.db")
    row = con.execute("SELECT page_text FROM pages WHERE title = 'Page A'").fetchone()
    assert row[0] == "Page text"
    con.close()


def test_harvester_resumes_from_checkpoint(tmp_path):
    repo = WikiSQLiteRepository(tmp_path / "wiki.db")
    repo.initialize()
    wiki_id = repo.upsert_wiki(normalize_wiki_target("https://onepiece.fandom.com"))
    repo.set_checkpoint(wiki_id, "allpages_continue", {"continue": "||", "gapcontinue": "Resume Page"})

    client = FakeClient([{"query": {"pages": [sample_page(3, "Resume Page")]}}])
    config = HarvestConfig(
        target="https://onepiece.fandom.com",
        db_path=tmp_path / "wiki.db",
        page_limit=1,
        batch_size=1,
        rate_delay=0,
        respect_robots=False,
        include_infobox_html=False,
    )

    result = MediaWikiHarvester(config, client=client, repository=repo).run()

    assert result["status"] == "finished"
    assert client.calls[0]["gapcontinue"] == "Resume Page"
    repo.close()


def test_harvester_records_access_restriction_and_stops(tmp_path):
    client = FakeClient([AccessRestrictedError("HTTP 429")])
    config = HarvestConfig(
        target="https://onepiece.fandom.com",
        db_path=tmp_path / "wiki.db",
        page_limit=1,
        rate_delay=0,
        respect_robots=False,
        include_infobox_html=False,
    )

    result = MediaWikiHarvester(config, client=client).run()

    assert result["status"] == "stopped"
    assert result["counts"]["crawl_errors"] == 1


def test_harvester_fetches_parse_html_for_infobox_fallback(tmp_path):
    client = FakeClient(
        [
            {"query": {"pages": [sample_page(4, "Infobox Page")]}},
            {
                "parse": {
                    "text": {
                        "*": """
                        <aside class="portable-infobox">
                          <div class="pi-item">
                            <h3 class="pi-data-label">Affiliation</h3>
                            <div class="pi-data-value">Demo Crew</div>
                          </div>
                        </aside>
                        """
                    }
                }
            },
        ]
    )
    config = HarvestConfig(
        target="https://onepiece.fandom.com",
        db_path=tmp_path / "wiki.db",
        page_limit=1,
        batch_size=1,
        rate_delay=0,
        respect_robots=False,
        include_infobox_html=True,
        parse_html_limit=1,
    )

    result = MediaWikiHarvester(config, client=client).run()

    assert result["status"] == "finished"
    assert client.calls[1]["action"] == "parse"

    con = sqlite3.connect(tmp_path / "wiki.db")
    row = con.execute("SELECT field_name, field_value FROM page_infobox_fields").fetchone()
    assert row == ("Affiliation", "Demo Crew")
    con.close()
