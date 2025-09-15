# utils/visualization/chart_generator.py
"""
Chart generation utilities for character data visualization.
Provides various chart types and customization options.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json


class ChartGenerator:
    """
    Comprehensive chart generator for character data visualization.

    Features:
    - Multiple chart types (bar, pie, line, scatter, histogram)
    - Data aggregation and processing
    - Customizable styling and themes
    - Export to various formats (PNG, SVG, HTML)
    - Interactive charts with plotly
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize chart generator.

        Args:
            config: Configuration dictionary with chart parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            'default_theme': 'plotly',
            'output_format': 'html',  # 'html', 'png', 'svg', 'json'
            'chart_size': {
                'width': 800,
                'height': 600
            },
            'colors': {
                'primary': '#1f77b4',
                'secondary': '#ff7f0e',
                'success': '#2ca02c',
                'warning': '#d62728',
                'info': '#9467bd',
                'palette': [
                    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
                ]
            },
            'styling': {
                'title_font_size': 18,
                'axis_font_size': 12,
                'legend_font_size': 10,
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
            },
            'export': {
                'output_dir': 'storage/exports/charts',
                'include_data': True,
                'responsive': True
            }
        }

        if config:
            self.config.update(config)

        # Check for plotting libraries
        self.plotly_available = False
        self.matplotlib_available = False

        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.offline import plot
            self.go = go
            self.px = px
            self.plot = plot
            self.plotly_available = True
            self.logger.info("Plotly available for interactive charts")
        except ImportError:
            self.logger.warning("Plotly not available - limited chart functionality")

        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            self.plt = plt
            self.sns = sns
            self.matplotlib_available = True
            self.logger.info("Matplotlib/Seaborn available for static charts")
        except ImportError:
            self.logger.warning("Matplotlib not available - limited static chart functionality")

    def generate_character_distribution(self, characters: List[Dict[str, Any]],
                                      group_by: str = 'source') -> Dict[str, Any]:
        """
        Generate character distribution chart.

        Args:
            characters: List of character data
            group_by: Field to group characters by

        Returns:
            Chart generation result
        """
        if not characters:
            return {'success': False, 'error': 'No character data provided'}

        self.logger.info(f"Generating character distribution chart grouped by '{group_by}'")

        try:
            # Aggregate data
            distribution = self._aggregate_by_field(characters, group_by)

            if not self.plotly_available:
                return {'success': False, 'error': 'Plotly not available for chart generation'}

            # Create pie chart
            fig = self.go.Figure(data=[
                self.go.Pie(
                    labels=list(distribution.keys()),
                    values=list(distribution.values()),
                    hole=0.3,  # Donut chart
                    textinfo='label+percent',
                    textposition='outside',
                    marker=dict(colors=self.config['colors']['palette'])
                )
            ])

            fig.update_layout(
                title=f'Character Distribution by {group_by.title()}',
                font=dict(size=self.config['styling']['axis_font_size']),
                width=self.config['chart_size']['width'],
                height=self.config['chart_size']['height'],
                margin=self.config['styling']['margin']
            )

            # Generate output
            result = self._export_chart(fig, f'character_distribution_{group_by}')
            result['chart_type'] = 'pie'
            result['data_summary'] = {
                'total_characters': len(characters),
                'groups': len(distribution),
                'distribution': distribution
            }

            return result

        except Exception as e:
        except Exception as e:
            error_msg = f"Failed to generate timeline chart: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def generate_quality_overview(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate data quality overview charts.

        Args:
            characters: List of character data with quality scores

        Returns:
            Chart generation result
        """
        if not characters:
            return {'success': False, 'error': 'No character data provided'}

        self.logger.info("Generating data quality overview chart")

        try:
            # Extract quality data
            quality_data = self._extract_quality_data(characters)

            if not quality_data['scores']:
                return {'success': False, 'error': 'No quality scores found in data'}

            if not self.plotly_available:
                return {'success': False, 'error': 'Plotly not available for chart generation'}

            # Create histogram of quality scores
            fig = self.go.Figure(data=[
                self.go.Histogram(
                    x=quality_data['scores'],
                    nbinsx=20,
                    marker=dict(color=self.config['colors']['primary'], opacity=0.7),
                    name='Quality Scores'
                )
            ])

            fig.update_layout(
                title='Data Quality Score Distribution',
                xaxis_title='Quality Score',
                yaxis_title='Number of Characters',
                font=dict(size=self.config['styling']['axis_font_size']),
                width=self.config['chart_size']['width'],
                height=self.config['chart_size']['height'],
                margin=self.config['styling']['margin']
            )

            # Add average line
            avg_score = sum(quality_data['scores']) / len(quality_data['scores'])
            fig.add_vline(
                x=avg_score,
                line_dash="dash",
                line_color=self.config['colors']['warning'],
                annotation_text=f"Average: {avg_score:.2f}"
            )

            result = self._export_chart(fig, 'quality_overview')
            result['chart_type'] = 'histogram'
            result['data_summary'] = {
                'total_characters': len(characters),
                'average_quality': avg_score,
                'quality_distribution': quality_data['distribution'],
                'scores_available': len(quality_data['scores'])
            }

            return result

        except Exception as e:
            error_msg = f"Failed to generate quality overview: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def generate_category_analysis(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate category analysis chart.

        Args:
            characters: List of character data

        Returns:
            Chart generation result
        """
        if not characters:
            return {'success': False, 'error': 'No character data provided'}

        self.logger.info("Generating category analysis chart")

        try:
            # Extract and count categories
            category_counts = self._count_categories(characters)

            if not category_counts:
                return {'success': False, 'error': 'No categories found in character data'}

            if not self.plotly_available:
                return {'success': False, 'error': 'Plotly not available for chart generation'}

            # Sort categories by frequency
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

            # Take top 15 categories to avoid overcrowding
            top_categories = sorted_categories[:15]
            categories, counts = zip(*top_categories) if top_categories else ([], [])

            # Create horizontal bar chart for better label readability
            fig = self.go.Figure(data=[
                self.go.Bar(
                    y=categories,
                    x=counts,
                    orientation='h',
                    marker=dict(color=self.config['colors']['secondary']),
                    text=counts,
                    textposition='auto'
                )
            ])

            fig.update_layout(
                title='Most Common Character Categories',
                xaxis_title='Number of Characters',
                yaxis_title='Category',
                font=dict(size=self.config['styling']['axis_font_size']),
                width=self.config['chart_size']['width'],
                height=max(400, len(categories) * 30),  # Dynamic height based on categories
                margin=self.config['styling']['margin']
            )

            result = self._export_chart(fig, 'category_analysis')
            result['chart_type'] = 'horizontal_bar'
            result['data_summary'] = {
                'total_categories': len(category_counts),
                'characters_with_categories': sum(1 for char in characters if char.get('categories')),
                'most_common_category': categories[0] if categories else None,
                'top_categories': dict(top_categories)
            }

            return result

        except Exception as e:
            error_msg = f"Failed to generate category analysis: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def generate_multi_chart_dashboard(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a dashboard with multiple charts.

        Args:
            characters: List of character data

        Returns:
            Dashboard generation result
        """
        if not characters:
            return {'success': False, 'error': 'No character data provided'}

        self.logger.info("Generating multi-chart dashboard")

        try:
            if not self.plotly_available:
                return {'success': False, 'error': 'Plotly not available for dashboard generation'}

            from plotly.subplots import make_subplots

            # Create subplot layout
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Source Distribution', 'Quality Scores', 'Collection Timeline', 'Top Categories'),
                specs=[[{"type": "pie"}, {"type": "histogram"}],
                       [{"type": "scatter"}, {"type": "bar"}]]
            )

            # 1. Source distribution (pie chart)
            source_dist = self._aggregate_by_field(characters, 'source')
            if source_dist:
                fig.add_trace(
                    self.go.Pie(
                        labels=list(source_dist.keys()),
                        values=list(source_dist.values()),
                        name="Sources"
                    ),
                    row=1, col=1
                )

            # 2. Quality scores (histogram)
            quality_data = self._extract_quality_data(characters)
            if quality_data['scores']:
                fig.add_trace(
                    self.go.Histogram(
                        x=quality_data['scores'],
                        name="Quality",
                        nbinsx=15
                    ),
                    row=1, col=2
                )

            # 3. Timeline (line chart)
            timeline_data = self._process_timeline_data(characters, 'scraped_at')
            if timeline_data:
                dates = list(timeline_data.keys())
                counts = list(timeline_data.values())
                fig.add_trace(
                    self.go.Scatter(
                        x=dates,
                        y=counts,
                        mode='lines+markers',
                        name="Timeline"
                    ),
                    row=2, col=1
                )

            # 4. Top categories (bar chart)
            category_counts = self._count_categories(characters)
            if category_counts:
                top_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                cats, counts = zip(*top_cats) if top_cats else ([], [])
                fig.add_trace(
                    self.go.Bar(
                        x=cats,
                        y=counts,
                        name="Categories"
                    ),
                    row=2, col=2
                )

            # Update layout
            fig.update_layout(
                title_text="Character Data Dashboard",
                showlegend=False,
                height=800,
                width=1200,
                margin=self.config['styling']['margin']
            )

            result = self._export_chart(fig, 'dashboard')
            result['chart_type'] = 'dashboard'
            result['data_summary'] = {
                'total_characters': len(characters),
                'charts_included': ['source_distribution', 'quality_scores', 'timeline', 'categories']
            }

            return result

        except Exception as e:
            error_msg = f"Failed to generate dashboard: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def _aggregate_by_field(self, characters: List[Dict[str, Any]], field: str) -> Dict[str, int]:
        """Aggregate character data by specified field."""
        aggregation = {}

        for character in characters:
            value = character.get(field, 'Unknown')
            if value is None:
                value = 'Unknown'

            value_str = str(value)
            aggregation[value_str] = aggregation.get(value_str, 0) + 1

        return aggregation

    def _process_timeline_data(self, characters: List[Dict[str, Any]],
                              date_field: str) -> Dict[str, int]:
        """Process timeline data from characters."""
        from datetime import datetime
        from collections import defaultdict

        daily_counts = defaultdict(int)

        for character in characters:
            date_str = character.get(date_field)
            if not date_str:
                continue

            try:
                # Parse date string
                if isinstance(date_str, str):
                    date_str = date_str.replace('Z', '+00:00')
                    date_obj = datetime.fromisoformat(date_str)
                else:
                    date_obj = date_str

                # Group by date (without time)
                date_key = date_obj.date().isoformat()
                daily_counts[date_key] += 1

            except Exception as e:
                self.logger.warning(f"Failed to parse date '{date_str}': {e}")
                continue

        # Sort by date
        sorted_dates = sorted(daily_counts.items())
        return dict(sorted_dates)

    def _extract_quality_data(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract quality scores and distribution from characters."""
        scores = []
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}

        for character in characters:
            # Look for quality score in various possible locations
            score = None

            # Check common quality score locations
            quality_locations = [
                'quality_score',
                'overall_score',
                '_quality_metadata.overall_score',
                'fusion_metadata.confidence_score'
            ]

            for location in quality_locations:
                if '.' in location:
                    # Nested field
                    parts = location.split('.')
                    value = character
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                    if value is not None:
                        score = value
                        break
                else:
                    # Direct field
                    score = character.get(location)
                    if score is not None:
                        break

            if score is not None:
                try:
                    score_float = float(score)
                    scores.append(score_float)

                    # Categorize score
                    if score_float >= 0.9:
                        distribution['excellent'] += 1
                    elif score_float >= 0.75:
                        distribution['good'] += 1
                    elif score_float >= 0.6:
                        distribution['fair'] += 1
                    else:
                        distribution['poor'] += 1

                except (ValueError, TypeError):
                    continue

        return {
            'scores': scores,
            'distribution': distribution
        }

    def _count_categories(self, characters: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count occurrences of each category across all characters."""
        category_counts = {}

        for character in characters:
            categories = character.get('categories', [])
            if not isinstance(categories, list):
                continue

            for category in categories:
                if category and isinstance(category, str):
                    category = category.strip()
                    if category:
                        category_counts[category] = category_counts.get(category, 0) + 1

        return category_counts

    def _export_chart(self, fig, filename: str) -> Dict[str, Any]:
        """Export chart to configured format."""
        try:
            output_dir = Path(self.config['export']['output_dir'])
            output_dir.mkdir(parents=True, exist_ok=True)

            format_type = self.config['output_format']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if format_type == 'html':
                output_path = output_dir / f"{filename}_{timestamp}.html"

                # Configure HTML output
                config = {
                    'displayModeBar': True,
                    'responsive': self.config['export']['responsive']
                }

                self.plot(
                    fig,
                    filename=str(output_path),
                    auto_open=False,
                    config=config,
                    include_plotlyjs='cdn'
                )

            elif format_type == 'json':
                output_path = output_dir / f"{filename}_{timestamp}.json"

                # Export as JSON
                chart_data = {
                    'data': fig.data,
                    'layout': fig.layout,
                    'config': self.config,
                    'generated_at': datetime.now().isoformat()
                }

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(chart_data, f, indent=2, default=str)

            else:
                # For PNG/SVG, would need kaleido package
                return {
                    'success': False,
                    'error': f'Export format {format_type} requires additional dependencies'
                }

            file_size = output_path.stat().st_size

            return {
                'success': True,
                'output_path': str(output_path),
                'file_size': file_size,
                'format': format_type,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': f'Chart export failed: {e}'}

    def generate_source_statistics(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate source statistics bar chart.

        Args:
            characters: List of character data

        Returns:
            Chart generation result
        """
        if not characters:
            return {'success': False, 'error': 'No character data provided'}

        self.logger.info("Generating source statistics chart")

        try:
            # Aggregate by source
            source_stats = self._aggregate_by_field(characters, 'source')

            if not self.plotly_available:
                return {'success': False, 'error': 'Plotly not available for chart generation'}

            # Sort by count
            sorted_sources = sorted(source_stats.items(), key=lambda x: x[1], reverse=True)
            sources, counts = zip(*sorted_sources) if sorted_sources else ([], [])

            # Create bar chart
            fig = self.go.Figure(data=[
                self.go.Bar(
                    x=sources,
                    y=counts,
                    marker=dict(color=self.config['colors']['primary']),
                    text=counts,
                    textposition='auto'
                )
            ])

            fig.update_layout(
                title='Character Count by Source',
                xaxis_title='Source',
                yaxis_title='Number of Characters',
                font=dict(size=self.config['styling']['axis_font_size']),
                width=self.config['chart_size']['width'],
                height=self.config['chart_size']['height'],
                margin=self.config['styling']['margin']
            )

            # Rotate x-axis labels if too many sources
            if len(sources) > 5:
                fig.update_xaxes(tickangle=45)

            result = self._export_chart(fig, 'source_statistics')
            result['chart_type'] = 'bar'
            result['data_summary'] = {
                'total_sources': len(source_stats),
                'total_characters': sum(source_stats.values()),
                'top_source': sources[0] if sources else None,
                'statistics': dict(sorted_sources)
            }

            return result

        except Exception as e:
            error_msg = f"Failed to generate source statistics chart: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def generate_timeline_chart(self, characters: List[Dict[str, Any]],
                                date_field: str = 'scraped_at') -> Dict[str, Any]:
        """
        Generate timeline chart showing character data collection over time.

        Args:
            characters: List of character data
            date_field: Field containing date information

        Returns:
            Chart generation result
        """
        if not characters:
            return {'success': False, 'error': 'No character data provided'}

        self.logger.info(f"Generating timeline chart based on '{date_field}'")

        try:
            # Extract and process dates
            timeline_data = self._process_timeline_data(characters, date_field)

            if not timeline_data:
                return {'success': False, 'error': f'No valid dates found in field "{date_field}"'}

            if not self.plotly_available:
                return {'success': False, 'error': 'Plotly not available for chart generation'}

            dates = list(timeline_data.keys())
            counts = list(timeline_data.values())

            # Create line chart
            fig = self.go.Figure(data=[
                self.go.Scatter(
                    x=dates,
                    y=counts,
                    mode='lines+markers',
                    line=dict(color=self.config['colors']['primary'], width=2),
                    marker=dict(size=6),
                    fill='tonexty' if len(dates) > 1 else None
                )
            ])

            fig.update_layout(
                title='Character Data Collection Timeline',
                xaxis_title='Date',
                yaxis_title='Characters Collected',
                font=dict(size=self.config['styling']['axis_font_size']),
                width=self.config['chart_size']['width'],
                height=self.config['chart_size']['height'],
                margin=self.config['styling']['margin']
            )

            result = self._export_chart(fig, 'timeline_chart')
            result['chart_type'] = 'line'
            result['data_summary'] = {
                'date_range': {
                    'start': min(dates) if dates else None,
                    'end': max(dates) if dates else None
                },
                'total_points': len(timeline_data),
                'peak_date': max(timeline_data.items(), key=lambda x: x[1])[0] if timeline_data else None
            }

            return result

        except Exception as e:
            error_msg = f"Failed to generate distribution chart: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

def create_chart_config() -> Dict[str, Any]:
    """Create default configuration for chart generator."""
    return {
        'default_theme': 'plotly',
        'output_format': 'html',
        'chart_size': {
            'width': 800,
            'height': 600
        },
        'colors': {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd',
            'palette': [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ]
        },
        'styling': {
            'title_font_size': 18,
            'axis_font_size': 12,
            'legend_font_size': 10,
            'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
        },
        'export': {
            'output_dir': 'storage/exports/charts',
            'include_data': True,
            'responsive': True
        }
    }
