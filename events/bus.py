from datetime import datetime
from typing import Callable, Dict, List, Any
import threading
from core.logging import setup_logger

logger = setup_logger("event_bus")

class Event:
    """Represents a system event flowing through the event bus."""
    def __init__(self, name: str, payload: Dict[str, Any] = None):
        self.name = name
        self.payload = payload or {}
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"<Event name={self.name} timestamp={self.timestamp}>"

class EventBus:
    """
    Thread-safe publish/subscribe Event Bus.
    Allows decoupling client activities (e.g. coding events) from companion logic.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """Subscribes a callback function to run whenever the given event is published."""
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)
            logger.info(f"Subscribed callback {callback.__name__} to event: '{event_name}'")

    def unsubscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """Unsubscribes a callback from the specified event."""
        with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(callback)
                    logger.info(f"Unsubscribed callback {callback.__name__} from event: '{event_name}'")
                except ValueError:
                    pass

    def publish(self, event: Event, async_mode: bool = True) -> None:
        """
        Publishes an event to all subscribed callbacks.
        Defaults to running callbacks asynchronously in separate daemon threads.
        """
        with self._lock:
            callbacks = self._subscribers.get(event.name, []).copy()

        if not callbacks:
            logger.debug(f"Published event '{event.name}' with zero subscribers.")
            return

        logger.info(f"Publishing event '{event.name}' to {len(callbacks)} subscribers.")

        for callback in callbacks:
            if async_mode:
                threading.Thread(
                    target=self._run_callback,
                    args=(callback, event),
                    daemon=True
                ).start()
            else:
                self._run_callback(callback, event)

    def _run_callback(self, callback: Callable[[Event], None], event: Event) -> None:
        try:
            callback(event)
        except Exception as e:
            logger.error(f"Error executing callback {callback.__name__} on event '{event.name}': {e}", exc_info=True)

# Global singleton Event Bus
global_bus = EventBus()
