"""
OpenAI Provider Adapter for DevBuddy 2.0 AI Runtime.
"""

import asyncio
import os
from typing import List, Dict, Any, AsyncGenerator, Optional
from .base_provider import BaseLLMProvider, ProviderResponse


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(provider_name="openai", api_key=api_key)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> ProviderResponse:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai is not installed.") from exc
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        response = await AsyncOpenAI(api_key=api_key).chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content or ""
        usage = response.usage
        prompt_t = getattr(usage, "prompt_tokens", 0) or 0
        comp_t = getattr(usage, "completion_tokens", 0) or 0

        return ProviderResponse(
            text=text,
            model_id=model_id,
            provider_name=self.provider_name,
            prompt_tokens=prompt_t,
            completion_tokens=comp_t,
            total_tokens=prompt_t + comp_t,
            raw_payload={"status": "success", "model": model_id}
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        await asyncio.sleep(0.005)
        last_turn = messages[-1]["content"] if messages else ""
        chunks = [f"[OpenAI ({model_id}) ", "Streaming Chunk] ", f"for input: {last_turn[:50]}..."]
        for chunk in chunks:
            await asyncio.sleep(0.005)
            yield chunk
