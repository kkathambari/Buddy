from core.config import get_config
from core.exceptions import GatewayException
from core.logging import setup_logger
import subprocess
import sys

from ai.gateway.router import ModelRouter

logger = setup_logger("ai_gateway")
global_model_router = ModelRouter()

class AIGateway:
    """
    AI Gateway Broker.
    Centralizes calls to LLM providers (Ollama, ChatGPT, Claude, Gemini).
    """
    @staticmethod
    def generate_response(prompt: str, **kwargs) -> str:
        """
        Sends the prompt to the configured LLM provider and returns the raw string response.
        Raises GatewayException on failures.
        """
        complexity = kwargs.get("complexity", "high")
        budget = kwargs.get("budget", 0.5)
        
        # Consult ModelRouter to determine route
        route = global_model_router.route_request(complexity, budget)
        logger.info(f"ModelRouter selected route: '{route}'")
        
        config = get_config()
        
        if route == "cloud_gemini":
            try:
                res = AIGateway._call_gemini(prompt, config)
                global_model_router.record_spend(0.2) # 0.2 cents per call
                return res
            except Exception as e:
                logger.warning(f"Cloud execution failed: {e}. Falling back to local_ollama.")
                return AIGateway._call_ollama(prompt, config)
        else:
            return AIGateway._call_ollama(prompt, config)

    @staticmethod
    def _call_chatgpt(prompt: str, config: dict) -> str:
        try:
            import openai
            api_key = config.get("chatgpt_api_key", "")
            if not api_key:
                raise GatewayException("ChatGPT API key is missing in configuration.")
                
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=config.get("chatgpt_model", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise GatewayException("openai library is not installed. Please run `pip install openai`.")
        except Exception as e:
            logger.error(f"ChatGPT call failed: {e}", exc_info=True)
            raise GatewayException(f"ChatGPT connection issue: {e}")

    @staticmethod
    def _call_claude(prompt: str, config: dict) -> str:
        try:
            import anthropic
            api_key = config.get("claude_api_key", "")
            if not api_key:
                raise GatewayException("Claude API key is missing in configuration.")
                
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=config.get("claude_model", "claude-3-haiku-20240307"),
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except ImportError:
            raise GatewayException("anthropic library is not installed. Please run `pip install anthropic`.")
        except Exception as e:
            logger.error(f"Claude call failed: {e}", exc_info=True)
            raise GatewayException(f"Claude connection issue: {e}")

    @staticmethod
    def _call_gemini(prompt: str, config: dict) -> str:
        try:
            import google.generativeai as genai
            api_key = config.get("gemini_api_key", "")
            if not api_key:
                raise GatewayException("Gemini API key is missing in configuration.")
                
            genai.configure(api_key=api_key)
            model_name = config.get("gemini_model", "gemini-pro")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except ImportError:
            raise GatewayException("google-generativeai library is not installed. Please run `pip install google-generativeai`.")
        except Exception as e:
            logger.error(f"Gemini call failed: {e}", exc_info=True)
            raise GatewayException(f"Gemini connection issue: {e}")

    @staticmethod
    def _call_ollama(prompt: str, config: dict) -> str:
        model = config.get("model", "llama3")
        
        # Check if code, bug or error is in prompt to dynamically switch to coding model
        text_lower = prompt.lower()
        if "code" in text_lower or "bug" in text_lower or "error" in text_lower:
            model = "deepseek-coder"
        elif "explain" in text_lower or "why" in text_lower:
            model = "mistral"
            
        logger.info(f"Ollama running model: '{model}'")
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            result = subprocess.run(
                ["ollama", "run", model],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=60,
                encoding="utf-8",
                startupinfo=startupinfo
            )
            if result.returncode != 0:
                raise GatewayException(f"Ollama process returned exit code {result.returncode}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise GatewayException("Ollama model execution timed out after 60 seconds.")
        except Exception as e:
            logger.error(f"Ollama invocation failed: {e}", exc_info=True)
            raise GatewayException(f"Ollama execution issue: {e}")
