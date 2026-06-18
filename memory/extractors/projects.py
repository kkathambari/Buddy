import json
import re
from typing import Any, Dict
from shared.storage import safe_load, safe_save

PROJECTS_DATA_FILE = "data/projects_list.json"

def extract_projects(chat_input: str) -> Dict[str, Any]:
    """Extracts completed coding projects and development session completions from dialogue."""
    projects = safe_load(PROJECTS_DATA_FILE, [])
    
    prompt = f"""
Analyze the user's chat input and determine if they have finished or started a coding project.
Current Projects:
{json.dumps(projects, indent=2)}

User Chat Input:
"{chat_input}"

Identify:
- project_name (e.g. Forge AI, DevBuddy, Calculator)
- status (e.g. started, active, completed)
- description (brief summary)

Response format: Return ONLY a valid JSON object matching the schema below. If no coding project is discussed, return an empty object {{}}.

JSON Schema:
{{
  "project_name": "string",
  "status": "string",
  "description": "string"
}}
"""
    try:
        from ai.gateway.broker import AIGateway
        from core.logging import setup_logger
        logger = setup_logger("projects_extractor")
        
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
            if updates and "project_name" in updates:
                project_name = updates["project_name"]
                status = updates.get("status", "started")
                desc = updates.get("description", "")
                
                # Check for existing project to update
                found = False
                for proj in projects:
                    if proj["project_name"].lower() == project_name.lower():
                        proj["status"] = status
                        if desc:
                            proj["description"] = desc
                        found = True
                        break
                        
                if not found:
                    projects.append({
                        "project_name": project_name,
                        "status": status,
                        "description": desc
                    })
                    
                safe_save(PROJECTS_DATA_FILE, projects)
                logger.info(f"Logged project update in database: {project_name} (status: {status})")
                
                # Log timeline event
                from timeline.history import log_timeline_event
                log_timeline_event(
                    title=f"Completed coding session for project: {project_name}",
                    source="project_session", # Triggers timeline milestone
                    metadata={"project": project_name, "status": status}
                )
                return updates
    except Exception as e:
        pass
    return {}
