"""
Local LLM Inference Engine using llama-cpp-python
No external software needed - runs models directly!
"""

import asyncio
import os
import sys
from typing import Dict, Generator, List, Optional


class LocalInference:
    """Run local GGUF models using llama-cpp-python"""

    def __init__(self):
        self.model = None
        self.current_model_path = None
        self.is_loaded = False

    def load_model(self, model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
        """
        Load a GGUF model

        Args:
            model_path: Path to .gguf file
            n_ctx: Context size (default 4096)
            n_gpu_layers: Number of layers to offload to GPU (0 = CPU only)
        """
        try:
            from llama_cpp import Llama

            # Unload previous model
            if self.model is not None:
                del self.model

            self.model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_threads=os.cpu_count() or 4,
                verbose=False,
            )
            self.current_model_path = model_path
            self.is_loaded = True
            return True
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. Run: pip install llama-cpp-python"
            )
        except Exception as e:
            self.is_loaded = False
            raise Exception(f"Failed to load model: {str(e)}")

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

        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
        )

        return output["choices"][0]["text"]

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: List[str] = None,
    ) -> Generator[str, None, None]:
        """Stream generation results"""
        if not self.is_loaded or self.model is None:
            raise Exception("No model loaded")

        for token in self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
            stream=True,
        ):
            yield token["choices"][0]["text"]

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

        # Convert messages to prompt format
        prompt = self._format_messages(messages)

        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|im_end|>", "User:", "user:"],
        )

        return output["choices"][0]["text"]

    def chat_stream(
        self, messages: List[Dict], max_tokens: int = 512, temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """Stream chat responses"""
        if not self.is_loaded or self.model is None:
            raise Exception("No model loaded")

        prompt = self._format_messages(messages)

        for token in self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|im_end|>", "User:", "user:"],
            stream=True,
        ):
            yield token["choices"][0]["text"]

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
