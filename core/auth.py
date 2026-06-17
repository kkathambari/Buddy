import random
import hashlib

ADJECTIVES = [
    "crimson", "azure", "obsidian", "spectral", "silent", 
    "echoing", "shadowy", "luminescent", "void", "hollow",
    "phantom", "astral", "abyssal", "shimmering", "ethereal"
]

NOUN = [
    "phantom", "echo", "shadow", "spark", "soul", 
    "ghost", "wraith", "whisper", "daemon", "specter",
    "nexus", "shard", "vortex", "dream", "byte"
]

NUMBERS = [str(i) for i in range(10, 999)]

def generate_soul_seed():
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUN)
    num = random.choice(NUMBERS)
    return f"{adj}-{noun}-{num}"

def hash_seed(seed):
    if not seed:
        return "default_pet"
    hasher = hashlib.sha256()
    salt = "pet-ghost-soul-salt"
    hasher.update((seed + salt).encode('utf-8'))
    return hasher.hexdigest()
