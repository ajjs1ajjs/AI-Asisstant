import asyncio
import os
import subprocess
from typing import Any, Dict, Optional


class AgentTools:
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or os.getcwd()

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

    def search_code(self, query: str, extensions: list = None) -> list:
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

    async def read_file_async(self, path: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_file, path)

    async def write_file_async(self, path: str, content: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.write_file, path, content)

    async def create_directory_async(self, path: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_directory, path)

    async def search_code_async(self, query: str, extensions: list = None) -> list:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search_code, query, extensions)

    async def run_command_async(self, cmd: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.root_dir,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
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
]
