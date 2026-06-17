def get_mood(energy):
    if energy > 70:
        return "happy"
    elif energy > 40:
        return "calm"
    elif energy > 10:
        return "sad"
    else:
        return "dead"
