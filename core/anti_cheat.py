from core.generator import generate_bones

def validate_pet(stored_species, stored_rarity):
    species, rarity = generate_bones()

    if species != stored_species or rarity != stored_rarity:
        print("⚠ Tampering detected. Resetting to valid state.")
        return species, rarity

    return stored_species, stored_rarity
