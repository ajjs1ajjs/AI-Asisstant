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


class LocalModelManager:
    """Manage local LLM models - download, delete, list compatible"""

    def __init__(self, models_dir: str = None):
        if models_dir is None:
            self.models_dir = Path.home() / ".ai-ide" / "models"
        else:
            self.models_dir = Path(models_dir)

        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Catalog of models optimized for coding
        self.model_catalog = [
            # Qwen Coder - BEST for programming
            {
                "name": "Qwen2.5-Coder-7B-Instruct",
                "size_gb": 4.7,
                "quantization": "Q4_K_M",
                "ram_required_gb": 8,
                "description": "🏆 BEST for CODE - Qwen 2.5 Coder",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
            },
            {
                "name": "Qwen2.5-Coder-14B-Instruct",
                "size_gb": 9.1,
                "quantization": "Q4_K_M",
                "ram_required_gb": 16,
                "description": "🏆 BEST 14B - Excellent code quality",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF/resolve/main/qwen2.5-coder-14b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-coder-14b-instruct-q4_k_m.gguf",
            },
            {
                "name": "Qwen2.5-Coder-32B-Instruct",
                "size_gb": 19.5,
                "quantization": "Q4_K_M",
                "ram_required_gb": 32,
                "description": "👑 SOTA for CODE - 32B beast",
                "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF/resolve/main/qwen2.5-coder-32b-instruct-q4_k_m.gguf",
                "file": "qwen2.5-coder-32b-instruct-q4_k_m.gguf",
            },
            # DeepSeek Coder
            {
                "name": "DeepSeek-Coder-6.7B-Instruct",
                "size_gb": 4.2,
                "quantization": "Q4_K_M",
                "ram_required_gb": 8,
                "description": "🎯 DeepSeek Coder - Great for code",
                "url": "https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct-q4_k_m.gguf",
                "file": "deepseek-coder-6.7b-instruct-q4_k_m.gguf",
            },
            {
                "name": "DeepSeek-Coder-33B-Instruct",
                "size_gb": 19.2,
                "quantization": "Q4_K_M",
                "ram_required_gb": 32,
                "description": "🎯 DeepSeek 33B - Code specialist",
                "url": "https://huggingface.co/TheBloch/deepseek-coder-33b-instruct-GGUF/resolve/main/deepseek-coder-33b-instruct-q4_k_m.gguf",
                "file": "deepseek-coder-33b-instruct-q4_k_m.gguf",
            },
            # Llama for general tasks
            {
                "name": "Llama-3.2-3B-Instruct",
                "size_gb": 2.1,
                "quantization": "Q4_K_M",
                "ram_required_gb": 4,
                "description": "⚡ Super fast - 3B for weak PCs",
                "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
                "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            },
            {
                "name": "Llama-3.1-8B-Instruct",
                "size_gb": 5.5,
                "quantization": "Q4_K_M",
                "ram_required_gb": 8,
                "description": "🦙 Llama 3.1 - Balanced",
                "url": "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                "file": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            },
            {
                "name": "Llama-3.1-70B-Instruct",
                "size_gb": 42.5,
                "quantization": "Q4_K_M",
                "ram_required_gb": 64,
                "description": "🦙 Llama 3.1 70B - Powerful",
                "url": "https://huggingface.co/bartowski/Meta-Llama-3.1-70B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf",
                "file": "Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf",
            },
            # Phi-3 - Microsoft efficient
            {
                "name": "Phi-3-mini-4k-instruct",
                "size_gb": 2.5,
                "quantization": "Q4_K_M",
                "ram_required_gb": 4,
                "description": "📱 Phi-3 Mini - Tiny but smart",
                "url": "https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q4_K_M.gguf",
                "file": "Phi-3-mini-4k-instruct-Q4_K_M.gguf",
            },
            {
                "name": "Phi-3-medium-4k-instruct",
                "size_gb": 5.2,
                "quantization": "Q4_K_M",
                "ram_required_gb": 8,
                "description": "📱 Phi-3 Medium - Great value",
                "url": "https://huggingface.co/bartowski/Phi-3-medium-4k-instruct-GGUF/resolve/main/Phi-3-medium-4k-instruct-Q4_K_M.gguf",
                "file": "Phi-3-medium-4k-instruct-Q4_K_M.gguf",
            },
            # Mistral
            {
                "name": "Mistral-7B-Instruct-v0.3",
                "size_gb": 4.4,
                "quantization": "Q4_K_M",
                "ram_required_gb": 8,
                "description": "💨 Mistral v3 - Reliable 7B",
                "url": "https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
                "file": "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
            },
        ]

        self._scan_downloaded_models()

    def get_system_ram_gb(self) -> float:
        """Get total system RAM in GB"""
        try:
            import psutil

            return psutil.virtual_memory().total / (1024**3)
        except:
            # Fallback for Windows
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
                return 8.0  # Default assumption

    def get_compatible_models(self) -> List[Dict]:
        """Get models that can run on this PC"""
        system_ram = self.get_system_ram_gb()
        compatible = []

        for model in self.model_catalog:
            is_compatible = (
                model["ram_required_gb"] <= system_ram * 0.8
            )  # Use 80% of RAM
            reason = ""

            if not is_compatible:
                reason = f"Need {model['ram_required_gb']}GB RAM, you have {system_ram:.1f}GB"

            # Check if already downloaded
            model_path = self.models_dir / model["file"]
            is_downloaded = model_path.exists()

            compatible.append(
                {
                    **model,
                    "is_compatible": is_compatible,
                    "reason": reason,
                    "is_downloaded": is_downloaded,
                    "system_ram_gb": system_ram,
                }
            )

        # Sort: downloaded first, then compatible by size
        compatible.sort(
            key=lambda m: (not m["is_downloaded"], not m["is_compatible"], m["size_gb"])
        )

        return compatible

    def _scan_downloaded_models(self):
        """Mark downloaded models"""
        downloaded_files = {f.name for f in self.models_dir.glob("*.gguf")}

        for model in self.model_catalog:
            if model["file"] in downloaded_files:
                model["is_downloaded"] = True

    def download_model(self, model: Dict, progress_callback=None) -> bool:
        """Download a model with progress tracking"""
        url = model["url"]
        file_path = self.models_dir / model["file"]

        if file_path.exists():
            return True

        try:
            import requests

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            print(f"Завантаження з: {url}")

            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            print(f"Розмір файлу: {total_size / (1024**3):.2f} GB")

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, downloaded, total_size)

            print(f"Завантажено: {file_path}")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"HTTP помилка: {e}")
            if file_path.exists():
                file_path.unlink()
            raise Exception(f"HTTP помилка: {e}")
        except Exception as e:
            print(f"Помилка завантаження: {e}")
            if file_path.exists():
                file_path.unlink()
            raise Exception(f"Помилка завантаження: {e}")

    def delete_model(self, model_name: str) -> bool:
        """Delete a downloaded model"""
        model = next((m for m in self.model_catalog if m["name"] == model_name), None)
        if not model:
            return False

        file_path = self.models_dir / model["file"]
        if file_path.exists():
            file_path.unlink()
            model["is_downloaded"] = False
            return True
        return False

    def get_downloaded_models(self) -> List[Dict]:
        """Get list of downloaded models"""
        return [m for m in self.get_compatible_models() if m["is_downloaded"]]

    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get path to model file"""
        model = next((m for m in self.model_catalog if m["name"] == model_name), None)
        if not model:
            return None

        path = self.models_dir / model["file"]
        if path.exists():
            return path
        return None

    def get_storage_usage(self) -> Dict:
        """Get storage usage info"""
        total_size = 0
        downloaded_count = 0

        for model in self.model_catalog:
            model_path = self.models_dir / model["file"]
            if model_path.exists():
                total_size += model["size_gb"]
                downloaded_count += 1

        return {
            "models_count": downloaded_count,
            "total_size_gb": total_size,
            "models_dir": str(self.models_dir),
        }
