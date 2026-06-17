def analyze_tone(text):
    text_lower = text.lower()

    tone = {
        "emotion": "neutral",
        "intensity": "low",
        "hidden": False
    }

    # emotion detection
    if any(w in text_lower for w in ["sad", "tired", "hurt", "cry"]):
        tone["emotion"] = "sad"
    elif any(w in text_lower for w in ["happy", "excited", "love"]):
        tone["emotion"] = "happy"
    elif any(w in text_lower for w in ["angry", "frustrated"]):
        tone["emotion"] = "angry"

    # intensity detection
    if "!" in text:
        tone["intensity"] = "high"
    elif "..." in text:
        tone["intensity"] = "low"

    # hidden emotion (VERY important)
    if text_lower in ["i'm fine", "im fine", "fine"]:
        tone["emotion"] = "sad"
        tone["hidden"] = True

    return tone
