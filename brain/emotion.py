def detect_emotion(text):
    text = text.lower()

    if any(word in text for word in ["sad", "tired", "hurt", "cry"]):
        return "sad"
    elif any(word in text for word in ["happy", "excited", "love"]):
        return "happy"
    elif any(word in text for word in ["angry", "frustrated", "annoyed"]):
        return "angry"
    elif any(word in text for word in ["lonely", "alone"]):
        return "lonely"
    else:
        return "neutral"
