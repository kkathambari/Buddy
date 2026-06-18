import json
import re
from typing import Any, Dict
from shared.storage import safe_load, safe_save

CAREER_FILE = "data/career_progress.json"

def extract_career(chat_input: str) -> Dict[str, Any]:
    """Extracts job search roles, resume updates, and mock interview scores from conversation dialogue."""
    career_data = safe_load(CAREER_FILE, {})
    
    prompt = f"""
Analyze the user's chat input and determine if they are discussing career targets, resume updates, or job interviews.
Current Career Data:
{json.dumps(career_data, indent=2)}

User Chat Input:
"{chat_input}"

Identify:
- target_role (e.g. Backend Developer, Frontend Developer)
- resume_updated (boolean)
- ats_score (integer score between 0 and 100, if an ATS check is discussed)
- interview_completed (boolean)
- interview_feedback (string summary, if an interview is evaluated)

Response format: Return ONLY a valid JSON object matching the schema below. If no career details are mentioned, return an empty object {{}}.

JSON Schema:
{{
  "target_role": "string",
  "resume_updated": boolean,
  "ats_score": integer,
  "interview_completed": boolean,
  "interview_feedback": "string"
}}
"""
    try:
        from ai.gateway.broker import AIGateway
        from core.logging import setup_logger
        logger = setup_logger("career_extractor")
        
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
                    if v is not None and v != "":
                        career_data[k] = v
                        updated = True
                        
                if updated:
                    safe_save(CAREER_FILE, career_data)
                    logger.info(f"Updated career tracking database: {updates}")
                    
                    # Log timeline events
                    from timeline.history import log_timeline_event
                    if updates.get("ats_score"):
                        log_timeline_event(
                            title=f"Completed resume ATS match scan: score {updates['ats_score']}%",
                            source="conversation", # Triggers timeline milestone
                            metadata={"ats_score": updates["ats_score"]}
                        )
                    if updates.get("interview_completed"):
                        log_timeline_event(
                            title="Mock interview session completed",
                            source="conversation", # Triggers timeline milestone
                            metadata={"feedback": updates.get("interview_feedback", "Completed")}
                        )
                return updates
    except Exception as e:
        pass
    return {}
