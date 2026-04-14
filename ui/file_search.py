import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QLabel,
)


class FileSearchDialog(QDialog):
    file_selected = Signal(str)

    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.files = []

        self.setWindowTitle("Quick Open File")
        self.setModal(False)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук файлу...")
        self.search_input.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_input)

        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.on_item_clicked)
        layout.addWidget(self.results)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.load_files()
        self.search_input.setFocus()

    def load_files(self):
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["__pycache__", "node_modules", "venv", ".venv"]
            ]
            for f in files:
                if not f.startswith(".") and not f.endswith(".pyc"):
                    path = os.path.join(root, f)
                    rel = os.path.relpath(path, self.project_path)
                    self.files.append((rel, path))
        self.files.sort()

    def filter_files(self, text):
        self.results.clear()
        text = text.lower()
        count = 0
        for rel, path in self.files:
            if text in rel.lower():
                item = QListWidgetItem(rel)
                item.setData(Qt.UserRole, path)
                self.results.addItem(item)
                count += 1
                if count >= 50:
                    break
        self.status_label.setText(f"Знайдено: {count}")

    def on_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        self.file_selected.emit(path)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return:
            current = self.results.currentItem()
            if current:
                self.on_item_clicked(current)
        else:
            super().keyPressEvent(event)
