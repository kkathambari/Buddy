"""
Model Router for DevBuddy 2.0 AI Runtime.
Dynamically assigns target LLM providers and models based on task classification, image payloads,
complexity estimation, and budget constraints.
No agent is permitted to hardcode a provider or model name.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RoutingDecision:
    provider: str        # e.g., "ollama", "claude", "openai", "gemini"
    model_id: str        # e.g., "mistral:latest", "claude-3-5-sonnet-20241022", "gpt-4o", "gemini-2.5-pro"
    fallback_chain: List[Dict[str, str]] = field(default_factory=list)
    reasoning: str = ""


class ModelRouter:
    """
    Evaluates incoming prompt requests to select the optimal model and failover chain.
    """

    def __init__(self, allow_cloud: bool = True, budget_limit_cents: float = 100.0):
        self.allow_cloud = allow_cloud
        self.budget_limit_cents = budget_limit_cents
        self.current_spent_cents = 0.0

        # Default routing tables
        self.default_routes = {
            "chat": {
                "provider": "ollama",
                "model_id": "mistral:latest",
                "fallbacks": [
                    {"provider": "gemini", "model_id": "gemini-2.5-flash"},
                    {"provider": "openai", "model_id": "gpt-4o-mini"}
                ]
            },
            "coding": {
                "provider": "claude",
                "model_id": "claude-3-5-sonnet-20241022",
                "fallbacks": [
                    {"provider": "gemini", "model_id": "gemini-2.5-pro"},
                    {"provider": "openai", "model_id": "gpt-4o"},
                    {"provider": "ollama", "model_id": "codellama:latest"}
                ]
            },
            "reasoning": {
                "provider": "openai",
                "model_id": "gpt-4o",
                "fallbacks": [
                    {"provider": "gemini", "model_id": "gemini-2.5-pro"},
                    {"provider": "claude", "model_id": "claude-3-5-sonnet-20241022"},
                    {"provider": "ollama", "model_id": "mistral:latest"}
                ]
            },
            "image": {
                "provider": "gemini",
                "model_id": "gemini-2.5-flash",
                "fallbacks": [
                    {"provider": "openai", "model_id": "gpt-4o"},
                    {"provider": "claude", "model_id": "claude-3-5-sonnet-20241022"}
                ]
            }
        }

    def classify_task_type(self, prompt_text: str, has_images: bool = False, task_hint: Optional[str] = None) -> str:
        """Inspect prompt or task hints to classify into chat, coding, reasoning, or image."""
        if has_images:
            return "image"

        hint = (task_hint or "").lower()
        if "code" in hint or "debug" in hint or "review" in hint or "function" in hint:
            return "coding"
        if "reason" in hint or "plan" in hint or "architecture" in hint or "decompose" in hint or "analyze" in hint:
            return "reasoning"
        if "chat" in hint or "viva" in hint or "conversation" in hint:
            return "chat"

        # Heuristic keywords in prompt
        text_lower = prompt_text.lower()
        if any(kw in text_lower for kw in ["def ", "class ", "import ", "function", "return ", "traceback", "syntax error", "bug"]):
            return "coding"
        if any(kw in text_lower for kw in ["step-by-step", "architect", "evaluate", "compare", "proof", "implication"]):
            return "reasoning"

        return "chat"

    def route(
        self,
        prompt_text: str,
        has_images: bool = False,
        task_hint: Optional[str] = None,
        force_local: bool = False
    ) -> RoutingDecision:
        """
        Determine provider and model. Forces local Ollama if `force_local` is true or if
        spend exceeds budget limit.
        """
        task_type = self.classify_task_type(prompt_text, has_images, task_hint)
        route_spec = self.default_routes.get(task_type, self.default_routes["chat"])

        # Check if local fallback forced
        if force_local or not self.allow_cloud or self.current_spent_cents >= self.budget_limit_cents:
            reason = f"Routed to local Ollama (Task: {task_type}, ForceLocal={force_local}, BudgetLimitReached={self.current_spent_cents >= self.budget_limit_cents})"
            return RoutingDecision(
                provider="ollama",
                model_id="mistral:latest" if task_type != "coding" else "codellama:latest",
                fallback_chain=[],
                reasoning=reason
            )

        reason = f"Dynamic route selected for task type '{task_type}' within budget."
        return RoutingDecision(
            provider=route_spec["provider"],
            model_id=route_spec["model_id"],
            fallback_chain=list(route_spec["fallbacks"]),
            reasoning=reason
        )

    def record_cost(self, cost_cents: float):
        """Update running expenditure."""
        self.current_spent_cents += max(0.0, float(cost_cents))
