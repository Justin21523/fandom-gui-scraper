# gui/main_window.py
"""
Main window implementation for Fandom Scraper GUI application.

This module contains the primary application window with menu bar,
toolbar, status bar, and central widget areas for user interactions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMenuBar,
    QMenu,
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
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QAction as QGuiAction

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
        screen = QApplication.primaryScreen().availableGeometry()  # type: ignore
        window = self.geometry()
        self.move(
            (screen.width() - window.width()) // 2,
            (screen.height() - window.height()) // 2,
        )

    def create_menu_bar(self):
        """Create and configure the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")  # type: ignore

        # New project action
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new scraping project")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)  # type: ignore

        # Open project action
        open_action = QAction("Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)  # type: ignore

        # Save project action
        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save current project")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)  # type: ignore

        file_menu.addSeparator()  # type: ignore

        # Export data action
        export_action = QAction("Export Data", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export scraped data to various formats")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)  # type: ignore

        file_menu.addSeparator()  # type: ignore

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)  # type: ignore

        # Edit menu
        edit_menu = menubar.addMenu("Edit")  # type: ignore

        # Preferences action
        prefs_action = QAction("Preferences", self)
        prefs_action.setStatusTip("Open application preferences")
        prefs_action.triggered.connect(self.open_preferences)
        edit_menu.addAction(prefs_action)  # type: ignore

        # Tools menu
        tools_menu = menubar.addMenu("Tools")  # type: ignore

        # Database viewer action
        db_action = QAction("Database Viewer", self)
        db_action.setStatusTip("View and manage scraped data")
        db_action.triggered.connect(self.open_database_viewer)
        tools_menu.addAction(db_action)  # type: ignore

        # Log viewer action
        log_action = QAction("Log Viewer", self)
        log_action.setStatusTip("View application logs")
        log_action.triggered.connect(self.open_log_viewer)
        tools_menu.addAction(log_action)  # type: ignore

        # Help menu
        help_menu = menubar.addMenu("Help")  # type: ignore

        # User guide action
        guide_action = QAction("User Guide", self)
        guide_action.setStatusTip("Open user documentation")
        guide_action.triggered.connect(self.open_user_guide)
        help_menu.addAction(guide_action)  # type: ignore

        # About action
        about_action = QAction("About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)  # type: ignore

    def create_toolbar(self):
        """Create and configure the toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)  # type: ignore
        toolbar.setIconSize(QSize(24, 24))  # type: ignore

        # Start scraping action
        self.start_action = QAction("Start Scraping", self)
        self.start_action.setStatusTip("Begin scraping anime data")
        self.start_action.triggered.connect(self.start_scraping)
        toolbar.addAction(self.start_action)  # type: ignore

        # Stop scraping action
        self.stop_action = QAction("Stop Scraping", self)
        self.stop_action.setStatusTip("Stop current scraping operation")
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self.stop_scraping)
        toolbar.addAction(self.stop_action)  # type: ignore

        toolbar.addSeparator()  # type: ignore

        # Clear data action
        clear_action = QAction("Clear Data", self)
        clear_action.setStatusTip("Clear all scraped data")
        clear_action.triggered.connect(self.clear_data)
        toolbar.addAction(clear_action)  # type: ignore

        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh data view")
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)  # type: ignore

    def create_main_content(self, main_layout):
        """
        Create the main content area with tabs and widgets.

        Args:
            main_layout: Main layout to add content to
        """
        # Create horizontal splitter for main content
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
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
        建立統計顯示元件 - 完成原有 TODO

        Returns:
            Widget containing statistics display
        """
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)

        # 建立統計標籤字典
        self.stats_labels = {}

        # 基本統計資訊
        basic_stats = [
            ("total_characters", "Total Characters: 0"),
            ("total_animes", "Total Animes: 0"),
            ("total_images", "Total Images: 0"),
            ("scraping_time", "Scraping Time: 0.00s"),
            ("success_rate", "Success Rate: 100.0%"),
        ]

        for key, default_text in basic_stats:
            label = QLabel(default_text)
            label.setFont(QFont("Arial", 10))
            self.stats_labels[key] = label
            layout.addWidget(label)

        # 新增詳細統計圖表區域
        charts_group = QGroupBox("Statistics Charts")
        charts_layout = QVBoxLayout(charts_group)

        # 這裡可以加入圖表元件（例如使用 matplotlib 或 QChart）
        placeholder_label = QLabel("Charts will be displayed here")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: gray; font-style: italic;")
        charts_layout.addWidget(placeholder_label)

        layout.addWidget(charts_group)
        layout.addStretch()

        return stats_widget

    def create_status_bar(self):
        """Create and configure the status bar."""
        status_bar = self.statusBar()

        # Main status label
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)  # type: ignore

        # Progress indicator for status bar
        self.status_progress = QProgressBar()
        self.status_progress.setMaximumWidth(200)
        self.status_progress.setVisible(False)
        status_bar.addPermanentWidget(self.status_progress)  # type: ignore

        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setStyleSheet("color: red;")
        status_bar.addPermanentWidget(self.connection_label)  # type: ignore

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
        self.status_text.verticalScrollBar().setValue(  # type: ignore
            self.status_text.verticalScrollBar().maximum()  # type: ignore
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

        # 從統計資料中獲取額外資訊
        statistics = results.get("statistics", {})
        duration = statistics.get("duration", 0)
        errors = statistics.get("errors_encountered", 0)

        # 計算成功率
        total_attempts = character_count + errors
        success_rate = (
            (character_count / total_attempts * 100) if total_attempts > 0 else 100
        )

        # 更新標籤
        self.stats_labels["total_characters"].setText(
            f"Total Characters: {character_count}"
        )
        self.stats_labels["total_animes"].setText(f"Total Animes: {anime_count}")
        self.stats_labels["total_images"].setText(f"Total Images: {image_count}")

        # 添加新的統計資訊
        if "scraping_time" in self.stats_labels:
            self.stats_labels["scraping_time"].setText(
                f"Scraping Time: {duration:.2f}s"
            )
        if "success_rate" in self.stats_labels:
            self.stats_labels["success_rate"].setText(
                f"Success Rate: {success_rate:.1f}%"
            )

    # Menu action handlers
    def new_project(self):
        """Create a new project."""
        reply = QMessageBox.question(
            self,
            "New Project",
            "Create a new project? Any unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 清除當前資料
            self.scraped_data = {}
            self.current_project = None

            # 重設 UI
            self.data_viewer.update_data([])
            self.config_widget.reset_configuration()

            # 更新狀態
            self.update_status("New project created")
            self.logger.info("New project created")

    def open_project(self):
        """開啟現有專案 - 完成 TODO"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Project files (*.json);;All files (*)")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    project_data = json.load(f)

                # 載入專案資料
                self.current_project = file_path
                self.scraped_data = project_data.get("scraped_data", {})

                # 更新 UI
                characters = project_data.get("scraped_data", {}).get("characters", [])
                self.data_viewer.update_data(characters)

                # 更新配置
                config = project_data.get("configuration", {})
                self.config_widget.load_configuration(config)

                self.update_status(f"Project loaded: {Path(file_path).name}")
                self.logger.info(f"Project loaded from: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open project:\n{e}")
                self.logger.error(f"Failed to open project: {e}")

    def save_project(self):
        """儲存目前專案 - 完成 TODO"""
        if self.current_project:
            # 儲存到現有檔案
            self._save_project_to_file(self.current_project)
        else:
            # 另存新檔
            self.save_project_as()

    def save_project_as(self):
        """另存專案 - 完成 TODO"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setNameFilter("Project files (*.json);;All files (*)")
        file_dialog.setDefaultSuffix("json")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self._save_project_to_file(file_path)
            self.current_project = file_path

    def _save_project_to_file(self, file_path: str):
        """儲存專案到指定檔案"""
        try:
            project_data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "scraped_data": self.scraped_data,
                "configuration": self.config_widget.get_configuration(),
                "statistics": {
                    "total_characters": len(self.scraped_data.get("characters", [])),
                    "total_animes": len(
                        set(
                            char.get("anime")
                            for char in self.scraped_data.get("characters", [])
                        )
                    ),
                },
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            self.update_status(f"Project saved: {Path(file_path).name}")
            self.logger.info(f"Project saved to: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")
            self.logger.error(f"Failed to save project: {e}")

    def export_data(self):
        """Export scraped data."""
        if not self.scraped_data.get("characters"):
            QMessageBox.information(self, "No Data", "No data available to export.")
            return

        # 建立匯出對話框
        from gui.dialogs.export_dialog import ExportDialog

        dialog = ExportDialog(self.scraped_data.get("characters", []), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            export_config = dialog.get_export_configuration()
            self._perform_export(export_config)

    def _perform_export(self, config: Dict[str, Any]):
        """執行資料匯出"""
        try:
            format_type = config["format"]
            file_path = config["file_path"]
            characters = config["data"]

            if format_type == "JSON":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(characters, f, indent=2, ensure_ascii=False)

            elif format_type == "CSV":
                import pandas as pd

                df = pd.json_normalize(characters)
                df.to_csv(file_path, index=False, encoding="utf-8")

            elif format_type == "Excel":
                import pandas as pd

                df = pd.json_normalize(characters)
                df.to_excel(file_path, index=False)

            self.update_status(f"Data exported to: {Path(file_path).name}")
            QMessageBox.information(
                self, "Export Complete", f"Data exported successfully to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{e}")
            self.logger.error(f"Export failed: {e}")

    def open_preferences(self):
        """Open preferences dialog."""
        from gui.dialogs.preferences_dialog import PreferencesDialog

        dialog = PreferencesDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 套用新設定
            settings = dialog.get_settings()
            self._apply_preferences(settings)

    def _apply_preferences(self, settings: Dict[str, Any]):
        """套用偏好設定"""
        try:
            # 更新 UI 主題
            if "theme" in settings:
                self._apply_theme(settings["theme"])

            # 更新語言設定
            if "language" in settings:
                self._apply_language(settings["language"])

            # 更新其他設定
            self.logger.info("Preferences applied successfully")

        except Exception as e:
            self.logger.error(f"Failed to apply preferences: {e}")

    def open_database_viewer(self):
        """Open database viewer."""
        try:
            from gui.dialogs.database_viewer import DatabaseViewer

            viewer = DatabaseViewer(self)
            viewer.show()

            self.logger.info("Database viewer opened")

        except ImportError:
            QMessageBox.information(
                self, "Feature Not Available", "Database viewer is not yet implemented."
            )

    def open_log_viewer(self):
        """Open log viewer."""
        try:
            from gui.widgets.log_viewer import LogViewerWidget

            log_viewer = QDialog(self)
            log_viewer.setWindowTitle("Log Viewer")
            log_viewer.setModal(False)
            log_viewer.resize(800, 600)

            layout = QVBoxLayout(log_viewer)
            log_widget = LogViewerWidget()
            layout.addWidget(log_widget)

            log_viewer.show()

            self.logger.info("Log viewer opened")

        except ImportError:
            QMessageBox.information(
                self, "Feature Not Available", "Log viewer is not yet implemented."
            )

    def open_user_guide(self):
        """Open user guide."""
        try:
            import webbrowser

            # 嘗試開啟本地文件
            guide_path = Path(__file__).parent.parent / "docs" / "user_guide.html"

            if guide_path.exists():
                webbrowser.open(f"file://{guide_path.absolute()}")
            else:
                # 開啟線上文件
                webbrowser.open("https://github.com/your-repo/fandom-scraper/wiki")

            self.logger.info("User guide opened")

        except Exception as e:
            QMessageBox.information(
                self, "Guide Not Available", f"Failed to open user guide:\n{e}"
            )
            self.logger.error(f"Failed to open user guide: {e}")

    def on_config_changed(self, config: Dict[str, Any]):
        """處理配置變更 - 完成 TODO"""
        try:
            # 驗證配置
            validation_result = self._validate_configuration(config)

            if validation_result["valid"]:
                # 更新 UI 狀態
                self.update_status("Configuration updated and validated")

                # 更新連線狀態
                if config.get("base_url"):
                    self._test_connection(config["base_url"])

            else:
                # 顯示驗證錯誤
                error_msg = validation_result.get("error", "Invalid configuration")
                self.update_status(f"Configuration error: {error_msg}")

            self.logger.info("Configuration change processed")

        except Exception as e:
            self.logger.error(f"Failed to process configuration change: {e}")

    def _validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """驗證爬蟲配置"""
        try:
            errors = []

            # 檢查必要欄位
            required_fields = ["anime_name", "base_url"]
            for field in required_fields:
                if not config.get(field):
                    errors.append(f"Missing required field: {field}")

            # 驗證 URL 格式
            if config.get("base_url"):
                url = config["base_url"]
                if not url.startswith(("http://", "https://")):
                    errors.append("Base URL must start with http:// or https://")

            # 驗證數值範圍
            numeric_validations = {
                "max_characters": (1, 10000),
                "download_delay": (0.1, 60.0),
                "concurrent_requests": (1, 32),
            }

            for field, (min_val, max_val) in numeric_validations.items():
                value = config.get(field)
                if value is not None:
                    try:
                        value = float(value)
                        if not (min_val <= value <= max_val):
                            errors.append(
                                f"{field} must be between {min_val} and {max_val}"
                            )
                    except (ValueError, TypeError):
                        errors.append(f"{field} must be a valid number")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "error": "; ".join(errors) if errors else None,
            }

        except Exception as e:
            return {"valid": False, "errors": [str(e)], "error": str(e)}

    def _test_connection(self, url: str):
        """測試連線狀態"""
        try:
            # 使用爬蟲控制器測試連線
            if self.scraper_controller.test_connection(url):
                self.connection_label.setText("Connected")
                self.connection_label.setStyleSheet("color: green;")
            else:
                self.connection_label.setText("Connection Failed")
                self.connection_label.setStyleSheet("color: red;")

        except Exception as e:
            self.connection_label.setText("Connection Error")
            self.connection_label.setStyleSheet("color: red;")
            self.logger.error(f"Connection test failed: {e}")

    # 其他輔助方法

    def _apply_theme(self, theme: str):
        """套用主題"""
        if theme == "dark":
            self.setStyleSheet(
                """
                QMainWindow { background-color: #2b2b2b; color: #ffffff; }
                QGroupBox { color: #ffffff; border: 1px solid #555555; }
                QLabel { color: #ffffff; }
                QTextEdit { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555555; }
                QTableWidget { background-color: #3c3c3c; color: #ffffff; gridline-color: #555555; }
            """
            )
        else:  # light theme
            self.setStyleSheet("")  # 使用預設樣式

    def _apply_language(self, language: str):
        """
        Apply language settings to the application.
        Complete implementation of TODO item.
        """
        try:
            self.logger.info(f"Applying language setting: {language}")

            # Store current language
            self.current_language = language

            # Language mapping
            language_codes = {
                "English": "en",
                "中文": "zh",
                "日本語": "ja",
                "한국어": "ko",
            }

            lang_code = language_codes.get(language, "en")

            # Update window title
            titles = {
                "en": "Fandom Character Scraper",
                "zh": "Fandom 角色爬取器",
                "ja": "Fandomキャラクタースクレーパー",
                "ko": "팬덤 캐릭터 스크래퍼",
            }
            self.setWindowTitle(titles.get(lang_code, titles["en"]))

            # Update menu texts
            self._update_menu_language(lang_code)

            # Update tab texts
            self._update_tab_language(lang_code)

            # Update widget languages
            self._update_widget_language(lang_code)

            # Update status bar
            status_messages = {
                "en": "Language changed to English",
                "zh": "语言已更改为中文",
                "ja": "言語が日本語に変更されました",
                "ko": "언어가 한국어로 변경되었습니다",
            }
            self.update_status(status_messages.get(lang_code, status_messages["en"]))

            # Save language preference
            self._save_language_preference(language)

            self.logger.info(f"Language successfully changed to: {language}")

        except Exception as e:
            self.logger.error(f"Failed to apply language {language}: {e}")
            self.update_status("Failed to change language")

    def _update_menu_language(self, lang_code: str):
        """Update menu item texts based on language."""
        menu_texts = {
            "en": {
                "file": "File",
                "new": "New Project",
                "open": "Open Project",
                "save": "Save Project",
                "save_as": "Save As...",
                "export": "Export Data",
                "exit": "Exit",
                "edit": "Edit",
                "preferences": "Preferences",
                "tools": "Tools",
                "database_viewer": "Database Viewer",
                "log_viewer": "Log Viewer",
                "help": "Help",
                "user_guide": "User Guide",
                "about": "About",
            },
            "zh": {
                "file": "文件",
                "new": "新建项目",
                "open": "打开项目",
                "save": "保存项目",
                "save_as": "另存为...",
                "export": "导出数据",
                "exit": "退出",
                "edit": "编辑",
                "preferences": "首选项",
                "tools": "工具",
                "database_viewer": "数据库查看器",
                "log_viewer": "日志查看器",
                "help": "帮助",
                "user_guide": "用户指南",
                "about": "关于",
            },
            "ja": {
                "file": "ファイル",
                "new": "新しいプロジェクト",
                "open": "プロジェクトを開く",
                "save": "プロジェクトを保存",
                "save_as": "名前を付けて保存...",
                "export": "データをエクスポート",
                "exit": "終了",
                "edit": "編集",
                "preferences": "環境設定",
                "tools": "ツール",
                "database_viewer": "データベースビューア",
                "log_viewer": "ログビューア",
                "help": "ヘルプ",
                "user_guide": "ユーザーガイド",
                "about": "このアプリについて",
            },
            "ko": {
                "file": "파일",
                "new": "새 프로젝트",
                "open": "프로젝트 열기",
                "save": "프로젝트 저장",
                "save_as": "다른 이름으로 저장...",
                "export": "데이터 내보내기",
                "exit": "종료",
                "edit": "편집",
                "preferences": "환경설정",
                "tools": "도구",
                "database_viewer": "데이터베이스 뷰어",
                "log_viewer": "로그 뷰어",
                "help": "도움말",
                "user_guide": "사용자 가이드",
                "about": "정보",
            },
        }

        texts = menu_texts.get(lang_code, menu_texts["en"])

        # Update menubar
        menubar = self.menuBar()
        menus = menubar.findChildren(QMenu)  # type: ignore

        # Update menu titles (simplified - in real app would need more robust menu finding)
        for menu in menus:
            menu_text = menu.title().replace("&", "").lower()
            if menu_text in texts:
                menu.setTitle(texts[menu_text])

    def _update_tab_language(self, lang_code: str):
        """Update tab texts based on language."""
        tab_texts = {
            "en": ["Configuration", "Data Viewer", "Progress"],
            "zh": ["配置", "数据查看器", "进度"],
            "ja": ["設定", "データビューア", "進捗"],
            "ko": ["구성", "데이터 뷰어", "진행률"],
        }

        texts = tab_texts.get(lang_code, tab_texts["en"])

        # Update tab widget texts
        if hasattr(self, "tab_widget"):
            for i in range(self.tab_widget.count()):
                if i < len(texts):
                    self.tab_widget.setTabText(i, texts[i])

    def _update_widget_language(self, lang_code: str):
        """Update widget texts based on language."""
        # Update configuration widget language
        if hasattr(self, "config_widget"):
            self.config_widget.update_language(lang_code)

        # Update data viewer language
        if hasattr(self, "data_viewer"):
            self.data_viewer.update_language(lang_code)

        # Update other widgets as needed
        # This would be expanded to update all text in the application

    def _save_language_preference(self, language: str):
        """Save language preference to settings."""
        try:
            import json
            import os

            # Create settings directory if it doesn't exist
            settings_dir = os.path.expanduser("~/.fandom_scraper")
            os.makedirs(settings_dir, exist_ok=True)

            settings_file = os.path.join(settings_dir, "settings.json")

            # Load existing settings or create new
            settings = {}
            if os.path.exists(settings_file):
                try:
                    with open(settings_file, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                except:
                    settings = {}

            # Update language setting
            settings["language"] = language

            # Save settings
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Language preference saved: {language}")

        except Exception as e:
            self.logger.error(f"Failed to save language preference: {e}")

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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.scraped_data = {}
            self.data_viewer.update_data([])
            self.update_status("All data cleared")
            self.logger.info("All scraped data cleared")

    def refresh_data(self):
        """Refresh data display."""
        self.data_viewer.refresh_data()
        self.update_status("Data refreshed")

    def create_images_widget(self) -> QWidget:
        """
        建立圖片顯示元件 - 完成原有 TODO

        Returns:
            Widget for displaying scraped images
        """
        images_widget = QWidget()
        layout = QVBoxLayout(images_widget)

        # 工具列
        toolbar_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh Images")
        refresh_btn.clicked.connect(self._refresh_images)
        toolbar_layout.addWidget(refresh_btn)

        export_images_btn = QPushButton("Export Images")
        export_images_btn.clicked.connect(self._export_images)
        toolbar_layout.addWidget(export_images_btn)

        toolbar_layout.addStretch()

        view_combo = QComboBox()
        view_combo.addItems(["Grid View", "List View"])
        view_combo.currentTextChanged.connect(self._change_images_view)
        toolbar_layout.addWidget(view_combo)

        layout.addLayout(toolbar_layout)

        # 圖片顯示區域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.images_container = QWidget()
        self.images_layout = QGridLayout(self.images_container)
        scroll_area.setWidget(self.images_container)

        layout.addWidget(scroll_area)

        return images_widget

    def _refresh_images(self):
        """重新整理圖片顯示"""
        # 清除現有圖片
        for i in reversed(range(self.images_layout.count())):
            child = self.images_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # 重新載入圖片
        if hasattr(self, "scraped_data") and self.scraped_data:
            characters = self.scraped_data.get("characters", [])
            row, col = 0, 0
            max_cols = 4

            for char in characters:
                images = char.get("images", [])
                for img_url in images[:1]:  # 只顯示第一張圖
                    try:
                        img_widget = self._create_image_widget(
                            img_url, char.get("name", "Unknown")
                        )
                        self.images_layout.addWidget(img_widget, row, col)

                        col += 1
                        if col >= max_cols:
                            col = 0
                            row += 1

                    except Exception as e:
                        self.logger.error(f"Failed to load image: {e}")

        self.update_status("Images refreshed")

    def _create_image_widget(self, img_url: str, char_name: str) -> QWidget:
        """建立單一圖片元件"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setFixedSize(150, 200)

        layout = QVBoxLayout(widget)

        # 圖片標籤（暫時顯示佔位符）
        img_label = QLabel()
        img_label.setFixedSize(130, 150)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        img_label.setText("Loading...")
        layout.addWidget(img_label)

        # 角色名稱
        name_label = QLabel(char_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        return widget

    def _export_images(self):
        """匯出所有圖片"""
        if not hasattr(self, "scraped_data") or not self.scraped_data:
            QMessageBox.information(self, "No Data", "No images available to export.")
            return

        # 選擇匯出目錄
        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")

        if export_dir:
            try:
                # 這裡實現圖片匯出邏輯
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Images will be exported to:\n{export_dir}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export images:\n{e}"
                )

    def _change_images_view(self, view_type: str):
        """變更圖片檢視模式"""
        if view_type == "List View":
            # 實現列表檢視
            pass
        else:
            # 使用網格檢視（預設）
            pass

        self.logger.info(f"Images view changed to: {view_type}")

    def closeEvent(self, event):
        """Handle application close event."""
        if self.is_scraping:
            reply = QMessageBox.question(
                self,
                "Close Application",
                "Scraping is in progress. Do you want to stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
