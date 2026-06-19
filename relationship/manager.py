import os
from typing import Dict, Any
from shared.storage import safe_load, safe_save
from relationship.bond import get_attachment_style
from relationship.history import log_interaction

RELATIONSHIP_FILE = "data/relationship.json"

def load_relationship_data() -> Dict[str, Any]:
    """Loads all relationship data from the file system."""
    return safe_load(RELATIONSHIP_FILE, {})

def save_relationship_data(data: Dict[str, Any]) -> None:
    """Saves all relationship data to the file system."""
    os.makedirs(os.path.dirname(RELATIONSHIP_FILE), exist_ok=True)
    safe_save(RELATIONSHIP_FILE, data)

def get_relationship(companion_id: str = "default_pet") -> Dict[str, Any]:
    """Gets the relationship state for a given companion ID."""
    data = load_relationship_data()
    if companion_id not in data:
        data[companion_id] = {
            "trust": 0.5,
            "bond": 0,
            "respect": 0.5,
            "confidence": 0.5,
            "growth_stage": "month_1_careful",
            "attachment_style": "neutral",
            "history": []
        }
    else:
        # Backwards compatibility and default backfills
        rel = data[companion_id]
        if "respect" not in rel: rel["respect"] = 0.5
        if "confidence" not in rel: rel["confidence"] = 0.5
        if "growth_stage" not in rel:
            bond = rel.get("bond", 0)
            if bond <= 50: rel["growth_stage"] = "month_1_careful"
            elif bond <= 150: rel["growth_stage"] = "month_3_playful"
            elif bond <= 300: rel["growth_stage"] = "month_6_confident"
            else: rel["growth_stage"] = "year_1_comfortable"
    return data[companion_id]

def update_relationship(companion_id: str, trust_change: float, bond_change: int, action_desc: str = None, respect_change: float = 0.0, confidence_change: float = 0.0) -> Dict[str, Any]:
    """
    Updates the trust, bond, respect and confidence scores for a given companion ID, recalculating attachment style, growth stage and logging history.
    Emits a relationship_changed event on the Event Bus.
    """
    all_data = load_relationship_data()
    
    # Ensure initialized
    if companion_id not in all_data:
        all_data[companion_id] = {
            "trust": 0.5,
            "bond": 0,
            "respect": 0.5,
            "confidence": 0.5,
            "growth_stage": "month_1_careful",
            "attachment_style": "neutral",
            "history": []
        }
    
    rel = all_data[companion_id]
    
    # Ensure all keys are backfilled if they were missing in saved json
    if "respect" not in rel: rel["respect"] = 0.5
    if "confidence" not in rel: rel["confidence"] = 0.5
    
    # Update metrics with bounds
    rel["trust"] = max(0.0, min(1.0, rel["trust"] + trust_change))
    rel["bond"] = max(0, rel["bond"] + bond_change)
    rel["respect"] = max(0.0, min(1.0, rel["respect"] + respect_change))
    rel["confidence"] = max(0.0, min(1.0, rel["confidence"] + confidence_change))
    
    # Calculate attachment style
    rel["attachment_style"] = get_attachment_style(rel["bond"])
    
    # Calculate personality growth stage
    bond = rel["bond"]
    if bond <= 50:
        rel["growth_stage"] = "month_1_careful"
    elif bond <= 150:
        rel["growth_stage"] = "month_3_playful"
    elif bond <= 300:
        rel["growth_stage"] = "month_6_confident"
    else:
        rel["growth_stage"] = "year_1_comfortable"
        
    # Log history
    if action_desc:
        rel["history"] = log_interaction(rel["history"], action_desc, rel["trust"], rel["bond"])
        
    save_relationship_data(all_data)
    
    # Publish to Event Bus
    try:
        from events.bus import global_bus, Event
        event = Event(
            "relationship_changed",
            "relationship_manager",
            {
                "companion_id": companion_id,
                "trust": rel["trust"],
                "bond": rel["bond"],
                "respect": rel["respect"],
                "confidence": rel["confidence"],
                "growth_stage": rel["growth_stage"],
                "attachment_style": rel["attachment_style"]
            }
        )
        global_bus.publish(event)
    except Exception:
        pass
        
    return rel
