"""
Cache Manager for DevBuddy 2.0 AI Runtime.
Stores and retrieves cached responses for identical prompt structures to reduce token costs and latency.
Supports in-memory caching and optional SQLite persistence with TTL invalidation.
"""

import time
import hashlib
import sqlite3
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CacheEntry:
    prompt_hash: str
    response_text: str
    model_id: str
    created_at: float
    ttl_seconds: float
    tokens_saved: int


class CacheManager:
    """
    Prompt caching engine. Checks SHA-256 hashes of normalized prompts against stored responses.
    """

    def __init__(self, db_path: Optional[str] = "data/ai_runtime_cache.db", default_ttl_seconds: float = 3600.0):
        self.default_ttl_seconds = default_ttl_seconds
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.db_path = db_path
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_tokens_saved = 0

        if self.db_path:
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite cache table if directory/db is accessible."""
        try:
            if os.path.dirname(self.db_path):
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_cache (
                        prompt_hash TEXT PRIMARY KEY,
                        response_text TEXT,
                        model_id TEXT,
                        created_at REAL,
                        ttl_seconds REAL,
                        tokens_saved INTEGER
                    )
                """)
        except Exception:
            # Fallback to pure in-memory cache if file system fails or locked
            self.db_path = None

    def compute_hash(self, prompt_text: str, model_id: str) -> str:
        """Compute SHA-256 hash of normalized prompt + model id."""
        payload = f"{model_id.strip().lower()}:::{prompt_text.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get_cached(self, prompt_text: str, model_id: str) -> Optional[str]:
        """Retrieve cached response if present and not expired."""
        key = self.compute_hash(prompt_text, model_id)
        now = time.time()

        # 1. Check in-memory dict
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if now - entry.created_at <= entry.ttl_seconds:
                self.cache_hits += 1
                self.total_tokens_saved += entry.tokens_saved
                return entry.response_text
            else:
                del self.memory_cache[key]

        # 2. Check SQLite table if configured
        if self.db_path:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT response_text, created_at, ttl_seconds, tokens_saved FROM prompt_cache WHERE prompt_hash = ?",
                        (key,)
                    )
                    row = cursor.fetchone()
                    if row:
                        resp_text, created_at, ttl_sec, tokens_saved = row
                        if now - created_at <= ttl_sec:
                            # Populate in-memory for fast future lookup
                            self.memory_cache[key] = CacheEntry(
                                prompt_hash=key,
                                response_text=resp_text,
                                model_id=model_id,
                                created_at=created_at,
                                ttl_seconds=ttl_sec,
                                tokens_saved=tokens_saved
                            )
                            self.cache_hits += 1
                            self.total_tokens_saved += tokens_saved
                            return resp_text
                        else:
                            conn.execute("DELETE FROM prompt_cache WHERE prompt_hash = ?", (key,))
            except Exception:
                pass

        self.cache_misses += 1
        return None

    def store_cache(
        self,
        prompt_text: str,
        model_id: str,
        response_text: str,
        tokens_saved: int = 0,
        ttl_seconds: Optional[float] = None
    ):
        """Store new response inside memory and SQLite tables."""
        key = self.compute_hash(prompt_text, model_id)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        now = time.time()

        entry = CacheEntry(
            prompt_hash=key,
            response_text=response_text,
            model_id=model_id,
            created_at=now,
            ttl_seconds=ttl,
            tokens_saved=tokens_saved
        )
        self.memory_cache[key] = entry

        if self.db_path:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO prompt_cache
                        (prompt_hash, response_text, model_id, created_at, ttl_seconds, tokens_saved)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (key, response_text, model_id, now, ttl, tokens_saved)
                    )
            except Exception:
                pass

    def invalidate(self, prompt_text: str, model_id: str):
        """Manually invalidate/delete a cached prompt entry."""
        key = self.compute_hash(prompt_text, model_id)
        self.memory_cache.pop(key, None)
        if self.db_path:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM prompt_cache WHERE prompt_hash = ?", (key,))
            except Exception:
                pass
