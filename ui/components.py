# 🚀 AI Coding IDE - Premium UI Components

import json
import os
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QMimeData, QThread, Signal, QSize, QProcess
from PySide6.QtGui import (
    QColor,
    QDrag,
    QPainter,
    QPixmap,
    QKeySequence,
    QIcon,
    QFont,
    QCursor,
    QSyntaxHighlighter,
    QTextCharFormat,
)
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
    QPlainTextEdit,
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
        name.setStyleSheet(
            "font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;"
        )

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


class StatusIndicator(QFrame):
    """
    Visual indicator showing AI status: idle, thinking, tool_calling, etc.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.current_status = "idle"
        self.setup_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.dot_index = 0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.pulse_animation)
        self.pulse_value = 0

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.container = QFrame()
        self.container.setFixedHeight(36)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #1a1d23;
                border: 1px solid #2d3139;
                border-radius: 18px;
                padding: 0px 16px;
            }
        """)
        inner_layout = QHBoxLayout(self.container)
        inner_layout.setContentsMargins(12, 0, 12, 0)
        inner_layout.setSpacing(10)

        # Status icon
        self.icon = QLabel("✨")
        self.icon.setStyleSheet("font-size: 16px;")
        inner_layout.addWidget(self.icon)

        # Status text
        self.status_text = QLabel("Ready")
        self.status_text.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        inner_layout.addWidget(self.status_text)

        inner_layout.addStretch()

        # Animated dots (for thinking state)
        self.dots = []
        for _ in range(3):
            dot = QLabel("●")
            dot.setStyleSheet("color: #2d3139; font-size: 14px;")
            dot.hide()
            inner_layout.addWidget(dot)
            self.dots.append(dot)

        layout.addWidget(self.container)
        layout.addStretch()

        self.hide()

    def set_status(self, status: str, message: str = ""):
        """Set status: idle, thinking, tool_calling, error, success"""
        self.current_status = status
        
        icon_map = {
            "idle": ("✨", "#64748b", "Ready"),
            "thinking": ("🧠", "#a78bfa", "Thinking..."),
            "tool_calling": ("🛠️", "#fbbf24", "Using tool..."),
            "error": ("❌", "#f87171", "Error"),
            "success": ("✅", "#34d399", "Done"),
        }
        
        icon_char, color, default_msg = icon_map.get(status, icon_map["idle"])
        display_msg = message if message else default_msg
        
        self.icon.setText(icon_char)
        self.status_text.setText(display_msg)
        self.status_text.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")
        
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1d23;
                border: 1px solid {color}40;
                border-radius: 18px;
                padding: 0px 16px;
            }}
        """)
        
        # Show/hide dots based on status
        for dot in self.dots:
            if status in ["thinking", "tool_calling"]:
                dot.show()
                dot.setStyleSheet(f"color: {color}40; font-size: 14px;")
            else:
                dot.hide()
        
        if status in ["thinking", "tool_calling"]:
            self.show()
            self.timer.start(500)
        elif status in ["idle", "success"]:
            if status == "idle":
                self.hide()
            else:
                self.show()
                self.timer.stop()
                self.pulse_timer.start(200)
        elif status == "error":
            self.show()
            self.timer.stop()

    def animate(self):
        """Animate the dots for thinking/tool_calling states"""
        if self.current_status not in ["thinking", "tool_calling"]:
            return
            
        color = "#a78bfa" if self.current_status == "thinking" else "#fbbf24"
        self.dot_index = (self.dot_index + 1) % 4
        
        for i, dot in enumerate(self.dots):
            if i < self.dot_index:
                dot.setStyleSheet(f"color: {color}; font-size: 16px;")
            else:
                dot.setStyleSheet(f"color: {color}40; font-size: 14px;")

    def pulse_animation(self):
        """Pulse animation for success state"""
        self.pulse_value = (self.pulse_value + 1) % 10
        alpha = 1.0 - (self.pulse_value * 0.1)
        if alpha <= 0:
            self.pulse_timer.stop()
            self.hide()


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
        layout.setContentsMargins(32, 4, 16, 4)  # More indent from left
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
    progress_updated = Signal(float, int, int)
    download_finished = Signal()
    download_failed = Signal(str)
    def __init__(self, model, model_manager, parent=None):
        super().__init__(parent)
        self.model = model
        self.model_manager = model_manager
        self.setWindowTitle(f"Завантаження {model['name']}")
        self.setModal(True)
        self.setFixedSize(380, 140)
        self.setStyleSheet(
            "background-color: #0f1115; color: #f1f5f9; border: 1px solid #2d3139; border-radius: 12px;"
        )

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

        self.progress_updated.connect(self.update_progress)
        self.download_finished.connect(self.accept)
        self.download_failed.connect(self.show_error)

        threading.Thread(target=self.start_download, daemon=True).start()

    def start_download(self):
        try:
            print(f"DEBUG: Starting download for {self.model.get('name')}")
            # Передаємо callback для прогресу
            self.model_manager.download_model(
                self.model,
                progress_callback=lambda p, d, t: self.progress_updated.emit(p, d, t),
            )
            self.download_finished.emit()
        except Exception as e:
            traceback.print_exc()
            self.label.setText(f"Помилка: {str(e)}")
            self.label.setStyleSheet("color: #ef4444; font-size: 10px;")

    def update_progress(self, percent, downloaded, total):
        self.progress.setValue(int(percent))
        self.label.setText(f"Завантажено {int(downloaded/(1024*1024))}MB з {int(total/(1024*1024))}MB")

    def show_error(self, message):
        self.label.setText(f"Помилка: {message}")
        self.label.setStyleSheet("color: #ef4444; font-size: 10px;")


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
                background-color: {"#10b981" if self.model["is_downloaded"] else "#2d3139"};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(status_dot)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(
            self.model["name"][:25] + ("..." if len(self.model["name"]) > 25 else "")
        )
        name.setStyleSheet("color: #f1f5f9; font-weight: 600; font-size: 11px;")
        name.setToolTip(self.model["name"])
        info.addWidget(name)

        meta = QLabel(
            f"{self.model['size_gb']} GB • {self.model['ram_required_gb']}G RAM"
        )
        meta.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 500;")
        info.addWidget(meta)

        # RAM warning indicator (dot instead of text to save space)
        if self.model.get("reason"):
            warning_dot = QFrame()
            warning_dot.setFixedSize(8, 8)
            warning_dot.setStyleSheet(f"""
                QFrame {{
                    background-color: #eab308;
                    border-radius: 4px;
                }}
            """)
            warning_dot.setToolTip(self.model["reason"])
            info.addWidget(warning_dot)

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
            # Завжди показуємо кнопку завантаження, навіть з попередженням про RAM
            dl_btn = QPushButton("⬇")
            dl_btn.setFixedSize(30, 30)
            dl_btn.setCursor(QCursor(Qt.PointingHandCursor))

            # Якщо є попередження про RAM, показуємо жовту кнопку
            if self.model.get("reason"):
                dl_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1d23;
                        color: #eab308;
                        border: 1px solid #eab308;
                        border-radius: 15px;
                        font-size: 12px;
                    }
                    QPushButton:hover { background-color: #eab308; color: black; }
                """)
                dl_btn.setToolTip(self.model["reason"])
            else:
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
                    menu.addAction(
                        "💬 Додати до чату",
                        lambda: self.add_to_chat_requested.emit(path),
                    )
                    menu.addSeparator()

                menu.addAction(
                    "📂 Відкрити", lambda: self.file_open_requested.emit(path)
                )
                menu.addAction(
                    "✏️ Перейменувати", lambda: self.rename_requested.emit(path)
                )
                menu.addAction("🗑️ Видалити", lambda: self.delete_requested.emit(path))
                menu.addSeparator()

        menu.addAction("🔄 Оновити", lambda: self.refresh_requested.emit())
        menu.addSeparator()

        create_menu = menu.addMenu("➕ Створити")
        create_menu.setStyleSheet(menu.styleSheet())
        create_menu.addAction(
            "📄 Новий файл",
            lambda: self.new_file_requested.emit(self._get_current_dir(item)),
        )
        create_menu.addAction(
            "📁 Нова папка",
            lambda: self.new_folder_requested.emit(self._get_current_dir(item)),
        )

        menu.exec_(self.viewport().mapToGlobal(position))

    def _get_current_dir(self, item):
        if not item:
            return ""  # Use project root
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
            scale = (
                "font-size: 20px; font-weight: bold;" if active else "font-size: 18px;"
            )
            dot.setStyleSheet(f"color: {color}; {scale}")


class TerminalWidget(QFrame):
    """
    Built-in Terminal Emulator using QProcess.
    """
    error_detected = Signal(str) # Emits the error log when a crash is detected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            TerminalWidget {
                background-color: #0c0c0c;
                border-top: 1px solid #2d2d30;
            }
        """)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.handle_finished)

        self.setup_ui()
        self.start_shell()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(30)
        toolbar.setStyleSheet("background-color: #1e1e1e; border-bottom: 1px solid #2d2d30;")
        tbl = QHBoxLayout(toolbar)
        tbl.setContentsMargins(10, 0, 10, 0)

        title = QLabel("TERMINAL (PowerShell)")
        title.setStyleSheet("color: #888; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        tbl.addWidget(title)
        tbl.addStretch()

        clear_btn = QPushButton("🧹 Clear")
        clear_btn.setStyleSheet("background: transparent; color: #888; font-size: 10px; border: none;")
        clear_btn.clicked.connect(self.clear)
        tbl.addWidget(clear_btn)

        layout.addWidget(toolbar)

        # Output
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setUndoRedoEnabled(False)
        self.output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0c0c0c;
                color: #cccccc;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: none;
                padding: 10px;
            }
        """)
        layout.addWidget(self.output)

        # Input
        self.input_field = QTextEdit()
        self.input_field.setFixedHeight(35)
        self.input_field.setPlaceholderText("Введіть команду...")
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: none;
                padding: 8px 10px;
            }
        """)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field)

    def start_shell(self):
        if sys.platform == "win32":
            self.process.start("powershell.exe", ["-NoLogo", "-NoExit"])
        else:
            self.process.start("/bin/bash")

    def read_output(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.output.insertPlainText(data)
        self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())

    def send_command(self):
        cmd = self.input_field.toPlainText().strip()
        if cmd:
            self.process.write((cmd + "\n").encode())
            self.input_field.clear()

    def clear(self):
        self.output.clear()

    def handle_finished(self):
        self.output.insertPlainText("\n--- Shell Process Finished ---\n")
        self.start_shell()  # Restart

    def eventFilter(self, obj, event):
        if obj is self.input_field and event.type() == 6:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_command()
                return True
        return super().eventFilter(obj, event)


class DiffDialog(QDialog):
    """
    Modern Side-by-Side Diff Viewer.
    """

    def __init__(self, old_text, new_text, filename="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Перегляд змін: {filename}")
        self.resize(1100, 700)
        self.setup_ui(old_text, new_text)

    def setup_ui(self, old_text, new_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        title = QLabel(f"📐 Порівняння змін")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)

        diff_area = QHBoxLayout()
        diff_area.setSpacing(10)

        # Old file (Left)
        old_container = QVBoxLayout()
        old_container.addWidget(QLabel("Оригінал (Current)"))
        self.old_view = QPlainTextEdit(old_text)
        self.old_view.setReadOnly(True)
        self.old_view.setStyleSheet("background-color: #1a1b1e; color: #94a3b8;")
        old_container.addWidget(self.old_view)
        diff_area.addLayout(old_container)

        # New file (Right)
        new_container = QVBoxLayout()
        new_container.addWidget(QLabel("Нова версія (Suggested)"))
        self.new_view = QPlainTextEdit(new_text)
        self.new_view.setReadOnly(True)
        self.new_view.setStyleSheet("background-color: #0f1115; color: #f1f5f9; border: 1px solid #10b981;")
        new_container.addWidget(self.new_view)
        diff_area.addLayout(new_container)

        layout.addLayout(diff_area)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()

        cancel_btn = QPushButton("Скасувати")
        cancel_btn.setFixedSize(120, 35)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        self.apply_btn = QPushButton("Застосувати зміни")
        self.apply_btn.setFixedSize(160, 35)
        self.apply_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold;")
        self.apply_btn.clicked.connect(self.accept)
        btns.addWidget(self.apply_btn)

        layout.addLayout(btns)

        self.setStyleSheet("""
            QDialog { background-color: #0a0c10; color: #f1f5f9; }
            QLabel { color: #94a3b8; font-size: 12px; font-weight: 600; }
            QPushButton { background-color: #1a1d23; border: 1px solid #2d3139; border-radius: 6px; color: #f1f5f9; }
            QPushButton:hover { background-color: #2d3139; }
        """)


class TestRunnerWidget(QFrame):
    """
    Panel for running and viewing unit tests.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            TestRunnerWidget {
                background-color: #1e1e1e;
                border-top: 1px solid #2d2d30;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(30)
        toolbar.setStyleSheet("background-color: #252526; border-bottom: 1px solid #2d2d30;")
        tbl = QHBoxLayout(toolbar)
        tbl.setContentsMargins(10, 0, 10, 0)

        title = QLabel("TEST RUNNER (PyTest)")
        title.setStyleSheet("color: #cccccc; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        tbl.addWidget(title)
        tbl.addStretch()

        self.run_btn = QPushButton("▶ Run All Tests")
        self.run_btn.setStyleSheet("background: #0e639c; color: white; border-radius: 4px; font-size: 10px; padding: 2px 10px;")
        tbl.addWidget(self.run_btn)

        layout.addWidget(toolbar)

        # Tests Output
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Результати тестів з'являться тут після запуску...")
        self.output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: none;
                padding: 10px;
            }
        """)
        layout.addWidget(self.output)

class SQLiteExplorerWidget(QFrame):
    """
    Simple SQLite database explorer and query executor.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1e1e1e;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        t = QHBoxLayout()
        self.db_path_label = QLabel("Database: None")
        self.db_path_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        t.addWidget(self.db_path_label)
        
        self.open_btn = QPushButton("📂 Open DB")
        self.open_btn.setFixedSize(100, 26)
        t.addWidget(self.open_btn)
        t.addStretch()
        layout.addLayout(t)

        from PySide6.QtWidgets import QTableWidget, QHeaderView
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget { background-color: #252526; color: #ddd; gridline-color: #333; }
            QHeaderView::section { background-color: #333; color: #ccc; border: none; padding: 4px; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # SQL Input
        self.sql_input = QTextEdit()
        self.sql_input.setPlaceholderText("Введіть SQL запит тут (напр. SELECT * FROM users)...")
        self.sql_input.setFixedHeight(60)
        self.sql_input.setStyleSheet("background: #121212; color: #d4d4d4; border: 1px solid #333;")
        layout.addWidget(self.sql_input)

class JupyterViewerWidget(QFrame):
    """
    Simple .ipynb (Jupyter Notebook) viewer.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1e1e1e;")
        layout = QVBoxLayout(self)
        
        from PySide6.QtWidgets import QScrollArea
        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.content = QLabel("Відкрийте .ipynb файл для перегляду")
        self.content.setWordWrap(True)
        self.content.setStyleSheet("color: #ddd; padding: 20px; font-size: 13px;")
        self.area.setWidget(self.content)
        layout.addWidget(self.area)

    def load_notebook(self, path):
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            html = "<h2>Jupyter Notebook</h2>"
            for cell in data.get("cells", []):
                ctype = cell.get("cell_type")
                source = "".join(cell.get("source", []))
                if ctype == "markdown":
                    html += f"<div style='margin-top: 10px; color: #4ec9b0;'>{source}</div>"
                elif ctype == "code":
                    html += f"<pre style='background: #2d2d2d; padding: 10px; color: #d4d4d4;'>{source}</pre>"
            
            self.content.setText(html)
        except Exception as e:
            self.content.setText(f"❌ Помилка завантаження: {e}")
