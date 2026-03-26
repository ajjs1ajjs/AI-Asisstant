import asyncio
import json
import time
from dataclasses import dataclass
from typing import List, Optional

import httpx


@dataclass
class Model:
    name: str
    provider: str
    latency: float = 0.0
    score: float = 0.5
    context_size: int = 4096
    cooldown_until: float = 0.0
    is_available: bool = True
    is_free: bool = True
    requires_key: bool = True
    setup_url: str = ""
    description: str = ""
    supports_tools: bool = False


class BaseProvider:
    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        raise NotImplementedError

    async def chat(self, model: str, messages: list, tools: list = None):
        raise NotImplementedError


class GroqProvider(BaseProvider):
    """
    Groq - FREE tier, ultra-fast
    ✅ Free forever
    ✅ Supports tool calls
    ✅ Best for coding
    """

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.groq.com/openai/v1")
        self.models = [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ]

    async def chat(self, model: str, messages: list, tools: list = None):
        payload = {"model": model, "messages": messages, "max_tokens": 2048}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            if response.status_code == 200:
                return response.json()
            raise Exception(f"Groq Error: {response.status_code}")

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 2048,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data:"):
                        yield line


class DeepSeekProvider(BaseProvider):
    """
    DeepSeek - FREE tier (currently)
    ✅ Excellent for coding
    ✅ Supports tool calls
    ✅ 128K context
    """

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.deepseek.com/v1")
        self.models = ["deepseek-chat", "deepseek-coder"]

    async def chat(self, model: str, messages: list, tools: list = None):
        payload = {"model": model, "messages": messages, "max_tokens": 4096}
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            if response.status_code == 200:
                return response.json()
            raise Exception(f"DeepSeek Error: {response.status_code}")

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        payload = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data:"):
                        yield line


class QwenProvider(BaseProvider):
    """
    Qwen (Alibaba) - FREE via HuggingFace or Together
    ✅ Excellent coding models
    ✅ Supports tool calls
    ✅ Qwen2.5-Coder is SOTA for code
    """

    def __init__(self, api_key: str = "", provider_type: str = "huggingface"):
        if provider_type == "together":
            super().__init__(api_key, "https://api.together.xyz/v1")
        else:
            super().__init__(
                api_key, "https://router.huggingface.co/hf-inference/models"
            )
        self.provider_type = provider_type
        self.models = [
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "Qwen/Qwen2.5-Coder-7B-Instruct",
        ]

    async def chat(self, model: str, messages: list, tools: list = None):
        if self.provider_type == "together":
            payload = {"model": model, "messages": messages, "max_tokens": 2048}
            if tools:
                payload["tools"] = tools

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                if response.status_code == 200:
                    return response.json()
                raise Exception(f"Together Error: {response.status_code}")
        else:
            # HuggingFace
            url = f"{self.base_url}/{model}/v1/chat/completions"
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"model": model, "messages": messages, "max_tokens": 2048},
                )
                if response.status_code == 200:
                    return response.json()
                raise Exception(f"HF Error: {response.status_code}")

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        result = await self.chat(model, messages, tools)
        content = result["choices"][0]["message"]["content"]
        for i in range(0, len(content), 10):
            yield f'data: {{"choices": [{{"delta": {{"content": "{content[i : i + 10]}"}}}}]}}'
            await asyncio.sleep(0.01)


class SiliconFlowProvider(BaseProvider):
    """
    SiliconFlow - FREE Qwen models
    ✅ Qwen-2.5-Coder models
    ✅ Free tier available
    ✅ Great for coding
    """

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.siliconflow.cn/v1")
        self.models = ["Qwen/Qwen2.5-Coder-32B-Instruct", "Qwen/Qwen2.5-72B-Instruct"]

    async def chat(self, model: str, messages: list, tools: list = None):
        payload = {"model": model, "messages": messages, "max_tokens": 2048}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            if response.status_code == 200:
                return response.json()
            raise Exception(f"SiliconFlow Error: {response.status_code}")

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        result = await self.chat(model, messages, tools)
        content = result["choices"][0]["message"]["content"]
        for i in range(0, len(content), 10):
            yield f'data: {{"choices": [{{"delta": {{"content": "{content[i : i + 10]}"}}}}]}}'
            await asyncio.sleep(0.01)


class ModelOrchestrator:
    def __init__(self):
        self.models: list[Model] = []
        self.providers: dict[str, BaseProvider] = {}
        self.auto_switch = True
        self.max_retries = 5

    def add_provider(self, name: str, provider: BaseProvider):
        self.providers[name] = provider

    def add_model(self, model: Model):
        self.models.append(model)

    def get_configured_models(self) -> list:
        """Get only models with valid API keys"""
        result = []
        for m in self.models:
            if not m.requires_key:
                result.append(m)
            elif m.provider in self.providers:
                if self.providers[m.provider].api_key:
                    result.append(m)
        return result

    def rank_models(self):
        available = self.get_configured_models()
        # Prioritize: tools support > score > is_free
        available.sort(
            key=lambda m: (m.supports_tools, m.score, m.is_free), reverse=True
        )
        self.models = available + [m for m in self.models if m not in available]

    def pick_model(self, task: str, need_tools: bool = False) -> Optional[Model]:
        available = self.get_configured_models()
        available = [m for m in available if m.cooldown_until <= time.time()]

        if need_tools:
            available = [m for m in available if m.supports_tools]

        if not available:
            return None

        if task == "autocomplete":
            return min(available, key=lambda m: m.latency)
        elif task == "chat":
            return max(available, key=lambda m: m.score)
        return max(available, key=lambda m: m.score)

    async def stream_request(
        self, messages: list, task: str = "chat", tools: list = None
    ):
        self.rank_models()
        need_tools = tools is not None
        last_error = None
        tried_models = set()

        for attempt in range(self.max_retries):
            model = self.pick_model(task, need_tools)
            if not model:
                if need_tools:
                    raise Exception("No models support tool calls")
                raise last_error or Exception(
                    "No available models - please setup an API key"
                )

            if model.name in tried_models and self.auto_switch:
                model.cooldown_until = time.time() + 30
                continue

            tried_models.add(model.name)
            provider = self.providers.get(model.provider)
            if not provider:
                continue

            try:
                async for chunk in provider.chat_stream(model.name, messages, tools):
                    yield chunk
                return
            except Exception as e:
                last_error = e
                model.cooldown_until = time.time() + 60

        raise last_error or Exception("All models failed")

    async def request(self, messages: list, task: str = "chat", tools: list = None):
        self.rank_models()
        need_tools = tools is not None
        last_error = None
        tried_models = set()

        for attempt in range(self.max_retries):
            model = self.pick_model(task, need_tools)
            if not model:
                if need_tools:
                    raise Exception("No models support tool calls")
                raise last_error or Exception("No available models")

            if model.name in tried_models and self.auto_switch:
                model.cooldown_until = time.time() + 30
                continue

            tried_models.add(model.name)
            provider = self.providers.get(model.provider)
            if not provider:
                continue

            try:
                response = await provider.chat(model.name, messages, tools)
                return response["choices"][0]["message"]["content"]
            except Exception as e:
                last_error = e
                model.cooldown_until = time.time() + 60

        raise last_error or Exception("All models failed")
