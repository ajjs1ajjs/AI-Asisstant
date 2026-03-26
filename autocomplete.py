import asyncio
from typing import Optional


class AutocompleteEngine:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.debounce_ms = 500
        self.max_context_lines = 50
        self.max_suggestion_length = 200

    def get_context(self, text: str, cursor_position: int) -> str:
        lines = text[:cursor_position].split("\n")
        context_lines = lines[-self.max_context_lines :]
        return "\n".join(context_lines)

    def get_current_line(self, text: str, cursor_position: int) -> str:
        lines = text[:cursor_position].split("\n")
        return lines[-1] if lines else ""

    async def autocomplete(self, text: str, cursor_position: int) -> Optional[str]:
        context = self.get_context(text, cursor_position)
        current_line = self.get_current_line(text, cursor_position)

        if not current_line.strip():
            return None

        prompt = (
            f"You are a code completion assistant. "
            f"Complete the current line of code. "
            f"Return ONLY the completion text, no explanations.\n\n"
            f"Context:\n{context}\n\n"
            f"Current line (incomplete): {current_line}\n"
            f"Complete this line:"
        )

        try:
            messages = [{"role": "user", "content": prompt}]
            completion = await self.orchestrator.request(messages, task="autocomplete")

            completion = completion.strip()

            if completion.startswith(current_line):
                completion = completion[len(current_line) :]

            if len(completion) > self.max_suggestion_length:
                completion = completion[: self.max_suggestion_length]

            return completion if completion else None
        except Exception:
            return None

    async def autocomplete_with_debounce(
        self, text: str, cursor_position: int
    ) -> Optional[str]:
        await asyncio.sleep(self.debounce_ms / 1000.0)
        return await self.autocomplete(text, cursor_position)
