from core.exceptions import GatewayException
from core.logging import setup_logger
import os

logger = setup_logger("ai_gateway")
class AIGateway:
    """
    AI Gateway Broker.
    Production gateway for the single supported provider: OpenAI.
    """
    @staticmethod
    def generate_response(prompt: str, **kwargs) -> str:
        """
        Sends the prompt to the configured LLM provider and returns the raw string response.
        Raises GatewayException on failures.
        """
        return AIGateway._call_openai(prompt, max_tokens=kwargs.get("max_tokens", 300))

    @staticmethod
    def _call_openai(prompt: str, max_tokens: int = 300) -> str:
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise GatewayException("OPENAI_API_KEY is not configured.")
                
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=os.getenv("BUDDY_OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise GatewayException("openai is not installed.")
        except Exception as e:
            logger.error(f"ChatGPT call failed: {e}", exc_info=True)
            raise GatewayException(f"OpenAI connection issue: {e}")
