import random

RARITY_WEIGHTS = {
    'common': 60,
    'uncommon': 25,
    'rare': 10,
    'epic': 4,
    'legendary': 1
}

RARITY_FLOOR = {
    'common': 5,
    'uncommon': 15,
    'rare': 25,
    'epic': 35,
    'legendary': 50
}

STAT_NAMES = ['DEBUGGING', 'PATIENCE', 'CHAOS', 'WISDOM', 'SNARK']

def roll_rarity():
    roll = random.randint(1, 100)
    if roll <= 60: return 'common'
    elif roll <= 85: return 'uncommon'
    elif roll <= 95: return 'rare'
    elif roll <= 99: return 'epic'
    else: return 'legendary'

def roll_stats(rarity):
    floor = RARITY_FLOOR[rarity]
    peak = random.choice(STAT_NAMES)
    dump = random.choice([s for s in STAT_NAMES if s != peak])

    stats = {}
    for name in STAT_NAMES:
        if name == peak:
            stats[name] = min(100, floor + 50 + random.randint(0, 30))
        elif name == dump:
            stats[name] = max(1, floor - 10 + random.randint(0, 15))
        else:
            stats[name] = floor + random.randint(0, 40)
    return stats

def initialize_buddy_stats(soul):
    if "stats" not in soul or "rarity" not in soul:
        rarity = roll_rarity()
        stats = roll_stats(rarity)
        soul["rarity"] = rarity
        soul["stats"] = stats
        print(f"[*] Rolled new Tamagotchi Stats! Rarity: {rarity.upper()}")
        print(f"[*] Stats: {stats}")
    return soul
