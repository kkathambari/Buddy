"""
Anthropic Claude Provider Adapter for DevBuddy 2.0 AI Runtime.
"""

import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from .base_provider import BaseLLMProvider, ProviderResponse


class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(provider_name="claude", api_key=api_key)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> ProviderResponse:
        await asyncio.sleep(0.01)
        last_turn = messages[-1]["content"] if messages else ""
        prompt_t = max(10, int(len(last_turn) / 4))
        comp_t = max(30, int(len(last_turn) / 3))
        text = f"[Claude ({model_id}) Completion] -> Processed: {last_turn[:120]}..."

        return ProviderResponse(
            text=text,
            model_id=model_id,
            provider_name=self.provider_name,
            prompt_tokens=prompt_t,
            completion_tokens=comp_t,
            total_tokens=prompt_t + comp_t,
            raw_payload={"status": "mock_or_sdk_success", "model": model_id}
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        await asyncio.sleep(0.005)
        last_turn = messages[-1]["content"] if messages else ""
        chunks = [f"[Claude ({model_id}) ", "Streaming Chunk] ", f"for input: {last_turn[:50]}..."]
        for chunk in chunks:
            await asyncio.sleep(0.005)
            yield chunk
