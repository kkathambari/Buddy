from core.logging import setup_logger

logger = setup_logger("model_router")

class ModelRouter:
    """
    Model Router.
    Routes prompts to either local models (Ollama) or cloud APIs (Gemini/Vertex)
    depending on cost bounds, complexity parameters, and connection status.
    """
    def __init__(self, cost_limit_cents: float = 100.0):
        self.cost_limit_cents = cost_limit_cents
        self.current_spend_cents = 0.0
        self.offline_mode = False

    def route_request(self, complexity: str, target_budget_cents: float = 0.5) -> str:
        """Determines model route destination. Returns 'local_ollama' or 'cloud_gemini'."""
        if self.offline_mode:
            logger.info("Router in offline mode. Routing to local_ollama.")
            return "local_ollama"

        if self.current_spend_cents >= self.cost_limit_cents:
            logger.warning(f"Cost limit of {self.cost_limit_cents} cents exceeded. Routing request to local_ollama.")
            return "local_ollama"
            
        if target_budget_cents < 0.1:
            logger.info("Low budget threshold specified. Routing to local_ollama.")
            return "local_ollama"

        complexity_lower = complexity.lower()
        if complexity_lower == "low":
            logger.info("Task complexity is low. Routing to local_ollama.")
            return "local_ollama"
            
        logger.info(f"Routing request to cloud_gemini (complexity: {complexity}, budget: {target_budget_cents}c).")
        return "cloud_gemini"

    def record_spend(self, amount_cents: float) -> None:
        """Accumulates total api consumption spend."""
        self.current_spend_cents += amount_cents
        logger.info(f"Recorded model spend: {amount_cents} cents. Cumulative spend: {self.current_spend_cents} cents.")
        
    def reset_spend(self) -> None:
        """Resets spending back to zero."""
        self.current_spend_cents = 0.0
        logger.info("Model spend tracking reset.")
