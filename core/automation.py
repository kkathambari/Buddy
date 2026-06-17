import re
import os
import webbrowser

def parse_and_execute_actions(response_text):
    """
    Scans the LLM response for automation tags, executes them on the OS,
    and removes the tags from the final text shown to the user.
    
    Supported Tags:
    [OPEN: notepad] or [OPEN: settings]
    [BROWSE: https://youtube.com]
    """
    clean_text = response_text
    
    # 1. Open Application Action
    open_matches = re.finditer(r'\[OPEN:\s*(.+?)\]', response_text, re.IGNORECASE)
    for match in open_matches:
        app_name = match.group(1).strip().lower()
        
        # Check if running on Android via jnius availability
        has_jnius = False
        try:
            from jnius import autoclass
            has_jnius = True
        except ImportError:
            pass
            
        if has_jnius:
            # Android implementation
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                
                if "map" in app_name:
                    intent = Intent(Intent.ACTION_VIEW, Uri.parse("geo:0,0?q="))
                    PythonActivity.mActivity.startActivity(intent)
                elif "setting" in app_name:
                    Settings = autoclass('android.provider.Settings')
                    intent = Intent(Settings.ACTION_SETTINGS)
                    PythonActivity.mActivity.startActivity(intent)
            except Exception as e:
                print(f"Failed to open {app_name} on Android: {e}")
        else:
            # Desktop implementation
            try:
                if "chrome" in app_name:
                    os.system("start chrome")
                elif "notepad" in app_name:
                    os.system("start notepad")
                elif "calc" in app_name:
                    os.system("start calc")
                elif "code" in app_name or "vscode" in app_name:
                    os.system("code")
                else:
                    os.system(f"start {app_name}")
            except Exception as e:
                print(f"Failed to open {app_name}: {e}")
                
        clean_text = clean_text.replace(match.group(0), "")
        
    # 2. Browse Web Action
    browse_matches = re.finditer(r'\[BROWSE:\s*(.+?)\]', response_text, re.IGNORECASE)
    for match in browse_matches:
        url = match.group(1).strip()
        if not url.startswith("http"):
            url = "https://" + url
        try:
            webbrowser.open(url)
        except Exception:
            pass
            
        clean_text = clean_text.replace(match.group(0), "")
        
    return clean_text.strip()

def get_clipboard_text(root):
    """
    Safely retrieves clipboard content using Tkinter to avoid heavy pip dependencies like pyperclip.
    """
    try:
        return root.clipboard_get()
    except Exception:
        return None
