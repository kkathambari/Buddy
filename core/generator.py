import hashlib
import getpass

SPECIES = [
    "Duck","Goose","Cat","Rabbit","Owl","Penguin","Turtle",
    "Snail","Dragon","Octopus","Axolotl","Ghost",
    "Robot","Blob","Cactus","Mushroom","Chonk","Capybara"
]

def generate_bones():
    user_id = getpass.getuser()

    seed = hashlib.sha256((user_id + "devbuddy_salt").encode()).hexdigest()
    num = int(seed[:8], 16)

    species = SPECIES[num % len(SPECIES)]

    roll = num % 100
    if roll < 60:
        return species, "Common"
    elif roll < 85:
        return species, "Uncommon"
    elif roll < 95:
        return species, "Rare"
    elif roll < 99:
        return species, "Epic"
    else:
        return species, "Legendary"
