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
        self.in_thought_block = False # Heuristic state
        self.accumulator = "" # For detecting local tool calls

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
                        async for chunk in self.orchestrator.stream_request(self.messages, task=self.task, tools=self.tools):
                            if not self.is_running: break
                            
                            # Handle Local (Raw Text) vs Cloud (data: prefix)
                            if not chunk.startswith("data:"):
                                # Local Chunk
                                self.typing_logic(chunk)
                                continue
                                
                            # Cloud Chunk parsing (Existing)
                            data_str = chunk[5:].strip()
                            if data_str == "[DONE]": continue
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                
                                # Handle "Reasoning/Thought" fields from API
                                thought = delta.get("reasoning_content") or delta.get("thought")
                                if thought:
                                    self.thought_received.emit(thought)
                                    continue

                                if "content" in delta and delta["content"]:
                                    self.typing_logic(delta["content"])
                            except: pass

                        if self.is_running:
                            # Final Check for Tool Calls in Accumulator
                            self.check_local_tool_calls()
                            self.finished_success.emit(str(self.full_response))
            except Exception as e:
                self.error.emit(str(e))
                
        loop.run_until_complete(fetch())

    def typing_logic(self, content):
        """Unified logic for handling thoughts vs content."""
        # Detect ChatML Tags (<|im_start|>thought)
        if "<|im_start|>thought" in content or "<thought>" in content:
            self.in_thought_block = True
            content = content.replace("<|im_start|>thought", "").replace("<thought>", "")
        
        if "<|im_end|>" in content or "</thought>" in content:
            parts = content.split("<|im_end|>" if "<|im_end|>" in content else "</thought>")
            thought_part = parts[0]
            main_part = parts[1] if len(parts) > 1 else ""
            
            if thought_part: self.thought_received.emit(thought_part)
            self.in_thought_block = False
            if main_part:
                self.full_response += main_part
                self.chunk_received.emit(main_part)
                self.accumulator += main_part
            self.check_local_tool_calls()
            return

        if not content: return

        if self.in_thought_block:
            self.thought_received.emit(content)
        else:
            self.full_response += content
            self.chunk_received.emit(content)
            self.accumulator += content
            self.check_local_tool_calls()

    def check_local_tool_calls(self):
        """Heuristic JSON detector for local model instructions."""
        if "```json" in self.accumulator and "tool_call" in self.accumulator:
            # Try to extract the JSON block
            try:
                import re
                blocks = re.findall(r"```json\n(.*?)\n```", self.accumulator, re.DOTALL)
                for block in blocks:
                    data = json.loads(block)
                    if "tool_call" in data:
                        tc = data["tool_call"]
                        msg = {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": f"local_{datetime.now().timestamp()}",
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["arguments"])
                                }
                            }]
                        }
                        self.is_tool_call = True
                        self.tool_called.emit(msg)
                        # Clear to prevent double trigger
                        self.accumulator = self.accumulator.replace(f"```json\n{block}\n```", "[ACTION_TAKEN]")
            except: pass
