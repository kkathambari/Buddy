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
├── events/                   # Global Event Bus Architecture
│   └── bus.py                # Pub/Sub event router linking hooks and components
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

## 🚀 Key Features & Pillars

### 💻 1. Desktop Pet Client (`interfaces/desktop/`)
- **Activity Monitoring**: Runs a low-overhead global background hook (`pynput`) to classify your current activity based on active window title names:
  - **Coding**: IDEs (VS Code, PyCharm, IntelliJ, Vim).
  - **Studying**: PDF viewers, Acrobat Reader.
  - **Browsing**: Web browsers (Chrome, Edge, Brave).
  - **Watching**: Streaming services (YouTube, Netflix).
  - **Chatting**: Communication apps (Discord, Slack, Teams).
- **Struggle Detector**: Detects if you're stuck or struggling based on high key delete/backspace ratios (exceeding 40%), pause duration, and time spent on the active document without compiling/saving.
- **Physics Engine**: The pet falls, collides with the taskbar, and shows custom animations (`dizzy`) if dragged and thrown around the screen using realistic gravity and friction.
- **Voice Interactions**: Features integrated Speech-to-Text (`SpeechRecognition`) and Text-to-Speech (`pyttsx3`) for fully hands-free conversations.
- **Drag & Drop Loading**: Drop a PDF file directly onto the pet to stage and process it as custom learning context.

### 📱 2. Android Mobile App (`interfaces/android/`)
- **Native Kivy Frontend**: Multi-touch responsive layouts tailored for mobile dimensions.
- **Background Syncing**: Keeps mobile pet attributes (bonding levels, hunger, energy) updated using mobile-native synchronization.
- **Automated Packaging**: Includes complete `buildozer.spec` and automation shell scripts (`build_apk.sh`, `resume_build.sh`) to download NDK/SDK toolchains and package python code into an installable `.apk` file.

### 🌐 3. Web Companion Dashboard (`interfaces/web/`)
- **React Frontend**: Modern Vite + React single-page app utilizing styling systems.
- **Analytics Visualization**: Tracks your historical productivity charts, coding hours, study milestones, and companion bonding levels.

---

## 🧠 Cognitive Engine (The Brain)

DevBuddy features a decentralized AI reasoning process that interprets inputs, manages memories, and determines reactions:

### A. Intent Classifier (`brain/intent.py`)
Matches inputs to pre-defined categories (`GREETING`, `SYSTEM_COMMAND`, `PRODUCTIVITY_QUERY`, `LEARNING`, `CAREER`, `MEMORY_QUERY`, `EMOTION`, `COMPANIONSHIP`).

### B. Attention Engine (`brain/attention.py`)
Computes an attention intensity score (from 0 to 1) based on the user's input and current dialog length. It extracts semantic keywords to govern what memories are relevant, scaling memory lookup limits dynamically.

### C. Cognitive Reasoner (`brain/reasoner.py`)
Assembles prompts dynamically by loading and merging:
1. Short-term dialog context from the **Working Memory**.
2. Structured demographic information from the **User Profile**.
3. Relevant historical snippets matched via the **Semantic Memory**.
4. Personality adjustments governed by your pet's current statistics.

### D. Pluggable Capabilities (`capabilities/`)
- **Education Handler**: Creates dynamic study schedules, runs sandboxed test environments, tracks quiz answers, and increases learning mastery.
- **Career Handler**: Advises on resume construction, performs mock interviews, and creates career milestone schedules.

---

## 🔗 Soul Sync: Cryptographic Device Pairing

Pairing your desktop pet with your Android app uses a **3-word Soul Seed** (similar to a BIP-39 cryptocurrency wallet seed):
1. **Generation**: The desktop app generates a randomized seed (e.g. `spectral-daemon-812`).
2. **Hashing**: The seed is cryptographically salted and hashed (`SHA-256`) to create a secure UUID (`companion_id`).
3. **Data Sync**:
   - The desktop pet pushes soul stats (energy, bonding levels, rarity) to the FastAPI server endpoint `/sync/{companion_id}`.
   - The Android client parses the same seed, hashes it locally, and fetches/syncs stats from the same backend endpoint.
   - Real-time updates (like message notifications and energy decay) are broadcasted to all connected clients via WebSocket channels (`/ws`).

---

## ⚙️ REST API Reference

| Endpoint | Method | Payload | Description |
| :--- | :--- | :--- | :--- |
| `/auth/login` | `POST` | `{email, password}` | Authenticates user credentials with Firebase or Mock auth. |
| `/auth/link` | `POST` | `{soul_seed}` | Maps the authenticated user profile to a companion ID. |
| `/sync/{id}` | `GET` | *None* | Downloads the latest companion soul stats (energy, bond, rarity). |
| `/sync/{id}` | `PUT` | `{name, energy, stats...}` | Saves/synchronizes companion state attributes. |
| `/chat` | `POST` | `{message, companion_id}` | Routes user messages to the Decision Engine and LLM. |
| `/health` | `GET` | *None* | Verifies database integration and AI provider status. |

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- Python 3.10+ installed on your host machine.
- [Ollama](https://ollama.com/) (Optional: Required if using local LLMs. Run `ollama run llama3` or `ollama run deepseek-coder`).

---

### 2. Startup FastAPI Backend
1. Open your terminal at the repository root and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the backend:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

---

### 3. Setup & Launch Desktop Pet
1. **Shortcut Launch**: Double-click the **`DevBuddy`** shortcut on your Desktop (or run `interfaces/desktop/DevBuddy.bat`).
2. **Manual CLI Launch**:
   ```bash
   cd interfaces/desktop
   python main.py
   ```
3. Right-click the pet to open **Settings** and configure your provider (`gemini`, `claude`, `chatgpt`, or `ollama`) and paste your API key.

---

### 4. Compile Kivy Android App
1. Navigate to the android interface directory:
   ```bash
   cd interfaces/android
   ```
2. Build the native package (requires Linux or WSL):
   ```bash
   bash build_apk.sh
   ```
*If a network drop occurs during compilation, resume the process by running `bash resume_build.sh`.*

---

### 5. Running Automated Tests
The repository contains a robust testing suite verifying Capabilites, APIs, SQL repositories, and Memory management.
Run them from the repository root:
```bash
python -m unittest discover -s tests
```
