import threading
import time
import asyncio
from typing import Optional
from proactive.trigger import proactive_queue
from relationship.manager import get_relationship
from ai.gateway.broker import AIGateway
from core.logging import setup_logger
from backend.repositories.factory import get_schedule_repository

logger = setup_logger("proactive_scheduler")

class PersistentScheduler:
    def __init__(self):
        self._running = False
        self._thread = None
        
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        self._running = False
        
    def _loop(self):
        repo = get_schedule_repository()
        while self._running:
            try:
                tasks = repo.get_pending_tasks()
                for task in tasks:
                    self._execute_task(task, repo)
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            time.sleep(5)
            
    def _execute_task(self, task, repo):
        name = task["name"]
        prompt = task["prompt"]
        companion_id = task["companion_id"]
        task_id = task["id"]
        try:
            # Check permissions or trust if needed
            rel = get_relationship() # Note: get_relationship doesn't take companion_id yet, but keeping legacy behavior
            if rel.get("trust", 0.5) < 0.3:
                logger.info(f"Scheduled reminder '{name}' ignored: trust too low.")
                repo.mark_completed(task_id)
                return
                
            response = AIGateway.generate_response(prompt)
            proactive_queue[companion_id].put(response)
            logger.info(f"Fired and queued scheduled reminder: {name}")
            
            if task["recurring"]:
                reschedule_at = time.time() + task["interval_sec"]
                repo.mark_completed(task_id, reschedule_at=reschedule_at)
            else:
                repo.mark_completed(task_id)
        except Exception as e:
            logger.error(f"Failed to execute scheduled task '{name}': {e}")
            repo.mark_completed(task_id) # Mark completed to prevent infinite retry on hard failure, or maybe retry? Let's just complete.

global_scheduler = PersistentScheduler()
global_scheduler.start()

def schedule_reminder(name: str, delay_sec: float, prompt: str, companion_id: str = "default_pet") -> str:
    """
    Schedules a persistent proactive reminder.
    Returns the task ID.
    """
    repo = get_schedule_repository()
    task_id = repo.create_task({
        "companion_id": companion_id,
        "name": name,
        "prompt": prompt,
        "run_at": time.time() + delay_sec
    })
    logger.info(f"Scheduled persistent proactive reminder '{name}' in {delay_sec} seconds (ID: {task_id}).")
    return task_id
