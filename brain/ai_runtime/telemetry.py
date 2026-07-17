"""
Telemetry Collector for DevBuddy 2.0 AI Runtime.
Captures and logs comprehensive metrics for every LLM interaction:
latency, token consumption, estimated monetary cost, provider used, retry counts, and cache hits.
"""

import time
import os
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TelemetryRecord:
    request_id: str
    provider: str
    model_id: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_cents: float
    retries_used: int
    cache_hit: bool
    status: str = "success"
    timestamp: float = field(default_factory=time.time)


class TelemetryCollector:
    """
    Collects, aggregates, and persists runtime performance and cost metrics.
    """

    # Approximate pricing table in cents per 1K tokens (input, output)
    PRICING_CENTS_PER_1K: Dict[str, Tuple[float, float]] = {
        "gpt-4o": (0.25, 1.00),
        "gpt-4o-mini": (0.015, 0.06),
        "claude-3-5-sonnet-20241022": (0.30, 1.50),
        "gemini-2.5-pro": (0.125, 0.50),
        "gemini-2.5-flash": (0.0075, 0.03),
        "default": (0.05, 0.10)
    }

    def __init__(self, db_path: Optional[str] = "data/ai_runtime_telemetry.db"):
        self.db_path = db_path
        self.records: List[TelemetryRecord] = []
        self.total_requests = 0
        self.total_cache_hits = 0
        self.total_tokens_consumed = 0
        self.total_cost_cents = 0.0

        if self.db_path:
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite telemetry table."""
        try:
            if os.path.dirname(self.db_path):
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_logs (
                        request_id TEXT PRIMARY KEY,
                        provider TEXT,
                        model_id TEXT,
                        latency_ms REAL,
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        total_tokens INTEGER,
                        estimated_cost_cents REAL,
                        retries_used INTEGER,
                        cache_hit INTEGER,
                        status TEXT,
                        timestamp REAL
                    )
                """)
        except Exception:
            self.db_path = None

    def estimate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost in cents based on token usage and model pricing."""
        if "mistral" in model_id.lower() or "ollama" in model_id.lower() or "codellama" in model_id.lower():
            return 0.0  # Local models are free

        pricing = self.PRICING_CENTS_PER_1K.get(model_id, self.PRICING_CENTS_PER_1K["default"])
        in_cost = (prompt_tokens / 1000.0) * pricing[0]
        out_cost = (completion_tokens / 1000.0) * pricing[1]
        return round(in_cost + out_cost, 4)

    def record(self, record: TelemetryRecord):
        """Log a new telemetry event."""
        if record.cache_hit:
            self.total_cache_hits += 1
        else:
            if record.estimated_cost_cents <= 0.0 and (record.prompt_tokens > 0 or record.completion_tokens > 0):
                record.estimated_cost_cents = self.estimate_cost(
                    record.model_id, record.prompt_tokens, record.completion_tokens
                )

        self.total_requests += 1
        self.total_tokens_consumed += record.total_tokens
        self.total_cost_cents += record.estimated_cost_cents
        self.records.append(record)

        if self.db_path:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO telemetry_logs
                        (request_id, provider, model_id, latency_ms, prompt_tokens, completion_tokens,
                         total_tokens, estimated_cost_cents, retries_used, cache_hit, status, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.request_id, record.provider, record.model_id, record.latency_ms,
                            record.prompt_tokens, record.completion_tokens, record.total_tokens,
                            record.estimated_cost_cents, record.retries_used, 1 if record.cache_hit else 0,
                            record.status, record.timestamp
                        )
                    )
            except Exception:
                pass

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Return aggregate telemetry statistics."""
        return {
            "total_requests": self.total_requests,
            "total_cache_hits": self.total_cache_hits,
            "cache_hit_ratio": round(self.total_cache_hits / max(1, self.total_requests), 4),
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_cost_cents": round(self.total_cost_cents, 4)
        }
