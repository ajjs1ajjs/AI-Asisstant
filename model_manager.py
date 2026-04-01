"""
Model Manager з розширеним каталогом моделей
Підтримка кількох джерел завантаження
"""

import asyncio
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import httpx


@dataclass
class ModelInfo:
    name: str
    size_gb: float
    quantization: str
    ram_required_gb: float
    description: str
    download_url: str
    sha256: str = ""
    is_downloaded: bool = False
    is_compatible: bool = True
    reason: str = ""
    source: str = "huggingface"  # huggingface, modelscope, local


class LocalModelManager:
    """Менеджер локальних LLM моделей з підтримкою кількох джерел"""

    # Дзеркала для завантаження
    MIRRORS = {
        "huggingface": "https://huggingface.co",
        "modelscope": "https://modelscope.cn",
        "ghproxy": "https://ghproxy.com",  # Проксі для HuggingFace
    }

    def __init__(self, models_dir: str = None, preferred_mirror: str = "huggingface"):
        if models_dir is None:
            self.models_dir = Path.home() / ".ai-ide" / "models"
        else:
            self.models_dir = Path(models_dir)

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.preferred_mirror = preferred_mirror

        # Розширений каталог моделей
        self.model_catalog = self._build_model_catalog()
        self._scan_downloaded_models()

    def _build_model_catalog(self) -> List[Dict]:
        """Побудувати каталог моделей з кількох джерел"""
        
        catalog = []
        
        # ========== 64GB RAM - НАЙПОТУЖНІШІ ==========
        catalog.extend([
            {
                "name": "Qwen2-72B-Instruct",
                "size_gb": 38.5,
                "ram_required_gb": 64,
                "description": "Найпотужніша 72B",
                "url": "https://huggingface.co/Qwen/Qwen2-72B-Instruct-GGUF/resolve/main/qwen2-72b-instruct-q4_0.gguf",
                "file": "qwen2-72b-instruct-q4_0.gguf",
                "tags": ["chat", "code", "multilingual"],
            },
            {
                "name": "Yi-34B-Chat",
                "size_gb": 19.2,
                "ram_required_gb": 64,
                "description": "01.AI Yi 34B Chat",
                "url": "https://huggingface.co/TheBloke/Yi-34B-Chat-GGUF/resolve/main/yi-34b-chat-q4_k_m.gguf",
                "file": "yi-34b-chat-q4_k_m.gguf",
                "tags": ["chat", "reasoning"],
            },
        ])

        # ========== 32GB RAM - ПОТУЖНІ ==========
        catalog.extend([
            {
                "name": "Qwen2.5-Coder-32B-Instruct",
                "size_gb": 18.5,
                "ram_required_gb": 32,
                "description": "🏆 Найкраща для коду 32B",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF/resolve/main/qwen2.5-coder-32b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-coder-32b-instruct-q4_k_m.gguf",
                "tags": ["code", "SOTA"],
            },
            {
                "name": "Qwen2.5-32B-Instruct",
                "size_gb": 18.2,
                "ram_required_gb": 32,
                "description": "Qwen2.5 32B Chat",
                "url": "https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF/resolve/main/qwen2.5-32b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-32b-instruct-q4_k_m.gguf",
                "tags": ["chat", "multilingual"],
            },
            {
                "name": "Gemma-2-27B-IT",
                "size_gb": 16.5,
                "ram_required_gb": 32,
                "description": "Google Gemma 2 27B",
                "url": "https://huggingface.co/bartowski/gemma-2-27b-it-GGUF/resolve/main/gemma-2-27b-it-Q4_K_M.gguf",
                "file": "gemma-2-27b-it-Q4_K_M.gguf",
                "tags": ["chat", "google"],
            },
            {
                "name": "GLM-4-9B-Chat",
                "size_gb": 9.5,
                "ram_required_gb": 32,
                "description": "GLM-4 Chinese champion",
                "url": "https://huggingface.co/THUDM/glm-4-9b-chat-GGUF/resolve/main/glm-4-9b-chat-q4_k_m.gguf",
                "file": "glm-4-9b-chat-q4_k_m.gguf",
                "tags": ["chat", "chinese"],
            },
            {
                "name": "Gemma-2-9B-IT",
                "size_gb": 5.5,
                "ram_required_gb": 32,
                "description": "Google Gemma 2 9B",
                "url": "https://huggingface.co/google/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-q4_k_m.gguf",
                "file": "gemma-2-9b-it-q4_k_m.gguf",
                "tags": ["chat", "google"],
            },
        ])

        # ========== 16GB RAM - СЕРЕДНІ ==========
        catalog.extend([
            {
                "name": "Qwen2.5-Coder-14B-Instruct",
                "size_gb": 8.4,
                "ram_required_gb": 16,
                "description": "🏆 Найкраща якість 14B",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF/resolve/main/qwen2.5-coder-14b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-coder-14b-instruct-q4_k_m.gguf",
                "tags": ["code"],
            },
            {
                "name": "Qwen2.5-14B-Instruct",
                "size_gb": 8.2,
                "ram_required_gb": 16,
                "description": "Qwen2.5 14B Chat",
                "url": "https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-14b-instruct-q4_k_m.gguf",
                "tags": ["chat"],
            },
            {
                "name": "Mistral-Nemo-12B-Instruct",
                "size_gb": 7.2,
                "ram_required_gb": 16,
                "description": "Mistral Nemo 12B",
                "url": "https://huggingface.co/bartowski/Mistral-Nemo-12B-Instruct-GGUF/resolve/main/Mistral-Nemo-12B-Instruct-Q4_K_M.gguf",
                "file": "Mistral-Nemo-12B-Instruct-Q4_K_M.gguf",
                "tags": ["chat", "mistral"],
            },
            {
                "name": "Mistral-7B-Instruct-v0.3",
                "size_gb": 4.4,
                "ram_required_gb": 16,
                "description": "Mistral 7B Instruct",
                "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2-q4_k_m.gguf",
                "file": "mistral-7b-instruct-v0.2-q4_k_m.gguf",
                "tags": ["chat", "mistral"],
            },
            {
                "name": "Llama-3.2-3B-Instruct",
                "size_gb": 2.0,
                "ram_required_gb": 16,
                "description": "Meta Llama 3.2 3B",
                "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
                "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
                "tags": ["chat", "meta"],
            },
            {
                "name": "Llama-3.1-8B-Instruct",
                "size_gb": 5.5,
                "ram_required_gb": 16,
                "description": "Meta Llama 3.1 8B",
                "url": "https://huggingface.co/bartowski/Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                "file": "Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                "tags": ["chat", "meta"],
            },
        ])

        # ========== 8GB RAM - ОПТИМАЛЬНІ ==========
        catalog.extend([
            {
                "name": "Qwen2.5-Coder-7B-Instruct",
                "size_gb": 4.4,
                "ram_required_gb": 8,
                "description": "🏆 Найкраща для коду 7B",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
                "tags": ["code", "recommended"],
            },
            {
                "name": "Qwen2.5-7B-Instruct",
                "size_gb": 4.1,
                "ram_required_gb": 8,
                "description": "Qwen2.5 7B Chat",
                "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-7b-instruct-q4_k_m.gguf",
                "tags": ["chat"],
            },
            {
                "name": "DeepSeek-Coder-6.7B-Instruct",
                "size_gb": 4.2,
                "ram_required_gb": 8,
                "description": "DeepSeek Coder 6.7B",
                "url": "https://huggingface.co/TheBloke/DeepSeek-Coder-6.7B-Instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct-q4_k_m.gguf",
                "file": "deepseek-coder-6.7b-instruct-q4_k_m.gguf",
                "tags": ["code"],
            },
            {
                "name": "Phi-3.5-mini-Instruct",
                "size_gb": 2.5,
                "ram_required_gb": 8,
                "description": "Microsoft Phi-3.5",
                "url": "https://huggingface.co/microsoft/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-q4.gguf",
                "file": "Phi-3.5-mini-instruct-q4.gguf",
                "tags": ["chat", "microsoft"],
            },
            {
                "name": "Phi-3-mini-4k-instruct",
                "size_gb": 2.2,
                "ram_required_gb": 8,
                "description": "Microsoft Phi-3 mini",
                "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
                "file": "Phi-3-mini-4k-instruct-q4.gguf",
                "tags": ["chat", "microsoft"],
            },
            {
                "name": "SmolLM2-1.7B-Instruct",
                "size_gb": 1.1,
                "ram_required_gb": 8,
                "description": "HuggingFace SmolLM2",
                "url": "https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF/resolve/main/SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
                "file": "SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
                "tags": ["chat", "small"],
            },
        ])

        # ========== 4GB RAM - МАЛЕНЬКІ ==========
        catalog.extend([
            {
                "name": "Qwen2.5-Coder-3B-Instruct",
                "size_gb": 1.9,
                "ram_required_gb": 4,
                "description": "Qwen Coder 3B",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_0.gguf",
                "file": "qwen2.5-coder-3b-instruct-q4_0.gguf",
                "tags": ["code"],
            },
            {
                "name": "Qwen2.5-Coder-1.5B-Instruct",
                "size_gb": 1.0,
                "ram_required_gb": 4,
                "description": "Qwen Coder 1.5B",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_0.gguf",
                "file": "qwen2.5-coder-1.5b-instruct-q4_0.gguf",
                "tags": ["code", "fast"],
            },
            {
                "name": "Qwen2.5-1.5B-Instruct",
                "size_gb": 1.0,
                "ram_required_gb": 4,
                "description": "Qwen2.5 1.5B Chat",
                "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_0.gguf",
                "file": "qwen2.5-1.5b-instruct-q4_0.gguf",
                "tags": ["chat", "fast"],
            },
            {
                "name": "Llama-3.2-1B-Instruct",
                "size_gb": 0.7,
                "ram_required_gb": 4,
                "description": "Meta Llama 3.2 1B",
                "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
                "file": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
                "tags": ["chat", "meta", "tiny"],
            },
            {
                "name": "TinyLlama-1.1B-Chat",
                "size_gb": 0.7,
                "ram_required_gb": 4,
                "description": "TinyLlama 1.1B",
                "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0-q4_k_m.gguf",
                "file": "TinyLlama-1.1B-Chat-v1.0-q4_k_m.gguf",
                "tags": ["chat", "tiny"],
            },
        ])

        # ========== 2GB RAM - КРИХІТНІ ==========
        catalog.extend([
            {
                "name": "Qwen2.5-Coder-0.5B-Instruct",
                "size_gb": 0.5,
                "ram_required_gb": 2,
                "description": "Qwen Coder 0.5B",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
                "tags": ["code", "tiny"],
            },
            {
                "name": "Qwen2.5-0.5B-Instruct",
                "size_gb": 0.4,
                "ram_required_gb": 2,
                "description": "Qwen2.5 0.5B Chat",
                "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf",
                "file": "qwen2.5-0.5b-instruct-q4_0.gguf",
                "tags": ["chat", "tiny"],
            },
            {
                "name": "SmolLM2-135M-Instruct",
                "size_gb": 0.1,
                "ram_required_gb": 2,
                "description": "SmolLM2 135M Ultra-fast",
                "url": "https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_K_M.gguf",
                "file": "SmolLM2-135M-Instruct-Q4_K_M.gguf",
                "tags": ["chat", "ultra-fast"],
            },
        ])

        # Сортування: завантажені перші, потім сумісні за розміром
        def sort_key(m):
            downloaded = self._is_model_downloaded(m["file"])
            compatible = m["ram_required_gb"] <= self.get_system_ram_gb() * 0.8
            return (not downloaded, not compatible, m["size_gb"])

        catalog.sort(key=sort_key)
        
        return catalog

    def _is_model_downloaded(self, filename: str) -> bool:
        """Перевірити чи модель завантажена"""
        return (self.models_dir / filename).exists()

    def get_system_ram_gb(self) -> float:
        """Отримати загальну RAM в GB"""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", c_ulonglong),
                        ("ullAvailPhys", c_ulonglong),
                        ("ullTotalPageFile", c_ulonglong),
                        ("ullAvailPageFile", c_ulonglong),
                        ("ullTotalVirtual", c_ulonglong),
                        ("ullAvailVirtual", c_ulonglong),
                        ("ullAvailExtendedVirtual", c_ulonglong),
                    ]

                status = MEMORYSTATUSEX()
                status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
                return status.ullTotalPhys / (1024**3)
            except:
                return 8.0

    def get_compatible_models(self) -> List[Dict]:
        """Отримати сумісні моделі"""
        system_ram = self.get_system_ram_gb()
        compatible = []

        for model in self.model_catalog:
            is_compatible = model["ram_required_gb"] <= system_ram * 0.8
            reason = ""

            if not is_compatible:
                reason = f"Потрібно {model['ram_required_gb']}GB RAM, у вас {system_ram:.1f}GB"

            # Перевірка завантаження
            model_path = self.models_dir / model["file"]
            is_downloaded = False
            if model_path.exists():
                actual_size_mb = model_path.stat().st_size / (1024**2)
                expected_size_mb = model["size_gb"] * 1024
                if actual_size_mb > expected_size_mb * 0.9:
                    is_downloaded = True
                else:
                    print(f"Файл {model['name']} пошкоджено: {actual_size_mb:.0f}MB vs {expected_size_mb:.0f}MB")
                    model_path.unlink()

            compatible.append({
                **model,
                "is_compatible": is_compatible,
                "reason": reason,
                "is_downloaded": is_downloaded,
                "system_ram_gb": system_ram,
            })

        # Сортування: завантажені перші, потім сумісні
        compatible.sort(
            key=lambda m: (not m["is_downloaded"], not m["is_compatible"], m["size_gb"])
        )

        return compatible

    def _scan_downloaded_models(self):
        """Позначити завантажені моделі"""
        downloaded_files = {f.name for f in self.models_dir.glob("*.gguf")}

        for model in self.model_catalog:
            if model["file"] in downloaded_files:
                model["is_downloaded"] = True

    def download_model(self, model: Dict, progress_callback=None, use_mirror: str = None) -> bool:
        """
        Завантажити модель з дзеркала

        Args:
            model: Словник з інформацією про модель
            progress_callback: Callback(progress, downloaded, total)
            use_mirror: Яке дзеркало використати
        """
        mirror = use_mirror or self.preferred_mirror
        url = model["url"]
        
        # Замінити дзеркало якщо потрібно
        if mirror != "huggingface" and "huggingface.co" in url:
            if mirror == "ghproxy":
                url = f"https://ghproxy.com/{url}"
            # Додати інші дзеркала за потреби

        file_path = self.models_dir / model["file"]
        expected_size_gb = model.get("size_gb", 0)

        # Перевірка наявності
        if file_path.exists():
            actual_size_mb = file_path.stat().st_size / (1024**2)
            expected_size_mb = expected_size_gb * 1024
            if actual_size_mb >= expected_size_mb * 0.9:
                print(f"✅ Модель вже завантажена: {file_path}")
                return True
            else:
                print(f"⚠️ Файл пошкоджено, перезавантаження...")
                file_path.unlink()

        try:
            import requests

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            print(f"📥 Завантаження з: {url}")
            print(f"📦 Очікуваний розмір: {expected_size_gb:.2f} GB")

            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, downloaded, total_size)

            final_size_mb = file_path.stat().st_size / (1024**2)
            expected_mb = total_size / (1024**2) if total_size > 0 else expected_size_gb * 1024
            
            if final_size_mb < expected_mb * 0.9:
                raise Exception(f"Завантаження неповне: {final_size_mb:.0f}MB vs {expected_mb:.0f}MB")

            print(f"✅ Завантажено: {file_path} ({final_size_mb:.0f}MB)")
            model["is_downloaded"] = True
            return True

        except Exception as e:
            print(f"❌ Помилка завантаження: {e}")
            if file_path.exists():
                file_path.unlink()
            raise Exception(f"Помилка завантаження: {str(e)}")

    def delete_model(self, model_name: str) -> bool:
        """Видалити модель"""
        model = next((m for m in self.model_catalog if m["name"] == model_name), None)
        if not model:
            return False

        file_path = self.models_dir / model["file"]
        if file_path.exists():
            file_path.unlink()
            model["is_downloaded"] = False
            print(f"🗑️ Модель видалено: {model_name}")
            return True
        return False

    def get_downloaded_models(self) -> List[Dict]:
        """Отримати завантажені моделі"""
        return [m for m in self.get_compatible_models() if m["is_downloaded"]]

    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Отримати шлях до моделі"""
        model = next((m for m in self.model_catalog if m["name"] == model_name), None)
        if not model:
            return None

        path = self.models_dir / model["file"]
        if path.exists():
            return path
        return None

    def get_storage_usage(self) -> Dict:
        """Отримати використання сховища"""
        total_size = 0
        downloaded_count = 0

        for model in self.model_catalog:
            model_path = self.models_dir / model["file"]
            if model_path.exists():
                total_size += model["size_gb"]
                downloaded_count += 1

        return {
            "models_count": downloaded_count,
            "total_size_gb": round(total_size, 2),
            "models_dir": str(self.models_dir),
        }

    def get_model_by_tag(self, tag: str) -> List[Dict]:
        """Отримати моделі за тегом"""
        return [m for m in self.model_catalog if tag in m.get("tags", [])]

    def search_models(self, query: str) -> List[Dict]:
        """Пошук моделей за назвою"""
        query_lower = query.lower()
        return [
            m for m in self.model_catalog
            if query_lower in m["name"].lower() or query_lower in m["description"].lower()
        ]
