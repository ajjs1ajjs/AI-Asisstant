# 🚀 AI Coding IDE - Ultra Compact Version

import json
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtCore import Qt, QTimer, QMimeData, QThread, Signal
from PySide6.QtGui import QColor, QDrag, QPainter, QPixmap, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QScrollArea,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from context_engine import ContextEngine
from local_engine import LocalInference, get_inference
from model_manager import LocalModelManager
from settings_dialog import SettingsDialog
from settings import get_settings
from orchestrator import ModelOrchestrator, Model, GroqProvider, OpenRouterProvider, DeepSeekProvider, QwenProvider
from agent_tools import AgentTools, TOOL_DEFINITIONS
import asyncio

CONFIG_FILE = Path.home() / ".ai-ide" / "config.json"
class DownloadDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Завантаження {model['name']}")
        self.setModal(True)
        self.setFixedSize(350, 120)
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")

        layout = QVBoxLayout(self)

        self.label = QLabel(f"Завантаження {model['name']} ({model['size_gb']} GB)...")
        self.label.setStyleSheet("color: #d4d4d4; font-size: 12px;")
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2e;
                border-radius: 8px;
                height: 20px;
                text-align: center;
                color: #fff;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress)

        self.cancel_btn = QPushButton("Скасувати")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3e;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                color: #d4d4d4;
            }
            QPushButton:hover { background-color: #4a4a4e; }
        """)
        self.cancel_btn.clicked.connect(self.close)
        layout.addWidget(self.cancel_btn)

    def update_progress(self, percent):
        self.progress.setValue(int(percent))


class ModelCard(QFrame):
    def __init__(self, model, on_load, on_delete, on_download):
        super().__init__()
        self.model = model
        self.on_load = on_load
        self.on_delete = on_delete
        self.on_download = on_download
        self.setFixedHeight(65)
        self.setStyleSheet("""
            QFrame {
                background-color: #2a2a2e;
                border-radius: 8px;
                margin: 2px 4px;
            }
            QFrame:hover {
                background-color: #3a3a3e;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        # Status dot
        if self.model["is_downloaded"]:
            dot = QLabel("●")
            dot.setStyleSheet("color: #4ec9b0; font-size: 14px;")
            layout.addWidget(dot)
        else:
            dot = QLabel("○")
            dot.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(dot)

        # Info
        info = QVBoxLayout()
        info.setSpacing(1)

        # Name
        name_text = self.model["name"]
        if len(name_text) > 22:
            name_text = name_text[:22] + "..."

        name = QLabel(name_text)
        name.setStyleSheet("color: #e8e8e8; font-weight: 600; font-size: 11px;")
        name.setToolTip(self.model["name"])
        info.addWidget(name)

        # Size
        size = QLabel(
            f"{self.model['size_gb']} GB • {self.model['ram_required_gb']}G RAM"
        )
        size.setStyleSheet("color: #777; font-size: 9px;")
        info.addWidget(size)

        info.addStretch()
        layout.addLayout(info)
        layout.addStretch()

        # Buttons
        if self.model["is_downloaded"]:
            load_btn = QPushButton("▶")
            load_btn.setFixedSize(28, 28)
            load_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border-radius: 14px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #1177bb; }
            """)
            load_btn.clicked.connect(lambda checked, m=self.model: self.on_load(m))
            load_btn.setToolTip("Завантажити")
            layout.addWidget(load_btn)

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 28)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a2525;
                    color: #f44747;
                    border-radius: 14px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #6a3535; }
            """)
            del_btn.clicked.connect(lambda checked, m=self.model: self.on_delete(m))
            del_btn.setToolTip("Видалити")
            layout.addWidget(del_btn)
        else:
            if self.model.get("is_compatible", True):
                dl_btn = QPushButton("⬇")
                dl_btn.setFixedSize(28, 28)
                dl_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #d6701e;
                        color: white;
                        border-radius: 14px;
                        font-size: 12px;
                    }
                    QPushButton:hover { background-color: #e6802e; }
                """)
                dl_btn.clicked.connect(
                    lambda checked, m=self.model: self.on_download(m)
                )
                dl_btn.setToolTip("Завантажити")
                layout.addWidget(dl_btn)
            else:
                no = QLabel("⚠️")
                no.setStyleSheet("color: #f44747; font-size: 12px;")
                no.setToolTip(f"Потрібно {self.model['ram_required_gb']}G RAM")
                layout.addWidget(no)


class FileTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Name"])
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                border: none;
                outline: none;
            }
            QTreeWidget::item { padding: 4px; border-radius: 4px; }
            QTreeWidget::item:selected { background-color: #37373d; }
        """)


class TypingIndicator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(36)
        self.setStyleSheet("QFrame { background-color: transparent; }")
        self.dots = []
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.current_dot = 0

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        icon = QLabel("⏳")
        icon.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon)

        self.label = QLabel("Думає...")
        self.label.setStyleSheet("color: #0078d4; font-size: 12px; font-style: italic;")
        layout.addWidget(self.label)

        dots = QHBoxLayout()
        dots.setSpacing(3)
        for i in range(3):
            dot = QLabel("•")
            dot.setStyleSheet("color: #3e3e3e; font-size: 16px;")
            dots.addWidget(dot)
            self.dots.append(dot)
        layout.addLayout(dots)
        layout.addStretch()

    def start(self):
        self.show()
        self.timer.start(400)
        self.animate()

    def stop(self):
        self.timer.stop()
        self.hide()
        for dot in self.dots:
            dot.setStyleSheet("color: #3e3e3e; font-size: 16px;")

    def animate(self):
        for i, dot in enumerate(self.dots):
            dot.setStyleSheet(
                "color: #3e3e3e; font-size: 16px;"
                if i != self.current_dot
                else "color: #0078d4; font-size: 16px;"
            )
        self.current_dot = (self.current_dot + 1) % 3


