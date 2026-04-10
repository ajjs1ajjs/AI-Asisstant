# 🦙 Ollama Manager Dialog
# Allows managing local LLMs directly from the IDE.

import httpx
import json
import os
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, 
    QMessageBox, QProgressBar, QFrame
)

class OllamaWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, action, model_name=None):
        super().__init__()
        self.action = action
        self.model_name = model_name
        self.url = "http://localhost:11434/api"

    def run(self):
        try:
            if self.action == "list":
                r = httpx.get(f"{self.url}/tags", timeout=5)
                self.finished.emit(r.json())
            elif self.action == "pull":
                # For pull we might need continuous updates, but here we just start it
                r = httpx.post(f"{self.url}/pull", json={"name": self.model_name}, timeout=None)
                self.finished.emit({"status": "started"})
        except Exception as e:
            self.error.emit(str(e))

class OllamaManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ollama Manager")
        self.resize(500, 400)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #cccccc; }
            QLabel { font-size: 13px; }
            QPushButton { background-color: #3e3e3e; border-radius: 4px; padding: 6px; color: white; }
            QPushButton:hover { background-color: #4e4e4e; }
            QListWidget { background-color: #252526; border: 1px solid #333; color: #ddd; padding: 5px; }
        """)
        self.setup_ui()
        self.refresh_models()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        header.addWidget(QLabel("🦙 Локальні моделі Ollama"))
        
        refresh_btn = QPushButton("🔄 Оновити")
        refresh_btn.clicked.connect(self.refresh_models)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        self.model_list = QListWidget()
        layout.addWidget(self.model_list)

        # Pull new model
        pull_layout = QHBoxLayout()
        self.pull_btn = QPushButton("⬇ Завантажити нову модель (llama3, mistral, etc.)")
        self.pull_btn.clicked.connect(self.pull_model)
        pull_layout.addWidget(self.pull_btn)
        layout.addLayout(pull_layout)

        self.status_label = QLabel("Статус: Готовий")
        layout.addWidget(self.status_label)

    def refresh_models(self):
        self.status_label.setText("Оновлення...")
        self.worker = OllamaWorker("list")
        self.worker.finished.connect(self._on_list_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_list_finished(self, data):
        self.model_list.clear()
        models = data.get("models", [])
        for m in models:
            item = QListWidgetItem(f"📦 {m['name']} ({m['size'] // (1024**2)} MB)")
            self.model_list.addItem(item)
        self.status_label.setText(f"Знайдено {len(models)} моделей")

    def _on_error(self, err):
        self.status_label.setText(f"❌ Помилка: {err}")
        if "connection" in err.lower():
            QMessageBox.warning(self, "Ollama Not Found", "Ollama не знайдено за адресою localhost:11434.\nПереконайтеся, що Ollama запущена.")

    def pull_model(self):
        from PySide6.QtWidgets import QInputDialog
        model, ok = QInputDialog.getText(self, "Pull Model", "Введіть назву моделі (напр. gemma2):")
        if ok and model:
            self.status_label.setText(f"Завантаження {model}...")
            self.worker = OllamaWorker("pull", model)
            self.worker.finished.connect(lambda: QMessageBox.information(self, "Ollama", f"Запит на завантаження {model} надіслано!"))
            self.worker.start()
