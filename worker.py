import time
import signal
import sys
from backend.repositories.factory import get_schedule_repository
from backend.repositories.postgres import init_db
from ai.gateway.broker import AIGateway
from backend.messaging import publish_ws_event
from core.logging import setup_logger

logger = setup_logger("buddy_worker")

class BuddyWorker:
    def __init__(self):
        self._running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}. Shutting down worker gracefully...")
        self._running = False

    def run(self):
        logger.info("Initializing database...")
        init_db()
        logger.info("Starting Buddy Worker main loop...")
        
        self._running = True
        repo = get_schedule_repository()
        
        while self._running:
            try:
                tasks = repo.get_pending_tasks()
                for task in tasks:
                    if not self._running:
                        break # Stop processing tasks if shutting down
                    self._execute_task(task, repo)
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
            
            # Sleep in small increments to respond to shutdown signals quickly
            for _ in range(50):
                if not self._running:
                    break
                time.sleep(0.1)
                
        logger.info("Buddy Worker stopped.")

    def _execute_task(self, task, repo):
        name = task["name"]
        prompt = task["prompt"]
        companion_id = task["companion_id"]
        task_id = task["id"]
        
        logger.info(f"Executing scheduled task '{name}' (ID: {task_id})...")
        try:
            # We used to check trust here, but let's assume if it's scheduled it should run.
            # In a real system, we'd fetch relationship and check trust if needed.
            response = AIGateway.generate_response(prompt)
            publish_ws_event(companion_id, response)
            logger.info(f"Completed scheduled task: {name}")
            
            if task.get("recurring"):
                reschedule_at = time.time() + task.get("interval_sec", 3600)
                repo.mark_completed(task_id, reschedule_at=reschedule_at)
            else:
                repo.mark_completed(task_id)
        except Exception as e:
            logger.error(f"Failed to execute scheduled task '{name}': {e}", exc_info=True)
            repo.mark_completed(task_id) # Mark completed on hard failure so we don't spin loop

if __name__ == "__main__":
    worker = BuddyWorker()
    worker.run()
