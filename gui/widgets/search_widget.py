# gui/widgets/search_widget.py
"""
Advanced search and filter widget for scraped data.

This module provides comprehensive search functionality with multiple
filter options, saved searches, and real-time filtering capabilities.
"""

import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, date
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QSpinBox,
    QDateEdit,
    QSlider,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QFrame,
    QMenu,
    QToolButton,
    QProgressBar,
    QMessageBox,
    QFileDialog,
    QDialogButtonBox,
    QButtonGroup,
    QRadioButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QAction, QCursor

from utils.logger import get_logger


class SearchWidget(QWidget):
    """
    Advanced search widget for filtering and finding scraped anime data.

    Provides multiple search modes:
    - Quick text search
    - Advanced filters
    - Saved search queries
    - Real-time filtering
    """

    # Custom signals
    search_executed = pyqtSignal(dict)  # search criteria
    results_filtered = pyqtSignal(list)  # filtered results
    search_saved = pyqtSignal(str, dict)  # name, criteria
    search_cleared = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize search widget."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)

        # State
        self.current_data = []
        self.filtered_results = []
        self.saved_searches = {}
        self.search_history = []

        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.load_saved_searches()

        self.logger.info("Search widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Top panel - search interface
        search_panel = self._create_search_panel()
        splitter.addWidget(search_panel)

        # Bottom panel - results and saved searches
        results_panel = self._create_results_panel()
        splitter.addWidget(results_panel)

        # Set splitter sizes
        splitter.setSizes([200, 300])

        # Search controls bar
        controls_bar = self._create_controls_bar()
        layout.addWidget(controls_bar)

    def _create_search_panel(self) -> QWidget:
        """Create search panel with tabs."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tab widget
        self.search_tabs = QTabWidget()
        layout.addWidget(self.search_tabs)

        # Quick search tab
        quick_tab = self._create_quick_search_tab()
        self.search_tabs.addTab(quick_tab, "Quick Search")

        # Advanced search tab
        advanced_tab = self._create_advanced_search_tab()
        self.search_tabs.addTab(advanced_tab, "Advanced")

        # Saved searches tab
        saved_tab = self._create_saved_searches_tab()
        self.search_tabs.addTab(saved_tab, "Saved")

        return panel

    def _create_quick_search_tab(self) -> QWidget:
        """Create quick search tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search input
        search_group = QGroupBox("Quick Search")
        search_layout = QVBoxLayout(search_group)

        # Main search input
        input_layout = QHBoxLayout()
        self.quick_search_input = QLineEdit()
        self.quick_search_input.setPlaceholderText(
            "Search characters, episodes, or any text..."
        )
        self.quick_search_btn = QPushButton("Search")
        self.quick_search_btn.setDefault(True)

        input_layout.addWidget(self.quick_search_input)
        input_layout.addWidget(self.quick_search_btn)
        search_layout.addLayout(input_layout)

        # Search options
        options_layout = QHBoxLayout()

        self.case_sensitive_checkbox = QCheckBox("Case sensitive")
        self.whole_words_checkbox = QCheckBox("Whole words only")
        self.regex_checkbox = QCheckBox("Regular expression")

        options_layout.addWidget(self.case_sensitive_checkbox)
        options_layout.addWidget(self.whole_words_checkbox)
        options_layout.addWidget(self.regex_checkbox)
        options_layout.addStretch()

        search_layout.addLayout(options_layout)

        layout.addWidget(search_group)

        # Search scope
        scope_group = QGroupBox("Search Scope")
        scope_layout = QVBoxLayout(scope_group)

        self.scope_button_group = QButtonGroup()
        self.search_all_radio = QRadioButton("Search all data")
        self.search_characters_radio = QRadioButton("Characters only")
        self.search_episodes_radio = QRadioButton("Episodes only")
        self.search_selected_radio = QRadioButton("Selected items only")

        self.search_all_radio.setChecked(True)

        self.scope_button_group.addButton(self.search_all_radio, 0)
        self.scope_button_group.addButton(self.search_characters_radio, 1)
        self.scope_button_group.addButton(self.search_episodes_radio, 2)
        self.scope_button_group.addButton(self.search_selected_radio, 3)

        scope_layout.addWidget(self.search_all_radio)
        scope_layout.addWidget(self.search_characters_radio)
        scope_layout.addWidget(self.search_episodes_radio)
        scope_layout.addWidget(self.search_selected_radio)

        layout.addWidget(scope_group)

        # Recent searches
        recent_group = QGroupBox("Recent Searches")
        recent_layout = QVBoxLayout(recent_group)

        self.recent_searches_list = QListWidget()
        self.recent_searches_list.setMaximumHeight(100)
        recent_layout.addWidget(self.recent_searches_list)

        layout.addWidget(recent_group)

        layout.addStretch()
        return tab

    def _create_advanced_search_tab(self) -> QWidget:
        """Create advanced search tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create scroll area for advanced options
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Text filters
        text_group = QGroupBox("Text Filters")
        text_layout = QFormLayout(text_group)

        self.name_filter = QLineEdit()
        self.name_filter.setPlaceholderText("Character/Episode name...")
        text_layout.addRow("Name contains:", self.name_filter)

        self.description_filter = QLineEdit()
        self.description_filter.setPlaceholderText("Description text...")
        text_layout.addRow("Description contains:", self.description_filter)

        self.tags_filter = QLineEdit()
        self.tags_filter.setPlaceholderText("Comma-separated tags...")
        text_layout.addRow("Tags:", self.tags_filter)

        scroll_layout.addWidget(text_group)

        # Category filters
        category_group = QGroupBox("Category Filters")
        category_layout = QFormLayout(category_group)

        self.anime_filter = QComboBox()
        self.anime_filter.addItem("Any Anime")
        self.anime_filter.setEditable(True)
        category_layout.addRow("Anime:", self.anime_filter)

        self.type_filter = QComboBox()
        self.type_filter.addItems(
            ["Any Type", "Character", "Episode", "Location", "Item"]
        )
        category_layout.addRow("Type:", self.type_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Any Status", "Active", "Deceased", "Unknown"])
        category_layout.addRow("Status:", self.status_filter)

        scroll_layout.addWidget(category_group)

        # Numeric filters
        numeric_group = QGroupBox("Numeric Filters")
        numeric_layout = QFormLayout(numeric_group)

        # Character age range
        age_layout = QHBoxLayout()
        self.min_age_spinbox = QSpinBox()
        self.min_age_spinbox.setRange(0, 1000)
        self.max_age_spinbox = QSpinBox()
        self.max_age_spinbox.setRange(0, 1000)
        self.max_age_spinbox.setValue(1000)

        age_layout.addWidget(QLabel("Min:"))
        age_layout.addWidget(self.min_age_spinbox)
        age_layout.addWidget(QLabel("Max:"))
        age_layout.addWidget(self.max_age_spinbox)
        age_layout.addStretch()

        numeric_layout.addRow("Age range:", age_layout)

        # Episode number range
        episode_layout = QHBoxLayout()
        self.min_episode_spinbox = QSpinBox()
        self.min_episode_spinbox.setRange(0, 10000)
        self.max_episode_spinbox = QSpinBox()
        self.max_episode_spinbox.setRange(0, 10000)
        self.max_episode_spinbox.setValue(10000)

        episode_layout.addWidget(QLabel("Min:"))
        episode_layout.addWidget(self.min_episode_spinbox)
        episode_layout.addWidget(QLabel("Max:"))
        episode_layout.addWidget(self.max_episode_spinbox)
        episode_layout.addStretch()

        numeric_layout.addRow("Episode range:", episode_layout)

        scroll_layout.addWidget(numeric_group)

        # Date filters
        date_group = QGroupBox("Date Filters")
        date_layout = QFormLayout(date_group)

        self.date_from_edit = QDateEdit()
        self.date_from_edit.setDate(QDate.currentDate().addYears(-10))
        self.date_from_edit.setCalendarPopup(True)
        date_layout.addRow("Created after:", self.date_from_edit)

        self.date_to_edit = QDateEdit()
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setCalendarPopup(True)
        date_layout.addRow("Created before:", self.date_to_edit)

        scroll_layout.addWidget(date_group)

        # Data quality filters
        quality_group = QGroupBox("Data Quality")
        quality_layout = QFormLayout(quality_group)

        self.has_image_checkbox = QCheckBox("Has character image")
        quality_layout.addRow(self.has_image_checkbox)

        self.has_description_checkbox = QCheckBox("Has description")
        quality_layout.addRow(self.has_description_checkbox)

        self.min_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_quality_slider.setRange(0, 100)
        self.min_quality_slider.setValue(0)
        self.quality_label = QLabel("0%")

        quality_slider_layout = QHBoxLayout()
        quality_slider_layout.addWidget(self.min_quality_slider)
        quality_slider_layout.addWidget(self.quality_label)

        quality_layout.addRow("Min quality score:", quality_slider_layout)

        scroll_layout.addWidget(quality_group)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        return tab

    def _create_saved_searches_tab(self) -> QWidget:
        """Create saved searches tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Saved searches list
        searches_group = QGroupBox("Saved Searches")
        searches_layout = QVBoxLayout(searches_group)

        self.saved_searches_tree = QTreeWidget()
        self.saved_searches_tree.setHeaderLabels(["Name", "Description", "Created"])
        self.saved_searches_tree.setRootIsDecorated(False)
        searches_layout.addWidget(self.saved_searches_tree)

        # Saved search controls
        saved_controls = QHBoxLayout()
        self.load_search_btn = QPushButton("Load Search")
        self.delete_search_btn = QPushButton("Delete")
        self.export_searches_btn = QPushButton("Export")
        self.import_searches_btn = QPushButton("Import")

        saved_controls.addWidget(self.load_search_btn)
        saved_controls.addWidget(self.delete_search_btn)
        saved_controls.addStretch()
        saved_controls.addWidget(self.export_searches_btn)
        saved_controls.addWidget(self.import_searches_btn)

        searches_layout.addLayout(saved_controls)
        layout.addWidget(searches_group)

        # Save current search
        save_group = QGroupBox("Save Current Search")
        save_layout = QFormLayout(save_group)

        self.search_name_input = QLineEdit()
        self.search_name_input.setPlaceholderText("Enter search name...")
        save_layout.addRow("Name:", self.search_name_input)

        self.search_description_input = QLineEdit()
        self.search_description_input.setPlaceholderText("Optional description...")
        save_layout.addRow("Description:", self.search_description_input)

        self.save_search_btn = QPushButton("Save Current Search")
        save_layout.addRow(self.save_search_btn)

        layout.addWidget(save_group)

        layout.addStretch()
        return tab

    def _create_results_panel(self) -> QWidget:
        """Create results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Results header
        header_layout = QHBoxLayout()
        self.results_label = QLabel("Search Results (0 items)")
        self.results_label.setFont(QFont("", 10, QFont.Weight.Bold))

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            [
                "Name (A-Z)",
                "Name (Z-A)",
                "Date (Newest)",
                "Date (Oldest)",
                "Quality (High-Low)",
                "Quality (Low-High)",
                "Relevance",
            ]
        )

        header_layout.addWidget(self.results_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Sort by:"))
        header_layout.addWidget(self.sort_combo)

        layout.addLayout(header_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.results_table.setSortingEnabled(True)
        layout.addWidget(self.results_table)

        # Results summary
        summary_layout = QHBoxLayout()
        self.characters_count_label = QLabel("Characters: 0")
        self.episodes_count_label = QLabel("Episodes: 0")
        self.avg_quality_label = QLabel("Avg Quality: 0%")

        summary_layout.addWidget(self.characters_count_label)
        summary_layout.addWidget(self.episodes_count_label)
        summary_layout.addWidget(self.avg_quality_label)
        summary_layout.addStretch()

        layout.addLayout(summary_layout)

        return panel

    def _create_controls_bar(self) -> QWidget:
        """Create search controls bar."""
        bar = QFrame()
        bar.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(5, 2, 5, 2)

        # Search execution controls
        self.execute_search_btn = QPushButton("Execute Search")
        self.execute_search_btn.setDefault(True)
        self.clear_search_btn = QPushButton("Clear")
        self.reset_filters_btn = QPushButton("Reset Filters")

        layout.addWidget(self.execute_search_btn)
        layout.addWidget(self.clear_search_btn)
        layout.addWidget(self.reset_filters_btn)

        layout.addStretch()

        # Real-time search toggle
        self.realtime_search_checkbox = QCheckBox("Real-time search")
        self.realtime_search_checkbox.setToolTip("Update results as you type")
        layout.addWidget(self.realtime_search_checkbox)

        # Progress indicator
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        self.search_progress.setMaximumWidth(150)
        layout.addWidget(self.search_progress)

        return bar

    def setup_connections(self):
        """Set up signal connections."""
        # Quick search
        self.quick_search_btn.clicked.connect(self.execute_quick_search)
        self.quick_search_input.returnPressed.connect(self.execute_quick_search)
        self.quick_search_input.textChanged.connect(self._on_quick_search_text_changed)

        # Recent searches
        self.recent_searches_list.itemDoubleClicked.connect(
            self._on_recent_search_selected
        )

        # Advanced search filters
        self.name_filter.textChanged.connect(self._on_filter_changed)
        self.description_filter.textChanged.connect(self._on_filter_changed)
        self.tags_filter.textChanged.connect(self._on_filter_changed)
        self.anime_filter.currentTextChanged.connect(self._on_filter_changed)
        self.type_filter.currentTextChanged.connect(self._on_filter_changed)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)

        # Numeric filters
        self.min_age_spinbox.valueChanged.connect(self._on_filter_changed)
        self.max_age_spinbox.valueChanged.connect(self._on_filter_changed)
        self.min_episode_spinbox.valueChanged.connect(self._on_filter_changed)
        self.max_episode_spinbox.valueChanged.connect(self._on_filter_changed)

        # Quality filters
        self.has_image_checkbox.toggled.connect(self._on_filter_changed)
        self.has_description_checkbox.toggled.connect(self._on_filter_changed)
        self.min_quality_slider.valueChanged.connect(self._update_quality_label)
        self.min_quality_slider.valueChanged.connect(self._on_filter_changed)

        # Saved searches
        self.save_search_btn.clicked.connect(self.save_current_search)
        self.load_search_btn.clicked.connect(self.load_selected_search)
        self.delete_search_btn.clicked.connect(self.delete_selected_search)
        self.export_searches_btn.clicked.connect(self.export_saved_searches)
        self.import_searches_btn.clicked.connect(self.import_saved_searches)

        # Results
        self.sort_combo.currentTextChanged.connect(self._sort_results)
        self.results_table.itemSelectionChanged.connect(
            self._on_result_selection_changed
        )

        # Controls
        self.execute_search_btn.clicked.connect(self.execute_search)
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.reset_filters_btn.clicked.connect(self.reset_filters)
        self.realtime_search_checkbox.toggled.connect(self._on_realtime_toggle)

        # Real-time search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.execute_search)

    def set_data(self, data: List[Dict[str, Any]]):
        """Set data to search through."""
        self.current_data = data
        self.filtered_results = data.copy()

        # Update anime filter options
        anime_names = set()
        for item in data:
            anime_name = item.get("anime_name", "")
            if anime_name:
                anime_names.add(anime_name)

        current_text = self.anime_filter.currentText()
        self.anime_filter.clear()
        self.anime_filter.addItem("Any Anime")
        self.anime_filter.addItems(sorted(anime_names))

        # Restore selection
        index = self.anime_filter.findText(current_text)
        if index >= 0:
            self.anime_filter.setCurrentIndex(index)

        self.update_results_display()
        self.logger.info(f"Search data updated: {len(data)} items")

    def execute_quick_search(self):
        """Execute quick search."""
        search_text = self.quick_search_input.text().strip()

        if not search_text:
            self.clear_search()
            return

        # Add to recent searches
        self._add_to_recent_searches(search_text)

        # Build search criteria
        criteria = {
            "text": search_text,
            "case_sensitive": self.case_sensitive_checkbox.isChecked(),
            "whole_words": self.whole_words_checkbox.isChecked(),
            "regex": self.regex_checkbox.isChecked(),
            "scope": self.scope_button_group.checkedId(),
        }

        self._execute_search_with_criteria(criteria)

    def execute_search(self):
        """Execute search with current filters."""
        criteria = self._build_search_criteria()
        self._execute_search_with_criteria(criteria)

    def _build_search_criteria(self) -> Dict[str, Any]:
        """Build search criteria from current filter settings."""
        return {
            # Text filters
            "quick_text": self.quick_search_input.text().strip(),
            "name": self.name_filter.text().strip(),
            "description": self.description_filter.text().strip(),
            "tags": [
                tag.strip() for tag in self.tags_filter.text().split(",") if tag.strip()
            ],
            # Category filters
            "anime": (
                self.anime_filter.currentText()
                if self.anime_filter.currentText() != "Any Anime"
                else ""
            ),
            "type": (
                self.type_filter.currentText()
                if self.type_filter.currentText() != "Any Type"
                else ""
            ),
            "status": (
                self.status_filter.currentText()
                if self.status_filter.currentText() != "Any Status"
                else ""
            ),
            # Numeric filters
            "min_age": (
                self.min_age_spinbox.value()
                if self.min_age_spinbox.value() > 0
                else None
            ),
            "max_age": (
                self.max_age_spinbox.value()
                if self.max_age_spinbox.value() < 1000
                else None
            ),
            "min_episode": (
                self.min_episode_spinbox.value()
                if self.min_episode_spinbox.value() > 0
                else None
            ),
            "max_episode": (
                self.max_episode_spinbox.value()
                if self.max_episode_spinbox.value() < 10000
                else None
            ),
            # Date filters
            "date_from": self.date_from_edit.date().toPython(),
            "date_to": self.date_to_edit.date().toPython(),
            # Quality filters
            "has_image": self.has_image_checkbox.isChecked(),
            "has_description": self.has_description_checkbox.isChecked(),
            "min_quality": self.min_quality_slider.value(),
            # Search options
            "case_sensitive": self.case_sensitive_checkbox.isChecked(),
            "whole_words": self.whole_words_checkbox.isChecked(),
            "regex": self.regex_checkbox.isChecked(),
            "scope": self.scope_button_group.checkedId(),
        }

    def _execute_search_with_criteria(self, criteria: Dict[str, Any]):
        """Execute search with given criteria."""
        self.search_progress.setVisible(True)
        self.search_progress.setValue(0)

        try:
            # Apply filters
            results = self._apply_filters(self.current_data, criteria)

            self.search_progress.setValue(80)

            # Update results
            self.filtered_results = results
            self.update_results_display()

            self.search_progress.setValue(100)

            # Emit signals
            self.search_executed.emit(criteria)
            self.results_filtered.emit(results)

            self.logger.info(f"Search executed: {len(results)} results found")

        except Exception as e:
            self.logger.error(f"Search execution failed: {e}")
            QMessageBox.warning(self, "Search Error", f"Search failed: {str(e)}")

        finally:
            self.search_progress.setVisible(False)

    def _apply_filters(
        self, data: List[Dict[str, Any]], criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply search filters to data."""
        results = []

        for item in data:
            if self._item_matches_criteria(item, criteria):
                results.append(item)

        return results

    def _item_matches_criteria(
        self, item: Dict[str, Any], criteria: Dict[str, Any]
    ) -> bool:
        """Check if item matches search criteria."""
        # Quick text search
        if criteria.get("quick_text"):
            if not self._text_matches(item, criteria["quick_text"], criteria):
                return False

        # Name filter
        if criteria.get("name"):
            item_name = item.get("name", "").lower()
            search_name = criteria["name"].lower()
            if search_name not in item_name:
                return False

        # Description filter
        if criteria.get("description"):
            item_desc = item.get("description", "").lower()
            search_desc = criteria["description"].lower()
            if search_desc not in item_desc:
                return False

        # Tags filter
        if criteria.get("tags"):
            item_tags = item.get("tags", [])
            if isinstance(item_tags, str):
                item_tags = [tag.strip() for tag in item_tags.split(",")]

            for required_tag in criteria["tags"]:
                if not any(required_tag.lower() in tag.lower() for tag in item_tags):
                    return False

        # Category filters
        if criteria.get("anime"):
            if item.get("anime_name", "").lower() != criteria["anime"].lower():
                return False

        if criteria.get("type"):
            if item.get("type", "").lower() != criteria["type"].lower():
                return False

        if criteria.get("status"):
            if item.get("status", "").lower() != criteria["status"].lower():
                return False

        # Numeric filters
        if criteria.get("min_age") is not None:
            item_age = item.get("age")
            if item_age is None or item_age < criteria["min_age"]:
                return False

        if criteria.get("max_age") is not None:
            item_age = item.get("age")
            if item_age is None or item_age > criteria["max_age"]:
                return False

        # Quality filters
        if criteria.get("has_image"):
            if not item.get("image_url"):
                return False

        if criteria.get("has_description"):
            if not item.get("description", "").strip():
                return False

        if criteria.get("min_quality", 0) > 0:
            item_quality = item.get("quality_score", 0)
            if item_quality < criteria["min_quality"]:
                return False

        return True

    def _text_matches(
        self, item: Dict[str, Any], search_text: str, criteria: Dict[str, Any]
    ) -> bool:
        """Check if item text matches search criteria."""
        import re

        # Get searchable text fields
        searchable_fields = ["name", "description", "tags", "abilities", "occupation"]
        text_content = []

        for field in searchable_fields:
            value = item.get(field, "")
            if isinstance(value, list):
                text_content.extend(str(v) for v in value)
            else:
                text_content.append(str(value))

        full_text = " ".join(text_content)

        # Apply search options
        if not criteria.get("case_sensitive", False):
            full_text = full_text.lower()
            search_text = search_text.lower()

        if criteria.get("regex", False):
            try:
                return bool(re.search(search_text, full_text))
            except re.error:
                return search_text in full_text

        if criteria.get("whole_words", False):
            pattern = r"\b" + re.escape(search_text) + r"\b"
            return bool(
                re.search(
                    pattern,
                    full_text,
                    re.IGNORECASE if not criteria.get("case_sensitive") else 0,
                )
            )

        return search_text in full_text

    def update_results_display(self):
        """Update results table display."""
        results = self.filtered_results

        # Update results count
        self.results_label.setText(f"Search Results ({len(results)} items)")

        # Set up table
        if not results:
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            self._update_summary_stats([])
            return

        # Get column headers
        all_keys = set()
        for item in results:
            all_keys.update(item.keys())

        # Filter and sort columns
        display_columns = [
            "name",
            "type",
            "anime_name",
            "status",
            "age",
            "description",
            "quality_score",
            "created_date",
        ]

        # Add any additional columns
        for key in sorted(all_keys):
            if key not in display_columns and not key.startswith("_"):
                display_columns.append(key)

        # Set table dimensions
        self.results_table.setRowCount(len(results))
        self.results_table.setColumnCount(len(display_columns))
        self.results_table.setHorizontalHeaderLabels(
            [col.replace("_", " ").title() for col in display_columns]
        )

        # Populate table
        for row, item in enumerate(results):
            for col, column_name in enumerate(display_columns):
                value = item.get(column_name, "")

                # Format value for display
                if isinstance(value, list):
                    display_value = ", ".join(str(v) for v in value[:3])
                    if len(value) > 3:
                        display_value += f" (+{len(value) - 3} more)"
                elif isinstance(value, dict):
                    display_value = f"{{{len(value)} items}}"
                elif isinstance(value, (int, float)) and column_name == "quality_score":
                    display_value = f"{value}%"
                else:
                    display_value = str(value) if value is not None else ""

                # Truncate long text
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."

                table_item = QTableWidgetItem(display_value)
                table_item.setToolTip(str(value))
                table_item.setData(Qt.ItemDataRole.UserRole, item)

                self.results_table.setItem(row, col, table_item)

        # Resize columns
        self.results_table.resizeColumnsToContents()

        # Update summary
        self._update_summary_stats(results)

    def _update_summary_stats(self, results: List[Dict[str, Any]]):
        """Update summary statistics."""
        if not results:
            self.characters_count_label.setText("Characters: 0")
            self.episodes_count_label.setText("Episodes: 0")
            self.avg_quality_label.setText("Avg Quality: 0%")
            return

        # Count by type
        character_count = sum(
            1 for item in results if item.get("type", "").lower() == "character"
        )
        episode_count = sum(
            1 for item in results if item.get("type", "").lower() == "episode"
        )
