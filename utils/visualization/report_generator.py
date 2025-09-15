# utils/visualization/report_generator.py
"""
Report generation utilities for character data analysis.
Provides comprehensive HTML and markdown report generation capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json


class ReportGenerator:
    """
    Comprehensive report generator for character data analysis.

    Features:
    - HTML reports with interactive elements
    - Markdown reports for documentation
    - Executive summaries
    - Detailed analysis reports
    - Custom templates and styling
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize report generator.

        Args:
            config: Configuration dictionary with report parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "output": {
                "format": "html",  # 'html', 'markdown', 'both'
                "include_charts": True,
                "include_raw_data": False,
                "responsive_design": True,
            },
            "styling": {
                "theme": "modern",  # 'modern', 'classic', 'minimal'
                "primary_color": "#1f77b4",
                "secondary_color": "#ff7f0e",
                "background_color": "#ffffff",
                "text_color": "#333333",
            },
            "content": {
                "include_executive_summary": True,
                "include_detailed_stats": True,
                "include_recommendations": True,
                "include_methodology": True,
                "max_characters_displayed": 50,
            },
            "export": {
                "output_dir": "storage/exports/reports",
                "filename_template": "character_report_{timestamp}",
                "include_timestamp": True,
            },
        }

        if config:
            self.config.update(config)

    def generate_comprehensive_report(
        self,
        characters: List[Dict[str, Any]],
        stats: Dict[str, Any],
        title: str = "Character Data Analysis Report",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report.

        Args:
            characters: List of character data
            stats: Statistics analysis results
            title: Report title

        Returns:
            Report generation result
        """
        if not characters:
            return {"success": False, "error": "No character data provided"}

        self.logger.info(
            f"Generating comprehensive report for {len(characters)} characters"
        )

        try:
            # Prepare report data
            report_data = {
                "title": title,
                "generated_at": datetime.now().isoformat(),
                "characters": characters,
                "statistics": stats,
                "config": self.config.copy(),
            }

            results = {}

            # Generate HTML report if configured
            if self.config["output"]["format"] in ["html", "both"]:
                html_result = self._generate_html_report(report_data)
                results["html"] = html_result

            # Generate Markdown report if configured
            if self.config["output"]["format"] in ["markdown", "both"]:
                md_result = self._generate_markdown_report(report_data)
                results["markdown"] = md_result

            return {
                "success": True,
                "reports": results,
                "characters_analyzed": len(characters),
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            error_msg = f"Report generation failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def generate_executive_summary(
        self, characters: List[Dict[str, Any]], stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate executive summary report.

        Args:
            characters: List of character data
            stats: Statistics analysis results

        Returns:
            Executive summary generation result
        """
        try:
            summary_data = {
                "title": "Executive Summary - Character Data Analysis",
                "generated_at": datetime.now().isoformat(),
                "key_metrics": self._extract_key_metrics(stats),
                "insights": self._generate_insights(characters, stats),
                "recommendations": self._generate_recommendations(stats),
            }

            # Generate HTML summary
            html_content = self._create_executive_summary_html(summary_data)

            # Save to file
            output_path = self._save_report(html_content, "executive_summary", "html")

            return {
                "success": True,
                "output_path": output_path,
                "summary_data": summary_data,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Executive summary generation failed: {e}",
            }

    def generate_source_comparison_report(
        self, characters: List[Dict[str, Any]], source_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate source comparison report.

        Args:
            characters: List of character data
            source_performance: Source performance analysis

        Returns:
            Source comparison report result
        """
        try:
            report_data = {
                "title": "Data Source Performance Comparison",
                "generated_at": datetime.now().isoformat(),
                "source_metrics": source_performance["source_metrics"],
                "ranking": source_performance["ranking"],
                "best_source": source_performance["best_source"],
                "worst_source": source_performance["worst_source"],
            }

            # Generate HTML report
            html_content = self._create_source_comparison_html(report_data)

            # Save to file
            output_path = self._save_report(html_content, "source_comparison", "html")

            return {
                "success": True,
                "output_path": output_path,
                "report_data": report_data,
            }

        except Exception as e:
            return {"success": False, "error": f"Source comparison report failed: {e}"}

    def _generate_html_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HTML report."""
        try:
            html_content = self._create_html_template(report_data)

            # Add sections
            html_content += self._create_executive_summary_section(report_data)
            html_content += self._create_statistics_section(report_data)
            html_content += self._create_characters_section(report_data)
            html_content += self._create_recommendations_section(report_data)

            # Close HTML
            html_content += self._get_html_footer()

            # Save to file
            output_path = self._save_report(
                html_content, "comprehensive_report", "html"
            )

            return {"success": True, "output_path": output_path, "format": "html"}

        except Exception as e:
            return {"success": False, "error": f"HTML report generation failed: {e}"}

    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Markdown report."""
        try:
            md_content = self._create_markdown_header(report_data)
            md_content += self._create_markdown_summary(report_data)
            md_content += self._create_markdown_statistics(report_data)
            md_content += self._create_markdown_characters(report_data)
            md_content += self._create_markdown_methodology(report_data)

            # Save to file
            output_path = self._save_report(md_content, "comprehensive_report", "md")

            return {"success": True, "output_path": output_path, "format": "markdown"}

        except Exception as e:
            return {
                "success": False,
                "error": f"Markdown report generation failed: {e}",
            }

    def _create_html_template(self, report_data: Dict[str, Any]) -> str:
        """Create HTML template with styling."""
        title = report_data["title"]
        theme = self.config["styling"]["theme"]

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>{title}</h1>
            <p class="generated-date">Generated on: {datetime.fromisoformat(report_data['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        <nav class="table-of-contents">
            <h2>Table of Contents</h2>
            <ul>
                <li><a href="#executive-summary">Executive Summary</a></li>
                <li><a href="#statistics">Statistics Overview</a></li>
                <li><a href="#characters">Character Analysis</a></li>
                <li><a href="#recommendations">Recommendations</a></li>
            </ul>
        </nav>
"""
        return html

    def _create_executive_summary_section(self, report_data: Dict[str, Any]) -> str:
        """Create executive summary section."""
        stats = report_data.get("statistics", {})
        overview = stats.get("overview", {})

        html = """
        <section id="executive-summary" class="section">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="metric-card">
                    <h3>Total Characters</h3>
                    <div class="metric-value">{}</div>
                </div>
                <div class="metric-card">
                    <h3>Data Sources</h3>
                    <div class="metric-value">{}</div>
                </div>
                <div class="metric-card">
                    <h3>Completion Rate</h3>
                    <div class="metric-value">{:.1f}%</div>
                </div>
                <div class="metric-card">
                    <h3>Avg Description Length</h3>
                    <div class="metric-value">{:.0f} chars</div>
                </div>
            </div>
        </section>
""".format(
            overview.get("total_characters", 0),
            overview.get("unique_sources", 0),
            (
                overview.get("characters_with_descriptions", 0)
                / max(overview.get("total_characters", 1), 1)
            )
            * 100,
            overview.get("avg_description_length", 0),
        )
        return html

    def _create_statistics_section(self, report_data: Dict[str, Any]) -> str:
        """Create statistics section."""
        stats = report_data.get("statistics", {})
        distributions = stats.get("distributions", {})

        html = """
        <section id="statistics" class="section">
            <h2>Statistics Overview</h2>

            <div class="stats-subsection">
                <h3>Source Distribution</h3>
                <table class="stats-table">
                    <thead>
                        <tr><th>Source</th><th>Count</th><th>Percentage</th></tr>
                    </thead>
                    <tbody>
"""

        # Add source distribution data
        source_dist = distributions.get("sources", {})
        total_chars = sum(source_dist.values()) if source_dist else 1

        for source, count in source_dist.items():
            percentage = (count / total_chars) * 100
            html += (
                f"<tr><td>{source}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
            )

        html += """
                    </tbody>
                </table>
            </div>

            <div class="stats-subsection">
                <h3>Category Distribution</h3>
                <div class="category-list">
"""

        # Add top categories
        categories = distributions.get("categories", {})
        top_categories = list(categories.items())[:10]

        for category, count in top_categories:
            html += f'<span class="category-tag">{category} ({count})</span>'

        html += """
                </div>
            </div>
        </section>
"""
        return html

    def _create_characters_section(self, report_data: Dict[str, Any]) -> str:
        """Create characters section."""
        characters = report_data.get("characters", [])
        max_display = self.config["content"]["max_characters_displayed"]

        html = f"""
        <section id="characters" class="section">
            <h2>Character Analysis</h2>
            <p>Showing top {min(len(characters), max_display)} characters:</p>

            <div class="characters-grid">
"""

        for char in characters[:max_display]:
            name = char.get("name", "Unknown")
            source = char.get("source", "Unknown")
            description = char.get("description", "No description available")

            # Truncate description
            if len(description) > 200:
                description = description[:200] + "..."

            categories = char.get("categories", [])
            category_str = ", ".join(categories[:3]) if categories else "None"

            html += f"""
                <div class="character-card">
                    <h4>{name}</h4>
                    <p class="character-source">Source: {source}</p>
                    <p class="character-description">{description}</p>
                    <p class="character-categories">Categories: {category_str}</p>
                </div>
"""

        html += """
            </div>
        </section>
"""
        return html

    def _create_recommendations_section(self, report_data: Dict[str, Any]) -> str:
        """Create recommendations section."""
        stats = report_data.get("statistics", {})
        recommendations = self._generate_recommendations(stats)

        html = """
        <section id="recommendations" class="section">
            <h2>Recommendations</h2>
            <ul class="recommendations-list">
"""

        for rec in recommendations:
            html += f"<li>{rec}</li>"

        html += """
            </ul>
        </section>
"""
        return html

    def _get_css_styles(self) -> str:
        """Get CSS styles for HTML reports."""
        primary_color = self.config["styling"]["primary_color"]
        secondary_color = self.config["styling"]["secondary_color"]

        return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}

        .report-header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, {primary_color}, {secondary_color});
            color: white;
            border-radius: 8px;
        }}

        .report-header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .generated-date {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .table-of-contents {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}

        .table-of-contents ul {{
            list-style-type: none;
        }}

        .table-of-contents li {{
            margin: 8px 0;
        }}

        .table-of-contents a {{
            color: {primary_color};
            text-decoration: none;
            font-weight: 500;
        }}

        .table-of-contents a:hover {{
            text-decoration: underline;
        }}

        .section {{
            margin-bottom: 40px;
            padding: 20px;
            border-left: 4px solid {primary_color};
        }}

        .section h2 {{
            color: {primary_color};
            margin-bottom: 20px;
            font-size: 1.8em;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #e9ecef;
        }}

        .metric-card h3 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: {primary_color};
        }}

        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        .stats-table th,
        .stats-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        .stats-table th {{
            background-color: {primary_color};
            color: white;
        }}

        .stats-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        .category-list {{
            margin: 20px 0;
        }}

        .category-tag {{
            display: inline-block;
            background: {secondary_color};
            color: white;
            padding: 5px 10px;
            margin: 5px;
            border-radius: 15px;
            font-size: 0.9em;
        }}

        .characters-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .character-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}

        .character-card h4 {{
            color: {primary_color};
            margin-bottom: 10px;
        }}

        .character-source {{
            color: #666;
            font-style: italic;
            margin-bottom: 10px;
        }}

        .character-description {{
            margin-bottom: 10px;
        }}

        .character-categories {{
            color: #666;
            font-size: 0.9em;
        }}

        .recommendations-list {{
            list-style-type: none;
        }}

        .recommendations-list li {{
            background: #e8f4fd;
            margin: 10px 0;
            padding: 15px;
            border-left: 4px solid {primary_color};
            border-radius: 4px;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}

            .summary-grid {{
                grid-template-columns: 1fr;
            }}

            .characters-grid {{
                grid-template-columns: 1fr;
            }}
        }}
"""

    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return """
    </div>
</body>
</html>
"""

    def _create_markdown_header(self, report_data: Dict[str, Any]) -> str:
        """Create Markdown report header."""
        title = report_data["title"]
        generated_at = datetime.fromisoformat(report_data["generated_at"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return f"""# {title}

**Generated on:** {generated_at}

## Table of Contents

- [Executive Summary](#executive-summary)
- [Statistics Overview](#statistics-overview)
- [Character Analysis](#character-analysis)
- [Methodology](#methodology)

---

"""

    def _create_markdown_summary(self, report_data: Dict[str, Any]) -> str:
        """Create Markdown executive summary."""
        stats = report_data.get("statistics", {})
        overview = stats.get("overview", {})

        return f"""## Executive Summary

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Characters | {overview.get('total_characters', 0)} |
| Unique Sources | {overview.get('unique_sources', 0)} |
| Characters with Descriptions | {overview.get('characters_with_descriptions', 0)} |
| Characters with Images | {overview.get('characters_with_images', 0)} |
| Average Description Length | {overview.get('avg_description_length', 0):.0f} characters |

"""

    def _create_markdown_statistics(self, report_data: Dict[str, Any]) -> str:
        """Create Markdown statistics section."""
        stats = report_data.get("statistics", {})
        distributions = stats.get("distributions", {})

        md = "## Statistics Overview\n\n"

        # Source distribution
        md += "### Source Distribution\n\n"
        source_dist = distributions.get("sources", {})
        if source_dist:
            md += "| Source | Count | Percentage |\n|--------|-------|------------|\n"
            total = sum(source_dist.values())
            for source, count in source_dist.items():
                percentage = (count / total * 100) if total > 0 else 0
                md += f"| {source} | {count} | {percentage:.1f}% |\n"

        md += "\n"

        # Top categories
        md += "### Top Categories\n\n"
        categories = distributions.get("categories", {})
        if categories:
            top_categories = list(categories.items())[:10]
            for category, count in top_categories:
                md += f"- **{category}**: {count} characters\n"

        md += "\n"

        return md

    def _create_markdown_characters(self, report_data: Dict[str, Any]) -> str:
        """Create Markdown characters section."""
        characters = report_data.get("characters", [])
        max_display = min(len(characters), 10)  # Limit for markdown

        md = f"## Character Analysis\n\nShowing top {max_display} characters:\n\n"

        for i, char in enumerate(characters[:max_display], 1):
            name = char.get("name", "Unknown")
            source = char.get("source", "Unknown")
            description = char.get("description", "No description available")

            # Truncate description for markdown
            if len(description) > 150:
                description = description[:150] + "..."

            categories = char.get("categories", [])
            category_str = ", ".join(categories[:3]) if categories else "None"

            md += f"""### {i}. {name}

- **Source**: {source}
- **Categories**: {category_str}
- **Description**: {description}

"""

        return md

    def _create_markdown_methodology(self, report_data: Dict[str, Any]) -> str:
        """Create Markdown methodology section."""
        return """## Methodology

### Data Collection
- Data was collected from multiple fandom wiki sources
- Each character record includes name, description, categories, and source information
- Images and additional metadata are preserved when available

### Analysis Process
1. **Data Validation**: All records are validated for completeness and consistency
2. **Statistical Analysis**: Descriptive statistics are calculated for all numerical fields
3. **Distribution Analysis**: Source and category distributions are analyzed
4. **Quality Assessment**: Data quality scores are calculated based on completeness and content richness

### Metrics Definitions
- **Completeness Rate**: Percentage of characters with description content
- **Source Diversity**: Number of unique data sources
- **Category Coverage**: Average number of categories per character
- **Content Quality**: Based on description length and detail level

---

*Report generated by Fandom Scraper Analysis Tool*
"""

    def _create_executive_summary_html(self, summary_data: Dict[str, Any]) -> str:
        """Create executive summary HTML."""
        title = summary_data["title"]

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{self._get_css_styles()}</style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>{title}</h1>
            <p class="generated-date">Generated on: {datetime.fromisoformat(summary_data['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <section class="section">
            <h2>Key Metrics</h2>
            <div class="summary-grid">
"""

        # Add key metrics
        for metric_name, metric_value in summary_data["key_metrics"].items():
            html += f"""
                <div class="metric-card">
                    <h3>{metric_name.replace('_', ' ').title()}</h3>
                    <div class="metric-value">{metric_value}</div>
                </div>
"""

        html += """
            </div>
        </section>

        <section class="section">
            <h2>Key Insights</h2>
            <ul class="recommendations-list">
"""

        # Add insights
        for insight in summary_data["insights"]:
            html += f"<li>{insight}</li>"

        html += """
            </ul>
        </section>

        <section class="section">
            <h2>Recommendations</h2>
            <ul class="recommendations-list">
"""

        # Add recommendations
        for rec in summary_data["recommendations"]:
            html += f"<li>{rec}</li>"

        html += """
            </ul>
        </section>
    </div>
</body>
</html>
"""
        return html

    def _create_source_comparison_html(self, report_data: Dict[str, Any]) -> str:
        """Create source comparison HTML."""
        title = report_data["title"]

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{self._get_css_styles()}</style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>{title}</h1>
            <p class="generated-date">Generated on: {datetime.fromisoformat(report_data['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <section class="section">
            <h2>Source Performance Ranking</h2>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Source</th>
                        <th>Performance Score</th>
                        <th>Character Count</th>
                        <th>Quality Score</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Add ranking data
        for i, source_rank in enumerate(report_data["ranking"], 1):
            source = source_rank["source"]
            score = source_rank["score"]
            metrics = report_data["source_metrics"][source]

            html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{source}</td>
                    <td>{score:.3f}</td>
                    <td>{metrics['character_count']}</td>
                    <td>{metrics['quality_score']:.3f}</td>
                </tr>
"""

        html += """
                </tbody>
            </table>
        </section>

        <section class="section">
            <h2>Best Performing Source</h2>
            <div class="metric-card">
                <h3>Top Source</h3>
                <div class="metric-value">{}</div>
            </div>
        </section>
    </div>
</body>
</html>
""".format(
            report_data["best_source"]
        )

        return html

    def _extract_key_metrics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for executive summary."""
        overview = stats.get("overview", {})

        return {
            "total_characters": overview.get("total_characters", 0),
            "unique_sources": overview.get("unique_sources", 0),
            "completion_rate": f"{(overview.get('characters_with_descriptions', 0) / max(overview.get('total_characters', 1), 1)) * 100:.1f}%",
            "avg_categories": f"{overview.get('avg_categories_per_character', 0):.1f}",
            "image_coverage": f"{(overview.get('characters_with_images', 0) / max(overview.get('total_characters', 1), 1)) * 100:.1f}%",
        }

    def _generate_insights(
        self, characters: List[Dict[str, Any]], stats: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from the data analysis."""
        insights = []
        overview = stats.get("overview", {})
        distributions = stats.get("distributions", {})

        # Source diversity insight
        unique_sources = overview.get("unique_sources", 0)
        if unique_sources == 1:
            insights.append(
                "Data comes from a single source, which may limit diversity and introduce bias."
            )
        elif unique_sources >= 3:
            insights.append(
                f"Good source diversity with {unique_sources} different sources providing varied perspectives."
            )

        # Completeness insight
        completion_rate = (
            overview.get("characters_with_descriptions", 0)
            / max(overview.get("total_characters", 1), 1)
        ) * 100
        if completion_rate >= 90:
            insights.append(
                "Excellent data completeness with most characters having detailed descriptions."
            )
        elif completion_rate >= 70:
            insights.append(
                "Good data completeness, though some characters lack detailed descriptions."
            )
        else:
            insights.append(
                "Data completeness needs improvement - many characters lack descriptions."
            )

        # Category distribution insight
        categories = distributions.get("categories", {})
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            insights.append(
                f"Most common character category is '{top_category[0]}' with {top_category[1]} characters."
            )

        # Image coverage insight
        image_rate = (
            overview.get("characters_with_images", 0)
            / max(overview.get("total_characters", 1), 1)
        ) * 100
        if image_rate >= 80:
            insights.append(
                "Excellent visual content with most characters having associated images."
            )
        elif image_rate >= 50:
            insights.append(
                "Moderate visual content coverage - consider adding more character images."
            )
        else:
            insights.append(
                "Low visual content coverage - images would enhance the dataset significantly."
            )

        return insights

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on statistics."""
        recommendations = []
        overview = stats.get("overview", {})
        quality_metrics = stats.get("quality_metrics", {})

        # Completeness recommendations
        completion_rate = (
            overview.get("characters_with_descriptions", 0)
            / max(overview.get("total_characters", 1), 1)
        ) * 100
        if completion_rate < 80:
            recommendations.append(
                "Focus on improving data completeness by adding descriptions to characters without them."
            )

        # Source diversity recommendations
        if overview.get("unique_sources", 0) < 3:
            recommendations.append(
                "Consider expanding to additional data sources to increase diversity and reduce bias."
            )

        # Content quality recommendations
        avg_desc_length = overview.get("avg_description_length", 0)
        if avg_desc_length < 100:
            recommendations.append(
                "Enhance description quality by providing more detailed character information."
            )

        # Image recommendations
        image_rate = (
            overview.get("characters_with_images", 0)
            / max(overview.get("total_characters", 1), 1)
        ) * 100
        if image_rate < 70:
            recommendations.append(
                "Improve visual content by adding character images where missing."
            )

        # Category recommendations
        avg_categories = overview.get("avg_categories_per_character", 0)
        if avg_categories < 2:
            recommendations.append(
                "Enhance categorization by adding more relevant categories to characters."
            )

        return recommendations

    def _save_report(self, content: str, report_type: str, file_extension: str) -> str:
        """Save report content to file."""
        # Ensure output directory exists
        output_dir = Path(self.config["export"]["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        if self.config["export"]["include_timestamp"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_type}_{timestamp}.{file_extension}"
        else:
            filename = f"{report_type}.{file_extension}"

        output_path = output_dir / filename

        # Write content
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(output_path)


def create_report_config() -> Dict[str, Any]:
    """Create default configuration for report generator."""
    return {
        "output": {
            "format": "html",
            "include_charts": True,
            "include_raw_data": False,
            "responsive_design": True,
        },
        "styling": {
            "theme": "modern",
            "primary_color": "#1f77b4",
            "secondary_color": "#ff7f0e",
            "background_color": "#ffffff",
            "text_color": "#333333",
        },
        "content": {
            "include_executive_summary": True,
            "include_detailed_stats": True,
            "include_recommendations": True,
            "include_methodology": True,
            "max_characters_displayed": 50,
        },
        "export": {
            "output_dir": "storage/exports/reports",
            "filename_template": "character_report_{timestamp}",
            "include_timestamp": True,
        },
    }
