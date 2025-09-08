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
        self.citation_pattern = re.compile(r"\[[\d\w\s,]+\]")
        self.extra_whitespace_pattern = re.compile(r"\s+")
        self.parentheses_pattern = re.compile(r"\(\s*\)")
        self.brackets_pattern = re.compile(r"\[\s*\]")
        self.wiki_markup_pattern = re.compile(r"\{\{[^}]*\}\}")
        self.html_tag_pattern = re.compile(r"<[^>]+>")

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

    def normalize_age(self, age: str) -> str:
        """
        Normalize age information to consistent format.

        Args:
            age: Age string to normalize

        Returns:
            Normalized age string
        """
        if not age:
            return "Unknown"

        cleaned = self.clean_text(age)

        # Handle special cases
        special_ages = {
            "unknown": "Unknown",
            "immortal": "Immortal",
            "ageless": "Ageless",
            "deceased": "Deceased",
            "varies": "Varies",
        }

        cleaned_lower = cleaned.lower()
        for key, value in special_ages.items():
            if key in cleaned_lower:
                return value

        # Extract age ranges
        range_match = self.age_range_pattern.search(cleaned)
        if range_match:
            start_age, end_age = range_match.groups()
            return f"{start_age}-{end_age}"

        # Extract single age number
        number_match = self.age_number_pattern.search(cleaned)
        if number_match:
            return number_match.group(1)

        return "Unknown"

    def normalize_gender(self, gender: str) -> str:
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
    return get_normalizer().normalize_age(age)


def normalize_gender(gender: str) -> str:
    """Normalize gender using the global normalizer."""
    return get_normalizer().normalize_gender(gender)


def normalize_url(url: str, base_url: str = None) -> str:  # type: ignore
    """Normalize URL using the global normalizer."""
    return get_normalizer().normalize_url(url, base_url)


def validate_data_quality(character_data: Dict[str, Any]) -> float:
    """Validate data quality using the global normalizer."""
    return get_normalizer().validate_data_quality(character_data)
