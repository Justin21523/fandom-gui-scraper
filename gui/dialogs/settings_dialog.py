# gui/dialogs/settings_dialog.py
"""
Settings dialog for quick application configurations.

This module provides a streamlined settings interface for commonly
used configuration options, complementing the comprehensive preferences dialog.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QSlider,
    QFileDialog,
    QMessageBox,
    QDialogButtonBox,
    QTabWidget,
    QWidget,
    QTextEdit,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap

from utils.logger import get_logger
from utils.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """
    Quick settings dialog for essential application configurations.

    Provides a simplified interface for frequently accessed settings
    without the complexity of the full preferences dialog.
    """

    # Custom signals
    settings_applied = pyqtSignal(dict)
    connection_tested = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        """Initialize settings dialog."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)
        self.config_manager = ConfigManager()

        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.load_current_settings()

        self.logger.info("Settings dialog initialized")

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Quick Settings")
        self.setModal(True)
        self.resize(500, 400)
        self.setMinimumSize(450, 350)

        # Main layout
        layout = QVBoxLayout(self)

        # Create tab widget for organization
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_scraping_tab()
        self._create_database_tab()
        self._create_output_tab()

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        layout.addWidget(self.button_box)

    def _create_scraping_tab(self):
        """Create scraping settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Basic scraping settings
        basic_group = QGroupBox("Basic Scraping Settings")
        basic_layout = QFormLayout(basic_group)

        # Request delay
        self.request_delay_spinbox = QDoubleSpinBox()
        self.request_delay_spinbox.setRange(0.1, 10.0)
        self.request_delay_spinbox.setSingleStep(0.1)
        self.request_delay_spinbox.setSuffix(" seconds")
        self.request_delay_spinbox.setToolTip(
            "Delay between requests to avoid being blocked"
        )
        basic_layout.addRow("Request Delay:", self.request_delay_spinbox)

        # Max concurrent requests
        self.max_requests_spinbox = QSpinBox()
        self.max_requests_spinbox.setRange(1, 10)
        self.max_requests_spinbox.setToolTip("Maximum number of simultaneous requests")
        basic_layout.addRow("Max Concurrent Requests:", self.max_requests_spinbox)

        # Timeout
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(5, 120)
        self.timeout_spinbox.setSuffix(" seconds")
        self.timeout_spinbox.setToolTip("Request timeout duration")
        basic_layout.addRow("Request Timeout:", self.timeout_spinbox)

        layout.addWidget(basic_group)

        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)

        # Respect robots.txt
        self.respect_robots_checkbox = QCheckBox("Respect robots.txt")
        self.respect_robots_checkbox.setToolTip("Follow robots.txt rules (recommended)")
        advanced_layout.addRow(self.respect_robots_checkbox)

        # Download images
        self.download_images_checkbox = QCheckBox("Download character images")
        self.download_images_checkbox.setToolTip("Download and save character images")
        advanced_layout.addRow(self.download_images_checkbox)

        # User agent
        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setToolTip("Custom user agent string")
        advanced_layout.addRow("User Agent:", self.user_agent_edit)

        layout.addWidget(advanced_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Scraping")

    def _create_database_tab(self):
        """Create database settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Connection settings
        connection_group = QGroupBox("Database Connection")
        connection_layout = QFormLayout(connection_group)

        # Host
        self.db_host_edit = QLineEdit()
        self.db_host_edit.setPlaceholderText("localhost")
        connection_layout.addRow("Host:", self.db_host_edit)

        # Port
        self.db_port_spinbox = QSpinBox()
        self.db_port_spinbox.setRange(1, 65535)
        self.db_port_spinbox.setValue(27017)
        connection_layout.addRow("Port:", self.db_port_spinbox)

        # Database name
        self.db_name_edit = QLineEdit()
        self.db_name_edit.setPlaceholderText("fandom_scraper")
        connection_layout.addRow("Database Name:", self.db_name_edit)

        # Test connection button
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.setToolTip("Test database connectivity")
        connection_layout.addRow(self.test_connection_btn)

        # Connection status
        self.connection_status_label = QLabel("Not tested")
        self.connection_status_label.setStyleSheet("color: gray;")
        connection_layout.addRow("Status:", self.connection_status_label)

        layout.addWidget(connection_group)

        # Data management settings
        data_group = QGroupBox("Data Management")
        data_layout = QFormLayout(data_group)

        # Auto-save
        self.auto_save_checkbox = QCheckBox("Enable auto-save")
        self.auto_save_checkbox.setToolTip("Automatically save data during scraping")
        data_layout.addRow(self.auto_save_checkbox)

        # Data validation
        self.data_validation_checkbox = QCheckBox("Enable data validation")
        self.data_validation_checkbox.setToolTip("Validate data before saving")
        data_layout.addRow(self.data_validation_checkbox)

        # Deduplication
        self.deduplication_checkbox = QCheckBox("Enable deduplication")
        self.deduplication_checkbox.setToolTip("Remove duplicate entries automatically")
        data_layout.addRow(self.deduplication_checkbox)

        layout.addWidget(data_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Database")

    def _create_output_tab(self):
        """Create output settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Export settings
        export_group = QGroupBox("Export Settings")
        export_layout = QFormLayout(export_group)

        # Default export format
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["JSON", "CSV", "Excel", "XML"])
        export_layout.addRow("Default Format:", self.export_format_combo)

        # Export directory
        export_dir_layout = QHBoxLayout()
        self.export_dir_edit = QLineEdit()
        self.browse_export_btn = QPushButton("Browse...")
        export_dir_layout.addWidget(self.export_dir_edit)
        export_dir_layout.addWidget(self.browse_export_btn)
        export_layout.addRow("Export Directory:", export_dir_layout)

        # Include metadata
        self.include_metadata_checkbox = QCheckBox("Include metadata in exports")
        export_layout.addRow(self.include_metadata_checkbox)

        layout.addWidget(export_group)

        # Log settings
        log_group = QGroupBox("Logging Settings")
        log_layout = QFormLayout(log_group)

        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addRow("Log Level:", self.log_level_combo)

        # Log to file
        self.log_to_file_checkbox = QCheckBox("Save logs to file")
        log_layout.addRow(self.log_to_file_checkbox)

        # Max log file size
        self.max_log_size_spinbox = QSpinBox()
        self.max_log_size_spinbox.setRange(1, 100)
        self.max_log_size_spinbox.setSuffix(" MB")
        self.max_log_size_spinbox.setEnabled(False)
        log_layout.addRow("Max Log File Size:", self.max_log_size_spinbox)

        layout.addWidget(log_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Output")

    def setup_connections(self):
        """Set up signal connections."""
        # Button box
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.apply_settings
        )

        # Database tab
        self.test_connection_btn.clicked.connect(self.test_database_connection)

        # Output tab
        self.browse_export_btn.clicked.connect(self.browse_export_directory)
        self.log_to_file_checkbox.toggled.connect(self.max_log_size_spinbox.setEnabled)

        # Auto-save dependency
        self.auto_save_checkbox.toggled.connect(self._on_auto_save_toggled)

    def load_current_settings(self):
        """Load current settings into dialog controls."""
        try:
            config = self.config_manager.get_config()

            # Scraping settings
            scraping_config = config.get("scraping", {})
            self.request_delay_spinbox.setValue(
                scraping_config.get("request_delay", 1.0)
            )
            self.max_requests_spinbox.setValue(
                scraping_config.get("max_concurrent_requests", 5)
            )
            self.timeout_spinbox.setValue(scraping_config.get("timeout", 30))
            self.respect_robots_checkbox.setChecked(
                scraping_config.get("respect_robots_txt", True)
            )
            self.download_images_checkbox.setChecked(
                scraping_config.get("download_images", True)
            )
            self.user_agent_edit.setText(
                scraping_config.get("user_agent", "FandomScraper/1.0")
            )

            # Database settings
            db_config = config.get("database", {})
            self.db_host_edit.setText(db_config.get("host", "localhost"))
            self.db_port_spinbox.setValue(db_config.get("port", 27017))
            self.db_name_edit.setText(db_config.get("name", "fandom_scraper"))
            self.auto_save_checkbox.setChecked(db_config.get("auto_save", True))
            self.data_validation_checkbox.setChecked(
                db_config.get("enable_validation", True)
            )
            self.deduplication_checkbox.setChecked(
                db_config.get("enable_deduplication", True)
            )

            # Output settings
            output_config = config.get("output", {})
            export_format = output_config.get("default_export_format", "JSON")
            format_index = self.export_format_combo.findText(export_format)
            if format_index >= 0:
                self.export_format_combo.setCurrentIndex(format_index)

            self.export_dir_edit.setText(
                output_config.get("export_directory", str(Path.home() / "Downloads"))
            )
            self.include_metadata_checkbox.setChecked(
                output_config.get("include_metadata", True)
            )

            # Logging settings
            log_config = config.get("logging", {})
            log_level = log_config.get("level", "INFO")
            level_index = self.log_level_combo.findText(log_level)
            if level_index >= 0:
                self.log_level_combo.setCurrentIndex(level_index)

            self.log_to_file_checkbox.setChecked(log_config.get("log_to_file", False))
            self.max_log_size_spinbox.setValue(log_config.get("max_file_size_mb", 10))
            self.max_log_size_spinbox.setEnabled(log_config.get("log_to_file", False))

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            QMessageBox.warning(
                self, "Warning", f"Failed to load current settings: {str(e)}"
            )

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings from dialog controls."""
        return {
            "scraping": {
                "request_delay": self.request_delay_spinbox.value(),
                "max_concurrent_requests": self.max_requests_spinbox.value(),
                "timeout": self.timeout_spinbox.value(),
                "respect_robots_txt": self.respect_robots_checkbox.isChecked(),
                "download_images": self.download_images_checkbox.isChecked(),
                "user_agent": self.user_agent_edit.text().strip()
                or "FandomScraper/1.0",
            },
            "database": {
                "host": self.db_host_edit.text().strip() or "localhost",
                "port": self.db_port_spinbox.value(),
                "name": self.db_name_edit.text().strip() or "fandom_scraper",
                "auto_save": self.auto_save_checkbox.isChecked(),
                "enable_validation": self.data_validation_checkbox.isChecked(),
                "enable_deduplication": self.deduplication_checkbox.isChecked(),
            },
            "output": {
                "default_export_format": self.export_format_combo.currentText(),
                "export_directory": self.export_dir_edit.text().strip()
                or str(Path.home() / "Downloads"),
                "include_metadata": self.include_metadata_checkbox.isChecked(),
            },
            "logging": {
                "level": self.log_level_combo.currentText(),
                "log_to_file": self.log_to_file_checkbox.isChecked(),
                "max_file_size_mb": self.max_log_size_spinbox.value(),
            },
        }

    def accept_settings(self):
        """Accept and apply settings."""
        if self.apply_settings():
            self.accept()

    def apply_settings(self) -> bool:
        """Apply current settings."""
        try:
            settings = self.get_settings()

            # Validate settings
            if not self._validate_settings(settings):
                return False

            # Update configuration
            config = self.config_manager.get_config()
            config.update(settings)
            self.config_manager.save_config(config)

            # Emit signal
            self.settings_applied.emit(settings)

            self.logger.info("Settings applied successfully")
            QMessageBox.information(
                self, "Success", "Settings have been applied successfully."
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")
            return False

    def _validate_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate settings before applying."""
        errors = []

        # Validate database settings
        db_settings = settings["database"]
        if not db_settings["host"]:
            errors.append("Database host cannot be empty")

        if not db_settings["name"]:
            errors.append("Database name cannot be empty")

        # Validate export directory
        export_dir = Path(settings["output"]["export_directory"])
        if not export_dir.exists():
            try:
                export_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                errors.append(f"Cannot create export directory: {export_dir}")

        # Validate scraping settings
        scraping_settings = settings["scraping"]
        if not scraping_settings["user_agent"]:
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

    @pyqtSlot()
    def test_database_connection(self):
        """Test database connection."""
        self.test_connection_btn.setEnabled(False)
        self.test_connection_btn.setText("Testing...")
        self.connection_status_label.setText("Testing connection...")
        self.connection_status_label.setStyleSheet("color: orange;")

        # Create connection test worker
        self.connection_worker = DatabaseTestWorker(
            self.db_host_edit.text().strip() or "localhost",
            self.db_port_spinbox.value(),
            self.db_name_edit.text().strip() or "fandom_scraper",
        )
        self.connection_worker.finished.connect(self._on_connection_test_finished)
        self.connection_worker.start()

    @pyqtSlot()
    def browse_export_directory(self):
        """Browse for export directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", self.export_dir_edit.text()
        )
        if directory:
            self.export_dir_edit.setText(directory)

    def _on_auto_save_toggled(self, enabled: bool):
        """Handle auto-save checkbox toggle."""
        if enabled:
            self.data_validation_checkbox.setChecked(True)

    @pyqtSlot(bool, str)
    def _on_connection_test_finished(self, success: bool, message: str):
        """Handle connection test completion."""
        self.test_connection_btn.setEnabled(True)
        self.test_connection_btn.setText("Test Connection")

        if success:
            self.connection_status_label.setText("✓ Connected")
            self.connection_status_label.setStyleSheet("color: green;")
        else:
            self.connection_status_label.setText("✗ Failed")
            self.connection_status_label.setStyleSheet("color: red;")
            QMessageBox.warning(
                self, "Connection Failed", f"Database connection failed:\n{message}"
            )

        self.connection_tested.emit(success, message)


class DatabaseTestWorker(QThread):
    """Worker thread for testing database connection."""

    finished = pyqtSignal(bool, str)

    def __init__(self, host: str, port: int, database: str):
        super().__init__()
        self.host = host
        self.port = port
        self.database = database
        self.logger = get_logger(self.__class__.__name__)

    def run(self):
        """Test database connection in background thread."""
        try:
            # Import here to avoid circular imports
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

            # Create client with short timeout for testing
            client = MongoClient(
                host=self.host,
                port=self.port,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )

            # Test connection
            client.admin.command("ping")

            # Test database access
            db = client[self.database]
            db.list_collection_names(limit=1)

            client.close()

            self.finished.emit(True, "Connection successful")

        except ConnectionFailure as e:
            self.logger.error(f"Database connection failed: {e}")
            self.finished.emit(False, f"Connection failed: {str(e)}")
        except ServerSelectionTimeoutError as e:
            self.logger.error(f"Database server timeout: {e}")
            self.finished.emit(False, "Server timeout - check host and port")
        except Exception as e:
            self.logger.error(f"Unexpected database error: {e}")
            self.finished.emit(False, f"Unexpected error: {str(e)}")
