import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

VALID_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-\.]{8,}$")


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
        self._validated = False

    def validate_key(self) -> bool:
        if not self.api_key:
            return False
        if not VALID_KEY_PATTERN.match(self.api_key):
            logger.warning("Invalid API key format for %s", self.base_url)
            return False
        self._validated = True
        return True

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
        payload = {"model": model, "messages": messages, "max_tokens": 4096}
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
            "max_tokens": 4096,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=None) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            }
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
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
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            }
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
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
            payload = {"model": model, "messages": messages, "max_tokens": 4096}
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
                    json={"model": model, "messages": messages, "max_tokens": 4096},
                )
                if response.status_code == 200:
                    return response.json()
                raise Exception(f"HF Error: {response.status_code}")

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        if self.provider_type == "together":
            payload = {"model": model, "messages": messages, "stream": True}
            if tools:
                payload["tools"] = tools

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as r:
                    async for line in r.aiter_lines():
                        if line.startswith("data:"):
                            yield line
        else:
            # HuggingFace real streaming
            url = f"{self.base_url}/{model}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "max_tokens": 4096,
                    },
                ) as r:
                    async for line in r.aiter_lines():
                        if line.startswith("data:"):
                            yield line


class OpenRouterProvider(BaseProvider):
    """
    OpenRouter - Aggregator for all models
    ✅ Access to Claude, GPT-4o, Llama 3
    ✅ Supports tool calls
    """

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://openrouter.ai/api/v1")
        self.models = [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "meta-llama/llama-3.1-70b-instruct",
            "google/gemini-1.5-pro",
        ]

    async def chat(self, model: str, messages: list, tools: list = None):
        payload = {"model": model, "messages": messages, "max_tokens": 4096}
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "AI Coding IDE",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code == 200:
                return response.json()
            raise Exception(f"OpenRouter Error: {response.status_code}")

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        payload = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "AI Coding IDE",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data:"):
                        yield line


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
        payload = {"model": model, "messages": messages, "max_tokens": 4096}

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
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": 4096,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data:"):
                        yield line


class LocalProvider(BaseProvider):
    def __init__(self, inference):
        super().__init__("", "")
        self.inference = inference

    async def chat(self, model: str, messages: list, tools: list = None):
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.inference.chat, messages, 2048, 0.7, tools
        )

    async def chat_stream(self, model: str, messages: list, tools: list = None):
        for chunk in self.inference.chat_stream(messages, tools=tools):
            yield chunk


class ModelOrchestrator:
    def __init__(self):
        self.models: list[Model] = []
        self.providers: dict[str, BaseProvider] = {}
        self.auto_switch = True
        self.max_retries = 5
        self.swarm_roles = {
            "developer": "Ти - досвідчений Senior Developer. Твоя задача: написати чистий, ефективний та структурований код.",
            "tester": "Ти - QA Automation Engineer. Твоя задача: написати unittest або pytest для перевірки коду на помилки.",
            "reviewer": "Ти - Security Auditor. Твоя задача: перевірити код на вразливості та знайти логічні помилки."
        }

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
                provider = self.providers[m.provider]
                if provider.api_key and provider.validate_key():
                    result.append(m)
                elif provider._validated:
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

        if not available:
            return None

        # ABSOLUTE FALLBACK: If any configured model exists, return one
        # Local models handle tools via prompt-based tool calling in the worker
        if need_tools:
            tools_models = [m for m in available if m.supports_tools]
            if tools_models:
                # Prefer models that explicitly support tools
                return max(tools_models, key=lambda m: m.score)
            else:
                # FALLBACK: Return any available model (local models handle tools via prompts)
                # This prevents "No models support tool calls" error
                return max(available, key=lambda m: m.score)

        if task == "autocomplete":
            return min(available, key=lambda m: m.latency)
        elif task == "chat":
            return max(available, key=lambda m: m.score)
        return max(available, key=lambda m: m.score)

    async def stream_request(
        self,
        messages: list,
        task: str = "chat",
        tools: list = None,
        status_callback=None,
    ):
        self.rank_models()
        need_tools = tools is not None
        last_error = None
        tried_models = set()

        for attempt in range(self.max_retries):
            model = self.pick_model(task, need_tools)
            if not model:
                # Fallback: if we need tools but no model supports them, try without tools flag
                if need_tools:
                    need_tools = False
                    model = self.pick_model(task, need_tools=False)
                    if model:
                        # Continue without tools - local models handle tools via prompts
                        tools = None
                    else:
                        raise last_error or Exception(
                            "No available models - please setup an API key"
                        )
                else:
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

            if status_callback:
                status_callback(f"🤖 Модель: {model.name} ({model.provider})")

            try:
                token_count = 0
                async for chunk in provider.chat_stream(model.name, messages, tools):
                    token_count += 1
                    if status_callback and token_count % 50 == 0:
                        status_callback(f"📝 Генерація... ({token_count} токенів)")
                    yield chunk
                if status_callback:
                    status_callback(f"✅ Готово ({token_count} токенів)")
                return
            except Exception as e:
                last_error = e
                model.cooldown_until = time.time() + 60
                if status_callback:
                    status_callback(f"❌ {model.name}: {str(e)[:50]}")

        raise last_error or Exception("All models failed")

    async def request(self, messages: list, task: str = "chat", tools: list = None):
        self.rank_models()
        need_tools = tools is not None
        last_error = None
        tried_models = set()

        for attempt in range(self.max_retries):
            model = self.pick_model(task, need_tools)
            if not model:
                # Fallback: if we need tools but no model supports them, try without tools flag
                if need_tools:
                    need_tools = False
                    model = self.pick_model(task, need_tools=False)
                    if model:
                        # Continue without tools - local models handle tools via prompts
                        tools = None
                    else:
                        raise last_error or Exception(
                            "No available models - please setup an API key"
                        )
                else:
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
                message = response["choices"][0]["message"]
                if "tool_calls" in message and message["tool_calls"]:
                    return message
                return message.get("content", "")
            except Exception as e:
                last_error = e
                model.cooldown_until = time.time() + 60

        raise last_error or Exception("All models failed")
    async def swarm_request(self, user_query: str, status_callback=None):
        """Executes a task using multiple sub-agents in parallel"""
        if status_callback:
            status_callback("🐝 Активую Swarm Mode (Паралельний запуск)...")
        
        async def run_role(role, system_prompt):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
            try:
                # Pick best model for each sub-agent
                res = await self.request(messages, task="chat")
                return f"### Role: {role.capitalize()}\n{res}\n"
            except Exception as e:
                return f"### Role: {role.capitalize()} Error: {e}"

        # Run all roles in parallel
        tasks = [run_role(role, prompt) for role, prompt in self.swarm_roles.items()]
        results = await asyncio.gather(*tasks)
        
        return "\n".join(results)
