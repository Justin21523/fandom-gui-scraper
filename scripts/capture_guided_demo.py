from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("GUIDED_DEMO_BASE_URL", "http://127.0.0.1:18000").rstrip("/")
APP_PATH = os.getenv("GUIDED_DEMO_APP_PATH", "/app").rstrip("/")
REQUESTED_OUT_DIR = Path(os.getenv("GUIDED_DEMO_OUT_DIR", "docs/images/guided-demo"))

VIEWPORT = {"width": 1440, "height": 940}
MOBILE_VIEWPORT = {"width": 390, "height": 844}


def writable_output_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return path
    except OSError:
        fallback = Path("/tmp/fandom-gui-scraper-guided-demo")
        fallback.mkdir(parents=True, exist_ok=True)
        print(f"Output directory is not writable, using {fallback}")
        return fallback


def inspect_page(page) -> dict:
    return page.evaluate(
        """() => {
            const doc = document.documentElement;
            const panel = document.querySelector('.demo-guide__panel--open');
            const spotlight = document.querySelector('.demo-guide__spotlight');
            const activeTarget = document.querySelector('.tour-target--active');
            const graph = document.querySelector('.network-graph svg, canvas, svg[role="img"]');
            return {
                title: document.title,
                hash: window.location.hash,
                lang: doc.lang,
                theme: doc.getAttribute('data-theme'),
                panelVisible: Boolean(panel),
                spotlightVisible: Boolean(spotlight),
                activeTarget: activeTarget?.getAttribute('data-tour') || '',
                horizontalOverflow: doc.scrollWidth > doc.clientWidth + 2,
                graphVisible: Boolean(graph),
                bodyTextLength: (document.body.textContent || '').trim().length,
            };
        }"""
    )


def prepare_page(page) -> None:
    page.add_init_script(
        """() => {
            localStorage.setItem('locale', 'zh');
            localStorage.setItem('theme', 'indigo');
            localStorage.removeItem('demoGuide.state');
        }"""
    )


def capture_flow(page, out_dir: Path, label: str, viewport: dict) -> list[dict]:
    page.set_viewport_size(viewport)
    page.goto(f"{BASE_URL}{APP_PATH}#/campaigns", wait_until="networkidle", timeout=120_000)
    page.wait_for_selector('[data-tour="campaigns-overview"]', timeout=30_000)
    page.locator('[data-tour="guide-open"]').click()
    page.wait_for_selector(".demo-guide__panel--open", timeout=10_000)

    results: list[dict] = []
    for index in range(13):
        page.wait_for_timeout(900)
        try:
            page.wait_for_selector(".tour-target--active", timeout=8_000)
        except PlaywrightTimeoutError:
            page.wait_for_selector(".demo-guide__warning", timeout=2_000)
        details = inspect_page(page)
        screenshot = f"guided_{label}_step_{index + 1:02d}.png"
        page.screenshot(path=str(out_dir / screenshot), full_page=True)
        details.update({"step": index + 1, "viewport": label, "screenshot": screenshot})
        results.append(details)
        if details["hash"].startswith("#/login"):
            raise RuntimeError("Unexpected login redirect during guided demo capture.")
        if details["horizontalOverflow"]:
            raise RuntimeError(f"Horizontal overflow detected at guided step {index + 1}.")
        if index < 12:
            page.locator("[data-guide-next]").click()
            page.wait_for_timeout(350)
    return results


def main() -> int:
    out_dir = writable_output_dir(REQUESTED_OUT_DIR)
    video_dir = out_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "base_url": BASE_URL,
        "app_path": APP_PATH,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "locale": "zh",
        "theme": "indigo",
        "screenshots": [],
        "videos": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=VIEWPORT, record_video_dir=str(video_dir))
        page = context.new_page()
        prepare_page(page)
        report["screenshots"].extend(capture_flow(page, out_dir, "desktop", VIEWPORT))
        video = page.video
        page.close()
        if video:
            report["videos"].append(str(video.path()))
        context.close()

        mobile_context = browser.new_context(viewport=MOBILE_VIEWPORT, record_video_dir=str(video_dir))
        mobile_page = mobile_context.new_page()
        prepare_page(mobile_page)
        report["screenshots"].extend(capture_flow(mobile_page, out_dir, "mobile", MOBILE_VIEWPORT))
        mobile_video = mobile_page.video
        mobile_page.close()
        if mobile_video:
            report["videos"].append(str(mobile_video.path()))
        mobile_context.close()
        browser.close()

    report_path = out_dir / "guided_demo_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
