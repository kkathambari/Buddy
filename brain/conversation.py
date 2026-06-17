import subprocess
import random
import time
import threading
import sys
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

def choose_model(user_input):
    cfg = get_config()
    text = user_input.lower()
    if "code" in text or "bug" in text or "error" in text:
        return "deepseek-coder"
    elif "explain" in text or "why" in text:
        return "mistral"
    else:
        return cfg.get("model", "llama3")

def ask_llm(prompt):
    cfg = get_config()
    provider = cfg.get("ai_provider", "ollama")
    
    if provider == "chatgpt":
        try:
            import openai
            api_key = cfg.get("chatgpt_api_key", "")
            if not api_key: return "My ChatGPT API key is missing!"
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"ChatGPT connection issue: {e}"
            
    elif provider == "claude":
        try:
            import anthropic
            api_key = cfg.get("claude_api_key", "")
            if not api_key: return "My Claude API key is missing!"
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Claude connection issue: {e}"
            
    elif provider == "gemini":
        try:
            import google.generativeai as genai
            api_key = cfg.get("gemini_api_key", "")
            if not api_key: return "My Gemini API key is missing!"
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Gemini connection issue: {e}"
            
    else: # default ollama
        model = choose_model(prompt)
        try:
            # Under Windows, prevent window popups if necessary
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ["ollama", "run", model],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=60,
                encoding="utf-8",
                startupinfo=startupinfo
            )
            if result.returncode != 0:
                return "Hmm… something feels off."
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "I’m here… just a little slow right now. (Timeout)"
        except Exception:
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

def ghost_presence():
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

def process_chat(user_input, stats, energy):
    tone = analyze_tone(user_input)
    log_emotion(tone["emotion"])

    threading.Thread(target=store_memory, args=(f"User said: {user_input}",), daemon=True).start()

    prompt = build_prompt(user_input, stats, energy)
    raw_response = ask_llm(prompt)

    cleaned_response = parse_and_execute_actions(raw_response)

    final = apply_personality(cleaned_response, stats)
    final = emotional_adjust(final, tone)

    if tone["emotion"] == "sad":
        time.sleep(2.0)
    elif tone["intensity"] == "high":
        time.sleep(0.5)
    else:
        time.sleep(1.2)

    typing_effect(final)

    return final
