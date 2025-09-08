# scraper/onepiece_spider.py
"""
One Piece Specific Spider

Specialized spider for the One Piece Fandom wiki with optimized
selectors and extraction logic for One Piece character data.
"""

import scrapy
from typing import Dict, List, Optional, Any, Generator
from urllib.parse import urljoin
from scrapy.http import Response

from .fandom_spider import FandomSpider


class OnePieceSpider(FandomSpider):
    """
    Specialized spider for One Piece Fandom wiki.

    This spider extends the generic FandomSpider with One Piece-specific
    optimizations, including:
    - Devil Fruit information extraction
    - Bounty tracking
    - Crew affiliation detection
    - Fighting style categorization
    - Haki abilities identification
    """

    name = "onepiece"

    def __init__(self, max_characters: int = None, *args, **kwargs):  # type: ignore
        """
        Initialize One Piece spider.

        Args:
            max_characters: Maximum number of characters to scrape
        """
        super().__init__(
            anime_name="One Piece", max_characters=max_characters, *args, **kwargs
        )

        # One Piece specific selectors
        self.onepiece_selectors = {
            # Devil Fruit information
            "devil_fruit_name": '.pi-data[data-source="devil fruit"] .pi-data-value::text',
            "devil_fruit_type": '.pi-data[data-source="devil fruit type"] .pi-data-value::text',
            # Bounty information
            "bounty_current": '.pi-data[data-source="bounty"] .pi-data-value::text',
            "bounty_history": ".bounty-history .bounty-amount::text",
            # Crew and affiliation
            "crew_name": '.pi-data[data-source="crew"] .pi-data-value a::text',
            "occupation": '.pi-data[data-source="occupation"] .pi-data-value::text',
            "status": '.pi-data[data-source="status"] .pi-data-value::text',
            # Physical characteristics
            "height": '.pi-data[data-source="height"] .pi-data-value::text',
            "age": '.pi-data[data-source="age"] .pi-data-value::text',
            "birthday": '.pi-data[data-source="birthday"] .pi-data-value::text',
            # Fighting abilities
            "fighting_style": ".fighting-style-section li::text",
            "haki_types": ".haki-section .haki-type::text",
            "weapons": ".weapons-section .weapon-name::text",
            # Story information
            "first_appearance": '.pi-data[data-source="first appearance"] .pi-data-value::text',
            "origin": '.pi-data[data-source="origin"] .pi-data-value::text',
            "epithet": '.pi-data[data-source="epithet"] .pi-data-value::text',
        }

        # Update selectors with One Piece specific ones
        self.selectors.update(self.onepiece_selectors)

        self.logger.info("Initialized One Piece spider with specialized selectors")

    def parse_character(
        self, response: Response
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Parse One Piece character page with specialized extraction.

        Args:
            response: Scrapy response object

        Yields:
            One Piece character data dictionary
        """
        character_url = response.meta.get("character_url", response.url)
        self.logger.info(f"Parsing One Piece character: {character_url}")

        try:
            # Get base character data
            character_data = self.extract_character_basic_info(response)

            # Extract One Piece specific data
            onepiece_data = self.extract_onepiece_specific_data(response)
            character_data.update(onepiece_data)

            # Extract images with One Piece specific handling
            character_data["images"] = self.extract_onepiece_images(response)

            # Extract Devil Fruit information
            character_data["devil_fruit"] = self.extract_devil_fruit_info(response)

            # Extract bounty information
            character_data["bounty"] = self.extract_bounty_info(response)

            # Extract crew and affiliation
            character_data["affiliation"] = self.extract_affiliation_info(response)

            # Extract fighting abilities
            character_data["fighting_abilities"] = self.extract_fighting_abilities(
                response
            )

            # Extract story elements
            character_data["story_info"] = self.extract_story_info(response)

            # Add One Piece specific metadata
            character_data.update(
                {
                    "source_url": character_url,
                    "anime_name": "One Piece",
                    "wiki_type": "onepiece_fandom",
                    "extraction_date": self.get_current_timestamp(),
                    "spider_version": "1.0-onepiece",
                }
            )

            # Normalize data with One Piece specific rules
            normalized_data = self.normalize_onepiece_data(character_data)

            # Update progress
            self.characters_scraped += 1
            progress = min(
                100, (self.characters_scraped / (self.max_characters or 100)) * 100
            )
            self._update_progress(
                f"Scraped One Piece character: {character_data.get('name', 'Unknown')}",
                progress,  # type: ignore
            )

            self.logger.info(
                f"Successfully extracted One Piece character: {character_data.get('name')}"
            )
            yield normalized_data

        except Exception as e:
            self.logger.error(
                f"Failed to parse One Piece character {character_url}: {e}"
            )
            yield {
                "error": str(e),
                "source_url": character_url,
                "anime_name": "One Piece",
                "extraction_date": self.get_current_timestamp(),
            }

    def extract_onepiece_specific_data(self, response: Response) -> Dict[str, Any]:
        """
        Extract One Piece specific character information.

        Args:
            response: Scrapy response object

        Returns:
            Dictionary with One Piece specific data
        """
        data = {}

        # Extract epithet (nickname)
        epithet = response.css(self.selectors["epithet"]).get()
        if epithet:
            data["epithet"] = epithet.strip().strip('"')

        # Extract physical characteristics
        physical_data = {}

        height = response.css(self.selectors["height"]).get()
        if height:
            physical_data["height"] = self.parse_height(height.strip())

        age = response.css(self.selectors["age"]).get()
        if age:
            physical_data["age"] = self.parse_age(age.strip())

        birthday = response.css(self.selectors["birthday"]).get()
        if birthday:
            physical_data["birthday"] = birthday.strip()

        if physical_data:
            data["physical_characteristics"] = physical_data

        # Extract origin/hometown
        origin = response.css(self.selectors["origin"]).get()
        if origin:
            data["origin"] = origin.strip()

        # Extract first appearance
        first_appearance = response.css(self.selectors["first_appearance"]).get()
        if first_appearance:
            data["first_appearance"] = first_appearance.strip()

        return data

    def extract_devil_fruit_info(self, response: Response) -> Optional[Dict[str, str]]:
        """
        Extract Devil Fruit information if character has one.

        Args:
            response: Scrapy response object

        Returns:
            Devil Fruit information dictionary or None
        """
        devil_fruit_name = response.css(self.selectors["devil_fruit_name"]).get()

        if not devil_fruit_name or devil_fruit_name.strip().lower() in [
            "none",
            "n/a",
            "-",
        ]:
            return None

        devil_fruit_info = {"name": devil_fruit_name.strip()}

        # Extract fruit type
        fruit_type = response.css(self.selectors["devil_fruit_type"]).get()
        if fruit_type:
            devil_fruit_info["type"] = fruit_type.strip()

        # Try to extract more detailed Devil Fruit information
        df_section = response.css(".devil-fruit-section, .abilities-section")
        if df_section:
            # Extract Devil Fruit abilities
            abilities = df_section.css("li::text, p::text").getall()
            if abilities:
                devil_fruit_info["abilities"] = [  # type: ignore
                    ability.strip()
                    for ability in abilities
                    if ability and ability.strip()
                ]

        return devil_fruit_info

    def extract_bounty_info(self, response: Response) -> Optional[Dict[str, Any]]:
        """
        Extract bounty information.

        Args:
            response: Scrapy response object

        Returns:
            Bounty information dictionary or None
        """
        current_bounty = response.css(self.selectors["bounty_current"]).get()

        if not current_bounty or current_bounty.strip().lower() in ["none", "n/a", "-"]:
            return None

        bounty_info = {"current": self.parse_bounty_amount(current_bounty.strip())}

        # Extract bounty history
        bounty_history = response.css(self.selectors["bounty_history"]).getall()
        if bounty_history:
            history = []
            for bounty in bounty_history:
                parsed_bounty = self.parse_bounty_amount(bounty.strip())
                if parsed_bounty:
                    history.append(parsed_bounty)

            if history:
                bounty_info["history"] = history  # type: ignore

        return bounty_info

    def extract_affiliation_info(self, response: Response) -> Dict[str, Any]:
        """
        Extract crew and affiliation information.

        Args:
            response: Scrapy response object

        Returns:
            Affiliation information dictionary
        """
        affiliation = {}

        # Extract crew name
        crew_name = response.css(self.selectors["crew_name"]).get()
        if crew_name:
            affiliation["crew"] = crew_name.strip()

        # Extract occupation/position
        occupation = response.css(self.selectors["occupation"]).get()
        if occupation:
            affiliation["occupation"] = occupation.strip()

        # Extract status (alive, dead, unknown)
        status = response.css(self.selectors["status"]).get()
        if status:
            affiliation["status"] = status.strip()

        # Try to extract more detailed affiliation info
        affiliation_section = response.css(".affiliation-section, .crew-section")
        if affiliation_section:
            # Extract former crews or affiliations
            former_crews = affiliation_section.css(
                ".former-crew::text, .previous-affiliation::text"
            ).getall()
            if former_crews:
                affiliation["former_affiliations"] = [
                    crew.strip() for crew in former_crews if crew and crew.strip()
                ]

        return affiliation

    def extract_fighting_abilities(self, response: Response) -> Dict[str, List[str]]:
        """
        Extract fighting styles and combat abilities.

        Args:
            response: Scrapy response object

        Returns:
            Fighting abilities dictionary
        """
        abilities = {}

        # Extract fighting styles
        fighting_styles = response.css(self.selectors["fighting_style"]).getall()
        if fighting_styles:
            abilities["fighting_styles"] = [
                style.strip() for style in fighting_styles if style and style.strip()
            ]

        # Extract Haki types
        haki_types = response.css(self.selectors["haki_types"]).getall()
        if haki_types:
            abilities["haki"] = [
                haki.strip() for haki in haki_types if haki and haki.strip()
            ]

        # Extract weapons
        weapons = response.css(self.selectors["weapons"]).getall()
        if weapons:
            abilities["weapons"] = [
                weapon.strip() for weapon in weapons if weapon and weapon.strip()
            ]

        # Try to extract additional combat information
        combat_section = response.css(".combat-section, .abilities-section")
        if combat_section:
            # Extract special techniques
            techniques = combat_section.css(
                ".technique-name::text, .move-name::text"
            ).getall()
            if techniques:
                abilities["special_techniques"] = [
                    technique.strip()
                    for technique in techniques
                    if technique and technique.strip()
                ]

        return abilities

    def extract_story_info(self, response: Response) -> Dict[str, str]:
        """
        Extract story-related information.

        Args:
            response: Scrapy response object

        Returns:
            Story information dictionary
        """
        story_info = {}

        # Extract first appearance
        first_appearance = response.css(self.selectors["first_appearance"]).get()
        if first_appearance:
            story_info["first_appearance"] = first_appearance.strip()

        # Extract origin/hometown
        origin = response.css(self.selectors["origin"]).get()
        if origin:
            story_info["origin"] = origin.strip()

        # Try to extract story arc information
        story_section = response.css(".story-section, .appearances-section")
        if story_section:
            # Extract major story arcs
            story_arcs = story_section.css(".arc-name::text, .saga-name::text").getall()
            if story_arcs:
                story_info["major_arcs"] = [
                    arc.strip() for arc in story_arcs if arc and arc.strip()
                ]

        return story_info

    def extract_onepiece_images(self, response: Response) -> List[Dict[str, str]]:
        """
        Extract images with One Piece specific classification.

        Args:
            response: Scrapy response object

        Returns:
            List of image data with One Piece specific types
        """
        images = self.extract_character_images(response)

        # Add One Piece specific image classification
        for image in images:
            image["type"] = self.classify_onepiece_image(image["url"])

        return images

    def classify_onepiece_image(self, image_url: str) -> str:
        """
        Classify image type with One Piece specific categories.

        Args:
            image_url: Image URL

        Returns:
            One Piece specific image type
        """
        url_lower = image_url.lower()

        # One Piece specific image types
        if "bounty" in url_lower or "wanted" in url_lower:
            return "bounty_poster"
        elif "devil_fruit" in url_lower or "fruit" in url_lower:
            return "devil_fruit"
        elif "crew" in url_lower or "flag" in url_lower:
            return "crew_symbol"
        elif "ship" in url_lower:
            return "ship"
        elif "weapon" in url_lower:
            return "weapon"
        else:
            # Fall back to generic classification
            return self.classify_image_type(image_url)

    def parse_bounty_amount(self, bounty_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse bounty amount from text.

        Args:
            bounty_text: Raw bounty text

        Returns:
            Parsed bounty information
        """
        if not bounty_text or bounty_text.lower() in ["none", "n/a", "-", "unknown"]:
            return None

        import re

        # Remove common prefixes and suffixes
        cleaned_text = (
            bounty_text.replace("฿", "").replace("Beli", "").replace("berries", "")
        )
        cleaned_text = re.sub(r"[^\d,.]", "", cleaned_text)

        if not cleaned_text:
            return {"raw_text": bounty_text, "amount": None, "currency": "berries"}

        try:
            # Convert to numeric value
            numeric_value = float(cleaned_text.replace(",", ""))

            return {
                "raw_text": bounty_text,
                "amount": int(numeric_value),
                "currency": "berries",
                "formatted": f"฿{int(numeric_value):,}",
            }
        except ValueError:
            return {"raw_text": bounty_text, "amount": None, "currency": "berries"}

    def parse_height(self, height_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse height information from text.

        Args:
            height_text: Raw height text

        Returns:
            Parsed height information
        """
        if not height_text:
            return None

        import re

        # Extract numeric values and units
        height_match = re.search(r"(\d+(?:\.\d+)?)\s*(cm|m|ft|in)", height_text.lower())

        if height_match:
            value = float(height_match.group(1))
            unit = height_match.group(2)

            # Convert to centimeters for standardization
            if unit == "m":
                cm_value = value * 100
            elif unit == "ft":
                cm_value = value * 30.48
            elif unit == "in":
                cm_value = value * 2.54
            else:
                cm_value = value

            return {
                "raw_text": height_text,
                "value": value,
                "unit": unit,
                "cm": round(cm_value, 1),
            }

        return {"raw_text": height_text, "value": None, "unit": None, "cm": None}

    def parse_age(self, age_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse age information from text.

        Args:
            age_text: Raw age text

        Returns:
            Parsed age information
        """
        if not age_text:
            return None

        import re

        # Extract numeric age
        age_match = re.search(r"(\d+)", age_text)

        if age_match:
            age_value = int(age_match.group(1))

            return {
                "raw_text": age_text,
                "value": age_value,
                "category": self.categorize_age(age_value),
            }

        return {"raw_text": age_text, "value": None, "category": "unknown"}

    def categorize_age(self, age: int) -> str:
        """
        Categorize age into groups.

        Args:
            age: Numeric age

        Returns:
            Age category
        """
        if age < 18:
            return "child"
        elif age < 30:
            return "young_adult"
        elif age < 50:
            return "adult"
        else:
            return "senior"

    def normalize_onepiece_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply One Piece specific data normalization.

        Args:
            data: Raw character data

        Returns:
            Normalized character data
        """
        # Use base normalizer first
        normalized_data = self.normalizer.normalize_character_data(data)

        # Apply One Piece specific normalizations
        if "epithet" in normalized_data:
            # Clean up epithet formatting
            epithet = normalized_data["epithet"]
            epithet = epithet.replace('"', "").replace("'", "")
            normalized_data["epithet"] = epithet

        # Standardize crew names
        if (
            "affiliation" in normalized_data
            and "crew" in normalized_data["affiliation"]
        ):
            crew_name = normalized_data["affiliation"]["crew"]
            normalized_data["affiliation"]["crew"] = self.standardize_crew_name(
                crew_name
            )

        # Ensure consistent Devil Fruit naming
        if "devil_fruit" in normalized_data and normalized_data["devil_fruit"]:
            df_name = normalized_data["devil_fruit"]["name"]
            normalized_data["devil_fruit"]["name"] = self.standardize_devil_fruit_name(
                df_name
            )

        return normalized_data

    def standardize_crew_name(self, crew_name: str) -> str:
        """
        Standardize crew name formatting.

        Args:
            crew_name: Raw crew name

        Returns:
            Standardized crew name
        """
        # Common crew name standardizations
        standardizations = {
            "straw hat pirates": "Straw Hat Pirates",
            "strawhat pirates": "Straw Hat Pirates",
            "straw hats": "Straw Hat Pirates",
            "whitebeard pirates": "Whitebeard Pirates",
            "red hair pirates": "Red Hair Pirates",
            "big mom pirates": "Big Mom Pirates",
            "beast pirates": "Beasts Pirates",
        }

        crew_lower = crew_name.lower()
        return standardizations.get(crew_lower, crew_name)

    def standardize_devil_fruit_name(self, fruit_name: str) -> str:
        """
        Standardize Devil Fruit name formatting.

        Args:
            fruit_name: Raw fruit name

        Returns:
            Standardized fruit name
        """
        # Ensure "no Mi" suffix is properly formatted
        if "no mi" in fruit_name.lower() and "no Mi" not in fruit_name:
            fruit_name = fruit_name.replace("no mi", "no Mi").replace("No mi", "no Mi")

        return fruit_name
