import time
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def animate(state):
    frames = {
        "happy": ["(•‿•)", "(•◡•)", "(•‿•)"],
        "idle": ["(•_•)", "(•.•)", "(•_•)"],
        "weak": ["(×_×)", "(x_x)", "(×_×)"],
        "dead": ["💀", "💀", "💀"]
    }

    for f in frames[state]:
        clear()
        print(f"\n   {f}\n")
        time.sleep(0.4)

def render(energy, alive):
    if not alive:
        animate("dead")
        return "💀 DEAD"

    if energy > 70:
        animate("happy")
        return "HAPPY"
    elif energy > 40:
        animate("idle")
        return "OKAY"
    elif energy > 10:
        animate("weak")
        return "WEAK"
    else:
        animate("dead")
        return "CRITICAL"
