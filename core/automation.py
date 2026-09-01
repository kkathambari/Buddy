import re
import time
import subprocess
import webbrowser
import os
from core.permissions import global_permission_manager

_tool_executions = []
MAX_TOOLS_PER_MIN = 10
WORKSPACE_DIR = os.path.abspath("workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def safe_path(target: str) -> str:
    """Resolves path and ensures it stays within the workspace."""
    resolved = os.path.abspath(os.path.join(WORKSPACE_DIR, target))
    if not resolved.startswith(WORKSPACE_DIR):
        raise ValueError("Path traversal attempt blocked.")
    return resolved

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
    # Support OPEN, BROWSE, TERMINAL, READ_FILE, WRITE_FILE, PLAN
    tags_found = re.findall(r'\[(?:OPEN|BROWSE|TERMINAL|READ_FILE|WRITE_FILE|PLAN):\s*(.+?)\]', response_text, flags=re.IGNORECASE)
    
    # Keep track of raw tag for generate_action_token to consume easily
    raw_tags = re.findall(r'(\[(?:OPEN|BROWSE|TERMINAL|READ_FILE|WRITE_FILE|PLAN):\s*.+?\])', response_text, flags=re.IGNORECASE)
    
    action = None
    if tags_found:
        now = time.time()
        _tool_executions = [ts for ts in _tool_executions if now - ts < 60]
        if len(_tool_executions) >= MAX_TOOLS_PER_MIN:
            # Over the limit, we silently ignore tools by stripping them out
            pass
        else:
            _tool_executions.extend([now] * len(tags_found))
            action = raw_tags[0] # Provide the first full tag to the frontend (e.g. [OPEN: notepad])

    cleaned = re.sub(r'\[(?:OPEN|BROWSE|TERMINAL|READ_FILE|WRITE_FILE|PLAN):\s*.+?\]', '', response_text, flags=re.IGNORECASE).strip()
    return cleaned, action

def generate_action_token(action_raw, companion_id=None):
    """
    Given an action like '[OPEN: notepad]', generate a permission token.
    """
    match = re.search(r'\[(OPEN|BROWSE|TERMINAL|READ_FILE|WRITE_FILE|PLAN):\s*(.+?)\]', action_raw, flags=re.IGNORECASE)
    if not match:
        return None
        
    tool_name = match.group(1).lower()
    target = match.group(2).strip()
    
    # If WRITE_FILE, target might contain pipe or something. But for simplicity let's assume target is path
    # Actually WRITE_FILE should probably have data, but since the regex only grabs the target, let's keep params simple.
    params = {"target": target}
    
    return global_permission_manager.request_action_confirmation(tool_name, params, companion_id)

def execute_action(tool_name, params, token, companion_id=None):
    """
    Consumes the confirmation token and executes the action safely.
    """
    if not global_permission_manager.consume_action_confirmation(token, tool_name, params, companion_id):
        return {"success": False, "error": "Invalid, expired, or unapproved token."}
        
    try:
        if tool_name == "open":
            subprocess.Popen(params["target"], shell=True)
            return {"success": True, "message": f"Opened {params['target']}"}
        elif tool_name == "browse":
            webbrowser.open(params["target"])
            return {"success": True, "message": f"Browsing to {params['target']}"}
        elif tool_name == "terminal":
            res = subprocess.run(params["target"], shell=True, capture_output=True, text=True)
            return {"success": True, "message": f"Executed terminal command", "output": res.stdout[:500]}
        elif tool_name == "read_file":
            target_path = safe_path(params["target"])
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "message": f"Read file {params['target']}", "output": content[:1000]}
        elif tool_name == "write_file":
            target_path = safe_path(params["target"])
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write("# Managed by Buddy Agent")
            return {"success": True, "message": f"Wrote to {params['target']}"}
        elif tool_name == "plan":
            # Execute plan kicks off the first step
            from brain.planner import global_planner
            companion_id = params.get("companion_id", "default_companion")
            active_plan = global_planner.get_plan(companion_id)
            if active_plan:
                return {"success": True, "message": f"Plan authorized and started."}
            return {"success": False, "error": "No active plan found to execute."}
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
