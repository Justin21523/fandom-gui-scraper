"""
Universal Fandom Spider with Brave Search Integration

This spider can scrape any Fandom wiki by accepting either:
1. Direct Fandom URL
2. Anime/series name (uses Brave Search to discover URL)

Supports multi-category crawling:
- Characters
- Episodes
- Galleries
- Chapters

Features:
- Brave Search API integration for URL discovery
- Configurable crawl scope and limits per category
- Page type detection (URL patterns + content selectors)
- Category-aware progress tracking
- Organized storage following AI_WAREHOUSE 3.0 structure
"""

import os
import re
import yaml
import json
from typing import List, Dict, Any, Optional, Literal
from pathlib import Path
from urllib.parse import urlparse, urljoin, urlencode, quote

import scrapy
from scrapy.http import Response, Request

# Import base spider and existing functionality
from scraper.base_spider import BaseSpider
from scraper.fandom_spider import FandomSpiderMixin
from utils.brave_search import BraveSearchClient, FandomSearchResult
from utils.logger import get_logger


class PageTypeDetector:
    """
    Detect page type from URL and content.

    Uses multiple strategies for accurate detection:
    1. URL pattern matching (fastest)
    2. Content selectors (most reliable)
    3. Default fallback
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

        # Load URL patterns from config
        config_path = Path(__file__).parent.parent / 'config' / 'universal_scraper.yaml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                detection_config = config.get('page_detection', {})
                self.url_patterns = detection_config.get('url_patterns', {})
                self.content_selectors = detection_config.get('content_selectors', {})
        else:
            self._init_default_patterns()

    def _init_default_patterns(self):
        """Initialize default detection patterns if config not found."""
        self.url_patterns = {
            'character': [
                r'^/wiki/(?!Episode_|Chapter_|Gallery|Category:)[A-Z].*',
                r'^/wiki/.*_\(character\)'
            ],
            'episode': [
                r'^/wiki/Episode_\d+',
                r'^/wiki/.*_\(Episode\)',
                r'^/wiki/Episode_.*'
            ],
            'gallery': [
                r'^/wiki/.*_Gallery$',
                r'^/wiki/Gallery',
                r'^/wiki/.*_(gallery|images)'
            ],
            'chapter': [
                r'^/wiki/Chapter_\d+',
                r'^/wiki/.*_\(Chapter\)'
            ],
            'category': [
                r'^/wiki/Category:'
            ]
        }

        self.content_selectors = {
            'character': [
                '.character-infobox',
                '.pi-theme-character',
                '.portable-infobox.pi-theme-character'
            ],
            'episode': [
                '.episode-infobox',
                '.pi-theme-episode'
            ],
            'gallery': [
                '.gallery-image-wrapper',
                '.wikia-gallery'
            ]
        }

    def detect_from_url(self, url: str) -> Optional[str]:
        """
        Detect page type from URL pattern.

        Args:
            url: Page URL

        Returns:
            Page type or None if no match
        """
        parsed = urlparse(url)
        path = parsed.path

        # Check each page type's patterns
        for page_type, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, path, re.IGNORECASE):
                    return page_type

        return None

    def detect_from_content(self, response: Response) -> Optional[str]:
        """
        Detect page type from page content.

        Args:
            response: Scrapy response

        Returns:
            Page type or None if no match
        """
        for page_type, selectors in self.content_selectors.items():
            for selector in selectors:
                if response.css(selector):
                    return page_type

        return None

    def detect(self, url: str, response: Optional[Response] = None) -> str:
        """
        Detect page type using all available strategies.

        Args:
            url: Page URL
            response: Scrapy response (optional)

        Returns:
            Detected page type (defaults to 'character' if unknown)
        """
        # Try URL pattern first (faster)
        url_type = self.detect_from_url(url)
        if url_type in ['episode', 'gallery', 'chapter', 'category']:
            # High confidence types
            return url_type

        # Try content detection if response available
        if response:
            content_type = self.detect_from_content(response)
            if content_type:
                return content_type

        # Default to character if URL type was detected but not high-confidence
        if url_type:
            return url_type

        # Final fallback
        return 'character'


class UniversalFandomSpider(BaseSpider, FandomSpiderMixin):
    """
    Universal Fandom wiki spider with multi-category support.

    This spider can scrape any Fandom wiki using either:
    - Direct URL input
    - Anime/series name with Brave Search discovery

    Supports configurable crawling of:
    - Character pages
    - Episode pages
    - Gallery/media pages
    - Chapter pages (manga)
    """

    name = "universal_fandom"

    @staticmethod
    def _to_bool(value) -> bool:
        """Convert string/bool value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'y')
        return bool(value)

    def __init__(
        self,
        input_source: str,
        input_type: Literal["url", "name"] = "name",
        use_playwright: bool = False,
        use_playwright_detail_pages: bool = False,
        crawl_characters: bool = True,
        crawl_episodes: bool = True,
        crawl_galleries: bool = True,
        crawl_chapters: bool = False,
        max_chars: int = 100,
        max_episodes: int = 50,
        max_gallery_images: int = 200,
        max_chapters: int = 50,
        **kwargs
    ):
        """
        Initialize universal spider.

        Args:
            input_source: Fandom URL or anime/series name
            input_type: "url" or "name"
            crawl_characters: Enable character crawling
            crawl_episodes: Enable episode crawling
            crawl_galleries: Enable gallery crawling
            crawl_chapters: Enable chapter crawling
            max_chars: Max characters to scrape (0 = unlimited)
            max_episodes: Max episodes to scrape
            max_gallery_images: Max gallery images
            max_chapters: Max chapters to scrape
            **kwargs: Additional spider arguments
        """
        # Note: Don't set self.logger directly as Scrapy Spider has read-only logger property
        # The spider.logger will be automatically available from Scrapy
        # If custom logger needed, access via get_logger() in methods

        # Convert string parameters to correct types (from command line args)
        use_playwright = self._to_bool(use_playwright)
        use_playwright_detail_pages = self._to_bool(use_playwright_detail_pages)
        crawl_characters = self._to_bool(crawl_characters)
        crawl_episodes = self._to_bool(crawl_episodes)
        crawl_galleries = self._to_bool(crawl_galleries)
        crawl_chapters = self._to_bool(crawl_chapters)
        max_chars = int(max_chars) if max_chars is not None else 100
        max_episodes = int(max_episodes) if max_episodes is not None else 50
        max_gallery_images = int(max_gallery_images) if max_gallery_images is not None else 200
        max_chapters = int(max_chapters) if max_chapters is not None else 50

        # Discover wiki URL if input is name
        if input_type == "name":
            self.wiki_url = self._discover_wiki_url(input_source)
            if not self.wiki_url:
                raise ValueError(f"Could not find Fandom wiki for: {input_source}")
        else:
            self.wiki_url = self._validate_and_normalize_url(input_source)

        # Extract anime name and domain from URL
        self.anime_name = self._extract_anime_name_from_url(self.wiki_url)
        self.wiki_domain = self._extract_domain_from_url(self.wiki_url)
        self.use_playwright = use_playwright
        self.use_playwright_detail_pages = use_playwright_detail_pages
        self._character_parser = None

        # Set up crawl configuration
        self.crawl_config = {
            'characters': {
                'enabled': crawl_characters,
                'max': max_chars,
                'count': 0,
                'category_pages': ['Category:Characters', 'Characters', 'List_of_Characters']
            },
            'episodes': {
                'enabled': crawl_episodes,
                'max': max_episodes,
                'count': 0,
                'category_pages': ['Category:Episodes', 'Episodes', 'Episode_List']
            },
            'galleries': {
                'enabled': crawl_galleries,
                'max': max_gallery_images,
                'count': 0,
                'category_pages': ['Category:Images', 'Gallery', 'Images']
            },
            'chapters': {
                'enabled': crawl_chapters,
                'max': max_chapters,
                'count': 0,
                'category_pages': ['Category:Chapters', 'Chapter_List']
            }
        }

        # Initialize page type detector
        self.page_detector = PageTypeDetector()
        self.max_category_depth = 3
        try:
            config_path = Path(__file__).parent.parent / 'config' / 'universal_scraper.yaml'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    cfg = yaml.safe_load(f) or {}
                self.max_category_depth = int((cfg.get('limits') or {}).get('max_depth', 3))
        except Exception:
            self.max_category_depth = 3

        # Initialize base spider
        super().__init__(anime_name=self.anime_name, **kwargs)

        # Update settings for universal spider
        data_root = Path(os.getenv("FANDOM_DATA_ROOT", "/mnt/data/datasets/fandom"))
        self.custom_settings.update(
            {
                "IMAGES_STORE": str(data_root / "images"),
            }
        )

    def _with_playwright_detail_meta(self, meta: dict) -> dict:
        if not self.use_playwright_detail_pages:
            return meta
        merged = dict(meta)
        merged.update(
            {
                "playwright": True,
                "playwright_include_page": False,
                "playwright_page_goto_kwargs": {
                    "wait_until": "domcontentloaded",
                    "timeout": 60000,
                },
            }
        )
        return merged

    def _discover_wiki_url(self, anime_name: str) -> Optional[str]:
        """
        Use Brave Search to discover Fandom wiki URL.

        Args:
            anime_name: Name of anime/series

        Returns:
            Fandom wiki URL or None if not found
        """
        self.logger.info(f"Searching for Fandom wiki: {anime_name}")

        try:
            client = BraveSearchClient()
            results = client.find_fandom_wiki(anime_name, top_n=5)

            if not results:
                self.logger.error(f"No Fandom wiki found for: {anime_name}")
                return None

            # Use highest-scoring result
            best_result = results[0]
            self.logger.info(
                f"Found wiki: {best_result.title} "
                f"(score: {best_result.relevance_score:.1f}) "
                f"URL: {best_result.url}"
            )

            return best_result.url

        except Exception as e:
            self.logger.error(f"Brave Search failed: {e}")
            return None

    def _validate_and_normalize_url(self, url: str) -> str:
        """
        Validate and normalize Fandom URL.

        Args:
            url: Input URL

        Returns:
            Normalized URL

        Raises:
            ValueError: If URL is not a valid Fandom URL
        """
        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Validate it's a Fandom URL
        if '.fandom.com' not in url:
            raise ValueError(f"Not a valid Fandom URL: {url}")

        # Normalize to base wiki URL
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        return base_url

    def _extract_anime_name_from_url(self, url: str) -> str:
        """
        Extract anime name from Fandom URL.

        Args:
            url: Fandom wiki URL

        Returns:
            Anime name extracted from domain
        """
        parsed = urlparse(url)
        domain = parsed.netloc

        # Extract subdomain (e.g., "onepiece" from "onepiece.fandom.com")
        subdomain = domain.split('.')[0]

        # Convert to title case with spaces
        # "onepiece" -> "One Piece"
        # "attackontitan" -> "Attack On Titan"
        import re
        # Insert space before capital letters
        spaced = re.sub(r'([A-Z])', r' \1', subdomain)
        # Title case
        title = spaced.title().strip()

        return title if title else subdomain

    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc

    def start_requests(self):
        """
        Generate initial requests for enabled categories.

        Yields:
            Initial category page requests
        """
        self.logger.info(f"=" * 80)
        self.logger.info(f"Starting Universal Fandom Spider")
        self.logger.info(f"=" * 80)
        self.logger.info(f"Anime: {self.anime_name}")
        self.logger.info(f"Wiki URL: {self.wiki_url}")
        self.logger.info(f"Crawl config: {self._get_config_summary()}")
        self.logger.info(f"=" * 80)

        # Generate requests for each enabled category
        for category, config in self.crawl_config.items():
            if not config['enabled']:
                self.logger.info(f"Skipping {category} (disabled)")
                continue

            self.logger.info(f"")
            self.logger.info(f"Enabling {category} crawl:")
            self.logger.info(f"  Max items: {config['max'] if config['max'] > 0 else 'unlimited'}")
            self.logger.info(f"  Trying {len(config['category_pages'])} category page variants...")

            # Try each category page variant
            for idx, category_page in enumerate(config['category_pages'], 1):
                # Prefer MediaWiki API for Category:* pages (faster + more consistent than HTML parsing).
                if category_page.startswith('Category:'):
                    api_url = self._build_categorymembers_api_url(category_page)
                    self.logger.info(
                        f"  [{idx}/{len(config['category_pages'])}] Requesting (API): {category_page} -> {api_url}"
                    )
                    yield Request(
                        url=api_url,
                        callback=self.parse_category_api,
                        errback=self.handle_error,
                        meta={
                            'category': category,
                            'anime_name': self.anime_name,
                            'category_title': category_page,
                            'category_depth': 0,
                        },
                        dont_filter=True,
                    )
                    continue

                url = f"{self.wiki_url}/wiki/{category_page}"
                self.logger.info(f"  [{idx}/{len(config['category_pages'])}] Requesting: {url}")

                meta = {
                    'category': category,
                    'anime_name': self.anime_name,
                    'dont_redirect': False,
                }

                # Default: use regular Scrapy downloader (faster and avoids Playwright timeouts).
                # If a site is blocked (e.g., Cloudflare/403) we can retry with Playwright later.
                if self.use_playwright:
                    from scrapy_playwright.page import PageMethod
                    meta.update({
                        'playwright': True,
                        'playwright_include_page': False,
                        'playwright_page_goto_kwargs': {
                            'wait_until': 'domcontentloaded',
                            'timeout': 60000,
                        },
                        'playwright_page_methods': [
                            PageMethod(
                                'wait_for_selector',
                                '.category-page__member, .category-page__members, #mw-pages, .mw-category, .mw-category-group',
                                timeout=15000,
                            ),
                            PageMethod('wait_for_timeout', 500),
                        ],
                    })

                yield Request(
                    url=url,
                    callback=self.parse_category_page,
                    errback=self.handle_error,
                    meta=meta,
                    dont_filter=True  # Allow revisiting category pages
                )

    def _build_categorymembers_api_url(self, category_title: str, cmcontinue: Optional[str] = None) -> str:
        """Build MediaWiki categorymembers API URL for this wiki."""
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': category_title,
            'cmlimit': 500,
            'cmnamespace': '0|14',  # pages + subcategories
            'format': 'json',
        }
        if cmcontinue:
            params['cmcontinue'] = cmcontinue
        return f"{self.wiki_url}/api.php?{urlencode(params)}"

    def _build_wiki_page_url(self, title: str) -> str:
        """Build a canonical /wiki/ URL for a given page title."""
        normalized = title.replace(' ', '_')
        return f"{self.wiki_url}/wiki/{quote(normalized, safe='()!$,:;@/._-')}"

    def parse_category_api(self, response: Response):
        """
        Parse category members via MediaWiki API (preferred for Category:* sources).

        Yields:
            Requests for pages/subcategories discovered in this category.
        """
        category = response.meta.get('category', 'characters')
        config = self.crawl_config[category]
        category_title = response.meta.get('category_title')
        category_depth = int(response.meta.get('category_depth', 0) or 0)

        self.logger.info(f"=== Parsing category API: {category_title} (depth {category_depth}/{self.max_category_depth}) ===")

        try:
            payload = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse category API JSON for {response.url}: {e}")
            return

        members = (((payload.get('query') or {}).get('categorymembers')) or [])
        self.logger.info(f"Category API returned {len(members)} members")

        # Handle pagination
        cont = payload.get('continue') or {}
        cmcontinue = cont.get('cmcontinue')

        # Queue members
        for member in members:
            if config['max'] > 0 and config['count'] >= config['max']:
                break

            ns = member.get('ns')
            title = member.get('title') or ''
            if not title:
                continue

            # Subcategory recursion
            if ns == 14 and category_depth < self.max_category_depth:
                subcat_title = title if title.startswith('Category:') else f"Category:{title}"
                yield Request(
                    url=self._build_categorymembers_api_url(subcat_title),
                    callback=self.parse_category_api,
                    errback=self.handle_error,
                    meta={
                        'category': category,
                        'anime_name': self.anime_name,
                        'category_title': subcat_title,
                        'category_depth': category_depth + 1,
                    },
                )
                continue

            # Normal pages
            if ns != 0:
                continue

            page_url = self._build_wiki_page_url(title)
            page_type = self.page_detector.detect(page_url)
            expected_type = category.rstrip('s')
            if page_type != expected_type:
                continue

            config['count'] += 1
            callback = self._get_callback_for_type(page_type)
            self.logger.info(f"[{category}] Queueing {page_type}: {page_url}")
            yield Request(
                url=page_url,
                callback=callback,
                errback=self.handle_error,
                meta=self._with_playwright_detail_meta(
                    {
                        'category': category,
                        'page_type': page_type,
                        'anime_name': self.anime_name,
                    }
                ),
            )

        # Continue paging if needed and we still want more
        if cmcontinue and (config['max'] == 0 or config['count'] < config['max']):
            yield Request(
                url=self._build_categorymembers_api_url(category_title, cmcontinue=cmcontinue),
                callback=self.parse_category_api,
                errback=self.handle_error,
                meta=dict(response.meta),
                dont_filter=True,
            )

    def _get_config_summary(self) -> str:
        """Get human-readable crawl config summary."""
        enabled = [cat for cat, cfg in self.crawl_config.items() if cfg['enabled']]
        return f"Categories: {', '.join(enabled)}"

    def parse_category_page(self, response: Response):
        """
        Parse category listing pages.

        Args:
            response: Category page response

        Yields:
            Requests for individual pages found in category
        """
        category = response.meta.get('category', 'characters')
        config = self.crawl_config[category]

        self.logger.info(f"=== Parsing category page: {response.url} ===")
        self.logger.info(f"Category: {category}")
        self.logger.info(f"Current count: {config['count']}/{config['max']}")
        self.logger.info(f"Response status: {response.status}")
        self.logger.info(f"Response size: {len(response.body)} bytes")

        # If this looks like a block page or the HTML is incomplete, retry once with Playwright.
        if not response.meta.get('playwright') and not response.meta.get('playwright_retry'):
            body_lower = response.text.lower() if hasattr(response, 'text') else ''
            blocked_markers = ['cloudflare', 'cf-browser-verification', 'attention required', 'captcha']
            if response.status in (403, 429) or any(m in body_lower for m in blocked_markers):
                from scrapy_playwright.page import PageMethod
                retry_meta = dict(response.meta)
                retry_meta.update({
                    'playwright': True,
                    'playwright_retry': True,
                    'playwright_include_page': False,
                    'playwright_page_goto_kwargs': {
                        'wait_until': 'domcontentloaded',
                        'timeout': 60000,
                    },
                    'playwright_page_methods': [
                        PageMethod(
                            'wait_for_selector',
                            '.category-page__member, .category-page__members, #mw-pages, .mw-category, .mw-category-group',
                            timeout=15000,
                        ),
                        PageMethod('wait_for_timeout', 500),
                    ],
                })
                self.logger.warning(f"Retrying with Playwright due to suspected blocking: {response.url}")
                yield Request(
                    url=response.url,
                    callback=self.parse_category_page,
                    errback=self.handle_error,
                    meta=retry_meta,
                    dont_filter=True,
                )
                return

        # Extract page links from category
        # Fandom uses different structures for category pages
        page_links = []
        link_sources = {}  # Track where each link came from for debugging

        # Strategy 1: Category members (.category-page__member)
        strategy1_links = response.css('.category-page__member a::attr(href)').getall()
        for link in strategy1_links:
            page_links.append(link)
            link_sources[link] = 'category-page__member'
        self.logger.info(f"Strategy 1 (category-page__member): found {len(strategy1_links)} links")

        # Strategy 2: Standard MediaWiki category pages (#mw-pages)
        strategy2_links = response.css('#mw-pages a::attr(href)').getall()
        for link in strategy2_links:
            if link not in page_links:
                page_links.append(link)
                link_sources[link] = 'mw-pages'
        self.logger.info(f"Strategy 2 (mw-pages): found {len(strategy2_links)} links")

        # Strategy 3: Gallery grid
        strategy3_links = response.css('.wikia-gallery-item a::attr(href)').getall()
        for link in strategy3_links:
            if link not in page_links:
                page_links.append(link)
                link_sources[link] = 'wikia-gallery-item'
        self.logger.info(f"Strategy 3 (wikia-gallery-item): found {len(strategy3_links)} links")

        # Strategy 4: Category page listings (newer Fandom layout)
        strategy4_links = response.css('.category-page__members a::attr(href)').getall()
        for link in strategy4_links:
            if link not in page_links:
                page_links.append(link)
                link_sources[link] = 'category-page__members'
        self.logger.info(f"Strategy 4 (category-page__members): found {len(strategy4_links)} links")

        # Strategy 5: mw-category-group (standard MediaWiki)
        strategy5_links = response.css('.mw-category-group a::attr(href)').getall()
        for link in strategy5_links:
            if link not in page_links:
                page_links.append(link)
                link_sources[link] = 'mw-category-group'
        self.logger.info(f"Strategy 5 (mw-category-group): found {len(strategy5_links)} links")

        # Strategy 6: Any link in main content that looks like a wiki article
        strategy6_links = response.css('.mw-content-text a[href*="/wiki/"]::attr(href)').getall()
        for link in strategy6_links:
            if link not in page_links and '/wiki/Category:' not in link and '/wiki/Special:' not in link:
                page_links.append(link)
                link_sources[link] = 'mw-content-text'
        self.logger.info(f"Strategy 6 (mw-content-text): found {len(strategy6_links)} new links")

        # Make URLs absolute
        page_links = [urljoin(response.url, link) for link in page_links]

        self.logger.info(f"Total unique links found: {len(page_links)}")

        # If this category page only lists subcategories, recurse into them (common on many Fandom wikis).
        category_depth = int(response.meta.get('category_depth', 0) or 0)
        subcategory_links = [l for l in page_links if '/wiki/Category:' in l]
        if subcategory_links and category_depth < self.max_category_depth:
            queued = 0
            for subcat_url in subcategory_links:
                # Don't keep Playwright meta for subcategory traversal unless explicitly enabled
                next_meta = dict(response.meta)
                next_meta.pop('playwright', None)
                next_meta.pop('playwright_page_methods', None)
                next_meta.pop('playwright_page_goto_kwargs', None)
                next_meta['category_depth'] = category_depth + 1
                yield Request(
                    url=subcat_url,
                    callback=self.parse_category_page,
                    errback=self.handle_error,
                    meta=next_meta,
                )
                queued += 1
            self.logger.info(
                f"Queued {queued} subcategories for traversal (depth {category_depth + 1}/{self.max_category_depth})"
            )

        # If we got a 200 but found no links, retry once with Playwright (some wikis lazy-load lists).
        if len(page_links) == 0 and not response.meta.get('playwright') and not response.meta.get('playwright_retry'):
            from scrapy_playwright.page import PageMethod
            retry_meta = dict(response.meta)
            retry_meta.update({
                'playwright': True,
                'playwright_retry': True,
                'playwright_include_page': False,
                'playwright_page_goto_kwargs': {
                    'wait_until': 'domcontentloaded',
                    'timeout': 60000,
                },
                'playwright_page_methods': [
                    PageMethod(
                        'wait_for_selector',
                        '.category-page__member, .category-page__members, #mw-pages, .mw-category, .mw-category-group',
                        timeout=15000,
                    ),
                    PageMethod('wait_for_timeout', 500),
                ],
            })
            self.logger.warning(f"No links found; retrying category page with Playwright: {response.url}")
            yield Request(
                url=response.url,
                callback=self.parse_category_page,
                errback=self.handle_error,
                meta=retry_meta,
                dont_filter=True,
            )
            return

        # Filter and yield requests
        processed_count = 0
        skipped_count = 0
        for link in page_links:
            # Check if we've hit the limit for this category
            if config['max'] > 0 and config['count'] >= config['max']:
                self.logger.info(f"Reached max limit for {category}: {config['max']}")
                break

            # Skip non-wiki pages
            if '/wiki/' not in link:
                skipped_count += 1
                continue

            # Skip special pages, file pages, category pages
            if any(x in link for x in ['/wiki/Special:', '/wiki/File:', '/wiki/Category:',
                                        '/wiki/Template:', '/wiki/Help:', '/wiki/MediaWiki:']):
                skipped_count += 1
                continue

            # Detect page type
            page_type = self.page_detector.detect(link)

            # Log detection for first few links
            if processed_count < 5:
                self.logger.debug(f"Link: {link}")
                self.logger.debug(f"  Detected type: {page_type}")
                self.logger.debug(f"  Expected type: {category.rstrip('s')}")

            # Only process if page type matches category
            expected_type = category.rstrip('s')  # 'characters' -> 'character'
            if page_type != expected_type:
                skipped_count += 1
                continue

            # Increment counter
            config['count'] += 1
            processed_count += 1

            # Yield request with appropriate callback
            callback = self._get_callback_for_type(page_type)

            self.logger.info(f"[{category}] Queueing {page_type}: {link}")

            yield Request(
                url=link,
                callback=callback,
                errback=self.handle_error,
                meta=self._with_playwright_detail_meta(
                    {
                        'category': category,
                        'page_type': page_type,
                        'anime_name': self.anime_name,
                    }
                ),
            )

        self.logger.info(f"=== Category page processed: {processed_count} items queued, {skipped_count} skipped ===")

        # Handle pagination (next page link)
        # Try multiple selectors for pagination
        next_page = None

        # Strategy 1: Standard category pagination
        next_page = response.css('.category-page__pagination-next::attr(href)').get()

        # Strategy 2: MediaWiki pagination
        if not next_page:
            next_page = response.css('#mw-pages a:contains("next")::attr(href)').get()

        # Strategy 3: Look for "next" or ">" links
        if not next_page:
            next_page = response.css('a:contains("next page")::attr(href), a:contains("Next")::attr(href)').get()

        if next_page:
            next_url = urljoin(response.url, next_page)
            self.logger.info(f"Following pagination: {next_url}")
            yield Request(
                url=next_url,
                callback=self.parse_category_page,
                meta=response.meta,
                dont_filter=True
            )

    def handle_error(self, failure):
        """
        Enhanced error handler with detailed logging.

        Args:
            failure: Twisted Failure object
        """
        request = failure.request
        category = request.meta.get('category', 'unknown')

        self.logger.error(f"=" * 80)
        self.logger.error(f"ERROR processing request:")
        self.logger.error(f"  URL: {request.url}")
        self.logger.error(f"  Category: {category}")
        self.logger.error(f"  Error type: {failure.type.__name__}")
        self.logger.error(f"  Error message: {failure.value}")
        self.logger.error(f"=" * 80)

        # Check if it's a 404 (category page doesn't exist)
        if '404' in str(failure.value) or 'NotFound' in str(failure.type.__name__):
            self.logger.warning(f"Category page not found (404): {request.url}")
            self.logger.warning(f"This variant may not exist for this wiki. Trying next variant...")
        elif '403' in str(failure.value) or 'Forbidden' in str(failure.type.__name__):
            self.logger.error(f"Access forbidden (403): {request.url}")
            self.logger.error(f"The wiki may be blocking our crawler")
        elif 'robots.txt' in str(failure.value).lower():
            self.logger.error(f"Blocked by robots.txt: {request.url}")
            self.logger.error(f"Consider setting ROBOTSTXT_OBEY = False for testing")

        # Call parent error handler
        super().handle_error(failure)

    def _get_callback_for_type(self, page_type: str):
        """Get parsing callback for page type."""
        callbacks = {
            'character': self.parse_character,
            'episode': self.parse_episode,
            'gallery': self.parse_gallery,
            'chapter': self.parse_chapter,
        }
        return callbacks.get(page_type, self.parse_character)

    def parse_character(self, response: Response):
        """
        Parse character page.

        Uses existing FandomSpider character parsing logic.
        """
        # Delegate to existing character parsing from FandomSpider (produces fields
        # expected by pipelines: name/anime_name/source_url/etc.).
        parser = self._get_character_parser()
        for item in parser.parse_character(response):
            if isinstance(item, dict):
                item.setdefault('content_type', 'character')
                try:
                    self.logger.info(
                        "EVENT item_scraped "
                        + json.dumps(
                            {
                                "content_type": "character",
                                "name": item.get("name"),
                                "source_url": item.get("source_url", response.url),
                            },
                            ensure_ascii=False,
                        )
                    )
                except Exception:
                    pass
            yield item

    def _get_character_parser(self):
        """Create/cache a lightweight parser using FandomSpider logic."""
        if self._character_parser is None:
            from scraper.fandom_spider import FandomSpider
            self._character_parser = FandomSpider(anime_name=self.anime_name)
        return self._character_parser

    def parse_episode(self, response: Response):
        """
        Parse episode page.

        Args:
            response: Episode page response

        Yields:
            Episode item
        """
        from models.episode_model import EpisodeInfo

        self.logger.info(f"Parsing episode page: {response.url}")

        # Extract episode data
        title = response.css('h1.page-header__title::text').get()

        # Extract episode number from title or URL
        import re
        episode_match = re.search(r'Episode[_\s]+(\d+)', response.url or title or '', re.IGNORECASE)
        episode_num = int(episode_match.group(1)) if episode_match else 0

        # Extract from infobox
        infobox = response.css('.portable-infobox, .infobox')

        synopsis = response.css('.mw-parser-output > p::text').getall()
        synopsis_text = ' '.join(synopsis).strip() if synopsis else None

        # Build episode item
        episode_data = {
            'title': title or 'Unknown Episode',
            'number': episode_num,
            'anime_name': self.anime_name,
            'source_url': response.url,
            'synopsis': synopsis_text,
            'episode_type': 'tv_episode',
            'content_type': 'episode',
        }

        # Extract additional fields from infobox if available
        for row in infobox.css('.pi-item'):
            label = row.css('.pi-data-label::text').get()
            value = row.css('.pi-data-value::text').get()

            if label and value:
                label_lower = label.lower().strip()
                if 'air date' in label_lower:
                    episode_data['air_date'] = value
                elif 'director' in label_lower:
                    episode_data['director'] = value
                elif 'writer' in label_lower:
                    episode_data['writer'] = value

        try:
            self.logger.info(
                "EVENT item_scraped "
                + json.dumps(
                    {
                        "content_type": "episode",
                        "title": episode_data.get("title"),
                        "number": episode_data.get("number"),
                        "source_url": response.url,
                    },
                    ensure_ascii=False,
                )
            )
        except Exception:
            pass
        yield episode_data

    def parse_gallery(self, response: Response):
        """
        Parse gallery page.

        Args:
            response: Gallery page response

        Yields:
            Gallery image items
        """
        from models.gallery_model import GalleryImage

        self.logger.info(f"Parsing gallery page: {response.url}")

        # Extract all images from gallery
        images = response.css('.wikia-gallery-item, .gallery-image-wrapper')

        for img_container in images:
            img_url = img_container.css('img::attr(src), img::attr(data-src)').get()
            caption = img_container.css('.lightbox-caption::text').get()

            if img_url:
                # Build gallery image item
                item = {
                    'url': img_url,
                    'anime_name': self.anime_name,
                    'source_url': response.url,
                    'caption': caption,
                    'category': 'screenshot',  # Default category
                    'content_type': 'gallery',
                }
                try:
                    self.logger.info(
                        "EVENT item_scraped "
                        + json.dumps(
                            {
                                "content_type": "gallery",
                                "url": item.get("url"),
                                "source_url": response.url,
                            },
                            ensure_ascii=False,
                        )
                    )
                except Exception:
                    pass
                yield item

    def parse_chapter(self, response: Response):
        """
        Parse chapter page (manga).

        Args:
            response: Chapter page response

        Yields:
            Chapter item
        """
        from models.episode_model import ChapterInfo

        self.logger.info(f"Parsing chapter page: {response.url}")

        title = response.css('h1.page-header__title::text').get()

        # Extract chapter number
        import re
        chapter_match = re.search(r'Chapter[_\s]+(\d+)', response.url or title or '', re.IGNORECASE)
        chapter_num = int(chapter_match.group(1)) if chapter_match else 0

        synopsis = response.css('.mw-parser-output > p::text').getall()
        synopsis_text = ' '.join(synopsis).strip() if synopsis else None

        item = {
            'title': title or 'Unknown Chapter',
            'number': chapter_num,
            'anime_name': self.anime_name,
            'manga_name': self.anime_name,
            'source_url': response.url,
            'synopsis': synopsis_text,
            'content_type': 'chapter',
        }
        try:
            self.logger.info(
                "EVENT item_scraped "
                + json.dumps(
                    {
                        "content_type": "chapter",
                        "title": item.get("title"),
                        "number": item.get("number"),
                        "source_url": response.url,
                    },
                    ensure_ascii=False,
                )
            )
        except Exception:
            pass
        yield item

    def closed(self, reason):
        """
        Called when spider is closed.

        Args:
            reason: Closing reason
        """
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info("Final statistics:")

        for category, config in self.crawl_config.items():
            if config['enabled']:
                self.logger.info(
                    f"  {category.title()}: {config['count']} pages crawled "
                    f"(max: {config['max'] if config['max'] > 0 else 'unlimited'})"
                )
