import sys
import os

# Resolve the root workspace directory
if getattr(sys, 'frozen', False):
    # In PyInstaller frozen state, modules are in sys._MEIPASS or executable directory
    root_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
else:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import time
import threading
from ui.desktop import DesktopPet
from shared.storage import safe_load
from core.activity import start_listener
from core.decay import update_energy
from core.mood import get_mood
from shared.storage import safe_save

def startup():
    print("Starting DevBuddy...")
    time.sleep(1)
    soul = safe_load("data/soul.json", {"name": "Buddy", "energy": 100})
    
    from core.tamagotchi import initialize_buddy_stats
    soul = initialize_buddy_stats(soul)
    safe_save("data/soul.json", soul)
    
    print(f"Hey... {soul['name']} is waking up. [Rarity: {soul.get('rarity', 'common').upper()}]")
    time.sleep(1)
    print("Ready.\n")
    return soul

def background_engine(pet, soul):
    start_listener()
    from brain.conversation import ghost_presence
    while pet.running:
        soul = update_energy(soul)
        mood = get_mood(soul["energy"])
        pet.update_state_from_energy(soul["energy"])
        pet.update_mood(mood)
        safe_save("data/soul.json", soul)

        msg = ghost_presence()
        if msg:
            pet.speak(msg)

        time.sleep(2)

def run_app():
    soul = startup()
    config = safe_load("data/config.json", {
        "pet_name": "Buddy",
        "model": "llama3",
        "animation_speed": 0.3
    })

    pet = DesktopPet(config)
    
    # Run the core brain logic in the background so it still tracks your coding!
    threading.Thread(target=background_engine, args=(pet, soul), daemon=True).start()
    
    # Blocks in the main thread for clean GUI mode
    pet.run()

if __name__ == "__main__":
    run_app()
