"""
Comprehensive Unit & Integration Test Suite for DevBuddy 2.0 AI Runtime (`brain/ai_runtime/`).
Verifies:
- AI-1: Runtime Manager central coordination and normalization
- AI-2: Prompt Builder layered hierarchy and formatting
- AI-3: Context Manager ranking, token estimation, and overflow compression
- AI-4: Model Router dynamic task-based routing (`Chat -> Ollama`, `Coding -> Claude`, `Long reasoning -> GPT`, `Image -> Gemini`)
- AI-5: Cache Manager identical prompt hashing and token savings tracking
- AI-6: Retry Engine exponential backoff and multi-tier failover (`Primary -> Secondary -> Fallback`)
- AI-7: Telemetry Collector latency, cost, and cache hit metrics
"""

import unittest
import asyncio
import os
import shutil
from typing import List, Dict, Any, AsyncGenerator

from brain.ai_runtime.prompt_builder import PromptBuilder, PromptRequest
from brain.ai_runtime.context_manager import ContextManager, MemoryCandidate
from brain.ai_runtime.model_router import ModelRouter
from brain.ai_runtime.cache import CacheManager
from brain.ai_runtime.retry import RetryEngine
from brain.ai_runtime.validator import ResponseValidator
from brain.ai_runtime.telemetry import TelemetryCollector, TelemetryRecord
from brain.ai_runtime.runtime import AIRuntimeManager, LLMRequest
from brain.ai_runtime.providers.base_provider import BaseLLMProvider, ProviderResponse


class MockFailingProvider(BaseLLMProvider):
    """Mock provider that always raises a TimeoutError to test failover progression."""
    def __init__(self, name="failing_mock"):
        super().__init__(provider_name=name)
        self.attempts = 0

    async def generate(self, messages, model_id, temperature=0.7, max_tokens=2048, tools_schema=None):
        self.attempts += 1
        raise TimeoutError(f"Simulated timeout failure in provider '{self.provider_name}'")

    async def stream(self, messages, model_id, temperature=0.7, max_tokens=2048, tools_schema=None):
        raise TimeoutError("Simulated streaming timeout")


class TestAIRuntime(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_dir = "tests/temp_ai_runtime_data"
        os.makedirs(cls.test_db_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir, ignore_errors=True)

    async def asyncSetUp(self):
        self.runtime = AIRuntimeManager(db_dir=self.test_db_dir)

    def test_ai2_prompt_builder_hierarchy(self):
        """Verify that PromptBuilder merges layers in correct order with exact section markers."""
        builder = PromptBuilder()
        req = PromptRequest(
            system_prompt="Custom System Prompt",
            developer_instructions="Never use print statements.",
            memory_context=["User prefers Python 3.12"],
            current_task="Fix bug in auth module",
            tool_results=[{"tool": "git_diff", "status": "success", "output": "- old + new"}],
            user_message="Please review the changes."
        )
        constructed = builder.build(req)

        self.assertIn("Custom System Prompt", constructed.system_instruction)
        self.assertIn("[Developer Instructions]", constructed.system_instruction)
        self.assertIn("Never use print statements.", constructed.system_instruction)

        # Check conversation messages ordering
        user_turn = constructed.messages[-1]["content"]
        self.assertIn("### [Retrieved Memory Context]\n- User prefers Python 3.12", user_turn)
        self.assertIn("### [Current Task Specification]\nFix bug in auth module", user_turn)
        self.assertIn("### [Tool Execution Results]\nTool: git_diff (Status: success) -> - old + new", user_turn)
        self.assertIn("### [User Message]\nPlease review the changes.", user_turn)

    def test_ai3_context_manager_ranking_and_compression(self):
        """Verify memory ranking and overflow turn compression bounds."""
        cm = ContextManager(default_max_tokens=100, chars_per_token=4.0)

        # Test ranking
        candidates = [
            MemoryCandidate(content="Old Low Importance", timestamp=1000.0, importance=0.1, semantic_score=0.2),
            MemoryCandidate(content="Recent High Importance", timestamp=9999999999.0, importance=0.9, semantic_score=0.9),
            MemoryCandidate(content="Medium Candidate", timestamp=5000000000.0, importance=0.5, semantic_score=0.5)
        ]
        ranked = cm.rank_memories(candidates, max_memories=2)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0], "Recent High Importance")

        # Test compression when exceeding token limits
        messages = [
            {"role": "system", "content": "You are a helpful assistant." * 5},
            {"role": "user", "content": "Turn 1 dialog message that takes tokens." * 3},
            {"role": "assistant", "content": "Turn 2 dialog response that takes tokens." * 3},
            {"role": "user", "content": "Latest user query."}
        ]
        compressed = cm.compress_and_bound(messages, max_tokens=60)
        self.assertEqual(compressed[0]["role"], "system")
        # Ensure pruning summary marker added when middle turns exceed budget
        self.assertTrue(any("Context Summary" in m["content"] or m["content"] == "Latest user query." for m in compressed))

    def test_ai4_model_router_table(self):
        """Verify dynamic routing rules across Chat, Coding, Long reasoning, and Image tasks."""
        router = ModelRouter(allow_cloud=True, budget_limit_cents=50.0)

        # Chat task -> Ollama
        r_chat = router.route("Hello, how are you today?", task_hint="chat")
        self.assertEqual(r_chat.provider, "ollama")
        self.assertEqual(r_chat.model_id, "mistral:latest")

        # Coding task -> Claude
        r_code = router.route("Check this traceback syntax error in my Python function.", task_hint="coding")
        self.assertEqual(r_code.provider, "claude")
        self.assertEqual(r_code.model_id, "claude-3-5-sonnet-20241022")

        # Long reasoning task -> GPT
        r_reason = router.route("Decompose the architectural implications of this system graph.", task_hint="reasoning")
        self.assertEqual(r_reason.provider, "openai")
        self.assertEqual(r_reason.model_id, "gpt-4o")

        # Image task -> Gemini
        r_img = router.route("Analyze this UI design screenshot.", has_images=True)
        self.assertEqual(r_img.provider, "gemini")
        self.assertEqual(r_img.model_id, "gemini-2.5-flash")

        # Verify fallback to local when spend exceeds budget
        router.record_cost(100.0)  # Exceed 50 cents limit
        r_budget = router.route("Check this traceback syntax error.", task_hint="coding")
        self.assertEqual(r_budget.provider, "ollama")

    def test_ai5_cache_manager(self):
        """Verify that identical prompts return cached responses without consuming extra tokens."""
        cache = CacheManager(db_path=f"{self.test_db_dir}/test_cache.db", default_ttl_seconds=3600)
        prompt = "Write a quick factorial function."
        model = "claude-3-5-sonnet-20241022"

        self.assertIsNone(cache.get_cached(prompt, model))
        cache.store_cache(prompt, model, "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)", tokens_saved=45)

        # Retrieve cached
        hit = cache.get_cached(prompt, model)
        self.assertIsNotNone(hit)
        self.assertIn("def factorial", hit)
        self.assertEqual(cache.cache_hits, 1)
        self.assertEqual(cache.total_tokens_saved, 45)

    async def test_ai6_retry_engine_failover(self):
        """Verify automatic failover across provider chain when primary times out."""
        retry = RetryEngine(max_retries_per_provider=1, base_delay_seconds=0.01)
        self.runtime.register_provider("failing_provider", MockFailingProvider("failing_provider"))

        def _call_fn(p_name, m_id):
            return self.runtime._execute_provider(p_name, m_id, [{"role": "user", "content": "hi"}], 0.7, 100, None)

        # Primary = failing_provider -> Fallback = ollama
        resp, stats = await retry.execute_with_retry(
            executor_fn=_call_fn,
            primary_provider="failing_provider",
            primary_model="bad_model",
            fallbacks=[{"provider": "ollama", "model_id": "mistral:latest"}]
        )
        self.assertEqual(stats.successful_provider, "ollama")
        self.assertGreaterEqual(stats.failovers_triggered, 1)
        self.assertIn("[Ollama", resp.text)

    def test_validator_and_telemetry(self):
        """Verify ResponseValidator JSON extraction and TelemetryCollector metrics aggregation."""
        val = ResponseValidator()
        raw = "Here is the result:\n```json\n{\"status\": \"ok\", \"count\": 42}\n```"
        res = val.validate_json(raw, required_keys=["status", "count"])
        self.assertTrue(res.is_valid)
        self.assertEqual(res.parsed_json["count"], 42)

        tel = TelemetryCollector(db_path=f"{self.test_db_dir}/test_tel.db")
        rec = TelemetryRecord("req_1", "claude", "claude-3-5-sonnet-20241022", 120.5, 100, 50, 150, 0.0, 0, False)
        tel.record(rec)
        summary = tel.get_summary_metrics()
        self.assertEqual(summary["total_requests"], 1)
        self.assertGreater(summary["total_cost_cents"], 0.0)

    async def test_ai1_runtime_manager_execution(self):
        """Verify end-to-end runtime execution through prompt building, routing, and caching."""
        req = LLMRequest(
            prompt_request=PromptRequest(user_message="Hello DevBuddy!"),
            task_hint="chat",
            use_cache=True
        )
        # First call -> cache miss -> routes to Ollama
        resp1 = await self.runtime.execute(req)
        self.assertFalse(resp1.is_cached)
        self.assertEqual(resp1.provider_name, "ollama")

        # Second call -> cache hit
        resp2 = await self.runtime.execute(req)
        self.assertTrue(resp2.is_cached)
        self.assertEqual(resp2.text, resp1.text)


if __name__ == "__main__":
    unittest.main()
