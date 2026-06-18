import re
from typing import Any, Dict, Tuple
from brain.intent_types import Intent, IntentCategory

def has_keyword(text: str, keywords: list) -> bool:
    """Helper to match keywords as full words using regex word boundaries."""
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return True
    return False

def match_intent_rules(text: str) -> Intent:
    text_lower = text.strip().lower()
    
    # 1. System commands
    if text_lower.startswith("/") or text_lower.startswith("[") or "open:" in text_lower or "browse:" in text_lower:
        return Intent(
            category=IntentCategory.SYSTEM_COMMAND,
            raw_text=text,
            confidence=1.0,
            entities={"command_type": "ui_automation"}
        )
        
    # 2. Greetings
    greeting_phrases = ["good morning", "good evening", "good afternoon", "good night"]
    greeting_keywords = [
        "hi", "hello", "hey", "gm", "gn", "morning", "evening", "greetings", 
        "what's up", "yo", "wazza", "howdy", "hola", "sup"
    ]
    words = text_lower.split()
    if any(phrase in text_lower for phrase in greeting_phrases) or (
        words and any(w == words[0].rstrip("!,.") for w in greeting_keywords)
    ):
        return Intent(
            category=IntentCategory.GREETING,
            raw_text=text,
            confidence=0.9
        )
        
    # 3. Learning triggers
    learning_keywords = [
        "study", "learn", "exam", "quiz", "revision", "viva", "concept", 
        "homework", "test", "course", "syllabus", "mastery"
    ]
    topics = ["python", "javascript", "databases", "algorithms", "react", "sql", "rust", "cpp"]
    matched_topic = None
    for topic in topics:
        if has_keyword(text_lower, [topic]):
            matched_topic = topic.capitalize()
            break
            
    if has_keyword(text_lower, learning_keywords):
        entities = {}
        if matched_topic:
            entities["concept"] = matched_topic
        return Intent(
            category=IntentCategory.LEARNING,
            raw_text=text,
            confidence=0.85,
            entities=entities
        )
        
    # 4. Career triggers
    career_keywords = [
        "job", "career", "interview", "resume", "internship", "ats", "cv", 
        "hired", "recruiter", "portfolio", "application"
    ]
    if has_keyword(text_lower, career_keywords):
        roles = ["backend", "frontend", "fullstack", "mobile", "design", "data"]
        matched_role = "General Developer"
        for role in roles:
            if has_keyword(text_lower, [role]):
                matched_role = role.capitalize() + " Developer"
                break
        return Intent(
            category=IntentCategory.CAREER,
            raw_text=text,
            confidence=0.85,
            entities={"role": matched_role}
        )
        
    # 5. Productivity queries
    productivity_keywords = [
        "stats", "hours", "coding time", "active window", "progress", 
        "dashboard", "metrics", "productivity", "achievements", "sessions"
    ]
    if has_keyword(text_lower, productivity_keywords):
        return Intent(
            category=IntentCategory.PRODUCTIVITY_QUERY,
            raw_text=text,
            confidence=0.9
        )
        
    # 6. Memory queries
    memory_keywords = [
        "remember", "recall", "forgot", "what did i say", "my profile", 
        "do you know my", "last time", "history"
    ]
    if has_keyword(text_lower, memory_keywords):
        return Intent(
            category=IntentCategory.MEMORY_QUERY,
            raw_text=text,
            confidence=0.8
        )
        
    # 7. Emotion logs
    emotion_keywords = [
        "tired", "exhausted", "stressed", "worried", "sad", "angry", 
        "happy", "excited", "frustrated", "struggling", "depressed"
    ]
    matched_emotion = None
    for emo in emotion_keywords:
        if has_keyword(text_lower, [emo]):
            matched_emotion = emo
            break
            
    if matched_emotion:
        return Intent(
            category=IntentCategory.EMOTION,
            raw_text=text,
            confidence=0.75,
            entities={"emotion": matched_emotion}
        )
        
    # 8. Companionship (Fallback)
    return Intent(
        category=IntentCategory.COMPANIONSHIP,
        raw_text=text,
        confidence=1.0
    )
