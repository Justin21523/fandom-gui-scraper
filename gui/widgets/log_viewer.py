# gui/widgets/log_viewer.py
"""
Log viewer widget for displaying and analyzing application logs.

This module provides comprehensive log viewing functionality including
filtering, searching, exporting, and real-time log monitoring.
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

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
    QLineEdit,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QFrame,
    QTabWidget,
    QProgressBar,
    QSlider,
    QMessageBox,
    QFileDialog,
    QMenu,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QDateTimeEdit,
    QButtonGroup,
    QRadioButton,
)
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QTimer,
    QThread,
    QDateTime,
    QSize,
    pyqtSlot,
    QFileSystemWatcher,
    QRegularExpression,
)
from PyQt6.QtGui import (
    QFont,
    QColor,
    QPalette,
    QTextCharFormat,
    QSyntaxHighlighter,
    QTextDocument,
    QAction,
    QIcon,
    QCursor,
    QKeySequence,
    QShortcut,
)

from utils.logger import get_logger


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry:
    """Log entry data structure."""

    def __init__(
        self,
        timestamp: str,
        level: str,
        logger: str,
        message: str,
        line_number: int = 0,
        raw_line: str = "",
    ):
        self.timestamp = timestamp
        self.level = level
        self.logger = logger
        self.message = message
        self.line_number = line_number
        self.raw_line = raw_line
        self.datetime = self._parse_timestamp(timestamp)

    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object."""
        try:
            # Try common timestamp formats
            formats = [
                "%Y-%m-%d %H:%M:%S,%f",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue

            return None
        except Exception:
            return None


class LogHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for log text."""

    def __init__(self, parent: QTextDocument):
        super().__init__(parent)

        # Define highlighting rules
        self.highlighting_rules = []

        # Log levels
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(220, 50, 47))  # Red
        error_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((QRegularExpression(r"\bERROR\b"), error_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"\bCRITICAL\b"), error_format)
        )

        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(255, 165, 0))  # Orange
        warning_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r"\bWARNING\b"), warning_format)
        )

        info_format = QTextCharFormat()
        info_format.setForeground(QColor(0, 150, 200))  # Blue
        self.highlighting_rules.append((QRegularExpression(r"\bINFO\b"), info_format))

        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(128, 128, 128))  # Gray
        self.highlighting_rules.append((QRegularExpression(r"\bDEBUG\b"), debug_format))

        # Timestamps
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(100, 100, 100))
        self.highlighting_rules.append(
            (
                QRegularExpression(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,\.]\d+"),
                timestamp_format,
            )
        )

        # URLs and file paths
        url_format = QTextCharFormat()
        url_format.setForeground(QColor(0, 100, 200))
        url_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        self.highlighting_rules.append(
            (QRegularExpression(r"https?://[^\s]+"), url_format)
        )

        path_format = QTextCharFormat()
        path_format.setForeground(QColor(150, 75, 0))
        self.highlighting_rules.append(
            (QRegularExpression(r"[A-Za-z]:\\[^\s]+|/[^\s]+"), path_format)
        )

    def highlightBlock(self, text: str):
        """Apply highlighting to text block."""
        for pattern, format_obj in self.highlighting_rules:
            expression = pattern
            iterator = expression.globalMatch(text)

            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), format_obj
                )


class LogViewerWidget(QWidget):
    """
    Comprehensive log viewer widget for application logs.

    Features:
    - Real-time log monitoring
    - Advanced filtering and searching
    - Log level filtering
    - Export functionality
    - Log statistics and analysis
    - Syntax highlighting
    """

    # Custom signals
    log_selected = pyqtSignal(object)  # LogEntry
    filter_changed = pyqtSignal(dict)  # filter criteria
    export_requested = pyqtSignal(str, list)  # format, log entries

    def __init__(self, parent=None):
        """Initialize log viewer widget."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)

        # Data
        self.log_entries = []
        self.filtered_entries = []
        self.current_log_files = []
        self.file_watcher = QFileSystemWatcher()

        # Settings
        self.auto_scroll = True
        self.max_entries = 10000
        self.refresh_interval = 1000  # ms
        self.current_log_file = None

        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.load_default_log_files()

        # Start monitoring timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(self.refresh_interval)

        self.logger.info("Log viewer widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)

        # Left panel - filters and controls
        left_panel = self._create_control_panel()
        content_splitter.addWidget(left_panel)

        # Center panel - log display
        center_panel = self._create_log_display_panel()
        content_splitter.addWidget(center_panel)

        # Right panel - log details and statistics
        right_panel = self._create_details_panel()
        content_splitter.addWidget(right_panel)

        # Set splitter sizes
        content_splitter.setSizes([250, 600, 300])

        # Status bar
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

    def _create_toolbar(self) -> QWidget:
        """Create toolbar with log controls."""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 2, 5, 2)

        # File controls
        self.open_log_btn = QPushButton("Open Log")
        self.reload_btn = QPushButton("Reload")
        self.clear_btn = QPushButton("Clear")

        layout.addWidget(self.open_log_btn)
        layout.addWidget(self.reload_btn)
        layout.addWidget(self.clear_btn)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        layout.addWidget(separator)

        # Auto-scroll toggle
        self.auto_scroll_checkbox = QCheckBox("Auto Scroll")
        self.auto_scroll_checkbox.setChecked(True)
        layout.addWidget(self.auto_scroll_checkbox)

        # Real-time monitoring
        self.monitor_checkbox = QCheckBox("Real-time")
        self.monitor_checkbox.setChecked(True)
        layout.addWidget(self.monitor_checkbox)

        layout.addStretch()

        # Export controls
        self.export_btn = QPushButton("Export")
        self.settings_btn = QPushButton("Settings")

        layout.addWidget(self.export_btn)
        layout.addWidget(self.settings_btn)

        return toolbar

    def _create_control_panel(self) -> QWidget:
        """Create control panel with filters."""
        panel = QWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)

        # Log file selection
        file_group = QGroupBox("Log Files")
        file_layout = QVBoxLayout(file_group)

        self.log_files_list = QListWidget()
        self.log_files_list.setMaximumHeight(120)
        self.log_files_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        file_layout.addWidget(self.log_files_list)

        file_buttons_layout = QHBoxLayout()
        self.add_file_btn = QPushButton("Add")
        self.remove_file_btn = QPushButton("Remove")

        file_buttons_layout.addWidget(self.add_file_btn)
        file_buttons_layout.addWidget(self.remove_file_btn)
        file_layout.addLayout(file_buttons_layout)

        layout.addWidget(file_group)

        # Search and filter
        filter_group = QGroupBox("Search & Filter")
        filter_layout = QVBoxLayout(filter_group)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        filter_layout.addWidget(self.search_input)

        # Search options
        search_options_layout = QHBoxLayout()
        self.case_sensitive_checkbox = QCheckBox("Case sensitive")
        self.regex_checkbox = QCheckBox("Regex")

        search_options_layout.addWidget(self.case_sensitive_checkbox)
        search_options_layout.addWidget(self.regex_checkbox)
        filter_layout.addLayout(search_options_layout)

        # Log level filter
        level_layout = QFormLayout()

        self.level_filter_group = QButtonGroup()
        self.show_all_radio = QRadioButton("All levels")
        self.show_all_radio.setChecked(True)
        self.show_errors_only_radio = QRadioButton("Errors only")
        self.show_warnings_plus_radio = QRadioButton("Warnings+")
        self.custom_levels_radio = QRadioButton("Custom")

        self.level_filter_group.addButton(self.show_all_radio, 0)
        self.level_filter_group.addButton(self.show_errors_only_radio, 1)
        self.level_filter_group.addButton(self.show_warnings_plus_radio, 2)
        self.level_filter_group.addButton(self.custom_levels_radio, 3)

        level_layout.addRow(self.show_all_radio)
        level_layout.addRow(self.show_errors_only_radio)
        level_layout.addRow(self.show_warnings_plus_radio)
        level_layout.addRow(self.custom_levels_radio)

        # Custom level checkboxes
        custom_levels_layout = QVBoxLayout()
        self.debug_checkbox = QCheckBox("DEBUG")
        self.info_checkbox = QCheckBox("INFO")
        self.warning_checkbox = QCheckBox("WARNING")
        self.error_checkbox = QCheckBox("ERROR")
        self.critical_checkbox = QCheckBox("CRITICAL")

        # Initially disable custom checkboxes
        self.debug_checkbox.setEnabled(False)
        self.info_checkbox.setEnabled(False)
        self.warning_checkbox.setEnabled(False)
        self.error_checkbox.setEnabled(False)
        self.critical_checkbox.setEnabled(False)

        custom_levels_layout.addWidget(self.debug_checkbox)
        custom_levels_layout.addWidget(self.info_checkbox)
        custom_levels_layout.addWidget(self.warning_checkbox)
        custom_levels_layout.addWidget(self.error_checkbox)
        custom_levels_layout.addWidget(self.critical_checkbox)

        level_layout.addRow("Levels:", custom_levels_layout)
        filter_layout.addLayout(level_layout)

        layout.addWidget(filter_group)

        # Time range filter
        time_group = QGroupBox("Time Range")
        time_layout = QFormLayout(time_group)

        self.time_filter_checkbox = QCheckBox("Enable time filter")
        time_layout.addRow(self.time_filter_checkbox)

        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.start_time_edit.setEnabled(False)
        time_layout.addRow("From:", self.start_time_edit)

        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setDateTime(QDateTime.currentDateTime())
        self.end_time_edit.setEnabled(False)
        time_layout.addRow("To:", self.end_time_edit)

        layout.addWidget(time_group)

        # Logger filter
        logger_group = QGroupBox("Logger Filter")
        logger_layout = QVBoxLayout(logger_group)

        self.logger_filter_input = QLineEdit()
        self.logger_filter_input.setPlaceholderText("Logger name pattern...")
        logger_layout.addWidget(self.logger_filter_input)

        self.logger_list = QListWidget()
        self.logger_list.setMaximumHeight(100)
        self.logger_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        logger_layout.addWidget(self.logger_list)

        layout.addWidget(logger_group)

        layout.addStretch()
        return panel

    def _create_log_display_panel(self) -> QWidget:
        """Create main log display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget for different views
        self.display_tabs = QTabWidget()
        layout.addWidget(self.display_tabs)

        # Table view
        self.log_table = self._create_log_table()
        self.display_tabs.addTab(self.log_table, "Table View")

        # Text view
        self.log_text = self._create_log_text()
        self.display_tabs.addTab(self.log_text, "Text View")

        # Analysis view
        analysis_view = self._create_analysis_view()
        self.display_tabs.addTab(analysis_view, "Analysis")

        return panel

    def _create_log_table(self) -> QWidget:
        """Create log table view."""
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(
            ["Timestamp", "Level", "Logger", "Message", "Line"]
        )

        # Configure table
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table_widget.setSortingEnabled(True)

        # Set column widths
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )  # Timestamp
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Level
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )  # Logger
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Message
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Line

        return self.table_widget

    def _create_log_text(self) -> QWidget:
        """Create log text view."""
        self.text_widget = QTextEdit()
        self.text_widget.setReadOnly(True)
        self.text_widget.setFont(QFont("Consolas", 10))

        # Set up syntax highlighting
        self.highlighter = LogHighlighter(self.text_widget.document())

        # Style the text widget
        self.text_widget.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
        """
        )

        return self.text_widget

    def _create_analysis_view(self) -> QWidget:
        """Create log analysis view."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Summary statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)

        self.total_entries_label = QLabel("0")
        self.error_count_label = QLabel("0")
        self.warning_count_label = QLabel("0")
        self.info_count_label = QLabel("0")
        self.debug_count_label = QLabel("0")

        stats_layout.addRow("Total Entries:", self.total_entries_label)
        stats_layout.addRow("Errors:", self.error_count_label)
        stats_layout.addRow("Warnings:", self.warning_count_label)
        stats_layout.addRow("Info:", self.info_count_label)
        stats_layout.addRow("Debug:", self.debug_count_label)

        layout.addWidget(stats_group)

        # Top errors/warnings
        top_issues_group = QGroupBox("Top Issues")
        top_issues_layout = QVBoxLayout(top_issues_group)

        self.top_issues_list = QListWidget()
        self.top_issues_list.setMaximumHeight(200)
        top_issues_layout.addWidget(self.top_issues_list)

        layout.addWidget(top_issues_group)

        # Logger activity
        logger_activity_group = QGroupBox("Logger Activity")
        logger_activity_layout = QVBoxLayout(logger_activity_group)

        self.logger_activity_list = QListWidget()
        self.logger_activity_list.setMaximumHeight(150)
        logger_activity_layout.addWidget(self.logger_activity_list)

        layout.addWidget(logger_activity_group)

        layout.addStretch()
        return widget

    def _create_details_panel(self) -> QWidget:
        """Create details panel for selected log entry."""
        panel = QWidget()
        panel.setMaximumWidth(350)
        layout = QVBoxLayout(panel)

        # Selected entry details
        details_group = QGroupBox("Entry Details")
        details_layout = QFormLayout(details_group)

        self.detail_timestamp_label = QLabel("-")
        self.detail_level_label = QLabel("-")
        self.detail_logger_label = QLabel("-")
        self.detail_line_label = QLabel("-")

        details_layout.addRow("Timestamp:", self.detail_timestamp_label)
        details_layout.addRow("Level:", self.detail_level_label)
        details_layout.addRow("Logger:", self.detail_logger_label)
        details_layout.addRow("Line Number:", self.detail_line_label)

        layout.addWidget(details_group)

        # Full message
        message_group = QGroupBox("Full Message")
        message_layout = QVBoxLayout(message_group)

        self.detail_message_text = QTextEdit()
        self.detail_message_text.setReadOnly(True)
        self.detail_message_text.setMaximumHeight(200)
        message_layout.addWidget(self.detail_message_text)

        layout.addWidget(message_group)

        # Context (surrounding entries)
        context_group = QGroupBox("Context")
        context_layout = QVBoxLayout(context_group)

        context_controls = QHBoxLayout()
        self.context_size_spinbox = QSpinBox()
        self.context_size_spinbox.setRange(1, 20)
        self.context_size_spinbox.setValue(5)
        self.show_context_btn = QPushButton("Show Context")

        context_controls.addWidget(QLabel("Lines:"))
        context_controls.addWidget(self.context_size_spinbox)
        context_controls.addWidget(self.show_context_btn)
        context_layout.addLayout(context_controls)

        self.context_text = QTextEdit()
        self.context_text.setReadOnly(True)
        self.context_text.setMaximumHeight(150)
        self.context_text.setFont(QFont("Consolas", 9))
        context_layout.addWidget(self.context_text)

        layout.addWidget(context_group)

        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.copy_entry_btn = QPushButton("Copy Entry")
        self.copy_message_btn = QPushButton("Copy Message")
        self.filter_logger_btn = QPushButton("Filter by Logger")
        self.find_similar_btn = QPushButton("Find Similar")

        actions_layout.addWidget(self.copy_entry_btn)
        actions_layout.addWidget(self.copy_message_btn)
        actions_layout.addWidget(self.filter_logger_btn)
        actions_layout.addWidget(self.find_similar_btn)

        layout.addWidget(actions_group)

        layout.addStretch()
        return panel

    def _create_status_bar(self) -> QWidget:
        """Create status bar."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("Ready")
        self.entries_count_label = QLabel("Entries: 0")
        self.filtered_count_label = QLabel("Filtered: 0")
        self.last_update_label = QLabel("Last update: Never")

        self.loading_progress = QProgressBar()
        self.loading_progress.setVisible(False)
        self.loading_progress.setMaximumWidth(150)

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.entries_count_label)
        layout.addWidget(self.filtered_count_label)
        layout.addWidget(self.last_update_label)
        layout.addWidget(self.loading_progress)

        return frame

    def setup_connections(self):
        """Set up signal connections."""
        # Toolbar connections
        self.open_log_btn.clicked.connect(self.open_log_file)
        self.reload_btn.clicked.connect(self.reload_logs)
        self.clear_btn.clicked.connect(self.clear_logs)
        self.export_btn.clicked.connect(self.export_logs)
        self.settings_btn.clicked.connect(self.show_settings)

        self.auto_scroll_checkbox.toggled.connect(self._on_auto_scroll_toggled)
        self.monitor_checkbox.toggled.connect(self._on_monitor_toggled)

        # File list connections
        self.add_file_btn.clicked.connect(self.add_log_file)
        self.remove_file_btn.clicked.connect(self.remove_selected_files)
        self.log_files_list.itemSelectionChanged.connect(
            self._on_file_selection_changed
        )

        # Filter connections
        self.search_input.textChanged.connect(self._apply_filters)
        self.case_sensitive_checkbox.toggled.connect(self._apply_filters)
        self.regex_checkbox.toggled.connect(self._apply_filters)

        # Level filter connections
        self.level_filter_group.buttonClicked.connect(self._on_level_filter_changed)
        self.debug_checkbox.toggled.connect(self._apply_filters)
        self.info_checkbox.toggled.connect(self._apply_filters)
        self.warning_checkbox.toggled.connect(self._apply_filters)
        self.error_checkbox.toggled.connect(self._apply_filters)
        self.critical_checkbox.toggled.connect(self._apply_filters)

        # Time filter connections
        self.time_filter_checkbox.toggled.connect(self._on_time_filter_toggled)
        self.start_time_edit.dateTimeChanged.connect(self._apply_filters)
        self.end_time_edit.dateTimeChanged.connect(self._apply_filters)

        # Logger filter connections
        self.logger_filter_input.textChanged.connect(self._apply_filters)
        self.logger_list.itemSelectionChanged.connect(self._apply_filters)

        # Table connections
        self.table_widget.itemSelectionChanged.connect(self._on_entry_selected)
        self.table_widget.itemDoubleClicked.connect(self._on_entry_double_clicked)

        # Details panel connections
        self.show_context_btn.clicked.connect(self._show_entry_context)
        self.copy_entry_btn.clicked.connect(self._copy_selected_entry)
        self.copy_message_btn.clicked.connect(self._copy_entry_message)
        self.filter_logger_btn.clicked.connect(self._filter_by_selected_logger)
        self.find_similar_btn.clicked.connect(self._find_similar_entries)

        # File watcher
        self.file_watcher.fileChanged.connect(self._on_file_changed)

    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Standard shortcuts
        QShortcut(QKeySequence.StandardKey.Find, self, self._focus_search)
        QShortcut(QKeySequence("F5"), self, self.reload_logs)
        QShortcut(QKeySequence("Ctrl+L"), self, self.clear_logs)
        QShortcut(QKeySequence("Ctrl+E"), self, self.export_logs)

        # Navigation shortcuts
        QShortcut(QKeySequence("Ctrl+Up"), self, self._go_to_previous_error)
        QShortcut(QKeySequence("Ctrl+Down"), self, self._go_to_next_error)

        # Filter shortcuts
        QShortcut(
            QKeySequence("Ctrl+1"), self, lambda: self.show_all_radio.setChecked(True)
        )
        QShortcut(
            QKeySequence("Ctrl+2"),
            self,
            lambda: self.show_errors_only_radio.setChecked(True),
        )
        QShortcut(
            QKeySequence("Ctrl+3"),
            self,
            lambda: self.show_warnings_plus_radio.setChecked(True),
        )

    def load_default_log_files(self):
        """Load default log files."""
        # Try to find application log files
        log_dirs = [
            Path.cwd() / "logs",
            Path.home() / ".fandom_scraper" / "logs",
            Path("/var/log"),  # Linux
            Path("C:/ProgramData/FandomScraper/logs"),  # Windows
        ]

        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    self.add_log_file_path(str(log_file))

        # Add some default files if they exist
        default_files = ["application.log", "scraper.log", "errors.log", "debug.log"]

        for filename in default_files:
            if os.path.exists(filename):
                self.add_log_file_path(filename)

    def open_log_file(self):
        """Open log file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Log Files (*.log *.txt);;All Files (*)"
        )

        if file_path:
            self.add_log_file_path(file_path)

    def add_log_file_path(self, file_path: str):
        """Add log file path to monitoring list."""
        if file_path not in self.current_log_files:
            self.current_log_files.append(file_path)

            # Add to UI list
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setToolTip(file_path)
            item.setCheckState(Qt.CheckState.Checked)
            self.log_files_list.addItem(item)

            # Add to file watcher
            if os.path.exists(file_path):
                self.file_watcher.addPath(file_path)

            self.logger.info(f"Added log file: {file_path}")

    def add_log_file(self):
        """Add new log file."""
        self.open_log_file()

    def remove_selected_files(self):
        """Remove selected log files."""
        selected_items = self.log_files_list.selectedItems()

        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)

            # Remove from monitoring
            if file_path in self.current_log_files:
                self.current_log_files.remove(file_path)

            # Remove from file watcher
            self.file_watcher.removePath(file_path)

            # Remove from UI
            row = self.log_files_list.row(item)
            self.log_files_list.takeItem(row)

        # Reload logs
        self.reload_logs()

    def reload_logs(self):
        """Reload all log entries."""
        self.loading_progress.setVisible(True)
        self.status_label.setText("Loading logs...")

        # Create worker thread for loading
        self.load_worker = LogLoadWorker(self.current_log_files)
        self.load_worker.progress.connect(self._update_loading_progress)
        self.load_worker.finished.connect(self._on_logs_loaded)
        self.load_worker.start()

    def clear_logs(self):
        """Clear all log entries."""
        self.log_entries.clear()
        self.filtered_entries.clear()
        self._update_displays()
        self._update_statistics()

        self.status_label.setText("Logs cleared")
        self.logger.info("Log entries cleared")

    def refresh_logs(self):
        """Refresh logs (incremental update)."""
        if not self.monitor_checkbox.isChecked():
            return

        # Only refresh if files have changed
        for file_path in self.current_log_files:
            if os.path.exists(file_path):
                # Check if file was modified recently
                mtime = os.path.getmtime(file_path)
                current_time = datetime.now().timestamp()

                if current_time - mtime < 5:  # Modified within last 5 seconds
                    self._load_file_incremental(file_path)
                    break

    def export_logs(self):
        """Export filtered logs."""
        if not self.filtered_entries:
            QMessageBox.information(self, "No Data", "No log entries to export.")
            return

        # Show export dialog
        dialog = LogExportDialog(self.filtered_entries, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            export_config = dialog.get_export_config()
            self._export_logs_with_config(export_config)

    def show_settings(self):
        """Show log viewer settings."""
        dialog = LogViewerSettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings = dialog.get_settings()
            self._apply_settings(settings)

    def _apply_filters(self):
        """Apply current filter criteria."""
        search_text = self.search_input.text()
        case_sensitive = self.case_sensitive_checkbox.isChecked()
        use_regex = self.regex_checkbox.isChecked()

        # Get level filter
        level_filter = self._get_level_filter()

        # Get time filter
        time_filter_enabled = self.time_filter_checkbox.isChecked()
        start_time = (
            self.start_time_edit.dateTime().toPython() if time_filter_enabled else None
        )
        end_time = (
            self.end_time_edit.dateTime().toPython() if time_filter_enabled else None
        )

        # Get logger filter
        logger_pattern = self.logger_filter_input.text()
        selected_loggers = [item.text() for item in self.logger_list.selectedItems()]

        # Apply filters
        self.filtered_entries = []

        for entry in self.log_entries:
            # Text search filter
            if search_text:
                search_target = f"{entry.message} {entry.logger}"
                if not case_sensitive:
                    search_target = search_target.lower()
                    search_text = search_text.lower()

                if use_regex:
                    try:
                        pattern = re.compile(
                            search_text, re.IGNORECASE if not case_sensitive else 0
                        )
                        if not pattern.search(search_target):
                            continue
                    except re.error:
                        # Invalid regex, fall back to simple search
                        if search_text not in search_target:
                            continue
                else:
                    if search_text not in search_target:
                        continue

            # Level filter
            if level_filter and entry.level not in level_filter:
                continue

            # Time filter
            if start_time and entry.datetime and entry.datetime < start_time:
                continue
            if end_time and entry.datetime and entry.datetime > end_time:
                continue

            # Logger filter
            if logger_pattern:
                if use_regex:
                    try:
                        pattern = re.compile(logger_pattern, re.IGNORECASE)
                        if not pattern.search(entry.logger):
                            continue
                    except re.error:
                        if logger_pattern.lower() not in entry.logger.lower():
                            continue
                else:
                    if logger_pattern.lower() not in entry.logger.lower():
                        continue

            if selected_loggers and entry.logger not in selected_loggers:
                continue

            self.filtered_entries.append(entry)

        # Update displays
        self._update_displays()
        self._update_statistics()

        # Emit signal
        filter_criteria = {
            "search_text": search_text,
            "level_filter": level_filter,
            "time_range": (start_time, end_time) if time_filter_enabled else None,
            "logger_pattern": logger_pattern,
            "selected_loggers": selected_loggers,
        }
        self.filter_changed.emit(filter_criteria)

    def _get_level_filter(self) -> Optional[List[str]]:
        """Get current level filter criteria."""
        selected_id = self.level_filter_group.checkedId()

        if selected_id == 0:  # All levels
            return None
        elif selected_id == 1:  # Errors only
            return ["ERROR", "CRITICAL"]
        elif selected_id == 2:  # Warnings+
            return ["WARNING", "ERROR", "CRITICAL"]
        elif selected_id == 3:  # Custom
            levels = []
            if self.debug_checkbox.isChecked():
                levels.append("DEBUG")
            if self.info_checkbox.isChecked():
                levels.append("INFO")
            if self.warning_checkbox.isChecked():
                levels.append("WARNING")
            if self.error_checkbox.isChecked():
                levels.append("ERROR")
            if self.critical_checkbox.isChecked():
                levels.append("CRITICAL")
            return levels if levels else None

        return None

    def _update_displays(self):
        """Update all display components."""
        self._update_table_view()
        self._update_text_view()
        self._update_logger_list()
        self._update_status_counts()

    def _update_table_view(self):
        """Update table view with filtered entries."""
        self.table_widget.setRowCount(len(self.filtered_entries))

        for row, entry in enumerate(self.filtered_entries):
            # Timestamp
            timestamp_item = QTableWidgetItem(entry.timestamp)
            timestamp_item.setData(Qt.ItemDataRole.UserRole, entry)
            self.table_widget.setItem(row, 0, timestamp_item)

            # Level
            level_item = QTableWidgetItem(entry.level)
            # Color code by level
            if entry.level == "ERROR" or entry.level == "CRITICAL":
                level_item.setForeground(QColor(220, 50, 47))
            elif entry.level == "WARNING":
                level_item.setForeground(QColor(255, 165, 0))
            elif entry.level == "DEBUG":
                level_item.setForeground(QColor(128, 128, 128))

            self.table_widget.setItem(row, 1, level_item)

            # Logger
            logger_item = QTableWidgetItem(entry.logger)
            self.table_widget.setItem(row, 2, logger_item)

            # Message (truncated for table)
            message = entry.message
            if len(message) > 100:
                message = message[:100] + "..."
            message_item = QTableWidgetItem(message)
            message_item.setToolTip(entry.message)
            self.table_widget.setItem(row, 3, message_item)

            # Line number
            line_item = QTableWidgetItem(str(entry.line_number))
            self.table_widget.setItem(row, 4, line_item)

        # Auto-scroll to bottom if enabled
        if self.auto_scroll and self.filtered_entries:
            self.table_widget.scrollToBottom()

    def _update_text_view(self):
        """Update text view with filtered entries."""
        text_content = []

        for entry in self.filtered_entries:
            text_content.append(
                entry.raw_line
                or f"{entry.timestamp} {entry.level} {entry.logger} - {entry.message}"
            )

        self.text_widget.setPlainText("\n".join(text_content))

        # Auto-scroll to bottom if enabled
        if self.auto_scroll and text_content:
            cursor = self.text_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.text_widget.setTextCursor(cursor)

    def _update_logger_list(self):
        """Update logger list with unique loggers."""
        current_loggers = set()
        for entry in self.log_entries:
            current_loggers.add(entry.logger)

        # Update logger list
        self.logger_list.clear()
        for logger in sorted(current_loggers):
            item = QListWidgetItem(logger)
            self.logger_list.addItem(item)

    def _update_statistics(self):
        """Update statistics display."""
        total = len(self.filtered_entries)

        # Count by level
        level_counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}

        top_issues = {}
        logger_activity = {}

        for entry in self.filtered_entries:
            level_counts[entry.level] = level_counts.get(entry.level, 0) + 1

            # Track top issues (error/warning messages)
            if entry.level in ["ERROR", "WARNING", "CRITICAL"]:
                issue_key = entry.message[:100]  # First 100 chars
                top_issues[issue_key] = top_issues.get(issue_key, 0) + 1

            # Track logger activity
            logger_activity[entry.logger] = logger_activity.get(entry.logger, 0) + 1

        # Update labels
        self.total_entries_label.setText(str(total))
        self.error_count_label.setText(
            str(level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0))
        )
        self.warning_count_label.setText(str(level_counts.get("WARNING", 0)))
        self.info_count_label.setText(str(level_counts.get("INFO", 0)))
        self.debug_count_label.setText(str(level_counts.get("DEBUG", 0)))

        # Update top issues list
        self.top_issues_list.clear()
        for issue, count in sorted(
            top_issues.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            item = QListWidgetItem(f"{count}x: {issue}")
            item.setToolTip(issue)
            self.top_issues_list.addItem(item)

        # Update logger activity list
        self.logger_activity_list.clear()
        for logger, count in sorted(
            logger_activity.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            item = QListWidgetItem(f"{logger}: {count}")
            self.logger_activity_list.addItem(item)

    def _update_status_counts(self):
        """Update status bar counts."""
        total_entries = len(self.log_entries)
        filtered_entries = len(self.filtered_entries)

        self.entries_count_label.setText(f"Entries: {total_entries}")
        self.filtered_count_label.setText(f"Filtered: {filtered_entries}")
        self.last_update_label.setText(
            f"Last update: {datetime.now().strftime('%H:%M:%S')}"
        )

    # Event handlers
    def _on_auto_scroll_toggled(self, enabled: bool):
        """Handle auto-scroll toggle."""
        self.auto_scroll = enabled

    def _on_monitor_toggled(self, enabled: bool):
        """Handle real-time monitoring toggle."""
        if enabled:
            self.refresh_timer.start(self.refresh_interval)
        else:
            self.refresh_timer.stop()

    def _on_file_selection_changed(self):
        """Handle log file selection changes."""
        # Could implement selective file loading here
        pass

    def _on_level_filter_changed(self, button):
        """Handle level filter changes."""
        # Enable/disable custom checkboxes
        is_custom = button == self.custom_levels_radio

        self.debug_checkbox.setEnabled(is_custom)
        self.info_checkbox.setEnabled(is_custom)
        self.warning_checkbox.setEnabled(is_custom)
        self.error_checkbox.setEnabled(is_custom)
        self.critical_checkbox.setEnabled(is_custom)

        self._apply_filters()

    def _on_time_filter_toggled(self, enabled: bool):
        """Handle time filter toggle."""
        self.start_time_edit.setEnabled(enabled)
        self.end_time_edit.setEnabled(enabled)
        self._apply_filters()

    def _on_entry_selected(self):
        """Handle log entry selection."""
        current_row = self.table_widget.currentRow()

        if current_row >= 0 and current_row < len(self.filtered_entries):
            entry = self.filtered_entries[current_row]
            self._show_entry_details(entry)
            self.log_selected.emit(entry)

    def _on_entry_double_clicked(self, item: QTableWidgetItem):
        """Handle log entry double click."""
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            # Show full entry in a dialog
            dialog = LogEntryDetailDialog(entry, self)
            dialog.exec()

    def _on_file_changed(self, file_path: str):
        """Handle file system changes."""
        if file_path in self.current_log_files:
            self._load_file_incremental(file_path)

    def _show_entry_details(self, entry: LogEntry):
        """Show details for selected entry."""
        self.detail_timestamp_label.setText(entry.timestamp)
        self.detail_level_label.setText(entry.level)
        self.detail_logger_label.setText(entry.logger)
        self.detail_line_label.setText(str(entry.line_number))
        self.detail_message_text.setPlainText(entry.message)

    def _show_entry_context(self):
        """Show context around selected entry."""
        current_row = self.table_widget.currentRow()

        if current_row >= 0:
            context_size = self.context_size_spinbox.value()
            start_row = max(0, current_row - context_size)
            end_row = min(len(self.filtered_entries), current_row + context_size + 1)

            context_entries = self.filtered_entries[start_row:end_row]
            context_text = []

            for i, entry in enumerate(context_entries):
                prefix = ">>> " if start_row + i == current_row else "    "
                context_text.append(f"{prefix}{entry.raw_line or entry.message}")

            self.context_text.setPlainText("\n".join(context_text))

    # Action methods
    def _focus_search(self):
        """Focus search input."""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _go_to_previous_error(self):
        """Go to previous error/warning."""
        current_row = self.table_widget.currentRow()

        for i in range(current_row - 1, -1, -1):
            if i < len(self.filtered_entries):
                entry = self.filtered_entries[i]
                if entry.level in ["ERROR", "WARNING", "CRITICAL"]:
                    self.table_widget.setCurrentRow(i)
                    break

    def _go_to_next_error(self):
        """Go to next error/warning."""
        current_row = self.table_widget.currentRow()

        for i in range(current_row + 1, len(self.filtered_entries)):
            entry = self.filtered_entries[i]
            if entry.level in ["ERROR", "WARNING", "CRITICAL"]:
                self.table_widget.setCurrentRow(i)
                break

    def _copy_selected_entry(self):
        """Copy selected log entry to clipboard."""
        current_row = self.table_widget.currentRow()

        if current_row >= 0 and current_row < len(self.filtered_entries):
            entry = self.filtered_entries[current_row]

            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(
                entry.raw_line
                or f"{entry.timestamp} {entry.level} {entry.logger} - {entry.message}"
            )

    def _copy_entry_message(self):
        """Copy selected entry message to clipboard."""
        current_row = self.table_widget.currentRow()

        if current_row >= 0 and current_row < len(self.filtered_entries):
            entry = self.filtered_entries[current_row]

            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(entry.message)

    def _filter_by_selected_logger(self):
        """Filter by selected entry's logger."""
        current_row = self.table_widget.currentRow()

        if current_row >= 0 and current_row < len(self.filtered_entries):
            entry = self.filtered_entries[current_row]
            self.logger_filter_input.setText(entry.logger)

    def _find_similar_entries(self):
        """Find entries similar to selected one."""
        current_row = self.table_widget.currentRow()

        if current_row >= 0 and current_row < len(self.filtered_entries):
            entry = self.filtered_entries[current_row]

            # Use first 50 characters of message as search term
            search_term = entry.message[:50]
            self.search_input.setText(search_term)

    # Worker thread event handlers
    @pyqtSlot(str, int)
    def _update_loading_progress(self, message: str, progress: int):
        """Update loading progress."""
        self.status_label.setText(message)
        self.loading_progress.setValue(progress)

    @pyqtSlot(list)
    def _on_logs_loaded(self, entries: List[LogEntry]):
        """Handle logs loaded from worker."""
        self.log_entries = entries
        self._apply_filters()

        self.loading_progress.setVisible(False)
        self.status_label.setText("Ready")

        self.logger.info(f"Loaded {len(entries)} log entries")

    # Utility methods
    def _load_file_incremental(self, file_path: str):
        """Load new entries from file (incremental)."""
        # This would implement incremental loading of new log entries
        # For now, just trigger a full reload
        self.reload_logs()

    def _parse_log_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line into LogEntry."""
        # Common log patterns
        patterns = [
            # Standard format: 2023-12-01 10:30:45,123 INFO logger_name - message
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,\.]\d+)\s+(\w+)\s+([^\s]+)\s*-\s*(.*)",
            # Alternative format: [2023-12-01 10:30:45] INFO [logger_name] message
            r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\w+)\s+\[([^\]]+)\]\s*(.*)",
            # Simple format: INFO:logger_name:message
            r"(\w+):([^:]+):(.*)",
        ]

        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()

                if len(groups) == 4:
                    timestamp, level, logger, message = groups
                elif len(groups) == 3:
                    # Simple format
                    level, logger, message = groups
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,000")
                else:
                    continue

                return LogEntry(
                    timestamp=timestamp,
                    level=level.upper(),
                    logger=logger,
                    message=message,
                    line_number=line_number,
                    raw_line=line,
                )

        # If no pattern matches, create a generic entry
        return LogEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S,000"),
            level="INFO",
            logger="unknown",
            message=line.strip(),
            line_number=line_number,
            raw_line=line,
        )

    def _export_logs_with_config(self, config: Dict[str, Any]):
        """Export logs with given configuration."""
        file_path = config["file_path"]
        format_type = config["format"]
        entries = config["entries"]

        try:
            if format_type == "JSON":
                self._export_to_json(file_path, entries)
            elif format_type == "CSV":
                self._export_to_csv(file_path, entries)
            elif format_type == "TXT":
                self._export_to_txt(file_path, entries)

            QMessageBox.information(
                self, "Export Complete", f"Logs exported to:\n{file_path}"
            )
            self.export_requested.emit(format_type, entries)

        except Exception as e:
            QMessageBox.critical(
                self, "Export Failed", f"Failed to export logs:\n{str(e)}"
            )
            self.logger.error(f"Log export failed: {e}")

    def _export_to_json(self, file_path: str, entries: List[LogEntry]):
        """Export entries to JSON format."""
        import json

        data = []
        for entry in entries:
            data.append(
                {
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "logger": entry.logger,
                    "message": entry.message,
                    "line_number": entry.line_number,
                }
            )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _export_to_csv(self, file_path: str, entries: List[LogEntry]):
        """Export entries to CSV format."""
        import csv

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Level", "Logger", "Message", "Line"])

            for entry in entries:
                writer.writerow(
                    [
                        entry.timestamp,
                        entry.level,
                        entry.logger,
                        entry.message,
                        entry.line_number,
                    ]
                )

    def _export_to_txt(self, file_path: str, entries: List[LogEntry]):
        """Export entries to text format."""
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(
                    entry.raw_line
                    or f"{entry.timestamp} {entry.level} {entry.logger} - {entry.message}"
                )
                f.write("\n")

    def _apply_settings(self, settings: Dict[str, Any]):
        """Apply log viewer settings."""
        self.max_entries = settings.get("max_entries", 10000)
        self.refresh_interval = settings.get("refresh_interval", 1000)

        # Update timer
        if self.refresh_timer.isActive():
            self.refresh_timer.setInterval(self.refresh_interval)


class LogLoadWorker(QThread):
    """Worker thread for loading log files."""

    progress = pyqtSignal(str, int)
    finished = pyqtSignal(list)

    def __init__(self, file_paths: List[str]):
        super().__init__()
        self.file_paths = file_paths
        self.logger = get_logger(self.__class__.__name__)

    def run(self):
        """Load log files in background thread."""
        all_entries = []
        total_files = len(self.file_paths)

        for i, file_path in enumerate(self.file_paths):
            self.progress.emit(
                f"Loading {os.path.basename(file_path)}...", int(i / total_files * 100)
            )

            try:
                if os.path.exists(file_path):
                    entries = self._load_file(file_path)
                    all_entries.extend(entries)
            except Exception as e:
                self.logger.error(f"Failed to load {file_path}: {e}")

        # Sort by timestamp
        all_entries.sort(key=lambda x: x.datetime or datetime.min)

        self.finished.emit(all_entries)

    def _load_file(self, file_path: str) -> List[LogEntry]:
        """Load entries from a single file."""
        entries = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        entry = self._parse_log_line(line, line_num)
                        if entry:
                            entries.append(entry)
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")

        return entries

    def _parse_log_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line into LogEntry."""
        # Same parsing logic as in main widget
        patterns = [
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,\.]\d+)\s+(\w+)\s+([^\s]+)\s*-\s*(.*)",
            r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\w+)\s+\[([^\]]+)\]\s*(.*)",
            r"(\w+):([^:]+):(.*)",
        ]

        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()

                if len(groups) == 4:
                    timestamp, level, logger, message = groups
                elif len(groups) == 3:
                    level, logger, message = groups
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,000")
                else:
                    continue

                return LogEntry  # type: ignore
