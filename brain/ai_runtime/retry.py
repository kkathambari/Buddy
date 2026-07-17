"""
Retry Engine for DevBuddy 2.0 AI Runtime.
Handles transient provider failures, connection timeouts, and rate limits using exponential backoff
and automatic failover progression across alternate LLM providers.
Example: GPT -> Timeout -> Retry -> Claude -> Retry -> Gemini.
"""

import asyncio
import time
from typing import Callable, Awaitable, Any, List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class RetryAttemptStats:
    total_attempts: int = 0
    failovers_triggered: int = 0
    last_error: str = ""
    successful_provider: str = ""
    successful_model: str = ""


class RetryEngine:
    """
    Executes async LLM generation calls with exponential backoff (`base_delay * (2 ^ attempt)`)
    and cascades across alternate provider fallbacks on persistent failures.
    """

    def __init__(self, max_retries_per_provider: int = 2, base_delay_seconds: float = 0.5, max_delay_seconds: float = 4.0):
        self.max_retries_per_provider = max_retries_per_provider
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds

    async def execute_with_retry(
        self,
        executor_fn: Callable[[str, str], Awaitable[Any]],
        primary_provider: str,
        primary_model: str,
        fallbacks: List[Dict[str, str]]
    ) -> Tuple[Any, RetryAttemptStats]:
        """
        Execute `executor_fn(provider_name, model_id)` with retries and failover.
        Returns `(response_payload, stats)`.
        """
        stats = RetryAttemptStats()
        chain = [{"provider": primary_provider, "model_id": primary_model}] + fallbacks

        for chain_idx, target in enumerate(chain):
            prov = target.get("provider", "unknown")
            mod = target.get("model_id", "default")

            if chain_idx > 0:
                stats.failovers_triggered += 1

            for attempt in range(self.max_retries_per_provider + 1):
                stats.total_attempts += 1
                try:
                    res = await executor_fn(prov, mod)
                    stats.successful_provider = prov
                    stats.successful_model = mod
                    return res, stats
                except (TimeoutError, ConnectionError, OSError, ValueError, RuntimeError) as exc:
                    stats.last_error = f"{prov}/{mod} (attempt {attempt+1}): {str(exc)}"
                    if attempt < self.max_retries_per_provider:
                        # Exponential backoff delay
                        delay = min(self.max_delay_seconds, self.base_delay_seconds * (2 ** attempt))
                        await asyncio.sleep(delay)
                    else:
                        # Exhausted retries for this provider; break to next fallback in chain
                        break

        raise RuntimeError(f"All providers in failover chain exhausted. Last error: {stats.last_error}")
