import os
import json
import asyncio
import threading
from typing import Dict, Any, Callable, Coroutine, List, Optional
from core.logging import setup_logger
from shared.storage import safe_load, safe_save

logger = setup_logger("agent_runtime")
STATE_FILE = "data/runtime_state.json"

class TaskScheduler:
    """
    Asynchronous task scheduler supporting delayed and recurring background jobs.
    """
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._lock = threading.Lock()

    def schedule_once(self, task_id: str, delay_seconds: float, func: Callable[[], Any]) -> None:
        """Schedules a synchronous or asynchronous function to execute once after a delay."""
        async def _run():
            try:
                await asyncio.sleep(delay_seconds)
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            except asyncio.CancelledError:
                logger.info(f"Delayed task '{task_id}' cancelled.")
            except Exception as e:
                logger.error(f"Error in delayed task '{task_id}': {e}", exc_info=True)
            finally:
                with self._lock:
                    self._active_tasks.pop(task_id, None)

        with self._lock:
            if task_id in self._active_tasks:
                old_task = self._active_tasks[task_id]
                if hasattr(old_task, "cancel"):
                    try:
                        self._loop.call_soon_threadsafe(old_task.cancel)
                    except RuntimeError:
                        old_task.cancel()
                else:
                    old_task.cancel()
            
            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop == self._loop:
                task = self._loop.create_task(_run())
            else:
                task = asyncio.run_coroutine_threadsafe(_run(), self._loop)
            self._active_tasks[task_id] = task
            logger.info(f"Scheduled one-shot task '{task_id}' in {delay_seconds}s.")

    def schedule_recurring(self, task_id: str, interval_seconds: float, func: Callable[[], Any]) -> None:
        """Schedules a task to execute repeatedly at a fixed interval."""
        async def _run():
            try:
                while True:
                    await asyncio.sleep(interval_seconds)
                    try:
                        if asyncio.iscoroutinefunction(func):
                            await func()
                        else:
                            func()
                    except Exception as e:
                        logger.error(f"Error in recurring task '{task_id}' iteration: {e}", exc_info=True)
            except asyncio.CancelledError:
                logger.info(f"Recurring task '{task_id}' stopped.")
            finally:
                with self._lock:
                    self._active_tasks.pop(task_id, None)

        with self._lock:
            if task_id in self._active_tasks:
                old_task = self._active_tasks[task_id]
                if hasattr(old_task, "cancel"):
                    try:
                        self._loop.call_soon_threadsafe(old_task.cancel)
                    except RuntimeError:
                        old_task.cancel()
                else:
                    old_task.cancel()
            
            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop == self._loop:
                task = self._loop.create_task(_run())
            else:
                task = asyncio.run_coroutine_threadsafe(_run(), self._loop)
            self._active_tasks[task_id] = task
            logger.info(f"Scheduled recurring task '{task_id}' every {interval_seconds}s.")

    def cancel_task(self, task_id: str) -> bool:
        """Cancels a scheduled task by ID. Returns True if cancelled successfully."""
        with self._lock:
            task = self._active_tasks.pop(task_id, None)
            if task:
                if hasattr(task, "cancel"):
                    try:
                        self._loop.call_soon_threadsafe(task.cancel)
                    except RuntimeError:
                        task.cancel()
                else:
                    task.cancel()
                logger.info(f"Cancelled task '{task_id}'.")
                return True
            return False

    def shutdown(self) -> None:
        """Cancels all active schedules and timers."""
        with self._lock:
            for task_id, task in list(self._active_tasks.items()):
                self._loop.call_soon_threadsafe(task.cancel)
            self._active_tasks.clear()
            logger.info("All scheduled tasks cancelled.")


class AgentRuntime:
    """
    Lifecycle and execution manager for concurrent agents.
    Runs on an isolated background event loop thread.
    """
    def __init__(self):
        self._active_agents: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="RuntimeLoopThread")
        self._thread.start()
        self.scheduler = TaskScheduler(self._loop)
        
        # Auto-load state on startup
        self.restore_state()

        # Register user_idle listener on event bus
        try:
            from events.bus import global_bus
            global_bus.subscribe("user_idle", self._on_user_idle)
        except Exception as e:
            logger.warning(f"Could not subscribe to event bus: {e}")

    def _on_user_idle(self, event_data: dict) -> None:
        """Callback invoked when user activity becomes idle."""
        logger.info("Received idle event notification. Scheduling dream cycle task.")
        from brain.dream import DreamEngine
        dream_engine = DreamEngine()
        self.scheduler.schedule_once("dream_cycle_task", 0.1, dream_engine.start_dream_cycle)

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"AgentRuntime loop encountered error: {e}")

    def register_agent(self, agent_id: str, agent_instance: Any, metadata: Dict[str, Any] = None) -> None:
        """Registers a live agent instance with the runtime."""
        with self._lock:
            self._active_agents[agent_id] = {
                "instance": agent_instance,
                "metadata": metadata or {},
                "status": "idle",
                "running_tasks": 0
            }
            logger.info(f"Agent '{agent_id}' registered successfully.")
            self.save_state()

    def unregister_agent(self, agent_id: str) -> None:
        """Unregisters an agent from the runtime."""
        with self._lock:
            self._active_agents.pop(agent_id, None)
            logger.info(f"Agent '{agent_id}' unregistered.")
            self.save_state()

    def run_agent_task(self, agent_id: str, task_id: str, coro_func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> None:
        """Runs an agent's task asynchronously on the background loop."""
        async def _execution_wrapper():
            with self._lock:
                if agent_id in self._active_agents:
                    self._active_agents[agent_id]["status"] = "busy"
                    self._active_agents[agent_id]["running_tasks"] += 1
            
            try:
                await coro_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Agent '{agent_id}' execution task '{task_id}' crashed: {e}", exc_info=True)
            finally:
                with self._lock:
                    if agent_id in self._active_agents:
                        self._active_agents[agent_id]["running_tasks"] -= 1
                        if self._active_agents[agent_id]["running_tasks"] <= 0:
                            self._active_agents[agent_id]["running_tasks"] = 0
                            self._active_agents[agent_id]["status"] = "idle"
                self.save_state()

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop == self._loop:
            self._loop.create_task(_execution_wrapper())
        else:
            asyncio.run_coroutine_threadsafe(_execution_wrapper(), self._loop)

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Returns details about a running agent."""
        with self._lock:
            agent = self._active_agents.get(agent_id)
            if agent:
                return {
                    "status": agent["status"],
                    "running_tasks": agent["running_tasks"],
                    "metadata": agent["metadata"]
                }
            return None

    def save_state(self) -> None:
        """Saves current runtime active agents list to disk for recovery."""
        try:
            state = {
                "active_agents": {
                    aid: {
                        "metadata": info["metadata"],
                        "status": info["status"]
                    } for aid, info in self._active_agents.items()
                },
                "timestamp": asyncio.get_event_loop().time() if self._loop.is_running() else 0
            }
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            safe_save(STATE_FILE, state)
        except Exception as e:
            logger.error(f"Failed to save runtime state: {e}")

    def restore_state(self) -> None:
        """Restores runtime states and loaded agents from crash storage."""
        if not os.path.exists(STATE_FILE):
            return
        try:
            state = safe_load(STATE_FILE, {})
            if "active_agents" in state:
                logger.info(f"Loaded past runtime state. Found {len(state['active_agents'])} unregistered agent states.")
                for aid, info in state["active_agents"].items():
                    self._active_agents[aid] = {
                        "instance": None,
                        "metadata": info["metadata"],
                        "status": "idle",
                        "running_tasks": 0
                    }
        except Exception as e:
            logger.error(f"Failed to restore runtime state: {e}")

    def shutdown(self) -> None:
        """Shuts down all agent loops, schedulers, and loops."""
        logger.info("Stopping AgentRuntime...")
        self.scheduler.shutdown()
        with self._lock:
            self._active_agents.clear()
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

# Global singleton runtime
global_runtime = AgentRuntime()
