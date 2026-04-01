# -*- coding: utf-8 -*-

code = '''"""
Local LLM Inference Engine using llama-cpp-python
"""

import logging
import os
import sys
import time
from typing import Dict, Generator, List, Optional


class LocalInference:
    def __init__(self):
        self.model = None
        self.current_model_path = None
        self.is_loaded = False
        self._model_config = {}

    def load_model(self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = 0, n_threads: int = None, n_batch: int = 512, use_mmap: bool = True, use_mlock: bool = False):
        try:
            from llama_cpp import Llama
            for logger_name in ["llama_cpp", "llamacpp", "llama"]:
                logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            os.environ["GGML_LOG_LEVEL"] = "0"
            os.environ["LLAMA_LOG_LEVEL"] = "0"
            if n_threads is None:
                n_threads = max(2, (os.cpu_count() or 4) - 1)
            print(f"Loading model: {os.path.basename(model_path)}")
            start = time.time()
            self.model = Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, n_threads=n_threads, n_batch=n_batch, use_mmap=use_mmap, use_mlock=use_mlock, verbose=False)
            elapsed = time.time() - start
            print(f"Model loaded in {elapsed:.1f}s")
            self.current_model_path = model_path
            self.is_loaded = True
            self._model_config = {"n_ctx": n_ctx, "n_gpu_layers": n_gpu_layers, "n_threads": n_threads}
            return True
        except ImportError:
            raise ImportError("Install: pip install llama-cpp-python")
        except Exception as e:
            print(f"Error: {e}")
            self.is_loaded = False
            raise

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7, stop: List[str] = None) -> str:
        if not self.is_loaded or self.model is None:
            raise Exception("Model not loaded")
        if stop is None:
            stop = [chr(10)+chr(10), "User:", "user:", "