from core.config import set_config, get_config
from core.personality import respond
from ui.ascii import render

def show_pet(bones, soul):
    print("\n------ DEV BUDDY ------")
    print(f"Name: {soul['name']}")
    print(f"Species: {bones['species']}")
    print(f"Rarity: {bones['rarity']}")
    print(f"Energy: {round(soul['energy'],2)}")
    print(render(soul["energy"], soul["alive"]))

def pet_action(stats):
    print("❤️ Your buddy is happy!")
    print(respond(stats))

def config_menu():
    print("\n--- CONFIG ---")
    cfg = get_config()
    print(cfg)

    key = input("Enter key to change (or enter to exit): ")
    if key:
        val = float(input("Enter value: "))
        set_config(key, val)
        print("Updated.")
