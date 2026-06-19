import subprocess
import random
import time
import threading
import sys
import queue
from memory.working_memory import get_recent_context
from core.mood import get_mood
from brain.emotion import detect_emotion
from core.care import get_care_message
from core.evolution import load_evolution
from core.config import get_config
from brain.tone import analyze_tone
from memory.extractors.emotion import log_emotion, detect_pattern
from core.adaptation import adapt_to_user
from memory.semantic import retrieve_memory, store_memory
from memory.projects import analyze_productivity
from core.activity import get_contextual_observation
from shared.typing import typing_effect
from core.automation import parse_and_execute_actions
from ai.gateway.broker import AIGateway
from brain.intent import detect_intent
from brain.decision_engine import global_decision_engine
from relationship.manager import get_relationship, update_relationship
from relationship.personality import adjust_personality_modifiers
from proactive.trigger import proactive_queue, register_proactive_subscribers

# Start proactive subscriptions
try:
    register_proactive_subscribers()
except Exception:
    pass

_pending_feedback = {}

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
    context = get_recent_context()
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

def ghost_presence(companion_id: str = "default_pet"):
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

def process_chat(user_input, stats, energy, companion_id: str = "default_pet"):
    from brain.tone import analyze_tone
    from brain.reflection import SelfReflection
    
    # 0. Check for Experience Engine intercept
    from brain.experience import ExperienceEngine
    experience_response = ExperienceEngine.intercept(user_input, companion_id)
    if experience_response is not None:
        try:
            from core.analytics import ProductAnalytics
            ProductAnalytics.track_event("experience_chat_turn", {
                "companion_id": companion_id,
                "experience_name": ExperienceEngine.load_state().get("active_experience", "unknown")
            })
        except Exception:
            pass
        typing_effect(experience_response)
        return experience_response

    # 1. Check for pending feedback reflection intercept
    if companion_id in _pending_feedback:
        fb_info = _pending_feedback.pop(companion_id)
        capability_name = fb_info["capability"]
        is_positive = SelfReflection.evaluate_feedback(user_input)
        
        # Calculate trust & bond changes
        trust_change = 0.1 if is_positive else -0.05
        bond_change = 5 if is_positive else -2
        
        # Update relationship
        rel = update_relationship(
            companion_id, 
            trust_change, 
            bond_change, 
            f"Reflection on {capability_name} completion (helpful={is_positive})"
        )
        
        # Log reflection milestone to timeline
        try:
            from timeline.history import log_timeline_event
            log_timeline_event(
                title=f"Reflection: {capability_name} was {'helpful' if is_positive else 'unhelpful'}",
                source="reflection",
                metadata={"capability": capability_name, "is_positive": is_positive, "trust": rel["trust"], "bond": rel["bond"]}
            )
        except Exception:
            pass
            
        final_response = "I'm glad to hear that! Let's keep making progress." if is_positive else "I appreciate the feedback. I will adjust and try to be more helpful."
        typing_effect(final_response)
        return final_response

    # 2. Standard dialogue execution
    intent = detect_intent(user_input)
    tone = analyze_tone(user_input)
    log_emotion(tone["emotion"])
    
    # Log product analytics
    try:
        from core.analytics import ProductAnalytics
        ProductAnalytics.track_event("chat_interaction", {
            "intent_category": intent.category.value if hasattr(intent.category, "value") else str(intent.category),
            "emotion_detected": tone.get("emotion", "neutral")
        })
    except Exception:
        pass

    # Load relationship trust and bond, adjust stats
    rel = get_relationship(companion_id)
    adjusted_stats = adjust_personality_modifiers(stats, rel["trust"], rel["bond"])

    # Route chitchat -> companionship for naming normalization
    if intent.category.value == "chitchat":
        from brain.intent_types import IntentCategory
        intent.category = IntentCategory.COMPANIONSHIP

    raw_response = global_decision_engine.execute(intent, adjusted_stats, energy)

    cleaned_response = parse_and_execute_actions(raw_response)

    if cleaned_response == "[ANIMATION: confused]":
        final = cleaned_response
    else:
        final = apply_personality(cleaned_response, adjusted_stats)
        final = emotional_adjust(final, tone)

    # Check if a capability has completed during this turn
    completed_capability = None
    
    # Check education capability
    education_cap = global_decision_engine._capabilities.get("education")
    if education_cap and hasattr(education_cap, "_active_sessions"):
        session = education_cap._active_sessions.get(companion_id)
        if session and session.get("stage") == "complete":
            completed_capability = "education"
            education_cap._active_sessions.pop(companion_id, None)
            
    # Check career capability
    career_cap = global_decision_engine._capabilities.get("career")
    if career_cap and hasattr(career_cap, "_active_career_sessions"):
        session = career_cap._active_career_sessions.get(companion_id)
        if session and session.get("stage") == "complete":
            completed_capability = "career"
            career_cap._active_career_sessions.pop(companion_id, None)
            
    if completed_capability:
        _pending_feedback[companion_id] = {"capability": completed_capability}
        final += "\nDid I help you get that working?"

    # Asynchronously evaluate and commit facts to Memory Manager
    try:
        from memory.manager import evaluate_and_commit
        evaluate_and_commit(user_input, final, tone["emotion"])
    except Exception:
        pass

    if tone["emotion"] == "sad":
        time.sleep(2.0)
    elif tone.get("intensity", "low") == "high":
        time.sleep(0.5)
    else:
        time.sleep(1.2)

    typing_effect(final)

    return final
