from __future__ import annotations

import json

from scraper.mediawiki import campaign
from scraper.mediawiki.campaign import CampaignConfig, load_campaign_events, run_campaign
from scraper.mediawiki.repository import WikiSQLiteRepository
from scraper.mediawiki.target import normalize_wiki_target


def _write_fake_db(db_path, target, job_id):
    repo = WikiSQLiteRepository(db_path)
    repo.initialize()
    wiki_id = repo.upsert_wiki(normalize_wiki_target(target))
    run_id = repo.start_run(wiki_id, job_id=job_id, config={"fake": True})
    page_id = repo.upsert_page(
        wiki_id,
        {"pageid": 1, "ns": 0, "title": "Page A", "length": 100},
        page_text="Page A text",
    )
    repo.replace_page_relations(page_id, "categories", [{"title": "Category:Test"}])
    repo.replace_page_relations(page_id, "links", [{"title": "Page B", "ns": 0}])
    repo.replace_infobox_fields(page_id, [{"field_name": "Kind", "field_value": "Demo", "source": "test"}])
    repo.upsert_revision(page_id, {"revid": 1, "timestamp": "2026-01-01T00:00:00Z", "user": "Tester"})
    repo.finish_run(run_id, "finished")
    repo.close()


def test_campaign_runner_writes_manifest_events_and_job_outputs(tmp_path, monkeypatch):
    def fake_harvest(config):
        _write_fake_db(config.db_path, config.target, config.job_id)
        return {
            "status": "finished",
            "db_path": str(config.db_path),
            "counts": {
                "pages": 1,
                "page_categories": 1,
                "page_links": 1,
                "page_templates": 0,
                "page_images": 0,
                "revisions": 1,
                "page_infobox_fields": 1,
                "crawl_errors": 0,
            },
        }

    monkeypatch.setattr(campaign, "harvest_to_sqlite", fake_harvest)

    manifest = run_campaign(
        CampaignConfig(
            campaign_id="test-campaign",
            targets=["https://onepiece.fandom.com", "https://stardewvalley.fandom.com"],
            output_root=tmp_path,
            page_limit=1,
            rate_delay=0,
        )
    )

    assert manifest["campaign_id"] == "test-campaign"
    assert manifest["summary"]["pages"] == 2
    assert len(manifest["jobs"]) == 2
    assert (tmp_path / "campaigns" / "test-campaign" / "campaign.json").exists()
    assert (tmp_path / "jobs" / "test-campaign-onepiece" / "wiki.db").exists()
    assert load_campaign_events("test-campaign", output_root=tmp_path)


def test_campaign_runner_skips_existing_finished_job(tmp_path, monkeypatch):
    calls = {"count": 0}

    def fake_harvest(config):
        calls["count"] += 1
        _write_fake_db(config.db_path, config.target, config.job_id)
        return {"status": "finished", "db_path": str(config.db_path), "counts": {"pages": 1}}

    monkeypatch.setattr(campaign, "harvest_to_sqlite", fake_harvest)
    config = CampaignConfig(campaign_id="skip-campaign", targets=["https://onepiece.fandom.com"], output_root=tmp_path, page_limit=1, rate_delay=0)

    first = run_campaign(config)
    second = run_campaign(config)

    assert first["summary"]["pages"] == 1
    assert second["summary"]["pages"] == 1
    assert calls["count"] == 1
    events = load_campaign_events("skip-campaign", output_root=tmp_path)
    assert any(event["stage"] == "skip" for event in events)


def test_campaign_manifest_is_json_serializable(tmp_path, monkeypatch):
    def fake_harvest(config):
        _write_fake_db(config.db_path, config.target, config.job_id)
        return {"status": "finished", "db_path": str(config.db_path), "counts": {"pages": 1}}

    monkeypatch.setattr(campaign, "harvest_to_sqlite", fake_harvest)
    run_campaign(CampaignConfig(campaign_id="json-campaign", targets=["https://fallout.fandom.com"], output_root=tmp_path, page_limit=1, rate_delay=0))

    path = tmp_path / "campaigns" / "json-campaign" / "campaign.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded["jobs"][0]["job_id"] == "json-campaign-fallout"
