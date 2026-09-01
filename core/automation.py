import re
import time
import subprocess
import webbrowser
from core.permissions import global_permission_manager

_tool_executions = []
MAX_TOOLS_PER_MIN = 10

def parse_and_execute_actions(response_text):
    """
    Removes legacy automation tags from LLM output.

    An LLM is not authorized to control the computer.  Callers may display the
    extracted action to the user and send it through the permission manager,
    but this compatibility function never launches an application or browser.
    
    Supported Tags:
    [OPEN: notepad] or [OPEN: settings]
    [BROWSE: https://youtube.com]
    """
    global _tool_executions
    
    # We match the entire tag to remove it, but capture the content
    tags_found = re.findall(r'\[(?:OPEN|BROWSE):\s*(.+?)\]', response_text, flags=re.IGNORECASE)
    
    action = None
    if tags_found:
        now = time.time()
        _tool_executions = [ts for ts in _tool_executions if now - ts < 60]
        if len(_tool_executions) >= MAX_TOOLS_PER_MIN:
            # Over the limit, we silently ignore tools by stripping them out
            pass
        else:
            _tool_executions.extend([now] * len(tags_found))
            action = tags_found[0] # Provide the first action to the frontend

    cleaned = re.sub(r'\[(?:OPEN|BROWSE):\s*.+?\]', '', response_text, flags=re.IGNORECASE).strip()
    return cleaned, action

def generate_action_token(action_raw):
    """
    Given an action like '[OPEN: notepad]', generate a permission token.
    """
    match = re.search(r'\[(OPEN|BROWSE):\s*(.+?)\]', action_raw, flags=re.IGNORECASE)
    if not match:
        return None
        
    tool_name = match.group(1).lower()
    target = match.group(2).strip()
    params = {"target": target}
    
    return global_permission_manager.request_action_confirmation(tool_name, params)

def execute_action(tool_name, params, token):
    """
    Consumes the confirmation token and executes the action safely.
    """
    if not global_permission_manager.consume_action_confirmation(token, tool_name, params):
        return {"success": False, "error": "Invalid, expired, or unapproved token."}
        
    try:
        if tool_name == "open":
            subprocess.Popen(params["target"], shell=True)
            return {"success": True, "message": f"Opened {params['target']}"}
        elif tool_name == "browse":
            webbrowser.open(params["target"])
            return {"success": True, "message": f"Browsing to {params['target']}"}
        else:
            return {"success": False, "error": "Unknown action type"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_clipboard_text(root):
    """
    Safely retrieves clipboard content using Tkinter to avoid heavy pip dependencies like pyperclip.
    """
    try:
        return root.clipboard_get()
    except Exception:
        return None
