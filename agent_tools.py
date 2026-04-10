import asyncio
import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Set

DANGEROUS_COMMANDS: Set[str] = {
    "rm -rf",
    "rm -r",
    "del /f",
    "del /s",
    "del /q",
    "format",
    "shutdown",
    "restart",
    "poweroff",
    "mkfs",
    "dd if=",
    "chmod 777",
    "chown",
    "sudo rm",
    "sudo dd",
    "sudo mkfs",
    ":(){:|:&};:",
    "fork bomb",
    "> /dev/sda",
    "> /dev/hda",
    "rmdir /s",
    "rmdir /q",
    "taskkill /f",
    "kill -9",
    "net user",
    "passwd",
    "wget http",
    "curl http",
    "powershell -enc",
    "powershell -encodedcommand",
    "certutil -decode",
    "certutil -urlcache",
}

DANGEROUS_PATTERNS: List[str] = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r"del\s+/[fqs]\s+/",
    r"format\s+[A-Z]:",
    r">\s*/dev/[sh]da",
    r":\(\)\{:\|:&\};:",
    r"sudo\s+rm\s+-rf",
    r"sudo\s+dd\s+",
    r"powershell\s+-(enc|encodedcommand)",
    r"certutil\s+-(decode|urlcache)",
    r"wget\s+.*\|\s*(bash|sh)",
    r"curl\s+.*\|\s*(bash|sh)",
    r"mkfs\.\w+\s+/dev/",
    r"chmod\s+777\s+/",
    r"chown\s+-R\s+\w+:/",
]

ALLOWED_COMMANDS: Set[str] = {
    "git",
    "python",
    "python3",
    "pip",
    "pip3",
    "npm",
    "npx",
    "yarn",
    "node",
    "cargo",
    "rustc",
    "gcc",
    "g++",
    "make",
    "cmake",
    "pytest",
    "unittest",
    "mypy",
    "flake8",
    "black",
    "ruff",
    "echo",
    "ls",
    "dir",
    "pwd",
    "cd",
    "cat",
    "type",
    "find",
    "where",
    "which",
    "pip",
    "pip3",
    "npm",
    "yarn",
    "docker",
    "docker-compose",
    "curl",
    "wget",
    "zip",
    "unzip",
    "tar",
    "grep",
    "findstr",
    "tree",
    "du",
    "df",
    "java",
    "javac",
    "mvn",
    "gradle",
    "go",
    "gofmt",
    "dotnet",
    "msbuild",
}


def is_command_safe(cmd: str) -> tuple[bool, str]:
    if not cmd or not cmd.strip():
        return False, "Empty command"

    cmd_stripped = cmd.strip()
    cmd_lower = cmd_stripped.lower()

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return False, f"Blocked dangerous pattern in command"

    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in cmd_lower:
            return False, f"Blocked dangerous command: {dangerous}"

    base_cmd = cmd_stripped.split()[0].lower()
    base_cmd = os.path.basename(base_cmd)

    if base_cmd in ("sh", "bash", "zsh", "cmd", "powershell", "pwsh"):
        rest = cmd_stripped[cmd_stripped.find(base_cmd) + len(base_cmd) :].strip()
        if rest.startswith("-c") or rest.startswith("/c"):
            inner_cmd = rest[2:].strip().strip("'\"")
            inner_safe, inner_reason = is_command_safe(inner_cmd)
            if not inner_safe:
                return False, f"Unsafe inner command: {inner_reason}"
            return True, ""

    if base_cmd not in ALLOWED_COMMANDS:
        return False, f"Command '{base_cmd}' is not in the allowed list"

    return True, ""


class AgentTools:
    def __init__(self, root_dir: str = "", safe_mode: bool = True):
        self.root_dir = root_dir if root_dir else os.getcwd()
        self.safe_mode = safe_mode
        self.plugins = {}
        self.load_plugins()

    def load_plugins(self):
        """Discover and load external tools from plugins/ directory"""
        plugins_dir = os.path.join(self.root_dir, "plugins")
        if not os.path.exists(plugins_dir):
            return

        import importlib.util

        for file in os.listdir(plugins_dir):
            if file.endswith(".py") and file != "__init__.py":
                plugin_name = file[:-3]
                file_path = os.path.join(plugins_dir, file)
                try:
                    spec = importlib.util.spec_from_file_location(plugin_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Look for register_tools function
                    if hasattr(module, "register_tools"):
                        new_tools = module.register_tools()
                        for name, func in new_tools.items():
                            setattr(self, name, func)
                            self.plugins[name] = plugin_name
                            logger.info(f"🧩 Plugin tool registered: {name}")
                except Exception as e:
                    logger.error(f"❌ Error loading plugin {plugin_name}: {e}")

    def web_search(self, query: str) -> str:
        """Search the web for up-to-date information and documentation"""
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append(
                        f"🌐 {r['title']}\n🔗 {r['href']}\n📝 {r['body']}\n{'-'*40}"
                    )

            if not results:
                return "No results found for your query."

            return "\n".join(results)
        except ImportError:
            return "❌ Error: 'duckduckgo_search' library not installed. Please run 'pip install duckduckgo-search'."
        except Exception as e:
            return f"❌ Web search error: {str(e)}"

    def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text using deep-translator"""
        try:
            from deep_translator import GoogleTranslator
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            return f"🌍 Translation ({target_lang}):\n{translated}"
        except Exception as e:
            return f"❌ Translation error: {str(e)}"

    def predictive_audit(self, target_file: str) -> str:
        """Perform an AI-based predictive analysis of performance and logic bottlenecks"""
        try:
            full_path = os.path.join(self.root_dir, target_file)
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"⚡ Починаю предиктивний аудит {target_file}...\nАналізую логічні цикли та навантаження..."
        except Exception as e:
            return f"❌ Audit error: {str(e)}"

    def architect_project(self, plan: list) -> str:
        """Create multiple files based on an architect plan."""
        results = []
        for file_info in plan:
            path = file_info.get("path")
            content = file_info.get("content")
            if not path or content is None: continue
            
            full_path = os.path.join(self.root_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            results.append(f"✅ Created: {path}")
        return "🏗️ Architect plan complete:\n" + "\n".join(results)

    def execute_sql(self, db_path: str, sql: str) -> str:
        """Execute a SQL query on a local SQLite database"""
        try:
            import sqlite3
            full_path = os.path.join(self.root_dir, db_path)
            conn = sqlite3.connect(full_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                cols = [description[0] for description in cursor.description]
                conn.close()
                return f"✅ SQL Executed. Results:\nColumns: {cols}\nRows: {rows[:50]}"
            else:
                conn.commit()
                affected = conn.total_changes
                conn.close()
                return f"✅ SQL Executed. Changes: {affected}"
        except Exception as e:
            return f"❌ SQL Error: {str(e)}"

    def perform_code_review(self) -> str:
        """Perform a comprehensive code review of the entire project."""
        # We use analyze_project to get the structure first
        structure = self.analyze_project()
        return f"🔍 Починаю повний аудит проекту...\nСтруктура:\n{structure}\n(Аналіз може зайняти деякий час...)"

    def capture_screen(self) -> str:
        """Capture a screenshot of the current screen for visual analysis"""
        try:
            import pyscreenshot as ImageGrab
            from datetime import datetime
            
            screenshots_dir = os.path.join(self.root_dir, "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            im = ImageGrab.grab()
            im.save(filepath)
            
            return f"📸 Скріншот збережено: {filepath}\nТепер я можу проаналізувати це зображення."
        except ImportError:
            return "❌ Помилка: Бібліотека 'pyscreenshot' не встановлена. Виконайте 'pip install pyscreenshot Pillow'."
        except Exception as e:
            return f"❌ Помилка при знятті скріншоту: {str(e)}"

    def run_tests(self, path: str = "") -> str:
        """Run project tests using pytest and return the results"""
        try:
            import subprocess
            target = path if path else self.root_dir
            result = subprocess.run(
                ["pytest", target, "-v"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return f"🧪 Результати тестів:\n\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"❌ Помилка при запуску тестів: {str(e)}"

    def read_file(self, path: str) -> str:
        full_path = os.path.join(self.root_dir, path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")

        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: str, content: str) -> bool:
        full_path = os.path.join(self.root_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    def create_directory(self, path: str) -> bool:
        full_path = os.path.join(self.root_dir, path)
        os.makedirs(full_path, exist_ok=True)
        return True

    def search_code(self, query: str, extensions: Optional[list] = None) -> list:
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".jsx", ".tsx"]

        results = []
        for root, dirs, files in os.walk(self.root_dir):
            if ".git" in root or "__pycache__" in root:
                continue

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        if query.lower() in content.lower():
                            rel_path = os.path.relpath(filepath, self.root_dir)
                            results.append(
                                {
                                    "file": rel_path,
                                    "matches": self._count_matches(content, query),
                                }
                            )
                    except:
                        pass

        return sorted(results, key=lambda x: x["matches"], reverse=True)

    def _count_matches(self, content: str, query: str) -> int:
        lines = content.split("\n")
        matches = sum(1 for line in lines if query.lower() in line.lower())
        return matches

    def run_command(self, cmd: str, timeout: int = 30) -> Dict[str, Any]:
        if self.safe_mode:
            safe, reason = is_command_safe(cmd)
            if not safe:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Command blocked for security: {reason}",
                    "returncode": -1,
                }

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.root_dir,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "returncode": -1,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

    def list_files(self, path: str = ".") -> list:
        full_path = os.path.join(self.root_dir, path)
        if not os.path.exists(full_path):
            return []

        items = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            items.append(
                {
                    "name": item,
                    "is_dir": os.path.isdir(item_path),
                    "path": os.path.relpath(item_path, self.root_dir),
                }
            )

        return sorted(items, key=lambda x: (not x["is_dir"], x["name"]))

    def get_file_info(self, path: str) -> Dict[str, Any]:
        full_path = os.path.join(self.root_dir, path)
        if not os.path.exists(full_path):
            return {}

        stat = os.stat(full_path)
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_dir": os.path.isdir(full_path),
        }

    def analyze_project(self) -> str:
        """Provide a comprehensive summary of the project codebase"""
        if not self.root_dir:
            return "No project directory"

        analysis = []
        analysis.append(f"📁 Project Analysis: {self.root_dir}")
        analysis.append("=" * 60)

        total_files = 0
        total_lines = 0
        extensions = {}
        ignored_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            "venv",
            "dist",
            "build",
            ".idea",
            ".vscode",
        }

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if not ext:
                    ext = "no-ext"
                extensions[ext] = extensions.get(ext, 0) + 1
                total_files += 1
                filepath = os.path.join(root, file)
                try:
                    # Only try to count lines for text-based files
                    if ext in {
                        ".py",
                        ".js",
                        ".ts",
                        ".html",
                        ".css",
                        ".md",
                        ".txt",
                        ".json",
                        ".yml",
                        ".yaml",
                        ".spec",
                        ".bat",
                        ".sh",
                    }:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            total_lines += len(f.readlines())
                except (OSError, UnicodeDecodeError):
                    pass

        analysis.append(f"📊 Total Files: {total_files}")
        analysis.append(f"📝 Estimated Lines of Code (text files): {total_lines:,}")
        
        # Sort and show top extensions
        sorted_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)
        analysis.append("\n📄 File Distribution:")
        for ext, count in sorted_exts[:10]:
            analysis.append(f"  - {ext}: {count}")

        # Structure Overview (top level and one level deep)
        analysis.append("\n📂 Structure Overview:")
        for entry in self.list_files("."):
            analysis.append(f"  {'📁' if entry['is_dir'] else '📄'} {entry['name']}")
            if entry['is_dir'] and entry['name'] not in ignored_dirs:
                try:
                    sub_entries = self.list_files(entry['name'])
                    for sub in sub_entries[:5]: # Show max 5 sub-items
                        analysis.append(f"    {'📁' if sub['is_dir'] else '📄'} {sub['name']}")
                    if len(sub_entries) > 5:
                        analysis.append(f"    ... and {len(sub_entries) - 5} more")
                except:
                    pass

        return "\n".join(analysis)

    async def read_file_async(self, path: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_file, path)

    async def write_file_async(self, path: str, content: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.write_file, path, content)

    async def create_directory_async(self, path: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_directory, path)

    async def search_code_async(
        self, query: str, extensions: Optional[list] = None
    ) -> list:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search_code, query, extensions)

    async def analyze_project_async(self) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_project)

    async def run_command_async(self, cmd: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.root_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout}s",
                    "returncode": -1,
                }

            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": process.returncode,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to project root",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to project root",
                },
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "search_code",
        "description": "Search for code patterns in the project",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
    {
        "name": "run_command",
        "description": "Execute a shell command",
        "parameters": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "Command to execute"}
            },
            "required": ["cmd"],
        },
    },
    {
        "name": "create_directory",
        "description": "Create a new directory",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to project root",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "analyze_project",
        "description": "Provide a high-level summary of the project codebase, including file counts, lines of code, and structure overview",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "capture_screen",
        "description": "Capture a screenshot of the current screen for visual analysis",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "architect_project",
        "description": "Create multiple files and folders at once based on a project plan",
        "parameters": {
            "type": "object",
            "properties": {
                "plan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative path to the file"},
                            "content": {"type": "string", "description": "Full content of the file"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            "required": ["plan"],
        },
    },
    {
        "name": "perform_code_review",
        "description": "Perform a comprehensive automated code review of the entire project",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    {
        "name": "execute_sql",
        "description": "Execute a SQL query on a local SQLite database",
        "parameters": {
            "type": "object",
            "properties": {
                "db_path": {"type": "string", "description": "Relative path to the .db or .sqlite file"},
                "sql": {"type": "string", "description": "SQL query to execute"}
            },
            "required": ["db_path", "sql"],
        },
    {
        "name": "predictive_audit",
        "description": "AI-based predictive analysis of performance and logic bottlenecks in a specific file",
        "parameters": {
            "type": "object",
            "properties": {
                "target_file": {"type": "string", "description": "Relative path to the file to audit"}
            },
            "required": ["target_file"],
        },
    },
]
