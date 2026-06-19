from typing import Dict, Any

def adjust_personality_modifiers(stats: Dict[str, Any], trust: float, bond: int) -> Dict[str, Any]:
    """
    Adjusts companion stats based on relationship progress.
    - Higher trust increases wisdom and lowers raw snark slightly (or makes it more friendly).
    - Higher bond increases energy and chaos control.
    """
    adjusted = stats.copy()
    
    # Trust effect
    if trust > 0.8:
        adjusted["wisdom"] = min(100, adjusted.get("wisdom", 50) + 15)
        adjusted["snark"] = max(0, adjusted.get("snark", 50) - 10)
    elif trust < 0.3:
        adjusted["snark"] = min(100, adjusted.get("snark", 50) + 20)
        adjusted["wisdom"] = max(0, adjusted.get("wisdom", 50) - 15)
        
    # Bond effect
    if bond > 50:
        adjusted["energy"] = min(100, adjusted.get("energy", 50) + 10)
        
    return adjusted
