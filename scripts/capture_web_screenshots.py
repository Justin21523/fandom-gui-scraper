from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("SCREENSHOT_BASE_URL", "http://127.0.0.1:18000")
OUT_DIR = Path(os.getenv("SCREENSHOT_OUT_DIR", "docs/images/screenshots"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = [
        ("web_scraper.png", f"{BASE_URL}/frontend/#/scraper"),
        ("web_jobs.png", f"{BASE_URL}/frontend/#/jobs"),
        ("web_browse.png", f"{BASE_URL}/frontend/#/browse"),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        for filename, url in targets:
            page.goto(url, wait_until="networkidle", timeout=120_000)
            page.wait_for_timeout(750)
            page.screenshot(path=str(OUT_DIR / filename), full_page=True)
            print(str(OUT_DIR / filename))

        browser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

