import json
import os
import threading
from typing import Any, Dict, List

def get_profile_file() -> str:
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and app.user_data_dir:
            return os.path.join(app.user_data_dir, "user_profile.json")
    except Exception:
        pass
    return "data/user_profile.json"

def load_profile() -> Dict[str, Any]:
    file_path = get_profile_file()
    default_profile = {
        "name": "Developer",
        "timezone": "UTC",
        "is_developer": False,
        "is_student": False,
        "favorite_language": "None",
        "college": "None",
        "goals": []
    }
    if not os.path.exists(file_path):
        return default_profile
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for k, v in default_profile.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return default_profile

def save_profile(profile: Dict[str, Any]) -> None:
    file_path = get_profile_file()
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4)
    except Exception as e:
        print(f"Error saving profile: {e}")

def update_profile_field(field: str, value: Any) -> None:
    profile = load_profile()
    if field in profile:
        profile[field] = value
        save_profile(profile)

def _extract_profile_job(chat_input: str) -> None:
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
        logger = setup_logger("user_profile")
        
        response = AIGateway.generate_response(prompt).strip()
        
        # Clean response from code block wrappers if LLM includes them
        if response.startswith("```"):
            # Strip first line and trailing ```
            lines = response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            response = "\n".join(lines).strip()
            
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            updates = json.loads(json_match.group(0))
            if updates:
                updated = False
                for k, v in updates.items():
                    if k in profile:
                        if k == "goals":
                            # Merge goal lists
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
                    logger.info(f"Updated user profile from chat: {updates}")
                    save_profile(profile)
    except Exception as e:
        # Fail silently in background
        pass

def extract_profile_async(chat_input: str) -> None:
    """Asynchronously extracts user profile insights from chat dialogue."""
    threading.Thread(target=_extract_profile_job, args=(chat_input,), daemon=True).start()
