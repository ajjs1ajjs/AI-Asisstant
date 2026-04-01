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

    def load_model(self, model_path, n_ctx=2048):
        try:
            from llama_cpp import Llama
            for n in ["llama_cpp", "llamacpp", "llama"]: 
                logging.getLogger(n).setLevel(logging.CRITICAL)
            os.environ["GGML_LOG_LEVEL"] = "0"
            os.environ["LLAMA_LOG_LEVEL"] = "0"
            self.model = Llama(model_path=model_path, n_ctx=n_ctx, verbose=False)
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Error: {e}")
            self.is_loaded = False
            raise

    def generate(self, prompt, max_tokens=512, temperature=0.7):
        if not self.is_loaded: 
            raise Exception("Model not loaded")
        stop = [chr(10)+chr(10), "User:", "user:"]
        result = self.model(prompt, max_tokens=max_tokens, temperature=temperature, stop=stop)
        return result["choices"][0]["text"]

    def chat(self, messages, max_tokens=512, temperature=0.7):
        if not self.is_loaded: 
            raise Exception("Model not loaded")
        prompt = self._format_messages(messages)
        return self.generate(prompt, max_tokens, temperature)

    def chat_stream(self, messages, max_tokens=512, temperature=0.7):
        if not self.is_loaded: 
            raise Exception("Model not loaded")
        prompt = self._format_messages(messages)
        for token in self.model(prompt, max_tokens=max_tokens, temperature=temperature, stream=True):
            yield token["choices"][0]["text"]

    def _format_messages(self, messages):
        parts = []
        for msg in messages:
            role, content = msg["role"], msg["content"]
            if role == "system": 
                parts.append(f"System: {content}" + chr(10))
            elif role == "user": 
                parts.append(f"User: {content}" + chr(10))
            elif role == "assistant": 
                parts.append(f"Assistant: {content}" + chr(10))
        parts.append("Assistant: ")
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
