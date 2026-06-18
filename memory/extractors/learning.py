import json
import re
from typing import Any, Dict
from shared.storage import safe_load, safe_save

LEARNING_FILE = "data/learning_progress.json"

def extract_learning(chat_input: str) -> Dict[str, Any]:
    """Extracts study topics, confidence levels, and progress from conversation dialogue."""
    progress = safe_load(LEARNING_FILE, {})
    
    prompt = f"""
Analyze the user's chat input and determine if they are learning or studying a programming topic.
Current Progress:
{json.dumps(progress, indent=2)}

User Chat Input:
"{chat_input}"

Identify:
- topic (e.g. FastAPI, Algorithms, CNN, React)
- status (e.g. started, reviewing, completed)
- confidence (e.g. low, medium, high)
- mastery_increment (integer between 0 and 50 representing estimated progress increase, if any)

Response format: Return ONLY a valid JSON object matching the schema below. If no learning topic is mentioned, return an empty object {{}}.

JSON Schema:
{{
  "topic": "string",
  "status": "string",
  "confidence": "string",
  "mastery_increment": integer
}}
"""
    try:
        from ai.gateway.broker import AIGateway
        from core.logging import setup_logger
        logger = setup_logger("learning_extractor")
        
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
            if updates and "topic" in updates:
                topic = updates["topic"]
                status = updates.get("status", "started")
                confidence = updates.get("confidence", "low")
                inc = updates.get("mastery_increment", 10)
                
                # Update progress database
                prev_val = progress.get(topic, 0)
                new_val = min(100, prev_val + inc)
                progress[topic] = new_val
                safe_save(LEARNING_FILE, progress)
                logger.info(f"Updated study progress for {topic}: {new_val}% mastery (status: {status})")
                
                # Log timeline events
                from timeline.history import log_timeline_event
                if prev_val == 0:
                    log_timeline_event(
                        title=f"Started learning {topic}",
                        source="document_pdf", # Triggers timeline milestone
                        metadata={"concept": topic, "confidence": confidence}
                    )
                else:
                    log_timeline_event(
                        title=f"Viva review completed for {topic}",
                        source="conversation", # Triggers timeline milestone
                        metadata={"concept": topic, "mastery": new_val, "confidence": confidence}
                    )
                return updates
    except Exception as e:
        pass
    return {}
