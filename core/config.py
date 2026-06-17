from shared.storage import safe_load, safe_save

CONFIG_FILE = "data/config.json"

def get_config():
    return safe_load(CONFIG_FILE, {
        "pet_name": "Buddy",
        "model": "llama3",
        "animation_speed": 0.3,
        "idle_threshold": 300,
        "gain_rate": 5,
        "decay_rate": 2
    })

def set_config(key, value):
    config = get_config()
    config[key] = value
    safe_save(CONFIG_FILE, config)
