# AI Coding IDE - Full Production Version

import json
import os
import shutil
import threading

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from agent_tools import AgentTools, TOOL_DEFINITIONS
from autocomplete import AutocompleteEngine
from context_engine import ContextEngine
from git_integration import GitIntegration
from local_engine import get_inference
from model_manager import LocalModelManager
from orchestrator import (
    DeepSeekProvider,
    GroqProvider,
    LocalProvider,
    Model,
    ModelOrchestrator,
    OpenRouterProvider,
    QwenProvider,
    SiliconFlowProvider,
)
from settings import get_settings
from threads.workers import AsyncChatWorker
from ui.analyst import DataAnalystWidget
from ui.components import (
    ChatBubble,
    DownloadDialog,
    FileTree,
    ModelCard,
    TerminalWidget,
    StatusIndicator,
)
from ui.editor import EditorTabs
from ui.jobs import BackgroundJobsWidget
from ui.time_machine import TimeMachineWidget


class MainWindow(QMainWindow):
    model_load_finished = Signal(bool, str, str)

    def __init__(self):
        super().__init__()
        self.project_path = os.getcwd()
        self.chat_history = []
        self.current_ai_text = ""
        self.active_bubble = None
        self.thought_bubble = None

        self.git = GitIntegration(self.project_path)
        self.settings = get_settings()

        self.setWindowTitle("AI Coding IDE v6.0")
        self.resize(1200, 800)

        self.model_manager = LocalModelManager()
        self.inference = get_inference()
        self.orchestrator = ModelOrchestrator()
        self.orchestrator.add_provider("local", LocalProvider(self.inference))
        self.agent_tools = AgentTools(self.project_path)
        self.context_engine = ContextEngine()
        self.autocomplete = AutocompleteEngine(self.project_path)

        self._configure_cloud_models()
        self.init_ui()
        self.model_load_finished.connect(self.on_model_load_finished)
        self.refresh_models()
        self.refresh_git_log()
        self._sync_local_models()

        self.file_search_dlg = None

        self._setup_shortcuts()

    def _setup_shortcuts(self):
        self.shortcut_search = QAction(self)
        self.shortcut_search.setShortcut("Ctrl+P")
        self.shortcut_search.triggered.connect(self.show_file_search)
        self.addAction(self.shortcut_search)

    def show_file_search(self):
        from ui.file_search import FileSearchDialog

        if self.file_search_dlg is None:
            self.file_search_dlg = FileSearchDialog(self.project_path, self)
            self.file_search_dlg.file_selected.connect(self.open_file)
        self.file_search_dlg.show()
        self.file_search_dlg.activateWindow()

    def init_ui(self):
        central = QWidget()
        layout = QHBoxLayout(central)
        self.splitter = QSplitter(Qt.Horizontal)

        self.tabs = QTabWidget()
        self.file_tree = FileTree()
        self.file_tree.file_open_requested.connect(self.open_file)
        self.file_tree.new_file_requested.connect(self.on_new_file_requested)
        self.file_tree.new_folder_requested.connect(self.on_new_folder_requested)
        self.file_tree.delete_requested.connect(self.on_delete_requested)
        self.file_tree.rename_requested.connect(self.on_rename_requested)
        self.file_tree.refresh_requested.connect(self.on_file_tree_refresh)
        self.tabs.addTab(self.file_tree, "Files")

        self.models_content = QWidget()
        self.models_layout = QVBoxLayout(self.models_content)
        self.models_scroll = QScrollArea()
        self.models_scroll.setWidgetResizable(True)
        self.models_container = QWidget()
        self.models_list_layout = QVBoxLayout(self.models_container)
        self.models_list_layout.addStretch()
        self.models_scroll.setWidget(self.models_container)
        self.models_layout.addWidget(self.models_scroll)
        self.tabs.addTab(self.models_content, "Models")
        self.splitter.addWidget(self.tabs)

        self.main_tabs = QTabWidget()

        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_scroll = QScrollArea()
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_scroll.setWidget(self.chat_container)
        self.chat_scroll.setWidgetResizable(True)
        chat_layout.addWidget(self.chat_scroll)

        self.chat_input = QTextEdit()
        self.chat_input.textChanged.connect(self.trigger_autocomplete)
        chat_layout.addWidget(self.chat_input)

        # Model selector
        self.model_selector = QComboBox()
        self.model_selector.setStyleSheet("""
            QComboBox {
                background-color: #1a1d23;
                color: #f1f5f9;
                border: 1px solid #2d3139;
                border-radius: 4px;
                padding: 6px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.model_selector.currentIndexChanged.connect(self.on_model_selected)
        chat_layout.addWidget(self.model_selector)

        # Status indicator
        self.status_indicator = StatusIndicator()
        chat_layout.addWidget(self.status_indicator)

        # Stream status label - more visible
        self.stream_status = QLabel("Ready")
        self.stream_status.setStyleSheet("""
            color: #94a3b8;
            font-size: 12px;
            padding: 8px;
            background-color: #1e293b;
            border-radius: 4px;
        """)
        self.stream_status.setAlignment(Qt.AlignCenter)
        chat_layout.addWidget(self.stream_status)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        chat_layout.addWidget(self.send_btn)
        self.main_tabs.addTab(self.chat_widget, "Chat")

        self.editor_tabs = EditorTabs()
        self.main_tabs.addTab(self.editor_tabs, "Editor")

        self.main_tabs.addTab(DataAnalystWidget(), "Analyst")
        self.main_tabs.addTab(TimeMachineWidget(), "Time Machine")
        self.main_tabs.addTab(BackgroundJobsWidget(), "Jobs")
        self.main_tabs.addTab(TerminalWidget(), "Terminal")

        self.splitter.addWidget(self.main_tabs)
        layout.addWidget(self.splitter)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setSizes([250, 750])
        self.setCentralWidget(central)

    def _configure_cloud_models(self):
        api_keys = self.settings.settings.api_keys
        provider_specs = [
            (
                "groq",
                GroqProvider(api_keys.get("groq", "")),
                [
                    Model(
                        "llama-3.1-70b-versatile",
                        "groq",
                        score=0.95,
                        latency=0.2,
                        supports_tools=True,
                    ),
                    Model(
                        "llama-3.1-8b-instant",
                        "groq",
                        score=0.84,
                        latency=0.05,
                        supports_tools=True,
                    ),
                ],
            ),
            (
                "openrouter",
                OpenRouterProvider(api_keys.get("openrouter", "")),
                [
                    Model(
                        "anthropic/claude-3.5-sonnet",
                        "openrouter",
                        score=0.94,
                        latency=0.4,
                        supports_tools=True,
                    ),
                    Model(
                        "openai/gpt-4o",
                        "openrouter",
                        score=0.92,
                        latency=0.35,
                        supports_tools=True,
                    ),
                ],
            ),
            (
                "deepseek",
                DeepSeekProvider(api_keys.get("deepseek", "")),
                [
                    Model(
                        "deepseek-chat",
                        "deepseek",
                        score=0.88,
                        latency=0.25,
                        supports_tools=True,
                    ),
                    Model(
                        "deepseek-coder",
                        "deepseek",
                        score=0.90,
                        latency=0.25,
                        supports_tools=True,
                    ),
                ],
            ),
            (
                "huggingface",
                QwenProvider(
                    api_keys.get("huggingface", ""), provider_type="huggingface"
                ),
                [
                    Model(
                        "Qwen/Qwen2.5-Coder-7B-Instruct",
                        "huggingface",
                        score=0.82,
                        latency=0.4,
                        supports_tools=False,
                    ),
                ],
            ),
            (
                "siliconflow",
                SiliconFlowProvider(api_keys.get("siliconflow", "")),
                [
                    Model(
                        "Qwen/Qwen2.5-Coder-32B-Instruct",
                        "siliconflow",
                        score=0.89,
                        latency=0.35,
                        supports_tools=True,
                    ),
                ],
            ),
        ]

        for name, provider, models in provider_specs:
            self.orchestrator.add_provider(name, provider)
            for model in models:
                self.orchestrator.add_model(model)

    def trigger_autocomplete(self):
        text = self.chat_input.toPlainText()
        if text:
            self.autocomplete.get_context(text, len(text))

    def send_message(self):
        text = self.chat_input.toPlainText().strip()
        if not text:
            return

        print(f"Sending message: {text[:50]}...")

        context = self.context_engine.get_context_for_query(text, k=3)
        context_str = "\n\n".join([c["text"] for c in context]) if context else ""
        prompt = f"Project context: {context_str}\n\nUser request: {text}"

        self.add_chat_bubble(text, "user")
        self.chat_input.clear()
        self.chat_history.append({"role": "user", "content": prompt})

        self.current_ai_text = ""
        self.thought_bubble = None
        self.active_bubble = self.add_chat_bubble("", "assistant")

        # Show thinking status
        self.status_indicator.set_status("thinking")
        self.stream_status.setText("🔄 Starting...")
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Thinking...")

        model_name = getattr(self, "current_model", None)
        if model_name:
            print(f"Using model: {model_name.name}")
            model_str = model_name.name
        else:
            print("No model selected, will auto-select")
            model_str = None

        self.start_chat_worker(text, model_str)

    def should_use_tools(self, text):
        lowered = text.lower()
        tool_triggers = [
            "search web",
            "web search",
            "google",
            "find online",
            "search online",
            "translate",
            "run tests",
            "test project",
            "search code",
            "read file",
            "write file",
            "run command",
            "terminal",
        ]
        return any(trigger in lowered for trigger in tool_triggers)

    def start_chat_worker(self, user_text=None, model_name=None):
        tools = (
            TOOL_DEFINITIONS
            if (user_text and self.should_use_tools(user_text))
            else None
        )
        self.worker = AsyncChatWorker(
            self.orchestrator,
            list(self.chat_history),
            tools=tools,
            selected_model=model_name,
        )
        self.worker.chunk_received.connect(self.on_ai_chunk)
        self.worker.finished_success.connect(self.on_ai_finished)
        self.worker.error.connect(self.on_ai_error)
        self.worker.tool_called.connect(self.on_tool_called)
        self.worker.status_changed.connect(self.on_status_changed)
        self.worker.thought_received.connect(self.on_thought_received)
        self.worker.start()

    def on_ai_chunk(self, chunk):
        self.current_ai_text += chunk
        if self.active_bubble:
            self.active_bubble.update_text(self.current_ai_text)

        # Update stream status
        token_count = len(self.current_ai_text.split())
        status = f"📝 Streaming... ({token_count} words)"
        self.stream_status.setText(status)
        print(f"[CHUNK] {token_count} words received")

    def on_ai_finished(self, text):
        print(f"[FINISHED] Response complete: {len(text) if text else 0} chars")
        final_text = text if text is not None else self.current_ai_text
        if not final_text:
            print("[WARNING] Empty response!")
            return
        self.current_ai_text = final_text
        if self.active_bubble:
            self.active_bubble.update_text(final_text)
        self.chat_history.append({"role": "assistant", "content": final_text})

        # Hide status indicator and re-enable send button
        self.stream_status.setText(f"✅ Done ({len(final_text.split())} words)")
        self.status_indicator.set_status("idle")
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")

    def on_ai_error(self, error_text):
        print(f"[ERROR] {error_text}")
        message = f"Error: {error_text}"
        self.statusBar().showMessage(message, 8000)
        self.stream_status.setText(f"❌ {error_text}")
        if self.active_bubble:
            self.active_bubble.update_text(message)
        else:
            self.add_chat_bubble(message, "assistant")

        # Show error status and re-enable send button
        self.status_indicator.set_status("error", message)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")

    def on_status_changed(self, status_text):
        print(f"[STATUS] {status_text}")
        self.statusBar().showMessage(status_text)
        self.stream_status.setText(status_text)

        # Update visual status indicator based on status text
        if "thinking" in status_text.lower() or "processing" in status_text.lower():
            self.status_indicator.set_status("thinking", status_text)
        elif "tool" in status_text.lower():
            self.status_indicator.set_status("tool_calling", status_text)
        elif self.active_bubble and not self.current_ai_text:
            self.active_bubble.update_text(status_text)

    def on_thought_received(self, thought_text):
        cleaned = thought_text.strip()
        if not cleaned:
            return
        if self.thought_bubble is None:
            self.thought_bubble = self.add_chat_bubble("", "assistant")
        current = getattr(self.thought_bubble, "text", "")
        self.thought_bubble.update_text((current + cleaned).strip())

    def on_tool_called(self, message):
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            return

        self.chat_history.append(message)
        outputs = []

        for call in tool_calls:
            function = call.get("function", {})
            tool_name = function.get("name", "")
            raw_arguments = function.get("arguments", "{}")

            try:
                arguments = (
                    json.loads(raw_arguments)
                    if isinstance(raw_arguments, str)
                    else raw_arguments
                )
            except json.JSONDecodeError:
                arguments = {}

            result = self.execute_tool(tool_name, arguments)
            outputs.append(f"[{tool_name}]\n{result}")
            self.chat_history.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "name": tool_name,
                    "content": result,
                }
            )

        if self.active_bubble:
            self.active_bubble.update_text("\n\n".join(outputs))

        # Show tool calling status
        self.status_indicator.set_status("tool_calling", f"Using: {tool_name}")

        self.current_ai_text = ""
        self.active_bubble = self.add_chat_bubble("", "assistant")
        self.start_chat_worker()

    def execute_tool(self, tool_name, arguments):
        tool = getattr(self.agent_tools, tool_name, None)
        if tool is None:
            return f"Unknown tool: {tool_name}"

        try:
            return str(tool(**arguments))
        except TypeError as e:
            return f"Tool argument error in {tool_name}: {e}"
        except Exception as e:
            return f"Tool execution error in {tool_name}: {e}"

    def add_chat_bubble(self, text, role="assistant"):
        bubble = ChatBubble(text, role)
        index = max(self.chat_layout.count() - 1, 0)
        self.chat_layout.insertWidget(index, bubble)
        return bubble

    def refresh_models(self):
        while self.models_list_layout.count():
            item = self.models_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for model in self.model_manager.get_compatible_models():
            card = ModelCard(
                model, self.load_model, self.delete_model, self.download_model
            )
            self.models_list_layout.addWidget(card)

        self.models_list_layout.addStretch()
        self._sync_local_models()
        self.update_model_selector()

    def update_model_selector(self):
        self.model_selector.clear()
        print(
            f"[DEBUG] Available models: {[(m.name, m.provider) for m in self.orchestrator.models]}"
        )
        local_index = 0
        for i, model in enumerate(self.orchestrator.models):
            label = f"{model.name} ({model.provider})"
            self.model_selector.addItem(label, model.provider + ":" + model.name)
            if model.provider == "local":
                local_index = i

        # Default to local model
        self.model_selector.setCurrentIndex(local_index)
        self.current_model = self.orchestrator.models[local_index]
        print(f"[DEBUG] Default model set: {self.current_model.name}")

    def on_model_selected(self, index):
        if index >= 0:
            model_data = self.model_selector.currentData()
            if model_data:
                provider, name = model_data.split(":", 1)
                for model in self.orchestrator.models:
                    if model.name == name and model.provider == provider:
                        self.current_model = model
                        print(f"[DEBUG] Model selected: {name} ({provider})")
                        break
        else:
            # Default to local model
            for model in self.orchestrator.models:
                if model.provider == "local":
                    self.current_model = model
                    print(f"[DEBUG] Default model: {model.name}")
                    break

    def refresh_git_log(self):
        pass

    def _sync_local_models(self):
        self.orchestrator.models = [
            m for m in self.orchestrator.models if m.provider != "local"
        ]

        for model in self.model_manager.get_downloaded_models():
            self.orchestrator.add_model(
                Model(
                    name=model["name"],
                    provider="local",
                    score=0.85,
                    latency=0.2,
                    context_size=8192,
                    is_free=True,
                    requires_key=False,
                    description=model.get("description", ""),
                    supports_tools=True,
                )
            )

        print(
            f"[DEBUG] Local models synced. Total models: {len(self.orchestrator.models)}"
        )

    def load_model(self, model):
        model_name = model.get("name")
        model_path = self.model_manager.get_model_path(model_name)
        if not model_path:
            QMessageBox.warning(
                self, "Model Not Found", f"Model {model_name} was not found on disk."
            )
            return

        self.statusBar().showMessage(f"Loading model: {model_name}...")

        def worker():
            try:
                self.inference.load_model(str(model_path))
                self.settings.settings.last_model = model_name
                self.settings.save()
                self.model_load_finished.emit(True, model_name, "")
            except Exception as e:
                print(f"[MainWindow] Failed to load model {model_name}: {e}")
                self.model_load_finished.emit(False, model_name, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def on_model_load_finished(self, success, model_name, error_text):
        if success:
            self.statusBar().showMessage(f"Loaded model: {model_name}", 5000)
            QMessageBox.information(
                self, "Model Ready", f"Model '{model_name}' loaded successfully."
            )
        else:
            self.statusBar().showMessage(f"Failed to load model: {model_name}", 5000)
            QMessageBox.critical(
                self,
                "Model Load Error",
                f"Could not load '{model_name}'.\n\n{error_text}",
            )

    def download_model(self, model):
        DownloadDialog(model, self.model_manager).exec()
        self.refresh_models()

    def delete_model(self, model):
        self.model_manager.delete_model(model.get("name"))
        self.refresh_models()

    def open_file(self, path):
        print(f"Opening: {path}")
        if os.path.isfile(path):
            self.editor_tabs.open_file(path)

    def on_new_file_requested(self, directory):
        if not directory:
            directory = "."
        name, ok = QInputDialog.getText(self, "Новий файл", "Ім'я файлу:")
        if ok and name:
            try:
                path = os.path.join(directory, name)
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")
                self.file_tree.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося створити файл: {e}")

    def on_new_folder_requested(self, directory):
        if not directory:
            directory = "."
        name, ok = QInputDialog.getText(self, "Нова папка", "Ім'я папки:")
        if ok and name:
            try:
                path = os.path.join(directory, name)
                os.makedirs(path, exist_ok=True)
                self.file_tree.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося створити папку: {e}")

    def on_delete_requested(self, path):
        reply = QMessageBox.question(
            self,
            "Підтвердження",
            f"Видалити {os.path.basename(path)}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.file_tree.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося видалити: {e}")

    def on_rename_requested(self, path):
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(
            self, "Перейменувати", "Нове ім'я:", text=old_name
        )
        if ok and new_name and new_name != old_name:
            try:
                new_path = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, new_path)
                self.file_tree.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося перейменувати: {e}")

    def on_file_tree_refresh(self):
        self.file_tree.refresh_tree()
