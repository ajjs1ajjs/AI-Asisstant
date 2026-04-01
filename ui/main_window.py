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
from PySide6.QtGui import QColor, QDrag, QPainter, QPixmap, QKeySequence, QIcon, QCursor
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
    QInputDialog,
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


from ui.components import DownloadDialog, ModelCard, FileTree, TypingIndicator, ChatBubble
from threads.workers import AsyncChatWorker

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
        self.settings = get_settings()
        self.agent_tools = AgentTools(os.getcwd())
        self.setup_orchestrator()

        self.current_model = None
        self.current_file = None
        self.chat_history = []
        self.project_path = None
        self.is_generating = False
        self.attached_files = []  # Прикріплені файли

        config = load_config()
        self.last_project = config.get("last_project", "")

        self.init_ui()
        self.create_menu_bar()
        self.refresh_models()
        
        self.current_bubble = None # For streaming

        if self.last_project and os.path.exists(self.last_project):
            self.load_project(self.last_project)

    def setup_orchestrator(self):
        self.orchestrator = ModelOrchestrator()
        api_keys = self.settings.settings.api_keys
        
        if api_keys.get("groq"):
            self.orchestrator.add_provider("groq", GroqProvider(api_keys["groq"]))
            self.orchestrator.add_model(Model("llama-3.1-70b-versatile", "groq", supports_tools=True, score=0.9, requires_key=True))
        if api_keys.get("openrouter"):
            self.orchestrator.add_provider("openrouter", OpenRouterProvider(api_keys["openrouter"]))
            self.orchestrator.add_model(Model("anthropic/claude-3.5-sonnet", "openrouter", supports_tools=True, score=1.0, requires_key=True))
        if api_keys.get("deepseek"):
            self.orchestrator.add_provider("deepseek", DeepSeekProvider(api_keys["deepseek"]))
            self.orchestrator.add_model(Model("deepseek-chat", "deepseek", supports_tools=True, score=0.95, requires_key=True))

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
        edit_menu.addSeparator()
        edit_menu.addAction("⚙️ Налаштування", self.open_settings)

        model_menu = menubar.addMenu("🧠 Модель")
        model_menu.addAction("🔄 Оновити список", self.refresh_models)
        model_menu.addAction("🗑️ Видалити модель", self.delete_current_model)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            # Setup orchestrator again if API keys changed
            self.setup_orchestrator()

    def clear_chat(self):
        while self.chat_layout.count() > 1: # Keep the stretch
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.chat_history.clear()

    def clear_context(self):
        self.context_engine.chunks = []
        self.context_label.setText("🧠 0")
        self.add_chat_bubble("Контекст очищено", "system")

    def copy_history(self):
        text_lines = []
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), ChatBubble):
                role = item.widget().role
                content = item.widget().text
                text_lines.append(f"[{role.upper()}] {content}")
        QApplication.clipboard().setText("\n\n".join(text_lines))

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

    def _start_ai_generation(self):
        """Запустити генерацію AI відповіді"""
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

        self._run_orchestrator_chat(tools_mode=False)

    def _analyze_project_structure(self) -> str:
        """Аналізувати структуру проекту"""
        if not self.project_path:
            return ""

        analysis = []
        analysis.append(f"📁 Project: {self.project_path}")
        analysis.append("=" * 60)

        total_files = 0
        total_lines = 0
        extensions = {}

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "node_modules", "venv", "dist", "build"]]
            for file in files:
                ext = os.path.splitext(file)[1]
                extensions[ext] = extensions.get(ext, 0) + 1
                total_files += 1
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += len(f.readlines())
                except (OSError, UnicodeDecodeError):
                    pass

        analysis.append(f"📊 Files: {total_files} | Lines: {total_lines:,}")
        analysis.append(f"📎 Extensions: {dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:8])}")

        # Структура
        analysis.append("\n📂 Structure:")
        for root, dirs, files in os.walk(self.project_path):
            level = root.replace(self.project_path, '').count(os.sep)
            if level > 2:
                continue
            indent = '  ' * level
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "node_modules", "venv"]]
            analysis.append(f"{indent}📁 {os.path.basename(root)}/")
            for file in files[:3]:
                analysis.append(f"{indent}  📄 {file}")

        # Мови
        lang_map = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".java": "Java", ".cpp": "C++", ".cs": "C#", ".go": "Go", ".rs": "Rust"}
        langs = [lang_map.get(ext, ext) for ext in extensions.keys() if ext in lang_map]
        if langs:
            analysis.append(f"\n💻 Languages: {', '.join(langs)}")

        return "\n".join(analysis)

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

        ph = QHBoxLayout()
        proj_title = QLabel("📁 Проєкт")
        proj_title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 12px;")
        ph.addWidget(proj_title)
        
        ph.addStretch()
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover { color: #3b82f6; }
        """)
        refresh_btn.clicked.connect(self.refresh_files)
        ph.addWidget(refresh_btn)
        pl.addLayout(ph)

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
        self.files.setMinimumHeight(200)
        
        # Connect FileTree signals
        self.files.file_open_requested.connect(self.open_file_path)
        self.files.add_to_chat_requested.connect(self._add_file_to_chat)
        self.files.new_file_requested.connect(self.new_file)
        self.files.new_folder_requested.connect(self.new_folder)
        self.files.refresh_requested.connect(self.refresh_files)
        self.files.delete_requested.connect(self.delete_item)
        self.files.rename_requested.connect(self.rename_item)
        
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

        # Chat Area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("QScrollArea { background-color: #0a0c10; border: none; }")
        
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background-color: #0a0c10;")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(10, 20, 10, 20)
        self.chat_layout.setSpacing(0)
        self.chat_layout.addStretch() # Push bubbles to the top
        
        self.chat_scroll.setWidget(self.chat_widget)
        rl.addWidget(self.chat_scroll, 1)

        # Typing
        self.typing = TypingIndicator()
        self.typing.hide()
        rl.addWidget(self.typing)

        # Input
        inp = QFrame()
        inp.setFixedHeight(140)
        inp.setStyleSheet("QFrame { background-color: #2d2d30; }")
        il = QVBoxLayout(inp)
        il.setContentsMargins(12, 10, 12, 10)
        il.setSpacing(6)

        self.chat_input = QTextEdit()
        self.chat_input.setMinimumHeight(60)
        self.chat_input.setMaximumHeight(100)
        self.chat_input.setPlaceholderText("Ask AI... (Ctrl+V для вставки, Drag&Drop для файлів)")
        self.chat_input.keyPressEvent = self.key_press
        self.chat_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_input.setAcceptDrops(True)  # Дозволити drag-and-drop
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

        # Файли
        self.files_label = QLabel("")
        self.files_label.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        self.files_label.setWordWrap(True)
        il.addWidget(self.files_label)

        sl = QHBoxLayout()
        
        # Кнопка додавання файлів
        attach_btn = QPushButton("📎 Файл")
        attach_btn.setFixedSize(70, 28)
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                color: #d4d4d4;
                border-radius: 6px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #4e4e4e; }
        """)
        attach_btn.clicked.connect(self.attach_file)
        sl.addWidget(attach_btn)
        
        send_btn = QPushButton("➤ Send")
        send_btn.setStyleSheet(
            "background-color: #0e639c; padding: 6px 16px; font-size: 12px;"
        )
        send_btn.clicked.connect(self.send)
        sl.addWidget(send_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                padding: 6px 16px;
                font-size: 11px;
                border-radius: 6px;
                color: #888;
            }
            QPushButton:enabled {
                background-color: #f43f5e;
                color: white;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_generation)
        sl.addWidget(self.stop_btn)

        sl.addStretch()
        il.addLayout(sl)

        rl.addWidget(inp, 0)  # Input container - no stretch
        splitter.addWidget(right)
        layout.addWidget(splitter)

        # Stretch factors
        splitter.setStretchFactor(0, 0)  # Sidebar - fixed
        splitter.setStretchFactor(1, 1)  # Right - expandable

        if not self.last_project or not os.path.exists(self.last_project):
            self.load_project(os.getcwd())

    def add_chat_bubble(self, text, role="assistant"):
        """Помічник для додавання нової бульбашки в чат"""
        bubble = ChatBubble(text, role)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Автоматична прокрутка вниз
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))
        return bubble

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
        self.add_chat_bubble(f"⏳ Завантаження {model['name']} в пам'ять...", "system")
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
                self.model_status.setStyleSheet("color: #10b981; font-weight: bold;")
                self.add_chat_bubble("✓ Модель готова!", "assistant")
            except Exception as e:
                import traceback

                print(f"Error: {e}")
                print(traceback.format_exc())
                self.model_status.setText("⚠️ Помилка")
                self.model_status.setStyleSheet("color: #f43f5e; font-weight: bold;")
                self.add_chat_bubble(f"✗ Помилка: {e}", "system")

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
                self.add_chat_bubble(f"✓ Видалено: {model['name']}", "system")
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
                self.add_chat_bubble("✓ Проект створено", "system")
            except Exception as e:
                self.add_chat_bubble(f"✗ Помилка створення проекту: {e}", "system")

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
        
        # Індексація проекту
        self.add_chat_bubble("📖 Індексація проекту...", "system")
        stats = self.context_engine.index_project(path)
        self.context_label.setText(f"🧠 {stats['files_indexed']}")
        self.add_chat_bubble(f"✓ Проіндексовано: {stats['files_indexed']} файлів, {stats['chunks_added']} чанків", "system")

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
        except (OSError, UnicodeDecodeError):
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
            self.add_chat_bubble(f"📄 {os.path.basename(path)}\n\n```\n{content[:1500]}\n```", "system")
            self.current_file = path
        except Exception as e:
            self.add_chat_bubble(f"✗ Помилка: {e}", "system")

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
            self.add_chat_bubble("✓ Додано до контексту", "system")
        except Exception as e:
            self.add_chat_bubble(f"✗ Помилка: {e}", "system")

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
                self.add_chat_bubble(f"GIT Output:\n{out}", "system")
        except Exception as e:
            self.add_chat_bubble(f"✗ Помилка Git: {e}", "system")

    def git_commit(self):
        if not self.current_model:
            self.add_chat_bubble("⚠️ Спочатку завантажте модель!", "system")
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
                self.add_chat_bubble(f"✗ Помилка Commit: {e}", "system")
            self.chat_history.clear()

    def attach_file(self):
        """Прикріпити файл до чату"""
        from PySide6.QtWidgets import QFileDialog
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Оберіть файли",
            "",
            "Text Files (*.py *.md *.txt *.json *.yaml *.yml *.js *.ts *.html *.css);;"
            "All Files (*)"
        )
        
        for path in file_paths:
            self._add_file_to_chat(path)

    def _add_file_to_chat(self, file_path):
        """Додати файл до списку прикріплених"""
        if file_path in self.attached_files:
            return
        
        self.attached_files.append(file_path)
        self._update_files_label()

    def _update_files_label(self):
        """Оновити мітку файлів"""
        if not self.attached_files:
            self.files_label.setText("")
            return
        
        names = [os.path.basename(f) for f in self.attached_files]
        if len(names) <= 3:
            self.files_label.setText("📎 " + ", ".join(names))
        else:
            self.files_label.setText(f"📎 {len(self.attached_files)} файлів")

    def clear_attached_files(self):
        """Очистити прикріплені файли"""
        self.attached_files.clear()
        self._update_files_label()

    def read_file_content(self, file_path):
        """Прочитати вміст файлу"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Текстові файли
        text_extensions = ['.py', '.md', '.txt', '.json', '.yaml', '.yml', 
                          '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
                          '.cpp', '.c', '.h', '.java', '.cs', '.go', '.rs',
                          '.php', '.rb', '.swift', '.sh', '.bat', '.xml', '.csv']
        
        if ext in text_extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return f"📄 Файл: {os.path.basename(file_path)}\n\n```{ext[1:]}\n{content}\n```"
            except Exception as e:
                return f"❌ Помилка читання {os.path.basename(file_path)}: {e}"
        
        # Зображення
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        if ext in image_extensions:
            return f"🖼️ Зображення: {os.path.basename(file_path)}\n\n(Локальні моделі не підтримують аналіз зображень. Використайте хмарний API з ключем.)"
        
        # Інші файли
        return f"📁 Файл: {os.path.basename(file_path)} ({ext}, {os.path.getsize(file_path)} байт)"

    def dropEvent(self, event):
        """Обробка drop event"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path):
                        self._add_file_to_chat(file_path)
            event.accept()
        else:
            super().dropEvent(event)

    def dragEnterEvent(self, event):
        """Обробка drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def key_press(self, e):
        if e.key() == Qt.Key_Return and not e.modifiers() & Qt.ShiftModifier:
            self.send()
        else:
            QTextEdit.keyPressEvent(self.chat_input, e)

    def send(self):
        text = self.chat_input.toPlainText().strip()
        if not text and not self.attached_files:
            return
        if not self.current_model:
            self.add_chat_bubble("⚠️ Спочатку завантажте модель!", "system")
            return
        if self.is_generating:
            return

        # Додаємо вміст файлів до тексту
        if self.attached_files:
            file_contents = []
            for file_path in self.attached_files:
                content = self.read_file_content(file_path)
                file_contents.append(content)
            
            if text:
                full_text = text + "\n\n" + "\n\n".join(file_contents)
            else:
                full_text = "\n\n".join(file_contents)
            
            # Показуємо файли в чаті
            files_display = ", ".join([os.path.basename(f) for f in self.attached_files])
            self.add_chat_bubble(f"📎 Прикріплено: {files_display}", "system")
            
            # Очищаємо список файлів
            self.attached_files.clear()
            self._update_files_label()
        else:
            full_text = text

        text_lower = full_text.lower()

        # ========== АНАЛІЗ ПРОЕКТУ ==========
        code_analysis_patterns = [
            "проаналізуй код", "аналіз коду", "аналіз проекту", "проаналізуй проект",
            "знайди помилки", "помилки в коді", "баги в коді", "знайди баги",
            "перевір код", "аудит коду", "рефакторинг", "оптимізуй код",
            "code analysis", "analyze code", "find bugs", "code review", "refactor",
        ]

        is_code_analysis = any(p in text_lower for p in code_analysis_patterns)

        if is_code_analysis and self.project_path and self.context_engine.chunks:
            # Отримуємо контекст
            ctx = self.context_engine.get_context_for_query(text, k=10)
            
            # Аналізуємо структуру
            analysis = self._analyze_project_structure()
            
            if ctx or analysis:
                full_context = "=== PROJECT ANALYSIS ===\n"
                if analysis:
                    full_context += analysis + "\n\n"
                if ctx:
                    full_context += "=== CODE CONTEXT ===\n" + ctx + "\n\n"
                full_context += "=== TASK ===\n" + text
                
                self.add_chat_bubble(f"🔍 Аналіз проекту ({len(self.context_engine.chunks)} чанків)...", "system")
                
                system_prompt = "Ти - досвідчений розробник ПЗ. Проаналізуй код проекту: структуру, мови, архітектуру, проблеми, рекомендації. Відповідай українською."
                
                if not self.chat_history or self.chat_history[0].get("role") != "system":
                    self.chat_history.insert(0, {"role": "system", "content": system_prompt})
                
                self.chat_history.append({"role": "user", "content": full_context})
                self._start_ai_generation()
                return

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
            self.add_chat_bubble("🖼️ Зображення не підтримуються локальними GGUF моделями.", "system")
            return

        self.add_chat_bubble(text, "user")
        self.chat_input.clear()
        ctx = (
            self.context_engine.get_context_for_query(text, k=5)
            if self.context_engine.chunks
            else ""
        )
        msg = f"Context:\n{ctx}\n\n{full_text}" if ctx else full_text
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

        self._run_orchestrator_chat(tools_mode=True)

    def _run_orchestrator_chat(self, tools_mode=True):
        if not self.orchestrator.get_configured_models():
            # Fallback to local
            response_data = {"ready": False, "response": None, "error": None}
            def generate_response():
                try:
                    response_data["response"] = self.inference.chat(self.chat_history)
                    self.chat_history.append({"role": "assistant", "content": response_data["response"]})
                    response_data["ready"] = True
                except Exception as e:
                    response_data["error"] = str(e)
                    response_data["ready"] = True
            import threading
            threading.Thread(target=generate_response, daemon=True).start()
            QTimer.singleShot(200, lambda: self.check_generation(response_data))
            return

        tools_to_pass = TOOL_DEFINITIONS if tools_mode else None
        self.worker = AsyncChatWorker(self.orchestrator, self.chat_history, tools=tools_to_pass)
        
        self.current_bubble = self.add_chat_bubble("", "assistant")
        self.streaming_text = ""
        
        self.worker.chunk_received.connect(self._on_chunk)
        self.worker.tool_called.connect(self._on_tool_call)
        self.worker.finished_success.connect(self._on_chat_success)
        self.worker.error.connect(self._on_chat_error)
        self.worker.status_changed.connect(self._update_status)
        
        self.stop_btn.setEnabled(True)
        self.worker.start()

    def _on_chunk(self, chunk):
        self.typing.stop()
        self.streaming_text += chunk
        if self.current_bubble:
            self.current_bubble.update_text(self.streaming_text)
        
        # Scroll to bottom smoothly
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )

    def _on_tool_call(self, message):
        self.chat_history.append(message)
        for call in message.get("tool_calls", []):
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            
            self._update_status(f"🛠️ Виконую {name}...")
            self.add_chat_bubble(f"🛠️ Інструмент: {name}({json.dumps(args, ensure_ascii=False)})", "system")
            
            res = "Tool unknown"
            try:
                if name == "read_file":
                    res = self.agent_tools.read_file(args.get("path", ""))
                elif name == "write_file":
                    res = str(self.agent_tools.write_file(args.get("path", ""), args.get("content", "")))
                elif name == "search_code":
                    res = json.dumps(self.agent_tools.search_code(args.get("query", "")))
                elif name == "run_command":
                    out = self.agent_tools.run_command(args.get("cmd", ""))
                    res = f"Stdout:\n{out['stdout']}\nStderr:\n{out['stderr']}"
            except Exception as e:
                res = f"Error: {e}"
                
            self.add_chat_bubble(f"✅ Результат: {str(res)[:200]}...", "system")
            
            self.chat_history.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "name": name,
                "content": str(res)
            })
            
        # Recursive call to continue reasoning
        self._run_orchestrator_chat(tools_mode=True)

    def _on_chat_success(self, full_response):
        if not hasattr(self.worker, 'is_tool_call') or not self.worker.is_tool_call:
            self.chat_history.append({"role": "assistant", "content": full_response})
            self._finish_generation()

    def _on_chat_error(self, err):
        self.add_chat_bubble(f"✗ Помилка: {err}", "system")
        self._finish_generation()

    def _finish_generation(self):
        self.is_generating = False
        self.typing.stop()
        self.stop_btn.setEnabled(False)
        self.work_status.setText("Готовий")
        self.status_icon.setStyleSheet("color: #10b981; font-size: 10px;")
        self.work_status.parent().setStyleSheet("""
            QFrame {
                background-color: #0f1115;
                border: 1px solid #1a1d23;
                border-radius: 12px;
                padding: 4px 12px;
            }
        """)

    def check_generation(self, response_data):
        if self.is_generating and not response_data.get("ready"):
            QTimer.singleShot(200, lambda: self.check_generation(response_data))
            return

        if response_data.get("error"):
            self._finish_generation()
            self.add_chat_bubble(f"✗ {response_data['error']}", "system")
        else:
            self._finish_generation()
            response = response_data.get("response", "")
            self.add_chat_bubble(response, "assistant")

        self.is_generating = False

    def closeEvent(self, e):
        try:
            self.inference.unload()
        except (OSError, UnicodeDecodeError):
            pass
        cfg = load_config()
        if self.project_path:
            cfg["last_project"] = self.project_path
        save_config(cfg)
        e.accept()


    def stop_generation(self):
        if hasattr(self, "worker") and self.worker:
            self.worker.stop()
            self.add_chat_bubble("⚠️ Генерацію зупинено.", "system")
            self._on_worker_finished("")

    def _update_status(self, text):
        self.work_status.setText(text)

    def new_file(self, parent_dir):
        if not parent_dir:
            parent_dir = self.project_path
        name, ok = QInputDialog.getText(self, "Новий файл", "Назва файлу:")
        if ok and name:
            try:
                path = os.path.join(parent_dir, name)
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")
                self.refresh_files()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def new_folder(self, parent_dir):
        if not parent_dir:
            parent_dir = self.project_path
        name, ok = QInputDialog.getText(self, "Нова папка", "Назва папки:")
        if ok and name:
            try:
                os.makedirs(os.path.join(parent_dir, name), exist_ok=True)
                self.refresh_files()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def delete_item(self, path):
        reply = QMessageBox.question(self, "Видалити", f"Ви впевнені, що хочете видалити {os.path.basename(path)}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                import shutil
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.refresh_files()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def rename_item(self, path):
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Перейменувати", "Нова назва:", text=old_name)
        if ok and new_name and new_name != old_name:
            try:
                new_path = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, new_path)
                self.refresh_files()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def open_file_path(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.add_chat_bubble(f"📄 {os.path.basename(path)}\n\n```\n{content[:1500]}\n```", "system")
            self.current_file = path
        except Exception as e:
            self.add_chat_bubble(f"✗ Помилка: {e}", "system")
