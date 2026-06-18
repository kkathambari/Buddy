from datetime import datetime
import time
import threading
import collections

last_interaction = datetime.now()
session_data = {
    "category": "idle",
    "start_time": datetime.now(),
    "has_warned": False
}

key_history = collections.deque()
last_struggle_time = 0.0
STRUGGLE_COOLDOWN_SEC = 300.0 # 5 minutes cooldown

def register_interaction():
    global last_interaction
    last_interaction = datetime.now()

def get_active_window_title():
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value.lower()
    except Exception:
        return ""

def categorize_window(title):
    if not title: return "idle"
    if "code" in title or "pycharm" in title or "intellij" in title or "vim" in title:
        return "coding"
    if "chrome" in title or "edge" in title or "firefox" in title or "brave" in title:
        if "youtube" in title or "netflix" in title:
            return "watching"
        return "browsing"
    if "discord" in title or "slack" in title or "teams" in title:
        return "chatting"
    return "other"

def monitor_screen_context():
    global session_data
    while True:
        title = get_active_window_title()
        cat = categorize_window(title)
        
        if cat != session_data["category"]:
            from memory.projects import log_session
            end_time = datetime.now()
            log_session(session_data["category"], session_data["start_time"], end_time)
            
            # Publish category changed event
            try:
                from events.bus import global_bus, Event
                event = Event("active_category_changed", {
                    "old_category": session_data["category"],
                    "new_category": cat,
                    "title": title
                })
                global_bus.publish(event)
            except Exception:
                pass
            
            session_data["category"] = cat
            session_data["start_time"] = end_time
            session_data["has_warned"] = False
            
        time.sleep(5)

def get_contextual_observation():
    """
    Returns an intelligent observation based on how long they've been doing an activity.
    """
    global session_data
    duration_mins = (datetime.now() - session_data["start_time"]).total_seconds() / 60.0
    
    if session_data["category"] == "coding" and duration_mins > 1.0 and not session_data["has_warned"]:
        session_data["has_warned"] = True
        return "You've been staring at code for a while. Don't forget to blink."
        
    if session_data["category"] == "watching" and duration_mins > 2.0 and not session_data["has_warned"]:
        session_data["has_warned"] = True
        return "Getting distracted, are we?"
        
    return None

def check_struggle(key):
    global key_history, last_struggle_time
    now = time.time()
    
    is_delete = False
    try:
        from pynput.keyboard import Key
        if key == Key.backspace or key == Key.delete:
            is_delete = True
    except Exception:
        pass
        
    if not is_delete:
        if hasattr(key, 'name') and key.name in ['backspace', 'delete']:
            is_delete = True
            
    key_history.append((now, is_delete))
    
    cutoff = now - 45.0
    while key_history and key_history[0][0] < cutoff:
        key_history.popleft()
        
    if len(key_history) >= 20:
        deletes = sum(1 for _, is_del in key_history if is_del)
        delete_ratio = deletes / len(key_history)
        
        if delete_ratio > 0.40 and (now - last_struggle_time) > STRUGGLE_COOLDOWN_SEC:
            last_struggle_time = now
            try:
                from events.bus import global_bus, Event
                event = Event("user_struggling", {
                    "delete_ratio": delete_ratio,
                    "total_keys": len(key_history)
                })
                global_bus.publish(event)
            except Exception:
                pass

def on_press(key):
    register_interaction()
    check_struggle(key)

def start_listener():
    try:
        from pynput import keyboard
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    except Exception as e:
        print(f"Global keyboard listener not started (normal on Android): {e}")
    
    # Check if Android to skip background window listener
    is_android = False
    try:
        from kivy.utils import platform
        if platform == 'android':
            is_android = True
    except ImportError:
        pass

    if not is_android:
        threading.Thread(target=monitor_screen_context, daemon=True).start()

def get_idle_time():
    global last_interaction
    return (datetime.now() - last_interaction).total_seconds()
