import requests
import threading
from core.config import get_config
from core.auth import hash_seed

def sync_to_cloud(soul_data):
    config = get_config()
    db_url = config.get("firebase_url", "")
    pet_id = config.get("pet_cloud_id", "default_pet")
    
    if not db_url:
        db_url = "https://pet-ghost-default-rtdb.asia-southeast1.firebasedatabase.app"
        
    if not db_url.endswith("/"):
        db_url += "/"
        
    hashed_id = hash_seed(pet_id)
    target_url = f"{db_url}pets/{hashed_id}.json"
    
    def _upload():
        try:
            requests.put(target_url, json=soul_data, timeout=5)
            print("Cloud save successful!")
        except Exception as e:
            print(f"Cloud save failed: {e}")
            
    threading.Thread(target=_upload, daemon=True).start()

def load_from_cloud_sync(db_url, pet_id):
    if not db_url:
        db_url = "https://pet-ghost-default-rtdb.asia-southeast1.firebasedatabase.app"
        
    if not db_url.endswith("/"):
        db_url += "/"
        
    hashed_id = hash_seed(pet_id)
    target_url = f"{db_url}pets/{hashed_id}.json"
    
    try:
        response = requests.get(target_url, timeout=5)
        if response.status_code == 200 and response.json():
            return response.json()
    except Exception as e:
        print(f"Cloud load failed: {e}")
        
    return None
