# utils/normalizer.py
"""
Data normalization and cleaning utilities.

This module provides comprehensive data cleaning and normalization functions
for text processing, URL handling, and data quality improvement.
"""

import re
import logging
import unicodedata
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin, urlparse
import html
from datetime import datetime

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Comprehensive data normalization and cleaning utility class.

    This class provides methods for cleaning and normalizing various types
    of data extracted from web scraping operations.

    Example:
        >>> normalizer = DataNormalizer()
        >>> cleaned_text = normalizer.clean_text("  Hello   World!  ")
        >>> print(cleaned_text)
        "Hello World!"
    """

    def __init__(self):
        """Initialize the data normalizer with common patterns."""
        # Common patterns for text cleaning
        self.text_patterns = {
            "extra_whitespace": re.compile(r"\s+"),
            "html_tags": re.compile(r"<[^>]+>"),
            "brackets": re.compile(r"\[.*?\]|\(.*?\)"),
            "quotes": re.compile(r'[""' "`]"),
            "special_chars": re.compile(r"[^\w\s\-.,!?]"),
        }
        self.citation_pattern = re.compile(r"\[[\d\w\s,]+\]")
        self.extra_whitespace_pattern = re.compile(r"\s+")
        self.parentheses_pattern = re.compile(r"\(\s*\)")
        self.brackets_pattern = re.compile(r"\[\s*\]")
        self.wiki_markup_pattern = re.compile(r"\{\{[^}]*\}\}")
        self.html_tag_pattern = re.compile(r"<[^>]+>")

        # Field name mappings for standardization
        self.field_mappings = {
            # Basic info
            "full name": "name",
            "character name": "name",
            "real name": "name",
            "birth name": "name",
            # Age variations
            "age": "age",
            "current age": "age",
            "years old": "age",
            # Gender variations
            "gender": "gender",
            "sex": "gender",
            # Status variations
            "status": "status",
            "alive/dead": "status",
            "current status": "status",
            # Occupation variations
            "occupation": "occupation",
            "job": "occupation",
            "profession": "occupation",
            "role": "occupation",
            "position": "occupation",
            # One Piece specific
            "epithet": "epithet",
            "nickname": "epithet",
            "alias": "epithet",
            "bounty": "bounty",
            "reward": "bounty",
            "devil fruit": "devil_fruit",
            "df": "devil_fruit",
            "crew": "crew",
            "pirate crew": "crew",
            "affiliation": "crew",
            "height": "height",
            "birthday": "birthday",
            "birth date": "birthday",
        }

        # URL patterns
        self.relative_url_pattern = re.compile(r"^/")
        self.query_param_pattern = re.compile(r"\?.*$")

        # Character name patterns
        self.title_suffix_pattern = re.compile(r"\s*\([^)]*\)$")
        self.disambiguation_pattern = re.compile(
            r"\s*\(.*character.*\)$", re.IGNORECASE
        )

        # Age patterns
        self.age_number_pattern = re.compile(r"(\d+)")
        self.age_range_pattern = re.compile(r"(\d+)\s*[-–—]\s*(\d+)")

        # Bounty patterns (for One Piece)
        self.bounty_pattern = re.compile(r"[^\d,.]")
        self.bounty_number_pattern = re.compile(r"[\d,]+")

    def clean_text(
        self,
        text: str,
        remove_citations: bool = True,
        normalize_whitespace: bool = True,
    ) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Input text to clean
            remove_citations: Whether to remove citation markers
            normalize_whitespace: Whether to normalize whitespace

        Returns:
            Cleaned text string
        """
        if not text or not isinstance(text, str):
            return ""

        # Decode HTML entities
        cleaned = html.unescape(text)

        # Remove HTML tags
        cleaned = self.html_tag_pattern.sub("", cleaned)

        # Remove wiki markup
        cleaned = self.wiki_markup_pattern.sub("", cleaned)

        # Remove citations if requested
        if remove_citations:
            cleaned = self.citation_pattern.sub("", cleaned)

        # Remove empty parentheses and brackets
        cleaned = self.parentheses_pattern.sub("", cleaned)
        cleaned = self.brackets_pattern.sub("", cleaned)

        # Normalize unicode characters
        cleaned = unicodedata.normalize("NFKC", cleaned)

        # Normalize whitespace if requested
        if normalize_whitespace:
            cleaned = self.extra_whitespace_pattern.sub(" ", cleaned)

        return cleaned.strip()

    def clean_character_name(self, name: str) -> str:
        """
        Clean character name with specific rules.

        Args:
            name: Character name to clean

        Returns:
            Cleaned character name
        """
        if not name:
            return ""

        # Basic text cleaning
        cleaned = self.clean_text(name)

        # Remove disambiguation suffixes
        cleaned = self.disambiguation_pattern.sub("", cleaned)

        # Remove common title suffixes but keep meaningful ones
        if cleaned.endswith(")"):
            # Keep important descriptors like "Captain", "Admiral", etc.
            important_descriptors = [
                "captain",
                "admiral",
                "commander",
                "lieutenant",
                "sergeant",
                "doctor",
                "professor",
                "king",
                "queen",
                "prince",
                "princess",
                "jr",
                "sr",
                "the great",
                "the terrible",
            ]

            suffix_match = self.title_suffix_pattern.search(cleaned)
            if suffix_match:
                suffix = suffix_match.group(0).lower()
                if not any(desc in suffix for desc in important_descriptors):
                    cleaned = self.title_suffix_pattern.sub("", cleaned)

        return cleaned.strip()

        """
        Normalize gender information.

        Args:
            gender: Gender string to normalize

        Returns:
            Normalized gender string
        """
        if not gender:
            return "Unknown"

        cleaned = self.clean_text(gender).lower()

        # Gender mappings
        gender_mappings = {
            "male": "Male",
            "man": "Male",
            "boy": "Male",
            "masculine": "Male",
            "female": "Female",
            "woman": "Female",
            "girl": "Female",
            "feminine": "Female",
            "non-binary": "Non-binary",
            "nonbinary": "Non-binary",
            "agender": "Agender",
            "genderless": "Genderless",
            "unknown": "Unknown",
            "varies": "Varies",
        }

        for key, value in gender_mappings.items():
            if key in cleaned:
                return value

        return "Unknown"

    def clean_description(self, description: str, max_length: int = 5000) -> str:
        """
        Clean character description with advanced formatting.

        Args:
            description: Description text to clean
            max_length: Maximum length of description

        Returns:
            Cleaned description text
        """
        if not description:
            return ""

        # Basic cleaning
        cleaned = self.clean_text(description)

        # Remove common wiki prefixes
        prefixes_to_remove = ["is a", "was a", "is an", "was an", "is the", "was the"]

        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix + " "):
                cleaned = cleaned[len(prefix) :].strip()
                # Capitalize first letter
                if cleaned:
                    cleaned = cleaned[0].upper() + cleaned[1:]

        # Truncate if too long
        if len(cleaned) > max_length:
            # Try to cut at sentence boundary
            sentences = cleaned.split(". ")
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ". ") <= max_length:
                    truncated += sentence + ". "
                else:
                    break

            if truncated:
                cleaned = truncated.rstrip()
            else:
                # Hard truncate with ellipsis
                cleaned = cleaned[: max_length - 3] + "..."

        return cleaned

    def normalize_url(self, url: str, base_url: str = None) -> str:  # type: ignore
        """
        Normalize and resolve URLs.

        Args:
            url: URL to normalize
            base_url: Base URL for resolving relative URLs

        Returns:
            Normalized absolute URL
        """
        if not url:
            return ""

        # Clean the URL
        cleaned_url = url.strip()

        # Handle relative URLs
        if self.relative_url_pattern.match(cleaned_url) and base_url:
            cleaned_url = urljoin(base_url, cleaned_url)

        # Remove query parameters for image URLs (common in Fandom)
        if any(
            ext in cleaned_url.lower()
            for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        ):
            # Keep only the path part for images
            parsed = urlparse(cleaned_url)
            cleaned_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Ensure HTTPS for security
        if cleaned_url.startswith("http://"):
            cleaned_url = cleaned_url.replace("http://", "https://", 1)

        return cleaned_url

    def clean_abilities_list(self, abilities: List[str]) -> List[str]:
        """
        Clean and normalize list of character abilities.

        Args:
            abilities: List of ability strings

        Returns:
            Cleaned list of abilities
        """
        if not abilities:
            return []

        cleaned_abilities = []
        seen_abilities = set()

        for ability in abilities:
            if not ability or not isinstance(ability, str):
                continue

            # Clean the ability text
            cleaned = self.clean_text(ability)

            # Skip very short or generic abilities
            if len(cleaned) < 3 or cleaned.lower() in ["n/a", "none", "unknown"]:
                continue

            # Remove duplicates (case-insensitive)
            if cleaned.lower() not in seen_abilities:
                cleaned_abilities.append(cleaned)
                seen_abilities.add(cleaned.lower())

        return cleaned_abilities

    def parse_bounty(self, bounty_text: str) -> Dict[str, Any]:
        """
        Parse bounty information (specific to One Piece).

        Args:
            bounty_text: Bounty text to parse

        Returns:
            Dictionary with bounty information
        """
        if not bounty_text:
            return {"amount": 0, "currency": "Berry", "formatted": "Unknown"}

        cleaned = self.clean_text(bounty_text)

        # Handle special cases
        if any(word in cleaned.lower() for word in ["unknown", "none", "n/a"]):
            return {"amount": 0, "currency": "Berry", "formatted": "Unknown"}

        if "former" in cleaned.lower() or "deceased" in cleaned.lower():
            return {"amount": 0, "currency": "Berry", "formatted": "Former bounty"}

        # Extract numbers
        numbers = self.bounty_number_pattern.findall(cleaned)
        if numbers:
            # Take the largest number found
            amounts = [
                int(num.replace(",", ""))
                for num in numbers
                if num.replace(",", "").isdigit()
            ]
            if amounts:
                max_amount = max(amounts)

                # Format the bounty nicely
                if max_amount >= 1000000000:  # Billion
                    formatted = f"{max_amount/1000000000:.1f}B Berry"
                elif max_amount >= 1000000:  # Million
                    formatted = f"{max_amount/1000000:.0f}M Berry"
                elif max_amount >= 1000:  # Thousand
                    formatted = f"{max_amount/1000:.0f}K Berry"
                else:
                    formatted = f"{max_amount:,} Berry"

                return {
                    "amount": max_amount,
                    "currency": "Berry",
                    "formatted": formatted,
                }

        return {"amount": 0, "currency": "Berry", "formatted": cleaned}

    def normalize_relationships(self, relationships: Dict[str, str]) -> Dict[str, str]:
        """
        Normalize relationship information.

        Args:
            relationships: Dictionary of relationship types to names

        Returns:
            Normalized relationships dictionary
        """
        if not relationships:
            return {}

        normalized = {}

        # Relationship type mappings
        relationship_mappings = {
            "father": "Father",
            "mother": "Mother",
            "parent": "Parent",
            "son": "Son",
            "daughter": "Daughter",
            "child": "Child",
            "brother": "Brother",
            "sister": "Sister",
            "sibling": "Sibling",
            "husband": "Husband",
            "wife": "Wife",
            "spouse": "Spouse",
            "crew": "Crew",
            "captain": "Captain",
            "mentor": "Mentor",
            "student": "Student",
            "friend": "Friend",
            "rival": "Rival",
            "enemy": "Enemy",
        }

        for rel_type, rel_name in relationships.items():
            if not rel_type or not rel_name:
                continue

            # Normalize relationship type
            rel_type_clean = self.clean_text(rel_type).lower()
            normalized_type = relationship_mappings.get(
                rel_type_clean, rel_type.title()
            )

            # Clean relationship name
            rel_name_clean = self.clean_character_name(rel_name)

            if rel_name_clean:
                normalized[normalized_type] = rel_name_clean

        return normalized

    def validate_data_quality(self, character_data: Dict[str, Any]) -> float:
        """
        Calculate data quality score based on completeness and consistency.

        Args:
            character_data: Character data dictionary

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0

        # Required fields scoring
        required_fields = {"name": 0.3, "anime": 0.2}

        for field, weight in required_fields.items():
            max_score += weight
            value = character_data.get(field)
            if value and isinstance(value, str) and len(value.strip()) > 0:
                score += weight

        # Optional fields scoring
        optional_fields = {
            "description": 0.2,
            "age": 0.1,
            "gender": 0.05,
            "occupation": 0.05,
            "abilities": 0.05,
            "relationships": 0.05,
        }

        for field, weight in optional_fields.items():
            max_score += weight
            value = character_data.get(field)

            if field in ["abilities", "relationships"]:
                if value and len(value) > 0:
                    score += weight
            elif value and isinstance(value, str) and len(value.strip()) > 0:
                # Bonus for longer descriptions
                if field == "description" and len(value) > 100:
                    score += weight * 1.2
                else:
                    score += weight

        # Normalize score
        return min(score / max_score, 1.0) if max_score > 0 else 0.0

    def normalize_character_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize complete character data dictionary.

        Args:
            data: Raw character data

        Returns:
            Normalized character data
        """
        normalized = {}

        # Normalize each field
        for key, value in data.items():
            normalized_key = self.normalize_field_name(key)
            normalized_value = self.normalize_field_value(normalized_key, value)

            if normalized_value is not None:
                normalized[normalized_key] = normalized_value

        # Apply post-processing
        normalized = self._post_process_character_data(normalized)

        return normalized

    def normalize_field_name(self, field_name: str) -> str:
        """
        Normalize field name to standard format.

        Args:
            field_name: Original field name

        Returns:
            Normalized field name
        """
        if not field_name:
            return field_name

        # Convert to lowercase and clean
        cleaned = field_name.lower().strip()
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)

        # Check for direct mapping
        if cleaned in self.field_mappings:
            return self.field_mappings[cleaned]

        # Check for partial matches
        for pattern, standard_name in self.field_mappings.items():
            if pattern in cleaned or cleaned in pattern:
                return standard_name

        # Convert to snake_case
        snake_case = re.sub(r"\s+", "_", cleaned)

        return snake_case

    def normalize_field_value(self, field_name: str, value: Any) -> Any:
        """
        Normalize field value based on field type.

        Args:
            field_name: Normalized field name
            value: Raw field value

        Returns:
            Normalized field value
        """
        if value is None:
            return None

        # Handle different field types
        if field_name in ["name", "anime_name"]:
            return self.normalize_text(value, preserve_case=True)

        elif field_name in ["description"]:
            return self.normalize_description(value)

        elif field_name in ["age"]:
            return self.normalize_age(value)

        elif field_name in ["gender"]:
            return self.normalize_gender(value)

        elif field_name in ["status"]:
            return self.normalize_status(value)

        elif field_name in ["bounty"]:
            return self.normalize_bounty(value)

        elif field_name in ["height"]:
            return self.normalize_height(value)

        elif field_name in ["epithet", "occupation"]:
            return self.normalize_text(value, preserve_case=True)

        elif isinstance(value, list):
            return self.normalize_list(value)

        elif isinstance(value, str):
            return self.normalize_text(value)

        else:
            return value

    def normalize_text(self, text: str, preserve_case: bool = False) -> Optional[str]:
        """
        Normalize text content.

        Args:
            text: Raw text
            preserve_case: Whether to preserve original case

        Returns:
            Normalized text or None if empty
        """
        if not text:
            return None

        # Convert to string if not already
        text = str(text)

        # Remove HTML tags
        text = self.text_patterns["html_tags"].sub("", text)

        # Clean quotes
        text = self.text_patterns["quotes"].sub('"', text)

        # Normalize whitespace
        text = self.text_patterns["extra_whitespace"].sub(" ", text)

        # Trim
        text = text.strip()

        # Apply case normalization if needed
        if not preserve_case:
            text = text.lower()

        return text if text else None

    def normalize_description(self, description: str) -> Optional[str]:
        """
        Normalize character description.

        Args:
            description: Raw description

        Returns:
            Normalized description
        """
        if not description:
            return None

        desc = self.normalize_text(description, preserve_case=True)

        if not desc:
            return None

        # Remove common prefixes
        prefixes_to_remove = [
            "is a character",
            "is a fictional character",
            "character from",
            "appears in",
        ]

        desc_lower = desc.lower()
        for prefix in prefixes_to_remove:
            if desc_lower.startswith(prefix):
                desc = desc[len(prefix) :].strip()
                break

        # Capitalize first letter
        if desc:
            desc = desc[0].upper() + desc[1:]

        return desc

    def normalize_age(self, age: str) -> Optional[str]:
        """
        Normalize age information.

        Args:
            age: Raw age string

        Returns:
            Normalized age string
        """
        if not age:
            return None

        age_str = str(age).strip().lower()

        # Remove common suffixes
        age_str = re.sub(r"\s*(years?\s*old|yrs?\.?|y\.?o\.?)\s*$", "", age_str)

        # Extract numbers and ranges
        age_match = re.search(r"(\d+(?:\s*-\s*\d+)?)", age_str)
        if age_match:
            return age_match.group(1).replace(" ", "")

        # Handle special cases
        if any(word in age_str for word in ["unknown", "n/a", "none", "?"]):
            return None

        if any(word in age_str for word in ["child", "kid", "young"]):
            return "child"

        if any(word in age_str for word in ["adult", "grown"]):
            return "adult"

        return age_str if age_str else None

    def normalize_gender(self, gender: str) -> Optional[str]:
        """
        Normalize gender information.

        Args:
            gender: Raw gender string

        Returns:
            Normalized gender
        """
        if not gender:
            return None

        gender_lower = str(gender).strip().lower()

        # Gender mappings
        gender_map = {
            "male": "male",
            "man": "male",
            "boy": "male",
            "m": "male",
            "female": "female",
            "woman": "female",
            "girl": "female",
            "f": "female",
            "unknown": None,
            "n/a": None,
            "none": None,
            "?": None,
        }

        return gender_map.get(gender_lower, gender_lower)

    def normalize_status(self, status: str) -> Optional[str]:
        """
        Normalize character status.

        Args:
            status: Raw status string

        Returns:
            Normalized status
        """
        if not status:
            return None

        status_lower = str(status).strip().lower()

        # Status mappings
        status_map = {
            "alive": "alive",
            "living": "alive",
            "active": "alive",
            "dead": "deceased",
            "deceased": "deceased",
            "killed": "deceased",
            "died": "deceased",
            "unknown": "unknown",
            "n/a": "unknown",
            "none": "unknown",
            "?": "unknown",
            "missing": "missing",
            "disappeared": "missing",
        }

        return status_map.get(status_lower, status_lower)

    def normalize_bounty(self, bounty: str) -> Optional[str]:
        """
        Normalize bounty information.

        Args:
            bounty: Raw bounty string

        Returns:
            Normalized bounty string
        """
        if not bounty:
            return None

        bounty_str = str(bounty).strip()

        # Remove currency symbols and common prefixes
        bounty_str = re.sub(
            r"^(bounty:?\s*|reward:?\s*)", "", bounty_str, flags=re.IGNORECASE
        )
        bounty_str = re.sub(r"[฿$,]", "", bounty_str)

        # Extract numbers
        number_match = re.search(r"(\d+(?:\.\d+)?)", bounty_str)
        if number_match:
            number = number_match.group(1)

            # Handle units
            if any(unit in bounty_str.lower() for unit in ["billion", "b"]):
                return f"{number} billion"
            elif any(unit in bounty_str.lower() for unit in ["million", "m"]):
                return f"{number} million"
            else:
                return number

        # Handle special cases
        if any(word in bounty_str.lower() for word in ["none", "n/a", "unknown", "0"]):
            return None

        return bounty_str

    def normalize_height(self, height: str) -> Optional[str]:
        """
        Normalize height information.

        Args:
            height: Raw height string

        Returns:
            Normalized height string
        """
        if not height:
            return None

        height_str = str(height).strip()

        # Extract height with units
        height_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(cm|m|ft|in|feet|inches)", height_str, re.IGNORECASE
        )
        if height_match:
            value = height_match.group(1)
            unit = height_match.group(2).lower()

            # Normalize units
            if unit in ["cm"]:
                return f"{value} cm"
            elif unit in ["m"]:
                return f"{value} m"
            elif unit in ["ft", "feet"]:
                return f"{value} ft"
            elif unit in ["in", "inches"]:
                return f"{value} in"

        return height_str

    def normalize_list(self, items: List[Any]) -> List[Any]:
        """
        Normalize list of items.

        Args:
            items: List of raw items

        Returns:
            List of normalized items
        """
        if not items:
            return []

        normalized_items = []
        for item in items:
            if isinstance(item, str):
                normalized_item = self.normalize_text(item, preserve_case=True)
                if normalized_item:
                    normalized_items.append(normalized_item)
            elif item is not None:
                normalized_items.append(item)

        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in normalized_items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)

        return unique_items

    def _post_process_character_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply post-processing to character data.

        Args:
            data: Normalized character data

        Returns:
            Post-processed character data
        """
        # Ensure required fields exist
        if "name" not in data or not data["name"]:
            data["name"] = "Unknown Character"

        if "anime_name" not in data or not data["anime_name"]:
            data["anime_name"] = "Unknown Anime"

        # Clean up empty lists
        list_fields = ["images", "relationships", "abilities", "appearances"]
        for field in list_fields:
            if field in data and not data[field]:
                data[field] = []

        # Ensure timestamps
        if "extraction_date" not in data:
            from datetime import datetime, timezone

            data["extraction_date"] = datetime.now(timezone.utc).isoformat()

        return data


# Global normalizer instance
_normalizer: Optional[DataNormalizer] = None


def get_normalizer() -> DataNormalizer:
    """
    Get or create the global data normalizer instance.

    Returns:
        Global DataNormalizer instance
    """
    global _normalizer

    if _normalizer is None:
        _normalizer = DataNormalizer()

    return _normalizer


# Convenience functions for common operations
def clean_text(text: str) -> str:
    """Clean text using the global normalizer."""
    return get_normalizer().clean_text(text)


def clean_character_name(name: str) -> str:
    """Clean character name using the global normalizer."""
    return get_normalizer().clean_character_name(name)


def normalize_age(age: str) -> str:
    """Normalize age using the global normalizer."""
    return get_normalizer().normalize_age(age)  # type: ignore


def normalize_gender(gender: str) -> str:
    """Normalize gender using the global normalizer."""
    return get_normalizer().normalize_gender(gender)  # type: ignore


def normalize_url(url: str, base_url: str = None) -> str:  # type: ignore
    """Normalize URL using the global normalizer."""
    return get_normalizer().normalize_url(url, base_url)


def validate_data_quality(character_data: Dict[str, Any]) -> float:
    """Validate data quality using the global normalizer."""
    return get_normalizer().validate_data_quality(character_data)
