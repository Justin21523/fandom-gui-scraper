# gui/dialogs/preferences_dialog.py
"""
Preferences dialog for application settings and configurations.

This module provides a comprehensive settings interface allowing users to
customize application behavior, appearance, scraping parameters, and
data management preferences.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QSlider,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QButtonGroup,
    QRadioButton,
    QColorDialog,
    QFontDialog,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

from utils.logger import get_logger
from utils.config_manager import ConfigManager


@dataclass
class ApplicationPreferences:
    """Data class for application preferences."""

    # General Settings
    language: str = "en"
    theme: str = "light"
    auto_save: bool = True
    auto_save_interval: int = 5  # minutes

    # GUI Settings
    window_size: tuple = (1200, 800)
    window_position: tuple = (100, 100)
    font_family: str = "Arial"
    font_size: int = 10
    show_tooltips: bool = True

    # Scraping Settings
    max_concurrent_requests: int = 5
    request_delay: float = 1.0
    timeout: int = 30
    retry_attempts: int = 3
    respect_robots_txt: bool = True
    user_agent: str = "FandomScraper/1.0"

    # Database Settings
    db_host: str = "localhost"
    db_port: int = 27017
    db_name: str = "fandom_scraper"
    auto_backup: bool = True
    backup_interval: int = 24  # hours

    # Data Processing
    enable_data_validation: bool = True
    enable_deduplication: bool = True
    image_download: bool = True
    max_image_size: int = 5  # MB
    image_quality: int = 85  # JPEG quality

    # Export Settings
    default_export_format: str = "JSON"
    export_directory: str = str(Path.home() / "Downloads")
    include_metadata: bool = True


class PreferencesDialog(QDialog):
    """
    Comprehensive preferences dialog for application settings.

    Provides tabbed interface for different categories of settings
    with immediate preview and validation of configuration changes.
    """

    # Custom signals
    preferences_changed = pyqtSignal(dict)
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize preferences dialog."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)
        self.config_manager = ConfigManager()

        # Load current preferences
        self.preferences = self._load_preferences()
        self.original_preferences = ApplicationPreferences(**asdict(self.preferences))

        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.load_current_settings()

        # Apply initial theme
        self._apply_dialog_theme()

        self.logger.info("Preferences dialog initialized")

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(700, 600)
        self.setMinimumSize(600, 500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_general_tab()
        self._create_appearance_tab()
        self._create_scraping_tab()
        self._create_database_tab()
        self._create_data_processing_tab()
        self._create_export_tab()

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        main_layout.addWidget(self.button_box)

    def _create_general_tab(self):
        """Create general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Language Settings
        lang_group = QGroupBox("Language & Localization")
        lang_layout = QFormLayout(lang_group)

        self.language_combo = QComboBox()
        self.language_combo.addItems(
            [("English", "en"), ("中文", "zh"), ("日本語", "ja")]
        )
        lang_layout.addRow("Language:", self.language_combo)

        layout.addWidget(lang_group)

        # Auto-save Settings
        autosave_group = QGroupBox("Auto-save Configuration")
        autosave_layout = QFormLayout(autosave_group)

        self.auto_save_checkbox = QCheckBox("Enable auto-save")
        autosave_layout.addRow(self.auto_save_checkbox)

        self.auto_save_interval_spinbox = QSpinBox()
        self.auto_save_interval_spinbox.setRange(1, 60)
        self.auto_save_interval_spinbox.setSuffix(" minutes")
        autosave_layout.addRow("Auto-save interval:", self.auto_save_interval_spinbox)

        layout.addWidget(autosave_group)

        # Tooltip Settings
        tooltip_group = QGroupBox("Interface Options")
        tooltip_layout = QFormLayout(tooltip_group)

        self.show_tooltips_checkbox = QCheckBox("Show tooltips")
        tooltip_layout.addRow(self.show_tooltips_checkbox)

        layout.addWidget(tooltip_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "General")

    def _create_appearance_tab(self):
        """Create appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Theme Settings
        theme_group = QGroupBox("Theme & Colors")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        theme_layout.addRow("Theme:", self.theme_combo)

        # Preview button
        self.preview_theme_btn = QPushButton("Preview Theme")
        theme_layout.addRow(self.preview_theme_btn)

        layout.addWidget(theme_group)

        # Font Settings
        font_group = QGroupBox("Font Configuration")
        font_layout = QFormLayout(font_group)

        self.font_family_combo = QComboBox()
        self.font_family_combo.setEditable(True)
        font_families = [
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Courier New",
            "Verdana",
        ]
        self.font_family_combo.addItems(font_families)
        font_layout.addRow("Font Family:", self.font_family_combo)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        font_layout.addRow("Font Size:", self.font_size_spinbox)

        self.font_preview_btn = QPushButton("Font Dialog...")
        font_layout.addRow(self.font_preview_btn)

        layout.addWidget(font_group)

        # Window Settings
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout(window_group)

        self.remember_window_state_checkbox = QCheckBox(
            "Remember window size and position"
        )
        window_layout.addRow(self.remember_window_state_checkbox)

        layout.addWidget(window_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Appearance")

    def _create_scraping_tab(self):
        """Create scraping settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Performance Settings
        performance_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(performance_group)

        self.max_requests_spinbox = QSpinBox()
        self.max_requests_spinbox.setRange(1, 20)
        perf_layout.addRow("Max concurrent requests:", self.max_requests_spinbox)

        self.request_delay_spinbox = QDoubleSpinBox()
        self.request_delay_spinbox.setRange(0.1, 10.0)
        self.request_delay_spinbox.setSingleStep(0.1)
        self.request_delay_spinbox.setSuffix(" seconds")
        perf_layout.addRow("Request delay:", self.request_delay_spinbox)

        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(5, 300)
        self.timeout_spinbox.setSuffix(" seconds")
        perf_layout.addRow("Request timeout:", self.timeout_spinbox)

        self.retry_attempts_spinbox = QSpinBox()
        self.retry_attempts_spinbox.setRange(0, 10)
        perf_layout.addRow("Retry attempts:", self.retry_attempts_spinbox)

        layout.addWidget(performance_group)

        # Behavior Settings
        behavior_group = QGroupBox("Scraping Behavior")
        behavior_layout = QFormLayout(behavior_group)

        self.respect_robots_checkbox = QCheckBox("Respect robots.txt")
        behavior_layout.addRow(self.respect_robots_checkbox)

        self.user_agent_edit = QLineEdit()
        behavior_layout.addRow("User Agent:", self.user_agent_edit)

        layout.addWidget(behavior_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Scraping")

    def _create_database_tab(self):
        """Create database settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Connection Settings
        connection_group = QGroupBox("Database Connection")
        conn_layout = QFormLayout(connection_group)

        self.db_host_edit = QLineEdit()
        conn_layout.addRow("Host:", self.db_host_edit)

        self.db_port_spinbox = QSpinBox()
        self.db_port_spinbox.setRange(1, 65535)
        conn_layout.addRow("Port:", self.db_port_spinbox)

        self.db_name_edit = QLineEdit()
        conn_layout.addRow("Database Name:", self.db_name_edit)

        # Test connection button
        self.test_connection_btn = QPushButton("Test Connection")
        conn_layout.addRow(self.test_connection_btn)

        layout.addWidget(connection_group)

        # Backup Settings
        backup_group = QGroupBox("Backup Configuration")
        backup_layout = QFormLayout(backup_group)

        self.auto_backup_checkbox = QCheckBox("Enable automatic backups")
        backup_layout.addRow(self.auto_backup_checkbox)

        self.backup_interval_spinbox = QSpinBox()
        self.backup_interval_spinbox.setRange(1, 168)  # 1 hour to 1 week
        self.backup_interval_spinbox.setSuffix(" hours")
        backup_layout.addRow("Backup interval:", self.backup_interval_spinbox)

        layout.addWidget(backup_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Database")

    def _create_data_processing_tab(self):
        """Create data processing settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Data Quality Settings
        quality_group = QGroupBox("Data Quality")
        quality_layout = QFormLayout(quality_group)

        self.data_validation_checkbox = QCheckBox("Enable data validation")
        quality_layout.addRow(self.data_validation_checkbox)

        self.deduplication_checkbox = QCheckBox("Enable automatic deduplication")
        quality_layout.addRow(self.deduplication_checkbox)

        layout.addWidget(quality_group)

        # Image Processing Settings
        image_group = QGroupBox("Image Processing")
        image_layout = QFormLayout(image_group)

        self.image_download_checkbox = QCheckBox("Download character images")
        image_layout.addRow(self.image_download_checkbox)

        self.max_image_size_spinbox = QSpinBox()
        self.max_image_size_spinbox.setRange(1, 50)
        self.max_image_size_spinbox.setSuffix(" MB")
        image_layout.addRow("Max image size:", self.max_image_size_spinbox)

        self.image_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_quality_slider.setRange(10, 100)
        self.image_quality_label = QLabel("85%")
        image_quality_layout = QHBoxLayout()
        image_quality_layout.addWidget(self.image_quality_slider)
        image_quality_layout.addWidget(self.image_quality_label)
        image_layout.addRow("JPEG Quality:", image_quality_layout)

        layout.addWidget(image_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Data Processing")

    def _create_export_tab(self):
        """Create export settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Export Format Settings
        format_group = QGroupBox("Default Export Settings")
        format_layout = QFormLayout(format_group)

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["JSON", "CSV", "Excel", "XML"])
        format_layout.addRow("Default format:", self.export_format_combo)

        # Export directory
        export_dir_layout = QHBoxLayout()
        self.export_dir_edit = QLineEdit()
        self.browse_export_dir_btn = QPushButton("Browse...")
        export_dir_layout.addWidget(self.export_dir_edit)
        export_dir_layout.addWidget(self.browse_export_dir_btn)
        format_layout.addRow("Export directory:", export_dir_layout)

        self.include_metadata_checkbox = QCheckBox("Include metadata in exports")
        format_layout.addRow(self.include_metadata_checkbox)

        layout.addWidget(format_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Export")

    def setup_connections(self):
        """Set up signal connections."""
        # Button box connections
        self.button_box.accepted.connect(self.accept_changes)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.apply_changes
        )
        self.button_box.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self.restore_defaults)

        # Appearance tab connections
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.preview_theme_btn.clicked.connect(self._preview_theme)
        self.font_preview_btn.clicked.connect(self._show_font_dialog)

        # Auto-save connection
        self.auto_save_checkbox.toggled.connect(
            self.auto_save_interval_spinbox.setEnabled
        )

        # Image quality slider
        self.image_quality_slider.valueChanged.connect(self._update_image_quality_label)

        # Database connections
        self.test_connection_btn.clicked.connect(self._test_database_connection)

        # Export directory browse
        self.browse_export_dir_btn.clicked.connect(self._browse_export_directory)

        # Backup checkbox
        self.auto_backup_checkbox.toggled.connect(
            self.backup_interval_spinbox.setEnabled
        )

        # Image download checkbox
        self.image_download_checkbox.toggled.connect(self._toggle_image_settings)

    def load_current_settings(self):
        """Load current settings into the dialog controls."""
        prefs = self.preferences

        # General tab
        lang_index = self.language_combo.findData(prefs.language)
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)

        self.auto_save_checkbox.setChecked(prefs.auto_save)
        self.auto_save_interval_spinbox.setValue(prefs.auto_save_interval)
        self.auto_save_interval_spinbox.setEnabled(prefs.auto_save)
        self.show_tooltips_checkbox.setChecked(prefs.show_tooltips)

        # Appearance tab
        theme_index = self.theme_combo.findText(prefs.theme.title())
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        self.font_family_combo.setCurrentText(prefs.font_family)
        self.font_size_spinbox.setValue(prefs.font_size)

        # Scraping tab
        self.max_requests_spinbox.setValue(prefs.max_concurrent_requests)
        self.request_delay_spinbox.setValue(prefs.request_delay)
        self.timeout_spinbox.setValue(prefs.timeout)
        self.retry_attempts_spinbox.setValue(prefs.retry_attempts)
        self.respect_robots_checkbox.setChecked(prefs.respect_robots_txt)
        self.user_agent_edit.setText(prefs.user_agent)

        # Database tab
        self.db_host_edit.setText(prefs.db_host)
        self.db_port_spinbox.setValue(prefs.db_port)
        self.db_name_edit.setText(prefs.db_name)
        self.auto_backup_checkbox.setChecked(prefs.auto_backup)
        self.backup_interval_spinbox.setValue(prefs.backup_interval)
        self.backup_interval_spinbox.setEnabled(prefs.auto_backup)

        # Data processing tab
        self.data_validation_checkbox.setChecked(prefs.enable_data_validation)
        self.deduplication_checkbox.setChecked(prefs.enable_deduplication)
        self.image_download_checkbox.setChecked(prefs.image_download)
        self.max_image_size_spinbox.setValue(prefs.max_image_size)
        self.image_quality_slider.setValue(prefs.image_quality)
        self._update_image_quality_label(prefs.image_quality)
        self._toggle_image_settings(prefs.image_download)

        # Export tab
        export_index = self.export_format_combo.findText(prefs.default_export_format)
        if export_index >= 0:
            self.export_format_combo.setCurrentIndex(export_index)

        self.export_dir_edit.setText(prefs.export_directory)
        self.include_metadata_checkbox.setChecked(prefs.include_metadata)

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings from the dialog controls."""
        return {
            # General
            "language": self.language_combo.currentData()
            or self.language_combo.currentText().lower()[:2],
            "auto_save": self.auto_save_checkbox.isChecked(),
            "auto_save_interval": self.auto_save_interval_spinbox.value(),
            "show_tooltips": self.show_tooltips_checkbox.isChecked(),
            # Appearance
            "theme": self.theme_combo.currentText().lower(),
            "font_family": self.font_family_combo.currentText(),
            "font_size": self.font_size_spinbox.value(),
            # Scraping
            "max_concurrent_requests": self.max_requests_spinbox.value(),
            "request_delay": self.request_delay_spinbox.value(),
            "timeout": self.timeout_spinbox.value(),
            "retry_attempts": self.retry_attempts_spinbox.value(),
            "respect_robots_txt": self.respect_robots_checkbox.isChecked(),
            "user_agent": self.user_agent_edit.text(),
            # Database
            "db_host": self.db_host_edit.text(),
            "db_port": self.db_port_spinbox.value(),
            "db_name": self.db_name_edit.text(),
            "auto_backup": self.auto_backup_checkbox.isChecked(),
            "backup_interval": self.backup_interval_spinbox.value(),
            # Data processing
            "enable_data_validation": self.data_validation_checkbox.isChecked(),
            "enable_deduplication": self.deduplication_checkbox.isChecked(),
            "image_download": self.image_download_checkbox.isChecked(),
            "max_image_size": self.max_image_size_spinbox.value(),
            "image_quality": self.image_quality_slider.value(),
            # Export
            "default_export_format": self.export_format_combo.currentText(),
            "export_directory": self.export_dir_edit.text(),
            "include_metadata": self.include_metadata_checkbox.isChecked(),
        }

    def accept_changes(self):
        """Accept and apply changes."""
        if self.apply_changes():
            self.accept()

    def apply_changes(self) -> bool:
        """Apply current settings."""
        try:
            settings = self.get_settings()

            # Validate settings
            if not self._validate_settings(settings):
                return False

            # Update preferences object
            for key, value in settings.items():
                if hasattr(self.preferences, key):
                    setattr(self.preferences, key, value)

            # Save preferences
            self._save_preferences()

            # Emit signals
            self.preferences_changed.emit(settings)

            if settings["theme"] != self.original_preferences.theme:
                self.theme_changed.emit(settings["theme"])

            self.logger.info("Preferences applied successfully")
            QMessageBox.information(
                self, "Success", "Preferences have been applied successfully."
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply preferences: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to apply preferences: {str(e)}"
            )
            return False

    def restore_defaults(self):
        """Restore default settings."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.preferences = ApplicationPreferences()
            self.load_current_settings()
            self.logger.info("Settings restored to defaults")

    def _load_preferences(self) -> ApplicationPreferences:
        """Load preferences from configuration."""
        try:
            config = self.config_manager.get_config()

            # Extract preferences from config
            prefs_dict = config.get("preferences", {})
            return ApplicationPreferences(**prefs_dict)

        except Exception as e:
            self.logger.warning(f"Failed to load preferences, using defaults: {e}")
            return ApplicationPreferences()

    def _save_preferences(self):
        """Save preferences to configuration."""
        try:
            config = self.config_manager.get_config()
            config["preferences"] = asdict(self.preferences)
            self.config_manager.save_config(config)

        except Exception as e:
            self.logger.error(f"Failed to save preferences: {e}")
            raise

    def _validate_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate settings before applying."""
        errors = []

        # Validate database connection
        if not settings["db_host"].strip():
            errors.append("Database host cannot be empty")

        if not settings["db_name"].strip():
            errors.append("Database name cannot be empty")

        # Validate export directory
        export_dir = Path(settings["export_directory"])
        if not export_dir.exists():
            try:
                export_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                errors.append(f"Cannot create export directory: {export_dir}")

        # Validate user agent
        if not settings["user_agent"].strip():
            errors.append("User agent cannot be empty")

        if errors:
            QMessageBox.warning(
                self,
                "Validation Errors",
                "Please fix the following issues:\n\n"
                + "\n".join(f"• {error}" for error in errors),
            )
            return False

        return True

    # Event handlers
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        self._apply_dialog_theme()

    def _preview_theme(self):
        """Preview selected theme."""
        current_theme = self.theme_combo.currentText().lower()
        self._apply_dialog_theme(current_theme)

    def _apply_dialog_theme(self, theme: str = None):
        """Apply theme to dialog."""
        if theme is None:
            theme = self.theme_combo.currentText().lower()

        if theme == "dark":
            dark_style = """
            QDialog { background-color: #2b2b2b; color: #ffffff; }
            QGroupBox { border: 1px solid #555555; margin-top: 1ex; padding-top: 5px; }
            QGroupBox::title { color: #ffffff; left: 10px; padding: 0 5px; }
            QTabWidget::pane { border: 1px solid #555555; }
            QTabBar::tab { background-color: #3c3c3c; color: #ffffff; padding: 8px; }
            QTabBar::tab:selected { background-color: #2b2b2b; }
            QPushButton { background-color: #0078d4; color: white; border: none; padding: 8px; }
            QPushButton:hover { background-color: #106ebe; }
            """
            self.setStyleSheet(dark_style)
        else:
            self.setStyleSheet("")  # Reset to default light theme

    def _show_font_dialog(self):
        """Show font selection dialog."""
        current_font = QFont(
            self.font_family_combo.currentText(), self.font_size_spinbox.value()
        )

        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.font_family_combo.setCurrentText(font.family())
            self.font_size_spinbox.setValue(font.pointSize())

    def _update_image_quality_label(self, value: int):
        """Update image quality label."""
        self.image_quality_label.setText(f"{value}%")

    def _test_database_connection(self):
        """Test database connection."""
        # This would be implemented with actual database connection testing
        QMessageBox.information(
            self,
            "Connection Test",
            "Database connection test functionality will be implemented in the next phase.",
        )

    def _browse_export_directory(self):
        """Browse for export directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", self.export_dir_edit.text()
        )
        if directory:
            self.export_dir_edit.setText(directory)

    def _toggle_image_settings(self, enabled: bool):
        """Toggle image processing settings based on image download checkbox."""
        self.max_image_size_spinbox.setEnabled(enabled)
        self.image_quality_slider.setEnabled(enabled)
        self.image_quality_label.setEnabled(enabled)
