# scraper/base_spider.py
"""
Base Spider Module for Fandom Scraper

This module provides the foundation spider class that all specific
Fandom wiki spiders will inherit from. It includes common functionality
for handling requests, parsing responses, and managing spider configuration.
"""

import scrapy
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from urllib.parse import urljoin, urlparse
from scrapy import Spider, Request
from scrapy.http import Response, Request
from utils.logger import get_logger


class BaseSpider(scrapy.Spider):
    """
    Abstract base class for all Fandom wiki spiders.

    This class provides common functionality for:
    - URL handling and validation
    - Request configuration and rate limiting
    - Response processing and error handling
    - Progress tracking and callback management
    - Selector configuration loading

    Attributes:
        name: Spider identifier for Scrapy framework
        allowed_domains: List of domains this spider can crawl
        start_urls: Initial URLs for crawling
        custom_settings: Spider-specific Scrapy settings
    """

    name = "base_spider"
    allowed_domains = ["fandom.com"]
    start_urls = []

    # Default spider settings
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "DOWNLOAD_DELAY_RANDOMIZE_RANGE": 0.5,
        "CONCURRENT_REQUESTS": 8,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        "USER_AGENT": "FandomScraper/1.0 (+https://github.com/user/fandom-scraper)",
        "COOKIES_ENABLED": True,
        "TELNETCONSOLE_ENABLED": False,
    }

    def __init__(
        self,
        anime_name: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        data_callback: Optional[Callable] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize the base spider with configuration and callbacks.

        Args:
            anime_name: Name of the anime to scrape (optional)
            progress_callback: Callback function for progress updates
            data_callback: Callback function for extracted data
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        # Spider configuration
        self.anime_name = anime_name
        self.start_time = time.time()
        self.page_count = 0
        self.item_count = 0
        self.error_count = 0

        # Callback functions for GUI integration
        self.progress_callback = progress_callback
        self.data_callback = data_callback

        # Load spider configuration
        self.selector_config = self._load_selector_config()
        self.spider_config = self._load_spider_config()

        # Initialize logger
        self.logger = get_logger(self.__class__.__name__)  # type: ignore

        self.logger.info(f"Initialized {self.name} spider for anime: {anime_name}")

    @property
    def custom_logger(self):
        """Access the custom logger safely."""
        return self.logger

    def _load_selector_config(self) -> Dict[str, Any]:
        """
        Load CSS/XPath selector configuration from file.

        Returns:
            Dictionary containing selector configuration
        """
        try:
            # This will be implemented when we create the selector config system
            # For now, return default selectors
            return {
                "character_list": {
                    "character_links": "a[href*='/wiki/']:not([href*='Category:']):not([href*='File:'])",
                    "next_page": ".category-page__pagination .category-page__pagination-next",
                },
                "character_page": {
                    "name": "h1.page-header__title",
                    "infobox": ".portable-infobox",
                    "description": ".mw-parser-output > p:first-of-type",
                    "main_image": ".pi-image img",
                    "gallery_images": ".wikia-gallery img",
                },
            }
        except Exception as e:
            self.logger.warning(f"Failed to load selector config: {e}")
            return {}

    def _load_spider_config(self) -> Dict[str, Any]:
        """
        Load spider-specific configuration.

        Returns:
            Dictionary containing spider configuration
        """
        return {
            "max_pages": 100,
            "max_characters": 1000,
            "download_images": True,
            "respect_robots_txt": True,
            "enable_autothrottle": True,
        }

    def start_requests(self) -> List[Request]:
        """
        Generate initial requests for the spider.

        Returns:
            List of Scrapy Request objects
        """
        if not self.start_urls:
            self.logger.error("No start URLs defined for spider")
            return []

        requests = []
        for url in self.start_urls:
            request = Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                meta={"page_type": "start_page", "anime_name": self.anime_name},
            )
            requests.append(request)

        self.logger.info(f"Generated {len(requests)} initial requests")
        return requests

    def parse(self, response: Response) -> Any:
        """
        Default parse method. Should be overridden by subclasses.

        Args:
            response: Scrapy Response object

        Yields:
            Items or additional requests
        """
        self.logger.warning(f"Parse method not implemented for {response.url}")
        self._update_progress("Parsing page", 0)

    def parse_character_page(self, response: Response) -> Dict[str, Any]:
        """
        Parse individual character page and extract data.

        Args:
            response: Scrapy Response object for character page

        Returns:
            Dictionary containing extracted character data
        """
        try:
            # Update progress
            self._update_progress(f"Parsing character page: {response.url}", None)

            # Extract basic character information
            selectors = self.selector_config.get("character_page", {})

            character_data = {
                "name": self._extract_text(response, selectors.get("name", "")),
                "url": response.url,
                "anime": self.anime_name,
                "description": self._extract_text(
                    response, selectors.get("description", "")
                ),
                "scraped_at": time.time(),
            }

            # Extract infobox data if available
            infobox_data = self._parse_infobox(response)
            character_data.update(infobox_data)

            # Extract images
            images = self._extract_images(response)
            character_data["image_urls"] = images

            # Increment item counter
            self.item_count += 1

            # Notify data callback if available
            if self.data_callback:
                self.data_callback(character_data)

            return character_data

        except Exception as e:
            self.logger.error(f"Failed to parse character page {response.url}: {e}")
            self.error_count += 1
            return {}

    def _parse_infobox(self, response: Response) -> Dict[str, Any]:
        """
        Parse character infobox data.

        Args:
            response: Scrapy Response object

        Returns:
            Dictionary containing infobox data
        """
        infobox_data = {}

        try:
            # This will be implemented with specific infobox parsing logic
            # For now, return basic structure
            infobox_selector = self.selector_config.get("character_page", {}).get(
                "infobox", ""
            )

            if infobox_selector:
                infobox = response.css(infobox_selector)
                if infobox:
                    # Extract key-value pairs from infobox
                    # This is a simplified version - real implementation will be more robust
                    pass

        except Exception as e:
            self.logger.warning(f"Failed to parse infobox: {e}")

        return infobox_data

    def _extract_images(self, response: Response) -> List[str]:
        """
        Extract image URLs from the page.

        Args:
            response: Scrapy Response object

        Returns:
            List of image URLs
        """
        images = []

        try:
            selectors = self.selector_config.get("character_page", {})

            # Main character image
            main_image_selector = selectors.get("main_image", "")
            if main_image_selector:
                main_image = response.css(main_image_selector + "::attr(src)").get()
                if main_image:
                    images.append(urljoin(response.url, main_image))

            # Gallery images
            gallery_selector = selectors.get("gallery_images", "")
            if gallery_selector:
                gallery_images = response.css(gallery_selector + "::attr(src)").getall()
                for img_url in gallery_images:
                    if img_url:
                        images.append(urljoin(response.url, img_url))

        except Exception as e:
            self.logger.warning(f"Failed to extract images: {e}")

        return list(set(images))  # Remove duplicates

    def _extract_text(self, response: Response, selector: str) -> str:
        """
        Extract and clean text from response using selector.

        Args:
            response: Scrapy Response object
            selector: CSS selector string

        Returns:
            Cleaned text content
        """
        if not selector:
            return ""

        try:
            text = response.css(selector + "::text").get()
            if text:
                # Clean and normalize text
                text = text.strip()
                text = " ".join(text.split())  # Normalize whitespace
                return text
        except Exception as e:
            self.logger.warning(
                f"Failed to extract text with selector '{selector}': {e}"
            )

        return ""

    def _update_progress(self, message: str, percentage: Optional[int]) -> None:
        """
        Update progress through callback if available.

        Args:
            message: Progress message
            percentage: Completion percentage (0-100)
        """
        if self.progress_callback:
            try:
                self.progress_callback(percentage or 0, message)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")

        # Log progress message
        self.logger.info(f"Progress: {message}")

    def handle_error(self, failure) -> None:
        """
        Handle request errors and failures.

        Args:
            failure: Twisted Failure object
        """
        self.error_count += 1
        request = failure.request

        self.logger.error(f"Request failed for {request.url}: {failure.value}")

        # Update progress with error information
        self._update_progress(f"Error processing {request.url}", None)

    def get_spider_stats(self) -> Dict[str, Any]:
        """
        Get current spider statistics.

        Returns:
            Dictionary containing spider statistics
        """
        elapsed_time = time.time() - self.start_time

        return {
            "spider_name": self.name,
            "anime_name": self.anime_name,
            "elapsed_time": elapsed_time,
            "pages_processed": self.page_count,
            "items_extracted": self.item_count,
            "errors_encountered": self.error_count,
            "pages_per_minute": (
                (self.page_count / elapsed_time * 60) if elapsed_time > 0 else 0
            ),
        }

    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is allowed for this spider.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid and allowed
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            # Check if domain is in allowed domains
            for allowed_domain in self.allowed_domains:
                if allowed_domain in domain:
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"URL validation failed for {url}: {e}")
            return False

    def create_request(
        self, url: str, callback: Callable = None, meta: Dict[str, Any] = None, **kwargs  # type: ignore
    ) -> Request:
        """
        Create a properly configured Scrapy Request.

        Args:
            url: Target URL
            callback: Callback function for response processing
            meta: Request metadata
            **kwargs: Additional request parameters

        Returns:
            Configured Scrapy Request object
        """
        if not self.validate_url(url):
            self.logger.warning(f"Invalid URL rejected: {url}")
            return None  # type: ignore

        # Default callback to parse method
        if callback is None:
            callback = self.parse

        # Default meta information
        if meta is None:
            meta = {}

        meta.update(
            {
                "spider_name": self.name,
                "anime_name": self.anime_name,
                "timestamp": time.time(),
            }
        )

        request = Request(
            url=url, callback=callback, errback=self.handle_error, meta=meta, **kwargs
        )

        return request

    def closed(self, reason: str) -> None:
        """
        Called when spider is closed.

        Args:
            reason: Reason for spider closure
        """
        stats = self.get_spider_stats()

        self.logger.info(f"Spider {self.name} closed. Reason: {reason}")
        self.logger.info(f"Final stats: {stats}")

        # Final progress update
        if reason == "finished":
            self._update_progress("Scraping completed successfully", 100)
        else:
            self._update_progress(f"Scraping stopped: {reason}", None)


class FandomSpiderMixin:
    """
    Mixin class providing Fandom-specific functionality.

    This mixin adds specialized methods for handling Fandom wiki
    pages, including navigation, content extraction, and URL patterns.
    """

    def get_fandom_base_url(self, anime_name: str) -> str:
        """
        Generate base Fandom URL for given anime.

        Args:
            anime_name: Name of the anime

        Returns:
            Base URL for the anime's Fandom wiki
        """
        # Convert anime name to URL-friendly format
        wiki_name = anime_name.lower().replace(" ", "").replace("-", "")
        return f"https://{wiki_name}.fandom.com"

    def get_character_category_url(self, base_url: str) -> str:
        """
        Generate character category URL for Fandom wiki.

        Args:
            base_url: Base Fandom wiki URL

        Returns:
            URL for character category page
        """
        return f"{base_url}/wiki/Category:Characters"

    def extract_fandom_page_title(self, response: Response) -> str:
        """
        Extract page title from Fandom wiki page.

        Args:
            response: Scrapy Response object

        Returns:
            Page title text
        """
        # Try multiple selectors for page title
        title_selectors = [
            "h1.page-header__title::text",
            "h1.PageHeader__title::text",
            "h1#firstHeading::text",
            "title::text",
        ]

        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()

        return ""

    def is_character_page(self, response: Response) -> bool:
        """
        Check if the current page is a character page.

        Args:
            response: Scrapy Response object

        Returns:
            True if page appears to be a character page
        """
        # Check for character-specific indicators
        indicators = [
            ".portable-infobox",  # Character infobox
            '[data-source="name"]',  # Character name field
            ".character-infobox",  # Alternative infobox class
        ]

        for indicator in indicators:
            if response.css(indicator):
                return True

        # Check page categories
        categories = response.css(".page-footer__categories a::text").getall()
        for category in categories:
            if "character" in category.lower():
                return True

        return False

    def extract_fandom_categories(self, response: Response) -> List[str]:
        """
        Extract page categories from Fandom wiki page.

        Args:
            response: Scrapy Response object

        Returns:
            List of category names
        """
        categories = []

        # Extract from footer categories
        footer_categories = response.css(".page-footer__categories a::text").getall()
        categories.extend([cat.strip() for cat in footer_categories if cat.strip()])

        # Extract from category navigation
        nav_categories = response.css(".category-navigation a::text").getall()
        categories.extend([cat.strip() for cat in nav_categories if cat.strip()])

        return list(set(categories))  # Remove duplicates


# Example usage and testing
if __name__ == "__main__":
    # This section can be used for testing the base spider
    import sys
    from pathlib import Path

    # Add project root to Python path for imports
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # Example of how to create a spider instance
    def example_progress_callback(percentage: int, message: str):
        print(f"Progress: {percentage}% - {message}")

    def example_data_callback(data: Dict[str, Any]):
        print(f"Extracted data: {data}")

    # Create spider instance
    spider = BaseSpider(
        anime_name="One Piece",
        progress_callback=example_progress_callback,
        data_callback=example_data_callback,
    )

    print(f"Created spider: {spider.name}")
    print(f"Anime: {spider.anime_name}")
    print(f"Allowed domains: {spider.allowed_domains}")
    print(f"Selector config loaded: {bool(spider.selector_config)}")

    # Test URL validation
    test_urls = [
        "https://onepiece.fandom.com/wiki/Monkey_D._Luffy",
        "https://naruto.fandom.com/wiki/Naruto_Uzumaki",
        "https://evil-site.com/malware",
    ]

    for url in test_urls:
        is_valid = spider.validate_url(url)
        print(f"URL {url} is {'valid' if is_valid else 'invalid'}")

    # Get initial stats
    stats = spider.get_spider_stats()
    print(f"Initial stats: {stats}")
