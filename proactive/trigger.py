import queue
from ai.gateway.broker import AIGateway
from events.bus import global_bus, Event
from relationship.manager import get_relationship
from proactive.cooldowns import is_cooldown_active, update_cooldown
from core.logging import setup_logger

logger = setup_logger("proactive_trigger")

# Unified queue for proactive messages
proactive_queue = queue.Queue()

def register_proactive_subscribers():
    """Subscribes proactive handlers to the global event bus."""
    global_bus.subscribe("user_struggling", handle_user_struggling)
    global_bus.subscribe("active_category_changed", handle_category_changed)
    logger.info("Proactive triggers successfully subscribed to Event Bus.")

def handle_user_struggling(event: Event):
    payload = event.payload
    ratio = payload.get("delete_ratio", 0.0)
    
    if is_cooldown_active("user_struggling"):
        logger.info("Proactive struggle trigger ignored: cooldown active.")
        return
        
    rel = get_relationship()
    if rel.get("trust", 0.5) < 0.3:
        logger.info("Proactive struggle trigger ignored: trust too low (< 0.3).")
        return
        
    prompt = f"""
You are Daemon, a calm, observant, and slightly teasing ghost developer coach.
The user is currently coding but seems to be struggling. They are typing and deleting code repeatedly in their IDE (delete ratio: {ratio:.0%}).
Do NOT be dry or diagnostic (do not mention ratios or error logs). Speak naturally, offering a hand or another pair of eyes in Daemon's persona.
Keep your response short (1-2 sentences).
Daemon:
"""
    try:
        response = AIGateway.generate_response(prompt)
        proactive_queue.put(response)
        update_cooldown("user_struggling")
        logger.info("Queued proactive struggle comment.")
    except Exception as e:
        logger.error(f"Failed to generate proactive struggle comment: {e}")

def handle_category_changed(event: Event):
    payload = event.payload
    new_cat = payload.get("new_category", "")
    title = payload.get("title", "")
    
    if is_cooldown_active("active_category_changed"):
        logger.info("Proactive category switch trigger ignored: cooldown active.")
        return
        
    rel = get_relationship()
    if rel.get("trust", 0.5) < 0.3:
        logger.info("Proactive category switch trigger ignored: trust too low (< 0.3).")
        return
        
    prompt = f"""
You are Daemon, a ghost developer companion.
The user has just switched their active window to: {new_cat} (Window title: "{title}").
Respond naturally in character (calm, teasing, observant), acknowledging this activity switch (e.g. noticing they are back to coding, or browsing).
Keep your response short (1-2 sentences).
Daemon:
"""
    try:
        response = AIGateway.generate_response(prompt)
        proactive_queue.put(response)
        update_cooldown("active_category_changed")
        logger.info("Queued proactive category comment.")
    except Exception as e:
        logger.error(f"Failed to generate proactive category comment: {e}")
