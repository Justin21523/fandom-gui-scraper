# utils/data_processing/data_fusion.py
"""
Data fusion module for combining data from multiple sources.
Handles merging, conflict resolution, and data consistency.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime
from difflib import SequenceMatcher
import hashlib


class DataFusion:
    """
    Advanced data fusion engine for combining character data from multiple sources.

    Features:
    - Intelligent field merging with conflict resolution
    - Similarity-based duplicate detection
    - Source priority management
    - Data quality assessment
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data fusion engine.

        Args:
            config: Configuration dictionary with fusion parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "similarity_threshold": 0.85,
            "source_priorities": {
                "onepiece.fandom.com": 100,
                "fandom.com": 80,
                "manual_entry": 90,
                "api_data": 70,
            },
            "merge_strategies": {
                "name": "highest_priority",
                "description": "longest_content",
                "stats": "most_complete",
                "images": "merge_all",
                "categories": "merge_unique",
                "relationships": "merge_unique",
            },
            "required_fields": ["name", "source"],
            "confidence_weights": {
                "source_priority": 0.4,
                "data_completeness": 0.3,
                "freshness": 0.2,
                "quality_score": 0.1,
            },
        }

        if config:
            self.config.update(config)

    def fuse_character_data(
        self, character_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fuse multiple character records into a single unified record.

        Args:
            character_records: List of character data dictionaries

        Returns:
            Fused character record with metadata
        """
        if not character_records:
            return {}

        if len(character_records) == 1:
            return self._add_fusion_metadata(
                character_records[0], [character_records[0]]
            )

        self.logger.info(f"Fusing {len(character_records)} character records")

        # Sort records by priority and quality
        prioritized_records = self._prioritize_records(character_records)

        # Initialize fused record with highest priority base
        fused_record = dict(prioritized_records[0])
        fusion_sources = [prioritized_records[0]]

        # Merge remaining records
        for record in prioritized_records[1:]:
            if self._should_merge_records(fused_record, record):
                fused_record = self._merge_records(fused_record, record)
                fusion_sources.append(record)

        # Add fusion metadata
        fused_record = self._add_fusion_metadata(fused_record, fusion_sources)

        self.logger.info(f"Fusion complete: merged {len(fusion_sources)} sources")
        return fused_record

    def detect_duplicates(
        self,
        records: List[Dict[str, Any]],
        similarity_threshold: Optional[float] = None,
    ) -> List[List[int]]:
        """
        Detect duplicate records based on similarity analysis.

        Args:
            records: List of character records
            similarity_threshold: Minimum similarity for duplicate detection

        Returns:
            List of duplicate groups (each group contains record indices)
        """
        threshold = similarity_threshold or self.config["similarity_threshold"]
        duplicate_groups = []
        processed_indices = set()

        for i, record1 in enumerate(records):
            if i in processed_indices:
                continue

            current_group = [i]
            processed_indices.add(i)

            for j, record2 in enumerate(records[i + 1 :], i + 1):
                if j in processed_indices:
                    continue

                similarity = self._calculate_record_similarity(record1, record2)
                if similarity >= threshold:
                    current_group.append(j)
                    processed_indices.add(j)

            if len(current_group) > 1:
                duplicate_groups.append(current_group)

        self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def batch_fuse_characters(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple character records and fuse duplicates.

        Args:
            records: List of all character records

        Returns:
            List of fused character records (deduplicated)
        """
        if not records:
            return []

        self.logger.info(f"Starting batch fusion of {len(records)} records")

        # Detect duplicate groups
        duplicate_groups = self.detect_duplicates(records)

        # Track processed records
        processed_indices = set()
        fused_records = []

        # Process duplicate groups
        for group in duplicate_groups:
            group_records = [records[i] for i in group]
            fused_record = self.fuse_character_data(group_records)
            fused_records.append(fused_record)
            processed_indices.update(group)

        # Add remaining unique records
        for i, record in enumerate(records):
            if i not in processed_indices:
                unique_record = self._add_fusion_metadata(record, [record])
                fused_records.append(unique_record)

        self.logger.info(
            f"Batch fusion complete: {len(records)} -> {len(fused_records)} records"
        )
        return fused_records

    def _prioritize_records(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Sort records by priority and quality."""

        def priority_score(record):
            source = record.get("source", "").lower()
            source_priority = self.config["source_priorities"].get(source, 50)

            # Calculate completeness score
            total_fields = (
                len(self.config["required_fields"]) + 10
            )  # Estimated total important fields
            filled_fields = sum(
                1
                for field in self.config["required_fields"]
                if record.get(field) not in [None, "", []]
            )
            completeness = (filled_fields / total_fields) * 100

            # Calculate freshness score (if timestamp available)
            freshness = 100  # Default if no timestamp
            if "scraped_at" in record:
                try:
                    scraped_time = datetime.fromisoformat(
                        record["scraped_at"].replace("Z", "+00:00")
                    )
                    age_hours = (
                        datetime.now() - scraped_time.replace(tzinfo=None)
                    ).total_seconds() / 3600
                    freshness = max(0, 100 - (age_hours / 24))  # Decrease by time
                except:
                    pass

            return source_priority + completeness * 0.5 + freshness * 0.2

        return sorted(records, key=priority_score, reverse=True)

    def _should_merge_records(
        self, record1: Dict[str, Any], record2: Dict[str, Any]
    ) -> bool:
        """Determine if two records should be merged."""
        similarity = self._calculate_record_similarity(record1, record2)
        return similarity >= self.config["similarity_threshold"]

    def _calculate_record_similarity(
        self, record1: Dict[str, Any], record2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two character records."""
        # Name similarity (most important)
        name1 = str(record1.get("name", "")).lower().strip()
        name2 = str(record2.get("name", "")).lower().strip()

        if not name1 or not name2:
            return 0.0

        name_similarity = SequenceMatcher(None, name1, name2).ratio()

        # Alternative names similarity
        alt_names1 = self._extract_alternative_names(record1)
        alt_names2 = self._extract_alternative_names(record2)
        alt_similarity = self._calculate_name_list_similarity(alt_names1, alt_names2)

        # Description similarity (if available)
        desc1 = str(record1.get("description", "")).lower()
        desc2 = str(record2.get("description", "")).lower()
        desc_similarity = 0.0
        if desc1 and desc2 and len(desc1) > 50 and len(desc2) > 50:
            desc_similarity = SequenceMatcher(None, desc1[:200], desc2[:200]).ratio()

        # Weighted similarity calculation
        weights = {"name": 0.6, "alt_names": 0.3, "description": 0.1}
        total_similarity = (
            name_similarity * weights["name"]
            + alt_similarity * weights["alt_names"]
            + desc_similarity * weights["description"]
        )

        return total_similarity

    def _extract_alternative_names(self, record: Dict[str, Any]) -> List[str]:
        """Extract alternative names from record."""
        alt_names = []

        # Common alternative name fields
        alt_fields = [
            "alternative_names",
            "aliases",
            "aka",
            "other_names",
            "japanese_name",
        ]

        for field in alt_fields:
            value = record.get(field)
            if isinstance(value, list):
                alt_names.extend([str(name).lower().strip() for name in value])
            elif isinstance(value, str) and value:
                alt_names.append(value.lower().strip())

        return list(set(alt_names))  # Remove duplicates

    def _calculate_name_list_similarity(
        self, names1: List[str], names2: List[str]
    ) -> float:
        """Calculate similarity between two lists of names."""
        if not names1 or not names2:
            return 0.0

        max_similarity = 0.0
        for name1 in names1:
            for name2 in names2:
                similarity = SequenceMatcher(None, name1, name2).ratio()
                max_similarity = max(max_similarity, similarity)

        return max_similarity

    def _merge_records(
        self, record1: Dict[str, Any], record2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two character records using configured strategies."""
        merged = dict(record1)

        for field, strategy in self.config["merge_strategies"].items():
            if field in record2:
                merged[field] = self._merge_field(
                    merged.get(field),
                    record2[field],
                    strategy,
                    record1.get("source"),
                    record2.get("source"),
                )

        # Merge any remaining fields not in strategies
        for field, value in record2.items():
            if field not in merged and value is not None:
                merged[field] = value

        return merged

    def _merge_field(
        self,
        value1: Any,
        value2: Any,
        strategy: str,
        source1: str = None,
        source2: str = None,
    ) -> Any:
        """Merge two field values using the specified strategy."""

        if strategy == "highest_priority":
            # Choose value from higher priority source
            priority1 = self.config["source_priorities"].get(source1, 50)
            priority2 = self.config["source_priorities"].get(source2, 50)
            return value1 if priority1 >= priority2 else value2

        elif strategy == "longest_content":
            # Choose longer content
            len1 = len(str(value1)) if value1 else 0
            len2 = len(str(value2)) if value2 else 0
            return value1 if len1 >= len2 else value2

        elif strategy == "most_complete":
            # Choose more complete data structure
            if isinstance(value1, dict) and isinstance(value2, dict):
                # Merge dictionaries, preferring non-null values
                merged = dict(value1)
                for k, v in value2.items():
                    if k not in merged or merged[k] is None:
                        merged[k] = v
                return merged
            else:
                return value2 if value1 is None else value1

        elif strategy == "merge_all":
            # Merge lists/arrays
            if isinstance(value1, list) and isinstance(value2, list):
                return list(set(value1 + value2))  # Remove duplicates
            elif isinstance(value1, list):
                return value1 + [value2] if value2 not in value1 else value1
            elif isinstance(value2, list):
                return [value1] + value2 if value1 not in value2 else value2
            else:
                return [value1, value2]

        elif strategy == "merge_unique":
            # Merge unique values only
            if isinstance(value1, list) and isinstance(value2, list):
                return list(set(value1 + value2))
            elif isinstance(value1, list):
                return value1 + [value2] if value2 not in value1 else value1
            elif isinstance(value2, list):
                return [value1] + value2 if value1 not in value2 else value2
            else:
                return value1 if value1 == value2 else [value1, value2]

        # Default: prefer non-null value
        return value2 if value1 is None else value1

    def _add_fusion_metadata(
        self, record: Dict[str, Any], source_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add metadata about the fusion process."""

        metadata = {
            "fusion_id": self._generate_fusion_id(record),
            "fused_at": datetime.now().isoformat(),
            "source_count": len(source_records),
            "confidence_score": self._calculate_confidence_score(
                record, source_records
            ),
            "fusion_sources": [
                {
                    "source": src.get("source", "unknown"),
                    "scraped_at": src.get("scraped_at"),
                    "url": src.get("url"),
                }
                for src in source_records
            ],
        }

        # Add to record without overwriting existing data
        result = dict(record)
        result["_fusion_metadata"] = metadata

        return result

    def _generate_fusion_id(self, record: Dict[str, Any]) -> str:
        """Generate unique fusion ID for the record."""
        name = str(record.get("name", ""))
        source = str(record.get("source", ""))
        content = f"{name}:{source}:{datetime.now().date()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _calculate_confidence_score(
        self, record: Dict[str, Any], source_records: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for the fused record."""

        weights = self.config["confidence_weights"]

        # Source priority score
        sources = [src.get("source", "") for src in source_records]
        max_source_priority = max(
            self.config["source_priorities"].get(src, 50) for src in sources
        )
        source_score = max_source_priority / 100

        # Data completeness score
        required_fields = self.config["required_fields"]
        filled_count = sum(
            1 for field in required_fields if record.get(field) not in [None, "", []]
        )
        completeness_score = filled_count / len(required_fields)

        # Freshness score
        freshness_score = 1.0  # Default
        if source_records and source_records[0].get("scraped_at"):
            try:
                scraped_time = datetime.fromisoformat(
                    source_records[0]["scraped_at"].replace("Z", "+00:00")
                )
                age_hours = (
                    datetime.now() - scraped_time.replace(tzinfo=None)
                ).total_seconds() / 3600
                freshness_score = max(
                    0, 1 - (age_hours / (24 * 7))
                )  # Decay over a week
            except:
                pass

        # Quality score (based on data richness)
        total_fields = len(record)
        filled_fields = sum(1 for v in record.values() if v not in [None, "", []])
        quality_score = filled_fields / max(total_fields, 1)

        # Weighted final score
        confidence = (
            source_score * weights["source_priority"]
            + completeness_score * weights["data_completeness"]
            + freshness_score * weights["freshness"]
            + quality_score * weights["quality_score"]
        )

        return round(confidence, 3)


def create_default_fusion_config() -> Dict[str, Any]:
    """Create default configuration for data fusion."""
    return {
        "similarity_threshold": 0.85,
        "source_priorities": {
            "onepiece.fandom.com": 100,
            "naruto.fandom.com": 95,
            "fandom.com": 80,
            "manual_entry": 90,
            "api_data": 70,
            "user_input": 60,
        },
        "merge_strategies": {
            "name": "highest_priority",
            "description": "longest_content",
            "stats": "most_complete",
            "images": "merge_all",
            "categories": "merge_unique",
            "relationships": "merge_unique",
            "abilities": "merge_unique",
        },
        "required_fields": ["name", "source"],
        "confidence_weights": {
            "source_priority": 0.4,
            "data_completeness": 0.3,
            "freshness": 0.2,
            "quality_score": 0.1,
        },
    }
