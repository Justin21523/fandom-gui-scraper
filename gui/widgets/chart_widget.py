# gui/widgets/chart_widget.py
"""
Data visualization chart widget for scraped anime data.

This module provides comprehensive charting capabilities for visualizing
anime character data, episode statistics, and data quality metrics.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QTabWidget,
    QFrame,
    QSplitter,
    QScrollArea,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QSlider,
    QButtonGroup,
    QRadioButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot, QThread
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np

from utils.logger import get_logger


class ChartWidget(QWidget):
    """
    Advanced data visualization widget for anime data analysis.

    Provides multiple chart types:
    - Character statistics (age distribution, status breakdown)
    - Episode analytics (timeline, quality metrics)
    - Data quality visualization
    - Comparison charts between anime series
    """

    # Custom signals
    chart_generated = pyqtSignal(str)  # chart type
    data_exported = pyqtSignal(str)  # export path
    chart_updated = pyqtSignal(dict)  # chart config

    def __init__(self, parent=None):
        """Initialize chart widget."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)

        # Data
        self.current_data = []
        self.filtered_data = []
        self.chart_history = []

        # Chart configuration
        self.chart_config = {
            "theme": "default",
            "color_palette": "viridis",
            "figure_size": (10, 6),
            "dpi": 100,
            "show_grid": True,
            "show_legend": True,
        }

        # Initialize matplotlib
        plt.style.use("default")
        sns.set_palette("viridis")

        # Initialize UI
        self.setup_ui()
        self.setup_connections()

        self.logger.info("Chart widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

        # Left panel - controls
        controls_panel = self._create_controls_panel()
        main_splitter.addWidget(controls_panel)

        # Right panel - charts
        chart_panel = self._create_chart_panel()
        main_splitter.addWidget(chart_panel)

        # Set splitter sizes
        main_splitter.setSizes([250, 750])

        # Status bar
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

    def _create_controls_panel(self) -> QWidget:
        """Create chart controls panel."""
        panel = QWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)

        # Chart type selection
        type_group = QGroupBox("Chart Type")
        type_layout = QVBoxLayout(type_group)

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(
            [
                "Character Age Distribution",
                "Character Status Breakdown",
                "Episode Timeline",
                "Data Quality Metrics",
                "Anime Comparison",
                "Tag Cloud",
                "Character Relationships",
                "Quality Score Trends",
            ]
        )
        type_layout.addWidget(self.chart_type_combo)

        layout.addWidget(type_group)

        # Data filters
        filter_group = QGroupBox("Data Filters")
        filter_layout = QFormLayout(filter_group)

        self.anime_filter = QComboBox()
        self.anime_filter.addItem("All Anime")
        filter_layout.addRow("Anime:", self.anime_filter)

        self.data_type_filter = QComboBox()
        self.data_type_filter.addItems(
            ["All Types", "Characters", "Episodes", "Locations"]
        )
        filter_layout.addRow("Type:", self.data_type_filter)

        self.min_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_quality_slider.setRange(0, 100)
        self.min_quality_slider.setValue(0)
        self.quality_label = QLabel("0%")

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.min_quality_slider)
        quality_layout.addWidget(self.quality_label)
        filter_layout.addRow("Min Quality:", quality_layout)

        layout.addWidget(filter_group)

        # Chart options
        options_group = QGroupBox("Chart Options")
        options_layout = QVBoxLayout(options_group)

        self.show_grid_checkbox = QCheckBox("Show grid")
        self.show_grid_checkbox.setChecked(True)
        options_layout.addWidget(self.show_grid_checkbox)

        self.show_legend_checkbox = QCheckBox("Show legend")
        self.show_legend_checkbox.setChecked(True)
        options_layout.addWidget(self.show_legend_checkbox)

        self.animated_checkbox = QCheckBox("Animated transitions")
        options_layout.addWidget(self.animated_checkbox)

        # Color scheme
        color_layout = QFormLayout()
        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.addItems(
            [
                "viridis",
                "plasma",
                "inferno",
                "magma",
                "Blues",
                "Reds",
                "Greens",
                "Purples",
                "Set1",
                "Set2",
                "Pastel1",
                "Dark2",
            ]
        )
        color_layout.addRow("Color Scheme:", self.color_scheme_combo)
        options_layout.addLayout(color_layout)

        layout.addWidget(options_group)

        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)

        self.bin_count_spinbox = QSpinBox()
        self.bin_count_spinbox.setRange(5, 50)
        self.bin_count_spinbox.setValue(20)
        advanced_layout.addRow("Histogram Bins:", self.bin_count_spinbox)

        self.smooth_lines_checkbox = QCheckBox("Smooth lines")
        advanced_layout.addRow(self.smooth_lines_checkbox)

        self.show_trend_checkbox = QCheckBox("Show trend line")
        advanced_layout.addRow(self.show_trend_checkbox)

        layout.addWidget(advanced_group)

        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.generate_chart_btn = QPushButton("Generate Chart")
        self.generate_chart_btn.setDefault(True)
        actions_layout.addWidget(self.generate_chart_btn)

        self.export_chart_btn = QPushButton("Export Chart")
        actions_layout.addWidget(self.export_chart_btn)

        self.save_config_btn = QPushButton("Save Configuration")
        actions_layout.addWidget(self.save_config_btn)

        layout.addWidget(actions_group)

        layout.addStretch()
        return panel

    def _create_chart_panel(self) -> QWidget:
        """Create chart display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Chart tabs
        self.chart_tabs = QTabWidget()
        layout.addWidget(self.chart_tabs)

        # Create initial chart canvas
        self.main_canvas = self._create_chart_canvas()
        self.chart_tabs.addTab(self.main_canvas, "Main Chart")

        # Chart info panel
        info_panel = self._create_chart_info_panel()
        layout.addWidget(info_panel)

        return panel

    def _create_chart_canvas(self) -> QWidget:
        """Create matplotlib chart canvas."""
        # Create matplotlib figure
        self.figure = Figure(
            figsize=self.chart_config["figure_size"], dpi=self.chart_config["dpi"]
        )
        self.canvas = FigureCanvas(self.figure)

        # Create widget to hold canvas
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.canvas)

        return widget

    def _create_chart_info_panel(self) -> QWidget:
        """Create chart information panel."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setMaximumHeight(60)

        layout = QHBoxLayout(frame)

        self.chart_title_label = QLabel("No chart generated")
        self.chart_title_label.setFont(QFont("", 10, QFont.Weight.Bold))

        self.data_points_label = QLabel("Data points: 0")
        self.chart_type_label = QLabel("Type: None")

        layout.addWidget(self.chart_title_label)
        layout.addStretch()
        layout.addWidget(self.data_points_label)
        layout.addWidget(self.chart_type_label)

        return frame

    def _create_status_bar(self) -> QWidget:
        """Create status bar."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("Ready to generate charts")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.progress_bar)

        return frame

    def setup_connections(self):
        """Set up signal connections."""
        # Chart generation
        self.generate_chart_btn.clicked.connect(self.generate_chart)
        self.chart_type_combo.currentTextChanged.connect(self._on_chart_type_changed)

        # Filters
        self.anime_filter.currentTextChanged.connect(self._on_filter_changed)
        self.data_type_filter.currentTextChanged.connect(self._on_filter_changed)
        self.min_quality_slider.valueChanged.connect(self._update_quality_label)
        self.min_quality_slider.valueChanged.connect(self._on_filter_changed)

        # Chart options
        self.show_grid_checkbox.toggled.connect(self._on_option_changed)
        self.show_legend_checkbox.toggled.connect(self._on_option_changed)
        self.color_scheme_combo.currentTextChanged.connect(self._on_option_changed)
        self.bin_count_spinbox.valueChanged.connect(self._on_option_changed)

        # Actions
        self.export_chart_btn.clicked.connect(self.export_chart)
        self.save_config_btn.clicked.connect(self.save_chart_config)

        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.generate_chart)

    def set_data(self, data: List[Dict[str, Any]]):
        """Set data for chart generation."""
        self.current_data = data
        self.filtered_data = data.copy()

        # Update anime filter options
        anime_names = set()
        for item in data:
            anime_name = item.get("anime_name", "")
            if anime_name:
                anime_names.add(anime_name)

        current_anime = self.anime_filter.currentText()
        self.anime_filter.clear()
        self.anime_filter.addItem("All Anime")
        self.anime_filter.addItems(sorted(anime_names))

        # Restore selection
        index = self.anime_filter.findText(current_anime)
        if index >= 0:
            self.anime_filter.setCurrentIndex(index)

        self._apply_filters()
        self.logger.info(f"Chart data updated: {len(data)} items")

    def generate_chart(self):
        """Generate chart based on current settings."""
        chart_type = self.chart_type_combo.currentText()

        if not self.filtered_data:
            QMessageBox.information(
                self,
                "No Data",
                "No data available for chart generation. Please load some data first.",
            )
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generating chart...")
        self.generate_chart_btn.setEnabled(False)

        try:
            # Clear previous chart
            self.figure.clear()

            # Generate chart based on type
            if chart_type == "Character Age Distribution":
                self._generate_age_distribution_chart()
            elif chart_type == "Character Status Breakdown":
                self._generate_status_breakdown_chart()
            elif chart_type == "Episode Timeline":
                self._generate_episode_timeline_chart()
            elif chart_type == "Data Quality Metrics":
                self._generate_quality_metrics_chart()
            elif chart_type == "Anime Comparison":
                self._generate_anime_comparison_chart()
            elif chart_type == "Tag Cloud":
                self._generate_tag_cloud_chart()
            elif chart_type == "Character Relationships":
                self._generate_relationships_chart()
            elif chart_type == "Quality Score Trends":
                self._generate_quality_trends_chart()

            self.progress_bar.setValue(80)

            # Apply chart options
            self._apply_chart_options()

            # Update canvas
            self.canvas.draw()

            self.progress_bar.setValue(100)

            # Update info
            self._update_chart_info(chart_type)

            # Add to history
            self.chart_history.append(
                {
                    "type": chart_type,
                    "timestamp": datetime.now(),
                    "data_count": len(self.filtered_data),
                    "config": self.chart_config.copy(),
                }
            )

            self.chart_generated.emit(chart_type)
            self.status_label.setText("Chart generated successfully")
            self.logger.info(f"Generated chart: {chart_type}")

        except Exception as e:
            self.logger.error(f"Chart generation failed: {e}")
            QMessageBox.critical(
                self, "Chart Error", f"Failed to generate chart:\n{str(e)}"
            )
            self.status_label.setText("Chart generation failed")

        finally:
            self.progress_bar.setVisible(False)
            self.generate_chart_btn.setEnabled(True)

    def _generate_age_distribution_chart(self):
        """Generate character age distribution histogram."""
        ages = []
        for item in self.filtered_data:
            age = item.get("age")
            if age is not None and isinstance(age, (int, float)) and 0 <= age <= 200:
                ages.append(age)

        if not ages:
            raise ValueError("No valid age data found")

        ax = self.figure.add_subplot(111)

        # Create histogram
        n, bins, patches = ax.hist(
            ages,
            bins=self.bin_count_spinbox.value(),
            alpha=0.7,
            edgecolor="black",
            linewidth=0.5,
        )

        # Color bars based on value
        cmap = plt.cm.get_cmap(self.color_scheme_combo.currentText())
        for i, p in enumerate(patches):
            p.set_facecolor(cmap(i / len(patches)))

        ax.set_xlabel("Age")
        ax.set_ylabel("Number of Characters")
        ax.set_title("Character Age Distribution")

        # Add statistics
        mean_age = np.mean(ages)
        median_age = np.median(ages)
        ax.axvline(
            mean_age,
            color="red",
            linestyle="--",
            alpha=0.7,
            label=f"Mean: {mean_age:.1f}",
        )
        ax.axvline(
            median_age,
            color="blue",
            linestyle="--",
            alpha=0.7,
            label=f"Median: {median_age:.1f}",
        )

        if self.show_legend_checkbox.isChecked():
            ax.legend()

    def _generate_status_breakdown_chart(self):
        """Generate character status breakdown pie chart."""
        statuses = []
        for item in self.filtered_data:
            status = item.get("status", "Unknown")
            if status:
                statuses.append(status.title())

        if not statuses:
            raise ValueError("No status data found")

        status_counts = Counter(statuses)

        ax = self.figure.add_subplot(111)

        # Create pie chart
        colors = plt.cm.get_cmap(self.color_scheme_combo.currentText())(
            np.linspace(0, 1, len(status_counts))
        )

        wedges, texts, autotexts = ax.pie(
            status_counts.values(),
            labels=status_counts.keys(),
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
        )

        ax.set_title("Character Status Breakdown")

        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

    def _generate_episode_timeline_chart(self):
        """Generate episode timeline chart."""
        episodes = [
            item for item in self.filtered_data if item.get("type") == "episode"
        ]

        if not episodes:
            raise ValueError("No episode data found")

        # Extract episode numbers and dates
        episode_numbers = []
        dates = []

        for ep in episodes:
            ep_num = ep.get("episode_number")
            date_str = ep.get("air_date") or ep.get("created_date")

            if ep_num is not None and date_str:
                try:
                    if isinstance(date_str, str):
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    else:
                        date = date_str
                    episode_numbers.append(ep_num)
                    dates.append(date)
                except:
                    continue

        if not episode_numbers:
            raise ValueError("No valid episode timeline data found")

        ax = self.figure.add_subplot(111)

        # Sort by episode number
        sorted_data = sorted(zip(episode_numbers, dates))
        episode_numbers, dates = zip(*sorted_data)

        # Plot timeline
        ax.plot(dates, episode_numbers, marker="o", linewidth=2, markersize=4)

        ax.set_xlabel("Air Date")
        ax.set_ylabel("Episode Number")
        ax.set_title("Episode Timeline")

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def _generate_quality_metrics_chart(self):
        """Generate data quality metrics chart."""
        quality_scores = []
        completeness_scores = []

        for item in self.filtered_data:
            quality = item.get("quality_score", 0)
            quality_scores.append(quality)

            # Calculate completeness based on filled fields
            total_fields = len(item)
            filled_fields = sum(
                1 for v in item.values() if v is not None and str(v).strip()
            )
            completeness = (
                (filled_fields / total_fields) * 100 if total_fields > 0 else 0
            )
            completeness_scores.append(completeness)

        ax = self.figure.add_subplot(111)

        # Create scatter plot
        scatter = ax.scatter(
            completeness_scores,
            quality_scores,
            alpha=0.6,
            c=quality_scores,
            cmap=self.color_scheme_combo.currentText(),
            s=30,
        )

        ax.set_xlabel("Data Completeness (%)")
        ax.set_ylabel("Quality Score")
        ax.set_title("Data Quality vs Completeness")

        # Add colorbar
        cbar = self.figure.colorbar(scatter, ax=ax)
        cbar.set_label("Quality Score")

        # Add trend line if requested
        if self.show_trend_checkbox.isChecked():
            z = np.polyfit(completeness_scores, quality_scores, 1)
            p = np.poly1d(z)
            ax.plot(completeness_scores, p(completeness_scores), "r--", alpha=0.8)

    def _generate_anime_comparison_chart(self):
        """Generate anime comparison bar chart."""
        anime_stats = defaultdict(
            lambda: {"characters": 0, "episodes": 0, "avg_quality": 0}
        )

        for item in self.filtered_data:
            anime_name = item.get("anime_name", "Unknown")
            item_type = item.get("type", "").lower()
            quality = item.get("quality_score", 0)

            if item_type == "character":
                anime_stats[anime_name]["characters"] += 1
            elif item_type == "episode":
                anime_stats[anime_name]["episodes"] += 1

            anime_stats[anime_name]["avg_quality"] += quality

        # Calculate averages
        for stats in anime_stats.values():
            total_items = stats["characters"] + stats["episodes"]
            if total_items > 0:
                stats["avg_quality"] /= total_items

        if not anime_stats:
            raise ValueError("No anime data found for comparison")

        anime_names = list(anime_stats.keys())
        characters = [anime_stats[name]["characters"] for name in anime_names]
        episodes = [anime_stats[name]["episodes"] for name in anime_names]

        ax = self.figure.add_subplot(111)

        x = np.arange(len(anime_names))
        width = 0.35

        # Create grouped bar chart
        bars1 = ax.bar(x - width / 2, characters, width, label="Characters", alpha=0.8)
        bars2 = ax.bar(x + width / 2, episodes, width, label="Episodes", alpha=0.8)

        ax.set_xlabel("Anime Series")
        ax.set_ylabel("Count")
        ax.set_title("Anime Data Comparison")
        ax.set_xticks(x)
        ax.set_xticklabels(anime_names, rotation=45, ha="right")

        if self.show_legend_checkbox.isChecked():
            ax.legend()

    def _generate_tag_cloud_chart(self):
        """Generate tag cloud visualization."""
        try:
            from wordcloud import WordCloud
        except ImportError:
            raise ImportError(
                "WordCloud library not installed. Please install with: pip install wordcloud"
            )

        # Collect all tags
        all_tags = []
        for item in self.filtered_data:
            tags = item.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",")]
            elif isinstance(tags, list):
                tags = [str(tag) for tag in tags]
            all_tags.extend(tags)

        if not all_tags:
            raise ValueError("No tag data found")

        # Create word cloud
        text = " ".join(all_tags)
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            colormap=self.color_scheme_combo.currentText(),
            max_words=100,
        ).generate(text)

        ax = self.figure.add_subplot(111)
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        ax.set_title("Character Tags Word Cloud")

    def _generate_relationships_chart(self):
        """Generate character relationships network chart."""
        # This is a simplified version - a full implementation would require network analysis
        relationships = defaultdict(int)

        for item in self.filtered_data:
            if item.get("type") == "character":
                relations = item.get("relationships", [])
                if isinstance(relations, str):
                    relations = [rel.strip() for rel in relations.split(",")]

                for rel in relations:
                    if rel:
                        relationships[rel] += 1

        if not relationships:
            raise ValueError("No relationship data found")

        # Create simple bar chart of relationship types
        ax = self.figure.add_subplot(111)

        rel_types = list(relationships.keys())[:10]  # Top 10
        rel_counts = [relationships[rel] for rel in rel_types]

        bars = ax.barh(rel_types, rel_counts)

        # Color bars
        cmap = plt.cm.get_cmap(self.color_scheme_combo.currentText())
        for i, bar in enumerate(bars):
            bar.set_color(cmap(i / len(bars)))

        ax.set_xlabel("Number of Characters")
        ax.set_title("Character Relationship Types")

    def _generate_quality_trends_chart(self):
        """Generate quality score trends over time."""
        dates = []
        qualities = []

        for item in self.filtered_data:
            date_str = item.get("created_date")
            quality = item.get("quality_score", 0)

            if date_str and quality is not None:
                try:
                    if isinstance(date_str, str):
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    else:
                        date = date_str
                    dates.append(date)
                    qualities.append(quality)
                except:
                    continue

        if not dates:
            raise ValueError("No dated quality data found")

        # Sort by date
        sorted_data = sorted(zip(dates, qualities))
        dates, qualities = zip(*sorted_data)

        ax = self.figure.add_subplot(111)

        # Plot quality trend
        ax.plot(dates, qualities, marker="o", linewidth=2, markersize=3, alpha=0.7)

        # Add moving average if enough data points
        if len(qualities) > 7:
            window_size = min(7, len(qualities) // 3)
            moving_avg = (
                pd.Series(qualities).rolling(window=window_size, center=True).mean()
            )
            ax.plot(
                dates,
                moving_avg,
                linewidth=3,
                alpha=0.8,
                label=f"{window_size}-point moving average",
            )

        ax.set_xlabel("Date")
        ax.set_ylabel("Quality Score")
        ax.set_title("Data Quality Trends Over Time")

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        if self.show_legend_checkbox.isChecked() and len(qualities) > 7:
            ax.legend()

    def _apply_chart_options(self):
        """Apply chart formatting options."""
        for ax in self.figure.get_axes():
            # Grid
            ax.grid(self.show_grid_checkbox.isChecked(), alpha=0.3)

            # Tight layout
            self.figure.tight_layout()

    def _apply_filters(self):
        """Apply current filters to data."""
        filtered = []

        anime_filter = self.anime_filter.currentText()
        type_filter = self.data_type_filter.currentText()
        min_quality = self.min_quality_slider.value()

        for item in self.current_data:
            # Anime filter
            if anime_filter != "All Anime":
                if item.get("anime_name") != anime_filter:
                    continue

            # Type filter
            if type_filter != "All Types":
                item_type = item.get("type", "").lower()
                if type_filter.lower() not in item_type:
                    continue

            # Quality filter
            quality = item.get("quality_score", 0)
            if quality < min_quality:
                continue

            filtered.append(item)

        self.filtered_data = filtered
        self.data_points_label.setText(f"Data points: {len(filtered)}")

    def _update_chart_info(self, chart_type: str):
        """Update chart information display."""
        self.chart_title_label.setText(chart_type)
        self.chart_type_label.setText(f"Type: {chart_type}")
        self.data_points_label.setText(f"Data points: {len(self.filtered_data)}")

    def export_chart(self):
        """Export current chart to file."""
        if not hasattr(self, "figure") or not self.figure.get_axes():
            QMessageBox.information(self, "No Chart", "Please generate a chart first.")
            return

        file_path, file_type = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;JPEG Files (*.jpg)",
        )

        if file_path:
            try:
                # Set high DPI for better quality
                self.figure.savefig(
                    file_path,
                    dpi=300,
                    bbox_inches="tight",
                    facecolor="white",
                    edgecolor="none",
                )

                self.data_exported.emit(file_path)
                self.logger.info(f"Chart exported to: {file_path}")
                QMessageBox.information(
                    self, "Export Successful", f"Chart saved to:\n{file_path}"
                )

            except Exception as e:
                self.logger.error(f"Chart export failed: {e}")
                QMessageBox.critical(
                    self, "Export Failed", f"Failed to export chart:\n{str(e)}"
                )

    def save_chart_config(self):
        """Save current chart configuration."""
        config = {
            "chart_type": self.chart_type_combo.currentText(),
            "anime_filter": self.anime_filter.currentText(),
            "type_filter": self.data_type_filter.currentText(),
            "min_quality": self.min_quality_slider.value(),
            "show_grid": self.show_grid_checkbox.isChecked(),
            "show_legend": self.show_legend_checkbox.isChecked(),
            "color_scheme": self.color_scheme_combo.currentText(),
            "bin_count": self.bin_count_spinbox.value(),
            "smooth_lines": self.smooth_lines_checkbox.isChecked(),
            "show_trend": self.show_trend_checkbox.isChecked(),
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chart Configuration",
            f"chart_config_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON Files (*.json)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)

                self.logger.info(f"Chart configuration saved to: {file_path}")
                QMessageBox.information(
                    self, "Config Saved", f"Configuration saved to:\n{file_path}"
                )

            except Exception as e:
                self.logger.error(f"Failed to save configuration: {e}")
                QMessageBox.critical(
                    self, "Save Failed", f"Failed to save configuration:\n{str(e)}"
                )

    def load_chart_config(self, file_path: str):
        """Load chart configuration from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Apply configuration
            chart_type = config.get("chart_type", "")
            index = self.chart_type_combo.findText(chart_type)
            if index >= 0:
                self.chart_type_combo.setCurrentIndex(index)

            anime_filter = config.get("anime_filter", "")
            index = self.anime_filter.findText(anime_filter)
            if index >= 0:
                self.anime_filter.setCurrentIndex(index)

            type_filter = config.get("type_filter", "")
            index = self.data_type_filter.findText(type_filter)
            if index >= 0:
                self.data_type_filter.setCurrentIndex(index)

            self.min_quality_slider.setValue(config.get("min_quality", 0))
            self.show_grid_checkbox.setChecked(config.get("show_grid", True))
            self.show_legend_checkbox.setChecked(config.get("show_legend", True))

            color_scheme = config.get("color_scheme", "")
            index = self.color_scheme_combo.findText(color_scheme)
            if index >= 0:
                self.color_scheme_combo.setCurrentIndex(index)

            self.bin_count_spinbox.setValue(config.get("bin_count", 20))
            self.smooth_lines_checkbox.setChecked(config.get("smooth_lines", False))
            self.show_trend_checkbox.setChecked(config.get("show_trend", False))

            self.logger.info(f"Chart configuration loaded from: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            QMessageBox.critical(
                self, "Load Failed", f"Failed to load configuration:\n{str(e)}"
            )

    # Event handlers
    def _on_chart_type_changed(self, chart_type: str):
        """Handle chart type change."""
        # Enable/disable relevant options based on chart type
        if chart_type in ["Character Age Distribution", "Quality Score Trends"]:
            self.bin_count_spinbox.setEnabled(True)
            self.show_trend_checkbox.setEnabled(True)
        else:
            self.bin_count_spinbox.setEnabled(False)
            self.show_trend_checkbox.setEnabled(False)

        # Auto-generate if data is available
        if self.filtered_data:
            self.update_timer.start(500)  # 500ms delay

    def _on_filter_changed(self):
        """Handle filter changes."""
        self._apply_filters()

        # Auto-update chart if enabled
        if self.filtered_data:
            self.update_timer.start(300)  # 300ms delay

    def _on_option_changed(self):
        """Handle chart option changes."""
        if hasattr(self, "figure") and self.figure.get_axes():
            self.update_timer.start(200)  # 200ms delay for options

    def _update_quality_label(self, value: int):
        """Update quality slider label."""
        self.quality_label.setText(f"{value}%")
