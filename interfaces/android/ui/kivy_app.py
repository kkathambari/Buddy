import os
import random
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout

from shared.storage import safe_load
from core.config import get_config, set_config
from sdk.client import ForgeSDK

from kivy.uix.spinner import Spinner

class SettingsPopup(Popup):
    def __init__(self, config, on_save, **kwargs):
        super().__init__(**kwargs)
        self.title = "Settings"
        self.size_hint = (0.9, 0.6)
        self.config = config
        self.on_save = on_save
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Provider selection
        prov_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        prov_layout.add_widget(Label(text="AI Provider:"))
        self.spinner = Spinner(
            text=config.get("ai_provider", "ollama"),
            values=('ollama', 'chatgpt', 'claude', 'gemini'),
            size_hint=(0.6, 1)
        )
        self.spinner.bind(text=self.on_provider_change)
        prov_layout.add_widget(self.spinner)
        layout.add_widget(prov_layout)
        
        # API Key input
        self.api_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        self.api_label = Label(text="API Key:")
        self.api_input = TextInput(multiline=False)
        self.api_layout.add_widget(self.api_label)
        self.api_layout.add_widget(self.api_input)
        layout.add_widget(self.api_layout)
        
        # Cloud Save Settings (Soul Seed)
        current_seed = config.get("pet_cloud_id", "")
        if not current_seed or current_seed == "default_pet":
            try:
                from core.auth import generate_soul_seed
                current_seed = generate_soul_seed()
                set_config("pet_cloud_id", current_seed)
                config["pet_cloud_id"] = current_seed
            except Exception:
                pass
                
        layout.add_widget(Label(text="Your Soul Seed (Copy to sync):", size_hint_y=0.1))
        self.seed_display = TextInput(text=current_seed, readonly=True, multiline=False, size_hint_y=0.15)
        layout.add_widget(self.seed_display)
        
        layout.add_widget(Label(text="Link to another Soul Seed:", size_hint_y=0.1))
        self.id_input = TextInput(text=current_seed, multiline=False, size_hint_y=0.15)
        layout.add_widget(self.id_input)
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        
        restore_btn = Button(text="Download Cloud Save")
        restore_btn.bind(on_press=self.restore_cloud)
        
        save_btn = Button(text="Save Settings")
        save_btn.bind(on_press=self.save_settings)
        
        btn_layout.add_widget(restore_btn)
        btn_layout.add_widget(save_btn)
        
        layout.add_widget(btn_layout)
        
        self.content = layout
        self.on_provider_change(self.spinner, self.spinner.text)

    def on_provider_change(self, spinner, text):
        if text == "ollama":
            self.api_layout.opacity = 0
            self.api_input.disabled = True
        else:
            self.api_layout.opacity = 1
            self.api_input.disabled = False
            self.api_label.text = f"{text.capitalize()} Key:"
            self.api_input.text = self.config.get(f"{text}_api_key", "")

    def save_settings(self, instance):
        provider = self.spinner.text
        set_config("ai_provider", provider)
        self.config["ai_provider"] = provider
        
        if provider != "ollama":
            key = f"{provider}_api_key"
            set_config(key, self.api_input.text.strip())
            self.config[key] = self.api_input.text.strip()
            
        # Save cloud settings
        set_config("pet_cloud_id", self.id_input.text.strip())
        self.config["pet_cloud_id"] = self.id_input.text.strip()
            
        self.on_save()
        self.dismiss()

    def restore_cloud(self, instance):
        pet_id = self.id_input.text.strip()
        if pet_id:
            app = App.get_running_app()
            cloud_soul = app.sdk.get_companion_state()
            if cloud_soul:
                from shared.storage import safe_save
                safe_save("data/soul.json", cloud_soul)
                self.title = "Cloud Save Restored! Restart App."
            else:
                self.title = "Failed to load cloud save."

class WelcomePopup(Popup):
    def __init__(self, soul, on_save, **kwargs):
        super().__init__(**kwargs)
        self.title = "Welcome to DevBuddy!"
        self.size_hint = (0.8, 0.4)
        self.auto_dismiss = False
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text="What would you like to name your pet?"))
        
        self.name_input = TextInput(text="Buddy", multiline=False, size_hint_y=0.4)
        layout.add_widget(self.name_input)
        
        btn = Button(text="Start", size_hint_y=0.4)
        btn.bind(on_press=lambda x: self.save_name(soul, on_save))
        layout.add_widget(btn)
        
        self.content = layout
        
    def save_name(self, soul, on_save):
        name = self.name_input.text.strip() or "Buddy"
        soul["name"] = name
        soul["is_first_run"] = False
        from shared.storage import safe_save
        safe_save("data/soul.json", soul)
        on_save()
        self.dismiss()

class AndroidPetApp(App):
    def build(self):
        from datetime import datetime
        self.session_start = datetime.now()
        
        self.config_data = get_config()
        self.soul = safe_load("data/soul.json", {"energy": 100})
        
        self.sdk = ForgeSDK()
        email = self.config_data.get("user_email")
        password = self.config_data.get("user_password")
        if email and password:
            self.sdk.login(email, password)
        if self.config_data.get("pet_cloud_id"):
            self.sdk.soul_seed = self.config_data["pet_cloud_id"]
        
        self.layout = BoxLayout(orientation='vertical')
        
        # Pet Image Area (Top half)
        self.pet_image = Image(source='', allow_stretch=True, keep_ratio=True, size_hint=(1, 0.5))
        self.layout.add_widget(self.pet_image)
        
        # Chat History
        self.chat_history = Label(text="Daemon is ready...\n", size_hint_y=None, markup=True)
        self.chat_history.bind(texture_size=self.chat_history.setter('size'))
        
        self.scroll = ScrollView(size_hint=(1, 0.4))
        self.scroll.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll)
        
        # Input Area
        input_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        settings_btn = Button(text="⚙", size_hint=(0.15, 1))
        settings_btn.bind(on_press=self.open_settings)
        
        self.text_input = TextInput(hint_text="Type...", multiline=False, size_hint=(0.65, 1))
        self.text_input.bind(on_text_validate=self.send_message)
        
        send_btn = Button(text=">", size_hint=(0.2, 1))
        send_btn.bind(on_press=self.send_message)
        
        input_layout.add_widget(settings_btn)
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(send_btn)
        
        self.layout.add_widget(input_layout)
        
        # Animation states
        self.state = "idle"
        self.frame_index = 0
        self.frames = self.load_all_frames()
        
        Clock.schedule_interval(self.animate_pet, 0.3)
        Clock.schedule_once(self.check_first_run, 0.5)
        Clock.schedule_interval(self.update_pet_stats, 5.0)
        
        return self.layout

    def check_first_run(self, dt):
        if self.soul.get("is_first_run", True):
            WelcomePopup(self.soul, self.on_welcome_done).open()
            
    def on_welcome_done(self):
        name = self.soul.get("name", "Buddy")
        self.append_chat(f"[color=aaaaaa]* {name} is ready! *[/color]\n")

    def load_all_frames(self):
        anim_dict = {}
        for state in ["idle", "walk", "sleep", "fall", "busy", "celebrate", "dizzy", "heart"]:
            path = os.path.join("assets", state)
            anim_dict[state] = []
            if os.path.exists(path):
                for f in sorted(os.listdir(path)):
                    if f.endswith(".png") or f.endswith(".gif"):
                        anim_dict[state].append(os.path.join(path, f))
        return anim_dict

    def animate_pet(self, dt):
        current_frames = self.frames.get(self.state, [])
        if current_frames:
            self.frame_index = (self.frame_index + 1) % len(current_frames)
            self.pet_image.source = current_frames[self.frame_index]

    def update_pet_stats(self, dt):
        from core.decay import update_energy
        from core.mood import get_mood
        from shared.storage import safe_save
        
        self.soul = update_energy(self.soul)
        mood = get_mood(self.soul.get("energy", 100))
        
        if self.state not in ["fall", "celebrate"]:
            if self.soul.get("energy", 100) < 10:
                self.state = "sleep"
            elif self.soul.get("energy", 100) < 40:
                self.state = "idle"
            elif mood == "happy":
                self.state = "walk"
            elif mood == "sad":
                self.state = "idle"
            elif mood == "dead":
                self.state = "sleep"
                
        safe_save("data/soul.json", self.soul)
            
    def append_chat(self, text, color="ffffff"):
        self.chat_history.text += f"[color={color}]{text}[/color]\n\n"
        self.scroll.scroll_y = 0

    def open_settings(self, instance):
        from core.activity import register_interaction
        register_interaction()
        SettingsPopup(self.config_data, lambda: None).open()

    def send_message(self, instance):
        text = self.text_input.text.strip()
        if not text:
            return
            
        self.text_input.text = ""
        self.append_chat(f"You: {text}", "88ff88")
        self.state = "busy"
        
        from core.activity import register_interaction
        register_interaction()
        
        def background_chat():
            from core.bonding import update_bond
            new_bond = update_bond(True)
            response = self.sdk.send_chat_message(text)
            Clock.schedule_once(lambda dt: self.receive_message(response, new_bond))
            
        threading.Thread(target=background_chat, daemon=True).start()

    def receive_message(self, response, new_bond):
        if int(new_bond) % 10 == 0 and int(new_bond) > 0:
            self.state = "celebrate"
            Clock.schedule_once(lambda dt: self.reset_state(), 4)
        else:
            self.state = "idle"
            
        # Every time the pet receives a message, sync its latest soul data to the cloud
        current_soul = safe_load("data/soul.json", self.soul)
        self.sdk.sync_companion_state(current_soul)
            
        self.append_chat(f"Daemon: {response}", "d0d0ff")
        
        # Speak the response using Android TTS
        from core.voice import speak_text
        speak_text(response)
        
    def reset_state(self):
        self.state = "idle"

    def on_pause(self):
        if hasattr(self, 'session_start'):
            from datetime import datetime
            from memory.projects import log_session
            log_session("engagement", self.session_start, datetime.now())
        return True

    def on_resume(self):
        from datetime import datetime
        self.session_start = datetime.now()
