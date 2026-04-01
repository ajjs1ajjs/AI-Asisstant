import os
import re

def patch_main():
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. IMPORTS
    import_addition = """from PySide6.QtCore import Qt, QTimer, QMimeData, QThread, Signal
from settings_dialog import SettingsDialog
from settings import get_settings
from orchestrator import ModelOrchestrator, Model, GroqProvider, OpenRouterProvider, DeepSeekProvider, QwenProvider
from agent_tools import AgentTools, TOOL_DEFINITIONS
import asyncio"""
    content = content.replace("from PySide6.QtCore import Qt, QTimer, QMimeData", import_addition)

    # 2. Add AsyncChatWorker before MainWindow
    worker_code = """
class AsyncChatWorker(QThread):
    chunk_received = Signal(str)
    tool_called = Signal(dict)
    finished_success = Signal(str)
    error = Signal(str)

    def __init__(self, orchestrator, messages, task="chat", tools=None):
        super().__init__()
        self.orchestrator = orchestrator
        self.messages = messages
        self.task = task
        self.tools = tools
        self.full_response = ""
        self.is_tool_call = False

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch():
            try:
                if self.tools:
                    res = await self.orchestrator.request(self.messages, task=self.task, tools=self.tools)
                    if isinstance(res, dict) and "tool_calls" in res:
                        self.is_tool_call = True
                        self.full_response = res
                        self.tool_called.emit(res)
                    else:
                        self.full_response = res
                        self.finished_success.emit(str(self.full_response))
                else:
                    async for chunk in self.orchestrator.stream_request(self.messages, task=self.task):
                        if chunk.startswith("data:"):
                            data_str = chunk[5:].strip()
                            if data_str == "[DONE]":
                                continue
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    content = delta["content"]
                                    self.full_response += content
                                    self.chunk_received.emit(content)
                            except json.JSONDecodeError:
                                pass
                    self.finished_success.emit(self.full_response)
            except Exception as e:
                self.error.emit(str(e))
                
        loop.run_until_complete(fetch())

"""
    if "class AsyncChatWorker(" not in content:
        content = content.replace("class MainWindow(QMainWindow):", worker_code + "class MainWindow(QMainWindow):")

    # 3. Add Settings to Menu in create_menu_bar
    menu_code = """        edit_menu.addAction("📝 Очистити контекст", self.clear_context)
        edit_menu.addSeparator()
        edit_menu.addAction("⚙️ Налаштування", self.open_settings)"""
    content = content.replace('edit_menu.addAction("📝 Очистити контекст", self.clear_context)', menu_code)

    # 4. Add open_settings method
    open_settings_code = """    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.setup_orchestrator()

    def clear_chat(self):"""
    content = content.replace("    def clear_chat(self):", open_settings_code)

    # 5. Initialization in MainWindow __init__
    init_replace = """        self.model_manager = LocalModelManager()
        self.inference = get_inference()
        self.context_engine = ContextEngine()
        self.editors = find_editors()
        self.settings = get_settings()
        self.agent_tools = AgentTools(os.getcwd())
        self.setup_orchestrator()"""
    content = content.replace("""        self.model_manager = LocalModelManager()
        self.inference = get_inference()
        self.context_engine = ContextEngine()
        self.editors = find_editors()""", init_replace)

    setup_orch_meth = """    def setup_orchestrator(self):
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

    def create_menu_bar(self):"""
    if "def setup_orchestrator" not in content:
        content = content.replace("    def create_menu_bar(self):", setup_orch_meth)

    # 6. Replace response logic in send()
    send_response_logic = """        self.typing.start()

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

        QTimer.singleShot(200, lambda: self.check_generation(response_data))"""
    
    new_send_logic = """        self.typing.start()
        self._run_orchestrator_chat()"""
    content = content.replace(send_response_logic, new_send_logic)

    # 7. Add _run_orchestrator_chat methods
    if "def _run_orchestrator_chat" not in content:
        chat_methods = """    def _run_orchestrator_chat(self, tools_mode=True):
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
        
        self.chat.append("<hr><span style='color: #4ec9b0;'>🧠</span> ")
        self.chat.moveCursor(self.chat.textCursor().End)
        self.streaming_text = ""
        
        self.worker.chunk_received.connect(self._on_chunk)
        self.worker.tool_called.connect(self._on_tool_call)
        self.worker.finished_success.connect(self._on_chat_success)
        self.worker.error.connect(self._on_chat_error)
        self.worker.start()

    def _on_chunk(self, chunk):
        self.typing.stop()
        self.chat.moveCursor(self.chat.textCursor().End)
        self.chat.insertPlainText(chunk)
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())
        self.streaming_text += chunk

    def _on_tool_call(self, message):
        self.chat_history.append(message)
        for call in message.get("tool_calls", []):
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            
            self.chat.append(f"<div style='color: #d6701e; margin-left: 10px;'>🛠️ Виконання: {name}({args})</div>")
            
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
                    res = f"Stdout:\\n{out['stdout']}\\nStderr:\\n{out['stderr']}"
            except Exception as e:
                res = f"Error: {e}"
                
            self.chat.append(f"<div style='color: #888; margin-left: 20px;'>=> {str(res)[:100]}...</div>")
            
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
        self.chat.append(f"<div style='color: #f44747;'>✗ Помилка Orchestrator: {err}</div>")
        self._finish_generation()

    def _finish_generation(self):
        self.is_generating = False
        self.typing.stop()
        self.work_status.setText("Готовий")
        self.status_icon.setStyleSheet("color: #4ec9b0; font-size: 10px;")
        self.work_status.parent().setStyleSheet(\"\"\"
            QFrame {
                background-color: #1e3a2a;
                border-radius: 12px;
                padding: 4px 12px;
            }
        \"\"\")

    def check_generation(self, response_data):"""
        content = content.replace("    def check_generation(self, response_data):", chat_methods)
        
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("Patched main.py successfully")

if __name__ == "__main__":
    patch_main()
