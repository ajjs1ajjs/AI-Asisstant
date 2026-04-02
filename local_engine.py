"""
Local LLM Inference Engine
"""

import logging, os, sys, time
from typing import Dict, Generator, List, Optional


class LocalInference:
    def __init__(self):
        self.model = None
        self.current_model_path = None
        self.is_loaded = False

    def load_model(self, model_path, n_ctx=8192):
        try:
            from llama_cpp import Llama

            for n in ["llama_cpp", "llamacpp", "llama"]:
                logging.getLogger(n).setLevel(logging.CRITICAL)
            os.environ["GGML_LOG_LEVEL"] = "0"
            os.environ["LLAMA_LOG_LEVEL"] = "0"

            print(f"[LocalEngine] Loading model from: {model_path}")
            print(f"[LocalEngine] File exists: {os.path.exists(model_path)}")
            print(
                f"[LocalEngine] File size: {os.path.getsize(model_path) / (1024**2):.0f}MB"
            )

            self.model = Llama(model_path=model_path, n_ctx=n_ctx, verbose=False)
            self.current_model_path = model_path
            self.is_loaded = True
            print(
                f"[LocalEngine] Model loaded successfully! is_loaded={self.is_loaded}"
            )
            return True
        except Exception as e:
            print(f"[LocalEngine] Error loading model: {e}")
            import traceback

            traceback.print_exc()
            self.is_loaded = False
            raise

    def generate(self, prompt, max_tokens=2048, temperature=0.7):
        if not self.is_loaded:
            raise Exception("Model not loaded")
        stop = ["User:", "user:", "System:", "system:"]
        result = self.model(
            prompt, max_tokens=max_tokens, temperature=temperature, stop=stop
        )
        return result["choices"][0]["text"]

    def chat(
        self,
        messages,
        max_tokens=2048,
        temperature=0.7,
        tools=None,
        status_callback=None,
    ):
        if not self.is_loaded:
            raise Exception("Model not loaded")
        prompt = self._format_messages(messages, tools)
        if status_callback:
            status_callback("📝 Генерація відповіді...")
        return self.generate(prompt, max_tokens, temperature)

    def chat_stream(self, messages, max_tokens=2048, temperature=0.7, tools=None):
        if not self.is_loaded:
            raise Exception("Model not loaded")
        prompt = self._format_messages(messages, tools)
        for token in self.model(
            prompt, max_tokens=max_tokens, temperature=temperature, stream=True
        ):
            yield token["choices"][0]["text"]

    def _format_messages(self, messages, tools=None):
        parts = []

        # Tool Injection
        if tools:
            tools_json = []
            for t in tools:
                tools_json.append(
                    {
                        "name": t.get("function", {}).get("name"),
                        "description": t.get("function", {}).get("description"),
                        "parameters": t.get("function", {}).get("parameters"),
                    }
                )

            system_msg = (
                "You are an AI Coding Assistant. You have access to the following tools:\n"
                f"{tools_json}\n"
                "To use a tool, respond with a JSON block in this format:\n"
                "```json\n"
                "{\n"
                '  "tool_call": {\n'
                '    "name": "tool_name",\n'
                '    "arguments": { ... }\n'
                "  }\n"
                "}\n"
                "```\n"
                "IMPORTANT: Respond with the JSON block to perform an action."
            )
            parts.append(f"<|im_start|>system\n{system_msg}<|im_end|>\n")

        for msg in messages:
            role, content = msg["role"], msg["content"]
            if role == "system" and not tools:
                parts.append(f"<|im_start|>system\n{content}<|im_end|>\n")
            elif role == "user":
                parts.append(f"<|im_start|>user\n{content}<|im_end|>\n")
            elif role == "assistant":
                parts.append(f"<|im_start|>assistant\n{content}<|im_end|>\n")
            elif role == "thought":
                parts.append(f"<|im_start|>thought\n{content}<|im_end|>\n")

        parts.append("<|im_start|>assistant\n")
        return "".join(parts)

    def unload(self):
        if self.model:
            del self.model
        self.model = None
        self.is_loaded = False


_inference = None


def get_inference():
    global _inference
    if _inference is None:
        _inference = LocalInference()
    return _inference
