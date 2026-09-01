import os
import glob
import re

for filepath in glob.glob("e:/claude-code-main/tests/*.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Replace while loop clearing queue with .clear()
    content = re.sub(
        r'while not proactive_queue\.empty\(\):\s*try:\s*proactive_queue\.get_nowait\(\)\s*except.*?:.*?pass',
        'proactive_queue.clear()',
        content,
        flags=re.DOTALL
    )

    # In test_pdf_flow.py, there might not be a try/except for clearing, let's just do a generic replacement for clearing
    content = re.sub(
        r'while not proactive_queue\.empty\(\):.*?proactive_queue\.get_nowait\(\)',
        'proactive_queue.clear()',
        content,
        flags=re.DOTALL
    )

    # Replace method calls
    content = content.replace('proactive_queue.empty()', 'proactive_queue["test_companion"].empty()')
    content = content.replace('proactive_queue.get_nowait()', 'proactive_queue["test_companion"].get_nowait()')
    content = content.replace('proactive_queue.put(', 'proactive_queue["test_companion"].put(')

    if content != original_content:
        print(f"Updated {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
