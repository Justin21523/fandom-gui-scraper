from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scraper.mediawiki.campaign import CampaignConfig, DEFAULT_CAMPAIGN_ID, DEFAULT_TARGETS, run_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a multi-Fandom MediaWiki campaign into local wiki.db job outputs.")
    parser.add_argument("--preset", choices=["portfolio-smoke"], default="portfolio-smoke")
    parser.add_argument("--campaign-id", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument("--output-root", default="sample_data")
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--page-limit", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--rate-delay", type=float, default=1.0)
    parser.add_argument("--parse-html-limit", type=int, default=10)
    parser.add_argument("--no-page-text", action="store_true")
    parser.add_argument("--no-infobox-html", action="store_true")
    parser.add_argument("--ignore-robots", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    targets = args.targets or DEFAULT_TARGETS
    manifest = run_campaign(
        CampaignConfig(
            campaign_id=args.campaign_id,
            targets=list(targets),
            output_root=args.output_root,
            page_limit=args.page_limit,
            batch_size=args.batch_size,
            rate_delay=args.rate_delay,
            include_page_text=not args.no_page_text,
            include_infobox_html=not args.no_infobox_html,
            parse_html_limit=args.parse_html_limit,
            respect_robots=not args.ignore_robots,
            force=args.force,
        )
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
