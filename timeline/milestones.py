from shared.storage import safe_load, safe_save
from events.bus import global_bus, Event

MILESTONES_FILE = "data/unlocked_milestones.json"

def load_unlocked_milestones() -> list:
    return safe_load(MILESTONES_FILE, [])

def save_unlocked_milestones(milestones: list) -> None:
    safe_save(MILESTONES_FILE, milestones)

def unlock_milestone(name: str, xp_reward: int) -> None:
    unlocked = load_unlocked_milestones()
    if name in unlocked:
        return
        
    unlocked.append(name)
    save_unlocked_milestones(unlocked)
    
    # Award Companion XP in data/soul.json
    try:
        soul = safe_load("data/soul.json", {})
        soul["experience"] = soul.get("experience", 0) + xp_reward
        safe_save("data/soul.json", soul)
        
        # Publish event bus alert
        event = Event("milestone_unlocked", "timeline_engine", {
            "milestone": name,
            "xp_reward": xp_reward,
            "new_xp": soul["experience"]
        })
        global_bus.publish(event)
    except Exception:
        pass

def evaluate_timeline_milestones(event: dict) -> None:
    title = event.get("title", "").lower()
    source = event.get("source", "")
    metadata = event.get("metadata", {})
    
    # 1. Started learning topics
    if source == "document_pdf" or "started learning" in title:
        concept = metadata.get("concept", "New Topic")
        unlock_milestone(f"Started learning {concept}", 10)
        
    # 2. Completed Viva or mock review
    if "finished viva" in title or "viva review completed" in title or "viva" in title:
        unlock_milestone("Completed first Viva oral exam", 25)
        
    # 3. Finished project coding sessions
    if source == "project_session" and "completed" in title:
        unlock_milestone("Finished project development session", 15)
        
    # 4. ATS screening milestone
    if "ats score" in title or "resume" in title:
        unlock_milestone("Completed first resume ATS match scan", 20)
