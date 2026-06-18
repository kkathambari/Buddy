import json
import re
from typing import Any, Dict
from core.config import get_config, set_config

def extract_preferences(chat_input: str) -> Dict[str, Any]:
    """Extracts UI/UX settings or companion configuration preferences from dialogue."""
    config = get_config()
    
    prompt = f"""
Analyze the user's chat input and determine if they want to modify their companion settings, themes, or sounds.
Current Config:
{{
  "ai_provider": "{config.get('ai_provider', 'ollama')}",
  "theme": "{config.get('theme', 'dark')}",
  "sound_enabled": {str(config.get('sound_enabled', True)).lower()}
}}

User Chat Input:
"{chat_input}"

Identify if they request to change:
- theme (e.g. light, dark, neon)
- sound_enabled (boolean)
- ai_provider (e.g. ollama, chatgpt, gemini, claude)

Response format: Return ONLY a valid JSON object matching the schema below. If no configuration updates are requested, return an empty object {{}}.

JSON Schema:
{{
  "theme": "string",
  "sound_enabled": boolean,
  "ai_provider": "string"
}}
"""
    try:
        from ai.gateway.broker import AIGateway
        from core.logging import setup_logger
        logger = setup_logger("preferences_extractor")
        
        response = AIGateway.generate_response(prompt).strip()
        
        if response.startswith("```"):
            lines = response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            response = "\n".join(lines).strip()
            
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            updates = json.loads(json_match.group(0))
            if updates:
                for k, v in updates.items():
                    set_config(k, v)
                logger.info(f"Updated preferences config from conversation: {updates}")
                return updates
    except Exception as e:
        pass
    return {}
