# 🚀 AI Coding IDE - Premium UI Components

import json
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QMimeData, QThread, Signal, QSize
from PySide6.QtGui import QColor, QDrag, QPainter, QPixmap, QKeySequence, QIcon, QFont, QCursor
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

class ChatBubble(QFrame):
    """
    Premium Chat Bubble with modern aesthetics.
    """
    def __init__(self, text, role="assistant", parent=None):
        super().__init__(parent)
        self.role = role
        self.text = text
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # Bubble Container
        self.bubble = QFrame()
        self.bubble_layout = QVBoxLayout(self.bubble)
        self.bubble_layout.setContentsMargins(14, 10, 14, 10)
        self.bubble_layout.setSpacing(6)

        # Header (Icon + Name)
        header = QHBoxLayout()
        header.setSpacing(8)
        
        icon = QLabel()
        icon.setFixedSize(20, 20)
        
        name = QLabel()
        name.setStyleSheet("font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;")

        if self.role == "user":
            icon.setText("👤")
            name.setText("You")
            name.setStyleSheet(name.styleSheet() + "color: #3b82f6;")
            self.bubble.setStyleSheet("""
                QFrame {
                    background-color: #1a1d23;
                    border: 1px solid #2d3139;
                    border-radius: 16px;
                    border-top-right-radius: 4px;
                }
            """)
            layout.setAlignment(Qt.AlignRight)
            header.addStretch()
            header.addWidget(name)
            header.addWidget(icon)
        else:
            icon.setText("🧠")
            name.setText("AI Assistant")
            name.setStyleSheet(name.styleSheet() + "color: #10b981;")
            self.bubble.setStyleSheet("""
                QFrame {
                    background-color: #0f1115;
                    border: 1px solid #1a1d23;
                    border-radius: 16px;
                    border-top-left-radius: 4px;
                }
            """)
            layout.setAlignment(Qt.AlignLeft)
            header.addWidget(icon)
            header.addWidget(name)
            header.addStretch()

        self.bubble_layout.addLayout(header)

        # Message Content
        self.content = QLabel(self.text)
        self.content.setWordWrap(True)
        self.content.setTextFormat(Qt.MarkdownText)
        self.content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.content.setStyleSheet("""
            QLabel {
                color: #f1f5f9;
                font-size: 13px;
                line-height: 1.5;
                background: transparent;
                border: none;
            }
        """)
        self.bubble_layout.addWidget(self.content)

        layout.addWidget(self.bubble)
        
        # Max width constraint (approx 80% of chat width)
        self.setMinimumWidth(100)
        self.bubble.setMaximumWidth(800)

    def update_text(self, text):
        self.text = text
        self.content.setText(text)

class ThoughtBubble(QFrame):
    """
    Subtle Bubble for AI Reasoning/Thoughts.
    """
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 4, 16, 4) # More indent from left
        layout.setSpacing(0)

        self.bubble = QFrame()
        self.bubble_layout = QVBoxLayout(self.bubble)
        self.bubble_layout.setContentsMargins(12, 8, 12, 8)
        self.bubble_layout.setSpacing(4)
        
        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        icon = QLabel("🧠")
        icon.setStyleSheet("font-size: 14px;")
        
        status = QLabel("ХІД ДУМОК (REASONING)")
        status.setStyleSheet("""
            color: #6366f1; 
            font-size: 9px; 
            font-weight: 800; 
            letter-spacing: 1px;
            text-transform: uppercase;
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(status)
        header_layout.addStretch()
        self.bubble_layout.addWidget(header_widget)

        self.bubble.setStyleSheet("""
            QFrame {
                background-color: #1a1f26;
                border: 1px solid #312e81;
                border-left: 3px solid #6366f1;
                border-radius: 8px;
            }
        """)

        # Thought Content
        self.content = QLabel(self.text)
        self.content.setTextFormat(Qt.MarkdownText)
        self.content.setWordWrap(True)
        self.content.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
                line-height: 1.6;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        self.bubble_layout.addWidget(self.content)
        
        layout.addWidget(self.bubble)
        self.bubble.setMaximumWidth(700)

    def update_text(self, text):
        self.text = text
        self.content.setText(text)


class DownloadDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Завантаження {model['name']}")
        self.setModal(True)
        self.setFixedSize(380, 140)
        self.setStyleSheet("background-color: #0f1115; color: #f1f5f9; border: 1px solid #2d3139; border-radius: 12px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.label = QLabel(f"Завантаження {model['name']} ({model['size_gb']} GB)...")
        self.label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #1a1d23;
                border: 1px solid #2d3139;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress)

        self.cancel_btn = QPushButton("Скасувати")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1d23;
                border: 1px solid #2d3139;
                padding: 6px;
                border-radius: 6px;
                color: #94a3b8;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #2d3139; color: #f1f5f9; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn, 0, Qt.AlignRight)

    def update_progress(self, percent):
        self.progress.setValue(int(percent))


class ModelCard(QFrame):
    def __init__(self, model, on_load, on_delete, on_download):
        super().__init__()
        self.model = model
        self.on_load = on_load
        self.on_delete = on_delete
        self.on_download = on_download
        self.setFixedHeight(75)
        self.setObjectName("model_card")
        self.setStyleSheet("""
            QFrame {
                background-color: #0f1115;
                border: 1px solid #1a1d23;
                border-radius: 12px;
                margin: 4px 8px;
            }
            QFrame:hover {
                background-color: #1a1d23;
                border: 1.5px solid #2d3139;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Status indicator
        status_dot = QFrame()
        status_dot.setFixedSize(10, 10)
        status_dot.setStyleSheet(f"""
            QFrame {{
                background-color: {'#10b981' if self.model['is_downloaded'] else '#2d3139'};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(status_dot)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(self.model["name"][:25] + ("..." if len(self.model["name"]) > 25 else ""))
        name.setStyleSheet("color: #f1f5f9; font-weight: 600; font-size: 11px;")
        name.setToolTip(self.model["name"])
        info.addWidget(name)

        meta = QLabel(f"{self.model['size_gb']} GB • {self.model['ram_required_gb']}G RAM")
        meta.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 500;")
        info.addWidget(meta)
        layout.addLayout(info)
        
        layout.addStretch()

        # Action Button Container
        actions = QHBoxLayout()
        actions.setSpacing(6)

        if self.model["is_downloaded"]:
            run_btn = QPushButton("▶")
            run_btn.setFixedSize(30, 30)
            run_btn.setCursor(QCursor(Qt.PointingHandCursor))
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 15px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #2563eb; }
            """)
            run_btn.clicked.connect(lambda: self.on_load(self.model))
            actions.addWidget(run_btn)

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(30, 30)
            del_btn.setCursor(QCursor(Qt.PointingHandCursor))
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a1d23;
                    color: #94a3b8;
                    border: 1px solid #2d3139;
                    border-radius: 15px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #4a2525; color: #f43f5e; border: 1px solid #f43f5e; }
            """)
            del_btn.clicked.connect(lambda: self.on_delete(self.model))
            actions.addWidget(del_btn)
        else:
            if self.model.get("is_compatible", True):
                dl_btn = QPushButton("⬇")
                dl_btn.setFixedSize(30, 30)
                dl_btn.setCursor(QCursor(Qt.PointingHandCursor))
                dl_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1d23;
                        color: #3b82f6;
                        border: 1px solid #3b82f6;
                        border-radius: 15px;
                        font-size: 12px;
                    }
                    QPushButton:hover { background-color: #3b82f6; color: white; }
                """)
                dl_btn.clicked.connect(lambda: self.on_download(self.model))
                actions.addWidget(dl_btn)
            else:
                layout.addWidget(QLabel("⚠️"))

        layout.addLayout(actions)


class FileTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Файли"])
        self.setIndentation(12)
        self.setAnimated(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemDoubleClicked.connect(self.item_double_clicked)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #0f1115;
                border: 1px solid #1a1d23;
                border-radius: 10px;
                padding: 6px;
                color: #94a3b8;
                font-size: 11px;
            }
            QTreeWidget::item { padding: 4px 6px; border-radius: 4px; }
            QTreeWidget::item:hover { background-color: #1a1d23; color: #f1f5f9; }
            QTreeWidget::item:selected { background-color: #3b82f6; color: white; }
        """)
        self.setColumnWidth(0, 200)

    # Signals
    file_open_requested = Signal(str)
    add_to_chat_requested = Signal(str)
    new_file_requested = Signal(str)
    new_folder_requested = Signal(str)
    refresh_requested = Signal()
    delete_requested = Signal(str)
    rename_requested = Signal(str)

    def show_context_menu(self, position):
        item = self.itemAt(position)
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #1a1d23; color: #f1f5f9; border: 1px solid #2d3139; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #3b82f6; }
        """)

        if item:
            path = item.data(0, Qt.UserRole)
            if path:
                if os.path.isfile(path):
                    menu.addAction("💬 Додати до чату", lambda: self.add_to_chat_requested.emit(path))
                    menu.addSeparator()
                
                menu.addAction("📂 Відкрити", lambda: self.file_open_requested.emit(path))
                menu.addAction("✏️ Перейменувати", lambda: self.rename_requested.emit(path))
                menu.addAction("🗑️ Видалити", lambda: self.delete_requested.emit(path))
                menu.addSeparator()

        menu.addAction("🔄 Оновити", lambda: self.refresh_requested.emit())
        menu.addSeparator()
        
        create_menu = menu.addMenu("➕ Створити")
        create_menu.setStyleSheet(menu.styleSheet())
        create_menu.addAction("📄 Новий файл", lambda: self.new_file_requested.emit(self._get_current_dir(item)))
        create_menu.addAction("📁 Нова папка", lambda: self.new_folder_requested.emit(self._get_current_dir(item)))

        menu.exec_(self.viewport().mapToGlobal(position))

    def _get_current_dir(self, item):
        if not item:
            return "" # Use project root
        path = item.data(0, Qt.UserRole)
        if path and os.path.isdir(path):
            return path
        elif path:
            return os.path.dirname(path)
        return ""

    def item_double_clicked(self, item, column):
        path = item.data(0, Qt.UserRole)
        if path and os.path.isfile(path):
            self.file_open_requested.emit(path)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.refresh_requested.emit()


class TypingIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("QFrame { background-color: transparent; }")
        self.setup_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.dot_index = 0

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self.bubble = QFrame()
        self.bubble.setFixedHeight(40)
        self.bubble.setStyleSheet("""
            QFrame {
                background-color: #1e1b4b;
                border: 1px solid #4338ca;
                border-radius: 20px;
                padding: 0px 20px;
            }
        """)
        bl = QHBoxLayout(self.bubble)
        bl.setContentsMargins(15, 0, 15, 0)
        bl.setSpacing(12)

        icon = QLabel("⚡")
        icon.setStyleSheet("font-size: 16px;")
        bl.addWidget(icon)

        self.label = QLabel("Асистент готує відповідь...")
        self.label.setStyleSheet("color: #a5b4fc; font-size: 12px; font-weight: 600;")
        bl.addWidget(self.label)

        self.dots = []
        for _ in range(3):
            dot = QLabel("●")
            dot.setStyleSheet("color: #818cf8; font-size: 18px;")
            bl.addWidget(dot)
            self.dots.append(dot)
            
        layout.addWidget(self.bubble)
        layout.addStretch()

    def start(self):
        self.show()
        self.timer.start(400)

    def stop(self):
        self.timer.stop()
        self.hide()

    def animate(self):
        self.dot_index = (self.dot_index + 1) % 4
        for i, dot in enumerate(self.dots):
            active = i < self.dot_index
            color = "#818cf8" if active else "#312e81"
            scale = "font-size: 20px; font-weight: bold;" if active else "font-size: 18px;"
            dot.setStyleSheet(f"color: {color}; {scale}")
