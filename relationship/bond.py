def get_attachment_style(bond: int) -> str:
    """Returns the attachment style based on bond points."""
    if bond < 10:
        return "neutral"
    elif bond < 40:
        return "warm"
    else:
        return "attached"

def get_relationship_level(bond: int) -> str:
    """Returns relationship status name based on bond level."""
    if bond < 10:
        return "stranger"
    elif bond < 30:
        return "familiar"
    elif bond < 60:
        return "friend"
    else:
        return "close"

def calculate_bond_increment(is_positive: bool, multiplier: float = 1.0) -> int:
    """Calculates bond points change based on interaction valence and multiplier."""
    base = 2 if is_positive else -1
    return int(base * multiplier)
