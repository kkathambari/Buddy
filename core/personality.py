def respond(stats):
    if stats.get("snark", 0) > 70:
        return "Oh wow… another bug. Incredible 🙄"
    elif stats.get("wisdom", 0) > 70:
        return "Think deeper. You're missing something subtle."
    elif stats.get("chaos", 0) > 70:
        return "DELETE THE CODE 😈"
    elif stats.get("patience", 0) > 70:
        return "You're doing okay. Keep going 💙"
    else:
        return "Continue."
