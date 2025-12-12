# scraper/naruto_spider.py
"""
Naruto Specific Spider

Specialized spider for the Naruto Fandom wiki with optimized
selectors and extraction logic for Naruto character data.
"""

import re
from typing import Dict, List, Optional, Any, Generator
from urllib.parse import urljoin
from scrapy.http import Response

from scraper.fandom_spider import FandomSpider


class NarutoSpider(FandomSpider):
    """
    Specialized spider for Naruto Fandom wiki.

    This spider extends the generic FandomSpider with Naruto-specific
    optimizations, including:
    - Jutsu and techniques extraction
    - Chakra nature identification
    - Clan affiliation detection
    - Kekkei Genkai tracking
    - Ninja rank classification
    - Tailed beast information
    """

    name = "naruto"

    # Naruto Fandom base URL
    allowed_domains = ["naruto.fandom.com"]
    start_urls = ["https://naruto.fandom.com/wiki/Category:Characters"]

    def __init__(self, max_characters: int = None, *args, **kwargs):  # type: ignore
        """
        Initialize Naruto spider.

        Args:
            max_characters: Maximum number of characters to scrape
        """
        super().__init__(
            anime_name="Naruto", max_characters=max_characters, *args, **kwargs
        )

        # Naruto specific selectors
        self.naruto_selectors = {
            # Ninja information
            "ninja_rank": '.pi-data[data-source="ninja rank"] .pi-data-value::text',
            "ninja_registration": '.pi-data[data-source="ninja registration"] .pi-data-value::text',
            "academy_grad_age": '.pi-data[data-source="academy grad. age"] .pi-data-value::text',
            "chunin_prom_age": '.pi-data[data-source="chūnin prom. age"] .pi-data-value::text',
            # Affiliation
            "affiliation": '.pi-data[data-source="affiliation"] .pi-data-value a::text',
            "team": '.pi-data[data-source="team"] .pi-data-value a::text',
            "clan": '.pi-data[data-source="clan"] .pi-data-value a::text',
            # Abilities
            "kekkei_genkai": '.pi-data[data-source="kekkei genkai"] .pi-data-value a::text',
            "nature_type": '.pi-data[data-source="nature type"] .pi-data-value a::text',
            "unique_traits": '.pi-data[data-source="unique traits"] .pi-data-value::text',
            # Tailed Beast
            "tailed_beast": '.pi-data[data-source="tailed beasts"] .pi-data-value a::text',
            "jinchuriki_status": '.pi-data[data-source="classification"] .pi-data-value::text',
            # Physical info
            "height": '.pi-data[data-source="height"] .pi-data-value::text',
            "weight": '.pi-data[data-source="weight"] .pi-data-value::text',
            "blood_type": '.pi-data[data-source="blood type"] .pi-data-value::text',
            "age": '.pi-data[data-source="age"] .pi-data-value::text',
            "birthday": '.pi-data[data-source="birthdate"] .pi-data-value::text',
            # Status
            "status": '.pi-data[data-source="status"] .pi-data-value::text',
            "occupation": '.pi-data[data-source="occupation"] .pi-data-value::text',
            # Story info
            "debut_manga": '.pi-data[data-source="manga debut"] .pi-data-value::text',
            "debut_anime": '.pi-data[data-source="anime debut"] .pi-data-value::text',
        }

        # Update selectors with Naruto specific ones
        self.selectors.update(self.naruto_selectors)

        # Override base URL
        self.base_url = "https://naruto.fandom.com"

        self.logger.info("Initialized Naruto spider with specialized selectors")

    def parse_character(
        self, response: Response
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Parse Naruto character page with specialized extraction.

        Args:
            response: Scrapy response object

        Yields:
            Naruto character data dictionary
        """
        character_url = response.meta.get("character_url", response.url)
        self.logger.info(f"Parsing Naruto character: {character_url}")

        try:
            # Get base character data
            character_data = self.extract_character_basic_info(response)

            # Extract Naruto specific data
            naruto_data = self.extract_naruto_specific_data(response)
            character_data.update(naruto_data)

            # Extract jutsu/techniques
            character_data["jutsu"] = self.extract_jutsu(response)

            # Extract images
            character_data["images"] = self.extract_character_images(response)

            # Set anime source
            character_data["anime_name"] = "Naruto"
            character_data["source_url"] = character_url

            # Update counter
            self.characters_scraped += 1

            yield character_data

        except Exception as e:
            self.logger.error(f"Error parsing Naruto character {character_url}: {e}")

    def extract_naruto_specific_data(self, response: Response) -> Dict[str, Any]:
        """
        Extract Naruto-specific character data.

        Args:
            response: Scrapy response object

        Returns:
            Dictionary with Naruto-specific data
        """
        data = {}

        # Extract ninja information
        ninja_rank = response.css(self.naruto_selectors["ninja_rank"]).get()
        if ninja_rank:
            data["ninja_rank"] = self.normalizer.clean_text(ninja_rank)

        # Extract clan
        clan = response.css(self.naruto_selectors["clan"]).getall()
        if clan:
            data["clan"] = [self.normalizer.clean_text(c) for c in clan]

        # Extract affiliations
        affiliations = response.css(self.naruto_selectors["affiliation"]).getall()
        if affiliations:
            data["affiliations"] = [self.normalizer.clean_text(a) for a in affiliations]

        # Extract team
        teams = response.css(self.naruto_selectors["team"]).getall()
        if teams:
            data["teams"] = [self.normalizer.clean_text(t) for t in teams]

        # Extract chakra nature types
        nature_types = response.css(self.naruto_selectors["nature_type"]).getall()
        if nature_types:
            data["chakra_natures"] = [
                self.normalizer.clean_text(n) for n in nature_types
            ]

        # Extract Kekkei Genkai
        kekkei_genkai = response.css(self.naruto_selectors["kekkei_genkai"]).getall()
        if kekkei_genkai:
            data["kekkei_genkai"] = [
                self.normalizer.clean_text(k) for k in kekkei_genkai
            ]

        # Extract tailed beast info
        tailed_beast = response.css(self.naruto_selectors["tailed_beast"]).get()
        if tailed_beast:
            data["tailed_beast"] = self.normalizer.clean_text(tailed_beast)
            data["is_jinchuriki"] = True
        else:
            data["is_jinchuriki"] = False

        # Extract physical info
        for field in ["height", "weight", "blood_type", "age", "birthday"]:
            value = response.css(self.naruto_selectors[field]).get()
            if value:
                data[field] = self.normalizer.clean_text(value)

        # Extract status
        status = response.css(self.naruto_selectors["status"]).get()
        if status:
            data["status"] = self.normalizer.clean_text(status).lower()

        return data

    def extract_jutsu(self, response: Response) -> List[Dict[str, str]]:
        """
        Extract character jutsu/techniques.

        Args:
            response: Scrapy response object

        Returns:
            List of jutsu dictionaries
        """
        jutsu_list = []

        # Try to find jutsu section
        jutsu_section = response.css(".jutsu-section, #Jutsu, #Abilities")

        # Extract jutsu from table if present
        jutsu_rows = response.css(
            'table.wikitable tr, .mw-parser-output table tr'
        )

        for row in jutsu_rows[:50]:  # Limit to prevent over-extraction
            jutsu_name = row.css("td:first-child a::text").get()
            if jutsu_name:
                jutsu_type = row.css("td:nth-child(2)::text").get()
                jutsu_list.append({
                    "name": self.normalizer.clean_text(jutsu_name),
                    "type": self.normalizer.clean_text(jutsu_type) if jutsu_type else "Unknown",
                })

        # Also extract from links in abilities section
        ability_links = response.css(
            "#Abilities ~ ul li a::text, #Ninjutsu ~ ul li a::text"
        ).getall()

        for ability in ability_links[:30]:
            if ability and ability not in [j["name"] for j in jutsu_list]:
                jutsu_list.append({
                    "name": self.normalizer.clean_text(ability),
                    "type": "Technique",
                })

        return jutsu_list

    def get_character_list_url(self) -> str:
        """Get URL for Naruto character list."""
        return "https://naruto.fandom.com/wiki/Category:Characters"

    def parse_character_list(
        self, response: Response
    ) -> Generator[Any, None, None]:
        """
        Parse Naruto character list page.

        Args:
            response: Scrapy response object

        Yields:
            Requests for individual character pages
        """
        # Extract character links from category page
        character_links = response.css(
            ".category-page__member-link::attr(href)"
        ).getall()

        for link in character_links:
            # Skip non-character pages
            if any(
                skip in link.lower()
                for skip in ["category:", "template:", "file:", "user:"]
            ):
                continue

            # Check max characters limit
            if self.max_characters and self.characters_scraped >= self.max_characters:
                self.logger.info(f"Reached max characters limit: {self.max_characters}")
                return

            full_url = urljoin(self.base_url, link)
            yield response.follow(
                full_url,
                callback=self.parse_character,
                meta={"character_url": full_url},
            )

        # Handle pagination
        next_page = response.css(
            ".category-page__pagination-next::attr(href)"
        ).get()

        if next_page:
            yield response.follow(next_page, callback=self.parse_character_list)
