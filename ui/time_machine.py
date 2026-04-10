# ⌛ Project Time Machine Widget
# Visual Git history and time travel.

import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class TimeMachineWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1e1e1e; border: none;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("⌛ Project Time Machine (Git History)")
        header.setStyleSheet("color: #4ec9b0; font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        self.commit_list = QListWidget()
        self.commit_list.setStyleSheet("""
            QListWidget { background: #252526; color: #ccc; border: 1px solid #333; padding: 5px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #2d2d30; }
            QListWidget::item:selected { background: #094771; }
        """)
        layout.addWidget(self.commit_list)

        buttons = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Оновити історію")
        self.refresh_btn.setStyleSheet("background: #333; color: #ddd; padding: 5px;")
        buttons.addWidget(self.refresh_btn)

        self.travel_btn = QPushButton("🚀 Подорожувати (Checkout)")
        self.travel_btn.setStyleSheet("background: #007acc; color: white; padding: 5px;")
        buttons.addWidget(self.travel_btn)
        
        layout.addLayout(buttons)

    def update_history(self, commits):
        self.commit_list.clear()
        for c in commits:
            item_text = f"[{c.short_hash}] {c.message}\n👤 {c.author} | 📅 {c.date}"
            self.commit_list.addItem(item_text)
