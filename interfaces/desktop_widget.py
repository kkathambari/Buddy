import os
import sys
from core.logging import setup_logger
from events.bus import global_bus, Event
from brain.personality.sprite import SpriteSheetAnimator

logger = setup_logger("desktop_widget")

# Try to import Kivy, setting environment configurations for headless runs if display server lacks graphics.
KIVY_AVAILABLE = False
try:
    os.environ['KIVY_NO_ARGS'] = '1'
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.image import Image
    from kivy.uix.label import Label
    from kivy.clock import Clock
    KIVY_AVAILABLE = True
except Exception as e:
    logger.warning(f"Kivy UI library not available: {e}. Falling back to headless widget mode.")

if KIVY_AVAILABLE:
    class CompanionApp(App):
        """
        Desktop Widget App (Kivy GUI).
        Renders character animations and active goals on the desktop.
        """
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.animator = SpriteSheetAnimator()
            self.current_state = "idle"
            self.frame_index = 0
            self.active_goal = "Initializing Companion..."
            self.image_widget = None
            self.label_widget = None

            # Subscribe to event bus callbacks
            global_bus.subscribe("task_started", self.on_task_started)
            global_bus.subscribe("user_struggling", self.on_user_struggling)
            global_bus.subscribe("personality_update", self.on_personality_update)

        def build(self):
            self.title = "DevBuddy Companion"
            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            
            # Image showing the animation frame
            initial_frame = self.animator.get_animation_frame(self.current_state, self.frame_index)
            self.image_widget = Image(source=initial_frame)
            layout.add_widget(self.image_widget)
            
            # Label showing active goal status
            self.label_widget = Label(text=self.active_goal, size_hint_y=None, height=40)
            layout.add_widget(self.label_widget)
            
            # Schedule tick animations every 250ms
            Clock.schedule_interval(self.animate_tick, 0.25)
            
            return layout

        def animate_tick(self, dt):
            self.frame_index += 1
            frame_path = self.animator.get_animation_frame(self.current_state, self.frame_index)
            if self.image_widget:
                self.image_widget.source = frame_path

        def on_task_started(self, event: Event):
            logger.info(f"Widget received task_started event: {event.payload}")
            self.current_state = "thinking"
            self.active_goal = f"Working on: {event.payload.get('task_name', 'Sub-Task')}"
            if self.label_widget:
                self.label_widget.text = self.active_goal

        def on_user_struggling(self, event: Event):
            logger.info(f"Widget received user_struggling event: {event.payload}")
            self.current_state = "struggling"
            self.active_goal = "Need help? Let's check the code!"
            if self.label_widget:
                self.label_widget.text = self.active_goal

        def on_personality_update(self, event: Event):
            logger.info(f"Widget received personality_update event: {event.payload}")
            self.current_state = event.payload.get("sprite_state", "idle")

else:
    class CompanionApp:
        """
        Headless CompanionApp mock fallback for testing without display servers.
        """
        def __init__(self, **kwargs):
            self.animator = SpriteSheetAnimator()
            self.current_state = "idle"
            self.frame_index = 0
            self.active_goal = "Initializing Companion (Headless)..."
            
            global_bus.subscribe("task_started", self.on_task_started)
            global_bus.subscribe("user_struggling", self.on_user_struggling)
            global_bus.subscribe("personality_update", self.on_personality_update)

        def build(self):
            logger.info("Building Headless Widget mockup.")
            return None

        def run(self):
            logger.info("Running Headless Widget loop mockup.")

        def stop(self):
            logger.info("Stopping Headless Widget loop mockup.")

        def animate_tick(self, dt=0) -> str:
            self.frame_index += 1
            return self.animator.get_animation_frame(self.current_state, self.frame_index)

        def on_task_started(self, event: Event):
            logger.info(f"Headless Widget received task_started event: {event.payload}")
            self.current_state = "thinking"
            self.active_goal = f"Working on: {event.payload.get('task_name', 'Sub-Task')}"

        def on_user_struggling(self, event: Event):
            logger.info(f"Headless Widget received user_struggling event: {event.payload}")
            self.current_state = "struggling"
            self.active_goal = "Need help? Let's check the code!"

        def on_personality_update(self, event: Event):
            logger.info(f"Headless Widget received personality_update event: {event.payload}")
            self.current_state = event.payload.get("sprite_state", "idle")
            
if __name__ == "__main__":
    app = CompanionApp()
    if KIVY_AVAILABLE:
        app.run()
    else:
        print("Kivy lacks graphical display capabilities. Exiting headless run.")
