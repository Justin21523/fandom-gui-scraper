# utils/data_processing/deduplication.py
"""
Advanced deduplication module for character data.
Provides multiple algorithms and strategies for duplicate detection and removal.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
import hashlib
import re
from difflib import SequenceMatcher
from datetime import datetime


class DeduplicationEngine:
    """
    Advanced deduplication engine with multiple detection strategies.

    Features:
    - Hash-based exact duplicate detection
    - Fuzzy similarity-based detection
    - Multi-field comparison algorithms
    - Configurable similarity thresholds
    - Conflict resolution strategies
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize deduplication engine.

        Args:
            config: Configuration dictionary with deduplication parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            'similarity_threshold': 0.85,
            'name_threshold': 0.9,
            'description_threshold': 0.7,
            'strict_mode': False,
            'field_weights': {
                'name': 0.5,
                'alternative_names': 0.2,
                'description': 0.15,
                'source': 0.1,
                'categories': 0.05
            },
            'normalization': {
                'lowercase': True,
                'remove_punctuation': True,
                'remove_extra_spaces': True,
                'remove_honorifics': True
            },
            'exclusion_patterns': [
                r'^\s*$',  # Empty strings
                r'^unknown$',
                r'^n/a$',
                r'^tbd$'
            ]
        }

        if config:
            self.config.update(config)

        # Compile exclusion patterns
        self.exclusion_regex = [re.compile(pattern, re.IGNORECASE)
                               for pattern in self.config['exclusion_patterns']]

    def find_duplicates(self, records: List[Dict[str, Any]],
                       algorithm: str = 'hybrid') -> Dict[str, Any]:
        """
        Find duplicate records using specified algorithm.

        Args:
            records: List of character records to check
            algorithm: Detection algorithm ('exact', 'fuzzy', 'hybrid', 'advanced')

        Returns:
            Dictionary containing duplicate groups and statistics
        """
        if not records:
            return {'duplicate_groups': [], 'statistics': self._create_empty_stats()}

        self.logger.info(f"Starting duplicate detection with {algorithm} algorithm on {len(records)} records")

        start_time = datetime.now()

        if algorithm == 'exact':
            duplicate_groups = self._exact_duplicate_detection(records)
        elif algorithm == 'fuzzy':
            duplicate_groups = self._fuzzy_duplicate_detection(records)
        elif algorithm == 'hybrid':
            duplicate_groups = self._hybrid_duplicate_detection(records)
        elif algorithm == 'advanced':
            duplicate_groups = self._advanced_duplicate_detection(records)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Calculate statistics
        statistics = self._calculate_statistics(records, duplicate_groups, processing_time)

        self.logger.info(f"Duplicate detection complete: found {len(duplicate_groups)} duplicate groups "
                        f"in {processing_time:.2f} seconds")

        return {
            'duplicate_groups': duplicate_groups,
            'statistics': statistics,
            'algorithm_used': algorithm,
            'config': self.config.copy()
        }

    def remove_duplicates(self, records: List[Dict[str, Any]],
                         strategy: str = 'keep_best') -> List[Dict[str, Any]]:
        """
        Remove duplicates from records using specified strategy.

        Args:
            records: List of character records
            strategy: Removal strategy ('keep_first', 'keep_last', 'keep_best', 'merge')

        Returns:
            Deduplicated list of records
        """
        duplicate_result = self.find_duplicates(records)
        duplicate_groups = duplicate_result['duplicate_groups']

        if not duplicate_groups:
            return records

        self.logger.info(f"Removing duplicates using {strategy} strategy")

        # Track indices to remove
        indices_to_remove = set()
        merged_records = []

        for group in duplicate_groups:
            indices = group['indices']
            group_records = [records[i] for i in indices]

            if strategy == 'keep_first':
                # Keep the first record, mark others for removal
                indices_to_remove.update(indices[1:])

            elif strategy == 'keep_last':
                # Keep the last record, mark others for removal
                indices_to_remove.update(indices[:-1])

            elif strategy == 'keep_best':
                # Keep the best quality record
                best_record, best_index = self._select_best_record(group_records, indices)
                remaining_indices = [i for i in indices if i != best_index]
                indices_to_remove.update(remaining_indices)

            elif strategy == 'merge':
                # Merge all records in the group
                merged_record = self._merge_duplicate_records(group_records)
                merged_records.append((min(indices), merged_record))  # Use first index for position
                indices_to_remove.update(indices)

        # Build result list
        result = []

        for i, record in enumerate(records):
            if i not in indices_to_remove:
                result.append(record)

        # Add merged records if using merge strategy
        if strategy == 'merge':
            for position, merged_record in sorted(merged_records):
                result.insert(position, merged_record)

        self.logger.info(f"Deduplication complete: {len(records)} -> {len(result)} records")
        return result

    def _exact_duplicate_detection(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect exact duplicates using hash comparison."""
        hash_groups = defaultdict(list)

        for i, record in enumerate(records):
            record_hash = self._calculate_record_hash(record)
            hash_groups[record_hash].append(i)

        duplicate_groups = []
        for record_hash, indices in hash_groups.items():
            if len(indices) > 1:
                duplicate_groups.append({
                    'type': 'exact',
                    'hash': record_hash,
                    'indices': indices,
                    'count': len(indices),
                    'similarity': 1.0
                })

        return duplicate_groups

    def _fuzzy_duplicate_detection(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect fuzzy duplicates using similarity comparison."""
        duplicate_groups = []
        processed_indices = set()

        for i, record1 in enumerate(records):
            if i in processed_indices:
                continue

            current_group = [i]
            processed_indices.add(i)

            for j, record2 in enumerate(records[i+1:], i+1):
                if j in processed_indices:
                    continue

                similarity = self._calculate_similarity(record1, record2)
                if similarity >= self.config['similarity_threshold']:
                    current_group.append(j)
                    processed_indices.add(j)

            if len(current_group) > 1:
                # Calculate average similarity for the group
                avg_similarity = self._calculate_group_similarity(
                    [records[idx] for idx in current_group]
                )

                duplicate_groups.append({
                    'type': 'fuzzy',
                    'indices': current_group,
                    'count': len(current_group),
                    'similarity': avg_similarity
                })

        return duplicate_groups

    def _hybrid_duplicate_detection(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine exact and fuzzy detection methods."""
        # First find exact duplicates
        exact_groups = self._exact_duplicate_detection(records)
        exact_indices = set()
        for group in exact_groups:
            exact_indices.update(group['indices'])

        # Then find fuzzy duplicates among remaining records
        remaining_records = [record for i, record in enumerate(records)
                           if i not in exact_indices]
        remaining_indices = [i for i in range(len(records))
                           if i not in exact_indices]

        fuzzy_groups = []
        if remaining_records:
            temp_fuzzy_groups = self._fuzzy_duplicate_detection(remaining_records)

            # Map back to original indices
            for group in temp_fuzzy_groups:
                original_indices = [remaining_indices[i] for i in group['indices']]
                fuzzy_groups.append({
                    'type': 'fuzzy',
                    'indices': original_indices,
                    'count': len(original_indices),
                    'similarity': group['similarity']
                })

        return exact_groups + fuzzy_groups

    def _advanced_duplicate_detection(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Advanced detection using multiple similarity metrics and clustering."""
        # Use hybrid detection as base
        duplicate_groups = self._hybrid_duplicate_detection(records)

        # Enhance with advanced analysis
        enhanced_groups = []

        for group in duplicate_groups:
            group_records = [records[i] for i in group['indices']]

            # Perform advanced analysis on the group
            enhanced_group = self._enhance_duplicate_group(group, group_records)
            enhanced_groups.append(enhanced_group)

        # Look for cross-group potential merges
        merged_groups = self._merge_similar_groups(enhanced_groups, records)

        return merged_groups

    def _calculate_record_hash(self, record: Dict[str, Any]) -> str:
        """Calculate hash for exact duplicate detection."""
        # Extract key fields for hashing
        key_fields = ['name', 'source', 'url']

        # Normalize values
        hash_data = []
        for field in key_fields:
            value = record.get(field, '')
            if value:
                normalized = self._normalize_text(str(value))
                hash_data.append(f"{field}:{normalized}")

        # Include description snippet if available
        description = record.get('description', '')
        if description and len(description) > 50:
            desc_snippet = self._normalize_text(description[:100])
            hash_data.append(f"desc:{desc_snippet}")

        hash_string = '|'.join(sorted(hash_data))
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _calculate_similarity(self, record1: Dict[str, Any], record2: Dict[str, Any]) -> float:
        """Calculate overall similarity between two records."""
        similarities = {}
        weights = self.config['field_weights']

        # Name similarity
        name1 = self._normalize_text(str(record1.get('name', '')))
        name2 = self._normalize_text(str(record2.get('name', '')))

        if name1 and name2:
            similarities['name'] = SequenceMatcher(None, name1, name2).ratio()
        else:
            similarities['name'] = 0.0

        # Alternative names similarity
        alt_names1 = self._extract_alternative_names(record1)
        alt_names2 = self._extract_alternative_names(record2)
        similarities['alternative_names'] = self._calculate_name_list_similarity(alt_names1, alt_names2)

        # Description similarity
        desc1 = self._normalize_text(str(record1.get('description', '')))
        desc2 = self._normalize_text(str(record2.get('description', '')))

        if desc1 and desc2 and len(desc1) > 20 and len(desc2) > 20:
            # Use first 200 characters for comparison
            similarities['description'] = SequenceMatcher(None, desc1[:200], desc2[:200]).ratio()
        else:
            similarities['description'] = 0.0

        # Source similarity
        source1 = str(record1.get('source', '')).lower()
        source2 = str(record2.get('source', '')).lower()
        similarities['source'] = 1.0 if source1 == source2 else 0.0

        # Categories similarity
        cats1 = set(record1.get('categories', []))
        cats2 = set(record2.get('categories', []))
        if cats1 or cats2:
            intersection = len(cats1.intersection(cats2))
            union = len(cats1.union(cats2))
            similarities['categories'] = intersection / union if union > 0 else 0.0
        else:
            similarities['categories'] = 0.0

        # Calculate weighted similarity
        total_similarity = 0.0
        total_weight = 0.0

        for field, weight in weights.items():
            if field in similarities:
                total_similarity += similarities[field] * weight
                total_weight += weight

        return total_similarity / total_weight if total_weight > 0 else 0.0

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ''

        normalized = text
        config = self.config['normalization']

        if config.get('lowercase', True):
            normalized = normalized.lower()

        if config.get('remove_punctuation', True):
            # Remove common punctuation but keep spaces
            normalized = re.sub(r'[^\w\s]', '', normalized)

        if config.get('remove_extra_spaces', True):
            normalized = re.sub(r'\s+', ' ', normalized).strip()

        if config.get('remove_honorifics', True):
            # Remove common honorifics
            honorifics = ['mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'madam']
            words = normalized.split()
            filtered_words = [word for word in words if word not in honorifics]
            normalized = ' '.join(filtered_words)

        return normalized

    def _extract_alternative_names(self, record: Dict[str, Any]) -> List[str]:
        """Extract and normalize alternative names from record."""
        alt_names = []
        alt_fields = ['alternative_names', 'aliases', 'aka', 'other_names', 'japanese_name']

        for field in alt_fields:
            value = record.get(field)
            if isinstance(value, list):
                for name in value:
                    if name and not self._is_excluded_value(str(name)):
                        alt_names.append(self._normalize_text(str(name)))
            elif isinstance(value, str) and value:
                if not self._is_excluded_value(value):
                    alt_names.append(self._normalize_text(value))

        return list(set(alt_names))  # Remove duplicates

    def _calculate_name_list_similarity(self, names1: List[str], names2: List[str]) -> float:
        """Calculate similarity between two lists of names."""
        if not names1 or not names2:
            return 0.0

        max_similarity = 0.0
        total_comparisons = 0
        total_similarity = 0.0

        for name1 in names1:
            for name2 in names2:
                similarity = SequenceMatcher(None, name1, name2).ratio()
                total_similarity += similarity
                total_comparisons += 1
                max_similarity = max(max_similarity, similarity)

        # Return average of max similarity and overall average
        avg_similarity = total_similarity / total_comparisons if total_comparisons > 0 else 0.0
        return (max_similarity + avg_similarity) / 2

    def _is_excluded_value(self, value: str) -> bool:
        """Check if value should be excluded from comparison."""
        for pattern in self.exclusion_regex:
            if pattern.match(value.strip()):
                return True
        return False

    def _calculate_group_similarity(self, records: List[Dict[str, Any]]) -> float:
        """Calculate average similarity within a group of records."""
        if len(records) < 2:
            return 1.0

        total_similarity = 0.0
        comparisons = 0

        for i, record1 in enumerate(records):
            for record2 in records[i+1:]:
                similarity = self._calculate_similarity(record1, record2)
                total_similarity += similarity
                comparisons += 1

        return total_similarity / comparisons if comparisons > 0 else 0.0

    def _enhance_duplicate_group(self, group: Dict[str, Any],
                                records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance duplicate group with additional analysis."""
        enhanced = group.copy()

        # Add confidence score
        enhanced['confidence'] = self._calculate_group_confidence(records)

        # Add quality scores for each record
        enhanced['record_qualities'] = [
            self._calculate_record_quality(record) for record in records
        ]

        # Add merge recommendation
        enhanced['merge_recommended'] = enhanced['confidence'] > 0.8

        # Add conflict analysis
        enhanced['conflicts'] = self._analyze_conflicts(records)

        return enhanced

    def _calculate_group_confidence(self, records: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for duplicate group."""
        if len(records) < 2:
            return 1.0

        # Factors affecting confidence
        factors = {
            'similarity_consistency': 0.4,
            'source_diversity': 0.3,
            'data_completeness': 0.2,
            'conflict_level': 0.1
        }

        # Similarity consistency
        similarities = []
        for i, record1 in enumerate(records):
            for record2 in records[i+1:]:
                similarities.append(self._calculate_similarity(record1, record2))

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        similarity_variance = sum((s - avg_similarity) ** 2 for s in similarities) / len(similarities) if similarities else 0
        similarity_consistency = max(0, 1 - similarity_variance)

        # Source diversity (lower diversity = higher confidence for duplicates)
        sources = set(record.get('source', '') for record in records)
        source_diversity = 1 - (len(sources) / len(records))

        # Data completeness
        completeness_scores = [self._calculate_record_quality(record) for record in records]
        avg_completeness = sum(completeness_scores) / len(completeness_scores)

        # Conflict level
        conflicts = self._analyze_conflicts(records)
        conflict_score = 1 - min(1.0, len(conflicts) / 10)  # Normalize to 0-1

        # Calculate weighted confidence
        confidence = (
            similarity_consistency * factors['similarity_consistency'] +
            source_diversity * factors['source_diversity'] +
            avg_completeness * factors['data_completeness'] +
            conflict_score * factors['conflict_level']
        )

        return round(confidence, 3)

    def _calculate_record_quality(self, record: Dict[str, Any]) -> float:
        """Calculate quality score for a single record."""
        # Important fields and their weights
        field_weights = {
            'name': 0.3,
            'description': 0.2,
            'categories': 0.15,
            'images': 0.1,
            'stats': 0.1,
            'relationships': 0.05,
            'abilities': 0.05,
            'source': 0.05
        }

        quality_score = 0.0
        total_weight = 0.0

        for field, weight in field_weights.items():
            value = record.get(field)
            field_quality = 0.0

            if value is not None:
                if isinstance(value, str):
                    # String quality based on length and content
                    if value.strip() and not self._is_excluded_value(value):
                        field_quality = min(1.0, len(value.strip()) / 100)
                elif isinstance(value, (list, dict)):
                    # Collection quality based on size
                    field_quality = min(1.0, len(value) / 5) if value else 0.0
                else:
                    # Other types
                    field_quality = 1.0 if value else 0.0

            quality_score += field_quality * weight
            total_weight += weight

        return quality_score / total_weight if total_weight > 0 else 0.0

    def _analyze_conflicts(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze conflicts between records in a duplicate group."""
        conflicts = []

        if len(records) < 2:
            return conflicts

        # Get all fields across records
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())

        # Check each field for conflicts
        for field in all_fields:
            if field.startswith('_'):  # Skip metadata fields
                continue

            values = []
            for record in records:
                value = record.get(field)
                if value is not None and value != '':
                    values.append(value)

            if len(set(str(v) for v in values)) > 1:  # Conflict detected
                conflicts.append({
                    'field': field,
                    'values': values,
                    'count': len(values),
                    'unique_count': len(set(str(v) for v in values))
                })

        return conflicts

    def _merge_similar_groups(self, groups: List[Dict[str, Any]],
                             records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge similar duplicate groups that might be related."""
        if len(groups) < 2:
            return groups

        merged_groups = []
        processed_groups = set()

        for i, group1 in enumerate(groups):
            if i in processed_groups:
                continue

            current_merge = group1
            processed_groups.add(i)

            for j, group2 in enumerate(groups[i+1:], i+1):
                if j in processed_groups:
                    continue

                # Check if groups should be merged
                if self._should_merge_groups(group1, group2, records):
                    # Merge the groups
                    current_merge = self._merge_groups(current_merge, group2)
                    processed_groups.add(j)

            merged_groups.append(current_merge)

        return merged_groups

    def _should_merge_groups(self, group1: Dict[str, Any], group2: Dict[str, Any],
                            records: List[Dict[str, Any]]) -> bool:
        """Determine if two duplicate groups should be merged."""
        # Get representative records from each group
        records1 = [records[i] for i in group1['indices']]
        records2 = [records[i] for i in group2['indices']]

        # Calculate cross-group similarity
        max_similarity = 0.0
        for record1 in records1:
            for record2 in records2:
                similarity = self._calculate_similarity(record1, record2)
                max_similarity = max(max_similarity, similarity)

        # Merge if similarity is above threshold
        return max_similarity >= self.config['similarity_threshold'] * 0.9

    def _merge_groups(self, group1: Dict[str, Any], group2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two duplicate groups."""
        merged = {
            'type': 'merged',
            'indices': group1['indices'] + group2['indices'],
            'count': group1['count'] + group2['count'],
            'similarity': (group1['similarity'] + group2['similarity']) / 2,
            'subgroups': [group1, group2]
        }

        # Merge other fields if present
        for field in ['confidence', 'merge_recommended']:
            if field in group1 and field in group2:
                merged[field] = (group1[field] + group2[field]) / 2

        return merged

    def _select_best_record(self, records: List[Dict[str, Any]],
                           indices: List[int]) -> Tuple[Dict[str, Any], int]:
        """Select the best record from a duplicate group."""
        if not records:
            return {}, -1

        best_record = records[0]
        best_index = indices[0]
        best_score = self._calculate_record_quality(best_record)

        for record, index in zip(records[1:], indices[1:]):
            score = self._calculate_record_quality(record)
            if score > best_score:
                best_record = record
                best_index = index
                best_score = score

        return best_record, best_index

    def _merge_duplicate_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple duplicate records into one."""
        if not records:
            return {}

        if len(records) == 1:
            return records[0]

        # Start with the best quality record as base
        qualities = [self._calculate_record_quality(record) for record in records]
        best_index = qualities.index(max(qualities))
        merged = dict(records[best_index])

        # Merge information from other records
        for i, record in enumerate(records):
            if i == best_index:
                continue

            for field, value in record.items():
                if field not in merged or merged[field] in [None, '', []]:
                    merged[field] = value
                elif field == 'categories' and isinstance(value, list):
                    # Merge categories
                    existing = merged.get(field, [])
                    if isinstance(existing, list):
                        merged[field] = list(set(existing + value))
                elif field == 'images' and isinstance(value, list):
                    # Merge image lists
                    existing = merged.get(field, [])
                    if isinstance(existing, list):
                        merged[field] = list(set(existing + value))

        # Add merge metadata
        merged['_merge_metadata'] = {
            'merged_at': datetime.now().isoformat(),
            'source_count': len(records),
            'merge_sources': [record.get('source', 'unknown') for record in records]
        }

        return merged

    def _calculate_statistics(self, records: List[Dict[str, Any]],
                             duplicate_groups: List[Dict[str, Any]],
                             processing_time: float) -> Dict[str, Any]:
        """Calculate deduplication statistics."""
        total_records = len(records)
        duplicate_count = sum(group['count'] for group in duplicate_groups)
        unique_count = total_records - duplicate_count + len(duplicate_groups)

        # Group statistics by type
        group_stats = defaultdict(int)
        for group in duplicate_groups:
            group_stats[group['type']] += 1

        return {
            'total_records': total_records,
            'duplicate_groups': len(duplicate_groups),
            'duplicate_records': duplicate_count,
            'unique_records': unique_count,
            'deduplication_rate': (duplicate_count / total_records) if total_records > 0 else 0,
            'group_types': dict(group_stats),
            'processing_time_seconds': processing_time,
            'average_group_size': duplicate_count / len(duplicate_groups) if duplicate_groups else 0
        }

    def _create_empty_stats(self) -> Dict[str, Any]:
        """Create empty statistics dictionary."""
        return {
            'total_records': 0,
            'duplicate_groups': 0,
            'duplicate_records': 0,
            'unique_records': 0,
            'deduplication_rate': 0,
            'group_types': {},
            'processing_time_seconds': 0,
            'average_group_size': 0
        }


def create_deduplication_config() -> Dict[str, Any]:
    """Create default configuration for deduplication."""
    return {
        'similarity_threshold': 0.85,
        'name_threshold': 0.9,
        'description_threshold': 0.7,
        'strict_mode': False,
        'field_weights': {
            'name': 0.5,
            'alternative_names': 0.2,
            'description': 0.15,
            'source': 0.1,
            'categories': 0.05
        },
        'normalization': {
            'lowercase': True,
            'remove_punctuation': True,
            'remove_extra_spaces': True,
            'remove_honorifics': True
        },
        'exclusion_patterns': [
            r'^\s*,
            r'^unknown,
            r'^n/a,
            r'^tbd,
            r'^none,
            r'^null
        ]
    }