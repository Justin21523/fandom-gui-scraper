# gui/widgets/anime_selector.py
"""
Anime selector widget for choosing target anime and scraping parameters.

This module provides an intuitive interface for users to select anime series,
configure scraping parameters, and preview available data sources.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse

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
    QTextEdit,
    QSpinBox,
    QCheckBox,
    QProgressBar,
    QSplitter,
    QFrame,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QMenu,
    QToolButton,
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QCursor

from utils.logger import get_logger


@dataclass
class AnimeInfo:
    """Data class for anime information."""

    name: str
    url: str
    wiki_type: str
    estimated_characters: int = 0
    estimated_episodes: int = 0
    last_updated: str = ""
    status: str = "unknown"
    description: str = ""
    categories: List[str] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = []


@dataclass
class ScrapingConfig:
    """Data class for scraping configuration."""

    anime_name: str
    target_url: str
    spider_type: str
    max_characters: int = 100
    max_episodes: int = 50
    include_images: bool = True
    include_episodes: bool = True
    include_characters: bool = True
    custom_selectors: Dict[str, str] = None

    def __post_init__(self):
        if self.custom_selectors is None:
            self.custom_selectors = {}


class AnimeSelector(QWidget):
    """
    Widget for selecting anime and configuring scraping parameters.

    Provides comprehensive interface for:
    - Searching and selecting anime series
    - Configuring scraping parameters
    - Previewing available data
    - Validating target URLs
    """

    # Custom signals
    anime_selected = pyqtSignal(object)  # AnimeInfo
    config_changed = pyqtSignal(object)  # ScrapingConfig
    url_validated = pyqtSignal(bool, str)  # success, message
    preview_requested = pyqtSignal(str)  # url

    def __init__(self, parent=None):
        """Initialize anime selector widget."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)

        # State
        self.current_anime = None
        self.available_anime = []
        self.validation_worker = None

        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.load_anime_database()

        self.logger.info("Anime selector widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - anime selection
        left_panel = self._create_selection_panel()
        splitter.addWidget(left_panel)

        # Right panel - configuration
        right_panel = self._create_configuration_panel()
        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([300, 400])

        # Status bar
        self.status_bar = self._create_status_bar()
        layout.addWidget(self.status_bar)

    def _create_selection_panel(self) -> QWidget:
        """Create anime selection panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Search section
        search_group = QGroupBox("Search Anime")
        search_layout = QVBoxLayout(search_group)

        # Search input
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter anime name or URL...")
        self.search_btn = QPushButton("Search")
        self.search_btn.setDefault(True)

        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.search_btn)
        search_layout.addLayout(search_input_layout)

        # Filter options
        filter_layout = QHBoxLayout()
        self.wiki_filter = QComboBox()
        self.wiki_filter.addItems(["All Wikis", "Fandom", "Wikia", "Custom"])
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Active", "Completed", "Ongoing"])

        filter_layout.addWidget(QLabel("Wiki:"))
        filter_layout.addWidget(self.wiki_filter)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        search_layout.addLayout(filter_layout)

        layout.addWidget(search_group)

        # Results section
        results_group = QGroupBox("Available Anime")
        results_layout = QVBoxLayout(results_group)

        # Anime list
        self.anime_list = QListWidget()
        self.anime_list.setAlternatingRowColors(True)
        results_layout.addWidget(self.anime_list)

        # Quick actions
        actions_layout = QHBoxLayout()
        self.add_custom_btn = QPushButton("Add Custom")
        self.refresh_btn = QPushButton("Refresh")
        self.preview_btn = QPushButton("Preview")

        actions_layout.addWidget(self.add_custom_btn)
        actions_layout.addWidget(self.refresh_btn)
        actions_layout.addWidget(self.preview_btn)
        results_layout.addLayout(actions_layout)

        layout.addWidget(results_group)

        return panel

    def _create_configuration_panel(self) -> QWidget:
        """Create configuration panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tab widget for organization
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Basic configuration tab
        basic_tab = self._create_basic_config_tab()
        tab_widget.addTab(basic_tab, "Basic Settings")

        # Advanced configuration tab
        advanced_tab = self._create_advanced_config_tab()
        tab_widget.addTab(advanced_tab, "Advanced")

        # Preview tab
        preview_tab = self._create_preview_tab()
        tab_widget.addTab(preview_tab, "Preview")

        return panel

    def _create_basic_config_tab(self) -> QWidget:
        """Create basic configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Selected anime info
        info_group = QGroupBox("Selected Anime")
        info_layout = QFormLayout(info_group)

        self.anime_name_label = QLabel("None selected")
        self.anime_url_label = QLabel("-")
        self.anime_status_label = QLabel("-")

        info_layout.addRow("Name:", self.anime_name_label)
        info_layout.addRow("URL:", self.anime_url_label)
        info_layout.addRow("Status:", self.anime_status_label)

        layout.addWidget(info_group)

        # Scraping parameters
        params_group = QGroupBox("Scraping Parameters")
        params_layout = QFormLayout(params_group)

        # Max characters
        self.max_characters_spinbox = QSpinBox()
        self.max_characters_spinbox.setRange(1, 1000)
        self.max_characters_spinbox.setValue(100)
        params_layout.addRow("Max Characters:", self.max_characters_spinbox)

        # Max episodes
        self.max_episodes_spinbox = QSpinBox()
        self.max_episodes_spinbox.setRange(1, 2000)
        self.max_episodes_spinbox.setValue(50)
        params_layout.addRow("Max Episodes:", self.max_episodes_spinbox)

        layout.addWidget(params_group)

        # Content options
        content_group = QGroupBox("Content to Scrape")
        content_layout = QVBoxLayout(content_group)

        self.include_characters_checkbox = QCheckBox("Character profiles")
        self.include_characters_checkbox.setChecked(True)
        content_layout.addWidget(self.include_characters_checkbox)

        self.include_episodes_checkbox = QCheckBox("Episode information")
        self.include_episodes_checkbox.setChecked(True)
        content_layout.addWidget(self.include_episodes_checkbox)

        self.include_images_checkbox = QCheckBox("Character images")
        self.include_images_checkbox.setChecked(True)
        content_layout.addWidget(self.include_images_checkbox)

        layout.addWidget(content_group)

        # URL validation
        validation_group = QGroupBox("URL Validation")
        validation_layout = QVBoxLayout(validation_group)

        # Custom URL input
        url_input_layout = QHBoxLayout()
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setPlaceholderText("Enter custom anime wiki URL...")
        self.validate_url_btn = QPushButton("Validate")

        url_input_layout.addWidget(self.custom_url_input)
        url_input_layout.addWidget(self.validate_url_btn)
        validation_layout.addLayout(url_input_layout)

        # Validation status
        self.validation_status_label = QLabel("Enter URL to validate")
        self.validation_status_label.setStyleSheet("color: gray;")
        validation_layout.addWidget(self.validation_status_label)

        layout.addWidget(validation_group)

        layout.addStretch()
        return tab

    def _create_advanced_config_tab(self) -> QWidget:
        """Create advanced configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Spider selection
        spider_group = QGroupBox("Spider Configuration")
        spider_layout = QFormLayout(spider_group)

        self.spider_type_combo = QComboBox()
        self.spider_type_combo.addItems(
            [
                "Auto-detect",
                "Fandom Spider",
                "One Piece Spider",
                "Naruto Spider",
                "Generic Spider",
            ]
        )
        spider_layout.addRow("Spider Type:", self.spider_type_combo)

        layout.addWidget(spider_group)

        # Custom selectors
        selectors_group = QGroupBox("Custom CSS Selectors")
        selectors_layout = QVBoxLayout(selectors_group)

        # Selector table
        self.selectors_table = QTableWidget()
        self.selectors_table.setColumnCount(2)
        self.selectors_table.setHorizontalHeaderLabels(["Element", "CSS Selector"])
        self.selectors_table.horizontalHeader().setStretchLastSection(True)

        # Add default selectors
        default_selectors = [
            ("Character Name", ".pi-item[data-source='name'] .pi-data-value"),
            ("Character Image", ".pi-image img"),
            ("Infobox", ".portable-infobox"),
            ("Description", ".mw-parser-output > p:first-of-type"),
        ]

        self.selectors_table.setRowCount(len(default_selectors))
        for row, (element, selector) in enumerate(default_selectors):
            self.selectors_table.setItem(row, 0, QTableWidgetItem(element))
            self.selectors_table.setItem(row, 1, QTableWidgetItem(selector))

        selectors_layout.addWidget(self.selectors_table)

        # Selector controls
        selector_controls = QHBoxLayout()
        self.add_selector_btn = QPushButton("Add Selector")
        self.remove_selector_btn = QPushButton("Remove Selected")
        self.reset_selectors_btn = QPushButton("Reset to Defaults")

        selector_controls.addWidget(self.add_selector_btn)
        selector_controls.addWidget(self.remove_selector_btn)
        selector_controls.addStretch()
        selector_controls.addWidget(self.reset_selectors_btn)
        selectors_layout.addLayout(selector_controls)

        layout.addWidget(selectors_group)

        # Performance settings
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QFormLayout(performance_group)

        self.request_delay_spinbox = QSpinBox()
        self.request_delay_spinbox.setRange(0, 10)
        self.request_delay_spinbox.setValue(1)
        self.request_delay_spinbox.setSuffix(" seconds")
        performance_layout.addRow("Request Delay:", self.request_delay_spinbox)

        self.concurrent_requests_spinbox = QSpinBox()
        self.concurrent_requests_spinbox.setRange(1, 10)
        self.concurrent_requests_spinbox.setValue(3)
        performance_layout.addRow(
            "Concurrent Requests:", self.concurrent_requests_spinbox
        )

        layout.addWidget(performance_group)

        layout.addStretch()
        return tab

    def _create_preview_tab(self) -> QWidget:
        """Create preview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Preview controls
        controls_layout = QHBoxLayout()
        self.preview_url_input = QLineEdit()
        self.preview_url_input.setPlaceholderText("URL to preview...")
        self.load_preview_btn = QPushButton("Load Preview")
        self.clear_preview_btn = QPushButton("Clear")

        controls_layout.addWidget(self.preview_url_input)
        controls_layout.addWidget(self.load_preview_btn)
        controls_layout.addWidget(self.clear_preview_btn)
        layout.addLayout(controls_layout)

        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Preview content will appear here...")
        layout.addWidget(self.preview_text)

        # Preview stats
        stats_layout = QHBoxLayout()
        self.characters_found_label = QLabel("Characters: 0")
        self.episodes_found_label = QLabel("Episodes: 0")
        self.images_found_label = QLabel("Images: 0")

        stats_layout.addWidget(self.characters_found_label)
        stats_layout.addWidget(self.episodes_found_label)
        stats_layout.addWidget(self.images_found_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        return tab

    def _create_status_bar(self) -> QWidget:
        """Create status bar."""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(status_frame)
        layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.progress_bar)

        return status_frame

    def setup_connections(self):
        """Set up signal connections."""
        # Search functionality
        self.search_btn.clicked.connect(self.search_anime)
        self.search_input.returnPressed.connect(self.search_anime)
        self.search_input.textChanged.connect(self._on_search_text_changed)

        # Filters
        self.wiki_filter.currentTextChanged.connect(self.filter_anime_list)
        self.status_filter.currentTextChanged.connect(self.filter_anime_list)

        # Anime list
        self.anime_list.itemSelectionChanged.connect(self._on_anime_selection_changed)
        self.anime_list.itemDoubleClicked.connect(self._on_anime_double_clicked)

        # Action buttons
        self.add_custom_btn.clicked.connect(self.add_custom_anime)
        self.refresh_btn.clicked.connect(self.refresh_anime_list)
        self.preview_btn.clicked.connect(self.preview_selected_anime)

        # URL validation
        self.validate_url_btn.clicked.connect(self.validate_custom_url)
        self.custom_url_input.returnPressed.connect(self.validate_custom_url)

        # Configuration changes
        self.max_characters_spinbox.valueChanged.connect(self._on_config_changed)
        self.max_episodes_spinbox.valueChanged.connect(self._on_config_changed)
        self.include_characters_checkbox.toggled.connect(self._on_config_changed)
        self.include_episodes_checkbox.toggled.connect(self._on_config_changed)
        self.include_images_checkbox.toggled.connect(self._on_config_changed)
        self.spider_type_combo.currentTextChanged.connect(self._on_config_changed)

        # Selector management
        self.add_selector_btn.clicked.connect(self.add_custom_selector)
        self.remove_selector_btn.clicked.connect(self.remove_selected_selector)
        self.reset_selectors_btn.clicked.connect(self.reset_selectors)

        # Preview functionality
        self.load_preview_btn.clicked.connect(self.load_preview)
        self.clear_preview_btn.clicked.connect(self.clear_preview)

    def load_anime_database(self):
        """Load anime database from configuration."""
        try:
            # Load from built-in database
            anime_db_path = (
                Path(__file__).parent.parent.parent / "data" / "anime_database.json"
            )

            if anime_db_path.exists():
                with open(anime_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.available_anime = [
                        AnimeInfo(**anime) for anime in data.get("anime", [])
                    ]
            else:
                # Create default anime list
                self.available_anime = self._get_default_anime_list()

            self.update_anime_list()
            self.logger.info(f"Loaded {len(self.available_anime)} anime entries")

        except Exception as e:
            self.logger.error(f"Failed to load anime database: {e}")
            self.available_anime = self._get_default_anime_list()
            self.update_anime_list()

    def _get_default_anime_list(self) -> List[AnimeInfo]:
        """Get default anime list."""
        return [
            AnimeInfo(
                name="One Piece",
                url="https://onepiece.fandom.com/wiki/",
                wiki_type="Fandom",
                estimated_characters=800,
                estimated_episodes=1000,
                status="ongoing",
                description="Popular pirate adventure anime",
            ),
            AnimeInfo(
                name="Naruto",
                url="https://naruto.fandom.com/wiki/",
                wiki_type="Fandom",
                estimated_characters=400,
                estimated_episodes=720,
                status="completed",
                description="Ninja adventure anime",
            ),
            AnimeInfo(
                name="Dragon Ball",
                url="https://dragonball.fandom.com/wiki/",
                wiki_type="Fandom",
                estimated_characters=300,
                estimated_episodes=500,
                status="completed",
                description="Martial arts adventure anime",
            ),
        ]

    def update_anime_list(self):
        """Update the anime list display."""
        self.anime_list.clear()

        for anime in self.available_anime:
            item = QListWidgetItem()
            item.setText(anime.name)
            item.setData(Qt.ItemDataRole.UserRole, anime)

            # Set tooltip with anime info
            tooltip = f"Name: {anime.name}\nURL: {anime.url}\nType: {anime.wiki_type}\nStatus: {anime.status}"
            if anime.description:
                tooltip += f"\nDescription: {anime.description}"
            item.setToolTip(tooltip)

            # Set icon based on status
            if anime.status == "ongoing":
                item.setIcon(
                    self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay)
                )
            elif anime.status == "completed":
                item.setIcon(
                    self.style().standardIcon(
                        self.style().StandardPixmap.SP_DialogApplyButton
                    )
                )
            else:
                item.setIcon(
                    self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
                )

            self.anime_list.addItem(item)

    def filter_anime_list(self):
        """Filter anime list based on selected filters."""
        wiki_filter = self.wiki_filter.currentText()
        status_filter = self.status_filter.currentText()

        for i in range(self.anime_list.count()):
            item = self.anime_list.item(i)
            anime = item.data(Qt.ItemDataRole.UserRole)

            # Apply filters
            show_item = True

            if wiki_filter != "All Wikis" and anime.wiki_type != wiki_filter:
                show_item = False

            if status_filter != "All Status" and anime.status != status_filter.lower():
                show_item = False

            item.setHidden(not show_item)

    def search_anime(self):
        """Search for anime based on input text."""
        search_text = self.search_input.text().strip().lower()

        if not search_text:
            # Show all items if search is empty
            for i in range(self.anime_list.count()):
                self.anime_list.item(i).setHidden(False)
            return

        # Check if input is a URL
        if search_text.startswith(("http://", "https://")):
            self.custom_url_input.setText(search_text)
            self.validate_custom_url()
            return

        # Text search
        for i in range(self.anime_list.count()):
            item = self.anime_list.item(i)
            anime = item.data(Qt.ItemDataRole.UserRole)

            # Search in name and description
            matches = (
                search_text in anime.name.lower()
                or search_text in anime.description.lower()
                or search_text in anime.url.lower()
            )

            item.setHidden(not matches)

        self.update_status(f"Search: '{search_text}'")

    def add_custom_anime(self):
        """Add custom anime entry."""
        from gui.dialogs.custom_anime_dialog import CustomAnimeDialog

        dialog = CustomAnimeDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            anime_info = dialog.get_anime_info()
            self.available_anime.append(anime_info)
            self.update_anime_list()
            self.logger.info(f"Added custom anime: {anime_info.name}")

    def refresh_anime_list(self):
        """Refresh anime list."""
        self.load_anime_database()
        self.update_status("Anime list refreshed")

    def preview_selected_anime(self):
        """Preview selected anime."""
        current_item = self.anime_list.currentItem()
        if current_item:
            anime = current_item.data(Qt.ItemDataRole.UserRole)
            self.preview_url_input.setText(anime.url)
            self.load_preview()

    def validate_custom_url(self):
        """Validate custom URL."""
        url = self.custom_url_input.text().strip()
        if not url:
            self.validation_status_label.setText("Enter URL to validate")
            self.validation_status_label.setStyleSheet("color: gray;")
            return

        # Start validation
        self.validate_url_btn.setEnabled(False)
        self.validate_url_btn.setText("Validating...")
        self.validation_status_label.setText("Validating URL...")
        self.validation_status_label.setStyleSheet("color: orange;")

        # Create validation worker
        self.validation_worker = URLValidationWorker(url)
        self.validation_worker.finished.connect(self._on_validation_finished)
        self.validation_worker.start()

    def load_preview(self):
        """Load preview content."""
        url = self.preview_url_input.text().strip()
        if not url:
            return

        self.load_preview_btn.setEnabled(False)
        self.load_preview_btn.setText("Loading...")
        self.clear_preview()

        # Create preview worker
        self.preview_worker = PreviewWorker(url)
        self.preview_worker.finished.connect(self._on_preview_finished)
        self.preview_worker.progress.connect(self._on_preview_progress)
        self.preview_worker.start()

    def clear_preview(self):
        """Clear preview content."""
        self.preview_text.clear()
        self.characters_found_label.setText("Characters: 0")
        self.episodes_found_label.setText("Episodes: 0")
        self.images_found_label.setText("Images: 0")

    def get_current_config(self) -> Optional[ScrapingConfig]:
        """Get current scraping configuration."""
        if not self.current_anime:
            return None

        # Get custom selectors
        custom_selectors = {}
        for row in range(self.selectors_table.rowCount()):
            element_item = self.selectors_table.item(row, 0)
            selector_item = self.selectors_table.item(row, 1)

            if element_item and selector_item:
                element = element_item.text()
                selector = selector_item.text()
                if element and selector:
                    custom_selectors[element] = selector

        return ScrapingConfig(
            anime_name=self.current_anime.name,
            target_url=self.custom_url_input.text() or self.current_anime.url,
            spider_type=self.spider_type_combo.currentText(),
            max_characters=self.max_characters_spinbox.value(),
            max_episodes=self.max_episodes_spinbox.value(),
            include_images=self.include_images_checkbox.isChecked(),
            include_episodes=self.include_episodes_checkbox.isChecked(),
            include_characters=self.include_characters_checkbox.isChecked(),
            custom_selectors=custom_selectors,
        )

    def update_status(self, message: str):
        """Update status message."""
        self.status_label.setText(message)

        # Auto-clear status after 5 seconds
        QTimer.singleShot(5000, lambda: self.status_label.setText("Ready"))

    # Event handlers
    def _on_search_text_changed(self, text: str):
        """Handle search text changes."""
        if not text:
            self.filter_anime_list()  # Apply current filters

    def _on_anime_selection_changed(self):
        """Handle anime selection change."""
        current_item = self.anime_list.currentItem()
        if current_item:
            self.current_anime = current_item.data(Qt.ItemDataRole.UserRole)
            self._update_anime_info_display()
            self.anime_selected.emit(self.current_anime)
            self._on_config_changed()

    def _on_anime_double_clicked(self, item: QListWidgetItem):
        """Handle anime double click."""
        anime = item.data(Qt.ItemDataRole.UserRole)
        self.preview_url_input.setText(anime.url)
        self.load_preview()

    def _on_config_changed(self):
        """Handle configuration changes."""
        config = self.get_current_config()
        if config:
            self.config_changed.emit(config)

    def _update_anime_info_display(self):
        """Update anime information display."""
        if not self.current_anime:
            self.anime_name_label.setText("None selected")
            self.anime_url_label.setText("-")
            self.anime_status_label.setText("-")
            return

        self.anime_name_label.setText(self.current_anime.name)
        self.anime_url_label.setText(self.current_anime.url)
        self.anime_status_label.setText(self.current_anime.status.title())

        # Auto-fill custom URL if empty
        if not self.custom_url_input.text():
            self.custom_url_input.setText(self.current_anime.url)

    @pyqtSlot(bool, str)
    def _on_validation_finished(self, success: bool, message: str):
        """Handle URL validation completion."""
        self.validate_url_btn.setEnabled(True)
        self.validate_url_btn.setText("Validate")

        if success:
            self.validation_status_label.setText("✓ Valid URL")
            self.validation_status_label.setStyleSheet("color: green;")
        else:
            self.validation_status_label.setText("✗ Invalid URL")
            self.validation_status_label.setStyleSheet("color: red;")

        self.url_validated.emit(success, message)

    @pyqtSlot(bool, str, dict)
    def _on_preview_finished(self, success: bool, message: str, stats: dict):
        """Handle preview loading completion."""
        self.load_preview_btn.setEnabled(True)
        self.load_preview_btn.setText("Load Preview")
        self.progress_bar.setVisible(False)

        if success:
            self.preview_text.setPlainText(message)

            # Update statistics
            self.characters_found_label.setText(
                f"Characters: {stats.get('characters', 0)}"
            )
            self.episodes_found_label.setText(f"Episodes: {stats.get('episodes', 0)}")
            self.images_found_label.setText(f"Images: {stats.get('images', 0)}")

            self.update_status("Preview loaded successfully")
        else:
            self.preview_text.setPlainText(f"Failed to load preview: {message}")
            self.update_status("Preview loading failed")

    @pyqtSlot(str, int)
    def _on_preview_progress(self, message: str, progress: int):
        """Handle preview loading progress."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(progress)
        self.update_status(message)

    # Selector management methods
    def add_custom_selector(self):
        """Add custom CSS selector."""
        row = self.selectors_table.rowCount()
        self.selectors_table.insertRow(row)

        self.selectors_table.setItem(row, 0, QTableWidgetItem("New Element"))
        self.selectors_table.setItem(row, 1, QTableWidgetItem(""))

        # Start editing the new row
        self.selectors_table.editItem(self.selectors_table.item(row, 0))

    def remove_selected_selector(self):
        """Remove selected CSS selector."""
        current_row = self.selectors_table.currentRow()
        if current_row >= 0:
            self.selectors_table.removeRow(current_row)

    def reset_selectors(self):
        """Reset selectors to defaults."""
        self.selectors_table.setRowCount(0)

        default_selectors = [
            ("Character Name", ".pi-item[data-source='name'] .pi-data-value"),
            ("Character Image", ".pi-image img"),
            ("Infobox", ".portable-infobox"),
            ("Description", ".mw-parser-output > p:first-of-type"),
        ]

        self.selectors_table.setRowCount(len(default_selectors))
        for row, (element, selector) in enumerate(default_selectors):
            self.selectors_table.setItem(row, 0, QTableWidgetItem(element))
            self.selectors_table.setItem(row, 1, QTableWidgetItem(selector))


class URLValidationWorker(QThread):
    """Worker thread for URL validation."""

    finished = pyqtSignal(bool, str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.logger = get_logger(self.__class__.__name__)

    def run(self):
        """Validate URL in background thread."""
        try:
            import requests

            # Basic URL validation
            parsed = urlparse(self.url)
            if not parsed.scheme or not parsed.netloc:
                self.finished.emit(False, "Invalid URL format")
                return

            # Check if URL is accessible
            response = requests.head(self.url, timeout=10, allow_redirects=True)

            if response.status_code == 200:
                self.finished.emit(True, "URL is accessible")
            else:
                self.finished.emit(False, f"HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            self.finished.emit(False, "Request timeout")
        except requests.exceptions.ConnectionError:
            self.finished.emit(False, "Connection error")
        except Exception as e:
            self.finished.emit(False, str(e))


class PreviewWorker(QThread):
    """Worker thread for loading preview content."""

    finished = pyqtSignal(bool, str, dict)
    progress = pyqtSignal(str, int)

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.logger = get_logger(self.__class__.__name__)

    def run(self):
        """Load preview content in background thread."""
        try:
            import requests
            from bs4 import BeautifulSoup

            self.progress.emit("Fetching page...", 20)

            # Fetch page content
            response = requests.get(self.url, timeout=15)
            response.raise_for_status()

            self.progress.emit("Parsing content...", 60)

            # Parse content
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract statistics
            stats = {
                "characters": len(
                    soup.find_all("a", href=lambda x: x and "character" in x.lower())  # type: ignore
                ),
                "episodes": len(
                    soup.find_all("a", href=lambda x: x and "episode" in x.lower())  # type: ignore
                ),
                "images": len(soup.find_all("img")),
            }

            self.progress.emit("Generating preview...", 90)

            # Generate preview text
            title = soup.find("title")
            title_text = title.get_text() if title else "No title"

            # Get first few paragraphs
            paragraphs = soup.find_all("p")[:5]
            content = "\n\n".join(
                [p.get_text()[:200] + "..." for p in paragraphs if p.get_text().strip()]
            )

            preview_text = f"Title: {title_text}\n\n{content}"

            self.progress.emit("Complete", 100)
            self.finished.emit(True, preview_text, stats)

        except Exception as e:
            self.logger.error(f"Preview loading failed: {e}")
            self.finished.emit(False, str(e), {})
