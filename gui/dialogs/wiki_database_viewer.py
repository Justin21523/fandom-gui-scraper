from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from scraper.mediawiki.query import DATASETS, WikiDBQueryService
from utils.logger import get_logger


class WikiDatabaseViewer(QDialog):
    """Local SQLite wiki.db browser."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)
        self.service: WikiDBQueryService | None = None
        self.current_rows = []
        self.current_dataset = "pages"
        self.offset = 0
        self.total_rows = 0
        self.setWindowTitle("Wiki DB Viewer")
        self.resize(1100, 720)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select a wiki.db file")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.open_file)

        self.dataset_combo = QComboBox()
        self.dataset_combo.addItems(DATASETS.keys())
        self.dataset_combo.currentTextChanged.connect(self.load_dataset)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search")
        self.search_edit.returnPressed.connect(self.reload_from_start)

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(25, 1000)
        self.limit_spin.setSingleStep(25)
        self.limit_spin.setValue(100)
        self.limit_spin.valueChanged.connect(self.reload_from_start)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.reload_from_start)
        prev_btn = QPushButton("Prev")
        prev_btn.clicked.connect(self.previous_page)
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(self.next_page)
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_current)

        toolbar.addWidget(QLabel("DB:"))
        toolbar.addWidget(self.path_edit, 1)
        toolbar.addWidget(browse_btn)
        toolbar.addWidget(QLabel("Dataset:"))
        toolbar.addWidget(self.dataset_combo)
        toolbar.addWidget(self.search_edit)
        toolbar.addWidget(QLabel("Limit:"))
        toolbar.addWidget(self.limit_spin)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(prev_btn)
        toolbar.addWidget(next_btn)
        toolbar.addWidget(export_btn)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.show_selected_detail)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.table)

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.addWidget(QLabel("Row Detail"))
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        splitter.addWidget(detail_panel)
        splitter.setSizes([760, 340])
        layout.addWidget(splitter)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open wiki.db", "", "SQLite DB (*.db *.sqlite);;All files (*)")
        if not path:
            return
        self.path_edit.setText(path)
        self.service = WikiDBQueryService(path)
        self.reload_from_start()

    def reload_from_start(self, *_args):
        self.offset = 0
        self.load_dataset(self.dataset_combo.currentText())

    def load_dataset(self, dataset: str):
        if not self.service:
            return
        if dataset != self.current_dataset:
            self.offset = 0
        self.current_dataset = dataset
        try:
            data = self.service.table(
                dataset,
                limit=self.limit_spin.value(),
                offset=self.offset,
                q=self.search_edit.text().strip(),
            )
            self.current_rows = data["items"]
            self.total_rows = data["total"]
            self._populate_table(data["columns"], self.current_rows)
            start = data["offset"] + 1 if data["total"] else 0
            end = min(data["offset"] + len(data["items"]), data["total"])
            self.status_label.setText(f"{start}-{end} of {data['total']} rows in {dataset}")
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", str(e))

    def previous_page(self):
        self.offset = max(0, self.offset - self.limit_spin.value())
        self.load_dataset(self.current_dataset)

    def next_page(self):
        if self.offset + self.limit_spin.value() >= self.total_rows:
            return
        self.offset += self.limit_spin.value()
        self.load_dataset(self.current_dataset)

    def _populate_table(self, columns, rows):
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        for row_idx, row in enumerate(rows):
            for col_idx, column in enumerate(columns):
                item = QTableWidgetItem(str(row.get(column, "")))
                self.table.setItem(row_idx, col_idx, item)

    def show_selected_detail(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        if row >= len(self.current_rows):
            return
        self.detail_text.setPlainText(json.dumps(self.current_rows[row], ensure_ascii=False, indent=2, default=str))

    def export_current(self):
        if not self.service:
            QMessageBox.information(self, "Export", "Open a wiki.db file first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Dataset",
            f"{self.current_dataset}.csv",
            "CSV files (*.csv);;JSON files (*.json)",
        )
        if not path:
            return
        fmt = "json" if path.endswith(".json") else "csv"
        try:
            tmp_path = self.service.export_dataset(self.current_dataset, fmt)
            Path(path).write_bytes(tmp_path.read_bytes())
            tmp_path.unlink(missing_ok=True)
            QMessageBox.information(self, "Export", f"Data exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
