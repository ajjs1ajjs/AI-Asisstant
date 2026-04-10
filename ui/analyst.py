# 📈 AI Data Analyst Widget
# Process CSV/Excel files and generate insights.

import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog, QPlainTextEdit
from PySide6.QtCore import Qt

class DataAnalystWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0f1115; border: none;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("📈 AI Data Analyst")
        header.setStyleSheet("color: #4ec9b0; font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        desc = QLabel("Завантажте CSV або Excel файл для ШІ-аналізу та візуалізації.")
        desc.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(desc)

        self.load_btn = QPushButton("📂 Відкрити файл даних")
        self.load_btn.setStyleSheet("""
            QPushButton { background: #3e3e3e; color: white; padding: 10px; border-radius: 6px; }
            QPushButton:hover { background: #4e4e4e; }
        """)
        self.load_btn.clicked.connect(self.load_data)
        layout.addWidget(self.load_btn)

        self.result_area = QPlainTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setStyleSheet("""
            QPlainTextEdit { background: #1e1e1e; color: #4ec9b0; border: 1px solid #333; font-family: Consolas; font-size: 12px; }
        """)
        layout.addWidget(self.result_area)

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Відкрити файл", "", "Data Files (*.csv *.xlsx *.json)")
        if file_path:
            self.result_area.setPlainText(f"📦 Завантажено: {os.path.basename(file_path)}\n\nАналізую структуру...\nВикористовую Pandas для обробки статистичних даних.")
            # Logic for actual analysis will go here
