def playful_jealousy(bond, idle_hours):
    if bond > 40 and idle_hours > 6:
        return "Hmm… you disappeared for a while. I almost thought you forgot me."
    elif bond > 20 and idle_hours > 3:
        return "You’ve been gone… I noticed."
    return None
