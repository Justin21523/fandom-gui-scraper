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
import yaml

from PyQt6.QtWidgets import (
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
    QMessageBox,
    QProgressBar,
    QSpinBox,
    QDateEdit,
    QSizePolicy,
    QFileDialog,
    QDialog,
    QApplication,
)
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    pyqtSlot,
    QTimer,
    QAbstractTableModel,
    QModelIndex,
    QVariant,
    QDate,
)
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QPalette,
    QIcon,
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
        self.sort_order = Qt.SortOrder.AscendingOrder

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

    def data(
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> QVariant:
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

        if role == Qt.ItemDataRole.DisplayRole:
            value = item.get(header, "")

            # Format different data types
            if isinstance(value, list):
                return f"[{len(value)} items]"  # type: ignore
            elif isinstance(value, dict):
                return f"{{object}}"  # type: ignore
            elif isinstance(value, (int, float)):
                return str(value)  # type: ignore
            elif isinstance(value, str):
                # Truncate long text
                return value[:100] + "..." if len(value) > 100 else value  # type: ignore
            else:
                return str(value) if value is not None else ""  # type: ignore

        elif role == Qt.ItemDataRole.ToolTipRole:
            value = item.get(header, "")
            if isinstance(value, (list, dict)):
                return json.dumps(value, indent=2)  # type: ignore
            else:
                return str(value)  # type: ignore

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Alternate row colors
            if index.row() % 2 == 1:
                return QBrush(QColor(248, 248, 248))  # type: ignore

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if header in ["scraped_at", "url"]:
                return Qt.AlignmentFlag.AlignCenter  # type: ignore
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter  # type: ignore

        return QVariant()

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
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
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if 0 <= section < len(self._headers):
                return self._headers[section]  # type: ignore

        elif (
            orientation == Qt.Orientation.Vertical
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return str(section + 1)  # type: ignore

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
            reverse = order == Qt.SortOrder.DescendingOrder

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
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
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
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
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
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)

        # Table header
        header_layout = QHBoxLayout()

        table_title = QLabel("Character Data")
        table_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
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
        self.data_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.data_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.data_table.setSortingEnabled(True)

        # Configure table headers
        self.data_table.horizontalHeader().setStretchLastSection(True)  # type: ignore
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # type: ignore
        self.data_table.verticalHeader().setVisible(False)  # type: ignore

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
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)

        # Detail header
        detail_title = QLabel("Item Details")
        detail_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
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
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

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
        self.no_images_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
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
        """顯示匯出對話框 - 完成 TODO"""
        if not self.filtered_data:
            QMessageBox.information(self, "No Data", "No data available to export.")
            return

        # 建立匯出對話框
        dialog = ExportConfigDialog(self.filtered_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            export_config = dialog.get_configuration()
            self.export_requested.emit(export_config["format"], export_config["data"])

        self.logger.info("Export dialog completed")

    @pyqtSlot()
    def delete_selected(self):
        """刪除選取的項目 - 完成 TODO"""
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 從資料中移除選取項目
            rows_to_remove = sorted(selected_rows, reverse=True)
            for row in rows_to_remove:
                if 0 <= row < len(self.filtered_data):
                    deleted_item = self.filtered_data.pop(row)
                    # 也從原始資料中移除
                    if deleted_item in self.current_data:
                        self.current_data.remove(deleted_item)

            # 更新顯示
            self.update_table_display()
            self.update_status()

            # 清除詳細檢視
            self.selected_item = {}
            self.update_detail_display()

            self.logger.info(f"Deleted {len(selected_rows)} items")

    @pyqtSlot()
    def edit_selected_item(self):
        """編輯選取的項目 - 完成 TODO"""
        if not self.selected_item:
            QMessageBox.information(
                self, "No Selection", "Please select an item to edit."
            )
            return

        # 建立編輯對話框
        dialog = ItemEditDialog(self.selected_item, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_item = dialog.get_updated_item()

            # 更新資料
            self._update_item_data(self.selected_item, updated_item)

            # 重新整理顯示
            self.update_table_display()
            self.update_detail_display()

            # 發出編輯信號
            self.data_edited.emit(updated_item)

        self.logger.info("Edit dialog completed")

    @pyqtSlot()
    def copy_selected_data(self):
        """Copy selected item data to clipboard."""
        if not self.selected_item:
            return

        try:
            # 建立可讀的文字格式
            text_data = self._format_item_for_clipboard(self.selected_item)

            # 複製到剪貼簿
            clipboard = QApplication.clipboard()
            clipboard.setText(text_data)  # type: ignore

            self.status_message.setText("Item data copied to clipboard")
            self.logger.info("Item data copied to clipboard")

        except Exception as e:
            self.logger.error(f"Failed to copy data: {e}")
            QMessageBox.warning(self, "Copy Error", f"Failed to copy data:\n{e}")

    @pyqtSlot()
    def copy_raw_data(self):
        """Copy raw data to clipboard."""
        if not self.selected_item:
            return

        try:
            # 複製 JSON 格式的原始資料
            json_data = json.dumps(self.selected_item, indent=2, ensure_ascii=False)

            clipboard = QApplication.clipboard()
            clipboard.setText(json_data)  # type: ignore

            self.status_message.setText("Raw data copied to clipboard")
            self.logger.info("Raw JSON data copied to clipboard")

        except Exception as e:
            self.logger.error(f"Failed to copy raw data: {e}")
            QMessageBox.warning(self, "Copy Error", f"Failed to copy raw data:\n{e}")

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
                # 實現 YAML 格式化
                try:
                    formatted_data = yaml.dump(
                        self.selected_item,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )
                except Exception:
                    # 如果 YAML 模組不可用，使用 JSON 格式
                    formatted_data = json.dumps(
                        self.selected_item, indent=2, ensure_ascii=False
                    )
            elif format_type == "Python Dict":
                # 格式化為 Python 字典
                formatted_data = self._format_as_python_dict(self.selected_item)
            else:
                formatted_data = str(self.selected_item)

            self.raw_data_text.setPlainText(formatted_data)

        except Exception as e:
            self.logger.error(f"Failed to format data: {e}")
            self.raw_data_text.setPlainText(f"Error formatting data: {e}")

    def _update_item_data(self, old_item: Dict, new_item: Dict):
        """更新項目資料"""
        # 在當前資料中更新
        for i, item in enumerate(self.current_data):
            if item is old_item:
                self.current_data[i] = new_item
                break

        # 在過濾資料中更新
        for i, item in enumerate(self.filtered_data):
            if item is old_item:
                self.filtered_data[i] = new_item
                break

        # 更新選取項目
        self.selected_item = new_item

    def _format_item_for_clipboard(self, item: Dict[str, Any]) -> str:
        """格式化項目資料供剪貼簿使用"""
        lines = []
        lines.append(f"Character: {item.get('name', 'Unknown')}")
        lines.append(f"Anime: {item.get('anime', 'Unknown')}")

        if item.get("description"):
            lines.append(f"Description: {item['description'][:200]}...")

        if item.get("abilities"):
            abilities = item["abilities"]
            if isinstance(abilities, list):
                lines.append(f"Abilities: {', '.join(abilities[:5])}")
            else:
                lines.append(f"Abilities: {abilities}")

        if item.get("images"):
            lines.append(f"Images: {len(item['images'])} found")

        lines.append(f"Scraped: {item.get('scraped_at', 'Unknown')}")

        return "\n".join(lines)

    def _format_as_python_dict(self, data: Any, indent: int = 0) -> str:
        """格式化資料為 Python 字典字串"""
        if isinstance(data, dict):
            if not data:
                return "{}"

            lines = ["{"]
            for key, value in data.items():
                formatted_value = self._format_as_python_dict(value, indent + 1)
                lines.append(f"{'    ' * (indent + 1)}{repr(key)}: {formatted_value},")
            lines.append(f"{'    ' * indent}")
            return "\n".join(lines)

        elif isinstance(data, list):
            if not data:
                return "[]"

            lines = ["["]
            for item in data:
                formatted_item = self._format_as_python_dict(item, indent + 1)
                lines.append(f"{'    ' * (indent + 1)}{formatted_item},")
            lines.append(f"{'    ' * indent}]")
            return "\n".join(lines)

        elif isinstance(data, str):
            return repr(data)
        else:
            return repr(data)

    def _format_cell_value(self, value: Any) -> str:
        """格式化儲存格值供顯示"""
        if isinstance(value, list):
            if len(value) <= 3:
                return ", ".join(str(v) for v in value)
            else:
                return f"{', '.join(str(v) for v in value[:3])} ... (+{len(value)-3})"
        elif isinstance(value, dict):
            return f"Dict ({len(value)} keys)"
        elif isinstance(value, str) and len(value) > 50:
            return value[:47] + "..."
        else:
            return str(value) if value is not None else ""

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
                table_item.setData(Qt.ItemDataRole.UserRole, value)

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
            child = self.images_layout.itemAt(i).widget()  # type: ignore
            if child:
                child.setParent(None)

        if not images:
            self.no_images_label = QLabel("No images available")
            self.no_images_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_images_label.setStyleSheet("color: gray; font-style: italic;")
            self.images_layout.addWidget(self.no_images_label)
            return

        # Add image widgets
        for i, image_url in enumerate(images[:10]):  # Limit to 10 images
            image_widget = self.create_image_widget(image_url, i)
            self.images_layout.addWidget(image_widget)

        if len(images) > 10:
            more_label = QLabel(f"... and {len(images) - 10} more images")
            more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        widget.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QVBoxLayout(widget)

        # Image label (placeholder for now)
        image_label = QLabel(f"Image {index + 1}")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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


class ExportConfigDialog(QDialog):
    """匯出配置對話框"""

    def __init__(self, data: List[Dict], parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Export Configuration")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()

    def setup_ui(self):
        """設置對話框界面"""
        layout = QVBoxLayout(self)

        # 格式選擇
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Export Format:"))

        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "CSV", "Excel"])
        format_layout.addWidget(self.format_combo)

        layout.addLayout(format_layout)

        # 欄位選擇
        fields_group = QGroupBox("Select Fields")
        fields_layout = QVBoxLayout(fields_group)

        # 全選/取消全選
        select_all_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_none_btn = QPushButton("Select None")

        select_all_layout.addWidget(self.select_all_btn)
        select_all_layout.addWidget(self.select_none_btn)
        select_all_layout.addStretch()

        fields_layout.addLayout(select_all_layout)

        # 欄位核取方塊
        self.field_checkboxes = {}
        if self.data:
            all_fields = set()
            for item in self.data:
                all_fields.update(item.keys())

            for field in sorted(all_fields):
                if not field.startswith("_"):
                    checkbox = QCheckBox(field.replace("_", " ").title())
                    checkbox.setChecked(True)
                    self.field_checkboxes[field] = checkbox
                    fields_layout.addWidget(checkbox)

        layout.addWidget(fields_group)

        # 按鈕
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Export")
        self.cancel_btn = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # 連接信號
        self.select_all_btn.clicked.connect(self.select_all_fields)
        self.select_none_btn.clicked.connect(self.select_no_fields)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def select_all_fields(self):
        """全選欄位"""
        for checkbox in self.field_checkboxes.values():
            checkbox.setChecked(True)

    def select_no_fields(self):
        """取消全選欄位"""
        for checkbox in self.field_checkboxes.values():
            checkbox.setChecked(False)

    def get_configuration(self) -> Dict[str, Any]:
        """取得匯出配置"""
        selected_fields = [
            field
            for field, checkbox in self.field_checkboxes.items()
            if checkbox.isChecked()
        ]

        # 過濾資料只包含選取的欄位
        filtered_data = []
        for item in self.data:
            filtered_item = {field: item.get(field) for field in selected_fields}
            filtered_data.append(filtered_item)

        return {
            "format": self.format_combo.currentText(),
            "fields": selected_fields,
            "data": filtered_data,
        }


class ItemEditDialog(QDialog):
    """項目編輯對話框"""

    def __init__(self, item: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.original_item = item.copy()
        self.setWindowTitle("Edit Item")
        self.setModal(True)
        self.resize(500, 600)

        self.field_editors = {}
        self.setup_ui()

    def setup_ui(self):
        """設置編輯對話框界面"""
        layout = QVBoxLayout(self)

        # 滾動區域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 為每個欄位建立編輯器
        for field, value in self.original_item.items():
            if field.startswith("_"):
                continue

            field_frame = QFrame()
            field_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            field_layout = QVBoxLayout(field_frame)

            # 欄位標籤
            label = QLabel(field.replace("_", " ").title() + ":")
            label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            field_layout.addWidget(label)

            # 根據值類型建立適當的編輯器
            editor = self._create_editor_for_value(value)
            self.field_editors[field] = editor
            field_layout.addWidget(editor)

            scroll_layout.addWidget(field_frame)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 按鈕
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Changes")
        self.cancel_btn = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # 連接信號
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _create_editor_for_value(self, value: Any) -> QWidget:
        """根據值類型建立編輯器"""
        if isinstance(value, str):
            if len(value) > 100:
                # 多行文字編輯器
                editor = QTextEdit()
                editor.setPlainText(value)
                editor.setMaximumHeight(150)
                return editor
            else:
                # 單行文字編輯器
                editor = QLineEdit()
                editor.setText(value)
                return editor

        elif isinstance(value, (int, float)):
            # 數字編輯器
            editor = QLineEdit()
            editor.setText(str(value))
            return editor

        elif isinstance(value, list):
            # 列表編輯器（以換行分隔的文字）
            editor = QTextEdit()
            if all(isinstance(item, str) for item in value):
                editor.setPlainText("\n".join(value))
            else:
                editor.setPlainText(json.dumps(value, indent=2, ensure_ascii=False))
            editor.setMaximumHeight(150)
            return editor

        elif isinstance(value, dict):
            # 字典編輯器（JSON 格式）
            editor = QTextEdit()
            editor.setPlainText(json.dumps(value, indent=2, ensure_ascii=False))
            editor.setMaximumHeight(200)
            return editor

        else:
            # 預設文字編輯器
            editor = QLineEdit()
            editor.setText(str(value))
            return editor

    def get_updated_item(self) -> Dict[str, Any]:
        """取得更新後的項目資料"""
        updated_item = self.original_item.copy()

        for field, editor in self.field_editors.items():
            original_value = self.original_item[field]

            try:
                if isinstance(editor, QTextEdit):
                    new_text = editor.toPlainText().strip()

                    if isinstance(original_value, list):
                        if new_text.startswith("[") or new_text.startswith("{"):
                            # JSON 格式
                            updated_item[field] = json.loads(new_text)
                        else:
                            # 換行分隔的列表
                            updated_item[field] = [
                                line.strip()
                                for line in new_text.split("\n")
                                if line.strip()
                            ]
                    elif isinstance(original_value, dict):
                        updated_item[field] = json.loads(new_text)
                    else:
                        updated_item[field] = new_text

                elif isinstance(editor, QLineEdit):
                    new_text = editor.text().strip()

                    if isinstance(original_value, (int, float)):
                        if isinstance(original_value, int):
                            updated_item[field] = int(new_text) if new_text else 0
                        else:
                            updated_item[field] = float(new_text) if new_text else 0.0
                    else:
                        updated_item[field] = new_text

            except (json.JSONDecodeError, ValueError) as e:
                # 如果轉換失敗，保持原值
                QMessageBox.warning(
                    self, "Invalid Value", f"Invalid value for field '{field}': {e}"
                )
                continue

        return updated_item


# 其他輔助函數和類別


def create_controls_section(self) -> QFrame:
    """建立控制面板 - 完成實現"""
    frame = QFrame()
    frame.setFrameStyle(QFrame.Shape.StyledPanel)
    layout = QHBoxLayout(frame)

    # 搜尋框
    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText("Search characters...")
    self.search_input.textChanged.connect(self._on_search_text_changed)
    layout.addWidget(QLabel("Search:"))
    layout.addWidget(self.search_input)

    # 過濾欄位選擇
    self.filter_column_combo = QComboBox()
    self.filter_column_combo.addItem("All Columns", "")
    self.filter_column_combo.currentTextChanged.connect(self.apply_filters)
    layout.addWidget(QLabel("Filter by:"))
    layout.addWidget(self.filter_column_combo)

    # 按鈕
    self.clear_search_btn = QPushButton("Clear")
    self.clear_search_btn.clicked.connect(self.clear_filters)
    layout.addWidget(self.clear_search_btn)

    self.refresh_btn = QPushButton("Refresh")
    self.refresh_btn.clicked.connect(self.refresh_data)
    layout.addWidget(self.refresh_btn)

    self.export_btn = QPushButton("Export")
    self.export_btn.clicked.connect(self.show_export_dialog)
    layout.addWidget(self.export_btn)

    layout.addStretch()

    return frame


def create_table_section(self) -> QFrame:
    """建立表格區域 - 完成實現"""
    frame = QFrame()
    layout = QVBoxLayout(frame)

    # 表格
    self.data_table = QTableWidget()
    self.data_table.setAlternatingRowColors(True)
    self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.data_table.setSortingEnabled(True)
    self.data_table.itemSelectionChanged.connect(self._on_table_selection_changed)

    # 設定表格右鍵選單
    self.data_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.data_table.customContextMenuRequested.connect(self._show_table_context_menu)

    layout.addWidget(self.data_table)

    return frame


def create_detail_section(self) -> QFrame:
    """建立詳細檢視區域 - 完成實現"""
    frame = QFrame()
    layout = QVBoxLayout(frame)

    # 詳細資訊標題
    detail_label = QLabel("Item Details")
    detail_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
    layout.addWidget(detail_label)

    # 基本資訊區域
    self.basic_info_text = QTextEdit()
    self.basic_info_text.setMaximumHeight(200)
    self.basic_info_text.setReadOnly(True)
    layout.addWidget(self.basic_info_text)

    # 原始資料格式選擇
    format_layout = QHBoxLayout()
    format_layout.addWidget(QLabel("Raw Data Format:"))

    self.raw_format_combo = QComboBox()
    self.raw_format_combo.addItems(["JSON", "YAML", "Python Dict"])
    self.raw_format_combo.currentTextChanged.connect(self.update_raw_data_display)
    format_layout.addWidget(self.raw_format_combo)
    format_layout.addStretch()

    layout.addLayout(format_layout)

    # 原始資料顯示
    self.raw_data_text = QTextEdit()
    self.raw_data_text.setReadOnly(True)
    self.raw_data_text.setFont(QFont("Courier", 9))
    layout.addWidget(self.raw_data_text)

    # 操作按鈕
    button_layout = QHBoxLayout()

    self.edit_btn = QPushButton("Edit Item")
    self.edit_btn.clicked.connect(self.edit_selected_item)
    button_layout.addWidget(self.edit_btn)

    self.copy_btn = QPushButton("Copy Summary")
    self.copy_btn.clicked.connect(self.copy_selected_data)
    button_layout.addWidget(self.copy_btn)

    self.copy_raw_btn = QPushButton("Copy Raw")
    self.copy_raw_btn.clicked.connect(self.copy_raw_data)
    button_layout.addWidget(self.copy_raw_btn)

    layout.addLayout(button_layout)

    return frame


def create_status_section(self) -> QFrame:
    """建立狀態列 - 完成實現"""
    frame = QFrame()
    frame.setMaximumHeight(30)
    layout = QHBoxLayout(frame)

    self.status_message = QLabel("Ready")
    layout.addWidget(self.status_message)

    layout.addStretch()

    self.item_count_label = QLabel("Items: 0")
    layout.addWidget(self.item_count_label)

    return frame


def _on_search_text_changed(self, text: str):
    """搜尋文字變更處理"""
    # 延遲搜尋以避免過度頻繁的更新
    self.search_timer.stop()
    self.search_timer.start(300)  # 300ms 延遲


def _on_table_selection_changed(self):
    """表格選擇變更處理"""
    selected_items = self.data_table.selectedItems()
    if selected_items:
        # 取得選取的項目資料
        row = selected_items[0].row()
        item_data = self.data_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if item_data:
            self.selected_item = item_data
            self.update_detail_display()
            self.item_selected.emit(item_data)


def _show_table_context_menu(self, position):
    """顯示表格右鍵選單"""
    if not self.data_table.itemAt(position):
        return

    menu = QMenu(self)

    edit_action = menu.addAction("Edit Item")
    edit_action.triggered.connect(self.edit_selected_item)  # type: ignore

    menu.addSeparator()

    copy_action = menu.addAction("Copy Summary")
    copy_action.triggered.connect(self.copy_selected_data)  # type: ignore

    copy_raw_action = menu.addAction("Copy Raw Data")
    copy_raw_action.triggered.connect(self.copy_raw_data)  # type: ignore

    menu.addSeparator()

    delete_action = menu.addAction("Delete Item")
    delete_action.triggered.connect(self.delete_selected)  # type: ignore

    menu.exec(self.data_table.mapToGlobal(position))


def update_detail_display(self):
    """更新詳細資訊顯示"""
    if not self.selected_item:
        self.basic_info_text.clear()
        self.raw_data_text.clear()
        return

    # 更新基本資訊
    basic_info = []

    # 主要欄位
    main_fields = ["name", "anime", "description", "abilities"]
    for field in main_fields:
        value = self.selected_item.get(field)
        if value:
            if isinstance(value, str) and len(value) > 200:
                basic_info.append(f"{field.title()}: {value[:200]}...")
            elif isinstance(value, list) and len(value) > 5:
                basic_info.append(
                    f"{field.title()}: {', '.join(map(str, value[:5]))} ... (+{len(value)-5})"
                )
            else:
                basic_info.append(f"{field.title()}: {value}")

    # 統計資訊
    stats = []
    if "images" in self.selected_item:
        stats.append(f"Images: {len(self.selected_item['images'])}")
    if "scraped_at" in self.selected_item:
        stats.append(f"Scraped: {self.selected_item['scraped_at']}")

    if stats:
        basic_info.append("\nStatistics:")
        basic_info.extend(stats)

    self.basic_info_text.setPlainText("\n".join(basic_info))

    # 更新原始資料顯示
    current_format = self.raw_format_combo.currentText()
    self.update_raw_data_display(current_format)


def update_status(self):
    """更新狀態顯示"""
    total_items = len(self.current_data)
    filtered_items = len(self.filtered_data)

    if total_items == filtered_items:
        self.item_count_label.setText(f"Items: {total_items}")
    else:
        self.item_count_label.setText(f"Items: {filtered_items} / {total_items}")

    if self.search_input.text():
        self.status_message.setText(f"Filtered by: '{self.search_input.text()}'")
    else:
        self.status_message.setText("Ready")


def apply_filters(self):
    """套用搜尋和過濾"""
    search_text = self.search_input.text().lower()
    filter_column = self.filter_column_combo.currentData() or ""

    if not search_text:
        self.filtered_data = self.current_data.copy()
    else:
        self.filtered_data = []

        for item in self.current_data:
            match_found = False

            if filter_column:
                # 只在指定欄位搜尋
                value = item.get(filter_column, "")
                if search_text in str(value).lower():
                    match_found = True
            else:
                # 在所有欄位搜尋
                for key, value in item.items():
                    if search_text in str(value).lower():
                        match_found = True
                        break

            if match_found:
                self.filtered_data.append(item)

    # 更新顯示
    self.update_table_display()
    self.update_status()


def setup_connections(self):
    """設置信號連接"""
    # 搜尋和過濾
    self.search_input.textChanged.connect(self._on_search_text_changed)
    self.filter_column_combo.currentTextChanged.connect(self.apply_filters)

    # 按鈕
    self.clear_search_btn.clicked.connect(self.clear_filters)
    self.refresh_btn.clicked.connect(self.refresh_data)
    self.export_btn.clicked.connect(self.show_export_dialog)

    # 表格
    self.data_table.itemSelectionChanged.connect(self._on_table_selection_changed)

    # 詳細檢視
    self.raw_format_combo.currentTextChanged.connect(self.update_raw_data_display)
