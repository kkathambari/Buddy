import json
import re
from typing import List
from backend.repositories.memory import store_long_term_memory

def extract_facts(chat_input: str, user_uid: str) -> None:
    """Extracts general useful facts about the user from dialogue and stores them in long-term memory."""
    prompt = f"""
You are a memory extraction assistant. Analyze the user's chat input and determine if it contains any useful long-term facts worth remembering.
Useful facts include:
- Preferences (e.g., "I prefer Python examples", "I like concise explanations")
- Ongoing context (e.g., "I'm working on Buddy", "I'm learning DSA")
- General likes/dislikes
- Personal context

User Chat Input:
"{chat_input}"

Response format: Return ONLY a valid JSON object matching the schema below. If no useful long-term facts are found, return an empty list for "facts".

JSON Schema:
{{
  "facts": ["string", "string"]
}}
"""
    try:
        from ai.gateway.broker import AIGateway
        from core.logging import setup_logger
        logger = setup_logger("facts_extractor")
        
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
            if updates and "facts" in updates:
                for fact in updates["facts"]:
                    store_long_term_memory(user_uid, fact)
                    logger.info(f"Extracted useful fact: {fact}")
    except Exception as e:
        pass
