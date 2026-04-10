"""
Autonomous Background Engine (v6.0)
Handles long-running AI tasks with automatic Git synchronization.
"""

import asyncio
import os
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Callable

@dataclass
class BackgroundTask:
    id: str
    name: str
    description: str
    status: str = "pending" # pending, running, success, error
    progress: int = 0
    result: str = ""

class BackgroundEngine:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.tasks: List[BackgroundTask] = []
        self._loop = asyncio.get_event_loop()

    async def run_task(self, name: str, description: str, coro_func: Callable):
        """Queue and run a background task"""
        task_id = f"task_{len(self.tasks) + 1}"
        task = BackgroundTask(task_id, name, description, status="running")
        self.tasks.append(task)
        
        try:
            # 1. Execute the actual work
            print(f"🚀 Starting background task: {name}")
            result = await coro_func(task)
            task.status = "success"
            task.result = result
            task.progress = 100
            
            # 2. Automated Git sync (Post-task)
            self._auto_git_sync(name)
            
        except Exception as e:
            task.status = "error"
            task.result = str(e)
            print(f"❌ Background task error: {e}")
        
    def _auto_git_sync(self, task_name: str):
        """Automatically stage, commit and push changes after task completion"""
        if not self.project_path: return
        
        try:
            print(f"🔄 Auto-syncing changes after {task_name}...")
            subprocess.run(["git", "add", "."], cwd=self.project_path)
            subprocess.run(["git", "commit", "-m", f"🤖 AI Autonomous: {task_name} completed"], cwd=self.project_path)
            subprocess.run(["git", "push"], cwd=self.project_path)
        except Exception as e:
            print(f"⚠️ Auto-git failed: {e}")

    def get_task_status(self) -> List[Dict]:
        return [vars(t) for t in self.tasks]
