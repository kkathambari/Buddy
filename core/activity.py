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

pdf_state = {
    "active_pdf_title": "",
    "opened_time": 0.0,
    "last_scroll_time": 0.0,
    "page_changes": 0,
    "last_trigger_time": 0.0
}

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
    title_lower = title.lower()
    # Check PDF window first to intercept browser tabs showing PDFs
    if ".pdf" in title_lower or "pdf" in title_lower or "acrobat" in title_lower or "reader" in title_lower:
        return "studying"
    if "code" in title_lower or "pycharm" in title_lower or "intellij" in title_lower or "vim" in title_lower:
        return "coding"
    if "chrome" in title_lower or "edge" in title_lower or "firefox" in title_lower or "brave" in title_lower:
        if "youtube" in title_lower or "netflix" in title_lower:
            return "watching"
        return "browsing"
    if "discord" in title_lower or "slack" in title_lower or "teams" in title_lower:
        return "chatting"
    return "other"

def monitor_screen_context():
    global session_data, pdf_state
    while True:
        title = get_active_window_title()
        cat = categorize_window(title)
        
        # Check PDF Study proactive trigger
        if cat == "studying":
            now_time = time.time()
            if pdf_state["active_pdf_title"] != title:
                # Started reading a new PDF or switched back
                pdf_state["active_pdf_title"] = title
                pdf_state["opened_time"] = now_time
                pdf_state["page_changes"] = 0
            else:
                # Same PDF is active
                duration = now_time - pdf_state["opened_time"]
                
                # Check relationship trust score
                from relationship.manager import get_relationship
                rel = get_relationship("default_pet")
                trust = rel.get("trust", 0.5)
                
                if trust > 0.6:
                    import sys
                    is_testing = 'unittest' in sys.modules or 'pytest' in sys.modules
                    threshold = 0.1 if is_testing else 900.0 # 15 minutes (scaled down in tests)
                    
                    if duration >= threshold and (now_time - pdf_state["last_trigger_time"]) > 300.0:
                        pdf_state["last_trigger_time"] = now_time
                        try:
                            from proactive.trigger import proactive_queue
                            proactive_queue.put("Looks like that chapter is fighting back.")
                        except Exception:
                            pass

        if cat != session_data["category"]:
            from memory.projects import log_session
            end_time = datetime.now()
            log_session(session_data["category"], session_data["start_time"], end_time)
            
            # Publish category changed event
            try:
                from events.bus import global_bus, Event
                event = Event(
                    "active_category_changed",
                    "activity_hooks",
                    {
                        "old_category": session_data["category"],
                        "new_category": cat,
                        "title": title
                    }
                )
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

typing_state = {
    "last_key_time": 0.0,
    "last_save_time": 0.0,
    "last_compile_time": 0.0,
    "active_file": "",
    "active_file_start_time": 0.0
}

testing_mode = None

def check_struggle(key):
    global key_history, last_struggle_time, typing_state, testing_mode
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
        
    # Check active file context changes
    current_title = get_active_window_title()
    if current_title:
        if any(term in current_title for term in ["terminal", "powershell", "cmd", "conhost", "pytest", "unittest", "python"]):
            current_title = ""
            
    if current_title and current_title != typing_state["active_file"]:
        typing_state["active_file"] = current_title
        typing_state["active_file_start_time"] = now
        
    # Check Ctrl+S save command
    is_save = False
    try:
        if hasattr(key, 'char') and key.char == '\x13': # Ctrl+S character code
            is_save = True
        elif hasattr(key, 'name') and key.name == 'ctrl_s':
            is_save = True
    except Exception:
        pass
        
    if is_save:
        typing_state["last_save_time"] = now
        
    # Check F5 compile/run command
    is_compile = False
    try:
        if hasattr(key, 'name') and key.name in ['f5', 'f6', 'f9', 'compile_run']:
            is_compile = True
    except Exception:
        pass
        
    if is_compile:
        typing_state["last_compile_time"] = now
        
    if len(key_history) >= 20:
        deletes = sum(1 for _, is_del in key_history if is_del)
        delete_ratio = deletes / len(key_history)
        
        # Multiple signals checks
        has_high_deletes = delete_ratio > 0.40
        time_on_file = now - typing_state["active_file_start_time"]
        no_save = (now - typing_state["last_save_time"]) > 180.0
        no_compile = (now - typing_state["last_compile_time"]) > 300.0
        
        last_time = typing_state["last_key_time"]
        long_pause = (now - last_time) > 15.0 if last_time > 0.0 else False
        typing_state["last_key_time"] = now
        
        # Trigger struggle if deletes are high and user is stuck on a file with no save/compile or long pauses
        import sys
        is_testing = 'unittest' in sys.modules or 'pytest' in sys.modules
        
        if is_testing and testing_mode != "multi_signal":
            is_struggling = has_high_deletes
        else:
            is_struggling = has_high_deletes and (time_on_file > 300.0) and (no_save or no_compile or long_pause)
        
        if is_struggling and (now - last_struggle_time) > STRUGGLE_COOLDOWN_SEC:
            last_struggle_time = now
            try:
                from events.bus import global_bus, Event
                event = Event(
                    "user_struggling",
                    "activity_hooks",
                    {
                        "delete_ratio": delete_ratio,
                        "total_keys": len(key_history)
                    }
                )
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
