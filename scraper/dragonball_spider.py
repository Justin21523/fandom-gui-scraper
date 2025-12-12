# scraper/dragonball_spider.py
"""
Dragon Ball Specific Spider

Specialized spider for the Dragon Ball Fandom wiki with optimized
selectors and extraction logic for Dragon Ball character data.
"""

import re
from typing import Dict, List, Optional, Any, Generator
from urllib.parse import urljoin
from scrapy.http import Response

from scraper.fandom_spider import FandomSpider


class DragonBallSpider(FandomSpider):
    """
    Specialized spider for Dragon Ball Fandom wiki.

    This spider extends the generic FandomSpider with Dragon Ball-specific
    optimizations, including:
    - Power level extraction
    - Ki techniques and attacks
    - Transformation tracking
    - Race identification (Saiyan, Namekian, etc.)
    - Saga/arc appearance tracking
    - Fusion information
    """

    name = "dragonball"

    # Dragon Ball Fandom base URL
    allowed_domains = ["dragonball.fandom.com"]
    start_urls = ["https://dragonball.fandom.com/wiki/Category:Characters"]

    def __init__(self, max_characters: int = None, *args, **kwargs):  # type: ignore
        """
        Initialize Dragon Ball spider.

        Args:
            max_characters: Maximum number of characters to scrape
        """
        super().__init__(
            anime_name="Dragon Ball", max_characters=max_characters, *args, **kwargs
        )

        # Dragon Ball specific selectors
        self.dragonball_selectors = {
            # Race and species
            "race": '.pi-data[data-source="Race"] .pi-data-value a::text',
            "species": '.pi-data[data-source="Species"] .pi-data-value::text',
            # Physical info
            "gender": '.pi-data[data-source="Gender"] .pi-data-value::text',
            "height": '.pi-data[data-source="Height"] .pi-data-value::text',
            "weight": '.pi-data[data-source="Weight"] .pi-data-value::text',
            "age": '.pi-data[data-source="Age"] .pi-data-value::text',
            "birthday": '.pi-data[data-source="Date of birth"] .pi-data-value::text',
            "death_date": '.pi-data[data-source="Date of death"] .pi-data-value::text',
            # Affiliations
            "occupation": '.pi-data[data-source="Occupation"] .pi-data-value::text',
            "allegiance": '.pi-data[data-source="Allegiance"] .pi-data-value a::text',
            "family": '.pi-data[data-source="Family"] .pi-data-value a::text',
            # Combat info
            "power_level": '.pi-data[data-source="Power Level"] .pi-data-value::text',
            "ki_color": '.pi-data[data-source="Ki Color"] .pi-data-value::text',
            # Techniques
            "techniques": '.pi-data[data-source="Techniques"] .pi-data-value a::text',
            "signature_technique": '.pi-data[data-source="Signature technique"] .pi-data-value::text',
            # Transformations
            "transformations": '.pi-data[data-source="Transformations"] .pi-data-value a::text',
            # Story info
            "debut_manga": '.pi-data[data-source="Manga Debut"] .pi-data-value::text',
            "debut_anime": '.pi-data[data-source="Anime Debut"] .pi-data-value::text',
            "saga": '.pi-data[data-source="Saga"] .pi-data-value::text',
            # Status
            "status": '.pi-data[data-source="Status"] .pi-data-value::text',
        }

        # Update selectors with Dragon Ball specific ones
        self.selectors.update(self.dragonball_selectors)

        # Override base URL
        self.base_url = "https://dragonball.fandom.com"

        self.logger.info("Initialized Dragon Ball spider with specialized selectors")

    def parse_character(
        self, response: Response
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Parse Dragon Ball character page with specialized extraction.

        Args:
            response: Scrapy response object

        Yields:
            Dragon Ball character data dictionary
        """
        character_url = response.meta.get("character_url", response.url)
        self.logger.info(f"Parsing Dragon Ball character: {character_url}")

        try:
            # Get base character data
            character_data = self.extract_character_basic_info(response)

            # Extract Dragon Ball specific data
            dragonball_data = self.extract_dragonball_specific_data(response)
            character_data.update(dragonball_data)

            # Extract techniques
            character_data["techniques"] = self.extract_techniques(response)

            # Extract transformations
            character_data["transformations"] = self.extract_transformations(response)

            # Extract images
            character_data["images"] = self.extract_character_images(response)

            # Set anime source
            character_data["anime_name"] = "Dragon Ball"
            character_data["source_url"] = character_url

            # Update counter
            self.characters_scraped += 1

            yield character_data

        except Exception as e:
            self.logger.error(f"Error parsing Dragon Ball character {character_url}: {e}")

    def extract_dragonball_specific_data(self, response: Response) -> Dict[str, Any]:
        """
        Extract Dragon Ball-specific character data.

        Args:
            response: Scrapy response object

        Returns:
            Dictionary with Dragon Ball-specific data
        """
        data = {}

        # Extract race/species
        race = response.css(self.dragonball_selectors["race"]).get()
        if race:
            data["race"] = self.normalizer.clean_text(race)
            data["is_saiyan"] = "saiyan" in race.lower()
        else:
            data["is_saiyan"] = False

        # Extract allegiance/affiliations
        allegiances = response.css(self.dragonball_selectors["allegiance"]).getall()
        if allegiances:
            data["affiliations"] = [
                self.normalizer.clean_text(a) for a in allegiances
            ]

        # Extract family relationships
        family = response.css(self.dragonball_selectors["family"]).getall()
        if family:
            data["family_members"] = [
                self.normalizer.clean_text(f) for f in family
            ]

        # Extract power level if available
        power_level = response.css(self.dragonball_selectors["power_level"]).get()
        if power_level:
            data["power_level"] = self.parse_power_level(power_level)

        # Extract ki color
        ki_color = response.css(self.dragonball_selectors["ki_color"]).get()
        if ki_color:
            data["ki_color"] = self.normalizer.clean_text(ki_color)

        # Extract physical info
        for field in ["gender", "height", "weight", "age", "birthday"]:
            value = response.css(self.dragonball_selectors[field]).get()
            if value:
                data[field] = self.normalizer.clean_text(value)

        # Extract status
        status = response.css(self.dragonball_selectors["status"]).get()
        if status:
            status_clean = self.normalizer.clean_text(status).lower()
            data["status"] = status_clean
            # Check for multiple deaths (common in Dragon Ball)
            if "deceased" in status_clean or "dead" in status_clean:
                data["has_died"] = True
            else:
                data["has_died"] = False

        # Extract debut info
        for field in ["debut_manga", "debut_anime", "saga"]:
            value = response.css(self.dragonball_selectors[field]).get()
            if value:
                data[field] = self.normalizer.clean_text(value)

        return data

    def parse_power_level(self, power_level_str: str) -> Optional[int]:
        """
        Parse power level string to integer.

        Args:
            power_level_str: Power level string (may contain text)

        Returns:
            Integer power level or None
        """
        try:
            # Remove commas and extract number
            cleaned = re.sub(r"[^\d]", "", power_level_str)
            if cleaned:
                return int(cleaned)
        except (ValueError, TypeError):
            pass
        return None

    def extract_techniques(self, response: Response) -> List[Dict[str, str]]:
        """
        Extract character techniques and ki attacks.

        Args:
            response: Scrapy response object

        Returns:
            List of technique dictionaries
        """
        techniques = []

        # Extract from infobox
        technique_links = response.css(
            self.dragonball_selectors["techniques"]
        ).getall()

        for tech in technique_links:
            techniques.append({
                "name": self.normalizer.clean_text(tech),
                "type": "Ki Technique",
            })

        # Extract signature technique
        signature = response.css(
            self.dragonball_selectors["signature_technique"]
        ).get()

        if signature:
            techniques.insert(0, {
                "name": self.normalizer.clean_text(signature),
                "type": "Signature",
                "is_signature": True,
            })

        # Extract from abilities section
        ability_section = response.css(
            "#Techniques ~ ul li a::text, "
            "#Power_and_abilities ~ ul li a::text, "
            "#Special_abilities ~ ul li a::text"
        ).getall()

        for ability in ability_section[:30]:
            name = self.normalizer.clean_text(ability)
            if name and name not in [t["name"] for t in techniques]:
                techniques.append({
                    "name": name,
                    "type": "Ability",
                })

        return techniques

    def extract_transformations(self, response: Response) -> List[Dict[str, Any]]:
        """
        Extract character transformations.

        Args:
            response: Scrapy response object

        Returns:
            List of transformation dictionaries
        """
        transformations = []

        # Extract from infobox
        transform_links = response.css(
            self.dragonball_selectors["transformations"]
        ).getall()

        for transform in transform_links:
            name = self.normalizer.clean_text(transform)
            transformations.append({
                "name": name,
                "is_super_saiyan": "super saiyan" in name.lower(),
            })

        # Extract from transformations section
        transform_section = response.css(
            "#Transformations ~ ul li a::text, "
            "#Forms_and_transformations ~ ul li a::text"
        ).getall()

        for transform in transform_section[:20]:
            name = self.normalizer.clean_text(transform)
            if name and name not in [t["name"] for t in transformations]:
                transformations.append({
                    "name": name,
                    "is_super_saiyan": "super saiyan" in name.lower(),
                })

        return transformations

    def get_character_list_url(self) -> str:
        """Get URL for Dragon Ball character list."""
        return "https://dragonball.fandom.com/wiki/Category:Characters"

    def parse_character_list(
        self, response: Response
    ) -> Generator[Any, None, None]:
        """
        Parse Dragon Ball character list page.

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
                for skip in ["category:", "template:", "file:", "user:", "list_of"]
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
