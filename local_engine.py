"""
Local LLM Inference Engine using llama-cpp-python
No external software needed - runs models directly!
"""

import asyncio
import os
import sys
from typing import Dict, Generator, List, Optional

import io


class LocalInference:
    """Run local GGUF models using llama-cpp-python"""

    def __init__(self):
        self.model = None
        self.current_model_path = None
        self.is_loaded = False

    def load_model(self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = 0):
        """
        Load a GGUF model with reduced context for faster loading
        """
        try:
            from llama_cpp import Llama
            import os
            import time

            print(f"Loading model from: {model_path}")
            start = time.time()

            # Reduce threads for stability
            n_threads = max(2, (os.cpu_count() or 4) - 1)
            print(f"Using {n_threads} threads, context: {n_ctx}")

            self.model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_threads=n_threads,
                n_batch=512,
                verbose=False,
            )

            elapsed = time.time() - start
            print(f"Model loaded in {elapsed:.1f}s!")

            self.current_model_path = model_path
            self.is_loaded = True
            return True
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. Run: pip install llama-cpp-python"
            )
        except Exception as e:
            import traceback

            print(f"Error loading model: {e}")
            print(traceback.format_exc())
            self.is_loaded = False
            raise Exception(f"Failed to load model: {str(e)}")

    def _suppress_stderr(self):
        """Suppress stderr to hide llama_cpp warnings - C level"""
        import sys
        import os

        # Save original stderr fd
        self._old_stderr_fd = os.dup(sys.stderr.fileno())
        # Open devnull
        self._devnull_fd = os.open(os.devnull, os.O_WRONLY)
        # Redirect stderr to devnull
        os.dup2(self._devnull_fd, sys.stderr.fileno())

    def _restore_stderr(self):
        """Restore stderr"""
        import sys
        import os

        try:
            os.dup2(self._old_stderr_fd, sys.stderr.fileno())
            os.close(self._old_stderr_fd)
            os.close(self._devnull_fd)
        except:
            pass

    def _run_inference(self, prompt, max_tokens, temperature):
        """Run inference with stderr suppressed"""
        self._suppress_stderr()
        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "User:", "user:"],
            )
            return output["choices"][0]["text"]
        except Exception as e:
            err_str = str(e).lower()
            if "image" in err_str and "vision" in err_str:
                raise Exception("This model does not support images.")
            raise
        finally:
            self._restore_stderr()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: List[str] = None,
    ) -> str:
        """Generate text from prompt"""
        if not self.is_loaded or self.model is None:
            raise Exception("No model loaded")

        return self._run_inference(prompt, max_tokens, temperature)

    def chat(
        self, messages: List[Dict], max_tokens: int = 512, temperature: float = 0.7
    ) -> str:
        """
        Chat with model using message format

        Args:
            messages: List of {"role": "user|assistant", "content": "..."}
        """
        if not self.is_loaded or self.model is None:
            raise Exception("No model loaded")

        prompt = self._format_messages(messages)

        try:
            return self._run_inference(prompt, max_tokens, temperature)
        except Exception as e:
            err_str = str(e).lower()
            if "image" in err_str and "vision" in err_str:
                raise Exception("This model does not support images.")
            raise

    def chat_stream(
        self, messages: List[Dict], max_tokens: int = 512, temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """Stream chat responses"""
        if not self.is_loaded or self.model is None:
            raise Exception("No model loaded")

        prompt = self._format_messages(messages)
        self._suppress_stderr()

        try:
            for token in self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "User:", "user:"],
                stream=True,
            ):
                yield token["choices"][0]["text"]
        finally:
            self._restore_stderr()

    def _format_messages(self, messages: List[Dict]) -> str:
        """Format messages into prompt string"""
        prompt_parts = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")

        prompt_parts.append("Assistant: ")

        return "".join(prompt_parts)

    def unload(self):
        """Unload current model"""
        if self.model is not None:
            del self.model
            self.model = None
            self.current_model_path = None
            self.is_loaded = False

    def get_model_info(self) -> Optional[Dict]:
        """Get info about loaded model"""
        if not self.is_loaded or self.model is None:
            return None

        return {"path": self.current_model_path, "is_loaded": self.is_loaded}


# Global instance
_inference = None


def get_inference() -> LocalInference:
    """Get singleton inference instance"""
    global _inference
    if _inference is None:
        _inference = LocalInference()
    return _inference
