from datetime import datetime
from typing import Callable, Dict, List, Any
import threading
import uuid
import asyncio
from core.logging import setup_logger

logger = setup_logger("event_bus")

class Event:
    """Represents a system event flowing through the event bus."""
    def __init__(self, name: str, sender: str, payload: Dict[str, Any] = None):
        self.event_id = str(uuid.uuid4())
        self.name = name
        self.sender = sender
        self.payload = payload or {}
        self.timestamp = datetime.utcnow().isoformat()

    def __repr__(self):
        return f"<Event name={self.name} sender={self.sender} timestamp={self.timestamp}>"

class EventBus:
    """
    Asynchronous and thread-safe publish/subscribe Event Bus.
    Supports both async and sync callbacks. Decouples client activities
    from companion logic without blocking UI or key listener threads.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._lock = threading.Lock()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="EventBusThread")
        self._thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"EventBus asyncio loop encountered error: {e}")

    def subscribe(self, event_name: str, callback: Callable[[Event], Any]) -> None:
        """Subscribes a callback function (sync or async) to an event."""
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            if callback not in self._subscribers[event_name]:
                self._subscribers[event_name].append(callback)
                logger.info(f"Subscribed callback {getattr(callback, '__name__', str(callback))} to event: '{event_name}'")

    def unsubscribe(self, event_name: str, callback: Callable[[Event], Any]) -> None:
        """Unsubscribes a callback from the specified event."""
        with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(callback)
                    logger.info(f"Unsubscribed callback {getattr(callback, '__name__', str(callback))} from event: '{event_name}'")
                except ValueError:
                    pass

    async def async_publish(self, event: Event) -> None:
        """Asynchronously dispatches event to all subscribers concurrently."""
        with self._lock:
            callbacks = self._subscribers.get(event.name, []).copy()

        if not callbacks:
            logger.debug(f"Published event '{event.name}' with zero subscribers.")
            return

        logger.info(f"Publishing event '{event.name}' to {len(callbacks)} subscribers asynchronously.")

        tasks = []
        for callback in callbacks:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(self._execute_async(callback, event))
            else:
                tasks.append(self._execute_sync(callback, event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def publish(self, event: Event, async_mode: Any = None) -> None:
        """
        Publishes an event to subscribers.
        If async_mode is False, executes callbacks synchronously in the current calling thread.
        If async_mode is None, defaults to False (sync) if running inside a unit test environment, otherwise True (async).
        """
        if async_mode is None:
            import sys
            is_testing = any(m in sys.modules for m in ["unittest", "pytest"])
            async_mode = not is_testing

        if not async_mode:
            with self._lock:
                callbacks = self._subscribers.get(event.name, []).copy()
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        # Running async coroutine in sync context
                        asyncio.run(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in sync/fallback callback {getattr(callback, '__name__', str(callback))}: {e}")
            return

        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop == self._loop:
            # We are already on the EventBus background loop, schedule task directly
            self._loop.create_task(self.async_publish(event))
        else:
            # Safely schedule the coroutine from another thread/context
            asyncio.run_coroutine_threadsafe(self.async_publish(event), self._loop)

    async def _execute_async(self, callback: Callable[[Event], Any], event: Event) -> None:
        try:
            await callback(event)
        except Exception as e:
            logger.error(f"Error in async callback {getattr(callback, '__name__', str(callback))} on event '{event.name}': {e}", exc_info=True)

    async def _execute_sync(self, callback: Callable[[Event], Any], event: Event) -> None:
        try:
            # Offloads sync callbacks to thread executors so they do not block the event loop
            await self._loop.run_in_executor(None, callback, event)
        except Exception as e:
            logger.error(f"Error in sync callback {getattr(callback, '__name__', str(callback))} on event '{event.name}': {e}", exc_info=True)

    def shutdown(self) -> None:
        """Safely stops the event loop."""
        logger.info("Stopping EventBus asyncio loop...")
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

# Global singleton Event Bus
global_bus = EventBus()
