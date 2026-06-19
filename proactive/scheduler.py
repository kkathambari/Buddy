import threading
from proactive.trigger import proactive_queue
from relationship.manager import get_relationship
from ai.gateway.broker import AIGateway
from core.logging import setup_logger

logger = setup_logger("proactive_scheduler")

def schedule_reminder(name: str, delay_sec: float, prompt: str) -> threading.Timer:
    """
    Schedules a proactive reminder.
    When the timer expires, it checks if trust level allows and generates/queues the response.
    """
    def task():
        try:
            rel = get_relationship()
            if rel.get("trust", 0.5) < 0.3:
                logger.info(f"Scheduled reminder '{name}' ignored: trust too low.")
                return
                
            response = AIGateway.generate_response(prompt)
            proactive_queue.put(response)
            logger.info(f"Fired and queued scheduled reminder: {name}")
        except Exception as e:
            logger.error(f"Failed to generate scheduled reminder '{name}': {e}")
            
    timer = threading.Timer(delay_sec, task)
    timer.daemon = True
    timer.start()
    logger.info(f"Scheduled proactive reminder '{name}' in {delay_sec} seconds.")
    return timer
