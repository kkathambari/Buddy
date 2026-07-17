import os
import sys
import unittest
import asyncio
import time
from unittest.mock import MagicMock

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from events.bus import Event, EventBus

class TestAsyncEventBus(unittest.TestCase):
    
    def test_sync_callback_async_publish(self):
        bus = EventBus()
        called_events = []
        
        def sync_callback(event):
            called_events.append(event)
            
        bus.subscribe("test_event", sync_callback)
        event = Event("test_event", "test_sender", {"val": 123})
        
        # Publish asynchronously (default async_mode=True)
        bus.publish(event, async_mode=True)
        
        # Wait a short duration to let background thread execute it
        time.sleep(0.2)
        
        self.assertEqual(len(called_events), 1)
        self.assertEqual(called_events[0].payload["val"], 123)
        bus.shutdown()

    def test_async_callback_async_publish(self):
        bus = EventBus()
        called_events = []
        
        async def async_callback(event):
            called_events.append(event)
            
        bus.subscribe("test_async_event", async_callback)
        event = Event("test_async_event", "test_sender", {"val": 456})
        
        # Publish asynchronously
        bus.publish(event, async_mode=True)
        
        # Wait a short duration for loop execution
        time.sleep(0.2)
        
        self.assertEqual(len(called_events), 1)
        self.assertEqual(called_events[0].payload["val"], 456)
        bus.shutdown()

    def test_synchronous_mode_execution(self):
        bus = EventBus()
        called_events = []
        
        def sync_callback(event):
            called_events.append(event)
            
        bus.subscribe("sync_only_event", sync_callback)
        event = Event("sync_only_event", "test_sender", {"val": 789})
        
        # Publish synchronously (async_mode=False)
        bus.publish(event, async_mode=False)
        
        # No sleep needed, assertion should pass immediately
        self.assertEqual(len(called_events), 1)
        self.assertEqual(called_events[0].payload["val"], 789)
        bus.shutdown()

    def test_unsubscribe(self):
        bus = EventBus()
        called_events = []
        
        def callback(event):
            called_events.append(event)
            
        bus.subscribe("test_unsub", callback)
        event = Event("test_unsub", "sender")
        
        bus.publish(event, async_mode=False)
        self.assertEqual(len(called_events), 1)
        
        # Unsubscribe
        bus.unsubscribe("test_unsub", callback)
        bus.publish(event, async_mode=False)
        
        # Verify count is still 1
        self.assertEqual(len(called_events), 1)
        bus.shutdown()

if __name__ == "__main__":
    unittest.main()
