# gui/main_window.py
"""
Main window implementation for Fandom Scraper GUI application.

This module contains the primary application window with menu bar,
toolbar, status bar, and central widget areas for user interactions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMenuBar,
    QMenu,
    QAction,
    QToolBar,
    QStatusBar,
    QSplitter,
    QTabWidget,
    QFrame,
    QLabel,
    QPushButton,
    QProgressBar,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QDialog,
)
from PyQt5.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot, Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QAction as QGuiAction

# Import custom widgets and controllers
from gui.widgets.progress_dialog import ProgressDialog
from gui.widgets.scraper_config_widget import ScraperConfigWidget
from gui.widgets.data_viewer_widget import DataViewerWidget
from gui.controllers.scraper_controller import ScraperController
from utils.logger import get_logger


class MainWindow(QMainWindow):
    """
    Main application window for Fandom Scraper.

    This class manages the primary user interface including:
    - Menu bar with file operations and settings
    - Toolbar with quick access buttons
    - Status bar for application feedback
    - Central widget area with tabs for different functions
    - Progress tracking and error handling
    """

    # Custom signals for communication between components
    scraping_started = pyqtSignal(str)  # Emitted when scraping begins
    scraping_finished = pyqtSignal(dict)  # Emitted when scraping completes
    scraping_error = pyqtSignal(str)  # Emitted when errors occur
    status_updated = pyqtSignal(str)  # Emitted for status bar updates

    def __init__(self, parent=None):
        """
        Initialize the main window.

        Args:
            parent: Parent widget (usually None for main window)
        """
        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(self.__class__.__name__)

        # Application state
        self.is_scraping = False
        self.current_project = None
        self.scraped_data = {}

        # Initialize controllers
        self.scraper_controller = ScraperController()

        # Set up the UI
        self.setup_ui()
        self.setup_connections()
        self.setup_style()

        # Initialize status
        self.update_status("Ready to scrape anime data")

        self.logger.info("Main window initialized successfully")

    def setup_ui(self):
        """
        Set up the user interface components.

        Creates and configures all UI elements including menus,
        toolbars, and the central widget layout.
        """
        # Set window properties
        self.setWindowTitle("Fandom Scraper - Anime Data Collection Tool")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Center window on screen
        self.center_window()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Set up main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Create main content area with splitter
        self.create_main_content(main_layout)

        # Create status bar
        self.create_status_bar()

    def center_window(self):
        """Center the window on the screen."""
        screen = QApplication.desktop().screenGeometry()
        window = self.geometry()
        self.move(
            (screen.width() - window.width()) // 2,
            (screen.height() - window.height()) // 2,
        )

    def create_menu_bar(self):
        """Create and configure the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # New project action
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new scraping project")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        # Open project action
        open_action = QAction("Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        # Save project action
        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save current project")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Export data action
        export_action = QAction("Export Data", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export scraped data to various formats")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        # Preferences action
        prefs_action = QAction("Preferences", self)
        prefs_action.setStatusTip("Open application preferences")
        prefs_action.triggered.connect(self.open_preferences)
        edit_menu.addAction(prefs_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        # Database viewer action
        db_action = QAction("Database Viewer", self)
        db_action.setStatusTip("View and manage scraped data")
        db_action.triggered.connect(self.open_database_viewer)
        tools_menu.addAction(db_action)

        # Log viewer action
        log_action = QAction("Log Viewer", self)
        log_action.setStatusTip("View application logs")
        log_action.triggered.connect(self.open_log_viewer)
        tools_menu.addAction(log_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        # User guide action
        guide_action = QAction("User Guide", self)
        guide_action.setStatusTip("Open user documentation")
        guide_action.triggered.connect(self.open_user_guide)
        help_menu.addAction(guide_action)

        # About action
        about_action = QAction("About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Create and configure the toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(24, 24))

        # Start scraping action
        self.start_action = QAction("Start Scraping", self)
        self.start_action.setStatusTip("Begin scraping anime data")
        self.start_action.triggered.connect(self.start_scraping)
        toolbar.addAction(self.start_action)

        # Stop scraping action
        self.stop_action = QAction("Stop Scraping", self)
        self.stop_action.setStatusTip("Stop current scraping operation")
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self.stop_scraping)
        toolbar.addAction(self.stop_action)

        toolbar.addSeparator()

        # Clear data action
        clear_action = QAction("Clear Data", self)
        clear_action.setStatusTip("Clear all scraped data")
        clear_action.triggered.connect(self.clear_data)
        toolbar.addAction(clear_action)

        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh data view")
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

    def create_main_content(self, main_layout):
        """
        Create the main content area with tabs and widgets.

        Args:
            main_layout: Main layout to add content to
        """
        # Create horizontal splitter for main content
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # Left panel - Configuration and controls
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel - Data viewer and results
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter proportions (30% left, 70% right)
        main_splitter.setSizes([400, 900])

    def create_left_panel(self) -> QWidget:
        """
        Create the left control panel.

        Returns:
            Widget containing scraper configuration controls
        """
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Scraper configuration widget
        config_group = QGroupBox("Scraper Configuration")
        config_layout = QVBoxLayout(config_group)

        self.config_widget = ScraperConfigWidget()
        config_layout.addWidget(self.config_widget)

        left_layout.addWidget(config_group)

        # Progress and status widget
        progress_group = QGroupBox("Progress Information")
        progress_layout = QVBoxLayout(progress_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        progress_layout.addWidget(self.status_text)

        left_layout.addWidget(progress_group)

        # Add stretch to push content to top
        left_layout.addStretch()

        return left_widget

    def create_right_panel(self) -> QWidget:
        """
        Create the right data panel.

        Returns:
            Widget containing data viewer and results
        """
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget for different data views
        self.tab_widget = QTabWidget()

        # Data viewer tab
        self.data_viewer = DataViewerWidget()
        self.tab_widget.addTab(self.data_viewer, "Scraped Data")

        # Statistics tab
        stats_widget = self.create_statistics_widget()
        self.tab_widget.addTab(stats_widget, "Statistics")

        # Images tab
        images_widget = self.create_images_widget()
        self.tab_widget.addTab(images_widget, "Images")

        right_layout.addWidget(self.tab_widget)

        return right_widget

    def create_statistics_widget(self) -> QWidget:
        """
        Create statistics display widget.

        Returns:
            Widget showing scraping statistics
        """
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)

        # Statistics summary
        summary_group = QGroupBox("Summary Statistics")
        summary_layout = QVBoxLayout(summary_group)

        self.stats_labels = {
            "total_characters": QLabel("Total Characters: 0"),
            "total_animes": QLabel("Total Animes: 0"),
            "total_images": QLabel("Total Images: 0"),
            "scraping_time": QLabel("Total Scraping Time: 00:00:00"),
            "success_rate": QLabel("Success Rate: 0%"),
        }

        for label in self.stats_labels.values():
            label.setFont(QFont("Arial", 10))
            summary_layout.addWidget(label)

        stats_layout.addWidget(summary_group)
        stats_layout.addStretch()

        return stats_widget

    def create_images_widget(self) -> QWidget:
        """
        Create images display widget.

        Returns:
            Widget for viewing downloaded images
        """
        images_widget = QWidget()
        images_layout = QVBoxLayout(images_widget)

        # TODO: Implement image gallery widget
        placeholder_label = QLabel("Image gallery will be implemented here")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("color: gray; font-style: italic;")

        images_layout.addWidget(placeholder_label)

        return images_widget

    def create_status_bar(self):
        """Create and configure the status bar."""
        status_bar = self.statusBar()

        # Main status label
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)

        # Progress indicator for status bar
        self.status_progress = QProgressBar()
        self.status_progress.setMaximumWidth(200)
        self.status_progress.setVisible(False)
        status_bar.addPermanentWidget(self.status_progress)

        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setStyleSheet("color: red;")
        status_bar.addPermanentWidget(self.connection_label)

    def setup_connections(self):
        """Set up signal-slot connections between components."""
        # Connect scraper controller signals
        self.scraper_controller.progress_updated.connect(self.update_progress)
        self.scraper_controller.status_updated.connect(self.update_status)
        self.scraper_controller.error_occurred.connect(self.handle_error)
        self.scraper_controller.scraping_finished.connect(self.on_scraping_finished)

        # Connect config widget signals
        self.config_widget.config_changed.connect(self.on_config_changed)

        # Connect internal signals
        self.scraping_started.connect(self.on_scraping_started)
        self.scraping_finished.connect(self.on_scraping_finished)
        self.status_updated.connect(self.update_status_bar)

    def setup_style(self):
        """Set up application styling and themes."""
        # Set application stylesheet
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 5px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }

        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            font-size: 14px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QPushButton:pressed {
            background-color: #3d8b40;
        }

        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }

        QTabWidget::pane {
            border: 1px solid #cccccc;
            border-radius: 4px;
        }

        QTabBar::tab {
            background-color: #e1e1e1;
            border: 1px solid #cccccc;
            padding: 8px 16px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom-color: #ffffff;
        }

        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 4px;
        }
        """
        self.setStyleSheet(style)

    # Slot implementations
    @pyqtSlot(str)
    def update_status(self, message: str):
        """Update application status message."""
        self.status_updated.emit(message)
        self.logger.info(f"Status updated: {message}")

    @pyqtSlot(str)
    def update_status_bar(self, message: str):
        """Update status bar message."""
        self.status_label.setText(message)

    @pyqtSlot(str, int)
    def update_progress(self, message: str, progress: int):
        """
        Update progress display.

        Args:
            message: Progress message
            progress: Progress percentage (0-100)
        """
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
            self.status_progress.setVisible(True)

        self.progress_bar.setValue(progress)
        self.status_progress.setValue(progress)

        # Update status text
        self.status_text.append(f"[{progress}%] {message}")
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    @pyqtSlot(str)
    def handle_error(self, error_message: str):
        """
        Handle error messages from scraper.

        Args:
            error_message: Error description
        """
        self.logger.error(f"Scraping error: {error_message}")

        # Show error in status text
        self.status_text.append(f"ERROR: {error_message}")

        # Show error dialog for critical errors
        if "critical" in error_message.lower():
            QMessageBox.critical(self, "Critical Error", error_message)

    # Action handlers
    def start_scraping(self):
        """Start the scraping process."""
        try:
            # Get configuration from config widget
            config = self.config_widget.get_configuration()

            if not config:
                QMessageBox.warning(
                    self,
                    "Configuration Error",
                    "Please configure scraping parameters before starting.",
                )
                return

            # Start scraping
            self.scraper_controller.start_scraping(config)
            self.scraping_started.emit(config.get("anime_name", "Unknown"))

        except Exception as e:
            self.logger.error(f"Failed to start scraping: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start scraping: {e}")

    def stop_scraping(self):
        """Stop the current scraping process."""
        try:
            self.scraper_controller.stop_scraping()
            self.on_scraping_stopped()
        except Exception as e:
            self.logger.error(f"Failed to stop scraping: {e}")

    @pyqtSlot(str)
    def on_scraping_started(self, anime_name: str):
        """Handle scraping started event."""
        self.is_scraping = True
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.connection_label.setText("Scraping...")
        self.connection_label.setStyleSheet("color: orange;")
        self.update_status(f"Started scraping {anime_name}")

    @pyqtSlot(dict)
    def on_scraping_finished(self, results: Dict[str, Any]):
        """Handle scraping finished event."""
        self.is_scraping = False
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.connection_label.setText("Completed")
        self.connection_label.setStyleSheet("color: green;")

        # Hide progress indicators
        self.progress_bar.setVisible(False)
        self.status_progress.setVisible(False)

        # Update data viewer
        self.data_viewer.update_data(results)  # type: ignore

        # Update statistics
        self.update_statistics(results)

        self.update_status("Scraping completed successfully")

    def on_scraping_stopped(self):
        """Handle scraping stopped event."""
        self.is_scraping = False
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.connection_label.setText("Stopped")
        self.connection_label.setStyleSheet("color: red;")

        # Hide progress indicators
        self.progress_bar.setVisible(False)
        self.status_progress.setVisible(False)

        self.update_status("Scraping stopped by user")

    def on_config_changed(self, config: Dict[str, Any]):
        """Handle configuration changes."""
        self.logger.info("Configuration updated")
        # TODO: Validate configuration and update UI accordingly

    def update_statistics(self, results: Dict[str, Any]):
        """
        Update statistics display.

        Args:
            results: Scraping results data
        """
        # Extract statistics from results
        character_count = len(results.get("characters", []))
        anime_count = len(
            set(char.get("anime") for char in results.get("characters", []))
        )
        image_count = sum(
            len(char.get("images", [])) for char in results.get("characters", [])
        )

        # Update labels
        self.stats_labels["total_characters"].setText(
            f"Total Characters: {character_count}"
        )
        self.stats_labels["total_animes"].setText(f"Total Animes: {anime_count}")
        self.stats_labels["total_images"].setText(f"Total Images: {image_count}")

        # TODO: Calculate and display scraping time and success rate

    # Menu action handlers
    def new_project(self):
        """Create a new project."""
        # TODO: Implement new project creation
        self.logger.info("New project requested")

    def open_project(self):
        """Open an existing project."""
        # TODO: Implement project opening
        self.logger.info("Open project requested")

    def save_project(self):
        """Save current project."""
        # TODO: Implement project saving
        self.logger.info("Save project requested")

    def export_data(self):
        """Export scraped data."""
        # TODO: Implement data export functionality
        self.logger.info("Data export requested")

    def open_preferences(self):
        """Open preferences dialog."""
        # TODO: Implement preferences dialog
        self.logger.info("Preferences requested")

    def open_database_viewer(self):
        """Open database viewer."""
        # TODO: Implement database viewer
        self.logger.info("Database viewer requested")

    def open_log_viewer(self):
        """Open log viewer."""
        # TODO: Implement log viewer
        self.logger.info("Log viewer requested")

    def open_user_guide(self):
        """Open user guide."""
        # TODO: Implement user guide
        self.logger.info("User guide requested")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Fandom Scraper",
            "Fandom Scraper v1.0\n\n"
            "A comprehensive tool for collecting and managing anime data "
            "from Fandom wikis with an intuitive desktop interface.\n\n"
            "Built with Python, PyQt5, and Scrapy.",
        )

    def clear_data(self):
        """Clear all scraped data."""
        reply = QMessageBox.question(
            self,
            "Clear Data",
            "Are you sure you want to clear all scraped data?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.data_viewer.clear_data()
            self.update_status("Data cleared")

    def refresh_data(self):
        """Refresh data display."""
        self.data_viewer.refresh_data()
        self.update_status("Data refreshed")

    def closeEvent(self, event):
        """Handle application close event."""
        if self.is_scraping:
            reply = QMessageBox.question(
                self,
                "Close Application",
                "Scraping is in progress. Do you want to stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.stop_scraping()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Fandom Scraper")
    app.setApplicationVersion("1.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
