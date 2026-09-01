import os

files = [
    "tests/test_career_integration.py",
    "tests/test_education_integration.py",
    "tests/test_pdf_flow.py",
    "tests/test_relationship_proactive.py"
]

for f in files:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    # 1. Fix the while loop
    loop_str = """        while not proactive_queue.empty():
            try:
                proactive_queue.get_nowait()
            except Exception:
                break"""
    
    content = content.replace(loop_str, "        proactive_queue.clear()")
    
    # 2. Fix empty(), get_nowait(), put()
    content = content.replace("proactive_queue.empty()", "proactive_queue['test_companion'].empty()")
    content = content.replace("proactive_queue.get_nowait()", "proactive_queue['test_companion'].get_nowait()")
    content = content.replace("proactive_queue.put(", "proactive_queue['test_companion'].put(")
    
    with open(f, "w", encoding="utf-8") as file:
        file.write(content)

print("Replacement complete.")
