import sys
import os

# Resolve the root workspace directory
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import time
from shared.storage import safe_load, safe_save
from core.tamagotchi import initialize_buddy_stats

def startup():
    print("Starting Android DevBuddy...")
    soul = safe_load("data/soul.json", {"name": "Buddy", "energy": 100})
    soul = initialize_buddy_stats(soul)
    safe_save("data/soul.json", soul)
    return soul

if __name__ == "__main__":
    soul = startup()
    from ui.kivy_app import AndroidPetApp
    AndroidPetApp().run()
