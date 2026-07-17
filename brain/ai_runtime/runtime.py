"""
AI Runtime Manager for DevBuddy 2.0 (`brain/ai_runtime/runtime.py`).
The single, centralized gateway for all Large Language Model interactions across all agents.
No agent or sub-system is permitted to instantiate provider SDKs directly or bypass this gateway.
Coordinates prompt construction, context ranking/compression, dynamic model routing,
prompt caching, retry failover, output validation, and telemetry logging.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field

from .prompt_builder import PromptBuilder, PromptRequest, ConstructedPrompt
from .context_manager import ContextManager, MemoryCandidate
from .model_router import ModelRouter, RoutingDecision
from .cache import CacheManager
from .retry import RetryEngine
from .validator import ResponseValidator, ValidationResult
from .telemetry import TelemetryCollector, TelemetryRecord
from .providers.base_provider import BaseLLMProvider, ProviderResponse
from .providers.openai import OpenAIProvider
from .providers.gemini import GeminiProvider
from .providers.claude import ClaudeProvider
from .providers.ollama import OllamaProvider


@dataclass
class LLMRequest:
    prompt_request: PromptRequest
    task_hint: Optional[str] = None
    has_images: bool = False
    force_local: bool = False
    temperature: float = 0.7
    max_tokens: int = 2048
    use_cache: bool = True
    required_json_keys: Optional[List[str]] = None
    request_id: Optional[str] = None


@dataclass
class LLMResponse:
    text: str
    model_id: str
    provider_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_cents: float
    is_cached: bool
    validation_result: ValidationResult
    retries_used: int = 0


class AIRuntimeManager:
    """
    Singleton gateway coordinating all LLM provider requests.
    """

    _instance: Optional["AIRuntimeManager"] = None

    def __init__(self, db_dir: str = "data"):
        self.prompt_builder = PromptBuilder()
        self.context_manager = ContextManager()
        self.router = ModelRouter()
        self.cache = CacheManager(db_path=f"{db_dir}/ai_runtime_cache.db")
        self.retry_engine = RetryEngine()
        self.validator = ResponseValidator()
        self.telemetry = TelemetryCollector(db_path=f"{db_dir}/ai_runtime_telemetry.db")

        # Pluggable Provider Registry
        self.providers: Dict[str, BaseLLMProvider] = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "claude": ClaudeProvider(),
            "ollama": OllamaProvider()
        }

    @classmethod
    def get_instance(cls, db_dir: str = "data") -> "AIRuntimeManager":
        if cls._instance is None:
            cls._instance = cls(db_dir=db_dir)
        return cls._instance

    def register_provider(self, name: str, provider: BaseLLMProvider):
        """Allow runtime registration of future providers."""
        self.providers[name.lower()] = provider

    async def _execute_provider(
        self,
        provider_name: str,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        tools_schema: Optional[List[Dict[str, Any]]]
    ) -> ProviderResponse:
        prov = self.providers.get(provider_name.lower())
        if not prov:
            raise ValueError(f"Unknown or unregistered provider: '{provider_name}'")
        return await prov.generate(
            messages=messages,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            tools_schema=tools_schema
        )

    async def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Execute an LLM request through the full AI Runtime pipeline.
        """
        start_time = time.time()
        req_id = request.request_id or f"req_{int(start_time * 1000)}"

        # 1. Build standardized layered prompt
        built_prompt = self.prompt_builder.build(request.prompt_request)

        # 2. Compress context if exceeding token limits
        compressed_messages = self.context_manager.compress_and_bound(
            built_prompt.messages,
            max_tokens=request.max_tokens
        )

        # 3. Route to target provider/model
        decision = self.router.route(
            prompt_text=built_prompt.raw_prompt,
            has_images=request.has_images,
            task_hint=request.task_hint,
            force_local=request.force_local
        )

        # 4. Check cache if enabled
        if request.use_cache:
            cached_text = self.cache.get_cached(built_prompt.raw_prompt, decision.model_id)
            if cached_text:
                latency_ms = (time.time() - start_time) * 1000.0
                val_res = self.validator.validate_text(cached_text)
                if request.required_json_keys or (request.prompt_request.output_format and "json" in request.prompt_request.output_format.lower()):
                    val_res = self.validator.validate_json(cached_text, request.required_json_keys)

                record = TelemetryRecord(
                    request_id=req_id,
                    provider=decision.provider,
                    model_id=decision.model_id,
                    latency_ms=latency_ms,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    estimated_cost_cents=0.0,
                    retries_used=0,
                    cache_hit=True
                )
                self.telemetry.record(record)

                return LLMResponse(
                    text=cached_text,
                    model_id=decision.model_id,
                    provider_name=decision.provider,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    estimated_cost_cents=0.0,
                    is_cached=True,
                    validation_result=val_res
                )

        # 5. Execute via Retry Engine & Failover
        def _call_fn(p_name: str, m_id: str):
            return self._execute_provider(
                provider_name=p_name,
                model_id=m_id,
                messages=compressed_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools_schema=built_prompt.tools_schema
            )

        provider_resp, stats = await self.retry_engine.execute_with_retry(
            executor_fn=_call_fn,
            primary_provider=decision.provider,
            primary_model=decision.model_id,
            fallbacks=decision.fallback_chain
        )

        # 6. Validate Output
        if request.required_json_keys or (request.prompt_request.output_format and "json" in request.prompt_request.output_format.lower()):
            val_res = self.validator.validate_json(provider_resp.text, request.required_json_keys)
        else:
            val_res = self.validator.validate_text(provider_resp.text)

        # 7. Record Cost and Store Cache
        cost_cents = self.telemetry.estimate_cost(
            provider_resp.model_id,
            provider_resp.prompt_tokens,
            provider_resp.completion_tokens
        )
        self.router.record_cost(cost_cents)

        if request.use_cache and val_res.is_valid:
            self.cache.store_cache(
                prompt_text=built_prompt.raw_prompt,
                model_id=provider_resp.model_id,
                response_text=provider_resp.text,
                tokens_saved=provider_resp.total_tokens
            )

        # 8. Log Telemetry
        latency_ms = (time.time() - start_time) * 1000.0
        record = TelemetryRecord(
            request_id=req_id,
            provider=provider_resp.provider_name,
            model_id=provider_resp.model_id,
            latency_ms=latency_ms,
            prompt_tokens=provider_resp.prompt_tokens,
            completion_tokens=provider_resp.completion_tokens,
            total_tokens=provider_resp.total_tokens,
            estimated_cost_cents=cost_cents,
            retries_used=stats.total_attempts - 1,
            cache_hit=False,
            status="success" if val_res.is_valid else "validation_warning"
        )
        self.telemetry.record(record)

        return LLMResponse(
            text=provider_resp.text,
            model_id=provider_resp.model_id,
            provider_name=provider_resp.provider_name,
            prompt_tokens=provider_resp.prompt_tokens,
            completion_tokens=provider_resp.completion_tokens,
            total_tokens=provider_resp.total_tokens,
            estimated_cost_cents=cost_cents,
            is_cached=False,
            validation_result=val_res,
            retries_used=stats.total_attempts - 1
        )

    async def execute_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """
        Execute streaming completion chunks.
        """
        built_prompt = self.prompt_builder.build(request.prompt_request)
        compressed_messages = self.context_manager.compress_and_bound(built_prompt.messages, max_tokens=request.max_tokens)
        decision = self.router.route(
            prompt_text=built_prompt.raw_prompt,
            has_images=request.has_images,
            task_hint=request.task_hint,
            force_local=request.force_local
        )
        prov = self.providers.get(decision.provider.lower(), self.providers["ollama"])

        async for chunk in prov.stream(
            messages=compressed_messages,
            model_id=decision.model_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools_schema=built_prompt.tools_schema
        ):
            yield chunk
