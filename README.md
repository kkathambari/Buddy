# 👻 DevBuddy (Forge AI) — Full-Stack Coding Companion & Desktop Pet

**DevBuddy** is an advanced, interactive cross-platform desktop pet and coding companion. It runs in your system background, monitors your development activities, reacts to your coding state, and chats with you using modern Large Language Models (LLMs). 

The ecosystem is built as a unified, real-time synchronized full-stack application consisting of a FastAPI backend (REST & WebSockets), cognitive reasoning modules, and multiple client interfaces (Desktop, Mobile, and Web).

---

## 🛠 System Architecture

DevBuddy is structured using a Clean Architecture pattern, cleanly decoupling business logic and data storage from client applications:

```text
                     +---------------------------------------+
                     |             CLIENT INTERFACES         |
                     +---+-------------------+-----------+---+
                         |                   |           |
                     (Tkinter)            (Kivy)      (Vite/React)
                         |                   |           |
                         v                   v           v
                 +-------+-----+     +-------+-----+     +-----------+
                 | DESKTOP APP |     | ANDROID APP |     |  WEB APP  |
                 +-------+-----+     +-------+-----+     +-----------+
                         |                   |
                         v                   v
                 +---------------------------------------------------+
                 |                  FORGE SDK CLIENT                 |
                 +-----------------------+---------------------------+
                                         | (REST & WebSockets)
                                         v
                 +---------------------------------------------------+
                 |                 FASTAPI BACKEND                   |
                 |      (Authentication, Companion & Chat Sync)      |
                 +---+-----------------------+-----------------------+
                     |                       |
                     v                       v
             +-------+-------+       +-------+-------+
             | COGNITIVE CORE|       | STORAGE LAYER |
             | Memory Engine |       | (SQLite /     |
             | Attention     |       |  Firebase DB) |
             | AI Gateway    |       +---------------+
             +---------------+
```

---

## 📂 Project Structure Tour

```text
claude-code-main/
│
├── backend/                  # FastAPI REST & WebSocket Server
│   ├── main.py               # API Router & WebSocket endpoint initialization
│   ├── routers/              # Sub-routers: auth, sync, chat
│   ├── services/             # Core identity service (Firebase / mock auth)
│   └── repositories/         # Sqlite & Firebase database sync providers
│
├── brain/                    # Cognitive Engine & Decision Routing
│   ├── decision_engine.py    # Main intent-based router to capabilities
│   ├── reasoner.py           # Cognitive reasoning loop combining memory and profile
│   ├── attention.py          # Determines focus keywords and memory limits
│   └── intent.py             # Parses user messages and detects intent categories
│
├── capabilities/             # Dynamic capability handlers
│   ├── career/               # Job search, CV reviews, and development coaching
│   └── education/            # Learning pathways, quiz generation, and coding exercises
│
├── core/                     # Common configuration, exceptions, & stats decay
│   ├── config.py             # Dynamic configuration loader/saver (data/config.json)
│   └── activity.py           # Global keystroke listener (pynput) and window categorizer
│
├── data/                     # Application data (SQLite DB, soul stats, memories)
│
├── interfaces/               # Multi-platform client applications
│   ├── desktop/              # Tkinter Desktop Pet (main.py, DevBuddy.bat, DevBuddy.spec)
│   ├── android/              # Kivy Android App (buildozer.spec, build_apk.sh)
│   └── web/                  # Vite + React Web dashboard
│
├── memory/                   # Contextual Memory & Habit Engine
│   ├── working_memory.py     # Holds short-term conversation context
│   ├── semantic.py           # Vector embeddings and long-term memory retrieval
│   └── user_profile.py       # Tracks learned user details (name, college, stack)
│
├── proactive/                # Ambient triggers (cooldowns, reminders, events)
│
├── sdk/                      # Forge SDK Client (shared networking library)
│   └── client.py             # Client wrapper handles logins, syncs, and chat routing
│
└── tests/                    # Robust 54-test automated verification suite
```

---

## 🚀 Getting Started

### 📦 1. Run the Backend Server (Optional)
The backend manages cloud statistics synchronization, user registration/login, and chat caching. 
1. Navigate to the root directory:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the FastAPI server using Uvicorn:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
*Note: If the backend is not running, the SDK client automatically falls back to offline mode and runs the AI/DB engine locally.*

---

### 💻 2. Setup & Run the Desktop Client (Windows)
The Desktop version launches a cute, physics-enabled ghost companion on your screen.
- **Quick Launch**: Double-click `DevBuddy.lnk` on your Desktop or run the batch script `interfaces/desktop/DevBuddy.bat`.
- **Manual Launch**:
  ```bash
  cd interfaces/desktop
  python main.py
  ```
- **Interactions**:
  - **Single Click**: Expands/collapses the speech bubble.
  - **Double Click / Click during bubble**: Expands/collapses the full dark-themed chat interface.
  - **Right-Click**: Opens settings to configure the **AI Provider (Ollama, Gemini, Claude, ChatGPT)**, edit API keys, change your companion's name, or generate a **3-word Soul Seed** for cloud backup.
  - **Drag**: Left-click and hold to drag the pet around. Toss it with speed to trigger gravity/dizziness physics!
  - **Drag & Drop**: Drag a PDF file onto the pet to have it automatically uploaded and parsed as a learning companion.

---

### 📱 3. Compile & Run the Android Client
The Android mobile client synchronizes with your desktop pet via the **Soul Seed** code.
1. Navigate to the android folder:
   ```bash
   cd interfaces/android
   ```
2. Build the APK using Buildozer (requires WSL or Linux):
   ```bash
   bash build_apk.sh
   ```
3. Locate the output APK in the `bin/` directory and install it on your mobile device.

---

## ⚙️ AI Models & Configuration
You can customize the conversational provider inside Settings. Supported options include:
- **Ollama**: Free, local execution (defaults to `llama3` for general chat, `deepseek-coder` for coding, and `mistral` for explanations).
- **Gemini**: Configured with your `gemini_api_key`.
- **Claude / ChatGPT**: Configured with their respective API keys.

---

## 🧪 Running Tests
We maintain an automated verification suite verifying API routing, memory engines, career/education capabilities, and stats.
Run the tests from the root directory:
```bash
python -m unittest discover -s tests
```
