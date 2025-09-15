# utils/data_processing/text_processor.py
"""
Text processing utilities for character data.
Provides text cleaning, normalization, and extraction capabilities.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter
import unicodedata
import html


class TextProcessor:
    """
    Comprehensive text processing engine for character data.

    Features:
    - Text cleaning and normalization
    - Entity extraction (names, places, abilities)
    - Language detection and processing
    - Content summarization
    - Keyword extraction
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize text processor.

        Args:
            config: Configuration dictionary with processing parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "normalization": {
                "lowercase": False,
                "remove_html": True,
                "remove_extra_whitespace": True,
                "normalize_unicode": True,
                "remove_special_chars": False,
                "preserve_line_breaks": True,
            },
            "extraction": {
                "min_keyword_length": 3,
                "max_keywords": 20,
                "min_entity_length": 2,
                "stop_words": [
                    "the",
                    "and",
                    "or",
                    "but",
                    "in",
                    "on",
                    "at",
                    "to",
                    "for",
                    "of",
                    "with",
                    "by",
                    "is",
                    "are",
                    "was",
                    "were",
                    "be",
                    "been",
                    "have",
                    "has",
                    "had",
                    "do",
                    "does",
                    "did",
                    "will",
                    "would",
                    "could",
                    "should",
                    "may",
                    "might",
                    "can",
                    "must",
                    "shall",
                    "this",
                    "that",
                    "these",
                    "those",
                    "a",
                    "an",
                    "as",
                    "if",
                    "so",
                    "no",
                    "not",
                    "only",
                    "own",
                    "same",
                    "such",
                    "than",
                    "too",
                    "very",
                    "just",
                    "now",
                    "also",
                    "any",
                    "some",
                    "all",
                ],
            },
            "patterns": {
                "honorifics": [
                    r"\b(mr|mrs|ms|miss|dr|prof|sir|madam|lord|lady)\b\.?",
                    r"\b(sama|san|kun|chan|sensei|senpai)\b",
                ],
                "titles": [
                    r"\b(captain|admiral|general|colonel|major|king|queen|prince|princess)\b",
                    r"\b(emperor|empress|duke|duchess|count|countess)\b",
                ],
                "abilities": [
                    r"\b(devil fruit|haki|chakra|jutsu|technique|power|ability)\b",
                    r"\b(skill|magic|spell|curse|blessing)\b",
                ],
            },
        }

        if config:
            self.config.update(config)

        # Compile regex patterns
        self._compile_patterns()

    def clean_text(
        self, text: str, custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Input text to clean
            custom_config: Optional custom configuration for this operation

        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""

        config = self.config["normalization"].copy()
        if custom_config:
            config.update(custom_config)

        cleaned = text

        # Remove HTML tags and entities
        if config.get("remove_html", True):
            cleaned = self._remove_html(cleaned)

        # Normalize Unicode characters
        if config.get("normalize_unicode", True):
            cleaned = self._normalize_unicode(cleaned)

        # Remove extra whitespace
        if config.get("remove_extra_whitespace", True):
            cleaned = self._normalize_whitespace(
                cleaned, config.get("preserve_line_breaks", True)
            )

        # Remove special characters
        if config.get("remove_special_chars", False):
            cleaned = self._remove_special_characters(cleaned)

        # Convert to lowercase
        if config.get("lowercase", False):
            cleaned = cleaned.lower()

        return cleaned.strip()

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract various entities from text.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary of extracted entities by category
        """
        if not text:
            return {"names": [], "places": [], "abilities": [], "titles": []}

        entities = {
            "names": self._extract_names(text),
            "places": self._extract_places(text),
            "abilities": self._extract_abilities(text),
            "titles": self._extract_titles(text),
            "organizations": self._extract_organizations(text),
        }

        return entities

    def extract_keywords(
        self, text: str, max_keywords: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract important keywords from text with frequency and importance scores.

        Args:
            text: Input text to analyze
            max_keywords: Maximum number of keywords to return

        Returns:
            List of keyword dictionaries with scores
        """
        if not text:
            return []

        max_kw = max_keywords or self.config["extraction"]["max_keywords"]

        # Clean text for keyword extraction
        cleaned_text = self.clean_text(
            text, {"lowercase": True, "remove_special_chars": True}
        )

        # Tokenize into words
        words = re.findall(r"\b\w+\b", cleaned_text)

        # Filter words
        filtered_words = []
        stop_words = set(self.config["extraction"]["stop_words"])
        min_length = self.config["extraction"]["min_keyword_length"]

        for word in words:
            if (
                len(word) >= min_length
                and word.lower() not in stop_words
                and not word.isdigit()
            ):
                filtered_words.append(word.lower())

        # Count word frequencies
        word_counts = Counter(filtered_words)

        # Calculate TF scores (simple term frequency)
        total_words = len(filtered_words)
        keywords = []

        for word, count in word_counts.most_common(max_kw):
            tf_score = count / total_words

            # Calculate importance score (considering position, length, etc.)
            importance = self._calculate_word_importance(word, text, count)

            keywords.append(
                {
                    "word": word,
                    "frequency": count,
                    "tf_score": tf_score,
                    "importance": importance,
                    "combined_score": (tf_score + importance) / 2,
                }
            )

        # Sort by combined score
        keywords.sort(key=lambda x: x["combined_score"], reverse=True)

        return keywords[:max_kw]

    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """
        Create a summary of the input text.

        Args:
            text: Input text to summarize
            max_sentences: Maximum number of sentences in summary

        Returns:
            Text summary
        """
        if not text:
            return ""

        # Split into sentences
        sentences = self._split_sentences(text)

        if len(sentences) <= max_sentences:
            return text

        # Score sentences by importance
        sentence_scores = []
        keywords = self.extract_keywords(text, max_keywords=10)
        important_words = set(kw["word"] for kw in keywords)

        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, important_words, i, len(sentences))
            sentence_scores.append((score, sentence))

        # Select top sentences
        sentence_scores.sort(reverse=True)
        selected_sentences = [sent for score, sent in sentence_scores[:max_sentences]]

        # Reorder by original position
        original_order = []
        for selected in selected_sentences:
            original_order.append((sentences.index(selected), selected))

        original_order.sort()
        summary_sentences = [sent for pos, sent in original_order]

        return " ".join(summary_sentences)

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the text (simplified implementation).

        Args:
            text: Input text to analyze

        Returns:
            Language detection results
        """
        if not text:
            return {"language": "unknown", "confidence": 0.0}

        # Simple heuristic-based language detection
        # In practice, you might use a library like langdetect

        # Japanese characters
        japanese_chars = len(
            re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
        )

        # Chinese characters (simplified heuristic)
        chinese_chars = len(re.findall(r"[\u4E00-\u9FFF]", text))

        # Korean characters
        korean_chars = len(re.findall(r"[\uAC00-\uD7AF]", text))

        # English/Latin characters
        latin_chars = len(re.findall(r"[A-Za-z]", text))

        total_chars = len(text)

        if total_chars == 0:
            return {"language": "unknown", "confidence": 0.0}

        # Calculate ratios
        japanese_ratio = japanese_chars / total_chars
        chinese_ratio = chinese_chars / total_chars
        korean_ratio = korean_chars / total_chars
        latin_ratio = latin_chars / total_chars

        # Determine language
        if japanese_ratio > 0.3:
            return {"language": "japanese", "confidence": min(japanese_ratio * 2, 1.0)}
        elif chinese_ratio > 0.3:
            return {"language": "chinese", "confidence": min(chinese_ratio * 2, 1.0)}
        elif korean_ratio > 0.3:
            return {"language": "korean", "confidence": min(korean_ratio * 2, 1.0)}
        elif latin_ratio > 0.7:
            return {"language": "english", "confidence": min(latin_ratio, 1.0)}
        else:
            return {"language": "mixed", "confidence": 0.5}

    def extract_character_info(self, text: str) -> Dict[str, Any]:
        """
        Extract character-specific information from text.

        Args:
            text: Character description text

        Returns:
            Extracted character information
        """
        if not text:
            return {}

        info = {
            "physical_traits": self._extract_physical_traits(text),
            "personality_traits": self._extract_personality_traits(text),
            "abilities": self._extract_abilities(text),
            "affiliations": self._extract_organizations(text),
            "relationships": self._extract_relationships(text),
            "locations": self._extract_places(text),
        }

        return {k: v for k, v in info.items() if v}  # Remove empty lists

    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        self.compiled_patterns = {}

        for category, patterns in self.config["patterns"].items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def _remove_html(self, text: str) -> str:
        """Remove HTML tags and decode HTML entities."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = html.unescape(text)

        return text

    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters."""
        # Normalize to NFC form (canonical composition)
        normalized = unicodedata.normalize("NFC", text)

        # Remove or replace problematic characters
        # Remove zero-width characters
        normalized = re.sub(r"[\u200B-\u200D\uFEFF]", "", normalized)

        return normalized

    def _normalize_whitespace(
        self, text: str, preserve_line_breaks: bool = True
    ) -> str:
        """Normalize whitespace in text."""
        if preserve_line_breaks:
            # Replace multiple spaces with single space, preserve line breaks
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n\s*\n", "\n\n", text)  # Normalize multiple line breaks
        else:
            # Replace all whitespace with single space
            text = re.sub(r"\s+", " ", text)

        return text

    def _remove_special_characters(self, text: str) -> str:
        """Remove special characters while preserving essential punctuation."""
        # Keep letters, numbers, basic punctuation, and whitespace
        cleaned = re.sub(r'[^\w\s.,;:!?()"\'-]', "", text)
        return cleaned

    def _extract_names(self, text: str) -> List[str]:
        """Extract potential character names from text."""
        names = []

        # Pattern for capitalized words (potential names)
        name_pattern = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")
        potential_names = name_pattern.findall(text)

        # Filter out common words that aren't names
        common_words = {
            "The",
            "This",
            "That",
            "These",
            "Those",
            "When",
            "Where",
            "What",
            "Who",
            "Why",
            "How",
            "After",
            "Before",
            "During",
            "Devil",
            "Fruit",
            "One",
            "Piece",
            "World",
            "Island",
            "Ocean",
            "Sea",
            "Marine",
            "Pirates",
        }

        for name in potential_names:
            if (
                name not in common_words
                and len(name) >= self.config["extraction"]["min_entity_length"]
                and not self._is_common_word(name)
            ):
                names.append(name)

        return list(set(names))  # Remove duplicates

    def _extract_places(self, text: str) -> List[str]:
        """Extract location names from text."""
        places = []

        # Common place indicators
        place_indicators = [
            r"\b(\w+)\s+(Island|Town|City|Village|Kingdom|Country|Sea|Ocean)\b",
            r"\b(East|West|North|South|Grand|New)\s+(\w+)\b",
            r"\b(\w+)\s+(Base|Headquarters|Prison|Palace|Castle)\b",
        ]

        for pattern in place_indicators:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                place = match.group().strip()
                if len(place) >= 3:
                    places.append(place)

        return list(set(places))

    def _extract_abilities(self, text: str) -> List[str]:
        """Extract abilities and powers from text."""
        abilities = []

        # Use compiled patterns
        for pattern in self.compiled_patterns.get("abilities", []):
            matches = pattern.findall(text)
            abilities.extend(matches)

        # Extract quoted abilities (often in quotes)
        quoted_abilities = re.findall(
            r'"([^"]*(?:technique|jutsu|ability|power)[^"]*)"', text, re.IGNORECASE
        )
        abilities.extend(quoted_abilities)

        # Extract capitalized ability names
        ability_pattern = re.compile(
            r"\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:Technique|Jutsu|Style|Form|Mode)\b"
        )
        cap_abilities = ability_pattern.findall(text)
        abilities.extend(cap_abilities)

        return list(set(abilities))

    def _extract_titles(self, text: str) -> List[str]:
        """Extract titles and ranks from text."""
        titles = []

        # Use compiled patterns
        for pattern in self.compiled_patterns.get("titles", []):
            matches = pattern.findall(text)
            titles.extend(matches)

        return list(set(titles))

    def _extract_organizations(self, text: str) -> List[str]:
        """Extract organization and group names."""
        organizations = []

        # Common organization patterns
        org_patterns = [
            r"\b(\w+)\s+(Pirates|Marines|Navy|Crew|Gang|Organization|Guild|Alliance)\b",
            r"\b(Straw\s+Hat|Whitebeard|Red\s+Hair|Big\s+Mom|Beast)\s+Pirates\b",
            r"\b(\w+)\s+(Government|Administration|Bureau|Department)\b",
        ]

        for pattern in org_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                org = match.group().strip()
                if len(org) >= 3:
                    organizations.append(org)

        return list(set(organizations))

    def _extract_physical_traits(self, text: str) -> List[str]:
        """Extract physical traits and appearance details."""
        traits = []

        # Physical trait patterns
        trait_patterns = [
            r"\b(tall|short|large|small|big|tiny|huge|massive)\b",
            r"\b(hair|eyes?|skin)\s+(?:is|are)?\s*(\w+)\b",
            r"\b(\w+)\s+(?:hair|eyes?|skin)\b",
            r"\b(muscular|slim|fat|thin|athletic|strong|weak)\b",
            r"\b(scar|tattoo|mark|wound)\b",
        ]

        for pattern in trait_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                trait = match.group().strip()
                if len(trait) >= 3:
                    traits.append(trait)

        return list(set(traits))

    def _extract_personality_traits(self, text: str) -> List[str]:
        """Extract personality traits and characteristics."""
        traits = []

        # Personality trait patterns
        trait_patterns = [
            r"\b(brave|cowardly|kind|cruel|smart|stupid|wise|foolish)\b",
            r"\b(friendly|hostile|calm|angry|happy|sad|cheerful|gloomy)\b",
            r"\b(loyal|treacherous|honest|deceitful|noble|evil|good|bad)\b",
            r"\b(confident|shy|outgoing|introverted|serious|playful)\b",
        ]

        for pattern in trait_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                trait = match.group().strip()
                if len(trait) >= 3:
                    traits.append(trait)

        return list(set(traits))

    def _extract_relationships(self, text: str) -> List[str]:
        """Extract relationship information."""
        relationships = []

        # Relationship patterns
        rel_patterns = [
            r"\b(son|daughter|father|mother|brother|sister|friend|enemy)\s+(?:of|to)\s+(\w+)\b",
            r"\b(\w+)(?:\'s)?\s+(captain|crew|member|ally|rival|enemy)\b",
            r"\b(married|engaged|dating|related)\s+to\s+(\w+)\b",
        ]

        for pattern in rel_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                rel = match.group().strip()
                if len(rel) >= 3:
                    relationships.append(rel)

        return list(set(relationships))

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r"[.!?]+", text)

        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum sentence length
                cleaned_sentences.append(sentence)

        return cleaned_sentences

    def _score_sentence(
        self,
        sentence: str,
        important_words: Set[str],
        position: int,
        total_sentences: int,
    ) -> float:
        """Score a sentence for importance in summarization."""
        score = 0.0

        # Word importance score
        words = re.findall(r"\b\w+\b", sentence.lower())
        word_score = sum(1 for word in words if word in important_words)
        score += word_score / len(words) if words else 0

        # Position score (first and last sentences often important)
        if position == 0:
            score += 0.3  # First sentence bonus
        elif position == total_sentences - 1:
            score += 0.2  # Last sentence bonus

        # Length score (moderate length preferred)
        word_count = len(words)
        if 10 <= word_count <= 30:
            score += 0.1

        return score

    def _calculate_word_importance(self, word: str, text: str, frequency: int) -> float:
        """Calculate importance score for a word."""
        importance = 0.0

        # Length bonus (longer words often more important)
        if len(word) >= 6:
            importance += 0.2
        elif len(word) >= 4:
            importance += 0.1

        # Capitalization in original text (proper nouns)
        capitalized_count = len(re.findall(rf"\b{re.escape(word.title())}\b", text))
        if capitalized_count > 0:
            importance += 0.3

        # Position in text (words appearing early might be more important)
        first_occurrence = text.lower().find(word.lower())
        if first_occurrence != -1:
            position_ratio = first_occurrence / len(text)
            if position_ratio < 0.2:  # Appears in first 20%
                importance += 0.2

        # Frequency normalization
        if frequency > 1:
            importance += min(0.3, frequency * 0.1)

        return min(importance, 1.0)  # Cap at 1.0

    def _is_common_word(self, word: str) -> bool:
        """Check if word is a common word that shouldn't be considered a name."""
        common_words = {
            "devil",
            "fruit",
            "power",
            "ability",
            "technique",
            "style",
            "form",
            "island",
            "ocean",
            "sea",
            "world",
            "marine",
            "pirate",
            "crew",
            "captain",
            "admiral",
            "king",
            "queen",
            "prince",
            "princess",
        }
        return word.lower() in common_words


def create_text_processor_config() -> Dict[str, Any]:
    """Create default configuration for text processor."""
    return {
        "normalization": {
            "lowercase": False,
            "remove_html": True,
            "remove_extra_whitespace": True,
            "normalize_unicode": True,
            "remove_special_chars": False,
            "preserve_line_breaks": True,
        },
        "extraction": {
            "min_keyword_length": 3,
            "max_keywords": 20,
            "min_entity_length": 2,
            "stop_words": [
                "the",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "can",
                "must",
                "shall",
                "this",
                "that",
                "these",
                "those",
                "a",
                "an",
                "as",
                "if",
                "so",
                "no",
                "not",
                "only",
                "own",
                "same",
                "such",
                "than",
                "too",
                "very",
                "just",
                "now",
                "also",
                "any",
                "some",
                "all",
            ],
        },
        "patterns": {
            "honorifics": [
                r"\b(mr|mrs|ms|miss|dr|prof|sir|madam|lord|lady)\b\.?",
                r"\b(sama|san|kun|chan|sensei|senpai)\b",
            ],
            "titles": [
                r"\b(captain|admiral|general|colonel|major|king|queen|prince|princess)\b",
                r"\b(emperor|empress|duke|duchess|count|countess)\b",
            ],
            "abilities": [
                r"\b(devil fruit|haki|chakra|jutsu|technique|power|ability)\b",
                r"\b(skill|magic|spell|curse|blessing)\b",
            ],
        },
    }
