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

from shared.storage import safe_load, safe_save

def migrate_and_merge_data(root_path):
    desktop_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    root_data_dir = os.path.join(root_path, "data")
    
    if os.path.abspath(desktop_data_dir) == os.path.abspath(root_data_dir):
        return
        
    if not os.path.exists(desktop_data_dir):
        return
        
    os.makedirs(root_data_dir, exist_ok=True)
    
    import shutil
    for file_name in os.listdir(desktop_data_dir):
        src_file = os.path.join(desktop_data_dir, file_name)
        dst_file = os.path.join(root_data_dir, file_name)
        
        if not os.path.isfile(src_file):
            continue
            
        if file_name == "config.json":
            local_config = safe_load(src_file, {})
            root_config = safe_load(dst_file, {})
            
            merged_config = root_config.copy()
            merged_config.update(local_config)
            
            # Strip whitespace from string values
            for k, v in merged_config.items():
                if isinstance(v, str):
                    merged_config[k] = v.strip()
                    
            safe_save(dst_file, merged_config)
        else:
            if not os.path.exists(dst_file) or os.path.getmtime(src_file) > os.path.getmtime(dst_file):
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception as e:
                    print(f"Failed to migrate file {file_name}: {e}")

# Migrate and merge configuration before changing directory
migrate_and_merge_data(root_dir)
os.chdir(root_dir)

import time
import threading
from ui.desktop import DesktopPet
from core.activity import start_listener
from core.decay import update_energy
from core.mood import get_mood

def ensure_default_data():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        mei_data = os.path.join(sys._MEIPASS, "data")
        if os.path.exists(mei_data):
            os.makedirs("data", exist_ok=True)
            for file in os.listdir(mei_data):
                src = os.path.join(mei_data, file)
                dst = os.path.join("data", file)
                if os.path.isfile(src) and not os.path.exists(dst):
                    try:
                        import shutil
                        shutil.copy2(src, dst)
                    except Exception as e:
                        print(f"Failed to copy default data file {file}: {e}")

def startup():
    print("Starting DevBuddy...")
    ensure_default_data()
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
