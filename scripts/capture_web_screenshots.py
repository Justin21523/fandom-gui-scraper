from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("SCREENSHOT_BASE_URL", "http://127.0.0.1:18000").rstrip("/")
OUT_DIR = Path(os.getenv("SCREENSHOT_OUT_DIR", "docs/images/screenshots"))
APP_PATH = os.getenv("SCREENSHOT_APP_PATH", "/app").rstrip("/")

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}

MAX_SECTION_HEIGHT = {
    "desktop": 900,
    "mobile": 780,
}

TARGETS = [
    ("campaigns", f"{BASE_URL}{APP_PATH}#/campaigns", '[data-tour="campaigns-overview"]'),
    ("browse", f"{BASE_URL}{APP_PATH}#/browse", '[data-tour="browse-datasets"]'),
    ("analysis", f"{BASE_URL}{APP_PATH}#/analysis", '[data-tour="analysis-network"]'),
    ("process", f"{BASE_URL}{APP_PATH}#/process", '[data-tour="process-timeline"]'),
    ("export", f"{BASE_URL}{APP_PATH}#/export", '[data-tour="export-center"]'),
    ("compliance", f"{BASE_URL}{APP_PATH}#/compliance", '[data-tour="compliance-log"]'),
    ("scraper", f"{BASE_URL}{APP_PATH}#/scraper", '[data-tour="scraper-source"]'),
]


def inspect_page(page) -> dict:
    return page.evaluate(
        """() => {
            const doc = document.documentElement;
            const overflowSamples = Array.from(
                document.querySelectorAll('button, .btn, .card, .dataset-chip, .target-chip, .badge, th, td')
            )
                .filter((el) => el.scrollWidth > el.clientWidth + 2)
                .slice(0, 12)
                .map((el) => ({
                    tag: el.tagName.toLowerCase(),
                    className: el.className || '',
                    text: (el.textContent || '').trim().slice(0, 80),
                    scrollWidth: el.scrollWidth,
                    clientWidth: el.clientWidth,
                }));
            const graphs = Array.from(document.querySelectorAll('.network-graph, svg, canvas'));
            return {
                title: document.title,
                lang: doc.lang,
                theme: doc.getAttribute('data-theme'),
                horizontalOverflow: doc.scrollWidth > doc.clientWidth + 2,
                scrollWidth: doc.scrollWidth,
                clientWidth: doc.clientWidth,
                overflowSamples,
                graphLikeElements: graphs.length,
                bodyTextLength: (document.body.textContent || '').trim().length,
            };
        }"""
    )


def capture_target(page, target, screenshot_path: Path, viewport_name: str) -> None:
    target.scroll_into_view_if_needed(timeout=10_000)
    page.wait_for_timeout(350)
    box = target.bounding_box()
    if not box:
        target.screenshot(path=str(screenshot_path))
        return
    clip = {
        "x": max(0, box["x"]),
        "y": max(0, box["y"]),
        "width": min(box["width"], page.viewport_size["width"] - max(0, box["x"])),
        "height": min(box["height"], MAX_SECTION_HEIGHT[viewport_name]),
    }
    page.screenshot(path=str(screenshot_path), clip=clip)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "base_url": BASE_URL,
        "app_path": APP_PATH,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "locale": "zh",
        "theme": "indigo",
        "pages": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for viewport_name, viewport in VIEWPORTS.items():
            page = browser.new_page(viewport=viewport)
            page.add_init_script(
                """() => {
                    localStorage.setItem('locale', 'zh');
                    localStorage.setItem('theme', 'indigo');
                    const originalFetch = window.fetch.bind(window);
                    window.fetch = async (...args) => {
                        const response = await originalFetch(...args);
                        try {
                            const url = new URL(response.url);
                            if (response.status === 401 && url.pathname.startsWith('/api/v1/')) {
                                return new Response(
                                    JSON.stringify({ detail: 'Screenshot smoke converted 401 to demo fallback.' }),
                                    { status: 503, headers: { 'content-type': 'application/json' } }
                                );
                            }
                        } catch (_) {
                            return response;
                        }
                        return response;
                    };
                }"""
            )
            for page_name, url, selector in TARGETS:
                filename = f"web_{page_name}_{viewport_name}.png"
                page.goto(url, wait_until="networkidle", timeout=120_000)
                page.wait_for_function("() => document.documentElement.lang && document.querySelector('#main-content h1')")
                page.evaluate(
                    """() => {
                        localStorage.setItem('locale', 'zh');
                        localStorage.setItem('theme', 'indigo');
                        document.documentElement.lang = 'zh-Hant';
                        document.documentElement.setAttribute('data-theme', 'indigo');
                    }"""
                )
                page.wait_for_timeout(1000)
                target = page.locator(selector).first
                if target.count() > 0:
                    capture_target(page, target, OUT_DIR / filename, viewport_name)
                else:
                    # 目標缺失時保留 viewport 截圖，報告會暴露 body/overflow 狀態。
                    page.screenshot(path=str(OUT_DIR / filename), full_page=False)
                details = inspect_page(page)
                details.update({"page": page_name, "viewport": viewport_name, "url": url, "selector": selector, "screenshot": filename})
                report["pages"].append(details)
                print(f"{viewport_name:7s} {page_name:10s} {OUT_DIR / filename}")
            page.close()
        browser.close()

    report_path = OUT_DIR / "visual_smoke_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
