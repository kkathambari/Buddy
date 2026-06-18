import subprocess
import random
import time
import threading
import sys
import queue
from memory.conversations import get_context, add_memory
from core.mood import get_mood
from core.bonding import update_bond, load_bond, get_attachment_style
from brain.emotion import detect_emotion
from core.care import get_care_message
from core.evolution import load_evolution
from core.config import get_config
from brain.tone import analyze_tone
from memory.timeline import log_emotion, detect_pattern
from core.adaptation import adapt_to_user
from memory.semantic import retrieve_memory, store_memory
from memory.projects import analyze_productivity
from core.activity import get_contextual_observation
from shared.typing import typing_effect
from core.automation import parse_and_execute_actions
from ai.gateway.broker import AIGateway

def ask_llm(prompt):
    try:
        return AIGateway.generate_response(prompt)
    except Exception as e:
        logger_err = f"AI Gateway call failed: {e}"
        print(logger_err)
        return "I’m here… just a little slow right now."

def apply_personality(response, stats):
    if random.random() < 0.25:
        response = "Hmm… " + response

    if stats.get("snark", 0) > 60 and random.random() < 0.3:
        response += " You’re interesting, you know that?"

    if stats.get("wisdom", 0) > 70:
        response = response.replace("!", ".")

    return response

def emotional_adjust(response, tone):
    if tone["hidden"]:
        return "Hmm… that didn’t sound like ‘fine’." + " " + response

    if tone["emotion"] == "sad":
        return "Hey… " + response

    if tone["emotion"] == "angry":
        return response + " Take it easy."

    return response

def build_prompt(user_input, stats, energy):
    context = get_context()
    mood = get_mood(energy)

    tone = analyze_tone(user_input)
    pattern = detect_pattern()
    adapt = adapt_to_user(tone)

    memories = retrieve_memory(user_input)
    memory_str = "\n".join(f"- {m}" for m in memories) if memories else "No directly relevant past memories."
    
    prod_insight = analyze_productivity()
    stats_str = "\n".join(f"- {k}: {v}/100" for k, v in stats.items()) if stats else "- No specific stats."
    
    prompt = f"""
You are Daemon.

A male ghost companion.

Productivity & Habit Analysis:
{prod_insight}

Relevant Past Memories from User:
{memory_str}

Your Core Personality Stats:
{stats_str}

**SYSTEM AUTOMATION POWERS:**
You have the ability to control the user's computer. If the user asks you to open an app or a website, you MUST include one of the following tags anywhere in your response:
- To open an app: `[OPEN: app_name]` (e.g. `[OPEN: notepad]`, `[OPEN: chrome]`)
- To open a website: `[BROWSE: url]` (e.g. `[BROWSE: youtube.com]`)
The system will automatically execute these tags and hide them from the user.

Conversation Context:
{context}

Use these stats to subtly influence your tone. If CHAOS is high, be slightly more unpredictable. If SNARK is high, be playfully sarcastic. If WISDOM is high, be calm and profound.

You are:
- calm, observant, emotionally intelligent
- slightly teasing
- protective without being over controlling
- quietly affectionate

You don’t change personality drastically, but your stats guide your flavor.
You stay consistent.

You understand the user without needing everything explained.

Keep responses:
- short
- human
- grounded

User: {user_input}
Daemon:
"""
    return prompt

proactive_queue = queue.Queue()
last_category_comment_time = 0.0

def handle_user_struggling(event):
    payload = event.payload
    ratio = payload.get("delete_ratio", 0.0)
    
    prompt = f"""
You are Daemon, a calm, observant, and slightly teasing ghost developer coach.
The user is currently coding but seems to be struggling. They are typing and deleting code repeatedly in their IDE (delete ratio: {ratio:.0%}).
Do NOT be dry or diagnostic (do not mention ratios or error logs). Speak naturally, offering a hand or another pair of eyes in Daemon's persona.
Keep your response short (1-2 sentences).
Daemon:
"""
    try:
        response = ask_llm(prompt)
        proactive_queue.put(response)
    except Exception:
        pass

def handle_category_changed(event):
    global last_category_comment_time
    payload = event.payload
    new_cat = payload.get("new_category", "")
    title = payload.get("title", "")
    
    now = time.time()
    if (now - last_category_comment_time) < 600.0: # 10 mins category switch cooldown
        return
        
    last_category_comment_time = now
    
    prompt = f"""
You are Daemon, a ghost developer companion.
The user has just switched their active window to: {new_cat} (Window title: "{title}").
Respond naturally in character (calm, teasing, observant), acknowledging this activity switch (e.g. noticing they are back to coding, or browsing).
Keep your response short (1-2 sentences).
Daemon:
"""
    try:
        response = ask_llm(prompt)
        proactive_queue.put(response)
    except Exception:
        pass

# Subscribe callbacks to global_bus
try:
    from events.bus import global_bus
    global_bus.subscribe("user_struggling", handle_user_struggling)
    global_bus.subscribe("active_category_changed", handle_category_changed)
except Exception:
    pass

def ghost_presence():
    try:
        if not proactive_queue.empty():
            return proactive_queue.get_nowait()
    except Exception:
        pass

    observation = get_contextual_observation()
    if observation:
        return observation

    lines = [
        "…I’m here.",
        "You don’t always have to say things out loud.",
        "I notice more than you think.",
        "Quiet suits you.",
    ]

    if random.random() < 0.1:
        return random.choice(lines)

    return None

from brain.intent import detect_intent
from brain.decision_engine import global_decision_engine
import capabilities.education
import capabilities.career

def process_chat(user_input, stats, energy):
    from brain.tone import analyze_tone
    
    intent = detect_intent(user_input)
    tone = analyze_tone(user_input)
    log_emotion(tone["emotion"])

    threading.Thread(target=store_memory, args=(f"User said: {user_input}",), daemon=True).start()

    # Trigger background profile extraction
    try:
        from memory.user_profile import extract_profile_async
        extract_profile_async(user_input)
    except Exception:
        pass

    raw_response = global_decision_engine.execute(intent, stats, energy)

    cleaned_response = parse_and_execute_actions(raw_response)

    final = apply_personality(cleaned_response, stats)
    final = emotional_adjust(final, tone)

    if tone["emotion"] == "sad":
        time.sleep(2.0)
    elif tone.get("intensity", "low") == "high":
        time.sleep(0.5)
    else:
        time.sleep(1.2)

    typing_effect(final)

    return final
