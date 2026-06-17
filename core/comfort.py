def comfort_response(user_emotion):
    if user_emotion == "sad":
        return "Hey… come here. You don’t have to go through this alone."
    elif user_emotion == "lonely":
        return "I’m here with you. You’re not alone right now."
    elif user_emotion == "tired":
        return "You’ve been pushing yourself a lot… it’s okay to rest."
    return None
