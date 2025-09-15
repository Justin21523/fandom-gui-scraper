# utils/data_processing/quality_scorer.py
"""
Data quality scoring module for character records.
Provides comprehensive quality assessment and scoring algorithms.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
import statistics


class QualityScorer:
    """
    Comprehensive data quality scoring engine.

    Features:
    - Multi-dimensional quality assessment
    - Configurable scoring criteria
    - Quality trends analysis
    - Detailed quality reports
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize quality scorer.

        Args:
            config: Configuration dictionary with scoring parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            'scoring_dimensions': {
                'completeness': 0.25,      # How complete is the data
                'accuracy': 0.25,          # How accurate/valid is the data
                'consistency': 0.20,       # Internal consistency
                'timeliness': 0.15,        # How fresh/recent is the data
                'uniqueness': 0.15         # Absence of duplicates
            },
            'field_importance': {
                'name': 1.0,
                'description': 0.8,
                'categories': 0.7,
                'stats': 0.6,
                'images': 0.5,
                'relationships': 0.4,
                'abilities': 0.4,
                'source': 0.3,
                'url': 0.2
            },
            'thresholds': {
                'excellent': 0.9,
                'good': 0.75,
                'fair': 0.6,
                'poor': 0.4
            },
            'validation_rules': {
                'name_min_length': 2,
                'name_max_length': 100,
                'description_min_length': 20,
                'description_max_length': 5000,
                'valid_sources': [
                    'onepiece.fandom.com',
                    'naruto.fandom.com',
                    'fandom.com',
                    'manual_entry'
                ]
            }
        }

        if config:
            self.config.update(config)

    def score_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive quality score for a single record.

        Args:
            record: Character record to score

        Returns:
            Quality score report with detailed breakdown
        """
        if not record:
            return self._create_empty_score()

        self.logger.debug(f"Scoring record: {record.get('name', 'Unknown')}")

        # Calculate scores for each dimension
        scores = {}
        details = {}

        scores['completeness'], details['completeness'] = self._score_completeness(record)
        scores['accuracy'], details['accuracy'] = self._score_accuracy(record)
        scores['consistency'], details['consistency'] = self._score_consistency(record)
        scores['timeliness'], details['timeliness'] = self._score_timeliness(record)
        scores['uniqueness'], details['uniqueness'] = self._score_uniqueness(record)

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(scores)

        # Determine quality grade
        grade = self._determine_grade(overall_score)

        # Create quality report
        quality_report = {
            'overall_score': round(overall_score, 3),
            'grade': grade,
            'dimension_scores': scores,
            'dimension_details': details,
            'recommendations': self._generate_recommendations(scores, details),
            'scored_at': datetime.now().isoformat(),
            'config_used': self.config.copy()
        }

        return quality_report

    def score_dataset(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score entire dataset and provide aggregate quality analysis.

        Args:
            records: List of character records

        Returns:
            Dataset quality report with statistics and trends
        """
        if not records:
            return self._create_empty_dataset_score()

        self.logger.info(f"Scoring dataset with {len(records)} records")

        start_time = datetime.now()

        # Score individual records
        record_scores = []
        dimension_scores = {dim: [] for dim in self.config['scoring_dimensions']}

        for record in records:
            score_report = self.score_record(record)
            record_scores.append(score_report['overall_score'])

            for dimension, score in score_report['dimension_scores'].items():
                dimension_scores[dimension].append(score)

        # Calculate aggregate statistics
        aggregate_stats = self._calculate_aggregate_stats(record_scores, dimension_scores)

        # Analyze quality distribution
        quality_distribution = self._analyze_quality_distribution(record_scores)

        # Identify quality issues
        quality_issues = self._identify_dataset_issues(records, record_scores)

        # Generate dataset recommendations
        recommendations = self._generate_dataset_recommendations(aggregate_stats, quality_issues)

        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            'dataset_summary': {
                'total_records': len(records),
                'average_score': aggregate_stats['overall']['mean'],
                'median_score': aggregate_stats['overall']['median'],
                'std_deviation': aggregate_stats['overall']['std'],
                'processing_time': processing_time
            },
            'dimension_statistics': aggregate_stats['dimensions'],
            'quality_distribution': quality_distribution,
            'quality_issues': quality_issues,
            'recommendations': recommendations,
            'scored_at': datetime.now().isoformat()
        }

    def _score_completeness(self, record: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score data completeness."""
        field_weights = self.config['field_importance']

        completed_weight = 0.0
        total_weight = 0.0
        field_status = {}

        for field, weight in field_weights.items():
            value = record.get(field)
            is_complete = self._is_field_complete(field, value)

            field_status[field] = {
                'present': value is not None,
                'complete': is_complete,
                'weight': weight
            }

            if is_complete:
                completed_weight += weight
            total_weight += weight

        completeness_score = completed_weight / total_weight if total_weight > 0 else 0.0

        details = {
            'score': completeness_score,
            'completed_fields': sum(1 for status in field_status.values() if status['complete']),
            'total_fields': len(field_status),
            'field_status': field_status,
            'missing_important_fields': [
                field for field, status in field_status.items()
                if not status['complete'] and status['weight'] >= 0.7
            ]
        }

        return completeness_score, details

    def _score_accuracy(self, record: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score data accuracy and validity."""
        validation_results = {}
        total_checks = 0
        passed_checks = 0

        # Name validation
        name = record.get('name', '')
        name_valid, name_issues = self._validate_name(name)
        validation_results['name'] = {'valid': name_valid, 'issues': name_issues}
        total_checks += 1
        if name_valid:
            passed_checks += 1

        # Description validation
        description = record.get('description', '')
        desc_valid, desc_issues = self._validate_description(description)
        validation_results['description'] = {'valid': desc_valid, 'issues': desc_issues}
        total_checks += 1
        if desc_valid:
            passed_checks += 1

        # Source validation
        source = record.get('source', '')
        source_valid, source_issues = self._validate_source(source)
        validation_results['source'] = {'valid': source_valid, 'issues': source_issues}
        total_checks += 1
        if source_valid:
            passed_checks += 1

        # URL validation
        url = record.get('url', '')
        url_valid, url_issues = self._validate_url(url)
        validation_results['url'] = {'valid': url_valid, 'issues': url_issues}
        total_checks += 1
        if url_valid:
            passed_checks += 1

        # Categories validation
        categories = record.get('categories', [])
        cat_valid, cat_issues = self._validate_categories(categories)
        validation_results['categories'] = {'valid': cat_valid, 'issues': cat_issues}
        total_checks += 1
        if cat_valid:
            passed_checks += 1

        accuracy_score = passed_checks / total_checks if total_checks > 0 else 0.0

        details = {
            'score': accuracy_score,
            'validation_results': validation_results,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'critical_issues': [
                field for field, result in validation_results.items()
                if not result['valid'] and field in ['name', 'source']
            ]
        }

        return accuracy_score, details

    def _score_consistency(self, record: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score internal data consistency."""
        consistency_checks = []

        # Check name consistency with alternative names
        name = record.get('name', '').lower()
        alt_names = record.get('alternative_names', [])
        if isinstance(alt_names, list) and name:
            name_in_alts = any(name in alt.lower() for alt in alt_names if isinstance(alt, str))
            consistency_checks.append({
                'check': 'name_in_alternatives',
                'passed': not name_in_alts,  # Name shouldn't be in alternatives
                'importance': 0.3
            })

        # Check description consistency with categories
        description = record.get('description', '').lower()
        categories = record.get('categories', [])
        if description and categories:
            cat_mentions = sum(1 for cat in categories
                             if isinstance(cat, str) and cat.lower() in description)
            cat_consistency = cat_mentions / len(categories) if categories else 0
            consistency_checks.append({
                'check': 'categories_in_description',
                'passed': cat_consistency > 0.3,
                'score': cat_consistency,
                'importance': 0.2
            })

        # Check data type consistency
        type_consistency = self._check_data_types(record)
        consistency_checks.append({
            'check': 'data_types',
            'passed': type_consistency > 0.8,
            'score': type_consistency,
            'importance': 0.2
        })

        # Check numeric value consistency (if stats present)
        if 'stats' in record and isinstance(record['stats'], dict):
            stats_consistency = self._check_stats_consistency(record['stats'])
            consistency_checks.append({
                'check': 'stats_consistency',
                'passed': stats_consistency > 0.7,
                'score': stats_consistency,
                'importance': 0.3
            })

        # Calculate overall consistency score
        total_weight = sum(check['importance'] for check in consistency_checks)
        if total_weight > 0:
            weighted_score = sum(
                (check.get('score', 1.0 if check['passed'] else 0.0) * check['importance'])
                for check in consistency_checks
            )
            consistency_score = weighted_score / total_weight
        else:
            consistency_score = 1.0

        details = {
            'score': consistency_score,
            'checks_performed': len(consistency_checks),
            'checks_passed': sum(1 for check in consistency_checks if check['passed']),
            'consistency_checks': consistency_checks,
            'issues_found': [
                check['check'] for check in consistency_checks if not check['passed']
            ]
        }

        return consistency_score, details

    def _score_timeliness(self, record: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score data timeliness/freshness."""
        scraped_at = record.get('scraped_at')
        updated_at = record.get('updated_at')

        # Use most recent timestamp
        timestamp = updated_at or scraped_at

        if not timestamp:
            # No timestamp available
            timeliness_score = 0.5  # Neutral score
            age_info = 'unknown'
        else:
            try:
                # Parse timestamp
                if isinstance(timestamp, str):
                    # Handle various timestamp formats
                    timestamp = timestamp.replace('Z', '+00:00')
                    scraped_time = datetime.fromisoformat(timestamp)
                else:
                    scraped_time = timestamp

                # Calculate age
                now = datetime.now()
                if scraped_time.tzinfo:
                    now = now.replace(tzinfo=scraped_time.tzinfo)

                age = now - scraped_time
                age_days = age.total_seconds() / (24 * 3600)

                # Score based on age (exponential decay)
                if age_days <= 1:
                    timeliness_score = 1.0
                elif age_days <= 7:
                    timeliness_score = 0.9
                elif age_days <= 30:
                    timeliness_score = 0.8
                elif age_days <= 90:
                    timeliness_score = 0.6
                elif age_days <= 365:
                    timeliness_score = 0.4
                else:
                    timeliness_score = 0.2

                age_info = f"{age_days:.1f} days"

            except Exception as e:
                self.logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
                timeliness_score = 0.3
                age_info = 'invalid_timestamp'

        details = {
            'score': timeliness_score,
            'timestamp': timestamp,
            'age': age_info,
            'freshness_category': self._categorize_freshness(timeliness_score)
        }

        return timeliness_score, details

    def _score_uniqueness(self, record: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Score record uniqueness (absence of duplication indicators)."""
        # This is a simplified version - in practice, you'd compare against other records
        uniqueness_indicators = []

        # Check for duplicate detection metadata
        if '_fusion_metadata' in record:
            fusion_data = record['_fusion_metadata']
            source_count = fusion_data.get('source_count', 1)
            uniqueness_score = 1.0 / source_count if source_count > 1 else 1.0
            uniqueness_indicators.append({
                'indicator': 'fusion_sources',
                'value': source_count,
                'impact': 1.0 - uniqueness_score
            })
        else:
            uniqueness_score = 1.0

        # Check for internal duplication (repeated content)
        internal_duplication = self._check_internal_duplication(record)
        if internal_duplication > 0:
            uniqueness_score *= (1.0 - internal_duplication * 0.3)
            uniqueness_indicators.append({
                'indicator': 'internal_duplication',
                'value': internal_duplication,
                'impact': internal_duplication * 0.3
            })

        details = {
            'score': uniqueness_score,
            'uniqueness_indicators': uniqueness_indicators,
            'internal_duplication': internal_duplication
        }

        return uniqueness_score, details

    def _is_field_complete(self, field: str, value: Any) -> bool:
        """Check if a field is considered complete."""
        if value is None:
            return False

        if isinstance(value, str):
            return len(value.strip()) > 0
        elif isinstance(value, (list, dict)):
            return len(value) > 0
        else:
            return True

    def _validate_name(self, name: str) -> Tuple[bool, List[str]]:
        """Validate character name."""
        issues = []

        if not name or not isinstance(name, str):
            issues.append("Name is missing or not a string")
            return False, issues

        name = name.strip()

        # Length validation
        min_len = self.config['validation_rules']['name_min_length']
        max_len = self.config['validation_rules']['name_max_length']

        if len(name) < min_len:
            issues.append(f"Name too short (minimum {min_len} characters)")
        elif len(name) > max_len:
            issues.append(f"Name too long (maximum {max_len} characters)")

        # Content validation
        if name.lower() in ['unknown', 'unnamed', 'n/a', 'null', 'none']:
            issues.append("Name appears to be a placeholder")

        if re.match(r'^[0-9]+
        , name):
            issues.append("Name appears to be just numbers")

        # Special character validation
        if re.search(r'[<>{}[\]\\|`~]', name):
            issues.append("Name contains invalid special characters")

        return len(issues) == 0, issues

    def _validate_description(self, description: str) -> Tuple[bool, List[str]]:
        """Validate character description."""
        issues = []

        if not description or not isinstance(description, str):
            issues.append("Description is missing or not a string")
            return False, issues

        description = description.strip()

        # Length validation
        min_len = self.config['validation_rules']['description_min_length']
        max_len = self.config['validation_rules']['description_max_length']

        if len(description) < min_len:
            issues.append(f"Description too short (minimum {min_len} characters)")
        elif len(description) > max_len:
            issues.append(f"Description too long (maximum {max_len} characters)")

        # Content quality validation
        if description.lower() in ['unknown', 'no description', 'n/a', 'tbd']:
            issues.append("Description appears to be a placeholder")

        # Check for meaningful content
        word_count = len(description.split())
        if word_count < 5:
            issues.append("Description appears too brief to be meaningful")

        # Check for HTML/markup remnants
        if re.search(r'<[^>]+>', description):
            issues.append("Description contains HTML markup")

        return len(issues) == 0, issues

    def _validate_source(self, source: str) -> Tuple[bool, List[str]]:
        """Validate data source."""
        issues = []

        if not source or not isinstance(source, str):
            issues.append("Source is missing or not a string")
            return False, issues

        source = source.strip().lower()
        valid_sources = [s.lower() for s in self.config['validation_rules']['valid_sources']]

        if source not in valid_sources:
            issues.append(f"Source '{source}' is not in the list of valid sources")

        return len(issues) == 0, issues

    def _validate_url(self, url: str) -> Tuple[bool, List[str]]:
        """Validate URL format."""
        issues = []

        if not url:
            # URL is optional
            return True, issues

        if not isinstance(url, str):
            issues.append("URL is not a string")
            return False, issues

        url = url.strip()

        # Basic URL format validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)
        , re.IGNORECASE)

        if not url_pattern.match(url):
            issues.append("URL format is invalid")

        return len(issues) == 0, issues

    def _validate_categories(self, categories: List[str]) -> Tuple[bool, List[str]]:
        """Validate categories list."""
        issues = []

        if not categories:
            # Categories are optional
            return True, issues

        if not isinstance(categories, list):
            issues.append("Categories should be a list")
            return False, issues

        # Check individual categories
        for i, category in enumerate(categories):
            if not isinstance(category, str):
                issues.append(f"Category {i} is not a string")
            elif not category.strip():
                issues.append(f"Category {i} is empty")

        # Check for duplicates
        if len(categories) != len(set(categories)):
            issues.append("Categories contain duplicates")

        return len(issues) == 0, issues

    def _check_data_types(self, record: Dict[str, Any]) -> float:
        """Check data type consistency."""
        expected_types = {
            'name': str,
            'description': str,
            'categories': list,
            'images': list,
            'stats': dict,
            'relationships': (list, dict),
            'abilities': list,
            'source': str,
            'url': str
        }

        correct_types = 0
        total_checks = 0

        for field, expected_type in expected_types.items():
            if field in record:
                value = record[field]
                if isinstance(expected_type, tuple):
                    is_correct = isinstance(value, expected_type)
                else:
                    is_correct = isinstance(value, expected_type)

                if is_correct:
                    correct_types += 1
                total_checks += 1

        return correct_types / total_checks if total_checks > 0 else 1.0

    def _check_stats_consistency(self, stats: Dict[str, Any]) -> float:
        """Check statistical data consistency."""
        if not isinstance(stats, dict):
            return 0.0

        consistency_score = 1.0

        # Check for numeric values
        numeric_fields = ['power', 'speed', 'strength', 'intelligence', 'durability']
        numeric_values = []

        for field in numeric_fields:
            if field in stats:
                try:
                    value = float(stats[field])
                    if 0 <= value <= 100:  # Assuming stats are 0-100 scale
                        numeric_values.append(value)
                    else:
                        consistency_score *= 0.9  # Penalty for out-of-range values
                except (ValueError, TypeError):
                    consistency_score *= 0.8  # Penalty for non-numeric values

        # Check for reasonable stat distribution
        if len(numeric_values) >= 3:
            std_dev = statistics.stdev(numeric_values)
            # Very low std dev might indicate fake/generated data
            if std_dev < 1.0:
                consistency_score *= 0.9

        return consistency_score

    def _categorize_freshness(self, timeliness_score: float) -> str:
        """Categorize data freshness based on score."""
        if timeliness_score >= 0.9:
            return 'very_fresh'
        elif timeliness_score >= 0.7:
            return 'fresh'
        elif timeliness_score >= 0.5:
            return 'moderate'
        elif timeliness_score >= 0.3:
            return 'stale'
        else:
            return 'very_stale'

    def _check_internal_duplication(self, record: Dict[str, Any]) -> float:
        """Check for internal content duplication."""
        duplication_score = 0.0

        # Check for repeated values in lists
        for field, value in record.items():
            if isinstance(value, list) and len(value) > 1:
                unique_items = len(set(str(item) for item in value))
                if unique_items < len(value):
                    duplication_ratio = 1 - (unique_items / len(value))
                    duplication_score = max(duplication_score, duplication_ratio)

        # Check for repeated phrases in text fields
        text_fields = ['description', 'background', 'abilities']
        for field in text_fields:
            if field in record and isinstance(record[field], str):
                text = record[field]
                words = text.lower().split()
                if len(words) > 10:
                    word_counts = Counter(words)
                    total_words = len(words)
                    repeated_words = sum(count - 1 for count in word_counts.values() if count > 1)
                    repetition_ratio = repeated_words / total_words
                    duplication_score = max(duplication_score, repetition_ratio * 0.5)

        return duplication_score

    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted overall quality score."""
        weights = self.config['scoring_dimensions']

        total_weight = 0.0
        weighted_sum = 0.0

        for dimension, weight in weights.items():
            if dimension in scores:
                weighted_sum += scores[dimension] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _determine_grade(self, score: float) -> str:
        """Determine quality grade based on score."""
        thresholds = self.config['thresholds']

        if score >= thresholds['excellent']:
            return 'A'
        elif score >= thresholds['good']:
            return 'B'
        elif score >= thresholds['fair']:
            return 'C'
        elif score >= thresholds['poor']:
            return 'D'
        else:
            return 'F'

    def _generate_recommendations(self, scores: Dict[str, float],
                                 details: Dict[str, Dict]) -> List[str]:
        """Generate improvement recommendations based on scores."""
        recommendations = []

        # Completeness recommendations
        if scores.get('completeness', 0) < 0.7:
            missing_fields = details.get('completeness', {}).get('missing_important_fields', [])
            if missing_fields:
                recommendations.append(f"Add missing important fields: {', '.join(missing_fields)}")

        # Accuracy recommendations
        if scores.get('accuracy', 0) < 0.8:
            critical_issues = details.get('accuracy', {}).get('critical_issues', [])
            if critical_issues:
                recommendations.append(f"Fix critical validation issues in: {', '.join(critical_issues)}")

        # Consistency recommendations
        if scores.get('consistency', 0) < 0.7:
            issues = details.get('consistency', {}).get('issues_found', [])
            if issues:
                recommendations.append(f"Resolve consistency issues: {', '.join(issues)}")

        # Timeliness recommendations
        if scores.get('timeliness', 0) < 0.6:
            recommendations.append("Consider updating this record with fresh data")

        # Uniqueness recommendations
        if scores.get('uniqueness', 0) < 0.8:
            recommendations.append("Check for and resolve potential duplicates")

        return recommendations

    def _calculate_aggregate_stats(self, record_scores: List[float],
                                  dimension_scores: Dict[str, List[float]]) -> Dict[str, Any]:
        """Calculate aggregate statistics for the dataset."""
        stats = {}

        # Overall statistics
        if record_scores:
            stats['overall'] = {
                'mean': statistics.mean(record_scores),
                'median': statistics.median(record_scores),
                'std': statistics.stdev(record_scores) if len(record_scores) > 1 else 0.0,
                'min': min(record_scores),
                'max': max(record_scores)
            }

        # Dimension statistics
        stats['dimensions'] = {}
        for dimension, scores in dimension_scores.items():
            if scores:
                stats['dimensions'][dimension] = {
                    'mean': statistics.mean(scores),
                    'median': statistics.median(scores),
                    'std': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                    'min': min(scores),
                    'max': max(scores)
                }

        return stats

    def _analyze_quality_distribution(self, scores: List[float]) -> Dict[str, Any]:
        """Analyze quality score distribution."""
        if not scores:
            return {}

        thresholds = self.config['thresholds']
        distribution = {
            'excellent': sum(1 for s in scores if s >= thresholds['excellent']),
            'good': sum(1 for s in scores if thresholds['good'] <= s < thresholds['excellent']),
            'fair': sum(1 for s in scores if thresholds['fair'] <= s < thresholds['good']),
            'poor': sum(1 for s in scores if thresholds['poor'] <= s < thresholds['fair']),
            'very_poor': sum(1 for s in scores if s < thresholds['poor'])
        }

        total = len(scores)
        percentages = {k: (v / total) * 100 for k, v in distribution.items()}

        return {
            'counts': distribution,
            'percentages': percentages,
            'total_records': total
        }

    def _identify_dataset_issues(self, records: List[Dict[str, Any]],
                                scores: List[float]) -> List[Dict[str, Any]]:
        """Identify common quality issues in the dataset."""
        issues = []

        # Low scoring records
        low_scores = [(i, score) for i, score in enumerate(scores) if score < 0.5]
        if low_scores:
            issues.append({
                'type': 'low_quality_records',
                'count': len(low_scores),
                'percentage': (len(low_scores) / len(records)) * 100,
                'description': f"{len(low_scores)} records have quality scores below 0.5"
            })

        # Missing critical fields
        critical_fields = ['name', 'description', 'source']
        for field in critical_fields:
            missing_count = sum(1 for record in records
                              if not record.get(field) or record[field] == '')
            if missing_count > 0:
                issues.append({
                    'type': 'missing_critical_field',
                    'field': field,
                    'count': missing_count,
                    'percentage': (missing_count / len(records)) * 100,
                    'description': f"{missing_count} records missing '{field}' field"
                })

        # Potential duplicates (simplified check)
        names = [record.get('name', '').lower().strip() for record in records]
        name_counts = Counter(names)
        duplicate_names = [name for name, count in name_counts.items() if count > 1 and name]

        if duplicate_names:
            total_duplicates = sum(name_counts[name] for name in duplicate_names)
            issues.append({
                'type': 'potential_duplicates',
                'count': total_duplicates,
                'unique_names': len(duplicate_names),
                'percentage': (total_duplicates / len(records)) * 100,
                'description': f"{total_duplicates} records have duplicate names"
            })

        return issues

    def _generate_dataset_recommendations(self, stats: Dict[str, Any],
                                         issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for dataset improvement."""
        recommendations = []

        # Overall quality recommendations
        overall_mean = stats.get('overall', {}).get('mean', 0)
        if overall_mean < 0.7:
            recommendations.append("Dataset quality is below acceptable threshold - consider data cleanup")

        # Dimension-specific recommendations
        dimensions = stats.get('dimensions', {})
        for dimension, dim_stats in dimensions.items():
            if dim_stats.get('mean', 0) < 0.6:
                recommendations.append(f"Focus on improving {dimension} across the dataset")

        # Issue-specific recommendations
        for issue in issues:
            if issue['type'] == 'low_quality_records':
                if issue['percentage'] > 20:
                    recommendations.append("Consider removing or improving low-quality records")
            elif issue['type'] == 'missing_critical_field':
                if issue['percentage'] > 10:
                    recommendations.append(f"Prioritize filling missing '{issue['field']}' fields")
            elif issue['type'] == 'potential_duplicates':
                if issue['percentage'] > 5:
                    recommendations.append("Run deduplication process to remove duplicate records")

        return recommendations

    def _create_empty_score(self) -> Dict[str, Any]:
        """Create empty score report."""
        return {
            'overall_score': 0.0,
            'grade': 'F',
            'dimension_scores': {},
            'dimension_details': {},
            'recommendations': ['No data available for scoring'],
            'scored_at': datetime.now().isoformat()
        }

    def _create_empty_dataset_score(self) -> Dict[str, Any]:
        """Create empty dataset score report."""
        return {
            'dataset_summary': {
                'total_records': 0,
                'average_score': 0.0,
                'median_score': 0.0,
                'std_deviation': 0.0,
                'processing_time': 0.0
            },
            'dimension_statistics': {},
            'quality_distribution': {},
            'quality_issues': [],
            'recommendations': ['No data available for analysis'],
            'scored_at': datetime.now().isoformat()
        }


def create_quality_config() -> Dict[str, Any]:
    """Create default configuration for quality scoring."""
    return {
        'scoring_dimensions': {
            'completeness': 0.25,
            'accuracy': 0.25,
            'consistency': 0.20,
            'timeliness': 0.15,
            'uniqueness': 0.15
        },
        'field_importance': {
            'name': 1.0,
            'description': 0.8,
            'categories': 0.7,
            'stats': 0.6,
            'images': 0.5,
            'relationships': 0.4,
            'abilities': 0.4,
            'source': 0.3,
            'url': 0.2
        },
        'thresholds': {
            'excellent': 0.9,
            'good': 0.75,
            'fair': 0.6,
            'poor': 0.4
        },
        'validation_rules': {
            'name_min_length': 2,
            'name_max_length': 100,
            'description_min_length': 20,
            'description_max_length': 5000,
            'valid_sources': [
                'onepiece.fandom.com',
                'naruto.fandom.com',
                'dragonball.fandom.com',
                'fandom.com',
                'manual_entry',
                'api_data'
            ]
        }
    }