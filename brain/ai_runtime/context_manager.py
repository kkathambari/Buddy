"""
Context Manager for DevBuddy 2.0 AI Runtime.
Responsible for retrieving memories, ranking relevance (semantic, recency, importance weighting),
compressing context, summarizing overflow, and guaranteeing strict provider token limits.
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MemoryCandidate:
    content: str
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5  # 0.0 to 1.0
    semantic_score: float = 0.5  # 0.0 to 1.0
    final_score: float = 0.0


class ContextManager:
    """
    Manages prompt context windows, ranks incoming memories, and compresses dialog turns
    to guarantee prompts never exceed provider context limits.
    """

    def __init__(
        self,
        default_max_tokens: int = 8192,
        semantic_weight: float = 0.5,
        recency_weight: float = 0.25,
        importance_weight: float = 0.25,
        chars_per_token: float = 4.0
    ):
        self.default_max_tokens = default_max_tokens
        self.semantic_weight = semantic_weight
        self.recency_weight = recency_weight
        self.importance_weight = importance_weight
        self.chars_per_token = chars_per_token

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count based on average character density."""
        if not text:
            return 0
        return max(1, int(len(str(text)) / self.chars_per_token))

    def estimate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate total tokens across a list of chat message dictionaries."""
        total = 0
        for m in messages:
            total += self.estimate_tokens(m.get("content", "")) + 4  # overhead per turn
        return total

    def rank_memories(self, candidates: List[MemoryCandidate], max_memories: int = 5) -> List[str]:
        """
        Rank candidate memories combining semantic similarity, recency decay, and importance scores.
        """
        if not candidates:
            return []

        now = time.time()
        for cand in candidates:
            # Calculate recency decay (0.0 to 1.0 over a 7-day window)
            age_seconds = max(0.0, now - cand.timestamp)
            recency_score = max(0.0, 1.0 - (age_seconds / (7 * 86400)))

            cand.final_score = (
                (cand.semantic_score * self.semantic_weight) +
                (recency_score * self.recency_weight) +
                (cand.importance * self.importance_weight)
            )

        # Sort descending by final score
        sorted_cands = sorted(candidates, key=lambda x: x.final_score, reverse=True)
        return [c.content for c in sorted_cands[:max_memories] if c.content.strip()]

    def compress_and_bound(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        preserve_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Compress conversation turn buffers if total token estimation exceeds `max_tokens`.
        Summarizes overflow or drops oldest middle turns while preserving system prompts and recent turns.
        """
        limit = max_tokens or self.default_max_tokens
        current_tokens = self.estimate_messages_tokens(messages)

        if current_tokens <= limit or len(messages) <= 2:
            return messages

        compressed: List[Dict[str, str]] = []
        if preserve_system and messages and messages[0].get("role") == "system":
            compressed.append(messages[0])
            candidates = list(messages[1:])
        else:
            candidates = list(messages)

        # Always try to keep the most recent user turn (last item)
        if not candidates:
            return compressed

        latest_turn = candidates.pop(-1)
        latest_tokens = self.estimate_tokens(latest_turn.get("content", ""))

        # Calculate remaining budget
        system_tokens = self.estimate_tokens(compressed[0].get("content", "")) if compressed else 0
        safety_buffer = min(50, int(limit * 0.1))
        budget = limit - system_tokens - latest_tokens - safety_buffer

        if budget <= 0:
            # Even system + latest turn exceeds budget; truncate latest turn content if needed
            if len(candidates) > 0:
                summary_turn = {
                    "role": "system",
                    "content": f"[Context Summary: {len(candidates)} earlier dialogue turns pruned to respect {limit}-token provider limit]"
                }
                compressed.append(summary_turn)
            
            if system_tokens + latest_tokens > limit:
                truncated_len = max(10, int((limit - system_tokens - 5) * self.chars_per_token))
                latest_turn = {
                    "role": latest_turn.get("role", "user"),
                    "content": latest_turn.get("content", "")[:truncated_len] + " ... [Truncated for token limit]"
                }
            return compressed + [latest_turn]

        # Iterate backward through middle turns to keep as many recent turns as fit within budget
        kept_middle: List[Dict[str, str]] = []
        middle_tokens = 0

        for turn in reversed(candidates):
            t_tokens = self.estimate_tokens(turn.get("content", "")) + 4
            if middle_tokens + t_tokens <= budget:
                kept_middle.insert(0, turn)
                middle_tokens += t_tokens
            else:
                dropped_count = len(candidates) - len(kept_middle)
                if dropped_count > 0:
                    summary_turn = {
                        "role": "system",
                        "content": f"[Context Summary: {dropped_count} earlier dialogue turns pruned to respect {limit}-token provider limit]"
                    }
                    kept_middle.insert(0, summary_turn)
                break

        return compressed + kept_middle + [latest_turn]
