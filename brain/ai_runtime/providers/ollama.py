"""
Ollama Provider Adapter for DevBuddy 2.0 AI Runtime (Local offline LLMs).
"""

import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from .base_provider import BaseLLMProvider, ProviderResponse


class OllamaProvider(BaseLLMProvider):
    def __init__(self, endpoint_url: str = "http://localhost:11434"):
        super().__init__(provider_name="ollama", api_key=None)
        self.endpoint_url = endpoint_url

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "mistral:latest",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> ProviderResponse:
        await asyncio.sleep(0.01)
        last_turn = messages[-1]["content"] if messages else ""
        prompt_t = max(10, int(len(last_turn) / 4))
        comp_t = max(15, int(len(last_turn) / 3))
        text = f"[Ollama ({model_id}) Completion] -> Processed: {last_turn[:120]}..."

        return ProviderResponse(
            text=text,
            model_id=model_id,
            provider_name=self.provider_name,
            prompt_tokens=prompt_t,
            completion_tokens=comp_t,
            total_tokens=prompt_t + comp_t,
            raw_payload={"status": "mock_or_local_server_success", "model": model_id}
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "mistral:latest",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        await asyncio.sleep(0.005)
        last_turn = messages[-1]["content"] if messages else ""
        chunks = [f"[Ollama ({model_id}) ", "Streaming Chunk] ", f"for input: {last_turn[:50]}..."]
        for chunk in chunks:
            await asyncio.sleep(0.005)
            yield chunk
