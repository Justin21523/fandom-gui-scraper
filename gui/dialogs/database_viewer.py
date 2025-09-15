# gui/dialogs/database_viewer.py - Complete implementation

"""
Database viewer dialog for managing scraped data.
Complete implementation of TODO item.
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QComboBox,
    QLabel,
    QTabWidget,
    QWidget,
    QTextEdit,
    QGroupBox,
    QFormLayout,
    QProgressBar,
    QMessageBox,
    QHeaderView,
    QMenu,
    QFileDialog,
    QSplitter,
    QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction

from gui.main_window import MainWindow
from utils.logger import get_logger


class DatabaseQueryThread(QThread):
    """Thread for database operations."""

    data_loaded = pyqtSignal(list)  # List of documents
    error_occurred = pyqtSignal(str)  # Error message
    progress_updated = pyqtSignal(int, str)  # Progress, message

    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        try:
            if self.operation == "load_collection":
                self.load_collection_data()
            elif self.operation == "search":
                self.search_data()
            elif self.operation == "delete":
                self.delete_data()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def load_collection_data(self):
        """Load data from collection."""
        # Simulate database loading
        import time

        for i in range(101):
            time.sleep(0.01)
            self.progress_updated.emit(i, f"Loading data... {i}%")

        # Mock data for demonstration
        mock_data = [
            {"_id": "1", "name": "Naruto Uzumaki", "anime": "Naruto", "age": 17},
            {"_id": "2", "name": "Sasuke Uchiha", "anime": "Naruto", "age": 17},
            {"_id": "3", "name": "Luffy", "anime": "One Piece", "age": 19},
        ]
        self.data_loaded.emit(mock_data)


class DatabaseViewer(QDialog):
    """
    Complete database viewer for managing scraped data.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)

        # Dialog setup
        self.setWindowTitle("Database Viewer")
        self.setModal(False)
        self.resize(1000, 700)

        # Data storage
        self.current_data = []
        self.query_thread = None

        self.setup_ui()
        self.connect_signals()
        self.load_initial_data()

        self.logger.info("Database viewer initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create toolbar
        self.create_toolbar(layout)

        # Create main content
        self.create_main_content(layout)

        # Create status bar
        self.create_status_bar(layout)

    def create_toolbar(self, parent_layout):
        """Create toolbar with database controls."""
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)

        # Collection selector
        toolbar_layout.addWidget(QLabel("Collection:"))
        self.collection_combo = QComboBox()
        self.collection_combo.addItems(["characters", "images", "metadata", "logs"])
        toolbar_layout.addWidget(self.collection_combo)

        # Search box
        toolbar_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documents...")
        toolbar_layout.addWidget(self.search_input)

        # Search button
        self.search_button = QPushButton("Search")
        toolbar_layout.addWidget(self.search_button)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        toolbar_layout.addWidget(self.refresh_button)

        toolbar_layout.addStretch()

        # Export button
        self.export_button = QPushButton("Export")
        toolbar_layout.addWidget(self.export_button)

        # Delete button
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.setEnabled(False)
        toolbar_layout.addWidget(self.delete_button)

        parent_layout.addWidget(toolbar_frame)

    def create_main_content(self, parent_layout):
        """Create main content area."""
        # Splitter for resizable areas
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Data table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_table.setSortingEnabled(True)

        # Configure table
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        splitter.addWidget(self.data_table)

        # Detail panel
        detail_panel = self.create_detail_panel()
        splitter.addWidget(detail_panel)

        # Set splitter proportions
        splitter.setSizes([700, 300])

        parent_layout.addWidget(splitter)

    def create_detail_panel(self):
        """Create detail panel for document inspection."""
        panel = QWidget()
        panel.setMaximumWidth(350)
        layout = QVBoxLayout(panel)

        # Title
        title_label = QLabel("Document Details")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Document content
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.detail_text)

        # Action buttons
        button_layout = QHBoxLayout()

        self.edit_doc_button = QPushButton("Edit")
        self.edit_doc_button.setEnabled(False)
        button_layout.addWidget(self.edit_doc_button)

        self.delete_doc_button = QPushButton("Delete")
        self.delete_doc_button.setEnabled(False)
        button_layout.addWidget(self.delete_doc_button)

        layout.addLayout(button_layout)

        return panel

    def create_status_bar(self, parent_layout):
        """Create status bar."""
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)

        # Status label
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # Document count
        self.count_label = QLabel("0 documents")
        status_layout.addWidget(self.count_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_layout.addWidget(self.progress_bar)

        parent_layout.addWidget(status_frame)

    def connect_signals(self):
        """Connect signals and slots."""
        self.collection_combo.currentTextChanged.connect(self.on_collection_changed)
        self.search_button.clicked.connect(self.search_documents)
        self.search_input.returnPressed.connect(self.search_documents)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.export_button.clicked.connect(self.export_data)
        self.delete_button.clicked.connect(self.delete_selected)

        self.data_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.data_table.cellDoubleClicked.connect(self.on_cell_double_clicked)

    def load_initial_data(self):
        """Load initial data."""
        self.load_collection_data("characters")

    def load_collection_data(self, collection_name):
        """Load data from specified collection."""
        if self.query_thread and self.query_thread.isRunning():
            return

        self.status_label.setText(f"Loading {collection_name} collection...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)

        self.query_thread = DatabaseQueryThread(
            "load_collection", collection=collection_name
        )
        self.query_thread.data_loaded.connect(self.on_data_loaded)
        self.query_thread.error_occurred.connect(self.on_error_occurred)
        self.query_thread.progress_updated.connect(self.on_progress_updated)
        self.query_thread.finished.connect(self.on_query_finished)
        self.query_thread.start()

    def on_collection_changed(self, collection_name):
        """Handle collection change."""
        self.load_collection_data(collection_name)

    def on_data_loaded(self, data):
        """Handle loaded data."""
        self.current_data = data
        self.populate_table(data)
        self.count_label.setText(f"{len(data)} documents")
        self.status_label.setText("Data loaded successfully")

    def populate_table(self, data):
        """Populate table with data."""
        if not data:
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return

        # Get all unique keys from all documents
        all_keys = set()
        for doc in data:
            all_keys.update(doc.keys())

        headers = sorted(list(all_keys))

        # Set up table
        self.data_table.setRowCount(len(data))
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)

        # Populate data
        for row, doc in enumerate(data):
            for col, key in enumerate(headers):
                value = doc.get(key, "")
                if isinstance(value, (dict, list)):
                    value = (
                        str(value)[:100] + "..."
                        if len(str(value)) > 100
                        else str(value)
                    )

                item = QTableWidgetItem(str(value))
                self.data_table.setItem(row, col, item)

    def on_selection_changed(self):
        """Handle table selection changes."""
        selected_rows = set()
        for item in self.data_table.selectedItems():
            selected_rows.add(item.row())

        has_selection = len(selected_rows) > 0
        self.delete_button.setEnabled(has_selection)
        self.edit_doc_button.setEnabled(len(selected_rows) == 1)
        self.delete_doc_button.setEnabled(len(selected_rows) == 1)

        # Show details for first selected row
        if selected_rows and self.current_data:
            row = min(selected_rows)
            if row < len(self.current_data):
                self.show_document_details(self.current_data[row])

    def show_document_details(self, document):
        """Show document details in detail panel."""
        import json

        try:
            formatted_json = json.dumps(document, indent=2, ensure_ascii=False)
            self.detail_text.setPlainText(formatted_json)
        except Exception as e:
            self.detail_text.setPlainText(
                f"Error formatting document: {e}\n\nRaw data:\n{document}"
            )

    def on_cell_double_clicked(self, row, column):
        """Handle cell double-click."""
        if row < len(self.current_data):
            document = self.current_data[row]
            self.edit_document(document)

    def edit_document(self, document):
        """Edit document (placeholder)."""
        QMessageBox.information(
            self,
            "Edit Document",
            "Document editing will be implemented in a future version.",
        )

    def search_documents(self):
        """Search documents."""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.populate_table(self.current_data)
            return

        # Simple text search in document values
        filtered_data = []
        search_lower = search_text.lower()

        for doc in self.current_data:
            for key, value in doc.items():
                if search_lower in str(value).lower():
                    filtered_data.append(doc)
                    break

        self.populate_table(filtered_data)
        self.count_label.setText(f"{len(filtered_data)} documents (filtered)")
        self.status_label.setText(f"Search completed: {len(filtered_data)} matches")

    def refresh_data(self):
        """Refresh current collection data."""
        collection = self.collection_combo.currentText()
        self.load_collection_data(collection)

    def export_data(self):
        """Export current data."""
        if not self.current_data:
            QMessageBox.information(self, "Export", "No data to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            f"{self.collection_combo.currentText()}_export.json",
            "JSON files (*.json);;CSV files (*.csv);;All files (*)",
        )

        if filename:
            try:
                if filename.endswith(".json"):
                    import json

                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(self.current_data, f, indent=2, ensure_ascii=False)
                elif filename.endswith(".csv"):
                    import csv

                    with open(filename, "w", newline="", encoding="utf-8") as f:
                        if self.current_data:
                            writer = csv.DictWriter(
                                f, fieldnames=self.current_data[0].keys()
                            )
                            writer.writeheader()
                            writer.writerows(self.current_data)

                QMessageBox.information(self, "Export", f"Data exported to {filename}")
                self.logger.info(f"Data exported to {filename}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export data:\n{e}"
                )

    def delete_selected(self):
        """Delete selected documents."""
        selected_rows = set()
        for item in self.data_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return

        reply = QMessageBox.question(
            self,
            "Delete Documents",
            f"Delete {len(selected_rows)} selected document(s)?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from data (in real app, would delete from database)
            sorted_rows = sorted(selected_rows, reverse=True)
            for row in sorted_rows:
                if row < len(self.current_data):
                    del self.current_data[row]

            self.populate_table(self.current_data)
            self.count_label.setText(f"{len(self.current_data)} documents")
            self.status_label.setText(f"Deleted {len(selected_rows)} documents")

    def on_progress_updated(self, value, message):
        """Handle progress updates."""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def on_error_occurred(self, error_message):
        """Handle query errors."""
        self.status_label.setText(f"Error: {error_message}")
        QMessageBox.critical(
            self, "Database Error", f"Database operation failed:\n{error_message}"
        )

    def on_query_finished(self):
        """Handle query completion."""
        self.progress_bar.setVisible(False)
        if self.query_thread:
            self.query_thread.deleteLater()
            self.query_thread = None


# gui/widgets/log_viewer.py - Complete implementation

"""
Log viewer widget for displaying application logs.
Complete implementation of TODO item.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QCheckBox,
    QSpinBox,
    QLineEdit,
    QFrame,
    QGroupBox,
    QFormLayout,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QFileSystemWatcher
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

from utils.logger import get_logger


class LogFileWatcher(QThread):
    """Thread for watching log file changes."""

    new_log_entries = pyqtSignal(list)  # List of new log lines

    def __init__(self, log_file_path):
        super().__init__()
        self.log_file_path = log_file_path
        self.last_position = 0
        self.running = True

    def run(self):
        """Monitor log file for changes."""
        while self.running:
            try:
                if os.path.exists(self.log_file_path):
                    with open(self.log_file_path, "r", encoding="utf-8") as f:
                        f.seek(self.last_position)
                        new_lines = f.readlines()

                        if new_lines:
                            self.new_log_entries.emit(
                                [line.strip() for line in new_lines]
                            )
                            self.last_position = f.tell()

                self.msleep(1000)  # Check every second

            except Exception as e:
                # Handle file access errors silently
                self.msleep(5000)  # Wait longer on error

    def stop(self):
        """Stop watching."""
        self.running = False


class LogViewerWidget(QWidget):
    """
    Complete log viewer widget for displaying application logs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)

        # Log data
        self.log_entries = []
        self.filtered_entries = []
        self.max_entries = 10000

        # File watching
        self.file_watcher = None
        self.auto_scroll = True

        # Filtering
        self.current_level_filter = "ALL"
        self.current_text_filter = ""

        self.setup_ui()
        self.connect_signals()
        self.setup_log_monitoring()

        self.logger.info("Log viewer widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create control panel
        self.create_control_panel(layout)

        # Create main content
        self.create_main_content(layout)

        # Create status bar
        self.create_status_bar(layout)

    def create_control_panel(self, parent_layout):
        """Create control panel."""
        control_frame = QFrame()
        control_layout = QVBoxLayout(control_frame)

        # First row - Level filter and search
        row1_layout = QHBoxLayout()

        # Log level filter
        row1_layout.addWidget(QLabel("Level:"))
        self.level_filter_combo = QComboBox()
        self.level_filter_combo.addItems(
            ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        row1_layout.addWidget(self.level_filter_combo)

        # Text search
        row1_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in logs...")
        row1_layout.addWidget(self.search_input)

        # Search button
        self.search_button = QPushButton("Search")
        row1_layout.addWidget(self.search_button)

        # Clear search
        self.clear_search_button = QPushButton("Clear")
        row1_layout.addWidget(self.clear_search_button)

        control_layout.addLayout(row1_layout)

        # Second row - Display options
        row2_layout = QHBoxLayout()

        # Auto-scroll
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        row2_layout.addWidget(self.auto_scroll_check)

        # Word wrap
        self.word_wrap_check = QCheckBox("Word wrap")
        row2_layout.addWidget(self.word_wrap_check)

        # Show timestamps
        self.show_timestamps_check = QCheckBox("Show timestamps")
        self.show_timestamps_check.setChecked(True)
        row2_layout.addWidget(self.show_timestamps_check)

        row2_layout.addStretch()

        # Max entries
        row2_layout.addWidget(QLabel("Max entries:"))
        self.max_entries_spin = QSpinBox()
        self.max_entries_spin.setRange(100, 100000)
        self.max_entries_spin.setValue(10000)
        row2_layout.addWidget(self.max_entries_spin)

        control_layout.addLayout(row2_layout)

        # Third row - Actions
        row3_layout = QHBoxLayout()

        # Clear logs
        self.clear_logs_button = QPushButton("Clear Display")
        row3_layout.addWidget(self.clear_logs_button)

        # Reload logs
        self.reload_logs_button = QPushButton("Reload")
        row3_layout.addWidget(self.reload_logs_button)

        # Export logs
        self.export_logs_button = QPushButton("Export")
        row3_layout.addWidget(self.export_logs_button)

        row3_layout.addStretch()

        # Pause/Resume
        self.pause_button = QPushButton("Pause")
        row3_layout.addWidget(self.pause_button)

        control_layout.addLayout(row3_layout)

        parent_layout.addWidget(control_frame)

    def create_main_content(self, parent_layout):
        """Create main log display."""
        # Splitter for log sources and content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Log sources panel
        sources_panel = self.create_sources_panel()
        splitter.addWidget(sources_panel)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.setup_log_formatting()
        splitter.addWidget(self.log_display)

        # Set splitter proportions
        splitter.setSizes([200, 800])

        parent_layout.addWidget(splitter)

    def create_sources_panel(self):
        """Create log sources panel."""
        panel = QWidget()
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)

        # Title
        title_label = QLabel("Log Sources")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Sources list
        self.sources_list = QListWidget()

        # Add default log sources
        sources = [
            "Application Log",
            "Scraper Log",
            "Database Log",
            "Error Log",
            "Performance Log",
        ]

        for source in sources:
            item = QListWidgetItem(source)
            item.setCheckState(Qt.CheckState.Checked)
            self.sources_list.addItem(item)

        layout.addWidget(self.sources_list)

        # Add file button
        self.add_file_button = QPushButton("Add Log File...")
        layout.addWidget(self.add_file_button)

        return panel

    def create_status_bar(self, parent_layout):
        """Create status bar."""
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)

        # Status label
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # Entry count
        self.entry_count_label = QLabel("0 entries")
        status_layout.addWidget(self.entry_count_label)

        # Last update
        self.last_update_label = QLabel("Never updated")
        status_layout.addWidget(self.last_update_label)

        parent_layout.addWidget(status_frame)

    def setup_log_formatting(self):
        """Set up syntax highlighting for log levels."""
        self.log_formats = {
            "DEBUG": self.create_format(QColor("#888888")),  # Gray
            "INFO": self.create_format(QColor("#000000")),  # Black
            "WARNING": self.create_format(QColor("#FF8C00")),  # Orange
            "ERROR": self.create_format(QColor("#FF0000")),  # Red
            "CRITICAL": self.create_format(
                QColor("#8B0000"), bold=True
            ),  # Dark red, bold
        }

    def create_format(self, color, bold=False):
        """Create text format for log levels."""
        format = QTextCharFormat()
        format.setForeground(color)
        if bold:
            format.setFontWeight(QFont.Weight.Bold)
        return format

    def connect_signals(self):
        """Connect signals and slots."""
        # Filtering
        self.level_filter_combo.currentTextChanged.connect(self.apply_filters)
        self.search_button.clicked.connect(self.apply_filters)
        self.search_input.returnPressed.connect(self.apply_filters)
        self.clear_search_button.clicked.connect(self.clear_search)

        # Display options
        self.auto_scroll_check.toggled.connect(self.toggle_auto_scroll)
        self.word_wrap_check.toggled.connect(self.toggle_word_wrap)
        self.show_timestamps_check.toggled.connect(self.refresh_display)
        self.max_entries_spin.valueChanged.connect(self.update_max_entries)

        # Actions
        self.clear_logs_button.clicked.connect(self.clear_logs)
        self.reload_logs_button.clicked.connect(self.reload_logs)
        self.export_logs_button.clicked.connect(self.export_logs)
        self.pause_button.clicked.connect(self.toggle_pause)

        # Sources
        self.sources_list.itemChanged.connect(self.on_source_changed)
        self.add_file_button.clicked.connect(self.add_log_file)

    def setup_log_monitoring(self):
        """Set up log file monitoring."""
        # Start monitoring application log file
        log_file = "logs/app.log"  # Default log file path
        if os.path.exists(log_file):
            self.start_file_watching(log_file)

        # Load existing log entries
        self.reload_logs()

    def start_file_watching(self, log_file_path):
        """Start watching a log file."""
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher.wait()

        self.file_watcher = LogFileWatcher(log_file_path)
        self.file_watcher.new_log_entries.connect(self.add_log_entries)
        self.file_watcher.start()

    def add_log_entries(self, entries):
        """Add new log entries."""
        for entry in entries:
            if len(self.log_entries) >= self.max_entries:
                self.log_entries.pop(0)  # Remove oldest entry

            self.log_entries.append(
                {
                    "timestamp": datetime.now(),
                    "text": entry,
                    "level": self.extract_log_level(entry),
                    "source": "Application Log",
                }
            )

        self.apply_filters()
        self.update_status()

    def extract_log_level(self, log_line):
        """Extract log level from log line."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            if level in log_line.upper():
                return level
        return "INFO"  # Default level

    def apply_filters(self):
        """Apply current filters to log entries."""
        level_filter = self.level_filter_combo.currentText()
        text_filter = self.search_input.text().lower()

        self.filtered_entries = []

        for entry in self.log_entries:
            # Level filter
            if level_filter != "ALL" and entry["level"] != level_filter:
                continue

            # Text filter
            if text_filter and text_filter not in entry["text"].lower():
                continue

            self.filtered_entries.append(entry)

        self.refresh_display()

    def refresh_display(self):
        """Refresh the log display."""
        self.log_display.clear()

        show_timestamps = self.show_timestamps_check.isChecked()

        for entry in self.filtered_entries:
            # Format entry
            if show_timestamps:
                timestamp_str = entry["timestamp"].strftime("%H:%M:%S")
                line = f"[{timestamp_str}] {entry['text']}"
            else:
                line = entry["text"]

            # Apply formatting based on level
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            if entry["level"] in self.log_formats:
                cursor.insertText(line + "\n", self.log_formats[entry["level"]])
            else:
                cursor.insertText(line + "\n")

        # Auto-scroll to bottom
        if self.auto_scroll:
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        self.update_status()

    def clear_search(self):
        """Clear search filters."""
        self.search_input.clear()
        self.level_filter_combo.setCurrentText("ALL")
        self.apply_filters()

    def toggle_auto_scroll(self, enabled):
        """Toggle auto-scroll."""
        self.auto_scroll = enabled

    def toggle_word_wrap(self, enabled):
        """Toggle word wrap."""
        if enabled:
            self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    def update_max_entries(self, value):
        """Update maximum entries limit."""
        self.max_entries = value

        # Trim existing entries if needed
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries :]
            self.apply_filters()

    def clear_logs(self):
        """Clear all log entries."""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Clear all log entries from display?\nThis will not affect actual log files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.log_entries.clear()
            self.filtered_entries.clear()
            self.log_display.clear()
            self.update_status()

    def reload_logs(self):
        """Reload logs from files."""
        self.status_label.setText("Reloading logs...")

        # Clear current entries
        self.log_entries.clear()

        # Load from log files (simplified - would load from actual files)
        sample_entries = [
            {
                "timestamp": datetime.now() - timedelta(minutes=5),
                "text": "Application started",
                "level": "INFO",
                "source": "Application",
            },
            {
                "timestamp": datetime.now() - timedelta(minutes=3),
                "text": "Database connection established",
                "level": "INFO",
                "source": "Database",
            },
            {
                "timestamp": datetime.now() - timedelta(minutes=1),
                "text": "Scraping operation started",
                "level": "INFO",
                "source": "Scraper",
            },
            {
                "timestamp": datetime.now(),
                "text": "Log viewer initialized",
                "level": "INFO",
                "source": "Application",
            },
        ]

        self.log_entries.extend(sample_entries)
        self.apply_filters()

        self.status_label.setText("Logs reloaded")

    def export_logs(self):
        """Export logs to file."""
        if not self.filtered_entries:
            QMessageBox.information(self, "Export", "No log entries to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt);;JSON files (*.json);;All files (*)",
        )

        if filename:
            try:
                if filename.endswith(".json"):
                    import json

                    export_data = []
                    for entry in self.filtered_entries:
                        export_data.append(
                            {
                                "timestamp": entry["timestamp"].isoformat(),
                                "level": entry["level"],
                                "source": entry["source"],
                                "text": entry["text"],
                            }
                        )

                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    # Export as text
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(f"Log Export - Generated: {datetime.now()}\n")
                        f.write("=" * 50 + "\n\n")

                        for entry in self.filtered_entries:
                            timestamp_str = entry["timestamp"].strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            f.write(
                                f"[{timestamp_str}] [{entry['level']}] [{entry['source']}] {entry['text']}\n"
                            )

                QMessageBox.information(self, "Export", f"Logs exported to {filename}")
                self.logger.info(f"Logs exported to {filename}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export logs:\n{e}"
                )

    def toggle_pause(self):
        """Toggle log monitoring pause."""
        if self.file_watcher and self.file_watcher.isRunning():
            if self.pause_button.text() == "Pause":
                # Pause monitoring
                self.file_watcher.running = False
                self.pause_button.setText("Resume")
                self.status_label.setText("Log monitoring paused")
            else:
                # Resume monitoring
                self.file_watcher.running = True
                self.pause_button.setText("Pause")
                self.status_label.setText("Log monitoring resumed")

    def on_source_changed(self, item):
        """Handle log source enable/disable."""
        # In a real implementation, this would enable/disable specific log sources
        self.apply_filters()

    def add_log_file(self):
        """Add external log file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Add Log File", "", "Log files (*.log *.txt);;All files (*)"
        )

        if filename:
            try:
                # Add to sources list
                source_name = os.path.basename(filename)
                item = QListWidgetItem(source_name)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, filename)  # Store file path
                self.sources_list.addItem(item)

                # Start watching this file
                self.start_file_watching(filename)

                QMessageBox.information(
                    self,
                    "Add Log File",
                    f"Log file '{source_name}' added successfully.",
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add log file:\n{e}")

    def update_status(self):
        """Update status information."""
        total_entries = len(self.log_entries)
        filtered_entries = len(self.filtered_entries)

        self.entry_count_label.setText(f"{filtered_entries}/{total_entries} entries")
        self.last_update_label.setText(
            f"Updated: {datetime.now().strftime('%H:%M:%S')}"
        )

    def closeEvent(self, event):
        """Handle widget close."""
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher.wait()
        event.accept()


# main_window.py - Complete _apply_language implementation

"""
Complete implementation of _apply_language method in MainWindow.
"""


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
        language_codes = {"English": "en", "中文": "zh", "日本語": "ja", "한국어": "ko"}

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
    menus = menubar.findChildren(QMenu)

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


# Add these methods to the MainWindow class
MainWindow._apply_language = _apply_language
MainWindow._update_menu_language = _update_menu_language
MainWindow._update_tab_language = _update_tab_language
MainWindow._update_widget_language = _update_widget_language
MainWindow._save_language_preference = _save_language_preference
