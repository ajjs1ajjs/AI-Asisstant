# 🚀 AI Coding IDE - Ultra Compact Version

import json
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtCore import Qt, QTimer, QMimeData
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

CONFIG_FILE = Path.home() / ".ai-ide" / "config.json"


def save_config(data):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def find_editors():
    editors = []
    paths = {
        "VS Code": os.path.join(
            os.getenv("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"
        ),
        "PyCharm": os.path.join(
            os.getenv("LOCALAPPDATA", ""),
            "JetBrains",
            "PyCharm Community Edition",
            "bin",
            "pycharm64.exe",
        ),
    }
    for name, path in paths.items():
        if os.path.exists(path):
            editors.append({"name": name, "path": path})
    return editors


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Coding IDE")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)

        # Set window icon
        icon_path = self._get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Segoe UI'; }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 10px;
                font-size: 13px;
            }
            QTextEdit QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 8px;
                border-radius: 4px;
            }
            QTextEdit QScrollBar::handle:vertical {
                background-color: #3e3e3e;
                border-radius: 4px;
                min-height: 30px;
            }
            QTextEdit QScrollBar::handle:vertical:hover {
                background-color: #0078d4;
            }
            QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1177bb; }
            QSplitter::handle {
                background-color: #3e3e3e;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #0078d4;
            }
            QScrollArea QScrollBar:vertical {
                background-color: #252525;
                width: 8px;
                border-radius: 4px;
            }
            QScrollArea QScrollBar::handle:vertical {
                background-color: #3e3e3e;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollArea QScrollBar::handle:vertical:hover {
                background-color: #0078d4;
            }
            QMenuBar {
                background-color: #2d2d30;
                color: #d4d4d4;
                border-bottom: 1px solid #3e3e3e;
            }
            QMenuBar::item:selected {
                background-color: #0e639c;
            }
        """)

        self.model_manager = LocalModelManager()
        self.inference = get_inference()
        self.context_engine = ContextEngine()
        self.editors = find_editors()

        self.current_model = None
        self.current_file = None
        self.chat_history = []
        self.project_path = None
        self.is_generating = False

        config = load_config()
        self.last_project = config.get("last_project", "")

        self.init_ui()
        self.create_menu_bar()
        self.refresh_models()

        if self.last_project and os.path.exists(self.last_project):
            self.load_project(self.last_project)

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("📁 Файл")
        file_menu.addAction("➕ Новий проєкт", self.create_project)
        file_menu.addAction("📂 Відкрити проєкт", self.open_project)
        file_menu.addSeparator()
        file_menu.addAction("📖 Відкрити файл", self.open_file)
        file_menu.addAction("🧠 Додати до контексту", self.add_to_context)
        file_menu.addSeparator()
        file_menu.addAction("🚪 Вихід", self.close)

        edit_menu = menubar.addMenu("✏️ Редагування")
        edit_menu.addAction("🧹 Очистити чат", self.clear_chat)
        edit_menu.addAction("📋 Копіювати історію", self.copy_history)
        edit_menu.addSeparator()
        edit_menu.addAction("📝 Очистити контекст", self.clear_context)

        model_menu = menubar.addMenu("🧠 Модель")
        model_menu.addAction("🔄 Оновити список", self.refresh_models)
        model_menu.addAction("🗑️ Видалити модель", self.delete_current_model)

    def clear_chat(self):
        self.chat.clear()
        self.chat_history.clear()

    def clear_context(self):
        self.context_engine.chunks = []
        self.context_label.setText("🧠 0")
        self.chat.append(
            "<div style='background: #2a2a2e; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #888;'>Контекст очищено</span></div>"
        )

    def copy_history(self):
        text = self.chat.toPlainText()
        QApplication.clipboard().setText(text)

    def delete_current_model(self):
        if self.current_model:
            model = next(
                (
                    m
                    for m in self.model_manager.model_catalog
                    if m["name"] == self.current_model
                ),
                None,
            )
            if model:
                self.delete_model(model)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3e3e3e;
            }
            QSplitter::handle:hover {
                background-color: #0078d4;
            }
        """)

        # Left sidebar
        sidebar = QWidget()
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(500)
        sidebar.setStyleSheet("background-color: #252525;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet("QFrame { background-color: #2d2d30; }")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 8, 12, 8)

        title_icon = QLabel("🧠")
        title_icon.setStyleSheet("font-size: 16px;")
        hl.addWidget(title_icon)

        title = QLabel("Моделі")
        title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 13px;")
        hl.addWidget(title)

        hl.addStretch()
        self.models_toggle = QPushButton("▼")
        self.models_toggle.setFixedSize(28, 28)
        self.models_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:hover { 
                color: #0078d4; 
                background-color: #3e3e3e;
            }
        """)
        self.models_toggle.clicked.connect(self.toggle_models)
        hl.addWidget(self.models_toggle)
        self.models_expanded = True
        sb_layout.addWidget(header)

        # Models
        self.models_scroll = QScrollArea()
        self.models_scroll.setWidgetResizable(True)
        self.models_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.models_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self.models_content = QWidget()
        self.models_layout = QVBoxLayout(self.models_content)
        self.models_layout.setAlignment(Qt.AlignTop)
        self.models_layout.setSpacing(6)
        self.models_scroll.setWidget(self.models_content)
        sb_layout.addWidget(self.models_scroll)

        # Project
        proj = QFrame()
        proj.setStyleSheet("QFrame { background-color: #2d2d30; }")
        pl = QVBoxLayout(proj)
        pl.setContentsMargins(12, 12, 12, 12)
        pl.setSpacing(8)

        proj_title = QLabel("📁 Проєкт")
        proj_title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 12px;")
        pl.addWidget(proj_title)

        bl = QHBoxLayout()
        bl.setSpacing(6)
        new_btn = QPushButton("➕ Створити")
        new_btn.setFixedHeight(28)
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d7d2d;
                border-radius: 6px;
                font-size: 11px;
                padding: 4px 12px;
            }
            QPushButton:hover { background-color: #3d8d3d; }
        """)
        new_btn.clicked.connect(self.create_project)
        bl.addWidget(new_btn)
        open_btn = QPushButton("📂 Відкрити")
        open_btn.setFixedHeight(28)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                border-radius: 6px;
                font-size: 11px;
                padding: 4px 12px;
            }
            QPushButton:hover { background-color: #1177bb; }
        """)
        open_btn.clicked.connect(self.open_project)
        bl.addWidget(open_btn)
        pl.addLayout(bl)

        self.project_label = QLabel("Немає проєкту")
        self.project_label.setStyleSheet(
            "color: #888; background: #1e1e1e; padding: 6px 10px; border-radius: 6px; font-size: 10px;"
        )
        pl.addWidget(self.project_label)

        self.files = FileTree()
        self.files.setMaximumHeight(180)
        self.files.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                border: 1px solid #3e3e3e;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        pl.addWidget(self.files)

        al = QHBoxLayout()
        al.setSpacing(6)
        of_btn = QPushButton("📖 Перегляд")
        of_btn.setFixedHeight(26)
        of_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                border-radius: 4px;
                font-size: 10px;
                padding: 4px 10px;
            }
            QPushButton:hover { background-color: #4e4e4e; }
        """)
        of_btn.clicked.connect(self.open_file)
        al.addWidget(of_btn)
        add_btn = QPushButton("🧠 Контекст")
        add_btn.setFixedHeight(26)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #d6701e;
                border-radius: 4px;
                font-size: 10px;
                padding: 4px 10px;
            }
            QPushButton:hover { background-color: #e6802e; }
        """)
        add_btn.clicked.connect(self.add_to_context)
        al.addWidget(add_btn)
        pl.addLayout(al)

        if self.editors:
            el = QHBoxLayout()
            el.setSpacing(4)
            self.editor_combo = QComboBox()
            self.editor_combo.addItems([e["name"] for e in self.editors])
            self.editor_combo.setStyleSheet(
                "padding: 4px; background: #3e3e3e; border-radius: 4px; font-size: 9px;"
            )
            el.addWidget(self.editor_combo)
            ext_btn = QPushButton("↗")
            ext_btn.setFixedWidth(30)
            ext_btn.setStyleSheet("background-color: #6a3d9a;")
            ext_btn.clicked.connect(self.open_external)
            el.addWidget(ext_btn)
            pl.addLayout(el)

        self.context_label = QLabel("🧠 0")
        self.context_label.setStyleSheet("color: #888; font-size: 9px;")
        pl.addWidget(self.context_label)

        sb_layout.addWidget(proj)
        splitter.addWidget(sidebar)

        # Right
        right = QWidget()
        right.setMinimumWidth(400)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # Top
        top = QFrame()
        top.setFixedHeight(50)
        top.setStyleSheet("QFrame { background-color: #2d2d30; }")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(16, 8, 16, 8)
        tl.setSpacing(12)

        self.model_status = QLabel("⚠️ Немає моделі")
        self.model_status.setStyleSheet(
            "color: #f44747; font-weight: bold; font-size: 12px;"
        )
        tl.addWidget(self.model_status)
        tl.addStretch()

        # Status badge with icon
        status_container = QFrame()
        status_container.setStyleSheet("""
            QFrame {
                background-color: #1e3a2a;
                border-radius: 12px;
                padding: 4px 12px;
            }
        """)
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)

        self.status_icon = QLabel("●")
        self.status_icon.setStyleSheet("color: #4ec9b0; font-size: 10px;")
        status_layout.addWidget(self.status_icon)

        self.work_status = QLabel("Готовий")
        self.work_status.setStyleSheet("color: #4ec9b0; font-size: 11px;")
        status_layout.addWidget(self.work_status)

        tl.addWidget(status_container)

        git_btn = QPushButton("Git ▼")
        git_btn.setFixedSize(60, 32)
        git_btn.setStyleSheet("""
            QPushButton {
                background-color: #6a3d9a;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7a4daa; }
        """)
        git_btn.clicked.connect(self.git_menu)
        tl.addWidget(git_btn)
        rl.addWidget(top)

        # Chat
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: none;
                padding: 16px;
            }
        """)
        rl.addWidget(self.chat)

        # Typing
        self.typing = TypingIndicator()
        self.typing.hide()
        rl.addWidget(self.typing)

        # Input
        inp = QFrame()
        inp.setFixedHeight(90)
        inp.setStyleSheet("QFrame { background-color: #2d2d30; }")
        il = QVBoxLayout(inp)
        il.setContentsMargins(12, 10, 12, 10)
        il.setSpacing(6)

        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(45)
        self.chat_input.setPlaceholderText("Ask AI...")
        self.chat_input.keyPressEvent = self.key_press
        self.chat_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 1px solid #0078d4;
            }
        """)
        il.addWidget(self.chat_input)

        sl = QHBoxLayout()
        send_btn = QPushButton("➤ Send")
        send_btn.setStyleSheet(
            "background-color: #0e639c; padding: 6px 16px; font-size: 12px;"
        )
        send_btn.clicked.connect(self.send)
        sl.addWidget(send_btn)
        sl.addStretch()
        il.addLayout(sl)

        rl.addWidget(inp)
        splitter.addWidget(right)
        layout.addWidget(splitter)

        if not self.last_project or not os.path.exists(self.last_project):
            self.load_project(os.getcwd())

    def _get_resource_path(self, filename):
        """Get path to resource file (works in dev and PyInstaller)"""
        if getattr(sys, "frozen", False):
            # Running as PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running in development
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, filename)

    def refresh_models(self):
        while self.models_layout.count():
            item = self.models_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        your_ram = self.model_manager.get_system_ram_gb()
        models = self.model_manager.get_compatible_models()

        for model in models:
            model["your_ram"] = f"{your_ram:.1f}"
            ram_needed = model["ram_required_gb"]
            if ram_needed > your_ram:
                model["is_compatible"] = False
            elif ram_needed > your_ram * 0.75:
                model["is_compatible"] = True
                model["is_slow"] = True
            else:
                model["is_compatible"] = True
                model["is_slow"] = False

            card = ModelCard(
                model, self.load_model, self.delete_model, self.download_model
            )
            self.models_layout.addWidget(card)

        self.models_layout.addStretch()

    def toggle_models(self):
        if self.models_expanded:
            self.models_scroll.hide()
            self.models_toggle.setText("▶")
        else:
            self.models_scroll.show()
            self.models_toggle.setText("▼")
        self.models_expanded = not self.models_expanded

    def download_model(self, model):
        reply = QMessageBox.question(
            self,
            "Завантаження",
            f"Завантажити {model['name']} ({model['size_gb']} GB)?\n\nЦе може зайняти 5-30 хвилин.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.dialog = DownloadDialog(model, self)
            self.download_progress = {"percent": 0, "done": False, "error": None}
            self.dialog.show()

            def update_progress(percent, downloaded, total_size):
                self.download_progress["percent"] = int(percent)

            def dl():
                try:
                    mm = LocalModelManager()
                    print(f"Start download: {model['name']}")
                    result = mm.download_model(model, update_progress)
                    if result:
                        print(f"Download complete: {model['name']}")
                    else:
                        print(f"Download failed: {model['name']}")
                        self.download_progress["error"] = "Download failed"
                except Exception as e:
                    print(f"Download error: {e}")
                    self.download_progress["error"] = str(e)
                finally:
                    self.download_progress["done"] = True

            threading.Thread(target=dl, daemon=True).start()

            def check_progress():
                if self.dialog:
                    self.dialog.update_progress(self.download_progress["percent"])
                    if self.download_progress["done"]:
                        self.dialog.close()
                        self.dialog = None
                        self.refresh_models()
                        if self.download_progress["error"]:
                            self.show_error(self.download_progress["error"])
                        return
                QTimer.singleShot(200, check_progress)

            QTimer.singleShot(200, check_progress)

    def show_error(self, msg):
        QMessageBox.critical(self, "Помилка", msg)

    def load_model(self, model):
        self.chat.append(
            f"<div style='color: #0078d4; font-style: italic; padding: 8px;'>⏳ Завантаження {model['name']} в пам'ять...</div>"
        )
        self.model_status.setText("⏳ Завантаження...")
        self.model_status.setStyleSheet("color: #0078d4; font-weight: bold;")

        def load():
            try:
                import time

                path = self.model_manager.get_model_path(model["name"])
                if not path:
                    raise Exception("Model not found")

                print(f"Loading model from: {path}")
                start = time.time()

                self.inference.load_model(str(path))

                elapsed = time.time() - start
                print(f"Model loaded in {elapsed:.1f}s")

                self.current_model = model["name"]
                self.model_status.setText(f"✅ {model['name']}")
                self.model_status.setStyleSheet("color: #4ec9b0; font-weight: bold;")
                self.chat.append(
                    "<div style='background: #1e3a2a; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #4ec9b0;'>✓ Модель готова!</span></div>"
                )
            except Exception as e:
                import traceback

                print(f"Error: {e}")
                print(traceback.format_exc())
                self.model_status.setText("⚠️ Помилка")
                self.model_status.setStyleSheet("color: #f44747; font-weight: bold;")
                self.chat.append(
                    f"<div style='color: #f44747; padding: 8px;'>✗ {e}</div>"
                )

        threading.Thread(target=load, daemon=True).start()

    def delete_model(self, model):
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Delete {model['name']}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.model_manager.delete_model(model["name"]):
                self.chat.append(
                    f"<div style='background: #3a2a1a; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #f44747;'>✓ Видалено: {model['name']}</span></div>"
                )
                self.refresh_models()
                if self.current_model == model["name"]:
                    self.inference.unload()
                    self.current_model = None
                    self.model_status.setText("⚠️ Немає моделі")
                    self.model_status.setStyleSheet(
                        "color: #f44747; font-weight: bold; font-size: 12px;"
                    )

    def create_project(self):
        d = QFileDialog()
        d.setFileMode(QFileDialog.Directory)
        d.setOption(QFileDialog.ShowDirsOnly)
        if d.exec():
            path = d.selectedFiles()[0]
            try:
                os.makedirs(os.path.join(path, "src"), exist_ok=True)
                with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
                    f.write(f"# Project\n\n{datetime.now()}\n")
                self.load_project(path)
                self.chat.append(
                    "<div style='background: #1e3a2a; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #4ec9b0;'>✓ Створено</span></div>"
                )
            except Exception as e:
                self.chat.append(
                    f"<div style='background: #3a2020; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #f44747;'>✗ Помилка: {str(e)}</span></div>"
                )

    def open_project(self):
        d = QFileDialog()
        d.setFileMode(QFileDialog.Directory)
        if d.exec():
            self.load_project(d.selectedFiles()[0])

    def load_project(self, path):
        self.project_path = path
        self.project_label.setText(f"📁 {os.path.basename(path)}")
        self.refresh_files()
        cfg = load_config()
        cfg["last_project"] = path
        save_config(cfg)
        self.chat.append(
            "<div style='color: #888; font-style: italic; padding: 8px;'>📖 Індексація...</div>"
        )
        self.context_engine.index_project(path)
        self.context_label.setText(f"🧠 {len(self.context_engine.chunks)}")
        self.chat.append(
            f"<div style='background: #1e3a2a; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #4ec9b0;'>✓ Проіндексовано: {len(self.context_engine.chunks)} файлів</span></div>"
        )

    def refresh_files(self):
        self.files.clear()
        if not self.project_path:
            return
        root = QTreeWidgetItem(self.files, [os.path.basename(self.project_path)])
        root.setForeground(0, QColor("#0078d4"))
        self._add_files(self.project_path, root)
        self.files.expandAll()

    def _add_files(self, root, parent):
        try:
            for item in sorted(os.listdir(root)):
                if item.startswith(".") or item in [
                    "__pycache__",
                    "node_modules",
                    ".git",
                    "dist",
                ]:
                    continue
                path = os.path.join(root, item)
                if os.path.isdir(path):
                    child = QTreeWidgetItem(parent, [f"📁 {item}"])
                    child.setForeground(0, QColor("#dcdcaa"))
                    self._add_files(path, child)
                elif item.endswith((".py", ".md", ".txt", ".js", ".ts", ".json")):
                    icon = "🐍" if item.endswith(".py") else "📄"
                    child = QTreeWidgetItem(parent, [f"{icon} {item}"])
                    child.setForeground(0, QColor("#9cdcfe"))
                    child.setData(0, Qt.UserRole, path)
        except:
            pass

    def open_file(self):
        items = self.files.selectedItems()
        if not items:
            return
        self.open_file_item(items[0])

    def open_file_item(self, item):
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.chat.append(f"""<div style='background: #1e1e1e; padding: 8px; border-radius: 8px; margin: 4px 0;'>
                <div style='color: #0078d4; font-weight: bold; font-size: 10px;'>📄 {os.path.basename(path)}</div>
                <pre style='color: #9cdcfe; font-size: 10px; white-space: pre-wrap;'>{content[:1500]}</pre>
            </div>""")
            self.current_file = path
        except Exception as e:
            self.chat.append(f"<div style='color: #f44747; padding: 8px;'>✗ {e}</div>")

    def add_to_context(self):
        items = self.files.selectedItems()
        if not items:
            return
        item = items[0]
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.context_engine.add_file(path, f.read())
            self.context_label.setText(f"🧠 {len(self.context_engine.chunks)}")
            self.chat.append(
                "<div style='background: #1e3a2a; padding: 8px; border-radius: 8px; margin: 4px 0;'><span style='color: #4ec9b0;'>✓ Додано до контексту</span></div>"
            )
        except Exception as e:
            self.chat.append(f"<div style='color: #f44747; padding: 8px;'>✗ {e}</div>")

    def open_external(self):
        if not self.editors:
            return
        name = self.editor_combo.currentText()
        editor = next((e for e in self.editors if e["name"] == name), None)
        if not editor:
            return
        path = self.current_file or self.project_path
        if path:
            subprocess.Popen([editor["path"], path])

    def git_menu(self):
        if not self.project_path:
            return
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252525;
                border: 1px solid #3e3e3e;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                color: #d4d4d4;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0e639c;
            }
        """)

        repo_menu = QMenu("📂 Репозиторій", self)
        repo_menu.setStyleSheet(menu.styleSheet())
        repo_menu.addAction("📦 git init", lambda: self.git_cmd("git init"))
        repo_menu.addAction("📋 git status", lambda: self.git_cmd("git status"))
        repo_menu.addAction(
            "📊 git status --short", lambda: self.git_cmd("git status --short")
        )

        changes_menu = QMenu("📝 Зміни", self)
        changes_menu.setStyleSheet(menu.styleSheet())
        changes_menu.addAction("➕ git add .", lambda: self.git_cmd("git add ."))
        changes_menu.addAction("➕ git add -A", lambda: self.git_cmd("git add -A"))
        changes_menu.addAction("📄 git diff", lambda: self.git_cmd("git diff"))
        changes_menu.addAction(
            "📋 git diff --staged", lambda: self.git_cmd("git diff --staged")
        )

        commit_menu = QMenu("💾 Commit", self)
        commit_menu.setStyleSheet(menu.styleSheet())
        commit_menu.addAction("📜 Створити commit", self.git_commit)
        commit_menu.addAction("📜 amend", lambda: self.git_cmd("git commit --amend"))

        remote_menu = QMenu("☁️ Remote", self)
        remote_menu.setStyleSheet(menu.styleSheet())
        remote_menu.addAction("🚀 git push", lambda: self.git_cmd("git push"))
        remote_menu.addAction(
            "🚀 git push -u origin main",
            lambda: self.git_cmd("git push -u origin main"),
        )
        remote_menu.addAction("🔄 git pull", lambda: self.git_cmd("git pull"))
        remote_menu.addAction("🔄 git fetch", lambda: self.git_cmd("git fetch"))

        log_menu = QMenu("📜 Історія", self)
        log_menu.setStyleSheet(menu.styleSheet())
        log_menu.addAction("📜 git log", lambda: self.git_cmd("git log --oneline -10"))
        log_menu.addAction(
            "📜 git log --graph", lambda: self.git_cmd("git log --oneline --graph -10")
        )

        menu.addMenu(repo_menu)
        menu.addMenu(changes_menu)
        menu.addMenu(commit_menu)
        menu.addMenu(remote_menu)
        menu.addMenu(log_menu)

        menu.exec_(self.mapToGlobal(self.sender().pos()))

    def git_cmd(self, cmd):
        if cmd == "commit":
            self.git_commit()
            return
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, cwd=self.project_path
            )
            out = r.stdout or r.stderr
            if out:
                self.chat.append(
                    f"<div style='background: #252525; padding: 10px; border-radius: 8px; margin: 4px 0;'><pre style='color: #9cdcfe; font-size: 11px; white-space: pre-wrap;'>{out}</pre></div>"
                )
        except Exception as e:
            self.chat.append(f"<div style='color: #f44747; padding: 8px;'>✗ {e}</div>")

    def git_commit(self):
        if not self.current_model:
            self.chat.append(
                "<div style='background: #3a2a1a; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #f44747;'>⚠️ Спочатку завантажте модель!</span></div>"
            )
            return
        r = subprocess.run(
            "git status --short",
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )
        if r.stdout:
            self.chat_history.append(
                {"role": "user", "content": f"Commit:\n{r.stdout}"}
            )
            try:
                msg = self.inference.chat(self.chat_history, max_tokens=50)
                self.git_cmd(f'git commit -m "{msg.strip().strip(chr(34) + chr(39))}"')
            except Exception as e:
                self.chat.append(
                    f"<div style='background: #3a2020; padding: 12px; border-radius: 8px; margin: 6px 40px 6px 0;'><span style='color: #f44747; font-size: 13px;'>✗ {e}</span></div>"
                )
            self.chat_history.clear()

    def key_press(self, e):
        if e.key() == Qt.Key_Return and not e.modifiers() & Qt.ShiftModifier:
            self.send()
        else:
            QTextEdit.keyPressEvent(self.chat_input, e)

    def send(self):
        text = self.chat_input.toPlainText().strip()
        if not text:
            return
        if not self.current_model:
            self.chat.append(
                "<div style='background: #3a2a1a; padding: 10px; border-radius: 8px; margin: 4px 0;'><span style='color: #f44747;'>⚠️ Спочатку завантажте модель!</span></div>"
            )
            return
        if self.is_generating:
            return

        text_lower = text.lower()

        # Check for image file references
        image_patterns = [
            "image file",
            "picture file",
            "photo file",
            "screenshot file",
            "upload image",
            "send image",
            "attach image",
            "add image",
            "зображення",
            "картинку",
            "фото",
            "скріншот",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
        ]

        is_image_request = any(p in text_lower for p in image_patterns)

        if is_image_request:
            self.chat.append(
                "<div style='background: #2a2525; padding: 14px; border-radius: 16px; margin: 8px 0; border: 1px solid #3a3535;'>"
                "<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 8px;'>"
                "<span style='font-size: 24px;'>🖼️</span>"
                "<span style='color: #f48771; font-size: 14px; font-weight: 600;'>Зображення не підтримуються</span>"
                "</div>"
                "<div style='color: #888; font-size: 12px; line-height: 1.4;'>Локальні GGUF моделі працюють лише з текстом.<br>Картинки, фото та скріншоти не підтримуються.</div>"
                "</div>"
            )
            return

        self.chat.append(f"""<div style='background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #264f78,stop:1 #2a5a8a); 
            padding: 12px; border-radius: 12px; margin: 6px 0 6px 40px;'>
            <div style='color: #4ec9b0; font-size: 11px; margin-bottom: 4px;'>👤</div>
            <div style='color: #d4d4d4; font-size: 13px;'>{text}</div>
        </div>""")
        self.chat_input.clear()
        ctx = (
            self.context_engine.get_context_for_query(text, k=5)
            if self.context_engine.chunks
            else ""
        )
        msg = f"Context:\n{ctx}\n\n{text}" if ctx else text
        self.chat_history.append({"role": "user", "content": msg})

        self.is_generating = True
        self.work_status.setText("Думає...")
        self.status_icon.setStyleSheet("color: #0078d4; font-size: 10px;")
        self.work_status.parent().setStyleSheet("""
            QFrame {
                background-color: #1a2a3a;
                border-radius: 12px;
                padding: 4px 12px;
            }
        """)
        self.typing.start()

        response_data = {"ready": False, "response": None, "error": None}

        def generate_response():
            try:
                response_data["response"] = self.inference.chat(self.chat_history)
                self.chat_history.append(
                    {"role": "assistant", "content": response_data["response"]}
                )
                response_data["ready"] = True
            except Exception as e:
                response_data["error"] = str(e)
                response_data["ready"] = True

        threading.Thread(target=generate_response, daemon=True).start()

        QTimer.singleShot(200, lambda: self.check_generation(response_data))

    def check_generation(self, response_data):
        if self.is_generating and not response_data.get("ready"):
            QTimer.singleShot(200, lambda: self.check_generation(response_data))
            return

        if response_data.get("error"):
            self.typing.stop()
            self.work_status.setText("Готовий")
            self.status_icon.setStyleSheet("color: #4ec9b0; font-size: 10px;")
            self.work_status.parent().setStyleSheet("""
                QFrame {
                    background-color: #1e3a2a;
                    border-radius: 12px;
                    padding: 4px 12px;
                }
            """)
            self.chat.append(
                f"<div style='color: #f44747; padding: 8px;'>✗ {response_data['error']}</div>"
            )
        else:
            self.typing.stop()
            self.work_status.setText("Готовий")
            self.status_icon.setStyleSheet("color: #4ec9b0; font-size: 10px;")
            self.work_status.parent().setStyleSheet("""
                QFrame {
                    background-color: #1e3a2a;
                    border-radius: 12px;
                    padding: 4px 12px;
                }
            """)
            response = response_data.get("response", "")
            self.chat.append(f"""<div style='background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a3a2a,stop:1 #1e4a34); 
                padding: 12px; border-radius: 12px; margin: 6px 40px 6px 0;'>
                <div style='color: #4ec9b0; font-size: 11px; margin-bottom: 4px;'>🧠</div>
                <div style='color: #d4d4d4; font-size: 13px; white-space: pre-wrap;'>{response}</div>
            </div>""")

        self.is_generating = False

    def closeEvent(self, e):
        try:
            self.inference.unload()
        except:
            pass
        cfg = load_config()
        if self.project_path:
            cfg["last_project"] = self.project_path
        save_config(cfg)
        e.accept()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
