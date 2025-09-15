# utils/visualization/stats_calculator.py
"""
Statistics calculation utilities for character data analysis.
Provides comprehensive statistical analysis and metrics calculation.
"""

import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict


class StatsCalculator:
    """
    Comprehensive statistics calculator for character data.

    Features:
    - Descriptive statistics
    - Distribution analysis
    - Trend analysis
    - Correlation analysis
    - Quality metrics
    - Growth analysis
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize statistics calculator.

        Args:
            config: Configuration dictionary with calculation parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "analysis": {
                "include_distributions": True,
                "include_trends": True,
                "include_quality_metrics": True,
                "include_growth_analysis": True,
            },
            "thresholds": {
                "min_data_points": 5,
                "outlier_threshold": 2.0,  # Standard deviations
                "trend_significance": 0.1,
            },
            "time_periods": {"daily": True, "weekly": True, "monthly": True},
        }

        if config:
            self.config.update(config)

    def calculate_comprehensive_stats(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for character dataset.

        Args:
            characters: List of character data

        Returns:
            Comprehensive statistics report
        """
        if not characters:
            return {"error": "No character data provided"}

        self.logger.info(
            f"Calculating comprehensive statistics for {len(characters)} characters"
        )

        stats_report = {
            "overview": self._calculate_overview_stats(characters),
            "distributions": self._calculate_distributions(characters),
            "quality_metrics": self._calculate_quality_metrics(characters),
            "temporal_analysis": self._calculate_temporal_stats(characters),
            "content_analysis": self._calculate_content_stats(characters),
            "source_analysis": self._calculate_source_stats(characters),
            "generated_at": datetime.now().isoformat(),
        }

        # Add growth analysis if configured
        if self.config["analysis"]["include_growth_analysis"]:
            stats_report["growth_analysis"] = self._calculate_growth_analysis(
                characters
            )

        return stats_report

    def calculate_dataset_health(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate dataset health metrics.

        Args:
            characters: List of character data

        Returns:
            Dataset health report
        """
        if not characters:
            return {"health_score": 0, "status": "no_data"}

        health_metrics = {
            "completeness": self._calculate_completeness_score(characters),
            "consistency": self._calculate_consistency_score(characters),
            "freshness": self._calculate_freshness_score(characters),
            "diversity": self._calculate_diversity_score(characters),
            "quality": self._calculate_overall_quality_score(characters),
        }

        # Calculate overall health score (weighted average)
        weights = {
            "completeness": 0.25,
            "consistency": 0.2,
            "freshness": 0.2,
            "diversity": 0.15,
            "quality": 0.2,
        }
        overall_score = sum(
            health_metrics[metric] * weights[metric] for metric in weights
        )

        # Determine health status
        if overall_score >= 0.8:
            status = "excellent"
        elif overall_score >= 0.6:
            status = "good"
        elif overall_score >= 0.4:
            status = "fair"
        else:
            status = "poor"

        return {
            "health_score": overall_score,
            "status": status,
            "metrics": health_metrics,
            "recommendations": self._generate_health_recommendations(health_metrics),
        }

    def calculate_source_performance(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics for each data source.

        Args:
            characters: List of character data

        Returns:
            Source performance analysis
        """
        source_performance = {}

        # Group characters by source
        by_source = defaultdict(list)
        for char in characters:
            source = char.get("source", "unknown")
            by_source[source].append(char)

        for source, source_chars in by_source.items():
            performance = {
                "character_count": len(source_chars),
                "completeness_score": self._calculate_completeness_score(source_chars),
                "quality_score": self._calculate_overall_quality_score(source_chars),
                "avg_description_length": self._calculate_avg_description_length(
                    source_chars
                ),
                "categories_per_character": self._calculate_avg_categories(
                    source_chars
                ),
                "images_per_character": self._calculate_avg_images(source_chars),
                "freshness_score": self._calculate_freshness_score(source_chars),
            }

            # Calculate performance ranking
            performance["performance_score"] = (
                performance["completeness_score"] * 0.3
                + performance["quality_score"] * 0.3
                + min(performance["avg_description_length"] / 500, 1.0) * 0.2
                + min(performance["categories_per_character"] / 5, 1.0) * 0.1
                + performance["freshness_score"] * 0.1
            )

            source_performance[source] = performance

        # Rank sources
        ranked_sources = sorted(
            source_performance.items(),
            key=lambda x: x[1]["performance_score"],
            reverse=True,
        )

        return {
            "source_metrics": source_performance,
            "ranking": [
                {"source": source, "score": metrics["performance_score"]}
                for source, metrics in ranked_sources
            ],
            "best_source": ranked_sources[0][0] if ranked_sources else None,
            "worst_source": ranked_sources[-1][0] if ranked_sources else None,
        }

    def calculate_trends(
        self, characters: List[Dict[str, Any]], time_field: str = "scraped_at"
    ) -> Dict[str, Any]:
        """
        Calculate trend analysis over time.

        Args:
            characters: List of character data
            time_field: Field containing timestamp data

        Returns:
            Trend analysis results
        """
        trends = {
            "daily_trends": self._calculate_daily_trends(characters, time_field),
            "weekly_trends": self._calculate_weekly_trends(characters, time_field),
            "monthly_trends": self._calculate_monthly_trends(characters, time_field),
            "growth_rate": self._calculate_growth_rate(characters, time_field),
            "peak_periods": self._identify_peak_periods(characters, time_field),
        }

        return trends

    def _calculate_overview_stats(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate basic overview statistics."""
        return {
            "total_characters": len(characters),
            "unique_sources": len(
                set(char.get("source", "unknown") for char in characters)
            ),
            "characters_with_descriptions": sum(
                1 for char in characters if char.get("description")
            ),
            "characters_with_images": sum(
                1 for char in characters if char.get("images")
            ),
            "characters_with_categories": sum(
                1 for char in characters if char.get("categories")
            ),
            "total_categories": len(self._get_all_categories(characters)),
            "avg_categories_per_character": self._calculate_avg_categories(characters),
            "avg_images_per_character": self._calculate_avg_images(characters),
            "avg_description_length": self._calculate_avg_description_length(
                characters
            ),
        }

    def _calculate_distributions(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate distribution statistics."""
        distributions = {}

        # Source distribution
        source_counts = Counter(char.get("source", "unknown") for char in characters)
        distributions["sources"] = dict(source_counts.most_common())

        # Category distribution
        all_categories = self._get_all_categories(characters)
        category_counts = Counter(all_categories)
        distributions["categories"] = dict(category_counts.most_common(20))  # Top 20

        # Description length distribution
        desc_lengths = [
            len(char.get("description", ""))
            for char in characters
            if char.get("description")
        ]
        if desc_lengths:
            distributions["description_lengths"] = {
                "mean": statistics.mean(desc_lengths),
                "median": statistics.median(desc_lengths),
                "std_dev": (
                    statistics.stdev(desc_lengths) if len(desc_lengths) > 1 else 0
                ),
                "min": min(desc_lengths),
                "max": max(desc_lengths),
                "quartiles": self._calculate_quartiles(desc_lengths),
            }

        # Image count distribution
        image_counts = [len(char.get("images", [])) for char in characters]
        distributions["image_counts"] = {
            "mean": statistics.mean(image_counts),
            "median": statistics.median(image_counts),
            "max": max(image_counts),
            "characters_with_0_images": image_counts.count(0),
            "characters_with_1_image": image_counts.count(1),
            "characters_with_multiple_images": sum(
                1 for count in image_counts if count > 1
            ),
        }

        return distributions

    def _calculate_quality_metrics(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate data quality metrics."""
        quality_metrics = {}

        # Completeness metrics
        total_chars = len(characters)
        quality_metrics["completeness"] = {
            "description_fill_rate": sum(
                1 for char in characters if char.get("description")
            )
            / total_chars,
            "categories_fill_rate": sum(
                1 for char in characters if char.get("categories")
            )
            / total_chars,
            "images_fill_rate": sum(1 for char in characters if char.get("images"))
            / total_chars,
            "url_fill_rate": sum(1 for char in characters if char.get("url"))
            / total_chars,
        }

        # Content quality metrics
        desc_chars_with_content = [
            char for char in characters if char.get("description")
        ]
        if desc_chars_with_content:
            quality_metrics["content_quality"] = {
                "avg_description_words": statistics.mean(
                    [
                        len(char["description"].split())
                        for char in desc_chars_with_content
                    ]
                ),
                "descriptions_too_short": sum(
                    1
                    for char in desc_chars_with_content
                    if len(char["description"]) < 50
                )
                / len(desc_chars_with_content),
                "descriptions_adequate": sum(
                    1
                    for char in desc_chars_with_content
                    if 50 <= len(char["description"]) <= 1000
                )
                / len(desc_chars_with_content),
                "descriptions_very_long": sum(
                    1
                    for char in desc_chars_with_content
                    if len(char["description"]) > 1000
                )
                / len(desc_chars_with_content),
            }

        return quality_metrics

    def _calculate_temporal_stats(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate temporal statistics."""
        temporal_stats = {}

        # Extract dates
        dates = []
        for char in characters:
            date_str = char.get("scraped_at") or char.get("updated_at")
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str
                    dates.append(date_obj)
                except Exception:
                    continue

        if dates:
            temporal_stats["date_range"] = {
                "earliest": min(dates).isoformat(),
                "latest": max(dates).isoformat(),
                "span_days": (max(dates) - min(dates)).days,
            }

            # Daily collection patterns
            daily_counts = Counter(date.date() for date in dates)
            temporal_stats["daily_collection"] = {
                "most_active_day": max(daily_counts, key=daily_counts.get).isoformat(),
                "max_daily_count": max(daily_counts.values()),
                "avg_daily_count": statistics.mean(daily_counts.values()),
                "collection_days": len(daily_counts),
            }

        return temporal_stats

    def _calculate_content_stats(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate content-related statistics."""
        content_stats = {}

        # Word frequency analysis from descriptions
        all_words = []
        for char in characters:
            description = char.get("description", "")
            if description:
                # Simple word extraction
                words = description.lower().split()
                # Filter out common words and short words
                filtered_words = [
                    word for word in words if len(word) > 3 and word.isalpha()
                ]
                all_words.extend(filtered_words)

        if all_words:
            word_counts = Counter(all_words)
            content_stats["common_words"] = dict(word_counts.most_common(20))

        # Category analysis
        all_categories = self._get_all_categories(characters)
        if all_categories:
            category_counts = Counter(all_categories)
            content_stats["category_analysis"] = {
                "total_unique_categories": len(category_counts),
                "most_common_categories": dict(category_counts.most_common(10)),
                "rare_categories": [
                    cat for cat, count in category_counts.items() if count == 1
                ],
            }

        return content_stats

    def _calculate_source_stats(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate source-related statistics."""
        source_stats = {}

        # Group by source
        by_source = defaultdict(list)
        for char in characters:
            source = char.get("source", "unknown")
            by_source[source].append(char)

        for source, source_chars in by_source.items():
            stats = {
                "character_count": len(source_chars),
                "percentage": (len(source_chars) / len(characters)) * 100,
                "avg_description_length": self._calculate_avg_description_length(
                    source_chars
                ),
                "completeness_rate": self._calculate_completeness_score(source_chars),
            }
            source_stats[source] = stats

        return source_stats

    def _calculate_growth_analysis(
        self, characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate growth analysis over time."""
        # Extract dates and sort characters by date
        dated_chars = []
        for char in characters:
            date_str = char.get("scraped_at") or char.get("updated_at")
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str
                    dated_chars.append((date_obj, char))
                except Exception:
                    continue

        if not dated_chars:
            return {"error": "No valid dates found for growth analysis"}

        dated_chars.sort(key=lambda x: x[0])

        # Calculate cumulative growth
        cumulative_counts = []
        for i, (date, char) in enumerate(dated_chars):
            cumulative_counts.append({"date": date.date().isoformat(), "count": i + 1})

        # Calculate growth rate
        if len(cumulative_counts) > 1:
            first_date = datetime.fromisoformat(cumulative_counts[0]["date"])
            last_date = datetime.fromisoformat(cumulative_counts[-1]["date"])
            days_span = (last_date - first_date).days

            if days_span > 0:
                growth_rate = len(characters) / days_span  # Characters per day
            else:
                growth_rate = 0
        else:
            growth_rate = 0

        return {
            "cumulative_growth": cumulative_counts,
            "growth_rate_per_day": growth_rate,
            "total_collection_period_days": days_span if "days_span" in locals() else 0,
        }

    def _calculate_completeness_score(self, characters: List[Dict[str, Any]]) -> float:
        """Calculate data completeness score."""
        if not characters:
            return 0.0

        important_fields = ["name", "description", "source", "categories"]
        total_score = 0

        for char in characters:
            field_score = 0
            for field in important_fields:
                if char.get(field):
                    field_score += 1
            total_score += field_score / len(important_fields)

        return total_score / len(characters)

    def _calculate_consistency_score(self, characters: List[Dict[str, Any]]) -> float:
        """Calculate data consistency score."""
        if not characters:
            return 0.0

        # Check for consistent data types and formats
        consistency_checks = 0
        total_checks = 0

        for char in characters:
            # Check if name is string
            if isinstance(char.get("name"), str):
                consistency_checks += 1
            total_checks += 1

            # Check if categories is list
            if (
                isinstance(char.get("categories"), list)
                or char.get("categories") is None
            ):
                consistency_checks += 1
            total_checks += 1

            # Check if images is list
            if isinstance(char.get("images"), list) or char.get("images") is None:
                consistency_checks += 1
            total_checks += 1

        return consistency_checks / total_checks if total_checks > 0 else 0.0

    def _calculate_freshness_score(self, characters: List[Dict[str, Any]]) -> float:
        """Calculate data freshness score."""
        if not characters:
            return 0.0

        now = datetime.now()
        fresh_count = 0
        dated_count = 0

        for char in characters:
            date_str = char.get("scraped_at") or char.get("updated_at")
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str

                    days_old = (now - date_obj.replace(tzinfo=None)).days

                    # Consider data fresh if less than 30 days old
                    if days_old <= 30:
                        fresh_count += 1

                    dated_count += 1
                except Exception:
                    continue

        return (
            fresh_count / dated_count if dated_count > 0 else 0.5
        )  # Neutral score if no dates

    def _calculate_diversity_score(self, characters: List[Dict[str, Any]]) -> float:
        """Calculate data diversity score."""
        if not characters:
            return 0.0

        # Source diversity
        sources = set(char.get("source", "unknown") for char in characters)
        source_diversity = min(len(sources) / 5, 1.0)  # Normalize to 5 sources max

        # Category diversity
        all_categories = self._get_all_categories(characters)
        category_diversity = min(
            len(set(all_categories)) / 50, 1.0
        )  # Normalize to 50 categories max

        return (source_diversity + category_diversity) / 2

    def _calculate_overall_quality_score(
        self, characters: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall quality score."""
        if not characters:
            return 0.0

        # Simple quality heuristics
        quality_score = 0

        for char in characters:
            char_score = 0

            # Name quality
            name = char.get("name", "")
            if name and len(name) > 2:
                char_score += 0.2

            # Description quality
            description = char.get("description", "")
            if description:
                if len(description) >= 50:
                    char_score += 0.3
                if len(description) >= 200:
                    char_score += 0.2

            # Categories
            if char.get("categories") and len(char["categories"]) > 0:
                char_score += 0.2

            # Images
            if char.get("images") and len(char["images"]) > 0:
                char_score += 0.1

            quality_score += char_score

        return quality_score / len(characters)

    def _generate_health_recommendations(
        self, health_metrics: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on health metrics."""
        recommendations = []

        if health_metrics["completeness"] < 0.7:
            recommendations.append(
                "Improve data completeness by filling missing fields"
            )

        if health_metrics["consistency"] < 0.8:
            recommendations.append("Address data consistency issues in field formats")

        if health_metrics["freshness"] < 0.6:
            recommendations.append("Update dataset with more recent data")

        if health_metrics["diversity"] < 0.5:
            recommendations.append("Increase source diversity to reduce bias")

        if health_metrics["quality"] < 0.6:
            recommendations.append("Focus on improving content quality and detail")

        return recommendations

    def _get_all_categories(self, characters: List[Dict[str, Any]]) -> List[str]:
        """Extract all categories from characters."""
        all_categories = []
        for char in characters:
            categories = char.get("categories", [])
            if isinstance(categories, list):
                all_categories.extend(categories)
        return all_categories

    def _calculate_avg_categories(self, characters: List[Dict[str, Any]]) -> float:
        """Calculate average number of categories per character."""
        if not characters:
            return 0.0

        total_categories = 0
        for char in characters:
            categories = char.get("categories", [])
            if isinstance(categories, list):
                total_categories += len(categories)

        return total_categories / len(characters)

    def _calculate_avg_images(self, characters: List[Dict[str, Any]]) -> float:
        """Calculate average number of images per character."""
        if not characters:
            return 0.0

        total_images = 0
        for char in characters:
            images = char.get("images", [])
            if isinstance(images, list):
                total_images += len(images)

        return total_images / len(characters)

    def _calculate_avg_description_length(
        self, characters: List[Dict[str, Any]]
    ) -> float:
        """Calculate average description length."""
        if not characters:
            return 0.0

        total_length = 0
        count = 0

        for char in characters:
            description = char.get("description", "")
            if description:
                total_length += len(description)
                count += 1

        return total_length / count if count > 0 else 0.0

    def _calculate_quartiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate quartiles for a list of values."""
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "q1": sorted_values[n // 4],
            "q2": statistics.median(sorted_values),
            "q3": sorted_values[3 * n // 4],
        }

    def _calculate_daily_trends(
        self, characters: List[Dict[str, Any]], time_field: str
    ) -> Dict[str, Any]:
        """Calculate daily collection trends."""
        daily_counts = defaultdict(int)

        for char in characters:
            date_str = char.get(time_field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str

                    date_key = date_obj.date().isoformat()
                    daily_counts[date_key] += 1
                except Exception:
                    continue

        if not daily_counts:
            return {}

        counts = list(daily_counts.values())
        return {
            "data": dict(daily_counts),
            "avg_per_day": statistics.mean(counts),
            "max_per_day": max(counts),
            "min_per_day": min(counts),
            "std_dev": statistics.stdev(counts) if len(counts) > 1 else 0,
        }

    def _calculate_weekly_trends(
        self, characters: List[Dict[str, Any]], time_field: str
    ) -> Dict[str, Any]:
        """Calculate weekly collection trends."""
        weekly_counts = defaultdict(int)

        for char in characters:
            date_str = char.get(time_field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str

                    # Get ISO week
                    year, week, _ = date_obj.isocalendar()
                    week_key = f"{year}-W{week:02d}"
                    weekly_counts[week_key] += 1
                except Exception:
                    continue

        if not weekly_counts:
            return {}

        counts = list(weekly_counts.values())
        return {
            "data": dict(weekly_counts),
            "avg_per_week": statistics.mean(counts),
            "max_per_week": max(counts),
            "total_weeks": len(weekly_counts),
        }

    def _calculate_monthly_trends(
        self, characters: List[Dict[str, Any]], time_field: str
    ) -> Dict[str, Any]:
        """Calculate monthly collection trends."""
        monthly_counts = defaultdict(int)

        for char in characters:
            date_str = char.get(time_field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str

                    month_key = date_obj.strftime("%Y-%m")
                    monthly_counts[month_key] += 1
                except Exception:
                    continue

        if not monthly_counts:
            return {}

        counts = list(monthly_counts.values())
        return {
            "data": dict(monthly_counts),
            "avg_per_month": statistics.mean(counts),
            "max_per_month": max(counts),
            "total_months": len(monthly_counts),
        }

    def _calculate_growth_rate(
        self, characters: List[Dict[str, Any]], time_field: str
    ) -> Dict[str, Any]:
        """Calculate overall growth rate."""
        dates = []
        for char in characters:
            date_str = char.get(time_field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str
                    dates.append(date_obj)
                except Exception:
                    continue

        if len(dates) < 2:
            return {}

        dates.sort()
        time_span = (dates[-1] - dates[0]).days

        if time_span == 0:
            return {"characters_per_day": len(characters)}

        return {
            "characters_per_day": len(characters) / time_span,
            "time_span_days": time_span,
            "start_date": dates[0].isoformat(),
            "end_date": dates[-1].isoformat(),
        }

    def _identify_peak_periods(
        self, characters: List[Dict[str, Any]], time_field: str
    ) -> Dict[str, Any]:
        """Identify peak collection periods."""
        daily_counts = defaultdict(int)

        for char in characters:
            date_str = char.get(time_field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_str = date_str.replace("Z", "+00:00")
                        date_obj = datetime.fromisoformat(date_str)
                    else:
                        date_obj = date_str

                    date_key = date_obj.date().isoformat()
                    daily_counts[date_key] += 1
                except Exception:
                    continue

        if not daily_counts:
            return {}

        # Find peak days
        sorted_days = sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)
        avg_daily = statistics.mean(daily_counts.values())

        peak_days = [day for day, count in sorted_days if count > avg_daily * 1.5]

        return {
            "peak_days": peak_days[:10],  # Top 10 peak days
            "average_daily_count": avg_daily,
            "highest_single_day": sorted_days[0] if sorted_days else None,
        }


def create_stats_config() -> Dict[str, Any]:
    """Create default configuration for statistics calculator."""
    return {
        "analysis": {
            "include_distributions": True,
            "include_trends": True,
            "include_quality_metrics": True,
            "include_growth_analysis": True,
        },
        "thresholds": {
            "min_data_points": 5,
            "outlier_threshold": 2.0,
            "trend_significance": 0.1,
        },
        "time_periods": {"daily": True, "weekly": True, "monthly": True},
    }
