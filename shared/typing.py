import time
import random
import sys

def typing_effect(text):
    try:
        output = ""
        for char in text:
            if sys.stdout:
                sys.stdout.write(char)
                sys.stdout.flush()
            time.sleep(random.uniform(0.02, 0.05))
        if sys.stdout:
            sys.stdout.write("\n")
            sys.stdout.flush()
    except Exception:
        pass
