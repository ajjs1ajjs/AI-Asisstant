"""
Git Integration Module
Інтеграція Git команд в AI IDE
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class GitStatus:
    """Статус Git репозиторію"""
    branch: str
    ahead: int
    behind: int
    staged: List[str]
    unstaged: List[str]
    untracked: List[str]
    is_clean: bool


@dataclass
class GitCommit:
    """Інформація про коміт"""
    hash: str
    short_hash: str
    author: str
    email: str
    date: str
    message: str


class GitIntegration:
    """Git інтеграція для AI IDE"""

    def __init__(self, repo_path: str = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self._git_available = self._check_git()

    def _check_git(self) -> bool:
        """Перевірити чи встановлений Git"""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _run_git(self, args: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Виконати Git команду"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return (
                result.returncode == 0,
                result.stdout.strip(),
                result.stderr.strip()
            )
        except subprocess.TimeoutExpired:
            return False, "", "Command timeout"
        except Exception as e:
            return False, "", str(e)

    def is_repo(self) -> bool:
        """Чи є директорія Git репозиторієм"""
        if not self._git_available:
            return False
        
        success, _, _ = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return success

    def init_repo(self) -> Tuple[bool, str]:
        """Ініціалізувати Git репозиторій"""
        success, stdout, stderr = self._run_git(["init"])
        if success:
            # Створити .gitignore
            gitignore = self.repo_path / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text(
                    "# Python\n"
                    "__pycache__/\n"
                    "*.py[cod]\n"
                    "*.so\n"
                    ".venv/\n"
                    "venv/\n"
                    ".env\n"
                    "\n"
                    "# IDE\n"
                    ".idea/\n"
                    ".vscode/\n"
                    "*.swp\n"
                    "*.swo\n"
                    "\n"
                    "# Build\n"
                    "dist/\n"
                    "build/\n"
                    "*.egg-info/\n"
                )
        return success, stderr if not success else "Repository initialized"

    def get_status(self) -> Optional[GitStatus]:
        """Отримати статус репозиторію"""
        if not self.is_repo():
            return None

        # Отримати поточну гілку
        success, branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if not success:
            branch = "unknown"

        # Отримати статус remote
        ahead, behind = 0, 0
        success, status, _ = self._run_git(["rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"])
        if success and status:
            parts = status.split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])

        # Отримати зміни
        success, staged, _ = self._run_git(["diff", "--cached", "--name-only"])
        staged_files = staged.split("\n") if staged else []

        success, unstaged, _ = self._run_git(["diff", "--name-only"])
        unstaged_files = unstaged.split("\n") if unstaged else []

        success, untracked, _ = self._run_git(["ls-files", "--others", "--exclude-standard"])
        untracked_files = untracked.split("\n") if untracked else []

        is_clean = not staged_files and not unstaged_files and not untracked_files

        return GitStatus(
            branch=branch,
            ahead=ahead,
            behind=behind,
            staged=[f for f in staged_files if f],
            unstaged=[f for f in unstaged_files if f],
            untracked=[f for f in untracked_files if f],
            is_clean=is_clean
        )

    def add_file(self, path: str) -> Tuple[bool, str]:
        """Додати файл до staging"""
        success, _, stderr = self._run_git(["add", path])
        return success, stderr if not success else "File added"

    def add_all(self) -> Tuple[bool, str]:
        """Додати всі зміни"""
        success, _, stderr = self._run_git(["add", "-A"])
        return success, stderr if not success else "All changes added"

    def commit(self, message: str) -> Tuple[bool, str]:
        """Створити коміт"""
        success, _, stderr = self._run_git(["commit", "-m", message])
        return success, stderr if not success else "Changes committed"

    def push(self, remote: str = "origin", branch: str = None) -> Tuple[bool, str]:
        """Push комітів"""
        if branch is None:
            success, branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            if not success:
                return False, "Cannot determine branch"

        # Встановити upstream якщо потрібно
        self._run_git(["push", "-u", remote, branch], timeout=60)
        success, output, error = self._run_git(["push", remote, branch], timeout=60)
        
        return success, output if success else error

    def pull(self, remote: str = "origin", branch: str = None) -> Tuple[bool, str]:
        """Pull змін"""
        if branch is None:
            success, branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            if not success:
                return False, "Cannot determine branch"

        success, output, error = self._run_git(["pull", remote, branch], timeout=120)
        return success, output if success else error

    def create_branch(self, name: str, start_point: str = None) -> Tuple[bool, str]:
        """Створити нову гілку"""
        args = ["checkout", "-b", name]
        if start_point:
            args.append(start_point)
        
        success, _, stderr = self._run_git(args)
        return success, stderr if not success else f"Branch '{name}' created"

    def checkout_branch(self, name: str) -> Tuple[bool, str]:
        """Перемкнутися на гілку"""
        success, _, stderr = self._run_git(["checkout", name])
        return success, stderr if not success else f"Switched to '{name}'"

    def get_branches(self) -> List[str]:
        """Отримати список гілок"""
        success, branches, _ = self._run_git(["branch", "--format", "%(refname:short)"])
        if success:
            return [b.strip() for b in branches.split("\n") if b.strip()]
        return []

    def get_log(self, count: int = 10) -> List[GitCommit]:
        """Отримати історію комітів"""
        success, output, _ = self._run_git([
            "log",
            f"-{count}",
            "--format=%H|%h|%an|%ae|%ai|%s"
        ])
        
        if not success:
            return []

        commits = []
        for line in output.split("\n"):
            if line and "|" in line:
                parts = line.split("|")
                if len(parts) >= 6:
                    commits.append(GitCommit(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        email=parts[3],
                        date=parts[4],
                        message=parts[5]
                    ))
        return commits

    def get_diff(self, staged: bool = False) -> str:
        """Отримати diff змін"""
        if staged:
            success, diff, _ = self._run_git(["diff", "--cached"])
        else:
            success, diff, _ = self._run_git(["diff"])
        return diff if success else ""

    def get_remote_url(self) -> Optional[str]:
        """Отримати URL remote репозиторію"""
        success, url, _ = self._run_git(["config", "--get", "remote.origin.url"])
        return url if success else None

    def set_remote_url(self, url: str) -> Tuple[bool, str]:
        """Встановити URL remote"""
        # Спочатку видалити існуючий origin якщо є
        self._run_git(["remote", "remove", "origin"])
        success, _, stderr = self._run_git(["remote", "add", "origin", url])
        return success, stderr if not success else "Remote URL set"

    def clone(self, url: str, target_dir: str = None) -> Tuple[bool, str]:
        """Клонувати репозиторій"""
        args = ["clone", url]
        if target_dir:
            args.append(target_dir)
        
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return False, "Clone timeout (5 min)"
        except Exception as e:
            return False, str(e)


# Глобальний екземпляр
_git = None


def get_git(repo_path: str = None) -> GitIntegration:
    """Отримати Git інтеграцію"""
    global _git
    if _git is None or (_git and repo_path and _git.repo_path != Path(repo_path)):
        _git = GitIntegration(repo_path)
    return _git
