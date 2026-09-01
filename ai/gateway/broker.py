from core.exceptions import GatewayException
from core.logging import setup_logger
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
        try:
            return AIGateway._call_openai(prompt, max_tokens=kwargs.get("max_tokens", 300))
        except GatewayException:
            raise
        except Exception as e:
            logger.error(f"Upstream provider failed after retries: {e}")
            raise GatewayException(f"AI Provider unavailable: {str(e)}")

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _call_openai(prompt: str, max_tokens: int = 300) -> str:
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise GatewayException("OPENAI_API_KEY is not configured.")
                
            client = openai.OpenAI(api_key=api_key, timeout=15.0)
            response = client.chat.completions.create(
                model=os.getenv("BUDDY_OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise GatewayException("openai is not installed.")
        except openai.APIConnectionError as e:
            logger.warning(f"ChatGPT connection error, retrying: {e}")
            raise
        except openai.RateLimitError as e:
            logger.warning(f"ChatGPT rate limit hit, retrying: {e}")
            raise
        except Exception as e:
            logger.error(f"ChatGPT call failed: {e}", exc_info=True)
            raise GatewayException(f"OpenAI connection issue: {e}")

    @staticmethod
    def stream_response(prompt: str, **kwargs):
        import openai
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            yield "[Error: OPENAI_API_KEY is not configured]"
            return
            
        client = openai.OpenAI(api_key=api_key, timeout=15.0)
        try:
            response = client.chat.completions.create(
                model=os.getenv("BUDDY_OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 300),
                temperature=0.7,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"ChatGPT stream failed: {e}", exc_info=True)
            yield f"\n[Connection error: {str(e)}]"
