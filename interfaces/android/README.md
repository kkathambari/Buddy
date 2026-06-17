# 👻 DevBuddy: Cross-Platform Coding Companion

**DevBuddy** is an interactive, cross-platform virtual pet and coding companion. Built as a dual-app ecosystem (Desktop + Mobile), it watches your productivity while you work, reacts to your coding activity, and talks to you using advanced Large Language Models (LLMs).

With DevBuddy, your desktop companion and your mobile pet are one and the same—synchronized in real time via the cloud.

---

## 🚀 Key Features

### 💻 Desktop App (`pet`)
- **Activity Detection**: Uses a low-overhead background listener (`pynput`) to track active window titles and keystrokes.
- **Productivity Analysis**: Automatically categorizes windows (e.g., Coding, Watching, Browsing, Chatting) and logs session durations.
- **Physics Engine**: Double-click to chat, drag-and-drop custom assets, or throw the pet around the screen with realistic gravity, friction, and dizziness reactions.
- **Voice Capabilities**: Interactive microphone button for Speech-to-Text (STT) input and Text-to-Speech (TTS) response.

### 📱 Android Mobile App (`android_pet`)
- **Native Mobile Experience**: Written using the Kivy framework for dynamic, mobile-friendly layouts.
- **Android Integration**: Native TTS implementation via `plyer` so your companion can talk to you on the go.
- **Portability**: Tailored build pipeline using Buildozer to compile the Python code directly into a native Android APK.

### 🔗 Soul Sync (Cloud Integration)
- **Firebase Sync**: Updates the pet's stats, bonding progress, energy, and traits to the cloud automatically.
- **3-Word Seed**: Sync your desktop pet with your Android app instantly using a secure, generated 3-word "Soul Seed" (similar to a crypto wallet seed).

---

## 🛠 System Architecture

```text
+-------------------+                      +-------------------+
|    DESKTOP APP    |                      |    ANDROID APP    |
|   (Tkinter GUI)   |                      |    (Kivy GUI)     |
+---------+---------+                      +---------+---------+
          |                                          |
          | (Pushes local stats)    (Syncs state)    |
          v                                          v
+--------------------------------------------------------------+
|                     FIREBASE CLOUD DATABASE                  |
|                    Stores: stats, energy, bond               |
+--------------------------------------------------------------+
```

---

## 📂 Project Structure

```text
claude-code-main/
│
├── pet/                       # Desktop Version
│   ├── main.py                # Main Entrypoint
│   ├── DevBuddy.bat           # Quick launcher & dependency installer
│   ├── requirements.txt       # Python Dependencies
│   ├── engine/                # Core simulation logic (decay, mood, LLM, etc.)
│   ├── ui/                    # Tkinter GUI code (desktop.py)
│   └── assets/                # Sprite animations (idle, walk, sleep, dizzy...)
│
└── android_pet/               # Android Version
    ├── main.py                # Main Entrypoint (Kivy starter)
    ├── buildozer.spec         # Android build configurations
    ├── build_apk.sh           # One-click Ubuntu/WSL dependency installer & builder
    ├── resume_build.sh        # WSL compilation resume script (fixes network drops)
    ├── requirements.txt       # Mobile development dependencies
    └── ui/                    # Kivy GUI (kivy_app.py)
```

---

## ⚙️ Desktop Setup & Installation

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) (Optional: Default local LLM provider. Install and run `ollama run llama3` or `ollama run deepseek-coder` before starting).

### Quick Start (Windows)
Double-click `DevBuddy.bat` in the `pet` directory. It will install all missing python packages and launch the app in the background.

### Manual Setup
1. Open your terminal in the `pet` directory:
   ```bash
   cd pet
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the desktop app:
   ```bash
   python main.py
   ```

---

## 📱 Android Setup & Compilation

### Prerequisites
- Linux or Windows Subsystem for Linux (WSL)
- Android Debug Bridge (ADB) installed on host

### One-Click APK Compilation
We provide automation scripts for compiles in WSL (Ubuntu):
1. Run the compilation script from the `android_pet` folder:
   ```bash
   cd android_pet
   bash build_apk.sh
   ```
2. The compiler will install SDKs, NDKs, and build dependencies, then output the compiled APK file into the `bin/` directory.

*Note: If the build gets interrupted or has network download drops, simply run `bash resume_build.sh` or double-click `Resume_Android_Build.bat` on Windows.*

---

## 💬 Configuration & AI Models

Right-click the desktop pet or click the settings icon `⚙` in the Android app to configure:
1. **AI Provider**: `ollama` (default local), `chatgpt`, `claude`, or `gemini`.
2. **API Keys**: Add your API key if using ChatGPT, Claude, or Gemini.
3. **Soul Sync Seed**: View your 3-word seed or paste a seed from another device to synchronize them.
