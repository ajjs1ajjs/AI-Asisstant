"""
Settings Manager для AI IDE
Зберігає налаштування користувача
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ModelSettings:
    """Налаштування моделі"""
    n_ctx: int = 8192  # Збільшено до 8K (макс 131072)
    n_gpu_layers: int = 0
    n_threads: int = 0  # 0 = auto
    n_batch: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 4096  # Збільшено до 4K (макс 32768)
    use_mmap: bool = True
    use_mlock: bool = False


@dataclass
class UISettings:
    """Налаштування інтерфейсу"""
    theme: str = "dark"  # dark, light, blue, purple
    font_size: int = 13
    sidebar_width: int = 250
    chat_height: int = 400
    show_line_numbers: bool = True
    auto_scroll: bool = True
    minimap_enabled: bool = False


@dataclass
class ContextSettings:
    """Налаштування контексту"""
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 300
    chunk_overlap: int = 50
    max_context_files: int = 500
    search_results: int = 5
    max_context_tokens: int = 2000
    auto_index: bool = True
    extensions: List[str] = field(default_factory=lambda: [
        ".py", ".md", ".txt", ".js", ".ts", ".jsx", ".tsx",
        ".json", ".yaml", ".yml", ".cpp", ".c", ".h", ".java"
    ])


@dataclass
class ChatSettings:
    """Налаштування чату"""
    save_history: bool = True
    max_history: int = 100
    export_format: str = "md"  # md, txt, json
    system_prompt: str = "You are a helpful AI coding assistant."
    stream_response: bool = True


@dataclass
class GitSettings:
    """Налаштування Git"""
    auto_commit: bool = False
    commit_template: str = "{message}"
    default_remote: str = "origin"
    default_branch: str = "main"


@dataclass
class AppSettings:
    """Загальні налаштування додатку"""
    model: ModelSettings = field(default_factory=ModelSettings)
    ui: UISettings = field(default_factory=UISettings)
    context: ContextSettings = field(default_factory=ContextSettings)
    chat: ChatSettings = field(default_factory=ChatSettings)
    git: GitSettings = field(default_factory=GitSettings)
    last_project: str = ""
    last_model: str = ""
    api_keys: Dict[str, str] = field(default_factory=dict)


class SettingsManager:
    """Менеджер налаштувань"""

    CONFIG_DIR = Path.home() / ".ai-ide"
    CONFIG_FILE = CONFIG_DIR / "settings.json"
    HISTORY_FILE = CONFIG_DIR / "chat_history.json"

    def __init__(self):
        self.settings = AppSettings()
        self._load()

    def _load(self):
        """Завантажити налаштування"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Оновити налаштування з файлу
                if "model" in data:
                    self.settings.model = ModelSettings(**data["model"])
                if "ui" in data:
                    self.settings.ui = UISettings(**data["ui"])
                if "context" in data:
                    self.settings.context = ContextSettings(**data["context"])
                if "chat" in data:
                    self.settings.chat = ChatSettings(**data["chat"])
                if "git" in data:
                    self.settings.git = GitSettings(**data["git"])
                if "last_project" in data:
                    self.settings.last_project = data["last_project"]
                if "last_model" in data:
                    self.settings.last_model = data["last_model"]
                if "api_keys" in data:
                    self.settings.api_keys = data["api_keys"]

                print(f"✅ Налаштування завантажено: {self.CONFIG_FILE}")

            except Exception as e:
                print(f"⚠️ Помилка завантаження налаштувань: {e}")
                self._backup_config()

    def _backup_config(self):
        """Створити резервну копію зіпсованого конфігу"""
        if self.CONFIG_FILE.exists():
            backup = self.CONFIG_FILE.with_suffix(".json.bak")
            try:
                self.CONFIG_FILE.rename(backup)
                print(f"📦 Створено резервну копію: {backup}")
            except:
                pass

    def save(self):
        """Зберегти налаштування"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        data = {
            "model": asdict(self.settings.model),
            "ui": asdict(self.settings.ui),
            "context": asdict(self.settings.context),
            "chat": asdict(self.settings.chat),
            "git": asdict(self.settings.git),
            "last_project": self.settings.last_project,
            "last_model": self.settings.last_model,
            "api_keys": self.settings.api_keys,
        }

        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_model(self, **kwargs):
        """Оновити налаштування моделі"""
        for key, value in kwargs.items():
            if hasattr(self.settings.model, key):
                setattr(self.settings.model, key, value)
        self.save()

    def update_ui(self, **kwargs):
        """Оновити налаштування UI"""
        for key, value in kwargs.items():
            if hasattr(self.settings.ui, key):
                setattr(self.settings.ui, key, value)
        self.save()

    def update_context(self, **kwargs):
        """Оновити налаштування контексту"""
        for key, value in kwargs.items():
            if hasattr(self.settings.context, key):
                setattr(self.settings.context, key, value)
        self.save()

    def set_api_key(self, provider: str, key: str):
        """Встановити API ключ"""
        self.settings.api_keys[provider] = key
        self.save()

    def get_api_key(self, provider: str) -> Optional[str]:
        """Отримати API ключ"""
        return self.settings.api_keys.get(provider)

    def reset_to_defaults(self):
        """Скинути до налаштувань за замовчуванням"""
        self.settings = AppSettings()
        self.save()
        print("🔄 Налаштування скинуто")

    def export_settings(self, path: str) -> bool:
        """Експортувати налаштування у файл"""
        try:
            data = {
                "model": asdict(self.settings.model),
                "ui": asdict(self.settings.ui),
                "context": asdict(self.settings.context),
                "chat": asdict(self.settings.chat),
                "git": asdict(self.settings.git),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False

    def import_settings(self, path: str) -> bool:
        """Імпортувати налаштування з файлу"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "model" in data:
                self.settings.model = ModelSettings(**data["model"])
            if "ui" in data:
                self.settings.ui = UISettings(**data["ui"])
            if "context" in data:
                self.settings.context = ContextSettings(**data["context"])
            if "chat" in data:
                self.settings.chat = ChatSettings(**data["chat"])
            if "git" in data:
                self.settings.git = GitSettings(**data["git"])

            self.save()
            return True
        except Exception as e:
            print(f"⚠️ Помилка імпорту: {e}")
            return False

    def get_settings_dict(self) -> Dict:
        """Отримати словник налаштувань"""
        return {
            "model": asdict(self.settings.model),
            "ui": asdict(self.settings.ui),
            "context": asdict(self.settings.context),
            "chat": asdict(self.settings.chat),
            "git": asdict(self.settings.git),
        }


# Глобальний екземпляр
_settings: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """Отримати менеджер налаштувань"""
    global _settings
    if _settings is None:
        _settings = SettingsManager()
    return _settings
