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
        """Load a GGUF model"""
        try:
            from llama_cpp import Llama
            import os
            import time
            import logging
            import io

            # Suppress all llama_cpp logging
            for logger_name in ["llama_cpp", "llamacpp", "llama"]:
                logging.getLogger(logger_name).setLevel(logging.CRITICAL)

            # Set environment to suppress C-level logs
            os.environ["GGML_LOG_LEVEL"] = "0"
            os.environ["LLAMA_LOG_LEVEL"] = "0"

            # Capture stdout during model loading
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            print(f"Loading model from: {model_path}")
            start = time.time()

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

            # Get any captured output and discard it
            sys.stdout.getvalue()
            sys.stdout = old_stdout

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
        """Suppress all output from llama_cpp"""
        import sys
        import os
        import io

        # Suppress Python logging
        import logging

        logging.getLogger("llama_cpp").setLevel(logging.CRITICAL)
        logging.getLogger("llamacpp").setLevel(logging.CRITICAL)

        # Suppress C-level output using file descriptor redirection
        self._old_stdout_fd = os.dup(sys.stdout.fileno())
        self._old_stderr_fd = os.dup(sys.stderr.fileno())

        # Create new file descriptors pointing to devnull
        self._devnull_out = os.open(os.devnull, os.O_WRONLY)
        self._devnull_err = os.open(os.devnull, os.O_WRONLY)

        # Redirect
        os.dup2(self._devnull_out, sys.stdout.fileno())
        os.dup2(self._devnull_err, sys.stderr.fileno())

    def _restore_stderr(self):
        """Restore stdout and stderr"""
        import sys
        import os

        try:
            # Restore stdout
            if hasattr(self, "_old_stdout_fd") and self._old_stdout_fd:
                os.dup2(self._old_stdout_fd, sys.stdout.fileno())
                os.close(self._old_stdout_fd)
            # Restore stderr
            if hasattr(self, "_old_stderr_fd") and self._old_stderr_fd:
                os.dup2(self._old_stderr_fd, sys.stderr.fileno())
                os.close(self._old_stderr_fd)
            # Close devnull fds
            if hasattr(self, "_devnull_out"):
                os.close(self._devnull_out)
            if hasattr(self, "_devnull_err"):
                os.close(self._devnull_err)
        except:
            pass

    def _run_inference(self, prompt, max_tokens, temperature):
        """Run inference"""
        import sys
        import os
        import io
        import logging

        # Suppress all output
        logging.getLogger("llama_cpp").setLevel(logging.CRITICAL)

        # Save and redirect
        stdout_fd = os.dup(sys.stdout.fileno())
        stderr_fd = os.dup(sys.stderr.fileno())
        devnull = os.open(os.devnull, os.O_WRONLY)

        os.dup2(devnull, sys.stdout.fileno())
        os.dup2(devnull, sys.stderr.fileno())

        try:
            result = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "User:", "user:"],
            )
            text = result["choices"][0]["text"]
        except Exception as e:
            # Restore first to get proper exception
            os.dup2(stdout_fd, sys.stdout.fileno())
            os.dup2(stderr_fd, sys.stderr.fileno())
            os.close(stdout_fd)
            os.close(stderr_fd)
            os.close(devnull)

            err = str(e)
            if (
                "image" in err.lower()
                or "vision" in err.lower()
                or "cannot read" in err.lower()
            ):
                raise Exception(
                    "Ця модель не підтримує изображения. Доступні лише текстові запити."
                )
            raise
        finally:
            # Restore if not already restored
            try:
                os.dup2(stdout_fd, sys.stdout.fileno())
                os.dup2(stderr_fd, sys.stderr.fileno())
                os.close(stdout_fd)
                os.close(stderr_fd)
                os.close(devnull)
            except:
                pass

        return text

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
        """Chat with model"""
        if not self.is_loaded or self.model is None:
            raise Exception("No model loaded")
        prompt = self._format_messages(messages)
        return self._run_inference(prompt, max_tokens, temperature)

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
        except Exception as e:
            err_str = str(e).lower()
            if "image" in err_str or "cannot read" in err_str:
                raise Exception(
                    "Ця модель не підтримує зображення. Доступні лише текстові запити."
                )
            raise
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
