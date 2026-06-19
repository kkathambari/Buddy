import tkinter as tk
import tkinter.simpledialog as sd
from PIL import Image, ImageTk
import os
import sys
import random
import time
from threading import Thread
from core.config import set_config, get_config
from sdk.client import ForgeSDK

# Resolve the asset/resource root directory
if getattr(sys, 'frozen', False):
    # In PyInstaller, data files like 'assets' are in sys._MEIPASS
    resource_root = sys._MEIPASS
else:
    # In development, it's the desktop interface root directory
    resource_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class DesktopPet:
    def __init__(self, config=None):
        if config is None:
            config = get_config()
            
        self.sdk = ForgeSDK()
        # Pre-authenticate if config details exist
        email = config.get("user_email")
        password = config.get("user_password")
        if email and password:
            self.sdk.login(email, password)
        if config.get("pet_cloud_id"):
            self.sdk.soul_seed = config["pet_cloud_id"]
            
        self.root = tk.Tk()
        self.root.title("DevBuddy")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        self.root.config(bg="white")
        self.root.attributes("-transparentcolor", "white")

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self.label = tk.Label(self.root, bg="white")
        self.label.pack()

        self.config = config
        self.anim_delay = config.get("animation_speed", 0.3)

        self.x = 300
        self.y = 300
        self.vx = 0
        self.vy = 0
        self.gravity = 1
        self.friction = 0.9

        self.root.geometry(f"+{self.x}+{self.y}")

        self.state = "idle"
        self.frame_index = 0
        self.running = True

        self.animations = {
            "idle": self.load_frames("assets/idle"),
            "walk": self.load_frames("assets/walk"),
            "sleep": self.load_frames("assets/sleep"),
            "fall": self.load_frames("assets/fall"),
            "busy": self.load_frames("assets/busy"),
            "dizzy": self.load_frames("assets/dizzy"),
            "celebrate": self.load_frames("assets/celebrate"),
            "heart": self.load_frames("assets/heart")
        }

        # Start loops
        Thread(target=self.animate_loop, daemon=True).start()
        Thread(target=self.move_loop, daemon=True).start()
        Thread(target=self.physics_loop, daemon=True).start()

        # Interactions
        self.label.bind("<Button-1>", self.on_click)
        self.label.bind("<ButtonRelease-1>", self.on_release)
        self.label.bind("<Double-Button-1>", self.on_click)
        self.label.bind("<B1-Motion>", self.drag)
        self.label.bind("<Button-3>", self.open_settings) # Right click for settings

        try:
            import windnd
            windnd.hook_dropfiles(self.root, func=self.on_drop_files)
        except ImportError:
            pass

    def update_bubble_position(self):
        if hasattr(self, 'bubble_win') and self.bubble_win.winfo_exists():
            self.bubble_win.geometry(f"200x120+{int(self.x)}+{int(self.y - 140)}")
        if hasattr(self, 'full_chat_win') and self.full_chat_win.winfo_exists():
            self.full_chat_win.geometry(f"280x300+{int(self.x)}+{int(self.y - 320)}")

    def open_comic_bubble(self, text="..."):
        if hasattr(self, 'full_chat_win') and self.full_chat_win.winfo_exists():
            self.type_message_full(text)
            return

        if not hasattr(self, 'bubble_win') or not self.bubble_win.winfo_exists():
            self.bubble_win = tk.Toplevel(self.root)
            self.bubble_win.overrideredirect(True)
            self.bubble_win.attributes("-topmost", True)
            self.bubble_win.config(bg="white")
            
            frame = tk.Frame(self.bubble_win, bg="#ffffff", bd=2, relief="solid")
            frame.pack(fill="both", expand=True)

            self.bubble_label = tk.Label(frame, text=text, bg="#ffffff", fg="#000000", wraplength=180, font=("Comic Sans MS", 10), justify="center")
            self.bubble_label.pack(padx=10, pady=10, expand=True)
            input_frame = tk.Frame(self.bubble_win, bg="white")
            input_frame.pack(fill=tk.X, padx=5, pady=(0,5))
            
            self.bubble_entry = tk.Entry(input_frame, bg="#f0f0f0", relief=tk.FLAT, font=("Arial", 9))
            self.bubble_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            self.bubble_entry.bind("<Return>", self.send_bubble_reply)
            
            self.mic_btn = tk.Button(input_frame, text="🎙️", bg="white", relief=tk.FLAT, bd=0, command=self.on_mic_click)
            self.mic_btn.pack(side=tk.RIGHT, padx=(2,0))
            
            frame.bind("<Double-Button-1>", self.expand_to_full_chat)
            self.bubble_label.bind("<Double-Button-1>", self.expand_to_full_chat)

            self.bubble_win.geometry(f"200x120+{int(self.x)}+{int(self.y - 140)}")
            self.bubble_entry.focus()
        else:
            self.bubble_label.config(text=text)

    def speak(self, text):
        bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.attributes("-topmost", True)
        
        bubble.config(bg="#f0f0f0")
        label = tk.Label(bubble, text=text, bg="#f0f0f0", wraplength=200, font=("Arial", 10))
        label.pack(padx=8, pady=8)

        bubble.geometry(f"+{int(self.x)}+{int(self.y - 80)}")
        self.root.after(3000, bubble.destroy)

    def send_bubble_reply(self, event=None):
        user_input = self.bubble_entry.get().strip()
        if not user_input: return
        
        if user_input.lower() in ["quit", "exit"]:
            self.close_app()
            return

        self.bubble_entry.delete(0, "end")
        if not hasattr(self, 'chat_history'): self.chat_history = []
        self.chat_history.append(("user", user_input))
        
        self.bubble_label.config(text="...")
        Thread(target=self.process_reply_async, args=(user_input,), daemon=True).start()

    def expand_to_full_chat(self, event=None):
        if hasattr(self, 'bubble_win') and self.bubble_win.winfo_exists():
            self.bubble_win.destroy()
        self.open_full_chat()

    def open_full_chat(self, event=None):
        if hasattr(self, 'full_chat_win') and self.full_chat_win.winfo_exists():
            self.full_chat_win.destroy()

        self.full_chat_win = tk.Toplevel(self.root)
        self.full_chat_win.overrideredirect(True)
        self.full_chat_win.attributes("-topmost", True)
        self.full_chat_win.geometry(f"280x300+{int(self.x)}+{int(self.y - 320)}")

        main_frame = tk.Frame(self.full_chat_win, bg="#1e1e1e", bd=2, relief="ridge")
        main_frame.pack(fill="both", expand=True)

        title_bar = tk.Frame(main_frame, bg="#2d2d30", height=25)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)

        title_lbl = tk.Label(title_bar, text="DevBuddy Chat", bg="#2d2d30", fg="white", font=("Segoe UI", 9, "bold"))
        title_lbl.pack(side="left", padx=5)

        btn_exit = tk.Button(title_bar, text="✕", bg="#e81123", fg="white", bd=0, width=3, command=self.close_app)
        btn_exit.pack(side="right")

        btn_min = tk.Button(title_bar, text="—", bg="#2d2d30", fg="white", bd=0, width=3, command=self.minimize_to_bubble)
        btn_min.pack(side="right")

        self.chat_text = tk.Text(main_frame, bg="#1e1e1e", fg="#e0e0e0", font=("Segoe UI", 10), wrap="word", state="normal", bd=0)
        self.chat_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.chat_text.tag_config("user", foreground="#88ff88", justify="right")
        self.chat_text.tag_config("pet", foreground="#d0d0ff", justify="left")
        
        if not hasattr(self, 'chat_history'): self.chat_history = []
        for sender, msg in self.chat_history:
            self.chat_text.insert("end", msg + "\n\n", sender)
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

        self.full_entry = tk.Entry(main_frame, bg="#2a2a2a", fg="#e0e0e0", insertbackground="white", relief="flat", font=("Segoe UI", 10))
        self.full_entry.pack(fill="x", padx=5, pady=5)
        self.full_entry.bind("<Return>", self.send_full_reply)
        self.full_entry.focus()

    def minimize_to_bubble(self):
        if hasattr(self, 'full_chat_win'):
            self.full_chat_win.destroy()
        last_msg = "I'm listening..."
        if hasattr(self, 'chat_history'):
            for sender, msg in reversed(self.chat_history):
                if sender == "pet":
                    last_msg = msg
                    break
        self.open_comic_bubble(last_msg)

    def close_app(self):
        self.running = False
        self.root.quit()

    def type_message_full(self, text):
        self.chat_text.config(state="normal")
        self.chat_text.insert("end", text + "\n\n", "pet")
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

    def send_full_reply(self, event=None):
        user_input = self.full_entry.get().strip()
        if not user_input: return
        
        if user_input.lower() in ["quit", "exit"]:
            self.close_app()
            return

        self.full_entry.delete(0, "end")
        if not hasattr(self, 'chat_history'): self.chat_history = []
        self.chat_history.append(("user", user_input))

        self.chat_text.config(state="normal")
        self.chat_text.insert("end", user_input + "\n\n", "user")
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

        Thread(target=self.process_reply_async, args=(user_input,), daemon=True).start()

    def on_mic_click(self):
        self.mic_btn.config(fg="red", text="🔴")
        from core.voice import listen_to_voice
        
        def _on_transcribed(text):
            self.root.after(0, lambda: self.mic_btn.config(fg="black", text="🎙️"))
            if text:
                self.bubble_entry.delete(0, tk.END)
                self.bubble_entry.insert(0, text)
                self.send_bubble_reply()
                
        listen_to_voice(_on_transcribed)

    def process_reply_async(self, user_input):
        import time, random
        from core.bonding import update_bond
        from shared.storage import safe_load
        from core.cloud import sync_to_cloud
        
        time.sleep(random.uniform(0.5, 1.2))
        self.root.after(0, lambda: setattr(self, 'state', 'busy'))

        response = self.sdk.send_chat_message(user_input)
        new_bond = update_bond(True)

        current_soul = safe_load("data/soul.json", {})
        if current_soul:
            self.sdk.sync_companion_state(current_soul)

        time.sleep(random.uniform(0.8, 1.5))
        
        if int(new_bond) % 10 == 0 and int(new_bond) > 0:
            self.root.after(0, lambda: setattr(self, 'state', 'celebrate'))
            def revert():
                time.sleep(4)
                if getattr(self, 'state', 'idle') == 'celebrate':
                    setattr(self, 'state', 'idle')
            Thread(target=revert, daemon=True).start()
        else:
            self.root.after(0, lambda: setattr(self, 'state', 'idle'))
            
        self.root.after(0, lambda: self.on_reply_received(response))

    def get_response(self, user_input):
        return self.sdk.send_chat_message(user_input)

    def on_reply_received(self, response):
        if "[ANIMATION: confused]" in response or response == "I’m here… just a little slow right now.":
            # Set animation state to dizzy (confusion)
            self.state = "dizzy"
            def recover():
                time.sleep(5)
                if self.state == "dizzy":
                    self.state = "idle"
            Thread(target=recover, daemon=True).start()
            response = "I'm having trouble connecting to my thoughts right now. Let's try again in a moment."

        if not hasattr(self, 'chat_history'): self.chat_history = []
        self.chat_history.append(("pet", response))
        
        # Trigger Voice Output (TTS)
        try:
            from core.voice import speak_text
            speak_text(response)
        except Exception:
            pass
        
        if hasattr(self, 'full_chat_win') and self.full_chat_win.winfo_exists():
            self.type_message_full(response)
        else:
            self.open_comic_bubble(response)

    def open_settings(self, event=None):
        name = sd.askstring("Settings", "Pet Name:", initialvalue=self.config.get("pet_name", "Buddy"))
        if name:
            set_config("pet_name", name)
            self.config["pet_name"] = name

        speed = sd.askfloat("Settings", "Animation Speed (0.2-0.5):", initialvalue=self.config.get("animation_speed", 0.3))
        if speed:
            set_config("animation_speed", speed)
            self.anim_delay = speed
            self.config["animation_speed"] = speed

        provider = sd.askstring("Settings", "AI Provider (ollama, chatgpt, claude, gemini):", initialvalue=self.config.get("ai_provider", "ollama"))
        if provider and provider.lower() in ["ollama", "chatgpt", "claude", "gemini"]:
            provider = provider.lower()
            set_config("ai_provider", provider)
            self.config["ai_provider"] = provider
            
            if provider != "ollama":
                api_key = sd.askstring("Settings", f"{provider.capitalize()} API Key:", initialvalue=self.config.get(f"{provider}_api_key", ""))
                if api_key is not None:
                    set_config(f"{provider}_api_key", api_key)
                    self.config[f"{provider}_api_key"] = api_key
                    
        # Generate Soul Seed if it doesn't exist
        current_seed = self.config.get("pet_cloud_id", "")
        if not current_seed or current_seed == "default_pet":
            try:
                from core.auth import generate_soul_seed
                current_seed = generate_soul_seed()
                set_config("pet_cloud_id", current_seed)
                self.config["pet_cloud_id"] = current_seed
            except Exception:
                current_seed = "error-generating-seed"
                
        import tkinter.messagebox as mb
        mb.showinfo("Soul Seed", f"Your unique Soul Seed is:\n\n{current_seed}\n\nType this 3-word phrase into your Android app to link your pet!")
            
        pet_id = sd.askstring("Soul Sync", "Enter a 3-word Soul Seed to link to another pet (leave as is to keep current):", initialvalue=current_seed)
        if pet_id is not None and pet_id.strip() != "":
            set_config("pet_cloud_id", pet_id.strip())
            self.config["pet_cloud_id"] = pet_id.strip()
            
        restore = sd.askstring("Cloud Restore", "Type 'yes' to download Cloud Save right now, or leave blank:")
        if restore and restore.lower().strip() == 'yes':
            cloud_soul = self.sdk.get_companion_state()
            if cloud_soul:
                safe_save("data/soul.json", cloud_soul)
                self.speak("Cloud memory restored! I remember everything.")
            else:
                self.speak("Failed to find cloud memory.")

    def load_frames(self, folder):
        frames = []
        if os.path.isabs(folder):
            actual_folder = folder
        else:
            actual_folder = os.path.join(resource_root, folder)

        if not os.path.exists(actual_folder):
            return frames
        for file in sorted(os.listdir(actual_folder)):
            if file.endswith(".png") or file.endswith(".gif"):
                img = Image.open(os.path.join(actual_folder, file))
                frames.append(ImageTk.PhotoImage(img))
        return frames

    def on_drop_files(self, files):
        if files:
            path = files[0].decode('gbk', errors='ignore') # windnd returns bytes
            if os.path.isdir(path):
                self.load_custom_character(path)
            elif os.path.isfile(path) and path.lower().endswith(".pdf"):
                self.handle_pdf_drop(path)

    def handle_pdf_drop(self, path):
        self.open_full_chat()
        self.type_message_full(f"Uploaded and started studying: {os.path.basename(path)}")
        self.send_full_reply_text(f"study pdf: {path}")

    def send_full_reply_text(self, text):
        if not hasattr(self, 'chat_history'): self.chat_history = []
        self.chat_history.append(("user", text))
        if hasattr(self, 'chat_text') and self.chat_text.winfo_exists():
            self.chat_text.config(state="normal")
            self.chat_text.insert("end", text + "\n\n", "user")
            self.chat_text.see("end")
            self.chat_text.config(state="disabled")
        Thread(target=self.process_reply_async, args=(text,), daemon=True).start()

    def load_custom_character(self, folder):
        self.animations["idle"] = self.load_frames(os.path.join(folder, "idle")) or self.animations["idle"]
        self.animations["walk"] = self.load_frames(os.path.join(folder, "walk")) or self.animations["walk"]
        self.animations["sleep"] = self.load_frames(os.path.join(folder, "sleep")) or self.animations["sleep"]
        self.animations["fall"] = self.load_frames(os.path.join(folder, "fall")) or self.animations["fall"]
        self.animations["busy"] = self.load_frames(os.path.join(folder, "busy")) or self.animations.get("busy", [])
        self.animations["dizzy"] = self.load_frames(os.path.join(folder, "dizzy")) or self.animations.get("dizzy", [])
        self.animations["celebrate"] = self.load_frames(os.path.join(folder, "celebrate")) or self.animations.get("celebrate", [])
        self.animations["heart"] = self.load_frames(os.path.join(folder, "heart")) or self.animations.get("heart", [])
        self.state = "idle"

    def animate_loop(self):
        while self.running:
            frames = self.animations.get(self.state, [])
            if frames:
                self.frame_index = self.frame_index % len(frames)
                try:
                    self.label.config(image=frames[self.frame_index])
                except Exception:
                    pass
                self.frame_index = (self.frame_index + 1) % len(frames)

            time.sleep(self.anim_delay)

    def keep_in_bounds(self):
        self.x = max(0, min(self.x, self.screen_w - 100))
        self.y = max(0, min(self.y, self.screen_h - 100))

    def move_loop(self):
        while self.running:
            if self.state == "sleep":
                time.sleep(2)
                continue

            self.vx += random.randint(-3, 3)

            if self.state not in ["fall", "sleep"] and abs(self.vx) > 0.5:
                self.state = "walk"
            elif self.state not in ["fall", "sleep"] and abs(self.vx) <= 0.5:
                self.state = "idle"

            time.sleep(2)

    def physics_loop(self):
        while self.running:
            self.vy += self.gravity
            self.x += self.vx
            self.y += self.vy

            ground = self.screen_h - 220

            if self.y >= ground:
                self.y = ground
                self.vy = 0
                if self.state == "fall":
                    self.state = "idle"

            if self.x <= 0:
                self.x = 0
                self.vx = 0
                self.vy *= 0.5
            elif self.x >= self.screen_w - 100:
                self.x = self.screen_w - 100
                self.vx = 0
                self.vy *= 0.5

            if self.vy > 5:
                self.state = "fall"

            self.vx *= self.friction

            try:
                self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
                self.update_bubble_position()
            except Exception:
                pass

            time.sleep(0.03)

    def update_state_from_energy(self, energy):
        if self.state == "fall":
            return
        if energy < 10:
            self.state = "sleep"
        elif energy < 40:
            self.state = "idle"
        else:
            self.state = "walk"

    def update_mood(self, mood):
        if self.state in ["fall", "sleep"]:
            return
        if mood == "happy":
            self.state = "walk"
        elif mood == "sad":
            self.state = "idle"
        elif mood == "dead":
            self.state = "sleep"

    def drag(self, event):
        old_x = self.x
        old_y = self.y
        self.x = event.x_root
        self.y = event.y_root
        self.vx = self.x - old_x
        self.vy = self.y - old_y
        self.state = "idle"
        try:
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
            self.update_bubble_position()
        except Exception:
            pass

    def on_release(self, event):
        if abs(self.vx) > 30 or abs(self.vy) > 30:
            self.state = "dizzy"
            def recover():
                import time
                time.sleep(3)
                if self.state == "dizzy":
                    self.state = "idle"
            Thread(target=recover, daemon=True).start()

    def on_click(self, event):
        if hasattr(self, 'bubble_win') and self.bubble_win.winfo_exists():
            self.expand_to_full_chat()
        else:
            self.open_comic_bubble("Yes?")



    def run(self):
        self.root.mainloop()
