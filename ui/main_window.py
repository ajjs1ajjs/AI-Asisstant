# 🚀 AI Coding IDE - Full Production Version

import json
import os
import threading
import traceback
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QWidget, QTextEdit, QPushButton, QScrollArea
)

# Internal Imports
from context_engine import ContextEngine
from local_engine import get_inference
from model_manager import LocalModelManager
from settings_dialog import SettingsDialog
from orchestrator import ModelOrchestrator, LocalProvider
from agent_tools import AgentTools
from autocomplete import AutocompleteEngine  # Імпортуємо ваш двигун
from ui.components import (
    ChatBubble, ThoughtBubble, TerminalWidget, FileTree, ModelCard, DownloadDialog
)
from ui.knowledge_graph import KnowledgeGraphWidget
from ui.time_machine import TimeMachineWidget
from ui.analyst import DataAnalystWidget
from ui.jobs import BackgroundJobsWidget
from threads.workers import AsyncChatWorker
from git_integration import GitIntegration

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_path = os.getcwd()
        self.chat_history = []
        self.git = GitIntegration(self.project_path)
        
        self.setWindowTitle("AI Coding IDE v6.0")
        self.resize(1200, 800)

        # Core Engines
        self.model_manager = LocalModelManager()
        self.inference = get_inference()
        self.orchestrator = ModelOrchestrator()
        self.orchestrator.add_provider("local", LocalProvider(self.inference))
        self.agent_tools = AgentTools(self.project_path)
        
        # New: Integration of Context and Autocomplete
        self.context_engine = ContextEngine()
        self.autocomplete = AutocompleteEngine(self.project_path)
        
        self.init_ui()
        self.refresh_models()
        self.refresh_git_log()

    def init_ui(self):
        central = QWidget()
        layout = QHBoxLayout(central)
        self.splitter = QSplitter(Qt.Horizontal)
        
        # LEFT: Tabs
        self.tabs = QTabWidget()
        self.file_tree = FileTree()
        self.file_tree.file_open_requested.connect(self.open_file)
        self.tabs.addTab(self.file_tree, "📂 Файли")
        
        self.models_content = QWidget()
        self.models_layout = QVBoxLayout(self.models_content)
        self.tabs.addTab(self.models_content, "🤖 Моделі")
        
        self.splitter.addWidget(self.tabs)
        
        # CENTER/RIGHT
        self.main_tabs = QTabWidget()
        
        # Chat with Autocomplete integration
        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_scroll = QScrollArea()
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)
        
        self.chat_input = QTextEdit()
        self.chat_input.textChanged.connect(self.trigger_autocomplete)
        chat_layout.addWidget(self.chat_input)
        
        self.send_btn = QPushButton("Надіслати")
        self.send_btn.clicked.connect(self.send_message)
        chat_layout.addWidget(self.send_btn)
        self.main_tabs.addTab(self.chat_widget, "💬 Чат")
        
        # Tabs from original structure
        self.main_tabs.addTab(DataAnalystWidget(), "📊 Аналітик")
        self.main_tabs.addTab(TimeMachineWidget(), "⏳ Time Machine")
        self.main_tabs.addTab(BackgroundJobsWidget(), "⚙️ Завдання")
        self.main_tabs.addTab(TerminalWidget(), "💻 Термінал")
        
        self.splitter.addWidget(self.main_tabs)
        layout.addWidget(self.splitter)
        self.setCentralWidget(central)

    def trigger_autocomplete(self):
        text = self.chat_input.toPlainText()
        suggestions = self.autocomplete.get_suggestions(text)
        # Логіка відображення підказок (якщо є в UI компонентах)
        
    def send_message(self):
        text = self.chat_input.toPlainText().strip()
        if not text: return
        
        # Context Injection (FAISS)
        context = self.context_engine.get_relevant_context(text)
        prompt = f"Контекст проекту: {context}\n\nЗапит: {text}"
        
        self.add_chat_bubble(text, "user")
        self.chat_input.clear()
        self.chat_history.append({"role": "user", "content": prompt})
        
        self.worker = AsyncChatWorker(self.orchestrator, self.chat_history)
        self.worker.chunk_received.connect(self.on_ai_chunk)
        self.worker.finished.connect(lambda: self.chat_history.append({"role": "assistant", "content": self.current_ai_text}))
        self.worker.start()
        self.current_ai_text = ""
        self.active_bubble = self.add_chat_bubble("", "assistant")

    def on_ai_chunk(self, chunk):
        self.current_ai_text += chunk
        self.active_bubble.update_text(self.current_ai_text)
    
    def add_chat_bubble(self, text, role="assistant"):
        bubble = ChatBubble(text, role)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        return bubble

    def refresh_models(self):
        while self.models_layout.count():
            item = self.models_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for m in self.model_manager.get_compatible_models():
            card = ModelCard(m, self.load_model, self.delete_model, self.download_model)
            self.models_layout.addWidget(card)
        self.models_layout.addStretch()

    def refresh_git_log(self):
        # Оновлення логу для Time Machine
        pass

    def load_model(self, model): threading.Thread(target=self.inference.load_model, args=(model.get('name'),), daemon=True).start()
    def download_model(self, model): DownloadDialog(model, self.model_manager).exec(); self.refresh_models()
    def delete_model(self, model): self.model_manager.delete_model(model.get('name')); self.refresh_models()
    def open_file(self, path): print(f"Opening: {path}")
