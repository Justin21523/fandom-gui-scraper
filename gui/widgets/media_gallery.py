# gui/widgets/media_gallery.py
"""
Media gallery widget for displaying and managing character images and media files.

This module provides comprehensive media management functionality including
image viewing, organizing, filtering, and batch operations.
"""

import os
import shutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import mimetypes

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QFrame,
    QSplitter,
    QTabWidget,
    QProgressBar,
    QSlider,
    QMessageBox,
    QFileDialog,
    QMenu,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
    QToolButton,
    QButtonGroup,
    QRadioButton,
)
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QTimer,
    QThread,
    QSize,
    QRect,
    QPoint,
    pyqtSlot,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt6.QtGui import (
    QPixmap,
    QIcon,
    QFont,
    QPainter,
    QColor,
    QPalette,
    QCursor,
    QAction,
    QKeySequence,
    QShortcut,
    QMovie,
    QPen,
    QBrush,
)

from utils.logger import get_logger


class MediaGallery(QWidget):
    """
    Comprehensive media gallery widget for anime character images and media.

    Features:
    - Grid and list view modes
    - Image filtering and sorting
    - Batch operations (download, organize, export)
    - Image metadata editing
    - Slideshow mode
    - Image comparison tools
    """

    # Custom signals
    image_selected = pyqtSignal(str)  # image path
    image_double_clicked = pyqtSignal(str)  # image path
    images_updated = pyqtSignal(list)  # image list
    download_requested = pyqtSignal(str, str)  # url, save_path
    batch_operation_completed = pyqtSignal(str, int)  # operation, count

    def __init__(self, parent=None):
        """Initialize media gallery widget."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)

        # Data
        self.media_items = []
        self.filtered_items = []
        self.selected_items = []
        self.current_item_index = 0

        # View settings
        self.view_mode = "grid"  # grid, list, details
        self.thumbnail_size = 150
        self.sort_by = "name"
        self.sort_order = "asc"

        # Gallery state
        self.slideshow_active = False
        self.slideshow_timer = QTimer()
        self.slideshow_interval = 3000  # 3 seconds

        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()

        self.logger.info("Media gallery widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)

        # Left panel - filters and info
        left_panel = self._create_control_panel()
        content_splitter.addWidget(left_panel)

        # Center panel - media gallery
        center_panel = self._create_gallery_panel()
        content_splitter.addWidget(center_panel)

        # Right panel - preview and details
        right_panel = self._create_preview_panel()
        content_splitter.addWidget(right_panel)

        # Set splitter sizes
        content_splitter.setSizes([200, 600, 300])

        # Status bar
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

    def _create_toolbar(self) -> QWidget:
        """Create toolbar with view controls."""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 2, 5, 2)

        # View mode buttons
        view_group = QButtonGroup()
        self.grid_view_btn = QPushButton("Grid")
        self.grid_view_btn.setCheckable(True)
        self.grid_view_btn.setChecked(True)
        self.list_view_btn = QPushButton("List")
        self.list_view_btn.setCheckable(True)
        self.details_view_btn = QPushButton("Details")
        self.details_view_btn.setCheckable(True)

        view_group.addButton(self.grid_view_btn, 0)
        view_group.addButton(self.list_view_btn, 1)
        view_group.addButton(self.details_view_btn, 2)

        layout.addWidget(QLabel("View:"))
        layout.addWidget(self.grid_view_btn)
        layout.addWidget(self.list_view_btn)
        layout.addWidget(self.details_view_btn)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        layout.addWidget(separator)

        # Thumbnail size slider
        layout.addWidget(QLabel("Size:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(50, 300)
        self.size_slider.setValue(150)
        self.size_slider.setMaximumWidth(100)
        layout.addWidget(self.size_slider)

        # Sort controls
        layout.addWidget(QLabel("Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            [
                "Name",
                "Date Created",
                "Date Modified",
                "File Size",
                "Image Dimensions",
                "Character Name",
                "Quality Score",
            ]
        )
        layout.addWidget(self.sort_combo)

        self.sort_order_btn = QPushButton("↓")
        self.sort_order_btn.setMaximumWidth(30)
        layout.addWidget(self.sort_order_btn)

        layout.addStretch()

        # Action buttons
        self.refresh_btn = QPushButton("Refresh")
        self.slideshow_btn = QPushButton("Slideshow")
        self.import_btn = QPushButton("Import")
        self.export_btn = QPushButton("Export")

        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.slideshow_btn)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.export_btn)

        return toolbar

    def _create_control_panel(self) -> QWidget:
        """Create control panel with filters and settings."""
        panel = QWidget()
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)

        # Search and filter
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search images...")
        search_layout.addWidget(self.search_input)

        # Filter options
        filter_layout = QFormLayout()

        self.anime_filter = QComboBox()
        self.anime_filter.addItem("All Anime")
        filter_layout.addRow("Anime:", self.anime_filter)

        self.character_filter = QComboBox()
        self.character_filter.addItem("All Characters")
        filter_layout.addRow("Character:", self.character_filter)

        self.type_filter = QComboBox()
        self.type_filter.addItems(
            ["All Types", "Portrait", "Full Body", "Scene", "Other"]
        )
        filter_layout.addRow("Type:", self.type_filter)

        search_layout.addLayout(filter_layout)

        # Image quality filter
        quality_layout = QHBoxLayout()
        self.min_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_quality_slider.setRange(0, 100)
        self.min_quality_slider.setValue(0)
        self.quality_label = QLabel("0%")

        quality_layout.addWidget(self.min_quality_slider)
        quality_layout.addWidget(self.quality_label)
        search_layout.addLayout(quality_layout)

        layout.addWidget(search_group)

        # Image properties
        properties_group = QGroupBox("Image Properties")
        properties_layout = QVBoxLayout(properties_group)

        self.has_metadata_checkbox = QCheckBox("Has metadata")
        properties_layout.addWidget(self.has_metadata_checkbox)

        self.high_resolution_checkbox = QCheckBox("High resolution (>500px)")
        properties_layout.addWidget(self.high_resolution_checkbox)

        self.recently_added_checkbox = QCheckBox("Recently added")
        properties_layout.addWidget(self.recently_added_checkbox)

        layout.addWidget(properties_group)

        # Batch operations
        batch_group = QGroupBox("Batch Operations")
        batch_layout = QVBoxLayout(batch_group)

        self.select_all_btn = QPushButton("Select All")
        batch_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Select None")
        batch_layout.addWidget(self.select_none_btn)

        batch_layout.addWidget(QLabel("Selected Actions:"))

        self.download_selected_btn = QPushButton("Download")
        batch_layout.addWidget(self.download_selected_btn)

        self.delete_selected_btn = QPushButton("Delete")
        batch_layout.addWidget(self.delete_selected_btn)

        self.organize_selected_btn = QPushButton("Organize")
        batch_layout.addWidget(self.organize_selected_btn)

        layout.addWidget(batch_group)

        layout.addStretch()
        return panel

    def _create_gallery_panel(self) -> QWidget:
        """Create main gallery display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget for different views
        self.gallery_tabs = QTabWidget()
        layout.addWidget(self.gallery_tabs)

        # Grid view
        self.grid_view = self._create_grid_view()
        self.gallery_tabs.addTab(self.grid_view, "Grid View")

        # List view
        self.list_view = self._create_list_view()
        self.gallery_tabs.addTab(self.list_view, "List View")

        # Slideshow view
        self.slideshow_view = self._create_slideshow_view()
        self.gallery_tabs.addTab(self.slideshow_view, "Slideshow")

        return panel

    def _create_grid_view(self) -> QWidget:
        """Create grid view for images."""
        # Use scroll area to contain the grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for grid items
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)

        scroll_area.setWidget(self.grid_container)
        return scroll_area

    def _create_list_view(self) -> QWidget:
        """Create list view for images."""
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.ViewMode.ListMode)
        self.image_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        return self.image_list

    def _create_slideshow_view(self) -> QWidget:
        """Create slideshow view."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Slideshow controls
        controls_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous")
        self.play_pause_btn = QPushButton("▶ Play")
        self.next_btn = QPushButton("Next ▶")
        self.fullscreen_btn = QPushButton("Fullscreen")

        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.fullscreen_btn)

        layout.addLayout(controls_layout)

        # Image display area
        self.slideshow_label = QLabel()
        self.slideshow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slideshow_label.setStyleSheet(
            "border: 1px solid gray; background-color: black;"
        )
        self.slideshow_label.setMinimumHeight(400)
        self.slideshow_label.setScaledContents(True)
        layout.addWidget(self.slideshow_label)

        # Image info
        self.slideshow_info_label = QLabel("No image")
        self.slideshow_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.slideshow_info_label)

        return widget

    def _create_preview_panel(self) -> QWidget:
        """Create preview and details panel."""
        panel = QWidget()
        panel.setMaximumWidth(350)
        layout = QVBoxLayout(panel)

        # Image preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet(
            "border: 1px solid gray; background-color: #f0f0f0;"
        )
        self.preview_label.setText("No image selected")
        preview_layout.addWidget(self.preview_label)

        # Preview controls
        preview_controls = QHBoxLayout()
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.fit_to_window_btn = QPushButton("Fit")
        self.actual_size_btn = QPushButton("1:1")

        preview_controls.addWidget(self.zoom_in_btn)
        preview_controls.addWidget(self.zoom_out_btn)
        preview_controls.addWidget(self.fit_to_window_btn)
        preview_controls.addWidget(self.actual_size_btn)

        preview_layout.addLayout(preview_controls)
        layout.addWidget(preview_group)

        # Image details
        details_group = QGroupBox("Details")
        details_layout = QFormLayout(details_group)

        self.filename_label = QLabel("-")
        self.dimensions_label = QLabel("-")
        self.file_size_label = QLabel("-")
        self.format_label = QLabel("-")
        self.character_label = QLabel("-")
        self.anime_label = QLabel("-")
        self.quality_label = QLabel("-")

        details_layout.addRow("Filename:", self.filename_label)
        details_layout.addRow("Dimensions:", self.dimensions_label)
        details_layout.addRow("File Size:", self.file_size_label)
        details_layout.addRow("Format:", self.format_label)
        details_layout.addRow("Character:", self.character_label)
        details_layout.addRow("Anime:", self.anime_label)
        details_layout.addRow("Quality:", self.quality_label)

        layout.addWidget(details_group)

        # Metadata editing
        metadata_group = QGroupBox("Edit Metadata")
        metadata_layout = QFormLayout(metadata_group)

        self.edit_character_input = QLineEdit()
        metadata_layout.addRow("Character:", self.edit_character_input)

        self.edit_anime_input = QLineEdit()
        metadata_layout.addRow("Anime:", self.edit_anime_input)

        self.edit_tags_input = QLineEdit()
        metadata_layout.addRow("Tags:", self.edit_tags_input)

        self.edit_description_input = QTextEdit()
        self.edit_description_input.setMaximumHeight(60)
        metadata_layout.addRow("Description:", self.edit_description_input)

        # Metadata buttons
        metadata_buttons = QHBoxLayout()
        self.save_metadata_btn = QPushButton("Save")
        self.reset_metadata_btn = QPushButton("Reset")

        metadata_buttons.addWidget(self.save_metadata_btn)
        metadata_buttons.addWidget(self.reset_metadata_btn)
        metadata_layout.addRow(metadata_buttons)

        layout.addWidget(metadata_group)

        # Image actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.open_image_btn = QPushButton("Open in Viewer")
        actions_layout.addWidget(self.open_image_btn)

        self.copy_path_btn = QPushButton("Copy Path")
        actions_layout.addWidget(self.copy_path_btn)

        self.rename_image_btn = QPushButton("Rename")
        actions_layout.addWidget(self.rename_image_btn)

        self.delete_image_btn = QPushButton("Delete")
        actions_layout.addWidget(self.delete_image_btn)

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
        self.image_count_label = QLabel("Images: 0")
        self.selected_count_label = QLabel("Selected: 0")
        self.total_size_label = QLabel("Total Size: 0 MB")

        self.operation_progress = QProgressBar()
        self.operation_progress.setVisible(False)
        self.operation_progress.setMaximumWidth(200)

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.image_count_label)
        layout.addWidget(self.selected_count_label)
        layout.addWidget(self.total_size_label)
        layout.addWidget(self.operation_progress)

        return frame

    def setup_connections(self):
        """Set up signal connections."""
        # Toolbar connections
        self.grid_view_btn.clicked.connect(lambda: self._set_view_mode("grid"))
        self.list_view_btn.clicked.connect(lambda: self._set_view_mode("list"))
        self.details_view_btn.clicked.connect(lambda: self._set_view_mode("details"))

        self.size_slider.valueChanged.connect(self._update_thumbnail_size)
        self.sort_combo.currentTextChanged.connect(self._sort_images)
        self.sort_order_btn.clicked.connect(self._toggle_sort_order)

        self.refresh_btn.clicked.connect(self.refresh_gallery)
        self.slideshow_btn.clicked.connect(self._toggle_slideshow)
        self.import_btn.clicked.connect(self.import_images)
        self.export_btn.clicked.connect(self.export_selected_images)

        # Filter connections
        self.search_input.textChanged.connect(self._filter_images)
        self.anime_filter.currentTextChanged.connect(self._filter_images)
        self.character_filter.currentTextChanged.connect(self._filter_images)
        self.type_filter.currentTextChanged.connect(self._filter_images)
        self.min_quality_slider.valueChanged.connect(self._update_quality_label)
        self.min_quality_slider.valueChanged.connect(self._filter_images)

        self.has_metadata_checkbox.toggled.connect(self._filter_images)
        self.high_resolution_checkbox.toggled.connect(self._filter_images)
        self.recently_added_checkbox.toggled.connect(self._filter_images)

        # Batch operation connections
        self.select_all_btn.clicked.connect(self._select_all_images)
        self.select_none_btn.clicked.connect(self._select_no_images)
        self.download_selected_btn.clicked.connect(self._download_selected_images)
        self.delete_selected_btn.clicked.connect(self._delete_selected_images)
        self.organize_selected_btn.clicked.connect(self._organize_selected_images)

        # List view connections
        self.image_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        self.image_list.itemDoubleClicked.connect(self._on_list_item_double_clicked)

        # Slideshow connections
        self.prev_btn.clicked.connect(self._previous_image)
        self.next_btn.clicked.connect(self._next_image)
        self.play_pause_btn.clicked.connect(self._toggle_slideshow_playback)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)

        # Slideshow timer
        self.slideshow_timer.timeout.connect(self._next_image)

        # Preview connections
        self.zoom_in_btn.clicked.connect(self._zoom_in_preview)
        self.zoom_out_btn.clicked.connect(self._zoom_out_preview)
        self.fit_to_window_btn.clicked.connect(self._fit_preview_to_window)
        self.actual_size_btn.clicked.connect(self._actual_size_preview)

        # Metadata connections
        self.save_metadata_btn.clicked.connect(self._save_image_metadata)
        self.reset_metadata_btn.clicked.connect(self._reset_image_metadata)

        # Action connections
        self.open_image_btn.clicked.connect(self._open_image_externally)
        self.copy_path_btn.clicked.connect(self._copy_image_path)
        self.rename_image_btn.clicked.connect(self._rename_selected_image)
        self.delete_image_btn.clicked.connect(self._delete_selected_image)

    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Navigation shortcuts
        QShortcut(QKeySequence.StandardKey.Delete, self, self._delete_selected_image)
        QShortcut(QKeySequence("F2"), self, self._rename_selected_image)
        QShortcut(QKeySequence("Ctrl+A"), self, self._select_all_images)
        QShortcut(QKeySequence("Escape"), self, self._select_no_images)

        # Slideshow shortcuts
        QShortcut(QKeySequence("Space"), self, self._toggle_slideshow_playback)
        QShortcut(QKeySequence("Left"), self, self._previous_image)
        QShortcut(QKeySequence("Right"), self, self._next_image)
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)

        # View shortcuts
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._set_view_mode("grid"))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._set_view_mode("list"))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._set_view_mode("details"))

    def set_media_data(self, media_items: List[Dict[str, Any]]):
        """Set media data to display in gallery."""
        self.media_items = media_items
        self.filtered_items = media_items.copy()

        # Update filter options
        self._update_filter_options()

        # Update display
        self._update_gallery_display()
        self._update_status_bar()

        self.images_updated.emit(media_items)
        self.logger.info(f"Gallery updated with {len(media_items)} media items")

    def refresh_gallery(self):
        """Refresh gallery display."""
        self._update_gallery_display()
        self._update_status_bar()
        self.status_label.setText("Gallery refreshed")

        # Auto-clear status after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

    def import_images(self):
        """Import images from file system."""
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")

        if directory:
            self._import_images_from_directory(directory)

    def export_selected_images(self):
        """Export selected images."""
        if not self.selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select images to export."
            )
            return

        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory")

        if directory:
            self._export_images_to_directory(directory)

    def _set_view_mode(self, mode: str):
        """Set gallery view mode."""
        self.view_mode = mode

        if mode == "grid":
            self.gallery_tabs.setCurrentIndex(0)
            self.grid_view_btn.setChecked(True)
        elif mode == "list":
            self.gallery_tabs.setCurrentIndex(1)
            self.list_view_btn.setChecked(True)
        elif mode == "details":
            self.gallery_tabs.setCurrentIndex(1)  # Use list view for details
            self.details_view_btn.setChecked(True)

        self._update_gallery_display()

    def _update_thumbnail_size(self, size: int):
        """Update thumbnail size."""
        self.thumbnail_size = size
        if self.view_mode == "grid":
            self._update_grid_view()

    def _toggle_sort_order(self):
        """Toggle sort order between ascending and descending."""
        if self.sort_order == "asc":
            self.sort_order = "desc"
            self.sort_order_btn.setText("↑")
        else:
            self.sort_order = "asc"
            self.sort_order_btn.setText("↓")

        self._sort_images()

    def _sort_images(self):
        """Sort images based on current criteria."""
        sort_key = self.sort_combo.currentText().lower().replace(" ", "_")
        reverse = self.sort_order == "desc"

        if sort_key == "name":
            self.filtered_items.sort(
                key=lambda x: x.get("filename", ""), reverse=reverse
            )
        elif sort_key == "date_created":
            self.filtered_items.sort(
                key=lambda x: x.get("created_date", ""), reverse=reverse
            )
        elif sort_key == "date_modified":
            self.filtered_items.sort(
                key=lambda x: x.get("modified_date", ""), reverse=reverse
            )
        elif sort_key == "file_size":
            self.filtered_items.sort(
                key=lambda x: x.get("file_size", 0), reverse=reverse
            )
        elif sort_key == "image_dimensions":
            self.filtered_items.sort(
                key=lambda x: x.get("width", 0) * x.get("height", 0), reverse=reverse
            )
        elif sort_key == "character_name":
            self.filtered_items.sort(
                key=lambda x: x.get("character_name", ""), reverse=reverse
            )
        elif sort_key == "quality_score":
            self.filtered_items.sort(
                key=lambda x: x.get("quality_score", 0), reverse=reverse
            )

        self._update_gallery_display()

    def _filter_images(self):
        """Filter images based on current criteria."""
        search_text = self.search_input.text().lower()
        anime_filter = self.anime_filter.currentText()
        character_filter = self.character_filter.currentText()
        type_filter = self.type_filter.currentText()
        min_quality = self.min_quality_slider.value()

        filtered = []

        for item in self.media_items:
            # Search filter
            if search_text:
                searchable_text = f"{item.get('filename', '')} {item.get('character_name', '')} {item.get('tags', '')}".lower()
                if search_text not in searchable_text:
                    continue

            # Anime filter
            if anime_filter != "All Anime":
                if item.get("anime_name") != anime_filter:
                    continue

            # Character filter
            if character_filter != "All Characters":
                if item.get("character_name") != character_filter:
                    continue

            # Type filter
            if type_filter != "All Types":
                if item.get("image_type") != type_filter.lower():
                    continue

            # Quality filter
            if item.get("quality_score", 0) < min_quality:
                continue

            # Property filters
            if self.has_metadata_checkbox.isChecked():
                if not item.get("character_name") and not item.get("tags"):
                    continue

            if self.high_resolution_checkbox.isChecked():
                width = item.get("width", 0)
                height = item.get("height", 0)
                if width < 500 and height < 500:
                    continue

            if self.recently_added_checkbox.isChecked():
                created_date = item.get("created_date", "")
                if created_date:
                    try:
                        created = datetime.fromisoformat(
                            created_date.replace("Z", "+00:00")
                        )
                        days_old = (datetime.now() - created).days
                        if days_old > 7:  # More than 7 days old
                            continue
                    except:
                        continue

            filtered.append(item)

        self.filtered_items = filtered
        self._sort_images()
        self._update_status_bar()

    def _update_filter_options(self):
        """Update filter dropdown options."""
        # Update anime filter
        anime_names = set()
        character_names = set()

        for item in self.media_items:
            anime_name = item.get("anime_name", "")
            character_name = item.get("character_name", "")

            if anime_name:
                anime_names.add(anime_name)
            if character_name:
                character_names.add(character_name)

        # Update anime filter
        current_anime = self.anime_filter.currentText()
        self.anime_filter.clear()
        self.anime_filter.addItem("All Anime")
        self.anime_filter.addItems(sorted(anime_names))

        index = self.anime_filter.findText(current_anime)
        if index >= 0:
            self.anime_filter.setCurrentIndex(index)

        # Update character filter
        current_character = self.character_filter.currentText()
        self.character_filter.clear()
        self.character_filter.addItem("All Characters")
        self.character_filter.addItems(sorted(character_names))

        index = self.character_filter.findText(current_character)
        if index >= 0:
            self.character_filter.setCurrentIndex(index)

    def _update_gallery_display(self):
        """Update gallery display based on current view mode."""
        if self.view_mode == "grid":
            self._update_grid_view()
        elif self.view_mode in ["list", "details"]:
            self._update_list_view()

    def _update_grid_view(self):
        """Update grid view display."""
        # Clear existing items
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        # Calculate grid dimensions
        columns = max(1, self.grid_container.width() // (self.thumbnail_size + 20))

        # Add image items
        for index, item in enumerate(self.filtered_items):
            row = index // columns
            col = index % columns

            image_widget = self._create_grid_image_widget(item, index)
            self.grid_layout.addWidget(image_widget, row, col)

        # Update layout
        self.grid_container.adjustSize()

    def _create_grid_image_widget(self, item: Dict[str, Any], index: int) -> QWidget:
        """Create image widget for grid view."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setFixedSize(self.thumbnail_size + 10, self.thumbnail_size + 40)
        widget.setStyleSheet(
            """
            QFrame {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            QFrame:hover {
                border-color: #4CAF50;
            }
        """
        )

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)

        # Image label
        image_label = QLabel()
        image_label.setFixedSize(self.thumbnail_size, self.thumbnail_size)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("border: none;")

        # Load thumbnail
        image_path = item.get("local_path") or item.get("image_url", "")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.thumbnail_size,
                    self.thumbnail_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("Invalid\nImage")
        else:
            image_label.setText("No\nImage")

        layout.addWidget(image_label)

        # Filename label
        filename = item.get("filename", "Unknown")
        if len(filename) > 15:
            filename = filename[:12] + "..."

        filename_label = QLabel(filename)
        filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_label.setStyleSheet("border: none; font-size: 10px;")
        layout.addWidget(filename_label)

        # Store item data
        widget.setProperty("item_data", item)
        widget.setProperty("item_index", index)

        # Install event filter for clicks
        widget.mousePressEvent = lambda event, w=widget: self._on_grid_item_clicked(
            w, event
        )

        return widget

    def _update_list_view(self):
        """Update list view display."""
        self.image_list.clear()

        for index, item in enumerate(self.filtered_items):
            list_item = QListWidgetItem()

            # Set item text based on view mode
            if self.view_mode == "list":
                text = item.get("filename", "Unknown")
            else:  # details mode
                filename = item.get("filename", "Unknown")
                character = item.get("character_name", "Unknown")
                anime = item.get("anime_name", "Unknown")
                size = self._format_file_size(item.get("file_size", 0))
                text = f"{filename} | {character} | {anime} | {size}"

            list_item.setText(text)

            # Set thumbnail icon
            image_path = item.get("local_path") or item.get("image_url", "")
            if image_path and os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    icon_pixmap = pixmap.scaled(
                        64,
                        64,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    list_item.setIcon(QIcon(icon_pixmap))

            # Store item data
            list_item.setData(Qt.ItemDataRole.UserRole, item)

            # Set tooltip
            tooltip = f"Character: {item.get('character_name', 'Unknown')}\n"
            tooltip += f"Anime: {item.get('anime_name', 'Unknown')}\n"
            tooltip += f"Size: {item.get('width', '?')}x{item.get('height', '?')}\n"
            tooltip += f"File Size: {self._format_file_size(item.get('file_size', 0))}"
            list_item.setToolTip(tooltip)

            self.image_list.addItem(list_item)

    def _update_status_bar(self):
        """Update status bar information."""
        total_images = len(self.media_items)
        filtered_images = len(self.filtered_items)
        selected_images = len(self.selected_items)

        # Calculate total file size
        total_size = sum(item.get("file_size", 0) for item in self.filtered_items)

        self.image_count_label.setText(f"Images: {filtered_images}/{total_images}")
        self.selected_count_label.setText(f"Selected: {selected_images}")
        self.total_size_label.setText(
            f"Total Size: {self._format_file_size(total_size)}"
        )

    def _update_quality_label(self, value: int):
        """Update quality filter label."""
        self.quality_label.setText(f"{value}%")

    # Event handlers
    def _on_grid_item_clicked(self, widget: QWidget, event):
        """Handle grid item click."""
        item_data = widget.property("item_data")
        item_index = widget.property("item_index")

        if event.button() == Qt.MouseButton.LeftButton:
            # Single click - select item
            self._select_image_item(item_data, item_index)

            if event.type() == event.Type.MouseButtonDblClick:
                # Double click - open image
                self.image_double_clicked.emit(item_data.get("local_path", ""))

    def _on_list_selection_changed(self):
        """Handle list view selection changes."""
        current_item = self.image_list.currentItem()
        if current_item:
            item_data = current_item.data(Qt.ItemDataRole.UserRole)
            row = self.image_list.row(current_item)
            self._select_image_item(item_data, row)

    def _on_list_item_double_clicked(self, item: QListWidgetItem):
        """Handle list item double click."""
        item_data = item.data(Qt.ItemDataRole.UserRole)
        image_path = item_data.get("local_path", "")
        self.image_double_clicked.emit(image_path)

    def _select_image_item(self, item_data: Dict[str, Any], index: int):
        """Select an image item and update preview."""
        self.current_item_index = index

        # Update preview
        self._update_image_preview(item_data)

        # Update metadata form
        self._load_image_metadata(item_data)

        # Emit signal
        image_path = item_data.get("local_path", "")
        if image_path:
            self.image_selected.emit(image_path)

    def _update_image_preview(self, item_data: Dict[str, Any]):
        """Update image preview display."""
        image_path = item_data.get("local_path", "")

        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit preview area
                preview_size = self.preview_label.size()
                scaled_pixmap = pixmap.scaled(
                    preview_size.width() - 10,
                    preview_size.height() - 10,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText("Invalid Image")
        else:
            self.preview_label.setText("Image Not Found")

        # Update details
        self.filename_label.setText(item_data.get("filename", "Unknown"))

        width = item_data.get("width", 0)
        height = item_data.get("height", 0)
        self.dimensions_label.setText(
            f"{width} x {height}" if width and height else "Unknown"
        )

        file_size = item_data.get("file_size", 0)
        self.file_size_label.setText(self._format_file_size(file_size))

        self.format_label.setText(item_data.get("format", "Unknown"))
        self.character_label.setText(item_data.get("character_name", "Unknown"))
        self.anime_label.setText(item_data.get("anime_name", "Unknown"))

        quality = item_data.get("quality_score", 0)
        self.quality_label.setText(f"{quality}%" if quality else "Unknown")

    def _load_image_metadata(self, item_data: Dict[str, Any]):
        """Load image metadata into edit form."""
        self.edit_character_input.setText(item_data.get("character_name", ""))
        self.edit_anime_input.setText(item_data.get("anime_name", ""))

        tags = item_data.get("tags", [])
        if isinstance(tags, list):
            tags_text = ", ".join(tags)
        else:
            tags_text = str(tags)
        self.edit_tags_input.setText(tags_text)

        self.edit_description_input.setPlainText(item_data.get("description", ""))

    # Action methods
    def _select_all_images(self):
        """Select all images."""
        self.selected_items = self.filtered_items.copy()
        self._update_status_bar()

        # Update visual selection in views
        if self.view_mode in ["list", "details"]:
            self.image_list.selectAll()

    def _select_no_images(self):
        """Clear image selection."""
        self.selected_items.clear()
        self._update_status_bar()

        # Update visual selection in views
        if self.view_mode in ["list", "details"]:
            self.image_list.clearSelection()

    def _download_selected_images(self):
        """Download selected images from URLs."""
        if not self.selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select images to download."
            )
            return

        # Create download worker
        download_worker = ImageDownloadWorker(self.selected_items)
        download_worker.progress.connect(self._update_download_progress)
        download_worker.finished.connect(self._on_download_finished)
        download_worker.start()

        self.operation_progress.setVisible(True)
        self.status_label.setText("Downloading images...")

    def _delete_selected_images(self):
        """Delete selected images."""
        if not self.selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select images to delete."
            )
            return

        reply = QMessageBox.question(
            self,
            "Delete Images",
            f"Are you sure you want to delete {len(self.selected_items)} image(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            for item in self.selected_items:
                image_path = item.get("local_path", "")
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                        deleted_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete {image_path}: {e}")

            # Remove from media items
            for item in self.selected_items:
                if item in self.media_items:
                    self.media_items.remove(item)

            self.selected_items.clear()
            self._filter_images()

            self.batch_operation_completed.emit("delete", deleted_count)
            QMessageBox.information(
                self, "Delete Complete", f"Deleted {deleted_count} images."
            )

    def _organize_selected_images(self):
        """Organize selected images by anime/character."""
        if not self.selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select images to organize."
            )
            return

        base_directory = QFileDialog.getExistingDirectory(
            self, "Select Organization Directory"
        )

        if base_directory:
            organized_count = 0

            for item in self.selected_items:
                source_path = item.get("local_path", "")
                if not source_path or not os.path.exists(source_path):
                    continue

                # Create organization structure
                anime_name = item.get("anime_name", "Unknown_Anime")
                character_name = item.get("character_name", "Unknown_Character")

                # Sanitize folder names
                anime_folder = self._sanitize_filename(anime_name)
                character_folder = self._sanitize_filename(character_name)

                target_dir = Path(base_directory) / anime_folder / character_folder
                target_dir.mkdir(parents=True, exist_ok=True)

                # Move file
                filename = os.path.basename(source_path)
                target_path = target_dir / filename

                try:
                    shutil.move(source_path, str(target_path))
                    # Update item path
                    item["local_path"] = str(target_path)
                    organized_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to organize {source_path}: {e}")

            self.batch_operation_completed.emit("organize", organized_count)
            QMessageBox.information(
                self, "Organization Complete", f"Organized {organized_count} images."
            )

    def _toggle_slideshow(self):
        """Toggle slideshow mode."""
        if not self.slideshow_active:
            self.slideshow_active = True
            self.slideshow_btn.setText("Exit Slideshow")
            self.gallery_tabs.setCurrentIndex(2)  # Switch to slideshow tab
            self._start_slideshow()
        else:
            self._stop_slideshow()

    def _start_slideshow(self):
        """Start slideshow."""
        if self.filtered_items:
            self.current_item_index = 0
            self._update_slideshow_image()
            self._toggle_slideshow_playback()

    def _stop_slideshow(self):
        """Stop slideshow."""
        self.slideshow_active = False
        self.slideshow_timer.stop()
        self.slideshow_btn.setText("Slideshow")
        self.play_pause_btn.setText("▶ Play")
        self.gallery_tabs.setCurrentIndex(0)  # Back to grid view

    def _toggle_slideshow_playback(self):
        """Toggle slideshow play/pause."""
        if self.slideshow_timer.isActive():
            self.slideshow_timer.stop()
            self.play_pause_btn.setText("▶ Play")
        else:
            self.slideshow_timer.start(self.slideshow_interval)
            self.play_pause_btn.setText("⏸ Pause")

    def _previous_image(self):
        """Go to previous image in slideshow."""
        if self.filtered_items:
            self.current_item_index = (self.current_item_index - 1) % len(
                self.filtered_items
            )
            self._update_slideshow_image()

    def _next_image(self):
        """Go to next image in slideshow."""
        if self.filtered_items:
            self.current_item_index = (self.current_item_index + 1) % len(
                self.filtered_items
            )
            self._update_slideshow_image()

    def _update_slideshow_image(self):
        """Update slideshow image display."""
        if not self.filtered_items or self.current_item_index >= len(
            self.filtered_items
        ):
            return

        item = self.filtered_items[self.current_item_index]
        image_path = item.get("local_path", "")

        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit slideshow area
                slideshow_size = self.slideshow_label.size()
                scaled_pixmap = pixmap.scaled(
                    slideshow_size.width() - 20,
                    slideshow_size.height() - 20,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.slideshow_label.setPixmap(scaled_pixmap)
            else:
                self.slideshow_label.setText("Invalid Image")
        else:
            self.slideshow_label.setText("Image Not Found")

        # Update info
        info_text = f"{self.current_item_index + 1} / {len(self.filtered_items)} - "
        info_text += f"{item.get('character_name', 'Unknown')} ({item.get('anime_name', 'Unknown')})"
        self.slideshow_info_label.setText(info_text)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        # This would need to be implemented with a separate fullscreen window
        QMessageBox.information(
            self, "Fullscreen", "Fullscreen mode not yet implemented."
        )

    # Preview zoom methods
    def _zoom_in_preview(self):
        """Zoom in preview image."""
        # Implementation would scale the current pixmap larger
        pass

    def _zoom_out_preview(self):
        """Zoom out preview image."""
        # Implementation would scale the current pixmap smaller
        pass

    def _fit_preview_to_window(self):
        """Fit preview image to window."""
        if self.current_item_index < len(self.filtered_items):
            item = self.filtered_items[self.current_item_index]
            self._update_image_preview(item)

    def _actual_size_preview(self):
        """Show preview image at actual size."""
        # Implementation would show image at 100% size
        pass

    # Metadata methods
    def _save_image_metadata(self):
        """Save edited image metadata."""
        if self.current_item_index >= len(self.filtered_items):
            return

        item = self.filtered_items[self.current_item_index]

        # Update item data
        item["character_name"] = self.edit_character_input.text()
        item["anime_name"] = self.edit_anime_input.text()

        tags_text = self.edit_tags_input.text()
        item["tags"] = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

        item["description"] = self.edit_description_input.toPlainText()
        item["last_modified"] = datetime.now().isoformat()

        # Update displays
        self._update_image_preview(item)
        self._update_filter_options()

        self.status_label.setText("Metadata saved")
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

    def _reset_image_metadata(self):
        """Reset image metadata form."""
        if self.current_item_index < len(self.filtered_items):
            item = self.filtered_items[self.current_item_index]
            self._load_image_metadata(item)

    # Action methods
    def _open_image_externally(self):
        """Open image in external viewer."""
        if self.current_item_index < len(self.filtered_items):
            item = self.filtered_items[self.current_item_index]
            image_path = item.get("local_path", "")

            if image_path and os.path.exists(image_path):
                import subprocess
                import platform

                try:
                    if platform.system() == "Windows":
                        os.startfile(image_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", image_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", image_path])
                except Exception as e:
                    QMessageBox.warning(
                        self, "Open Failed", f"Failed to open image:\n{str(e)}"
                    )

    def _copy_image_path(self):
        """Copy image path to clipboard."""
        if self.current_item_index < len(self.filtered_items):
            item = self.filtered_items[self.current_item_index]
            image_path = item.get("local_path", "")

            if image_path:
                from PyQt6.QtWidgets import QApplication

                clipboard = QApplication.clipboard()
                clipboard.setText(image_path)

                self.status_label.setText("Path copied to clipboard")
                QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

    def _rename_selected_image(self):
        """Rename selected image."""
        if self.current_item_index < len(self.filtered_items):
            item = self.filtered_items[self.current_item_index]
            current_path = item.get("local_path", "")

            if not current_path or not os.path.exists(current_path):
                QMessageBox.warning(self, "Invalid Path", "Image file not found.")
                return

            current_name = os.path.basename(current_path)
            new_name, ok = QInputDialog.getText(
                self, "Rename Image", "Enter new filename:", text=current_name
            )

            if ok and new_name.strip() and new_name != current_name:
                directory = os.path.dirname(current_path)
                new_path = os.path.join(directory, new_name.strip())

                try:
                    os.rename(current_path, new_path)
                    item["local_path"] = new_path
                    item["filename"] = new_name.strip()

                    self._update_image_preview(item)
                    self._update_gallery_display()

                    self.status_label.setText("Image renamed")
                    QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

                except Exception as e:
                    QMessageBox.critical(
                        self, "Rename Failed", f"Failed to rename image:\n{str(e)}"
                    )

    def _delete_selected_image(self):
        """Delete currently selected image."""
        if self.current_item_index < len(self.filtered_items):
            item = self.filtered_items[self.current_item_index]
            self.selected_items = [item]
            self._delete_selected_images()

    # Utility methods
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for file system."""
        import re

        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(". ")

        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]

        return sanitized or "Unknown"

    def _import_images_from_directory(self, directory: str):
        """Import images from directory."""
        supported_formats = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        imported_count = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_formats):
                    file_path = os.path.join(root, file)

                    try:
                        # Get image info
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull():
                            stat = os.stat(file_path)

                            # Create media item
                            media_item = {
                                "filename": file,
                                "local_path": file_path,
                                "width": pixmap.width(),
                                "height": pixmap.height(),
                                "file_size": stat.st_size,
                                "format": file.split(".")[-1].upper(),
                                "created_date": datetime.fromtimestamp(
                                    stat.st_ctime
                                ).isoformat(),
                                "modified_date": datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                                "character_name": "",
                                "anime_name": "",
                                "tags": [],
                                "description": "",
                                "quality_score": 50,  # Default quality
                            }

                            self.media_items.append(media_item)
                            imported_count += 1

                    except Exception as e:
                        self.logger.error(f"Failed to import {file_path}: {e}")

        if imported_count > 0:
            self._filter_images()
            self.images_updated.emit(self.media_items)

            QMessageBox.information(
                self,
                "Import Complete",
                f"Imported {imported_count} images from {directory}",
            )
        else:
            QMessageBox.information(
                self,
                "No Images Found",
                "No supported image files found in the selected directory.",
            )

    def _export_images_to_directory(self, directory: str):
        """Export selected images to directory."""
        exported_count = 0

        for item in self.selected_items:
            source_path = item.get("local_path", "")
            if not source_path or not os.path.exists(source_path):
                continue

            filename = item.get("filename", os.path.basename(source_path))
            target_path = os.path.join(directory, filename)

            try:
                shutil.copy2(source_path, target_path)
                exported_count += 1
            except Exception as e:
                self.logger.error(f"Failed to export {source_path}: {e}")

        QMessageBox.information(
            self, "Export Complete", f"Exported {exported_count} images to {directory}"
        )

    # Worker thread event handlers
    @pyqtSlot(str, int)
    def _update_download_progress(self, message: str, progress: int):
        """Update download progress."""
        self.status_label.setText(message)
        self.operation_progress.setValue(progress)

    @pyqtSlot(int)
    def _on_download_finished(self, downloaded_count: int):
        """Handle download completion."""
        self.operation_progress.setVisible(False)
        self.status_label.setText("Ready")

        if downloaded_count > 0:
            self.refresh_gallery()
            self.batch_operation_completed.emit("download", downloaded_count)

            QMessageBox.information(
                self, "Download Complete", f"Downloaded {downloaded_count} images."
            )
