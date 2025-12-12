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
from typing import List, Dict, Any, Optional, Literal
from pathlib import Path
from urllib.parse import urlparse, urljoin

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

    def __init__(
        self,
        input_source: str,
        input_type: Literal["url", "name"] = "name",
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
        self.logger = get_logger(self.__class__.__name__)

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

        # Initialize base spider
        super().__init__(anime_name=self.anime_name, **kwargs)

        # Update settings for universal spider
        self.custom_settings.update({
            'IMAGES_STORE': str(Path(f'/mnt/data/datasets/fandom/{self.anime_name}/images')),
        })

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
        self.logger.info(f"Starting universal spider for: {self.anime_name}")
        self.logger.info(f"Wiki URL: {self.wiki_url}")
        self.logger.info(f"Crawl config: {self._get_config_summary()}")

        # Generate requests for each enabled category
        for category, config in self.crawl_config.items():
            if not config['enabled']:
                continue

            self.logger.info(
                f"Enabling {category} crawl "
                f"(max: {config['max'] if config['max'] > 0 else 'unlimited'})"
            )

            # Try each category page variant
            for category_page in config['category_pages']:
                url = f"{self.wiki_url}/wiki/{category_page}"

                yield Request(
                    url=url,
                    callback=self.parse_category_page,
                    errback=self.handle_error,
                    meta={
                        'category': category,
                        'anime_name': self.anime_name,
                        'dont_redirect': False,
                    },
                    dont_filter=True  # Allow revisiting category pages
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

        self.logger.info(f"Parsing category page: {response.url} ({category})")

        # Extract page links from category
        # Fandom uses different structures for category pages
        page_links = []

        # Strategy 1: Category members (.category-page__member)
        page_links.extend(
            response.css('.category-page__member a::attr(href)').getall()
        )

        # Strategy 2: Standard wiki links in content
        page_links.extend(
            response.css('#mw-pages a::attr(href)').getall()
        )

        # Strategy 3: Gallery grid
        page_links.extend(
            response.css('.wikia-gallery-item a::attr(href)').getall()
        )

        # Make URLs absolute
        page_links = [urljoin(response.url, link) for link in page_links]

        # Filter and yield requests
        for link in page_links:
            # Check if we've hit the limit for this category
            if config['max'] > 0 and config['count'] >= config['max']:
                self.logger.info(f"Reached max limit for {category}: {config['max']}")
                break

            # Skip non-wiki pages
            if '/wiki/' not in link:
                continue

            # Detect page type
            page_type = self.page_detector.detect(link)

            # Only process if page type matches category
            if page_type != category.rstrip('s'):  # 'characters' -> 'character'
                continue

            # Increment counter
            config['count'] += 1

            # Yield request with appropriate callback
            callback = self._get_callback_for_type(page_type)

            yield Request(
                url=link,
                callback=callback,
                errback=self.handle_error,
                meta={
                    'category': category,
                    'page_type': page_type,
                    'anime_name': self.anime_name,
                }
            )

        # Handle pagination (next page link)
        next_page = response.css('.category-page__pagination-next::attr(href)').get()
        if next_page:
            next_url = urljoin(response.url, next_page)
            yield Request(
                url=next_url,
                callback=self.parse_category_page,
                meta=response.meta,
                dont_filter=True
            )

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
        # Delegate to existing character parsing from FandomSpider
        from scraper.fandom_spider import FandomSpider

        # Create temporary FandomSpider instance to use its methods
        temp_spider = FandomSpider(anime_name=self.anime_name)

        # Extract character data
        item = temp_spider.parse_character_page(response)

        if item:
            yield item

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
            'episode_type': 'tv_episode'
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
                yield {
                    'url': img_url,
                    'anime_name': self.anime_name,
                    'source_url': response.url,
                    'caption': caption,
                    'category': 'screenshot',  # Default category
                }

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

        yield {
            'title': title or 'Unknown Chapter',
            'number': chapter_num,
            'manga_name': self.anime_name,
            'source_url': response.url,
            'synopsis': synopsis_text,
        }

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
