"""
Base Provider Interface for DevBuddy 2.0 AI Runtime.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass, field


@dataclass
class ProviderResponse:
    text: str
    model_id: str
    provider_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw_payload: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM provider adapters.
    """

    def __init__(self, provider_name: str, api_key: Optional[str] = None):
        self.provider_name = provider_name
        self.api_key = api_key

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> ProviderResponse:
        """Asynchronously generate a complete completion response."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools_schema: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """Asynchronously yield completion token chunks."""
        pass
