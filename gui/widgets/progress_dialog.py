# gui/widgets/progress_dialog.py
"""
Progress dialog widget for displaying scraping progress and status.

This module provides a comprehensive progress dialog that shows real-time
scraping progress, status messages, and allows user control over operations.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QFrame,
    QSizePolicy,
    QScrollArea,
    QWidget,
    QGroupBox,
    QGridLayout,
    QSpacerItem,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
)
from PyQt6.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot, Qt, QMutex, QMutexLocker
from PyQt6.QtGui import QFont, QPixmap, QMovie, QPalette, QColor

from utils.logger import get_logger


class ProgressDialog(QDialog):
    """
    Enhanced progress dialog for scraping operations.

    Features:
    - Real-time progress tracking with multiple progress bars
    - Detailed status messages with timestamps
    - Statistics display (items scraped, success rate, etc.)
    - Cancel/pause functionality
    - Estimated time remaining calculations
    - Error reporting and handling
    """

    # Signals for external communication
    cancel_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    details_requested = pyqtSignal(str)  # Request details for specific item

    def __init__(self, parent=None, title="Scraping Progress", modal=True):
        """
        Initialize the progress dialog.

        Args:
            parent: Parent widget
            title: Dialog window title
            modal: Whether dialog should be modal
        """
        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(self.__class__.__name__)

        # Dialog configuration
        self.setWindowTitle(title)
        self.setModal(modal)
        self.setMinimumSize(600, 500)
        self.resize(800, 600)

        # Progress tracking state
        self.start_time = None
        self.is_paused = False
        self.is_cancelled = False
        self.total_items = 0
        self.completed_items = 0
        self.failed_items = 0
        self.skipped_items = 0

        # Statistics tracking
        self.statistics = {
            "characters_scraped": 0,
            "images_downloaded": 0,
            "pages_processed": 0,
            "data_validated": 0,
            "errors_encountered": 0,
            "duplicate_items": 0,
            "processing_rate": 0.0,  # items per second
            "success_rate": 0.0,  # percentage
            "average_response_time": 0.0,  # seconds
        }

        # Thread safety
        self.mutex = QMutex()

        # Timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second

        # Set up UI
        self.setup_ui()
        self.setup_style()

        self.logger.info("Progress dialog initialized")

    def setup_ui(self):
        """Set up the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Header section
        header_frame = self.create_header_section()
        main_layout.addWidget(header_frame)

        # Progress section
        progress_frame = self.create_progress_section()
        main_layout.addWidget(progress_frame)

        # Statistics section
        stats_frame = self.create_statistics_section()
        main_layout.addWidget(stats_frame)

        # Status log section
        log_frame = self.create_log_section()
        main_layout.addWidget(log_frame)

        # Control buttons section
        controls_frame = self.create_controls_section()
        main_layout.addWidget(controls_frame)

    def create_header_section(self) -> QFrame:
        """
        Create the header section with operation info.

        Returns:
            Frame containing header elements
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)

        # Operation title
        self.operation_label = QLabel("Preparing to scrape...")
        self.operation_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.operation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.operation_label)

        # Target information
        self.target_label = QLabel("Target: Not specified")
        self.target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.target_label)

        # Time information
        time_layout = QHBoxLayout()

        self.start_time_label = QLabel("Start: --:--:--")
        time_layout.addWidget(self.start_time_label)

        time_layout.addStretch()

        self.elapsed_time_label = QLabel("Elapsed: 00:00:00")
        time_layout.addWidget(self.elapsed_time_label)

        time_layout.addStretch()

        self.eta_label = QLabel("ETA: --:--:--")
        time_layout.addWidget(self.eta_label)

        layout.addLayout(time_layout)

        return frame

    def create_progress_section(self) -> QFrame:
        """
        Create the progress section with multiple progress bars.

        Returns:
            Frame containing progress elements
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)

        # 主要進度條
        main_progress_layout = QVBoxLayout()

        self.main_progress_label = QLabel("Overall Progress")
        self.main_progress_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        main_progress_layout.addWidget(self.main_progress_label)

        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setRange(0, 100)
        self.main_progress_bar.setValue(0)
        self.main_progress_bar.setTextVisible(True)
        main_progress_layout.addWidget(self.main_progress_bar)

        layout.addLayout(main_progress_layout)

        # 詳細進度條
        details_group = QGroupBox("Detailed Progress")
        details_layout = QGridLayout(details_group)

        # 字符爬取進度
        details_layout.addWidget(QLabel("Characters:"), 0, 0)
        self.characters_progress = QProgressBar()
        self.characters_progress.setRange(0, 100)
        self.characters_progress_label = QLabel("0/0")
        details_layout.addWidget(self.characters_progress, 0, 1)
        details_layout.addWidget(self.characters_progress_label, 0, 2)

        # 圖片下載進度
        details_layout.addWidget(QLabel("Images:"), 1, 0)
        self.images_progress = QProgressBar()
        self.images_progress.setRange(0, 100)
        self.images_progress_label = QLabel("0/0")
        details_layout.addWidget(self.images_progress, 1, 1)
        details_layout.addWidget(self.images_progress_label, 1, 2)

        # 頁面處理進度
        details_layout.addWidget(QLabel("Pages:"), 2, 0)
        self.pages_progress = QProgressBar()
        self.pages_progress.setRange(0, 100)
        self.pages_progress_label = QLabel("0/0")
        details_layout.addWidget(self.pages_progress, 2, 1)
        details_layout.addWidget(self.pages_progress_label, 2, 2)

        layout.addWidget(details_group)

        return frame

    def create_statistics_section(self) -> QFrame:
        """
        Create the statistics section.

        Returns:
            Frame containing statistics display
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        stats_group = QGroupBox("Statistics")
        layout = QGridLayout(stats_group)

        # Create statistics labels
        self.stats_labels = {}

        # Row 0: Counts
        layout.addWidget(QLabel("Characters:"), 0, 0)
        self.stats_labels["characters"] = QLabel("0")
        self.stats_labels["characters"].setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.stats_labels["characters"], 0, 1)

        layout.addWidget(QLabel("Images:"), 0, 2)
        self.stats_labels["images"] = QLabel("0")
        self.stats_labels["images"].setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.stats_labels["images"], 0, 3)

        layout.addWidget(QLabel("Pages:"), 0, 4)
        self.stats_labels["pages"] = QLabel("0")
        self.stats_labels["pages"].setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.stats_labels["pages"], 0, 5)

        # Row 1: Rates and percentages
        layout.addWidget(QLabel("Success Rate:"), 1, 0)
        self.stats_labels["success_rate"] = QLabel("0%")
        self.stats_labels["success_rate"].setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.stats_labels["success_rate"], 1, 1)

        layout.addWidget(QLabel("Processing Rate:"), 1, 2)
        self.stats_labels["processing_rate"] = QLabel("0/s")
        self.stats_labels["processing_rate"].setFont(
            QFont("Arial", 10, QFont.Weight.Bold)
        )
        layout.addWidget(self.stats_labels["processing_rate"], 1, 3)

        layout.addWidget(QLabel("Errors:"), 1, 4)
        self.stats_labels["errors"] = QLabel("0")
        self.stats_labels["errors"].setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.stats_labels["errors"], 1, 5)

        # Row 2: Response time and duplicates
        layout.addWidget(QLabel("Avg Response:"), 2, 0)
        self.stats_labels["response_time"] = QLabel("0ms")
        self.stats_labels["response_time"].setFont(
            QFont("Arial", 10, QFont.Weight.Bold)
        )
        layout.addWidget(self.stats_labels["response_time"], 2, 1)

        layout.addWidget(QLabel("Duplicates:"), 2, 2)
        self.stats_labels["duplicates"] = QLabel("0")
        self.stats_labels["duplicates"].setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.stats_labels["duplicates"], 2, 3)

        # Add frame layout
        frame_layout = QVBoxLayout(frame)
        frame_layout.addWidget(stats_group)

        return frame

    def create_log_section(self) -> QFrame:
        """
        Create the status log section.

        Returns:
            Frame containing log display
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        log_group = QGroupBox("Status Log")
        layout = QVBoxLayout(log_group)

        # Create log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))

        # Set up log formatting
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
        """
        )

        layout.addWidget(self.log_text)

        # Log controls
        log_controls = QHBoxLayout()

        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_controls.addWidget(self.clear_log_btn)

        self.auto_scroll_checkbox = QPushButton("Auto Scroll")
        self.auto_scroll_checkbox.setCheckable(True)
        self.auto_scroll_checkbox.setChecked(True)
        log_controls.addWidget(self.auto_scroll_checkbox)

        log_controls.addStretch()

        self.export_log_btn = QPushButton("Export Log")
        self.export_log_btn.clicked.connect(self.export_log)
        log_controls.addWidget(self.export_log_btn)

        layout.addLayout(log_controls)

        # Add frame layout
        frame_layout = QVBoxLayout(frame)
        frame_layout.addWidget(log_group)

        return frame

    def create_controls_section(self) -> QFrame:
        """
        Create the control buttons section.

        Returns:
            Frame containing control buttons
        """
        frame = QFrame()
        layout = QHBoxLayout(frame)

        # Pause/Resume button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        layout.addWidget(self.pause_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_operation)
        layout.addWidget(self.cancel_btn)

        layout.addStretch()

        # Details button
        self.details_btn = QPushButton("Show Details")
        self.details_btn.clicked.connect(self.show_details)
        layout.addWidget(self.details_btn)

        # Close button (initially hidden)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setVisible(False)
        layout.addWidget(self.close_btn)

        return frame

    def setup_style(self):
        """Set up the dialog styling."""
        style = """
        QDialog {
            background-color: #f8f9fa;
        }

        QFrame {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            margin: 2px;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #6c757d;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 5px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }

        QProgressBar {
            border: 1px solid #6c757d;
            border-radius: 3px;
            text-align: center;
            font-weight: bold;
        }

        QProgressBar::chunk {
            background-color: #28a745;
            border-radius: 3px;
        }

        QPushButton {
            background-color: #007bff;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            font-size: 14px;
            border-radius: 4px;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #0056b3;
        }

        QPushButton:pressed {
            background-color: #004085;
        }

        QPushButton:disabled {
            background-color: #6c757d;
            color: #adb5bd;
        }
        """
        self.setStyleSheet(style)

    # Public methods for external control
    def start_operation(self, operation_name: str, target: str, total_items: int = 0):
        """
        Start a new operation.

        Args:
            operation_name: Name of the operation
            target: Target being processed
            total_items: Total number of items to process
        """
        with QMutexLocker(self.mutex):
            self.start_time = datetime.now()
            self.is_paused = False
            self.is_cancelled = False
            self.total_items = total_items
            self.completed_items = 0
            self.failed_items = 0
            self.skipped_items = 0

            # Reset statistics
            for key in self.statistics:
                self.statistics[key] = 0

        # Update UI
        self.operation_label.setText(operation_name)
        self.target_label.setText(f"Target: {target}")
        self.start_time_label.setText(f"Start: {self.start_time.strftime('%H:%M:%S')}")

        if total_items > 0:
            self.overall_progress.setMaximum(total_items)
            self.overall_progress.setValue(0)
        else:
            self.overall_progress.setMaximum(0)  # Indeterminate progress

        self.pause_btn.setEnabled(True)
        self.close_btn.setVisible(False)

        self.add_log_message(f"Started: {operation_name}", "INFO")
        self.logger.info(f"Operation started: {operation_name}")

    def update_overall_progress(self, completed: int, total: int = None, message: str = ""):  # type: ignore
        """
        Update overall progress.

        Args:
            completed: Number of completed items
            total: Total number of items (optional)
            message: Status message
        """
        with QMutexLocker(self.mutex):
            self.completed_items = completed
            if total is not None:
                self.total_items = total

        if total is not None:
            self.overall_progress.setMaximum(total)
        self.overall_progress.setValue(completed)

        if message:
            self.overall_status.setText(message)

    def update_task_progress(self, progress: int, total: int = 100, message: str = ""):
        """
        Update current task progress.

        Args:
            progress: Current progress value
            total: Maximum progress value
            message: Task status message
        """
        self.task_progress.setMaximum(total)
        self.task_progress.setValue(progress)

        if message:
            self.task_status.setText(message)

    def update_subtask_progress(
        self, progress: int, total: int = 100, message: str = "", visible: bool = True
    ):
        """
        Update sub-task progress.

        Args:
            progress: Current progress value
            total: Maximum progress value
            message: Sub-task status message
            visible: Whether to show sub-task progress
        """
        self.subtask_progress.setVisible(visible)
        self.subtask_status.setVisible(visible)

        if visible:
            self.subtask_progress.setMaximum(total)
            self.subtask_progress.setValue(progress)

            if message:
                self.subtask_status.setText(message)

    def update_statistics(self, stats: Dict[str, Any]):
        """
        Update statistics display.

        Args:
            stats: Dictionary containing updated statistics
        """
        with QMutexLocker(self.mutex):
            self.statistics.update(stats)

    def add_log_message(self, message: str, level: str = "INFO"):
        """
        Add a message to the status log.

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR, DEBUG)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding for different log levels
        color_map = {
            "INFO": "#ffffff",
            "WARNING": "#ffc107",
            "ERROR": "#dc3545",
            "DEBUG": "#6c757d",
            "SUCCESS": "#28a745",
        }

        color = color_map.get(level, "#ffffff")
        formatted_message = (
            f'<span style="color: {color}">[{timestamp}] {level}: {message}</span>'
        )

        self.log_text.append(formatted_message)

        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())  # type: ignore

    def operation_completed(self, success: bool = True, message: str = ""):
        """
        Mark operation as completed.

        Args:
            success: Whether operation completed successfully
            message: Completion message
        """
        with QMutexLocker(self.mutex):
            self.is_paused = False

        self.pause_btn.setEnabled(False)
        self.close_btn.setVisible(True)

        if success:
            self.overall_status.setText("Completed successfully")
            self.add_log_message(
                message or "Operation completed successfully", "SUCCESS"
            )
        else:
            self.overall_status.setText("Completed with errors")
            self.add_log_message(
                message or "Operation completed with errors", "WARNING"
            )

        self.logger.info(f"Operation completed - Success: {success}")

    def operation_failed(self, error_message: str):
        """
        Mark operation as failed.

        Args:
            error_message: Error description
        """
        with QMutexLocker(self.mutex):
            self.is_paused = False

        self.pause_btn.setEnabled(False)
        self.close_btn.setVisible(True)

        self.overall_status.setText("Operation failed")
        self.add_log_message(f"Operation failed: {error_message}", "ERROR")

        self.logger.error(f"Operation failed: {error_message}")

    # Slot implementations
    @pyqtSlot()
    def update_display(self):
        """Update time displays and calculated statistics."""
        if not self.start_time:
            return

        # Calculate elapsed time
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split(".")[0]  # Remove microseconds
        self.elapsed_time_label.setText(f"Elapsed: {elapsed_str}")

        # Calculate ETA if we have progress data
        with QMutexLocker(self.mutex):
            if self.total_items > 0 and self.completed_items > 0:
                items_per_second = self.completed_items / elapsed.total_seconds()
                remaining_items = self.total_items - self.completed_items

                if items_per_second > 0:
                    eta_seconds = remaining_items / items_per_second
                    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                    self.eta_label.setText(f"ETA: {eta_time.strftime('%H:%M:%S')}")

                # Update processing rate
                self.statistics["processing_rate"] = items_per_second

        # Update statistics display
        self.update_statistics_display()

    def update_statistics_display(self):
        """Update the statistics labels."""
        with QMutexLocker(self.mutex):
            stats = self.statistics.copy()

        self.stats_labels["characters"].setText(str(stats["characters_scraped"]))
        self.stats_labels["images"].setText(str(stats["images_downloaded"]))
        self.stats_labels["pages"].setText(str(stats["pages_processed"]))
        self.stats_labels["errors"].setText(str(stats["errors_encountered"]))
        self.stats_labels["duplicates"].setText(str(stats["duplicate_items"]))

        # Format rates and percentages
        self.stats_labels["processing_rate"].setText(
            f"{stats['processing_rate']:.1f}/s"
        )
        self.stats_labels["success_rate"].setText(f"{stats['success_rate']:.1f}%")
        self.stats_labels["response_time"].setText(
            f"{stats['average_response_time']:.0f}ms"
        )

    @pyqtSlot()
    def toggle_pause(self):
        """Toggle pause/resume state."""
        with QMutexLocker(self.mutex):
            self.is_paused = not self.is_paused

        if self.is_paused:
            self.pause_btn.setText("Resume")
            self.pause_requested.emit()
            self.add_log_message("Operation paused", "INFO")
        else:
            self.pause_btn.setText("Pause")
            self.resume_requested.emit()
            self.add_log_message("Operation resumed", "INFO")

    @pyqtSlot()
    def cancel_operation(self):
        """Cancel the current operation."""
        with QMutexLocker(self.mutex):
            self.is_cancelled = True

        self.cancel_requested.emit()
        self.add_log_message("Cancel requested", "WARNING")
        self.pause_btn.setEnabled(False)

    @pyqtSlot()
    def clear_log(self):
        """Clear the status log."""
        self.log_text.clear()

    @pyqtSlot()
    def export_log(self):
        """Export log to a file."""
        import re
        from html import unescape

        # Get current log content
        log_html = self.log_text.toHtml()

        # Strip HTML tags and decode entities for plain text version
        plain_text = self.log_text.toPlainText()

        # Show file dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Log",
            f"scrape_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "Text Files (*.txt);;HTML Files (*.html);;CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            if selected_filter == "HTML Files (*.html)" or file_path.endswith('.html'):
                # Export as HTML with styling
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Scraper Log Export</title>
    <style>
        body {{
            font-family: Consolas, monospace;
            background-color: #1e1e1e;
            color: #ffffff;
            padding: 20px;
        }}
        .header {{
            border-bottom: 1px solid #555;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .stats {{
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .stats table {{
            width: 100%;
        }}
        .stats td {{
            padding: 5px 10px;
        }}
        .log-content {{
            white-space: pre-wrap;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Scraper Log Export</h1>
        <p>Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Operation: {self.operation_label.text()}</p>
        <p>Target: {self.target_label.text()}</p>
    </div>
    <div class="stats">
        <h2>Statistics</h2>
        <table>
            <tr><td>Characters Scraped:</td><td>{self.statistics['characters_scraped']}</td></tr>
            <tr><td>Images Downloaded:</td><td>{self.statistics['images_downloaded']}</td></tr>
            <tr><td>Pages Processed:</td><td>{self.statistics['pages_processed']}</td></tr>
            <tr><td>Errors:</td><td>{self.statistics['errors_encountered']}</td></tr>
            <tr><td>Success Rate:</td><td>{self.statistics['success_rate']:.1f}%</td></tr>
        </table>
    </div>
    <div class="log-content">
        <h2>Log Entries</h2>
        {log_html}
    </div>
</body>
</html>"""
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)

            elif selected_filter == "CSV Files (*.csv)" or file_path.endswith('.csv'):
                # Export as CSV
                import csv

                # Parse log entries from plain text
                lines = plain_text.strip().split('\n')

                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Level', 'Message'])

                    for line in lines:
                        if line.strip():
                            # Parse format: [HH:MM:SS] LEVEL: message
                            match = re.match(r'\[(\d{2}:\d{2}:\d{2})\]\s*(\w+):\s*(.*)', line)
                            if match:
                                writer.writerow([match.group(1), match.group(2), match.group(3)])
                            else:
                                writer.writerow(['', '', line])
            else:
                # Export as plain text (default)
                header = f"""Scraper Log Export
==================
Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Operation: {self.operation_label.text()}
Target: {self.target_label.text()}

Statistics:
-----------
Characters Scraped: {self.statistics['characters_scraped']}
Images Downloaded: {self.statistics['images_downloaded']}
Pages Processed: {self.statistics['pages_processed']}
Errors Encountered: {self.statistics['errors_encountered']}
Success Rate: {self.statistics['success_rate']:.1f}%

Log Entries:
------------
{plain_text}
"""
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(header)

            self.add_log_message(f"Log exported to: {file_path}", "SUCCESS")
            self.logger.info(f"Log exported to: {file_path}")

        except (IOError, OSError) as e:
            self.add_log_message(f"Failed to export log: {e}", "ERROR")
            self.logger.error(f"Failed to export log: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export log to file:\n{e}"
            )

    @pyqtSlot()
    def show_details(self):
        """Show detailed operation information in a dialog."""
        details_dialog = OperationDetailsDialog(self, self.get_operation_details())
        details_dialog.exec()

    def get_operation_details(self) -> Dict[str, Any]:
        """
        Get comprehensive operation details.

        Returns:
            Dictionary containing all operation details
        """
        with QMutexLocker(self.mutex):
            elapsed = (datetime.now() - self.start_time) if self.start_time else timedelta(0)

            return {
                "operation": self.operation_label.text(),
                "target": self.target_label.text().replace("Target: ", ""),
                "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else "N/A",
                "elapsed_time": str(elapsed).split('.')[0],
                "status": "Paused" if self.is_paused else ("Cancelled" if self.is_cancelled else "Running"),
                "total_items": self.total_items,
                "completed_items": self.completed_items,
                "failed_items": self.failed_items,
                "skipped_items": self.skipped_items,
                "statistics": self.statistics.copy(),
            }


class OperationDetailsDialog(QDialog):
    """Dialog showing detailed operation statistics and information."""

    def __init__(self, parent=None, details: Dict[str, Any] = None):
        super().__init__(parent)
        self.details = details or {}
        self.setWindowTitle("Operation Details")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget for organized display
        tab_widget = QTabWidget()

        # Overview tab
        overview_tab = self.create_overview_tab()
        tab_widget.addTab(overview_tab, "Overview")

        # Statistics tab
        stats_tab = self.create_statistics_tab()
        tab_widget.addTab(stats_tab, "Statistics")

        # Performance tab
        performance_tab = self.create_performance_tab()
        tab_widget.addTab(performance_tab, "Performance")

        layout.addWidget(tab_widget)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def create_overview_tab(self) -> QWidget:
        """Create the overview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Operation info group
        info_group = QGroupBox("Operation Information")
        info_layout = QGridLayout(info_group)

        info_items = [
            ("Operation:", self.details.get("operation", "N/A")),
            ("Target:", self.details.get("target", "N/A")),
            ("Start Time:", self.details.get("start_time", "N/A")),
            ("Elapsed Time:", self.details.get("elapsed_time", "N/A")),
            ("Status:", self.details.get("status", "N/A")),
        ]

        for row, (label, value) in enumerate(info_items):
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            info_layout.addWidget(label_widget, row, 0)
            info_layout.addWidget(QLabel(str(value)), row, 1)

        layout.addWidget(info_group)

        # Progress summary group
        progress_group = QGroupBox("Progress Summary")
        progress_layout = QGridLayout(progress_group)

        total = self.details.get("total_items", 0)
        completed = self.details.get("completed_items", 0)
        failed = self.details.get("failed_items", 0)
        skipped = self.details.get("skipped_items", 0)
        remaining = max(0, total - completed - failed - skipped)

        progress_items = [
            ("Total Items:", total, "#333"),
            ("Completed:", completed, "#28a745"),
            ("Failed:", failed, "#dc3545"),
            ("Skipped:", skipped, "#ffc107"),
            ("Remaining:", remaining, "#007bff"),
        ]

        for row, (label, value, color) in enumerate(progress_items):
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            progress_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(str(value))
            value_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            progress_layout.addWidget(value_label, row, 1)

            # Add percentage
            if total > 0 and label != "Total Items:":
                pct = (value / total) * 100
                pct_label = QLabel(f"({pct:.1f}%)")
                pct_label.setStyleSheet("color: #666;")
                progress_layout.addWidget(pct_label, row, 2)

        layout.addWidget(progress_group)
        layout.addStretch()

        return widget

    def create_statistics_tab(self) -> QWidget:
        """Create the statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        stats = self.details.get("statistics", {})

        # Create table for statistics
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Statistic", "Value"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        stat_display = [
            ("Characters Scraped", stats.get("characters_scraped", 0)),
            ("Images Downloaded", stats.get("images_downloaded", 0)),
            ("Pages Processed", stats.get("pages_processed", 0)),
            ("Data Validated", stats.get("data_validated", 0)),
            ("Errors Encountered", stats.get("errors_encountered", 0)),
            ("Duplicate Items", stats.get("duplicate_items", 0)),
        ]

        table.setRowCount(len(stat_display))

        for row, (name, value) in enumerate(stat_display):
            name_item = QTableWidgetItem(name)
            value_item = QTableWidgetItem(str(value))
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Color coding for errors
            if "error" in name.lower() and value > 0:
                value_item.setForeground(QColor("#dc3545"))

            table.setItem(row, 0, name_item)
            table.setItem(row, 1, value_item)

        layout.addWidget(table)

        return widget

    def create_performance_tab(self) -> QWidget:
        """Create the performance tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        stats = self.details.get("statistics", {})

        # Performance metrics group
        perf_group = QGroupBox("Performance Metrics")
        perf_layout = QGridLayout(perf_group)

        processing_rate = stats.get("processing_rate", 0)
        success_rate = stats.get("success_rate", 0)
        avg_response = stats.get("average_response_time", 0)

        perf_items = [
            ("Processing Rate:", f"{processing_rate:.2f} items/sec"),
            ("Success Rate:", f"{success_rate:.1f}%"),
            ("Average Response Time:", f"{avg_response:.0f}ms"),
        ]

        for row, (label, value) in enumerate(perf_items):
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            perf_layout.addWidget(label_widget, row, 0)
            perf_layout.addWidget(QLabel(value), row, 1)

        layout.addWidget(perf_group)

        # Throughput analysis
        throughput_group = QGroupBox("Throughput Analysis")
        throughput_layout = QVBoxLayout(throughput_group)

        elapsed_str = self.details.get("elapsed_time", "0:00:00")
        completed = self.details.get("completed_items", 0)
        total = self.details.get("total_items", 0)

        # Parse elapsed time
        try:
            parts = elapsed_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            total_seconds = hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError):
            total_seconds = 0

        if total_seconds > 0 and completed > 0:
            items_per_minute = (completed / total_seconds) * 60
            remaining = max(0, total - completed)
            eta_seconds = (remaining / completed) * total_seconds if completed > 0 else 0
            eta_str = str(timedelta(seconds=int(eta_seconds)))

            throughput_text = f"""
Items processed: {completed} in {elapsed_str}
Average throughput: {items_per_minute:.1f} items/minute
Remaining items: {remaining}
Estimated time to completion: {eta_str}
"""
        else:
            throughput_text = "Insufficient data for throughput analysis."

        throughput_label = QLabel(throughput_text.strip())
        throughput_label.setWordWrap(True)
        throughput_layout.addWidget(throughput_label)

        layout.addWidget(throughput_group)
        layout.addStretch()

        return widget

    def setup_style(self):
        """Set up dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #6c757d;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 5px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
            QPushButton {
                background-color: #007bff;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

    # Properties for external access
    @property
    def is_operation_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        with QMutexLocker(self.mutex):
            return self.is_cancelled

    @property
    def is_operation_paused(self) -> bool:
        """Check if operation is paused."""
        with QMutexLocker(self.mutex):
            return self.is_paused

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.pause_btn.isEnabled():  # Operation is still running
            self.cancel_operation()

        # Stop update timer
        self.update_timer.stop()

        super().closeEvent(event)
