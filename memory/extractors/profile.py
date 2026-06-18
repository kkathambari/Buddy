import json
import re
from typing import Any, Dict
from shared.storage import safe_load, safe_save

def extract_profile(chat_input: str) -> Dict[str, Any]:
    """Extracts user profile details from conversation dialogue and updates profile memory."""
    try:
        from memory.user_profile import load_profile, save_profile
    except ImportError:
        return {}
        
    profile = load_profile()
    
    prompt = f"""
You are an extraction assistant. Analyze the user's chat input and determine if it reveals new information about their profile.
Current Profile:
{json.dumps(profile, indent=2)}

User Chat Input:
"{chat_input}"

Identify if the user mentions any of:
- Name
- Timezone (e.g. EST, PST, IST, GMT+5:30)
- Whether they are a developer (true/false)
- Whether they are a student (true/false)
- Favorite programming language
- College / University name
- Goals or what they are building

Response format: Return ONLY a valid JSON object matching the schema below, containing ONLY the fields that have been explicitly mentioned or updated. Do not include any markdown format tags or explanation. If no new fields or goals are found, return an empty object {{}}.

JSON Schema:
{{
  "name": "string",
  "timezone": "string",
  "is_developer": boolean,
  "is_student": boolean,
  "favorite_language": "string",
  "college": "string",
  "goals": ["string"]
}}
"""
    try:
        from ai.gateway.broker import AIGateway
        from core.logging import setup_logger
        logger = setup_logger("profile_extractor")
        
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
                updated = False
                for k, v in updates.items():
                    if k in profile:
                        if k == "goals":
                            current_goals = set(profile[k])
                            for goal in v:
                                if goal.strip():
                                    current_goals.add(goal.strip())
                            if len(current_goals) > len(profile[k]):
                                profile[k] = list(current_goals)
                                updated = True
                        elif profile[k] != v:
                            profile[k] = v
                            updated = True
                if updated:
                    logger.info(f"Automatically updated profile from conversation: {updates}")
                    save_profile(profile)
                    
                    # Log event to timeline
                    from timeline.history import log_timeline_event
                    log_timeline_event(
                        title=f"User Profile Updated: {', '.join(updates.keys())}",
                        source="structured_profile",
                        metadata=updates
                    )
                return updates
    except Exception as e:
        pass
    return {}
