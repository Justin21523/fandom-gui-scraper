# gui/widgets/progress_dialog.py
"""
Progress dialog widget for displaying scraping progress and status.

This module provides a comprehensive progress dialog that shows real-time
scraping progress, status messages, and allows user control over operations.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
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
)
from PyQt5.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot, Qt, QMutex, QMutexLocker
from PyQt5.QtGui import QFont, QPixmap, QMovie, QPalette, QColor

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
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(frame)

        # Operation title
        self.operation_label = QLabel("Preparing to scrape...")
        self.operation_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.operation_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.operation_label)

        # Target information
        self.target_label = QLabel("Target: Not specified")
        self.target_label.setAlignment(Qt.AlignCenter)
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
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(frame)

        # Overall progress
        overall_group = QGroupBox("Overall Progress")
        overall_layout = QVBoxLayout(overall_group)

        self.overall_progress = QProgressBar()
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setFormat("%p% (%v/%m)")
        overall_layout.addWidget(self.overall_progress)

        self.overall_status = QLabel("Waiting to start...")
        overall_layout.addWidget(self.overall_status)

        layout.addWidget(overall_group)

        # Current task progress
        task_group = QGroupBox("Current Task")
        task_layout = QVBoxLayout(task_group)

        self.task_progress = QProgressBar()
        self.task_progress.setTextVisible(True)
        task_layout.addWidget(self.task_progress)

        self.task_status = QLabel("No active task")
        task_layout.addWidget(self.task_status)

        layout.addWidget(task_group)

        # Sub-task progress (for detailed operations)
        subtask_group = QGroupBox("Sub-task Progress")
        subtask_layout = QVBoxLayout(subtask_group)

        self.subtask_progress = QProgressBar()
        self.subtask_progress.setTextVisible(True)
        self.subtask_progress.setVisible(False)  # Hidden by default
        subtask_layout.addWidget(self.subtask_progress)

        self.subtask_status = QLabel("No sub-task")
        self.subtask_status.setVisible(False)
        subtask_layout.addWidget(self.subtask_status)

        layout.addWidget(subtask_group)

        return frame

    def create_statistics_section(self) -> QFrame:
        """
        Create the statistics section.

        Returns:
            Frame containing statistics display
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)

        stats_group = QGroupBox("Statistics")
        layout = QGridLayout(stats_group)

        # Create statistics labels
        self.stats_labels = {}

        # Row 0: Counts
        layout.addWidget(QLabel("Characters:"), 0, 0)
        self.stats_labels["characters"] = QLabel("0")
        self.stats_labels["characters"].setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.stats_labels["characters"], 0, 1)

        layout.addWidget(QLabel("Images:"), 0, 2)
        self.stats_labels["images"] = QLabel("0")
        self.stats_labels["images"].setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.stats_labels["images"], 0, 3)

        layout.addWidget(QLabel("Pages:"), 0, 4)
        self.stats_labels["pages"] = QLabel("0")
        self.stats_labels["pages"].setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.stats_labels["pages"], 0, 5)

        # Row 1: Rates and percentages
        layout.addWidget(QLabel("Success Rate:"), 1, 0)
        self.stats_labels["success_rate"] = QLabel("0%")
        self.stats_labels["success_rate"].setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.stats_labels["success_rate"], 1, 1)

        layout.addWidget(QLabel("Processing Rate:"), 1, 2)
        self.stats_labels["processing_rate"] = QLabel("0/s")
        self.stats_labels["processing_rate"].setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.stats_labels["processing_rate"], 1, 3)

        layout.addWidget(QLabel("Errors:"), 1, 4)
        self.stats_labels["errors"] = QLabel("0")
        self.stats_labels["errors"].setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.stats_labels["errors"], 1, 5)

        # Row 2: Response time and duplicates
        layout.addWidget(QLabel("Avg Response:"), 2, 0)
        self.stats_labels["response_time"] = QLabel("0ms")
        self.stats_labels["response_time"].setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.stats_labels["response_time"], 2, 1)

        layout.addWidget(QLabel("Duplicates:"), 2, 2)
        self.stats_labels["duplicates"] = QLabel("0")
        self.stats_labels["duplicates"].setFont(QFont("Arial", 10, QFont.Bold))
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
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)

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
            scrollbar.setValue(scrollbar.maximum())

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
        # TODO: Implement log export functionality
        self.add_log_message("Log export not yet implemented", "INFO")

    @pyqtSlot()
    def show_details(self):
        """Show detailed operation information."""
        # TODO: Implement details dialog
        self.add_log_message("Details view not yet implemented", "INFO")

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
