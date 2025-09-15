# gui/widgets/tag_manager.py
"""
Tag management widget for organizing and categorizing scraped data.

This module provides comprehensive tag management functionality including
tag creation, editing, categorization, and bulk operations.
"""

import json
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QTextEdit,
    QSplitter,
    QFrame,
    QMenu,
    QAction,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QCompleter,
    QInputDialog,
    QColorDialog,
    QToolButton,
    QButtonGroup,
    QRadioButton,
    QScrollArea,
    QDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QStringListModel, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QCursor, QPixmap

from utils.logger import get_logger


class TagManager(QWidget):
    """
    Comprehensive tag management widget for anime data organization.

    Features:
    - Tag creation and editing
    - Hierarchical tag categories
    - Bulk tag operations
    - Tag statistics and analytics
    - Tag import/export
    - Color coding and organization
    """

    # Custom signals
    tags_changed = pyqtSignal(list)  # Updated tag list
    tag_selected = pyqtSignal(str)  # Selected tag
    tag_applied = pyqtSignal(str, list)  # Tag applied to items
    tag_removed = pyqtSignal(str, list)  # Tag removed from items
    category_changed = pyqtSignal(str, str)  # Tag, new category

    def __init__(self, parent=None):
        """Initialize tag manager widget."""
        super().__init__(parent)

        self.logger = get_logger(self.__class__.__name__)

        # Data
        self.all_tags = set()
        self.tag_categories = {}
        self.tag_colors = {}
        self.tag_descriptions = {}
        self.tag_usage_count = Counter()
        self.selected_items = []

        # Tag hierarchy
        self.tag_hierarchy = defaultdict(set)  # parent -> children
        self.tag_parents = {}  # child -> parent

        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.load_tag_data()

        self.logger.info("Tag manager widget initialized")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

        # Left panel - tag management
        left_panel = self._create_tag_management_panel()
        main_splitter.addWidget(left_panel)

        # Right panel - tag operations
        right_panel = self._create_operations_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter sizes
        main_splitter.setSizes([400, 300])

        # Status bar
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

    def _create_tag_management_panel(self) -> QWidget:
        """Create tag management panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # All tags tab
        all_tags_tab = self._create_all_tags_tab()
        tab_widget.addTab(all_tags_tab, "All Tags")

        # Categories tab
        categories_tab = self._create_categories_tab()
        tab_widget.addTab(categories_tab, "Categories")

        # Statistics tab
        stats_tab = self._create_statistics_tab()
        tab_widget.addTab(stats_tab, "Statistics")

        return panel

    def _create_all_tags_tab(self) -> QWidget:
        """Create all tags tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search and filter section
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout(search_group)

        # Search input
        search_input_layout = QHBoxLayout()
        self.tag_search_input = QLineEdit()
        self.tag_search_input.setPlaceholderText("Search tags...")
        self.clear_search_btn = QPushButton("Clear")

        search_input_layout.addWidget(self.tag_search_input)
        search_input_layout.addWidget(self.clear_search_btn)
        search_layout.addLayout(search_input_layout)

        # Filter options
        filter_layout = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")

        self.usage_filter = QComboBox()
        self.usage_filter.addItems(
            ["All Tags", "Frequently Used", "Rarely Used", "Unused"]
        )

        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("Usage:"))
        filter_layout.addWidget(self.usage_filter)

        search_layout.addLayout(filter_layout)
        layout.addWidget(search_group)

        # Tags list
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)

        self.tags_list = QListWidget()
        self.tags_list.setAlternatingRowColors(True)
        self.tags_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        tags_layout.addWidget(self.tags_list)

        # Tag actions
        tag_actions_layout = QHBoxLayout()
        self.add_tag_btn = QPushButton("Add Tag")
        self.edit_tag_btn = QPushButton("Edit")
        self.delete_tag_btn = QPushButton("Delete")
        self.merge_tags_btn = QPushButton("Merge")

        tag_actions_layout.addWidget(self.add_tag_btn)
        tag_actions_layout.addWidget(self.edit_tag_btn)
        tag_actions_layout.addWidget(self.delete_tag_btn)
        tag_actions_layout.addWidget(self.merge_tags_btn)

        tags_layout.addLayout(tag_actions_layout)
        layout.addWidget(tags_group)

        return tab

    def _create_categories_tab(self) -> QWidget:
        """Create categories tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Category tree
        tree_group = QGroupBox("Tag Categories")
        tree_layout = QVBoxLayout(tree_group)

        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabels(["Category", "Tags", "Color"])
        self.category_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        tree_layout.addWidget(self.category_tree)

        # Category actions
        category_actions_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("Add Category")
        self.edit_category_btn = QPushButton("Edit")
        self.delete_category_btn = QPushButton("Delete Category")
        self.set_color_btn = QPushButton("Set Color")

        category_actions_layout.addWidget(self.add_category_btn)
        category_actions_layout.addWidget(self.edit_category_btn)
        category_actions_layout.addWidget(self.delete_category_btn)
        category_actions_layout.addWidget(self.set_color_btn)

        tree_layout.addLayout(category_actions_layout)
        layout.addWidget(tree_group)

        # Quick category assignment
        assignment_group = QGroupBox("Quick Assignment")
        assignment_layout = QFormLayout(assignment_group)

        self.selected_tag_label = QLabel("No tag selected")
        assignment_layout.addRow("Selected Tag:", self.selected_tag_label)

        self.assign_category_combo = QComboBox()
        self.assign_category_combo.addItem("Uncategorized")
        assignment_layout.addRow("Assign to Category:", self.assign_category_combo)

        self.assign_btn = QPushButton("Assign")
        assignment_layout.addRow(self.assign_btn)

        layout.addWidget(assignment_group)

        return tab

    def _create_statistics_tab(self) -> QWidget:
        """Create statistics tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Usage statistics
        stats_group = QGroupBox("Usage Statistics")
        stats_layout = QVBoxLayout(stats_group)

        # Summary labels
        summary_layout = QFormLayout()
        self.total_tags_label = QLabel("0")
        self.total_categories_label = QLabel("0")
        self.avg_tags_per_item_label = QLabel("0.0")
        self.most_used_tag_label = QLabel("None")

        summary_layout.addRow("Total Tags:", self.total_tags_label)
        summary_layout.addRow("Categories:", self.total_categories_label)
        summary_layout.addRow("Avg Tags/Item:", self.avg_tags_per_item_label)
        summary_layout.addRow("Most Used Tag:", self.most_used_tag_label)

        stats_layout.addLayout(summary_layout)

        # Top tags list
        top_tags_layout = QVBoxLayout()
        top_tags_layout.addWidget(QLabel("Most Frequently Used Tags:"))

        self.top_tags_list = QListWidget()
        self.top_tags_list.setMaximumHeight(150)
        top_tags_layout.addWidget(self.top_tags_list)

        stats_layout.addLayout(top_tags_layout)
        layout.addWidget(stats_group)

        # Cleanup suggestions
        cleanup_group = QGroupBox("Cleanup Suggestions")
        cleanup_layout = QVBoxLayout(cleanup_group)

        self.cleanup_list = QListWidget()
        self.cleanup_list.setMaximumHeight(100)
        cleanup_layout.addWidget(self.cleanup_list)

        cleanup_actions_layout = QHBoxLayout()
        self.auto_cleanup_btn = QPushButton("Auto Cleanup")
        self.refresh_suggestions_btn = QPushButton("Refresh")

        cleanup_actions_layout.addWidget(self.auto_cleanup_btn)
        cleanup_actions_layout.addWidget(self.refresh_suggestions_btn)
        cleanup_actions_layout.addStretch()

        cleanup_layout.addLayout(cleanup_actions_layout)
        layout.addWidget(cleanup_group)

        layout.addStretch()
        return tab

    def _create_operations_panel(self) -> QWidget:
        """Create tag operations panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Selected items info
        selection_group = QGroupBox("Selected Items")
        selection_layout = QVBoxLayout(selection_group)

        self.selected_items_label = QLabel("No items selected")
        selection_layout.addWidget(self.selected_items_label)

        # Current tags for selected items
        self.current_tags_list = QListWidget()
        self.current_tags_list.setMaximumHeight(100)
        selection_layout.addWidget(QLabel("Current Tags:"))
        selection_layout.addWidget(self.current_tags_list)

        layout.addWidget(selection_group)

        # Tag operations
        operations_group = QGroupBox("Tag Operations")
        operations_layout = QVBoxLayout(operations_group)

        # Add tags
        add_tags_layout = QHBoxLayout()
        self.add_tags_input = QLineEdit()
        self.add_tags_input.setPlaceholderText("Enter tags (comma-separated)...")
        self.apply_tags_btn = QPushButton("Apply Tags")

        add_tags_layout.addWidget(self.add_tags_input)
        add_tags_layout.addWidget(self.apply_tags_btn)
        operations_layout.addLayout(add_tags_layout)

        # Tag suggestions
        suggestions_layout = QVBoxLayout()
        suggestions_layout.addWidget(QLabel("Suggested Tags:"))

        self.suggested_tags_list = QListWidget()
        self.suggested_tags_list.setMaximumHeight(80)
        self.suggested_tags_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection
        )
        suggestions_layout.addWidget(self.suggested_tags_list)

        operations_layout.addLayout(suggestions_layout)

        # Remove tags
        remove_layout = QHBoxLayout()
        self.remove_selected_tags_btn = QPushButton("Remove Selected")
        self.remove_all_tags_btn = QPushButton("Remove All")

        remove_layout.addWidget(self.remove_selected_tags_btn)
        remove_layout.addWidget(self.remove_all_tags_btn)
        operations_layout.addLayout(remove_layout)

        layout.addWidget(operations_group)

        # Bulk operations
        bulk_group = QGroupBox("Bulk Operations")
        bulk_layout = QVBoxLayout(bulk_group)

        # Replace tags
        replace_layout = QFormLayout()
        self.replace_from_input = QLineEdit()
        self.replace_to_input = QLineEdit()
        self.replace_tags_btn = QPushButton("Replace")

        replace_layout.addRow("Replace:", self.replace_from_input)
        replace_layout.addRow("With:", self.replace_to_input)
        replace_layout.addRow(self.replace_tags_btn)

        bulk_layout.addLayout(replace_layout)

        # Batch operations
        batch_layout = QHBoxLayout()
        self.normalize_tags_btn = QPushButton("Normalize Tags")
        self.deduplicate_tags_btn = QPushButton("Remove Duplicates")

        batch_layout.addWidget(self.normalize_tags_btn)
        batch_layout.addWidget(self.deduplicate_tags_btn)

        bulk_layout.addLayout(batch_layout)
        layout.addWidget(bulk_group)

        # Import/Export
        import_export_group = QGroupBox("Import/Export")
        import_export_layout = QHBoxLayout(import_export_group)

        self.import_tags_btn = QPushButton("Import Tags")
        self.export_tags_btn = QPushButton("Export Tags")
        self.backup_tags_btn = QPushButton("Backup")

        import_export_layout.addWidget(self.import_tags_btn)
        import_export_layout.addWidget(self.export_tags_btn)
        import_export_layout.addWidget(self.backup_tags_btn)

        layout.addWidget(import_export_group)

        layout.addStretch()
        return panel

    def _create_status_bar(self) -> QWidget:
        """Create status bar."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("Ready")
        self.tag_count_label = QLabel("Tags: 0")
        self.operation_progress = QProgressBar()
        self.operation_progress.setVisible(False)
        self.operation_progress.setMaximumWidth(150)

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.tag_count_label)
        layout.addWidget(self.operation_progress)

        return frame

    def setup_connections(self):
        """Set up signal connections."""
        # Search and filter
        self.tag_search_input.textChanged.connect(self._filter_tags)
        self.clear_search_btn.clicked.connect(self._clear_search)
        self.category_filter.currentTextChanged.connect(self._filter_tags)
        self.usage_filter.currentTextChanged.connect(self._filter_tags)

        # Tags list
        self.tags_list.itemSelectionChanged.connect(self._on_tag_selection_changed)
        self.tags_list.itemDoubleClicked.connect(self._edit_selected_tag)

        # Tag actions
        self.add_tag_btn.clicked.connect(self.add_new_tag)
        self.edit_tag_btn.clicked.connect(self._edit_selected_tag)
        self.delete_tag_btn.clicked.connect(self._delete_selected_tags)
        self.merge_tags_btn.clicked.connect(self._merge_selected_tags)

        # Category tree
        self.category_tree.itemSelectionChanged.connect(
            self._on_category_selection_changed
        )
        self.category_tree.itemChanged.connect(self._on_category_item_changed)

        # Category actions
        self.add_category_btn.clicked.connect(self._add_category)
        self.edit_category_btn.clicked.connect(self._edit_category)
        self.delete_category_btn.clicked.connect(self._delete_category)
        self.set_color_btn.clicked.connect(self._set_category_color)

        # Quick assignment
        self.assign_btn.clicked.connect(self._assign_tag_to_category)

        # Tag operations
        self.apply_tags_btn.clicked.connect(self._apply_tags_to_selected)
        self.suggested_tags_list.itemDoubleClicked.connect(self._add_suggested_tag)
        self.remove_selected_tags_btn.clicked.connect(self._remove_selected_tags)
        self.remove_all_tags_btn.clicked.connect(self._remove_all_tags)

        # Bulk operations
        self.replace_tags_btn.clicked.connect(self._replace_tags)
        self.normalize_tags_btn.clicked.connect(self._normalize_tags)
        self.deduplicate_tags_btn.clicked.connect(self._deduplicate_tags)

        # Import/Export
        self.import_tags_btn.clicked.connect(self.import_tags)
        self.export_tags_btn.clicked.connect(self.export_tags)
        self.backup_tags_btn.clicked.connect(self._backup_tags)

        # Statistics
        self.auto_cleanup_btn.clicked.connect(self._auto_cleanup)
        self.refresh_suggestions_btn.clicked.connect(self._refresh_cleanup_suggestions)

        # Auto-complete for tag input
        self.tag_completer = QCompleter()
        self.add_tags_input.setCompleter(self.tag_completer)

    def set_selected_items(self, items: List[Dict[str, Any]]):
        """Set currently selected items for tag operations."""
        self.selected_items = items
        count = len(items)

        if count == 0:
            self.selected_items_label.setText("No items selected")
            self.current_tags_list.clear()
            self.suggested_tags_list.clear()
        elif count == 1:
            self.selected_items_label.setText(
                f"1 item selected: {items[0].get('name', 'Unknown')}"
            )
            self._update_current_tags_display()
            self._update_tag_suggestions()
        else:
            self.selected_items_label.setText(f"{count} items selected")
            self._update_current_tags_display()
            self._update_tag_suggestions()

    def update_tag_data(self, data: List[Dict[str, Any]]):
        """Update tag data from scraped items."""
        self.all_tags.clear()
        self.tag_usage_count.clear()

        # Extract all tags from data
        for item in data:
            tags = item.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            elif not isinstance(tags, list):
                continue

            for tag in tags:
                if tag:
                    self.all_tags.add(tag)
                    self.tag_usage_count[tag] += 1

        # Update UI
        self._update_tags_display()
        self._update_category_filter()
        self._update_statistics()
        self._update_tag_completer()

        self.logger.info(f"Updated tag data: {len(self.all_tags)} unique tags")

    def add_new_tag(self):
        """Add a new tag."""
        dialog = TagEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tag_data = dialog.get_tag_data()
            tag_name = tag_data["name"]

            if tag_name in self.all_tags:
                QMessageBox.warning(
                    self, "Tag Exists", f"Tag '{tag_name}' already exists."
                )
                return

            # Add tag
            self.all_tags.add(tag_name)
            self.tag_categories[tag_name] = tag_data.get("category", "Uncategorized")
            self.tag_colors[tag_name] = tag_data.get("color", "#000000")
            self.tag_descriptions[tag_name] = tag_data.get("description", "")

            self._update_tags_display()
            self._update_statistics()
            self.tags_changed.emit(list(self.all_tags))

            self.logger.info(f"Added new tag: {tag_name}")

    def get_all_tags(self) -> List[str]:
        """Get all available tags."""
        return sorted(list(self.all_tags))

    def get_tag_categories(self) -> Dict[str, str]:
        """Get tag category mappings."""
        return self.tag_categories.copy()

    def get_tags_by_category(self, category: str) -> List[str]:
        """Get all tags in a specific category."""
        return [tag for tag, cat in self.tag_categories.items() if cat == category]

    def load_tag_data(self):
        """Load tag data from configuration file."""
        try:
            config_dir = Path.home() / ".fandom_scraper"
            tag_file = config_dir / "tag_data.json"

            if tag_file.exists():
                with open(tag_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.tag_categories = data.get("categories", {})
                self.tag_colors = data.get("colors", {})
                self.tag_descriptions = data.get("descriptions", {})

                # Rebuild all_tags set
                self.all_tags = set(self.tag_categories.keys())

                self._update_tags_display()
                self._update_category_tree()
                self._update_statistics()

                self.logger.info(f"Loaded tag data: {len(self.all_tags)} tags")

        except Exception as e:
            self.logger.warning(f"Failed to load tag data: {e}")

    def save_tag_data(self):
        """Save tag data to configuration file."""
        try:
            config_dir = Path.home() / ".fandom_scraper"
            config_dir.mkdir(exist_ok=True)

            tag_file = config_dir / "tag_data.json"

            data = {
                "categories": self.tag_categories,
                "colors": self.tag_colors,
                "descriptions": self.tag_descriptions,
                "last_updated": datetime.now().isoformat(),
            }

            with open(tag_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            self.logger.info("Tag data saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save tag data: {e}")

    def _update_tags_display(self):
        """Update tags list display."""
        search_text = self.tag_search_input.text().lower()
        category_filter = self.category_filter.currentText()
        usage_filter = self.usage_filter.currentText()

        self.tags_list.clear()

        # Filter tags
        filtered_tags = []
        for tag in sorted(self.all_tags):
            # Search filter
            if search_text and search_text not in tag.lower():
                continue

            # Category filter
            if category_filter != "All Categories":
                tag_category = self.tag_categories.get(tag, "Uncategorized")
                if tag_category != category_filter:
                    continue

            # Usage filter
            usage_count = self.tag_usage_count.get(tag, 0)
            if usage_filter == "Frequently Used" and usage_count < 5:
                continue
            elif usage_filter == "Rarely Used" and usage_count >= 5:
                continue
            elif usage_filter == "Unused" and usage_count > 0:
                continue

            filtered_tags.append(tag)

        # Add tags to list
        for tag in filtered_tags:
            item = QListWidgetItem(tag)

            # Set tooltip with tag info
            usage_count = self.tag_usage_count.get(tag, 0)
            category = self.tag_categories.get(tag, "Uncategorized")
            description = self.tag_descriptions.get(tag, "")

            tooltip = f"Tag: {tag}\nCategory: {category}\nUsed: {usage_count} times"
            if description:
                tooltip += f"\nDescription: {description}"
            item.setToolTip(tooltip)

            # Set color if available
            color = self.tag_colors.get(tag)
            if color:
                item.setForeground(QColor(color))

            self.tags_list.addItem(item)

        self.tag_count_label.setText(f"Tags: {len(filtered_tags)}")

    def _update_category_tree(self):
        """Update category tree display."""
        self.category_tree.clear()

        # Group tags by category
        categories = defaultdict(list)
        for tag, category in self.tag_categories.items():
            categories[category].append(tag)

        # Add uncategorized tags
        uncategorized = []
        for tag in self.all_tags:
            if tag not in self.tag_categories:
                uncategorized.append(tag)
        if uncategorized:
            categories["Uncategorized"] = uncategorized

        # Build tree
        for category, tags in sorted(categories.items()):
            category_item = QTreeWidgetItem([category, str(len(tags)), ""])
            category_item.setData(
                0, Qt.ItemDataRole.UserRole, {"type": "category", "name": category}
            )

            # Set category color if available
            category_color = self.tag_colors.get(f"category_{category}")
            if category_color:
                category_item.setBackground(2, QColor(category_color))

            for tag in sorted(tags):
                tag_item = QTreeWidgetItem(
                    [tag, str(self.tag_usage_count.get(tag, 0)), ""]
                )
                tag_item.setData(
                    0, Qt.ItemDataRole.UserRole, {"type": "tag", "name": tag}
                )

                # Set tag color
                tag_color = self.tag_colors.get(tag)
                if tag_color:
                    tag_item.setForeground(0, QColor(tag_color))

                category_item.addChild(tag_item)

            self.category_tree.addTopLevelItem(category_item)

        # Expand all categories
        self.category_tree.expandAll()

        # Resize columns
        for i in range(3):
            self.category_tree.resizeColumnToContents(i)

    def _update_category_filter(self):
        """Update category filter options."""
        current_category = self.category_filter.currentText()

        self.category_filter.clear()
        self.category_filter.addItem("All Categories")

        # Get unique categories
        categories = set(self.tag_categories.values())
        categories.add("Uncategorized")

        for category in sorted(categories):
            self.category_filter.addItem(category)

        # Restore selection
        index = self.category_filter.findText(current_category)
        if index >= 0:
            self.category_filter.setCurrentIndex(index)

        # Update assignment combo
        self.assign_category_combo.clear()
        self.assign_category_combo.addItem("Uncategorized")
        for category in sorted(categories):
            if category != "Uncategorized":
                self.assign_category_combo.addItem(category)

    def _update_statistics(self):
        """Update statistics display."""
        total_tags = len(self.all_tags)
        total_categories = (
            len(set(self.tag_categories.values())) if self.tag_categories else 0
        )

        # Calculate average tags per item
        total_usage = sum(self.tag_usage_count.values())
        avg_tags = total_usage / len(self.selected_items) if self.selected_items else 0

        # Most used tag
        most_used = self.tag_usage_count.most_common(1)
        most_used_tag = (
            f"{most_used[0][0]} ({most_used[0][1]})" if most_used else "None"
        )

        # Update labels
        self.total_tags_label.setText(str(total_tags))
        self.total_categories_label.setText(str(total_categories))
        self.avg_tags_per_item_label.setText(f"{avg_tags:.1f}")
        self.most_used_tag_label.setText(most_used_tag)

        # Update top tags list
        self.top_tags_list.clear()
        for tag, count in self.tag_usage_count.most_common(10):
            item = QListWidgetItem(f"{tag} ({count})")
            self.top_tags_list.addItem(item)

        # Update cleanup suggestions
        self._refresh_cleanup_suggestions()

    def _update_current_tags_display(self):
        """Update current tags display for selected items."""
        self.current_tags_list.clear()

        if not self.selected_items:
            return

        # Get common tags across all selected items
        if len(self.selected_items) == 1:
            # Single item - show all tags
            tags = self.selected_items[0].get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        else:
            # Multiple items - show common tags
            tag_sets = []
            for item in self.selected_items:
                tags = item.get("tags", [])
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
                tag_sets.append(set(tags))

            if tag_sets:
                tags = list(set.intersection(*tag_sets))
            else:
                tags = []

        for tag in sorted(tags):
            item = QListWidgetItem(tag)
            category = self.tag_categories.get(tag, "Uncategorized")
            item.setToolTip(f"Category: {category}")

            # Set color
            color = self.tag_colors.get(tag)
            if color:
                item.setForeground(QColor(color))

            self.current_tags_list.addItem(item)

    def _update_tag_suggestions(self):
        """Update tag suggestions based on selected items."""
        self.suggested_tags_list.clear()

        if not self.selected_items:
            return

        # Suggest tags based on item properties
        suggestions = set()

        for item in self.selected_items:
            # Suggest based on anime name
            anime_name = item.get("anime_name", "")
            if anime_name:
                suggestions.add(anime_name.lower().replace(" ", "_"))

            # Suggest based on character type/status
            char_type = item.get("type", "")
            if char_type:
                suggestions.add(char_type.lower())

            status = item.get("status", "")
            if status:
                suggestions.add(status.lower())

            # Suggest based on occupation/role
            occupation = item.get("occupation", "")
            if occupation:
                for occ in occupation.split(","):
                    suggestions.add(occ.strip().lower())

        # Add frequently used tags as suggestions
        common_tags = [tag for tag, count in self.tag_usage_count.most_common(20)]
        suggestions.update(common_tags[:10])

        # Remove tags that are already applied
        current_tags = set()
        if len(self.selected_items) == 1:
            tags = self.selected_items[0].get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            current_tags = set(tags)

        suggestions -= current_tags

        # Add to list
        for suggestion in sorted(suggestions)[:15]:  # Limit to 15 suggestions
            if suggestion:  # Skip empty suggestions
                item = QListWidgetItem(suggestion)
                item.setToolTip("Double-click to add this tag")
                self.suggested_tags_list.addItem(item)

    def _update_tag_completer(self):
        """Update tag auto-completer."""
        tag_list = sorted(list(self.all_tags))
        model = QStringListModel(tag_list)
        self.tag_completer.setModel(model)

    # Event handlers and slot methods
    def _filter_tags(self):
        """Filter tags based on search and filter criteria."""
        self._update_tags_display()

    def _clear_search(self):
        """Clear search input."""
        self.tag_search_input.clear()

    def _on_tag_selection_changed(self):
        """Handle tag selection changes."""
        selected_items = self.tags_list.selectedItems()
        if selected_items:
            tag_name = selected_items[0].text()
            self.selected_tag_label.setText(tag_name)
            self.tag_selected.emit(tag_name)
        else:
            self.selected_tag_label.setText("No tag selected")

    def _on_category_selection_changed(self):
        """Handle category tree selection changes."""
        current_item = self.category_tree.currentItem()
        if current_item:
            item_data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and item_data.get("type") == "tag":
                tag_name = item_data["name"]
                self.tag_selected.emit(tag_name)

    def _on_category_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle category tree item changes."""
        # This could handle in-place editing of categories/tags
        pass

    def _edit_selected_tag(self):
        """Edit selected tag."""
        current_item = self.tags_list.currentItem()
        if not current_item:
            QMessageBox.information(
                self, "No Selection", "Please select a tag to edit."
            )
            return

        tag_name = current_item.text()

        # Create edit dialog with current data
        dialog = TagEditDialog(self)
        dialog.set_tag_data(
            {
                "name": tag_name,
                "category": self.tag_categories.get(tag_name, "Uncategorized"),
                "color": self.tag_colors.get(tag_name, "#000000"),
                "description": self.tag_descriptions.get(tag_name, ""),
            }
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_tag_data()
            new_name = new_data["name"]

            # Handle tag rename
            if new_name != tag_name:
                if new_name in self.all_tags:
                    QMessageBox.warning(
                        self, "Tag Exists", f"Tag '{new_name}' already exists."
                    )
                    return

                # Rename tag
                self.all_tags.remove(tag_name)
                self.all_tags.add(new_name)

                # Update mappings
                if tag_name in self.tag_categories:
                    del self.tag_categories[tag_name]
                if tag_name in self.tag_colors:
                    del self.tag_colors[tag_name]
                if tag_name in self.tag_descriptions:
                    del self.tag_descriptions[tag_name]
                if tag_name in self.tag_usage_count:
                    self.tag_usage_count[new_name] = self.tag_usage_count.pop(tag_name)

            # Update tag data
            self.tag_categories[new_name] = new_data["category"]
            self.tag_colors[new_name] = new_data["color"]
            self.tag_descriptions[new_name] = new_data["description"]

            self._update_tags_display()
            self._update_category_tree()
            self.tags_changed.emit(list(self.all_tags))

            self.logger.info(f"Edited tag: {tag_name} -> {new_name}")

    def _delete_selected_tags(self):
        """Delete selected tags."""
        selected_items = self.tags_list.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select tags to delete."
            )
            return None
