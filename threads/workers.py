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
class AsyncChatWorker(QThread):
    chunk_received = Signal(str)
    tool_called = Signal(dict)
    finished_success = Signal(str)
    error = Signal(str)
    status_changed = Signal(str) # For "🧠 Thinking", "🛠️ Tool: xyz", etc.
    thought_received = Signal(str) # For streaming reasoning/thoughts

    def __init__(self, orchestrator, messages, task="chat", tools=None):
        super().__init__()
        self.orchestrator = orchestrator
        self.messages = messages
        self.task = task
        self.tools = tools
        self.full_response = ""
        self.is_tool_call = False
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch():
            try:
                if self.is_running:
                    if self.tools:
                        self.status_changed.emit("🛠️ Виконання інструментів...")
                        res = await self.orchestrator.request(self.messages, task=self.task, tools=self.tools)
                        if not self.is_running: return
                        if isinstance(res, dict) and "tool_calls" in res:
                            self.is_tool_call = True
                            self.full_response = res
                            self.tool_called.emit(res)
                        else:
                            self.full_response = res
                            self.finished_success.emit(str(self.full_response))
                    else:
                        self.status_changed.emit("🧠 Генерація...")
                        async for chunk in self.orchestrator.stream_request(self.messages, task=self.task):
                            if not self.is_running: break
                            if chunk.startswith("data:"):
                                data_str = chunk[5:].strip()
                                if data_str == "[DONE]":
                                    continue
                                try:
                                    delta = data.get("choices", [{}])[0].get("delta", {})
                                    
                                    # Handle "Reasoning/Thought" fields
                                    thought = delta.get("reasoning_content") or delta.get("thought")
                                    if thought:
                                        self.thought_received.emit(thought)
                                        continue

                                    if "content" in delta and delta["content"]:
                                        content = delta["content"]
                                        self.full_response += content
                                        self.chunk_received.emit(content)
                                except json.JSONDecodeError:
                                    pass
                        if self.is_running:
                            self.finished_success.emit(str(self.full_response))
            except Exception as e:
                self.error.emit(str(e))
                
        loop.run_until_complete(fetch())


