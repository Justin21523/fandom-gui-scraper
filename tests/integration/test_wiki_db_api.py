from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.security.jwt import get_current_user
from scripts.create_demo_wiki_job import create_demo_job
from scraper.mediawiki import campaign
from scraper.mediawiki.campaign import CampaignConfig, run_campaign
from scraper.mediawiki.repository import WikiSQLiteRepository
from scraper.mediawiki.target import normalize_wiki_target


@pytest.fixture
def client():
    async def mock_get_current_user():
        return {"username": "test_user", "id": "123"}

    app.dependency_overrides[get_current_user] = mock_get_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def job_dir(tmp_path, monkeypatch):
    import api.endpoints.scraper as scraper_api

    root = tmp_path / "jobs" / "job-1"
    root.mkdir(parents=True)
    db_path = root / "wiki.db"
    repo = WikiSQLiteRepository(db_path)
    repo.initialize()
    wiki_id = repo.upsert_wiki(normalize_wiki_target("https://onepiece.fandom.com"))
    run_id = repo.start_run(wiki_id, job_id="job-1", config={})
    page_id = repo.upsert_page(
        wiki_id,
        {"pageid": 1, "ns": 0, "title": "Page A", "length": 100},
        page_text="Page A has useful wiki text.",
    )
    repo.replace_page_relations(page_id, "categories", [{"title": "Category:Characters"}])
    repo.finish_run(run_id, "finished")
    repo.close()
    (root / "manifest.json").write_text(json.dumps({"wiki_db": {"path": "wiki.db"}}), encoding="utf-8")

    monkeypatch.setattr(scraper_api, "JOBS_AVAILABLE", True)
    monkeypatch.setattr(scraper_api, "get_job_dir", lambda job_id: root, raising=False)
    return root


def test_wiki_db_summary_and_table_endpoints(client, job_dir):
    summary = client.get("/api/v1/scraper/jobs/job-1/wiki-db/summary")
    table = client.get("/api/v1/scraper/jobs/job-1/wiki-db/table/pages?q=Page")

    assert summary.status_code == 200
    assert summary.json()["summary"]["counts"]["pages"] == 1
    assert table.status_code == 200
    assert table.json()["items"][0]["title"] == "Page A"


def test_wiki_db_analysis_and_export_endpoints(client, job_dir):
    analysis = client.get("/api/v1/scraper/jobs/job-1/wiki-db/analysis")
    export = client.get("/api/v1/scraper/jobs/job-1/wiki-db/export?dataset=pages&format=json")

    assert analysis.status_code == 200
    assert analysis.json()["analysis"]["overview"]["pages"] == 1
    assert export.status_code == 200
    assert export.json()[0]["title"] == "Page A"


def test_wiki_db_parquet_export_returns_503_when_pyarrow_missing(client, job_dir, monkeypatch):
    import scraper.mediawiki.query as query

    def fail_parquet(*_args, **_kwargs):
        raise query.ParquetUnavailableError("Parquet export requires pyarrow")

    monkeypatch.setattr(query, "_write_parquet", fail_parquet)

    response = client.get("/api/v1/scraper/jobs/job-1/wiki-db/export?dataset=pages&format=parquet")

    assert response.status_code == 503
    assert "pyarrow" in response.json()["detail"]


def test_wiki_db_rejects_manifest_path_traversal(client, job_dir):
    (job_dir / "manifest.json").write_text(json.dumps({"wiki_db": {"path": "../wiki.db"}}), encoding="utf-8")

    response = client.get("/api/v1/scraper/jobs/job-1/wiki-db/summary")

    assert response.status_code == 400


def test_demo_mode_serves_offline_job_without_queue(client, tmp_path, monkeypatch):
    import api.endpoints.scraper as scraper_api

    demo_root = tmp_path / "sample_data"
    create_demo_job(demo_root)
    monkeypatch.setenv("FANDOM_DEMO_MODE", "true")
    monkeypatch.setenv("FANDOM_DEMO_ROOT", str(demo_root))
    monkeypatch.setattr(scraper_api, "JOBS_AVAILABLE", False)

    jobs = client.get("/api/v1/scraper/jobs")
    summary = client.get("/api/v1/scraper/jobs/demo-onepiece-action-api-001/wiki-db/summary")

    assert jobs.status_code == 200
    assert jobs.json()[0]["job_id"] == "demo-onepiece-action-api-001"
    assert summary.status_code == 200
    assert summary.json()["summary"]["counts"]["pages"] == 3


def test_campaign_endpoints_serve_local_campaign(client, tmp_path, monkeypatch):
    import api.endpoints.scraper as scraper_api

    def fake_harvest(config):
        root = Path(config.db_path).parent
        root.mkdir(parents=True, exist_ok=True)
        repo = WikiSQLiteRepository(config.db_path)
        repo.initialize()
        wiki_id = repo.upsert_wiki(normalize_wiki_target(config.target))
        run_id = repo.start_run(wiki_id, job_id=config.job_id, config={"fake": True})
        page_id = repo.upsert_page(wiki_id, {"pageid": 1, "title": "Page A", "ns": 0}, page_text="Page text")
        repo.replace_page_relations(page_id, "categories", [{"title": "Category:Test"}])
        repo.finish_run(run_id, "finished")
        repo.close()
        return {"status": "finished", "db_path": str(config.db_path), "counts": {"pages": 1, "page_categories": 1}}

    monkeypatch.setenv("FANDOM_DEMO_ROOT", str(tmp_path))
    monkeypatch.setattr(campaign, "harvest_to_sqlite", fake_harvest)
    monkeypatch.setattr(scraper_api, "JOBS_AVAILABLE", False)
    run_campaign(CampaignConfig(campaign_id="api-campaign", targets=["https://onepiece.fandom.com"], output_root=tmp_path, page_limit=1, rate_delay=0))

    headers = {"X-Forwarded-For": "campaign-test"}
    campaigns = client.get("/api/v1/scraper/campaigns", headers=headers)
    detail = client.get("/api/v1/scraper/campaigns/api-campaign", headers=headers)
    events = client.get("/api/v1/scraper/campaigns/api-campaign/events", headers=headers)
    analysis = client.get("/api/v1/scraper/campaigns/api-campaign/analysis", headers=headers)

    assert campaigns.status_code == 200
    assert campaigns.json()["items"][0]["campaign_id"] == "api-campaign"
    assert detail.status_code == 200
    assert events.status_code == 200
    assert analysis.status_code == 200
    assert analysis.json()["analysis"]["overview"]["pages"] == 1


def test_campaign_run_endpoint_queues_background_task(client, tmp_path, monkeypatch):
    import api.endpoints.scraper as scraper_api

    calls = []

    def fake_run(config):
        calls.append(config)
        return {"campaign_id": config.campaign_id}

    monkeypatch.setenv("FANDOM_DEMO_ROOT", str(tmp_path))
    monkeypatch.setattr(scraper_api, "run_campaign", fake_run)

    response = client.post(
        "/api/v1/scraper/campaigns/run",
        json={"campaign_id": "queued-campaign", "targets": ["https://onepiece.fandom.com"], "page_limit": 1, "rate_delay": 0},
        headers={"X-Forwarded-For": "campaign-run-test"},
    )

    assert response.status_code == 200
    assert response.json()["campaign_id"] == "queued-campaign"
    assert calls[0].campaign_id == "queued-campaign"


def test_campaign_presets_endpoint_serves_demo_and_live_options(client):
    response = client.get("/api/v1/scraper/campaigns/presets", headers={"X-Forwarded-For": "campaign-presets-test"})

    assert response.status_code == 200
    items = response.json()["items"]
    ids = {item["id"] for item in items}
    assert "offline-portfolio-smoke" in ids
    assert "live-quick-two-wikis" in ids
    live = next(item for item in items if item["id"] == "live-quick-two-wikis")
    assert live["mode"] == "live"
    assert live["targets"]
    assert live["defaults"]["page_limit"] >= 1
