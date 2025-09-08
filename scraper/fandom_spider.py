# scraper/fandom_spider.py
"""
Generic Fandom Wiki Spider

This spider provides a flexible framework for scraping character data
from any Fandom wiki site. It automatically discovers character pages
and extracts structured information using configurable selectors.
"""

import scrapy
import re
import json
from typing import Dict, List, Optional, Any, Generator
from urllib.parse import urljoin, urlparse
from scrapy.http import Response, Request
from scrapy.exceptions import CloseSpider

from .base_spider import BaseSpider, FandomSpiderMixin
from ..utils.selectors import SelectorManager
from ..utils.normalizer import DataNormalizer
from ..models.document import AnimeCharacter


class FandomSpider(BaseSpider, FandomSpiderMixin):
    """
    Generic Fandom wiki spider for extracting anime character data.

    This spider can adapt to different Fandom wiki structures by using
    configurable selectors and intelligent content detection.

    Features:
    - Automatic character page discovery
    - Flexible data extraction using CSS/XPath selectors
    - Image URL collection and validation
    - Character relationship mapping
    - Episode appearance tracking
    """

    name = "fandom"

    def __init__(
        self, anime_name: str = None, max_characters: int = None, *args, **kwargs  # type: ignore
    ):
        """
        Initialize Fandom spider with specific anime target.

        Args:
            anime_name: Target anime name (e.g., "One Piece", "Naruto")
            max_characters: Maximum number of characters to scrape (for testing)
        """
        super().__init__(anime_name=anime_name, *args, **kwargs)

        if not anime_name:
            raise ValueError("anime_name parameter is required")

        self.anime_name = anime_name
        self.max_characters = max_characters
        self.characters_scraped = 0

        # Initialize utilities
        self.selector_manager = SelectorManager()
        self.normalizer = DataNormalizer()

        # Load anime-specific configuration
        self.selectors = self.load_anime_selectors()
        self.base_url = self.get_fandom_base_url(anime_name)

        # Set start URLs
        self.start_urls = [
            self.get_character_category_url(self.base_url),
            f"{self.base_url}/wiki/Category:Main_Characters",
            f"{self.base_url}/wiki/Characters",
        ]

        self.logger.info(f"Initialized Fandom spider for: {anime_name}")
        self.logger.info(f"Base URL: {self.base_url}")
        self.logger.info(f"Start URLs: {self.start_urls}")

    def load_anime_selectors(self) -> Dict[str, str]:
        """
        Load anime-specific selectors configuration.

        Returns:
            Dictionary of CSS/XPath selectors for data extraction
        """
        try:
            # Try to load anime-specific selectors first
            selectors = self.selector_manager.get_selectors(self.anime_name)
            self.logger.info(f"Loaded specific selectors for {self.anime_name}")
            return selectors
        except FileNotFoundError:
            # Fall back to generic Fandom selectors
            selectors = self.selector_manager.get_selectors("generic_fandom")
            self.logger.info("Using generic Fandom selectors")
            return selectors

    def parse(self, response: Response) -> Generator[Request, None, None]:
        """
        Parse character category or listing pages to find character links.

        Args:
            response: Scrapy response object

        Yields:
            Requests for individual character pages
        """
        self.logger.info(f"Parsing character listing page: {response.url}")

        # Extract character page links using multiple strategies
        character_links = set()

        # Strategy 1: Category page member links
        category_links = response.css(
            self.selectors.get(
                "category_member_links", ".category-page__member-link::attr(href)"
            )
        ).getall()

        # Strategy 2: Character list links
        list_links = response.css(
            self.selectors.get(
                "character_list_links",
                'a[href*="/wiki/"][title*="Character"]::attr(href)',
            )
        ).getall()

        # Strategy 3: Character navigation links
        nav_links = response.css(
            self.selectors.get(
                "character_nav_links",
                ".character-grid a::attr(href), " ".character-list a::attr(href)",
            )
        ).getall()

        # Combine all found links
        all_links = category_links + list_links + nav_links

        for link in all_links:
            if link:
                full_url = urljoin(response.url, link)
                if self.is_character_page_url(full_url):
                    character_links.add(full_url)

        self.logger.info(f"Found {len(character_links)} character page links")

        # Create requests for character pages
        for character_url in character_links:
            if self.max_characters and self.characters_scraped >= self.max_characters:
                self.logger.info(
                    f"Reached maximum characters limit: {self.max_characters}"
                )
                return

            yield self.create_request(
                url=character_url,
                callback=self.parse_character,
                meta={"character_url": character_url},
            )

        # Look for pagination links
        pagination_links = response.css(
            self.selectors.get(
                "pagination_links", ".category-page__pagination a::attr(href)"
            )
        ).getall()

        for page_link in pagination_links:
            if page_link and "next" in page_link.lower():
                next_page_url = urljoin(response.url, page_link)
                self.logger.info(f"Following pagination: {next_page_url}")
                yield self.create_request(url=next_page_url, callback=self.parse)

    def is_character_page_url(self, url: str) -> bool:
        """
        Determine if URL points to a character page.

        Args:
            url: URL to check

        Returns:
            True if URL appears to be a character page
        """
        # Skip non-wiki pages
        if "/wiki/" not in url:
            return False

        # Skip system/meta pages
        skip_patterns = [
            "/Category:",
            "/Template:",
            "/File:",
            "/User:",
            "/Special:",
            "/Help:",
            "/Project:",
            "/Media:",
            "/MediaWiki:",
        ]

        for pattern in skip_patterns:
            if pattern in url:
                return False

        # Skip common non-character pages
        non_character_keywords = [
            "episode",
            "chapter",
            "arc",
            "season",
            "movie",
            "ova",
            "soundtrack",
            "game",
            "merchandise",
            "gallery",
            "trivia",
        ]

        url_lower = url.lower()
        for keyword in non_character_keywords:
            if keyword in url_lower:
                return False

        return True

    def parse_character(
        self, response: Response
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Parse individual character page and extract character data.

        Args:
            response: Scrapy response object for character page

        Yields:
            Character data dictionary
        """
        character_url = response.meta.get("character_url", response.url)
        self.logger.info(f"Parsing character page: {character_url}")

        try:
            # Extract basic character information
            character_data = self.extract_character_basic_info(response)

            # Extract character images
            character_data["images"] = self.extract_character_images(response)

            # Extract character relationships
            character_data["relationships"] = self.extract_character_relationships(
                response
            )

            # Extract abilities and techniques
            character_data["abilities"] = self.extract_character_abilities(response)

            # Extract appearance information
            character_data["appearances"] = self.extract_character_appearances(response)

            # Add metadata
            character_data.update(
                {
                    "source_url": character_url,
                    "anime_name": self.anime_name,
                    "extraction_date": self.get_current_timestamp(),
                    "spider_version": "1.0",
                }
            )

            # Normalize and validate data
            normalized_data = self.normalizer.normalize_character_data(character_data)

            # Update progress
            self.characters_scraped += 1
            progress = min(
                100, (self.characters_scraped / (self.max_characters or 100)) * 100
            )
            self._update_progress(
                f"Scraped character: {character_data.get('name', 'Unknown')}", progress  # type: ignore
            )

            self.logger.info(
                f"Successfully extracted character: {character_data.get('name')}"
            )
            yield normalized_data

        except Exception as e:
            self.logger.error(f"Failed to parse character page {character_url}: {e}")
            # Yield error information for tracking
            yield {
                "error": str(e),
                "source_url": character_url,
                "anime_name": self.anime_name,
                "extraction_date": self.get_current_timestamp(),
            }

    def extract_character_basic_info(self, response: Response) -> Dict[str, Any]:
        """
        Extract basic character information from page.

        Args:
            response: Scrapy response object

        Returns:
            Dictionary with basic character data
        """
        data = {}

        # Character name (try multiple selectors)
        name_selectors = [
            self.selectors.get("character_name", ".page-header__title::text"),
            "h1.page-title::text",
            ".pi-title::text",
            ".infobox-title::text",
        ]

        for selector in name_selectors:
            name = response.css(selector).get()
            if name:
                data["name"] = name.strip()
                break

        # Character description/summary
        description_selectors = [
            self.selectors.get("character_description", ".pi-data-value p::text"),
            ".character-summary::text",
            ".page-content p:first-of-type::text",
        ]

        for selector in description_selectors:
            description = response.css(selector).get()
            if description:
                data["description"] = description.strip()
                break

        # Extract infobox data
        infobox_data = self.extract_infobox_data(response)
        data.update(infobox_data)

        return data

    def extract_infobox_data(self, response: Response) -> Dict[str, Any]:
        """
        Extract structured data from character infobox.

        Args:
            response: Scrapy response object

        Returns:
            Dictionary with infobox data
        """
        infobox_data = {}

        # Common infobox selectors
        infobox_selectors = [
            ".portable-infobox .pi-data",
            ".infobox tr",
            ".character-infobox .data-row",
        ]

        for selector in infobox_selectors:
            rows = response.css(selector)
            if rows:
                for row in rows:
                    # Extract label and value
                    label_selectors = [
                        ".pi-data-label::text",
                        "th::text",
                        ".label::text",
                    ]
                    value_selectors = [
                        ".pi-data-value::text",
                        "td::text",
                        ".value::text",
                    ]

                    label = None
                    value = None

                    for label_sel in label_selectors:
                        label = row.css(label_sel).get()
                        if label:
                            break

                    for value_sel in value_selectors:
                        value = row.css(value_sel).get()
                        if value:
                            break

                    if label and value:
                        # Normalize field names
                        field_name = self.normalizer.normalize_field_name(label.strip())
                        field_value = value.strip()

                        if field_name and field_value:
                            infobox_data[field_name] = field_value

                break  # Use first successful selector

        return infobox_data

    def extract_character_images(self, response: Response) -> List[Dict[str, str]]:
        """
        Extract character image URLs and metadata.

        Args:
            response: Scrapy response object

        Returns:
            List of image data dictionaries
        """
        images = []

        # Image selectors for different page layouts
        image_selectors = [
            self.selectors.get("character_images", ".pi-image img::attr(src)"),
            ".character-image img::attr(src)",
            ".infobox-image img::attr(src)",
            ".gallery img::attr(src)",
            ".image-collection img::attr(src)",
        ]

        seen_urls = set()

        for selector in image_selectors:
            image_urls = response.css(selector).getall()

            for image_url in image_urls:
                if image_url and image_url not in seen_urls:
                    # Convert relative URLs to absolute
                    full_image_url = urljoin(response.url, image_url)

                    # Extract image metadata
                    image_data = {
                        "url": full_image_url,
                        "source_page": response.url,
                        "type": self.classify_image_type(image_url),
                        "filename": self.generate_image_filename(image_url),
                    }

                    images.append(image_data)
                    seen_urls.add(image_url)

        self.logger.debug(f"Found {len(images)} images for character")
        return images

    def extract_character_relationships(
        self, response: Response
    ) -> List[Dict[str, str]]:
        """
        Extract character relationships information.

        Args:
            response: Scrapy response object

        Returns:
            List of relationship data
        """
        relationships = []

        # Look for relationship sections
        relationship_selectors = [
            ".relationships .relationship-item",
            ".family-section .family-member",
            ".allies-section .ally-item",
        ]

        for selector in relationship_selectors:
            items = response.css(selector)

            for item in items:
                rel_name = item.css(".name::text, a::text").get()
                rel_type = item.css(".type::text, .relationship-type::text").get()

                if rel_name:
                    relationships.append(
                        {
                            "name": rel_name.strip(),
                            "type": rel_type.strip() if rel_type else "unknown",
                            "source": response.url,
                        }
                    )

        return relationships

    def extract_character_abilities(self, response: Response) -> List[str]:
        """
        Extract character abilities and techniques.

        Args:
            response: Scrapy response object

        Returns:
            List of abilities
        """
        abilities = []

        # Ability section selectors
        ability_selectors = [
            ".abilities-section li::text",
            ".powers-section li::text",
            ".techniques-list .technique-name::text",
        ]

        for selector in ability_selectors:
            ability_items = response.css(selector).getall()

            for ability in ability_items:
                if ability and ability.strip():
                    abilities.append(ability.strip())

        return list(set(abilities))  # Remove duplicates

    def extract_character_appearances(self, response: Response) -> List[Dict[str, str]]:
        """
        Extract character appearance information (episodes, arcs, etc.).

        Args:
            response: Scrapy response object

        Returns:
            List of appearance data
        """
        appearances = []

        # Appearance section selectors
        appearance_selectors = [
            ".appearances-section .episode-link",
            ".episodes-list .episode-item",
            ".arcs-section .arc-link",
        ]

        for selector in appearance_selectors:
            items = response.css(selector)

            for item in items:
                episode_name = item.css("::text").get()
                episode_link = item.css("::attr(href)").get()

                if episode_name:
                    appearances.append(
                        {
                            "name": episode_name.strip(),
                            "url": (
                                urljoin(response.url, episode_link)
                                if episode_link
                                else None
                            ),
                            "type": "episode",
                        }
                    )

        return appearances

    def classify_image_type(self, image_url: str) -> str:
        """
        Classify image type based on URL patterns.

        Args:
            image_url: Image URL

        Returns:
            Image type classification
        """
        url_lower = image_url.lower()

        if "portrait" in url_lower or "headshot" in url_lower:
            return "portrait"
        elif "full" in url_lower or "body" in url_lower:
            return "full_body"
        elif "thumb" in url_lower or "small" in url_lower:
            return "thumbnail"
        else:
            return "general"

    def generate_image_filename(self, image_url: str) -> str:
        """
        Generate appropriate filename for image.

        Args:
            image_url: Image URL

        Returns:
            Sanitized filename
        """
        # Extract filename from URL
        filename = image_url.split("/")[-1].split("?")[0]

        # Sanitize filename
        filename = re.sub(r"[^\w\-_\.]", "_", filename)

        return filename

    def get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            Current timestamp string
        """
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def get_spider_stats(self) -> Dict[str, Any]:
        """
        Get spider execution statistics.

        Returns:
            Dictionary containing spider statistics
        """
        return {
            "characters_scraped": getattr(self, "characters_scraped", 0),
            "anime_name": getattr(self, "anime_name", None),
            "max_characters": getattr(self, "max_characters", None),
            "start_time": getattr(self, "start_time", None),
            "spider_name": self.name,
        }

    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is properly formatted and allowed.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        if not url:
            return False

        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)

            # Check basic URL structure
            if not all([parsed.scheme, parsed.netloc]):
                return False

            # Check if domain is allowed
            if hasattr(self, "allowed_domains"):
                domain = parsed.netloc.lower()
                if not any(allowed in domain for allowed in self.allowed_domains):
                    return False

            return True
        except Exception:
            return False

    def handle_error(self, failure):
        """
        Handle request errors.

        Args:
            failure: Twisted failure object
        """
        self.logger.error(f"Request failed: {failure}")

        # Update error statistics
        if not hasattr(self, "error_count"):
            self.error_count = 0
        self.error_count += 1

        # Notify progress callback of error
        if hasattr(self, "progress_callback") and self.progress_callback:
            self.progress_callback(f"Request error occurred: {failure.value}", None)

    def _update_progress(self, message: str, progress: Optional[float] = None):
        """
        Update progress and notify callback.

        Args:
            message: Progress message
            progress: Progress percentage (0-100) or None
        """
        self.logger.info(f"Progress: {message}")

        if hasattr(self, "progress_callback") and self.progress_callback:
            self.progress_callback(message, progress)

        # Update internal progress tracking
        if not hasattr(self, "progress_history"):
            self.progress_history = []

        self.progress_history.append(
            {
                "timestamp": self.get_current_timestamp(),
                "message": message,
                "progress": progress,
            }
        )
