from core.activity import get_idle_time
from core.config import get_config

def update_energy(soul):
    config = get_config()
    idle = get_idle_time()

    if idle < config["idle_threshold"]:
        soul["energy"] += config["gain_rate"]
    else:
        soul["energy"] -= config["decay_rate"]

    soul["energy"] = max(0, min(100, soul["energy"]))

    if soul["energy"] == 0:
        soul["alive"] = False

    return soul
