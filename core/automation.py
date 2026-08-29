import re
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
    return re.sub(r'\[(?:OPEN|BROWSE):\s*.+?\]', '', response_text, flags=re.IGNORECASE).strip()

def get_clipboard_text(root):
    """
    Safely retrieves clipboard content using Tkinter to avoid heavy pip dependencies like pyperclip.
    """
    try:
        return root.clipboard_get()
    except Exception:
        return None
