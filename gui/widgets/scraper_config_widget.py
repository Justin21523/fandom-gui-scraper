# gui/widgets/scraper_config_widget.py
"""
Scraper configuration widget for setting up web scraping parameters.

This widget provides a user-friendly interface for configuring all aspects
of the web scraping operation including target selection, rate limiting,
output settings, and advanced options.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QTabWidget,
    QScrollArea,
    QFrame,
    QSlider,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer, QThread
from PyQt6.QtGui import QFont, QIntValidator, QDoubleValidator, QIcon

from utils.logger import get_logger
from utils.config_manager import ConfigManager


class ScraperConfigWidget(QWidget):
    """
    Comprehensive scraper configuration widget.

    Provides interfaces for:
    - Target website and anime selection
    - Rate limiting and politeness settings
    - Data extraction configuration
    - Output and storage options
    - Advanced scraping parameters
    """

    # Signals for external communication
    config_changed = pyqtSignal(dict)  # Emitted when configuration changes
    config_validated = pyqtSignal(bool)  # Emitted after validation
    test_connection_requested = pyqtSignal(str)  # Test target URL
    preview_requested = pyqtSignal(dict)  # Preview scraping results

    def __init__(self, parent=None):
        """
        Initialize the scraper configuration widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(self.__class__.__name__)

        # Configuration manager
        self.config_manager = ConfigManager()

        # Current configuration state
        self.current_config = {}
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_configuration)

        # Available anime presets
        self.anime_presets = self.load_anime_presets()

        # Set up UI
        self.setup_ui()
        self.setup_connections()
        self.load_default_configuration()

        self.logger.info("Scraper config widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Create tab widget for organized configuration
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create configuration tabs
        self.create_target_tab()
        self.create_extraction_tab()
        self.create_performance_tab()
        self.create_storage_tab()
        self.create_advanced_tab()

        # Configuration actions
        actions_frame = self.create_actions_section()
        main_layout.addWidget(actions_frame)

    def create_target_tab(self):
        """Create the target configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Target selection group
        target_group = QGroupBox("Target Selection")
        target_layout = QFormLayout(target_group)

        # Anime selection
        self.anime_combo = QComboBox()
        self.anime_combo.setEditable(True)
        self.anime_combo.addItems(list(self.anime_presets.keys()))
        self.anime_combo.currentTextChanged.connect(self.on_anime_changed)
        target_layout.addRow("Anime/Series:", self.anime_combo)

        # Base URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://onepiece.fandom.com/wiki/")
        self.base_url_edit.textChanged.connect(self.on_config_changed)
        target_layout.addRow("Base URL:", self.base_url_edit)

        # Character list URL
        self.character_list_url_edit = QLineEdit()
        self.character_list_url_edit.setPlaceholderText("Characters category page URL")
        self.character_list_url_edit.textChanged.connect(self.on_config_changed)
        target_layout.addRow("Character List URL:", self.character_list_url_edit)

        # Test connection button
        test_layout = QHBoxLayout()
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_connection_btn)

        self.connection_status = QLabel("Not tested")
        self.connection_status.setStyleSheet("color: gray;")
        test_layout.addWidget(self.connection_status)
        test_layout.addStretch()

        target_layout.addRow(test_layout)

        layout.addWidget(target_group)

        # URL patterns group
        patterns_group = QGroupBox("URL Patterns")
        patterns_layout = QFormLayout(patterns_group)

        # Character URL pattern
        self.character_pattern_edit = QLineEdit()
        self.character_pattern_edit.setPlaceholderText("/wiki/Character_Name")
        self.character_pattern_edit.textChanged.connect(self.on_config_changed)
        patterns_layout.addRow("Character URL Pattern:", self.character_pattern_edit)

        # Image URL pattern
        self.image_pattern_edit = QLineEdit()
        self.image_pattern_edit.setPlaceholderText("*.jpg, *.png, *.gif")
        self.image_pattern_edit.textChanged.connect(self.on_config_changed)
        patterns_layout.addRow("Image URL Pattern:", self.image_pattern_edit)

        layout.addWidget(patterns_group)

        # Limits group
        limits_group = QGroupBox("Scraping Limits")
        limits_layout = QFormLayout(limits_group)

        # Maximum characters to scrape
        self.max_characters_spin = QSpinBox()
        self.max_characters_spin.setRange(1, 10000)
        self.max_characters_spin.setValue(100)
        self.max_characters_spin.setSuffix(" characters")
        self.max_characters_spin.valueChanged.connect(self.on_config_changed)
        limits_layout.addRow("Max Characters:", self.max_characters_spin)

        # Maximum pages per character
        self.max_pages_spin = QSpinBox()
        self.max_pages_spin.setRange(1, 50)
        self.max_pages_spin.setValue(5)
        self.max_pages_spin.setSuffix(" pages")
        self.max_pages_spin.valueChanged.connect(self.on_config_changed)
        limits_layout.addRow("Max Pages per Character:", self.max_pages_spin)

        # Maximum images per character
        self.max_images_spin = QSpinBox()
        self.max_images_spin.setRange(0, 100)
        self.max_images_spin.setValue(10)
        self.max_images_spin.setSuffix(" images")
        self.max_images_spin.valueChanged.connect(self.on_config_changed)
        limits_layout.addRow("Max Images per Character:", self.max_images_spin)

        layout.addWidget(limits_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Target & Limits")

    def create_extraction_tab(self):
        """Create the data extraction configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # CSS Selectors group
        selectors_group = QGroupBox("CSS Selectors Configuration")
        selectors_layout = QFormLayout(selectors_group)

        # Character name selector
        self.name_selector_edit = QLineEdit()
        self.name_selector_edit.setPlaceholderText("h1.page-header__title")
        self.name_selector_edit.textChanged.connect(self.on_config_changed)
        selectors_layout.addRow("Character Name:", self.name_selector_edit)

        # Description selector
        self.description_selector_edit = QLineEdit()
        self.description_selector_edit.setPlaceholderText(
            ".mw-parser-output > p:first-of-type"
        )
        self.description_selector_edit.textChanged.connect(self.on_config_changed)
        selectors_layout.addRow("Description:", self.description_selector_edit)

        # Infobox selector
        self.infobox_selector_edit = QLineEdit()
        self.infobox_selector_edit.setPlaceholderText(".portable-infobox")
        self.infobox_selector_edit.textChanged.connect(self.on_config_changed)
        selectors_layout.addRow("Infobox:", self.infobox_selector_edit)

        # Image selector
        self.image_selector_edit = QLineEdit()
        self.image_selector_edit.setPlaceholderText(".image img, .infobox-image img")
        self.image_selector_edit.textChanged.connect(self.on_config_changed)
        selectors_layout.addRow("Images:", self.image_selector_edit)

        # Categories selector
        self.categories_selector_edit = QLineEdit()
        self.categories_selector_edit.setPlaceholderText("#mw-normal-catlinks a")
        self.categories_selector_edit.textChanged.connect(self.on_config_changed)
        selectors_layout.addRow("Categories:", self.categories_selector_edit)

        layout.addWidget(selectors_group)

        # Data extraction options
        extraction_group = QGroupBox("Extraction Options")
        extraction_layout = QVBoxLayout(extraction_group)

        # Checkboxes for what to extract
        extraction_options_layout = QGridLayout()

        self.extract_infobox_check = QCheckBox("Extract Infobox Data")
        self.extract_infobox_check.setChecked(True)
        self.extract_infobox_check.toggled.connect(self.on_config_changed)
        extraction_options_layout.addWidget(self.extract_infobox_check, 0, 0)

        self.extract_images_check = QCheckBox("Download Images")
        self.extract_images_check.setChecked(True)
        self.extract_images_check.toggled.connect(self.on_config_changed)
        extraction_options_layout.addWidget(self.extract_images_check, 0, 1)

        self.extract_categories_check = QCheckBox("Extract Categories")
        self.extract_categories_check.setChecked(True)
        self.extract_categories_check.toggled.connect(self.on_config_changed)
        extraction_options_layout.addWidget(self.extract_categories_check, 1, 0)

        self.extract_relationships_check = QCheckBox("Extract Relationships")
        self.extract_relationships_check.setChecked(False)
        self.extract_relationships_check.toggled.connect(self.on_config_changed)
        extraction_options_layout.addWidget(self.extract_relationships_check, 1, 1)

        self.extract_abilities_check = QCheckBox("Extract Abilities")
        self.extract_abilities_check.setChecked(False)
        self.extract_abilities_check.toggled.connect(self.on_config_changed)
        extraction_options_layout.addWidget(self.extract_abilities_check, 2, 0)

        self.extract_appearances_check = QCheckBox("Extract Appearances")
        self.extract_appearances_check.setChecked(False)
        self.extract_appearances_check.toggled.connect(self.on_config_changed)
        extraction_options_layout.addWidget(self.extract_appearances_check, 2, 1)

        extraction_layout.addLayout(extraction_options_layout)
        layout.addWidget(extraction_group)

        # Custom fields group
        custom_group = QGroupBox("Custom Fields")
        custom_layout = QVBoxLayout(custom_group)

        # Custom fields table
        self.custom_fields_table = QTableWidget(0, 3)
        self.custom_fields_table.setHorizontalHeaderLabels(
            ["Field Name", "CSS Selector", "Data Type"]
        )
        self.custom_fields_table.horizontalHeader().setStretchLastSection(True)  # type: ignore
        custom_layout.addWidget(self.custom_fields_table)

        # Custom fields controls
        custom_controls_layout = QHBoxLayout()

        add_field_btn = QPushButton("Add Field")
        add_field_btn.clicked.connect(self.add_custom_field)
        custom_controls_layout.addWidget(add_field_btn)

        remove_field_btn = QPushButton("Remove Field")
        remove_field_btn.clicked.connect(self.remove_custom_field)
        custom_controls_layout.addWidget(remove_field_btn)

        custom_controls_layout.addStretch()
        custom_layout.addLayout(custom_controls_layout)
        layout.addWidget(custom_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Data Extraction")

    def create_performance_tab(self):
        """Create the performance and rate limiting tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Rate limiting group
        rate_group = QGroupBox("Rate Limiting")
        rate_layout = QFormLayout(rate_group)

        # Download delay
        self.download_delay_spin = QDoubleSpinBox()
        self.download_delay_spin.setRange(0.1, 10.0)
        self.download_delay_spin.setValue(1.0)
        self.download_delay_spin.setSingleStep(0.1)
        self.download_delay_spin.setSuffix(" seconds")
        self.download_delay_spin.valueChanged.connect(self.on_config_changed)
        rate_layout.addRow("Download Delay:", self.download_delay_spin)

        # Random delay
        self.random_delay_check = QCheckBox("Randomize Delay")
        self.random_delay_check.setChecked(True)
        self.random_delay_check.toggled.connect(self.on_config_changed)
        rate_layout.addRow("Random Delay:", self.random_delay_check)

        # Concurrent requests
        self.concurrent_requests_spin = QSpinBox()
        self.concurrent_requests_spin.setRange(1, 16)
        self.concurrent_requests_spin.setValue(8)
        self.concurrent_requests_spin.valueChanged.connect(self.on_config_changed)
        rate_layout.addRow("Concurrent Requests:", self.concurrent_requests_spin)

        # Auto throttle
        self.auto_throttle_check = QCheckBox("Enable Auto Throttle")
        self.auto_throttle_check.setChecked(True)
        self.auto_throttle_check.toggled.connect(self.on_config_changed)
        rate_layout.addRow("Auto Throttle:", self.auto_throttle_check)

        layout.addWidget(rate_group)

        # Retry settings group
        retry_group = QGroupBox("Retry Settings")
        retry_layout = QFormLayout(retry_group)

        # Retry times
        self.retry_times_spin = QSpinBox()
        self.retry_times_spin.setRange(0, 10)
        self.retry_times_spin.setValue(3)
        self.retry_times_spin.valueChanged.connect(self.on_config_changed)
        retry_layout.addRow("Retry Times:", self.retry_times_spin)

        # Retry delay
        self.retry_delay_spin = QDoubleSpinBox()
        self.retry_delay_spin.setRange(1.0, 60.0)
        self.retry_delay_spin.setValue(5.0)
        self.retry_delay_spin.setSuffix(" seconds")
        self.retry_delay_spin.valueChanged.connect(self.on_config_changed)
        retry_layout.addRow("Retry Delay:", self.retry_delay_spin)

        # Retry HTTP codes
        self.retry_codes_edit = QLineEdit()
        self.retry_codes_edit.setText("500,502,503,504,408,429")
        self.retry_codes_edit.setPlaceholderText("500,502,503,504,408,429")
        self.retry_codes_edit.textChanged.connect(self.on_config_changed)
        retry_layout.addRow("Retry HTTP Codes:", self.retry_codes_edit)

        layout.addWidget(retry_group)

        # Memory and cache settings
        memory_group = QGroupBox("Memory & Cache")
        memory_layout = QFormLayout(memory_group)

        # Memory limit
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(128, 8192)
        self.memory_limit_spin.setValue(2048)
        self.memory_limit_spin.setSuffix(" MB")
        self.memory_limit_spin.valueChanged.connect(self.on_config_changed)
        memory_layout.addRow("Memory Limit:", self.memory_limit_spin)

        # Cache enabled
        self.cache_enabled_check = QCheckBox("Enable HTTP Cache")
        self.cache_enabled_check.setChecked(False)
        self.cache_enabled_check.toggled.connect(self.on_config_changed)
        memory_layout.addRow("HTTP Cache:", self.cache_enabled_check)

        # Cache expiration
        self.cache_expiration_spin = QSpinBox()
        self.cache_expiration_spin.setRange(60, 86400)
        self.cache_expiration_spin.setValue(3600)
        self.cache_expiration_spin.setSuffix(" seconds")
        self.cache_expiration_spin.setEnabled(False)
        self.cache_expiration_spin.valueChanged.connect(self.on_config_changed)
        self.cache_enabled_check.toggled.connect(self.cache_expiration_spin.setEnabled)
        memory_layout.addRow("Cache Expiration:", self.cache_expiration_spin)

        layout.addWidget(memory_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Performance")

    def create_storage_tab(self):
        """Create the storage and output configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Output directory group
        output_group = QGroupBox("Output Configuration")
        output_layout = QFormLayout(output_group)

        # Base output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText("./storage")
        self.output_dir_edit.textChanged.connect(self.on_config_changed)
        output_dir_layout.addWidget(self.output_dir_edit)

        browse_output_btn = QPushButton("Browse")
        browse_output_btn.clicked.connect(self.browse_output_directory)
        output_dir_layout.addWidget(browse_output_btn)

        output_layout.addRow("Output Directory:", output_dir_layout)

        # Image storage options
        self.image_storage_check = QCheckBox("Store Images Locally")
        self.image_storage_check.setChecked(True)
        self.image_storage_check.toggled.connect(self.on_config_changed)
        output_layout.addRow("Image Storage:", self.image_storage_check)

        # Image format and quality
        image_layout = QHBoxLayout()
        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["JPEG", "PNG", "WebP"])
        self.image_format_combo.currentTextChanged.connect(self.on_config_changed)
        image_layout.addWidget(self.image_format_combo)

        self.image_quality_spin = QSpinBox()
        self.image_quality_spin.setRange(10, 100)
        self.image_quality_spin.setValue(85)
        self.image_quality_spin.setSuffix("%")
        self.image_quality_spin.valueChanged.connect(self.on_config_changed)
        image_layout.addWidget(self.image_quality_spin)

        output_layout.addRow("Image Format/Quality:", image_layout)

        layout.addWidget(output_group)

        # Database configuration group
        db_group = QGroupBox("Database Configuration")
        db_layout = QFormLayout(db_group)

        # MongoDB connection
        self.mongo_uri_edit = QLineEdit()
        self.mongo_uri_edit.setText("mongodb://localhost:27017/")
        self.mongo_uri_edit.textChanged.connect(self.on_config_changed)
        db_layout.addRow("MongoDB URI:", self.mongo_uri_edit)

        # Database name
        self.db_name_edit = QLineEdit()
        self.db_name_edit.setText("fandom_scraper")
        self.db_name_edit.textChanged.connect(self.on_config_changed)
        db_layout.addRow("Database Name:", self.db_name_edit)

        # Collection name
        self.collection_name_edit = QLineEdit()
        self.collection_name_edit.setText("characters")
        self.collection_name_edit.textChanged.connect(self.on_config_changed)
        db_layout.addRow("Collection Name:", self.collection_name_edit)

        # Test database connection
        test_db_layout = QHBoxLayout()
        self.test_db_btn = QPushButton("Test Database")
        self.test_db_btn.clicked.connect(self.test_database_connection)
        test_db_layout.addWidget(self.test_db_btn)

        self.db_status_label = QLabel("Not tested")
        self.db_status_label.setStyleSheet("color: gray;")
        test_db_layout.addWidget(self.db_status_label)
        test_db_layout.addStretch()

        db_layout.addRow(test_db_layout)

        layout.addWidget(db_group)

        # Export options group
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)

        export_options_layout = QGridLayout()

        self.export_json_check = QCheckBox("Export to JSON")
        self.export_json_check.setChecked(True)
        self.export_json_check.toggled.connect(self.on_config_changed)
        export_options_layout.addWidget(self.export_json_check, 0, 0)

        self.export_csv_check = QCheckBox("Export to CSV")
        self.export_csv_check.setChecked(False)
        self.export_csv_check.toggled.connect(self.on_config_changed)
        export_options_layout.addWidget(self.export_csv_check, 0, 1)

        self.export_excel_check = QCheckBox("Export to Excel")
        self.export_excel_check.setChecked(False)
        self.export_excel_check.toggled.connect(self.on_config_changed)
        export_options_layout.addWidget(self.export_excel_check, 1, 0)

        self.export_pdf_check = QCheckBox("Export to PDF")
        self.export_pdf_check.setChecked(False)
        self.export_pdf_check.toggled.connect(self.on_config_changed)
        export_options_layout.addWidget(self.export_pdf_check, 1, 1)

        export_layout.addLayout(export_options_layout)
        layout.addWidget(export_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Storage")

    def create_advanced_tab(self):
        """Create the advanced configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # User agent and headers group
        headers_group = QGroupBox("Headers & User Agent")
        headers_layout = QFormLayout(headers_group)

        # User agent
        self.user_agent_combo = QComboBox()
        self.user_agent_combo.setEditable(True)
        self.user_agent_combo.addItems(
            [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ]
        )
        self.user_agent_combo.currentTextChanged.connect(self.on_config_changed)
        headers_layout.addRow("User Agent:", self.user_agent_combo)

        # Custom headers
        self.custom_headers_text = QTextEdit()
        self.custom_headers_text.setMaximumHeight(100)
        self.custom_headers_text.setPlaceholderText(
            'Enter custom headers in JSON format:\n{\n  "Accept-Language": "en-US,en;q=0.9"\n}'
        )
        self.custom_headers_text.textChanged.connect(self.on_config_changed)
        headers_layout.addRow("Custom Headers:", self.custom_headers_text)

        layout.addWidget(headers_group)

        # Proxy settings group
        proxy_group = QGroupBox("Proxy Settings")
        proxy_layout = QFormLayout(proxy_group)

        # Enable proxy
        self.proxy_enabled_check = QCheckBox("Enable Proxy")
        self.proxy_enabled_check.toggled.connect(self.on_config_changed)
        proxy_layout.addRow("Use Proxy:", self.proxy_enabled_check)

        # Proxy URL
        self.proxy_url_edit = QLineEdit()
        self.proxy_url_edit.setPlaceholderText("http://proxy.example.com:8080")
        self.proxy_url_edit.setEnabled(False)
        self.proxy_url_edit.textChanged.connect(self.on_config_changed)
        self.proxy_enabled_check.toggled.connect(self.proxy_url_edit.setEnabled)
        proxy_layout.addRow("Proxy URL:", self.proxy_url_edit)

        layout.addWidget(proxy_group)

        # JavaScript and rendering group
        js_group = QGroupBox("JavaScript & Rendering")
        js_layout = QFormLayout(js_group)

        # Enable JavaScript
        self.js_enabled_check = QCheckBox("Enable JavaScript Rendering")
        self.js_enabled_check.setChecked(False)
        self.js_enabled_check.toggled.connect(self.on_config_changed)
        js_layout.addRow("JavaScript:", self.js_enabled_check)

        # Page load timeout
        self.page_timeout_spin = QSpinBox()
        self.page_timeout_spin.setRange(5, 120)
        self.page_timeout_spin.setValue(30)
        self.page_timeout_spin.setSuffix(" seconds")
        self.page_timeout_spin.valueChanged.connect(self.on_config_changed)
        js_layout.addRow("Page Load Timeout:", self.page_timeout_spin)

        layout.addWidget(js_group)

        # Logging and debugging group
        logging_group = QGroupBox("Logging & Debugging")
        logging_layout = QFormLayout(logging_group)

        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self.on_config_changed)
        logging_layout.addRow("Log Level:", self.log_level_combo)

        # Enable stats collection
        self.stats_enabled_check = QCheckBox("Enable Statistics Collection")
        self.stats_enabled_check.setChecked(True)
        self.stats_enabled_check.toggled.connect(self.on_config_changed)
        logging_layout.addRow("Statistics:", self.stats_enabled_check)

        # Debug mode
        self.debug_mode_check = QCheckBox("Enable Debug Mode")
        self.debug_mode_check.setChecked(False)
        self.debug_mode_check.toggled.connect(self.on_config_changed)
        logging_layout.addRow("Debug Mode:", self.debug_mode_check)

        layout.addWidget(logging_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced")

    def create_actions_section(self) -> QFrame:
        """
        Create the actions section with control buttons.

        Returns:
            Frame containing action buttons
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QHBoxLayout(frame)

        # Load configuration button
        load_btn = QPushButton("Load Config")
        load_btn.clicked.connect(self.load_configuration)
        layout.addWidget(load_btn)

        # Save configuration button
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self.save_configuration)
        layout.addWidget(save_btn)

        layout.addStretch()

        # Reset to defaults button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        layout.addWidget(reset_btn)

        # Validate configuration button
        self.validate_btn = QPushButton("Validate Config")
        self.validate_btn.clicked.connect(self.validate_configuration)
        layout.addWidget(self.validate_btn)

        # Preview scraping button
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self.preview_scraping)
        layout.addWidget(preview_btn)

        return frame

    def setup_connections(self):
        """Set up signal-slot connections."""
        # Connect validation timer
        self.validation_timer.timeout.connect(self.validate_configuration)

    def load_anime_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Load anime presets from configuration files.

        Returns:
            Dictionary of anime presets
        """
        presets = {
            "One Piece": {
                "base_url": "https://onepiece.fandom.com/wiki/",
                "character_list_url": "https://onepiece.fandom.com/wiki/Category:Characters",
                "selectors": {
                    "name": "h1.page-header__title",
                    "description": ".mw-parser-output > p:first-of-type",
                    "infobox": ".portable-infobox",
                    "images": ".image img, .infobox-image img",
                    "categories": "#mw-normal-catlinks a",
                },
            },
            "Naruto": {
                "base_url": "https://naruto.fandom.com/wiki/",
                "character_list_url": "https://naruto.fandom.com/wiki/Category:Characters",
                "selectors": {
                    "name": "h1.page-header__title",
                    "description": ".mw-parser-output > p:first-of-type",
                    "infobox": ".portable-infobox",
                    "images": ".image img, .infobox-image img",
                    "categories": "#mw-normal-catlinks a",
                },
            },
            "Dragon Ball": {
                "base_url": "https://dragonball.fandom.com/wiki/",
                "character_list_url": "https://dragonball.fandom.com/wiki/Category:Characters",
                "selectors": {
                    "name": "h1.page-header__title",
                    "description": ".mw-parser-output > p:first-of-type",
                    "infobox": ".portable-infobox",
                    "images": ".image img, .infobox-image img",
                    "categories": "#mw-normal-catlinks a",
                },
            },
        }
        return presets

    def load_default_configuration(self):
        """Load default configuration values."""
        self.logger.info("Loading default configuration")

        # Set default anime (One Piece)
        self.anime_combo.setCurrentText("One Piece")
        self.on_anime_changed("One Piece")

    # Event handlers and slots
    @pyqtSlot()
    def browse_output_directory(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir_edit.text()
        )
        if directory:
            self.output_dir_edit.setText(directory)

    @pyqtSlot()
    def load_configuration(self):
        """Load configuration from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON files (*.json);;All files (*)"
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                self.apply_configuration(config)
                self.logger.info(f"Configuration loaded from {file_path}")

                QMessageBox.information(
                    self, "Success", "Configuration loaded successfully!"
                )

            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                QMessageBox.critical(
                    self, "Error", f"Failed to load configuration:\n{e}"
                )

    @pyqtSlot()
    def save_configuration(self):
        """Save current configuration to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "JSON files (*.json);;All files (*)"
        )

        if file_path:
            try:
                config = self.get_configuration()

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                self.logger.info(f"Configuration saved to {file_path}")

                QMessageBox.information(
                    self, "Success", "Configuration saved successfully!"
                )

            except Exception as e:
                self.logger.error(f"Failed to save configuration: {e}")
                QMessageBox.critical(
                    self, "Error", f"Failed to save configuration:\n{e}"
                )

    @pyqtSlot()
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.load_default_configuration()
            self.logger.info("Configuration reset to defaults")

    @pyqtSlot()
    def validate_configuration(self):
        """Validate current configuration."""
        try:
            config = self.get_configuration()
            errors = []
            warnings = []

            # Validate required fields
            if not config.get("base_url"):
                errors.append("Base URL is required")

            if not config.get("character_list_url"):
                errors.append("Character list URL is required")

            # Validate URL format
            for url_field in ["base_url", "character_list_url"]:
                url = config.get(url_field, "")
                if url and not url.startswith(("http://", "https://")):
                    errors.append(
                        f"{url_field.replace('_', ' ').title()} must start with http:// or https://"
                    )

            # Validate selectors
            required_selectors = ["name_selector", "description_selector"]
            for selector in required_selectors:
                if not config.get(selector):
                    warnings.append(
                        f"{selector.replace('_', ' ').title()} is recommended"
                    )

            # Validate numeric ranges
            if config.get("download_delay", 0) < 0.1:
                warnings.append("Download delay should be at least 0.1 seconds")

            if config.get("concurrent_requests", 1) > 16:
                warnings.append("High concurrent requests may cause rate limiting")

            # Validate MongoDB URI
            mongo_uri = config.get("mongo_uri", "")
            if mongo_uri and not mongo_uri.startswith("mongodb://"):
                errors.append("MongoDB URI must start with mongodb://")

            # Validate output directory
            output_dir = config.get("output_directory", "")
            if output_dir:
                output_path = Path(output_dir)
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create output directory: {e}")

            # Update validation status
            if errors:
                self.validate_btn.setStyleSheet("background-color: #dc3545;")
                self.validate_btn.setText("❌ Invalid")
                self.config_validated.emit(False)

                error_msg = "Configuration Errors:\n" + "\n".join(
                    f"• {error}" for error in errors
                )
                if warnings:
                    error_msg += "\n\nWarnings:\n" + "\n".join(
                        f"• {warning}" for warning in warnings
                    )

                QMessageBox.warning(self, "Configuration Issues", error_msg)

            elif warnings:
                self.validate_btn.setStyleSheet("background-color: #ffc107;")
                self.validate_btn.setText("⚠️ Valid")
                self.config_validated.emit(True)

                warning_msg = "Configuration Warnings:\n" + "\n".join(
                    f"• {warning}" for warning in warnings
                )
                QMessageBox.information(self, "Configuration Warnings", warning_msg)

            else:
                self.validate_btn.setStyleSheet("background-color: #28a745;")
                self.validate_btn.setText("✅ Valid")
                self.config_validated.emit(True)

                QMessageBox.information(
                    self, "Validation Success", "Configuration is valid!"
                )

            self.logger.info(
                f"Configuration validation completed - Errors: {len(errors)}, Warnings: {len(warnings)}"
            )

        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            self.validate_btn.setStyleSheet("background-color: #dc3545;")
            self.validate_btn.setText("❌ Error")
            self.config_validated.emit(False)

    @pyqtSlot()
    def preview_scraping(self):
        """Preview scraping with current configuration."""
        config = self.get_configuration()
        if not config:
            QMessageBox.warning(
                self,
                "Configuration Error",
                "Please configure scraping parameters before previewing.",
            )
            return

        # Emit signal for external handling
        self.preview_requested.emit(config)

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration as dictionary.

        Returns:
            Dictionary containing all configuration parameters
        """
        try:
            # Custom headers parsing
            custom_headers = {}
            headers_text = self.custom_headers_text.toPlainText().strip()
            if headers_text:
                try:
                    custom_headers = json.loads(headers_text)
                except json.JSONDecodeError:
                    self.logger.warning("Invalid JSON in custom headers, ignoring")

            # Custom fields parsing
            custom_fields = []
            for row in range(self.custom_fields_table.rowCount()):
                field_name = self.custom_fields_table.item(row, 0)
                field_selector = self.custom_fields_table.item(row, 1)
                field_type_widget = self.custom_fields_table.cellWidget(row, 2)

                if field_name and field_selector and field_type_widget:
                    custom_fields.append(
                        {
                            "name": field_name.text(),
                            "selector": field_selector.text(),
                            "type": field_type_widget.currentText(),  # type: ignore
                        }
                    )

            # Retry HTTP codes parsing
            retry_codes = []
            codes_text = self.retry_codes_edit.text().strip()
            if codes_text:
                try:
                    retry_codes = [int(code.strip()) for code in codes_text.split(",")]
                except ValueError:
                    self.logger.warning("Invalid retry codes format, using defaults")
                    retry_codes = [500, 502, 503, 504, 408, 429]

            config = {
                # Target configuration
                "anime_name": self.anime_combo.currentText(),
                "base_url": self.base_url_edit.text().strip(),
                "character_list_url": self.character_list_url_edit.text().strip(),
                "character_pattern": self.character_pattern_edit.text().strip(),
                "image_pattern": self.image_pattern_edit.text().strip(),
                # Limits
                "max_characters": self.max_characters_spin.value(),
                "max_pages_per_character": self.max_pages_spin.value(),
                "max_images_per_character": self.max_images_spin.value(),
                # Selectors
                "name_selector": self.name_selector_edit.text().strip(),
                "description_selector": self.description_selector_edit.text().strip(),
                "infobox_selector": self.infobox_selector_edit.text().strip(),
                "image_selector": self.image_selector_edit.text().strip(),
                "categories_selector": self.categories_selector_edit.text().strip(),
                # Extraction options
                "extract_infobox": self.extract_infobox_check.isChecked(),
                "extract_images": self.extract_images_check.isChecked(),
                "extract_categories": self.extract_categories_check.isChecked(),
                "extract_relationships": self.extract_relationships_check.isChecked(),
                "extract_abilities": self.extract_abilities_check.isChecked(),
                "extract_appearances": self.extract_appearances_check.isChecked(),
                # Custom fields
                "custom_fields": custom_fields,
                # Performance settings
                "download_delay": self.download_delay_spin.value(),
                "randomize_delay": self.random_delay_check.isChecked(),
                "concurrent_requests": self.concurrent_requests_spin.value(),
                "auto_throttle": self.auto_throttle_check.isChecked(),
                # Retry settings
                "retry_times": self.retry_times_spin.value(),
                "retry_delay": self.retry_delay_spin.value(),
                "retry_http_codes": retry_codes,
                # Memory and cache
                "memory_limit_mb": self.memory_limit_spin.value(),
                "cache_enabled": self.cache_enabled_check.isChecked(),
                "cache_expiration": self.cache_expiration_spin.value(),
                # Storage settings
                "output_directory": self.output_dir_edit.text().strip(),
                "store_images_locally": self.image_storage_check.isChecked(),
                "image_format": self.image_format_combo.currentText(),
                "image_quality": self.image_quality_spin.value(),
                # Database settings
                "mongo_uri": self.mongo_uri_edit.text().strip(),
                "database_name": self.db_name_edit.text().strip(),
                "collection_name": self.collection_name_edit.text().strip(),
                # Export options
                "export_json": self.export_json_check.isChecked(),
                "export_csv": self.export_csv_check.isChecked(),
                "export_excel": self.export_excel_check.isChecked(),
                "export_pdf": self.export_pdf_check.isChecked(),
                # Advanced settings
                "user_agent": self.user_agent_combo.currentText(),
                "custom_headers": custom_headers,
                "proxy_enabled": self.proxy_enabled_check.isChecked(),
                "proxy_url": self.proxy_url_edit.text().strip(),
                "javascript_enabled": self.js_enabled_check.isChecked(),
                "page_load_timeout": self.page_timeout_spin.value(),
                # Logging settings
                "log_level": self.log_level_combo.currentText(),
                "stats_enabled": self.stats_enabled_check.isChecked(),
                "debug_mode": self.debug_mode_check.isChecked(),
            }

            # Cache current configuration
            self.current_config = config.copy()

            # Emit configuration change signal
            self.config_changed.emit(config)

            return config

        except Exception as e:
            self.logger.error(f"Failed to get configuration: {e}")
            return {}

    def apply_configuration(self, config: Dict[str, Any]):
        """
        Apply configuration from dictionary.

        Args:
            config: Configuration dictionary to apply
        """
        try:
            # Target configuration
            self.anime_combo.setCurrentText(config.get("anime_name", ""))
            self.base_url_edit.setText(config.get("base_url", ""))
            self.character_list_url_edit.setText(config.get("character_list_url", ""))
            self.character_pattern_edit.setText(config.get("character_pattern", ""))
            self.image_pattern_edit.setText(config.get("image_pattern", ""))

            # Limits
            self.max_characters_spin.setValue(config.get("max_characters", 100))
            self.max_pages_spin.setValue(config.get("max_pages_per_character", 5))
            self.max_images_spin.setValue(config.get("max_images_per_character", 10))

            # Selectors
            self.name_selector_edit.setText(config.get("name_selector", ""))
            self.description_selector_edit.setText(
                config.get("description_selector", "")
            )
            self.infobox_selector_edit.setText(config.get("infobox_selector", ""))
            self.image_selector_edit.setText(config.get("image_selector", ""))
            self.categories_selector_edit.setText(config.get("categories_selector", ""))

            # Extraction options
            self.extract_infobox_check.setChecked(config.get("extract_infobox", True))
            self.extract_images_check.setChecked(config.get("extract_images", True))
            self.extract_categories_check.setChecked(
                config.get("extract_categories", True)
            )
            self.extract_relationships_check.setChecked(
                config.get("extract_relationships", False)
            )
            self.extract_abilities_check.setChecked(
                config.get("extract_abilities", False)
            )
            self.extract_appearances_check.setChecked(
                config.get("extract_appearances", False)
            )

            # Performance settings
            self.download_delay_spin.setValue(config.get("download_delay", 1.0))
            self.random_delay_check.setChecked(config.get("randomize_delay", True))
            self.concurrent_requests_spin.setValue(config.get("concurrent_requests", 8))
            self.auto_throttle_check.setChecked(config.get("auto_throttle", True))

            # Retry settings
            self.retry_times_spin.setValue(config.get("retry_times", 3))
            self.retry_delay_spin.setValue(config.get("retry_delay", 5.0))
            retry_codes = config.get("retry_http_codes", [500, 502, 503, 504, 408, 429])
            self.retry_codes_edit.setText(",".join(map(str, retry_codes)))

            # Memory and cache
            self.memory_limit_spin.setValue(config.get("memory_limit_mb", 2048))
            self.cache_enabled_check.setChecked(config.get("cache_enabled", False))
            self.cache_expiration_spin.setValue(config.get("cache_expiration", 3600))

            # Storage settings
            self.output_dir_edit.setText(config.get("output_directory", "./storage"))
            self.image_storage_check.setChecked(
                config.get("store_images_locally", True)
            )
            self.image_format_combo.setCurrentText(config.get("image_format", "JPEG"))
            self.image_quality_spin.setValue(config.get("image_quality", 85))

            # Database settings
            self.mongo_uri_edit.setText(
                config.get("mongo_uri", "mongodb://localhost:27017/")
            )
            self.db_name_edit.setText(config.get("database_name", "fandom_scraper"))
            self.collection_name_edit.setText(
                config.get("collection_name", "characters")
            )

            # Export options
            self.export_json_check.setChecked(config.get("export_json", True))
            self.export_csv_check.setChecked(config.get("export_csv", False))
            self.export_excel_check.setChecked(config.get("export_excel", False))
            self.export_pdf_check.setChecked(config.get("export_pdf", False))

            # Advanced settings
            self.user_agent_combo.setCurrentText(config.get("user_agent", ""))

            # Custom headers
            custom_headers = config.get("custom_headers", {})
            if custom_headers:
                headers_json = json.dumps(custom_headers, indent=2)
                self.custom_headers_text.setPlainText(headers_json)

            self.proxy_enabled_check.setChecked(config.get("proxy_enabled", False))
            self.proxy_url_edit.setText(config.get("proxy_url", ""))
            self.js_enabled_check.setChecked(config.get("javascript_enabled", False))
            self.page_timeout_spin.setValue(config.get("page_load_timeout", 30))

            # Logging settings
            self.log_level_combo.setCurrentText(config.get("log_level", "INFO"))
            self.stats_enabled_check.setChecked(config.get("stats_enabled", True))
            self.debug_mode_check.setChecked(config.get("debug_mode", False))

            # Custom fields
            custom_fields = config.get("custom_fields", [])
            self.custom_fields_table.setRowCount(0)
            for field in custom_fields:
                self.add_custom_field()
                row = self.custom_fields_table.rowCount() - 1
                self.custom_fields_table.setItem(
                    row, 0, QTableWidgetItem(field.get("name", ""))
                )
                self.custom_fields_table.setItem(
                    row, 1, QTableWidgetItem(field.get("selector", ""))
                )
                type_combo = self.custom_fields_table.cellWidget(row, 2)
                if type_combo:
                    type_combo.setCurrentText(field.get("type", "Text"))  # type: ignore

            self.logger.info("Configuration applied successfully")

        except Exception as e:
            self.logger.error(f"Failed to apply configuration: {e}")
            raise

    def is_configuration_valid(self) -> bool:
        """
        Check if current configuration is valid.

        Returns:
            True if configuration is valid, False otherwise
        """
        config = self.get_configuration()

        # Check required fields
        required_fields = ["base_url", "character_list_url", "name_selector"]
        for field in required_fields:
            if not config.get(field):
                return False

        # Check URL format
        for url_field in ["base_url", "character_list_url"]:
            url = config.get(url_field, "")
            if url and not url.startswith(("http://", "https://")):
                return False

        return True

    # External callback methods for status updates
    def update_connection_status(self, success: bool, message: str = ""):
        """
        Update connection test status.

        Args:
            success: Whether connection test succeeded
            message: Status message
        """
        if success:
            self.connection_status.setText(message or "Connected successfully")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText(message or "Connection failed")
            self.connection_status.setStyleSheet("color: red;")

        self.test_connection_btn.setEnabled(True)

    def update_database_status(self, success: bool, message: str = ""):
        """
        Update database connection status.

        Args:
            success: Whether database connection succeeded
            message: Status message
        """
        if success:
            self.db_status_label.setText(message or "Connected successfully")
            self.db_status_label.setStyleSheet("color: green;")
        else:
            self.db_status_label.setText(message or "Connection failed")
            self.db_status_label.setStyleSheet("color: red;")

        self.test_db_btn.setEnabled(True)

    def on_config_changed(self):
        """Handle configuration changes."""
        # Restart validation timer
        self.validation_timer.stop()
        self.validation_timer.start(1000)  # Validate after 1 second of inactivity

    @pyqtSlot(str)
    def on_anime_changed(self, anime_name: str):
        """
        Handle anime selection change.

        Args:
            anime_name: Selected anime name
        """
        if anime_name in self.anime_presets:
            preset = self.anime_presets[anime_name]

            # Update URL fields
            self.base_url_edit.setText(preset["base_url"])
            self.character_list_url_edit.setText(preset["character_list_url"])

            # Update selectors
            selectors = preset["selectors"]
            self.name_selector_edit.setText(selectors.get("name", ""))
            self.description_selector_edit.setText(selectors.get("description", ""))
            self.infobox_selector_edit.setText(selectors.get("infobox", ""))
            self.image_selector_edit.setText(selectors.get("images", ""))
            self.categories_selector_edit.setText(selectors.get("categories", ""))

            self.logger.info(f"Applied preset for {anime_name}")

    @pyqtSlot()
    def test_connection(self):
        """Test connection to target website."""
        url = self.base_url_edit.text().strip()
        if not url:
            self.connection_status.setText("No URL specified")
            self.connection_status.setStyleSheet("color: red;")
            return

        self.connection_status.setText("Testing...")
        self.connection_status.setStyleSheet("color: orange;")
        self.test_connection_btn.setEnabled(False)

        # Emit signal for external handling
        self.test_connection_requested.emit(url)

    @pyqtSlot()
    def test_database_connection(self):
        """Test database connection."""
        uri = self.mongo_uri_edit.text().strip()
        db_name = self.db_name_edit.text().strip()

        if not uri or not db_name:
            self.db_status_label.setText("Invalid parameters")
            self.db_status_label.setStyleSheet("color: red;")
            return

        self.db_status_label.setText("Testing...")
        self.db_status_label.setStyleSheet("color: orange;")
        self.test_db_btn.setEnabled(False)

        # TODO: Implement database connection test
        # For now, simulate a successful connection
        QTimer.singleShot(2000, self._simulate_db_test_success)

    def _simulate_db_test_success(self):
        """Simulate successful database test."""
        self.db_status_label.setText("Connected successfully")
        self.db_status_label.setStyleSheet("color: green;")
        self.test_db_btn.setEnabled(True)

    @pyqtSlot()
    def add_custom_field(self):
        """Add a new custom field row."""
        row_count = self.custom_fields_table.rowCount()
        self.custom_fields_table.insertRow(row_count)

        # Add default items
        self.custom_fields_table.setItem(row_count, 0, QTableWidgetItem(""))
        self.custom_fields_table.setItem(row_count, 1, QTableWidgetItem(""))

        # Add data type combo
        data_type_combo = QComboBox()
        data_type_combo.addItems(["Text", "Number", "Boolean", "List", "URL"])
        self.custom_fields_table.setCellWidget(row_count, 2, data_type_combo)

    @pyqtSlot()
    def remove_custom_field(self):
        """Remove selected custom field row."""
        current_row = self.custom_fields_table.currentRow()
        if current_row >= 0:
            self.custom_fields_table.removeRow(current_row)
