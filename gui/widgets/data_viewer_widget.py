# gui/widgets/data_viewer_widget.py
"""
Data viewer widget for displaying scraped anime character data.

This widget provides comprehensive data viewing capabilities including
table views, search/filter functionality, data preview, and export options.
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QFrame,
    QScrollArea,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QAction,
    QMessageBox,
    QProgressBar,
    QSpinBox,
    QDateEdit,
    QSizePolicy,
    QFileDialog,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    pyqtSlot,
    QTimer,
    QThread,
    QSortFilterProxyModel,
    QAbstractTableModel,
    QModelIndex,
    QVariant,
    QDate,
)
from PyQt5.QtGui import (
    QFont,
    QColor,
    QPalette,
    QPixmap,
    QIcon,
    QBrush,
    QPainter,
    QContextMenuEvent,
    QKeySequence,
    QStandardItemModel,
    QStandardItem,
)

from utils.logger import get_logger


class CharacterDataModel(QAbstractTableModel):
    """
    Table model for character data display.

    Provides a structured view of character data with sorting,
    filtering, and editing capabilities.
    """

    def __init__(self, data: List[Dict[str, Any]] = None, parent=None):  # type: ignore
        """
        Initialize the data model.

        Args:
            data: List of character data dictionaries
            parent: Parent widget
        """
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)
        self._data = data or []
        self._headers = self._extract_headers()

        # Data filtering and sorting
        self.filter_text = ""
        self.filter_column = ""
        self.sort_column = 0
        self.sort_order = Qt.AscendingOrder

    def _extract_headers(self) -> List[str]:
        """
        Extract column headers from data.

        Returns:
            List of column header names
        """
        if not self._data:
            return ["Name", "Anime", "Description", "Images", "Scraped At"]

        # Get all unique keys from all data items
        all_keys = set()
        for item in self._data:
            all_keys.update(item.keys())

        # Sort headers with important ones first
        priority_headers = ["name", "anime", "description", "url", "scraped_at"]
        headers = []

        # Add priority headers first
        for header in priority_headers:
            if header in all_keys:
                headers.append(header.replace("_", " ").title())
                all_keys.remove(header)

        # Add remaining headers
        for header in sorted(all_keys):
            if not header.startswith("_"):  # Skip private fields
                headers.append(header.replace("_", " ").title())

        return headers

    def rowCount(self, parent=QModelIndex()) -> int:
        """Return number of rows."""
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Return number of columns."""
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> QVariant:
        """
        Return data for the given index and role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data for the specified index and role
        """
        if not index.isValid() or index.row() >= len(self._data):
            return QVariant()

        item = self._data[index.row()]
        header = self._headers[index.column()].lower().replace(" ", "_")

        if role == Qt.DisplayRole:
            value = item.get(header, "")

            # Format different data types
            if isinstance(value, list):
                return f"[{len(value)} items]"
            elif isinstance(value, dict):
                return f"{{object}}"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, str):
                # Truncate long text
                return value[:100] + "..." if len(value) > 100 else value
            else:
                return str(value) if value is not None else ""

        elif role == Qt.ToolTipRole:
            value = item.get(header, "")
            if isinstance(value, (list, dict)):
                return json.dumps(value, indent=2)
            else:
                return str(value)

        elif role == Qt.BackgroundRole:
            # Alternate row colors
            if index.row() % 2 == 1:
                return QBrush(QColor(248, 248, 248))

        elif role == Qt.TextAlignmentRole:
            if header in ["scraped_at", "url"]:
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return QVariant()

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> QVariant:
        """
        Return header data.

        Args:
            section: Header section
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self._headers):
                return self._headers[section]

        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)

        return QVariant()

    def sort(self, column: int, order: Qt.SortOrder):
        """
        Sort data by column.

        Args:
            column: Column index to sort by
            order: Sort order (ascending/descending)
        """
        if 0 <= column < len(self._headers):
            self.layoutAboutToBeChanged.emit()

            header = self._headers[column].lower().replace(" ", "_")
            reverse = order == Qt.DescendingOrder

            # Sort data
            self._data.sort(key=lambda x: str(x.get(header, "")), reverse=reverse)

            self.sort_column = column
            self.sort_order = order

            self.layoutChanged.emit()

    def update_data(self, new_data: List[Dict[str, Any]]):
        """
        Update model with new data.

        Args:
            new_data: New character data list
        """
        self.beginResetModel()
        self._data = new_data or []
        self._headers = self._extract_headers()
        self.endResetModel()

        self.logger.info(f"Data model updated with {len(self._data)} items")

    def get_item_data(self, row: int) -> Dict[str, Any]:
        """
        Get complete data for a specific row.

        Args:
            row: Row index

        Returns:
            Complete data dictionary for the row
        """
        if 0 <= row < len(self._data):
            return self._data[row].copy()
        return {}

    def filter_data(self, text: str, column: str = ""):
        """
        Filter data based on text and column.

        Args:
            text: Filter text
            column: Column to filter (empty for all columns)
        """
        self.filter_text = text.lower()
        self.filter_column = column.lower()

        # TODO: Implement proper filtering
        # For now, just refresh the view
        self.layoutChanged.emit()


class DataViewerWidget(QWidget):
    """
    Comprehensive data viewer widget for scraped character data.

    Features:
    - Table view with sorting and filtering
    - Detailed item view
    - Search and filter controls
    - Data statistics
    - Export functionality
    """

    # Signals for external communication
    item_selected = pyqtSignal(dict)  # Emitted when item is selected
    export_requested = pyqtSignal(str, list)  # Format and data to export
    data_edited = pyqtSignal(dict)  # Emitted when data is edited

    def __init__(self, parent=None):
        """
        Initialize the data viewer widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(self.__class__.__name__)

        # Data management
        self.data_model = CharacterDataModel()
        self.current_data = []
        self.filtered_data = []
        self.selected_item = {}

        # Search and filter state
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_filters)

        # Set up UI
        self.setup_ui()
        self.setup_connections()

        self.logger.info("Data viewer widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Create control panel
        controls_frame = self.create_controls_section()
        main_layout.addWidget(controls_frame)

        # Create main content splitter
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)

        # Left panel - Data table
        table_frame = self.create_table_section()
        content_splitter.addWidget(table_frame)

        # Right panel - Detail view
        detail_frame = self.create_detail_section()
        content_splitter.addWidget(detail_frame)

        # Set splitter proportions (70% table, 30% details)
        content_splitter.setSizes([700, 300])

        # Status bar
        status_frame = self.create_status_section()
        main_layout.addWidget(status_frame)

    def create_controls_section(self) -> QFrame:
        """
        Create the controls section with search and filter options.

        Returns:
            Frame containing control widgets
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QHBoxLayout(frame)

        # Search group
        search_group = QGroupBox("Search & Filter")
        search_layout = QHBoxLayout(search_group)

        # Search input
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search characters...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)

        # Filter column combo
        search_layout.addWidget(QLabel("Column:"))
        self.filter_column_combo = QComboBox()
        self.filter_column_combo.addItem("All Columns", "")
        self.filter_column_combo.currentTextChanged.connect(self.on_filter_changed)
        search_layout.addWidget(self.filter_column_combo)

        # Clear filters button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_filters)
        search_layout.addWidget(clear_btn)

        layout.addWidget(search_group)

        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        actions_layout.addWidget(refresh_btn)

        # Export button
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.show_export_dialog)
        actions_layout.addWidget(export_btn)

        # Delete selected button
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        actions_layout.addWidget(delete_btn)

        layout.addWidget(actions_group)

        layout.addStretch()

        return frame

    def create_table_section(self) -> QFrame:
        """
        Create the table section for data display.

        Returns:
            Frame containing the data table
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(frame)

        # Table header
        header_layout = QHBoxLayout()

        table_title = QLabel("Character Data")
        table_title.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(table_title)

        header_layout.addStretch()

        # View options
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Table View", "Card View", "Tree View"])
        self.view_mode_combo.currentTextChanged.connect(self.change_view_mode)
        header_layout.addWidget(self.view_mode_combo)

        layout.addLayout(header_layout)

        # Create table widget
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.data_table.setSortingEnabled(True)

        # Configure table headers
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.data_table.verticalHeader().setVisible(False)

        # Set up table signals
        self.data_table.cellClicked.connect(self.on_table_cell_clicked)
        self.data_table.itemSelectionChanged.connect(self.on_selection_changed)

        layout.addWidget(self.data_table)

        return frame

    def create_detail_section(self) -> QFrame:
        """
        Create the detail section for selected item view.

        Returns:
            Frame containing detail widgets
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(frame)

        # Detail header
        detail_title = QLabel("Item Details")
        detail_title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(detail_title)

        # Create tab widget for different detail views
        self.detail_tabs = QTabWidget()

        # General info tab
        general_tab = self.create_general_info_tab()
        self.detail_tabs.addTab(general_tab, "General")

        # Raw data tab
        raw_tab = self.create_raw_data_tab()
        self.detail_tabs.addTab(raw_tab, "Raw Data")

        # Images tab
        images_tab = self.create_images_tab()
        self.detail_tabs.addTab(images_tab, "Images")

        layout.addWidget(self.detail_tabs)

        # Detail actions
        detail_actions = QHBoxLayout()

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_selected_item)
        detail_actions.addWidget(edit_btn)

        copy_btn = QPushButton("Copy Data")
        copy_btn.clicked.connect(self.copy_selected_data)
        detail_actions.addWidget(copy_btn)

        detail_actions.addStretch()

        layout.addLayout(detail_actions)

        return frame

    def create_general_info_tab(self) -> QWidget:
        """
        Create the general information tab.

        Returns:
            Widget containing general info display
        """
        tab = QScrollArea()
        tab.setWidgetResizable(True)

        content_widget = QWidget()
        layout = QFormLayout(content_widget)

        # Create labels for displaying character info
        self.detail_labels = {
            "name": QLabel("No character selected"),
            "anime": QLabel(""),
            "description": QLabel(""),
            "url": QLabel(""),
            "scraped_at": QLabel(""),
            "categories": QLabel(""),
            "image_count": QLabel(""),
            "data_quality": QLabel(""),
        }

        # Style labels
        for label in self.detail_labels.values():
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Add labels to layout
        layout.addRow("Name:", self.detail_labels["name"])
        layout.addRow("Anime:", self.detail_labels["anime"])
        layout.addRow("Description:", self.detail_labels["description"])
        layout.addRow("URL:", self.detail_labels["url"])
        layout.addRow("Scraped At:", self.detail_labels["scraped_at"])
        layout.addRow("Categories:", self.detail_labels["categories"])
        layout.addRow("Image Count:", self.detail_labels["image_count"])
        layout.addRow("Data Quality:", self.detail_labels["data_quality"])

        tab.setWidget(content_widget)
        return tab

    def create_raw_data_tab(self) -> QWidget:
        """
        Create the raw data tab.

        Returns:
            Widget containing raw data display
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Raw data text area
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.raw_data_text)

        # Raw data controls
        controls_layout = QHBoxLayout()

        format_combo = QComboBox()
        format_combo.addItems(["JSON", "YAML", "Python Dict"])
        format_combo.currentTextChanged.connect(self.update_raw_data_display)
        controls_layout.addWidget(format_combo)

        self.format_combo = format_combo  # Store reference for later use

        controls_layout.addStretch()

        copy_raw_btn = QPushButton("Copy Raw Data")
        copy_raw_btn.clicked.connect(self.copy_raw_data)
        controls_layout.addWidget(copy_raw_btn)

        layout.addLayout(controls_layout)

        return tab

    def create_images_tab(self) -> QWidget:
        """
        Create the images tab.

        Returns:
            Widget containing image display
        """
        tab = QScrollArea()
        tab.setWidgetResizable(True)

        self.images_widget = QWidget()
        self.images_layout = QVBoxLayout(self.images_widget)

        # Placeholder label
        self.no_images_label = QLabel("No images available")
        self.no_images_label.setAlignment(Qt.AlignCenter)
        self.no_images_label.setStyleSheet("color: gray; font-style: italic;")
        self.images_layout.addWidget(self.no_images_label)

        tab.setWidget(self.images_widget)
        return tab

    def create_status_section(self) -> QFrame:
        """
        Create the status section.

        Returns:
            Frame containing status information
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QHBoxLayout(frame)

        # Statistics labels
        self.total_items_label = QLabel("Total: 0")
        layout.addWidget(self.total_items_label)

        self.filtered_items_label = QLabel("Filtered: 0")
        layout.addWidget(self.filtered_items_label)

        self.selected_items_label = QLabel("Selected: 0")
        layout.addWidget(self.selected_items_label)

        layout.addStretch()

        # Status message
        self.status_message = QLabel("Ready")
        layout.addWidget(self.status_message)

        return frame

    def setup_connections(self):
        """Set up signal-slot connections."""
        # Connect search timer
        self.search_timer.timeout.connect(self.apply_filters)

    # Event handlers and slots
    @pyqtSlot(str)
    def on_search_changed(self, text: str):
        """
        Handle search text change.

        Args:
            text: New search text
        """
        # Restart search timer for delayed search
        self.search_timer.stop()
        self.search_timer.start(500)  # 500ms delay

    @pyqtSlot(str)
    def on_filter_changed(self, text: str):
        """
        Handle filter column change.

        Args:
            text: Selected filter column
        """
        self.apply_filters()

    @pyqtSlot(int, int)
    def on_table_cell_clicked(self, row: int, column: int):
        """
        Handle table cell click.

        Args:
            row: Clicked row
            column: Clicked column
        """
        if 0 <= row < len(self.filtered_data):
            item_data = self.filtered_data[row]
            self.select_item(item_data)

    @pyqtSlot()
    def on_selection_changed(self):
        """Handle table selection change."""
        selected_rows = set()
        for item in self.data_table.selectedItems():
            selected_rows.add(item.row())

        self.selected_items_label.setText(f"Selected: {len(selected_rows)}")

    @pyqtSlot(str)
    def change_view_mode(self, mode: str):
        """
        Change the data view mode.

        Args:
            mode: New view mode
        """
        # TODO: Implement different view modes
        self.logger.info(f"View mode changed to: {mode}")

    @pyqtSlot()
    def apply_filters(self):
        """Apply current search and filter settings."""
        search_text = self.search_input.text().lower()
        filter_column = self.filter_column_combo.currentData()

        if not search_text:
            self.filtered_data = self.current_data.copy()
        else:
            self.filtered_data = []

            for item in self.current_data:
                # Search in all columns or specific column
                if filter_column:
                    # Search in specific column
                    value = str(item.get(filter_column, "")).lower()
                    if search_text in value:
                        self.filtered_data.append(item)
                else:
                    # Search in all columns
                    found = False
                    for key, value in item.items():
                        if search_text in str(value).lower():
                            found = True
                            break
                    if found:
                        self.filtered_data.append(item)

        self.update_table_display()
        self.update_status()

    @pyqtSlot()
    def clear_filters(self):
        """Clear all filters and search text."""
        self.search_input.clear()
        self.filter_column_combo.setCurrentIndex(0)
        self.apply_filters()

    @pyqtSlot()
    def refresh_data(self):
        """Refresh the data display."""
        self.update_table_display()
        self.update_status()
        self.status_message.setText("Data refreshed")

    @pyqtSlot()
    def show_export_dialog(self):
        """Show export dialog."""
        if not self.filtered_data:
            QMessageBox.information(self, "No Data", "No data available to export.")
            return

        # TODO: Implement export dialog
        self.logger.info("Export dialog requested")

    @pyqtSlot()
    def delete_selected(self):
        """Delete selected items."""
        selected_rows = set()
        for item in self.data_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.information(
                self, "No Selection", "Please select items to delete."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_rows)} item(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # TODO: Implement delete functionality
            self.logger.info(f"Delete requested for {len(selected_rows)} items")

    @pyqtSlot()
    def edit_selected_item(self):
        """Edit the selected item."""
        if not self.selected_item:
            QMessageBox.information(
                self, "No Selection", "Please select an item to edit."
            )
            return

        # TODO: Implement edit dialog
        self.logger.info("Edit dialog requested")

    @pyqtSlot()
    def copy_selected_data(self):
        """Copy selected item data to clipboard."""
        if not self.selected_item:
            return

        # TODO: Implement clipboard copy
        self.logger.info("Copy data requested")

    @pyqtSlot()
    def copy_raw_data(self):
        """Copy raw data to clipboard."""
        if not self.selected_item:
            return

        # TODO: Implement raw data copy
        self.logger.info("Copy raw data requested")

    @pyqtSlot(str)
    def update_raw_data_display(self, format_type: str):
        """
        Update raw data display format.

        Args:
            format_type: Display format (JSON, YAML, etc.)
        """
        if not self.selected_item:
            self.raw_data_text.clear()
            return

        try:
            if format_type == "JSON":
                formatted_data = json.dumps(
                    self.selected_item, indent=2, ensure_ascii=False
                )
            elif format_type == "YAML":
                # TODO: Implement YAML formatting
                formatted_data = json.dumps(
                    self.selected_item, indent=2, ensure_ascii=False
                )
            else:  # Python Dict
                formatted_data = str(self.selected_item)

            self.raw_data_text.setPlainText(formatted_data)

        except Exception as e:
            self.logger.error(f"Failed to format data: {e}")
            self.raw_data_text.setPlainText(f"Error formatting data: {e}")

    # Public methods for external control
    def update_data(self, data: List[Dict[str, Any]]):
        """
        Update the viewer with new data.

        Args:
            data: List of character data dictionaries
        """
        self.current_data = data or []
        self.filtered_data = self.current_data.copy()

        # Update filter column combo
        self.update_filter_columns()

        # Update display
        self.update_table_display()
        self.update_status()

        # Clear selection
        self.selected_item = {}
        self.update_detail_display()

        self.logger.info(f"Data viewer updated with {len(self.current_data)} items")

    def update_filter_columns(self):
        """Update the filter column combo box."""
        current_text = self.filter_column_combo.currentText()

        self.filter_column_combo.clear()
        self.filter_column_combo.addItem("All Columns", "")

        if self.current_data:
            # Get all unique column names
            all_columns = set()
            for item in self.current_data:
                all_columns.update(item.keys())

            # Add columns to combo
            for column in sorted(all_columns):
                if not column.startswith("_"):  # Skip private fields
                    display_name = column.replace("_", " ").title()
                    self.filter_column_combo.addItem(display_name, column)

        # Restore previous selection if possible
        index = self.filter_column_combo.findText(current_text)
        if index >= 0:
            self.filter_column_combo.setCurrentIndex(index)

    def update_table_display(self):
        """Update the table widget display."""
        if not self.filtered_data:
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return

        # Get all unique columns
        all_columns = set()
        for item in self.filtered_data:
            all_columns.update(item.keys())

        # Filter out private columns and sort
        display_columns = sorted(
            [col for col in all_columns if not col.startswith("_")]
        )

        # Set table dimensions
        self.data_table.setRowCount(len(self.filtered_data))
        self.data_table.setColumnCount(len(display_columns))

        # Set headers
        headers = [col.replace("_", " ").title() for col in display_columns]
        self.data_table.setHorizontalHeaderLabels(headers)

        # Populate table
        for row, item in enumerate(self.filtered_data):
            for col, column_name in enumerate(display_columns):
                value = item.get(column_name, "")

                # Format value for display
                if isinstance(value, list):
                    display_value = f"[{len(value)} items]"
                elif isinstance(value, dict):
                    display_value = "{object}"
                elif isinstance(value, str) and len(value) > 50:
                    display_value = value[:50] + "..."
                else:
                    display_value = str(value) if value is not None else ""

                # Create table item
                table_item = QTableWidgetItem(display_value)
                table_item.setToolTip(str(value))

                # Set item data for sorting
                table_item.setData(Qt.UserRole, value)

                self.data_table.setItem(row, col, table_item)

        # Resize columns to content
        self.data_table.resizeColumnsToContents()

    def update_detail_display(self):
        """Update the detail view with selected item data."""
        if not self.selected_item:
            # Clear all detail displays
            for label in self.detail_labels.values():
                label.setText("")

            self.detail_labels["name"].setText("No character selected")
            self.raw_data_text.clear()
            self.update_images_display([])
            return

        # Update general info
        self.detail_labels["name"].setText(self.selected_item.get("name", "Unknown"))
        self.detail_labels["anime"].setText(self.selected_item.get("anime", "Unknown"))

        description = self.selected_item.get("description", "")
        if len(description) > 200:
            description = description[:200] + "..."
        self.detail_labels["description"].setText(description)

        url = self.selected_item.get("url", "")
        if url:
            self.detail_labels["url"].setText(f'<a href="{url}">{url}</a>')
            self.detail_labels["url"].setOpenExternalLinks(True)
        else:
            self.detail_labels["url"].setText("No URL")

        # Format scraped date
        scraped_at = self.selected_item.get("scraped_at", "")
        if scraped_at:
            try:
                if isinstance(scraped_at, (int, float)):
                    scraped_date = datetime.fromtimestamp(scraped_at)
                    formatted_date = scraped_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_date = str(scraped_at)
                self.detail_labels["scraped_at"].setText(formatted_date)
            except:
                self.detail_labels["scraped_at"].setText(str(scraped_at))
        else:
            self.detail_labels["scraped_at"].setText("Unknown")

        # Categories
        categories = self.selected_item.get("categories", [])
        if isinstance(categories, list):
            self.detail_labels["categories"].setText(", ".join(categories[:5]))
        else:
            self.detail_labels["categories"].setText(str(categories))

        # Image count
        images = self.selected_item.get("images", [])
        image_count = len(images) if isinstance(images, list) else 0
        self.detail_labels["image_count"].setText(str(image_count))

        # Data quality (simple calculation)
        quality_score = self.calculate_data_quality(self.selected_item)
        self.detail_labels["data_quality"].setText(f"{quality_score}%")

        # Update raw data display
        self.update_raw_data_display(self.format_combo.currentText())

        # Update images display
        self.update_images_display(images)

    def update_images_display(self, images: List[str]):
        """
        Update the images tab display.

        Args:
            images: List of image URLs or paths
        """
        # Clear existing images
        for i in reversed(range(self.images_layout.count())):
            child = self.images_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if not images:
            self.no_images_label = QLabel("No images available")
            self.no_images_label.setAlignment(Qt.AlignCenter)
            self.no_images_label.setStyleSheet("color: gray; font-style: italic;")
            self.images_layout.addWidget(self.no_images_label)
            return

        # Add image widgets
        for i, image_url in enumerate(images[:10]):  # Limit to 10 images
            image_widget = self.create_image_widget(image_url, i)
            self.images_layout.addWidget(image_widget)

        if len(images) > 10:
            more_label = QLabel(f"... and {len(images) - 10} more images")
            more_label.setAlignment(Qt.AlignCenter)
            more_label.setStyleSheet("color: gray; font-style: italic;")
            self.images_layout.addWidget(more_label)

    def create_image_widget(self, image_url: str, index: int) -> QWidget:
        """
        Create a widget for displaying an image.

        Args:
            image_url: Image URL or path
            index: Image index

        Returns:
            Widget containing image display
        """
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(widget)

        # Image label (placeholder for now)
        image_label = QLabel(f"Image {index + 1}")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(100)
        image_label.setStyleSheet("border: 1px dashed gray; background-color: #f0f0f0;")
        layout.addWidget(image_label)

        # Image URL
        url_label = QLabel(image_url)
        url_label.setWordWrap(True)
        url_label.setStyleSheet("font-size: 10px; color: gray;")
        layout.addWidget(url_label)

        return widget

    def update_status(self):
        """Update status information."""
        total_count = len(self.current_data)
        filtered_count = len(self.filtered_data)

        self.total_items_label.setText(f"Total: {total_count}")
        self.filtered_items_label.setText(f"Filtered: {filtered_count}")

        if filtered_count != total_count:
            self.status_message.setText(
                f"Showing {filtered_count} of {total_count} items"
            )
        else:
            self.status_message.setText("Showing all items")

    def select_item(self, item_data: Dict[str, Any]):
        """
        Select an item and update detail display.

        Args:
            item_data: Selected item data
        """
        self.selected_item = item_data.copy()
        self.update_detail_display()

        # Emit selection signal
        self.item_selected.emit(self.selected_item)

    def calculate_data_quality(self, item: Dict[str, Any]) -> int:
        """
        Calculate data quality score for an item.

        Args:
            item: Item data dictionary

        Returns:
            Quality score (0-100)
        """
        required_fields = ["name", "anime", "description", "url"]
        optional_fields = ["images", "categories", "infobox_data"]

        score = 0
        total_points = len(required_fields) * 25 + len(optional_fields) * 10

        # Check required fields (25 points each)
        for field in required_fields:
            if field in item and item[field]:
                if isinstance(item[field], str) and len(item[field]) > 10:
                    score += 25
                elif not isinstance(item[field], str) and item[field]:
                    score += 25
                else:
                    score += 10  # Partial credit for short content

        # Check optional fields (10 points each)
        for field in optional_fields:
            if field in item and item[field]:
                score += 10

        return min(100, int((score / total_points) * 100))

    def clear_data(self):
        """Clear all data from the viewer."""
        self.current_data = []
        self.filtered_data = []
        self.selected_item = {}

        self.update_table_display()
        self.update_detail_display()
        self.update_status()

        self.logger.info("Data viewer cleared")

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """
        Get currently selected items.

        Returns:
            List of selected item data
        """
        selected_rows = set()
        for item in self.data_table.selectedItems():
            selected_rows.add(item.row())

        return [
            self.filtered_data[row]
            for row in selected_rows
            if row < len(self.filtered_data)
        ]
