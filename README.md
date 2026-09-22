# JARVIS: Modular Desktop AI Voice Assistant

A production-grade, modular, and extensible desktop AI voice assistant for Windows (with macOS/Linux cross-compatibility) built in Python.

JARVIS features real-time wake word detection, low-latency speech transcription, high-fidelity neural text-to-speech, multi-provider LLM function-calling (Gemini, OpenAI, Ollama), and deep native OS automation.

---

## 🌟 Core Architecture & Capabilities

```
                       [ Microphone Stream ]
                                 │
                     [ Wake Word Listener ]
                   (openWakeWord / "Jarvis")
                                 │
                    [ Speech-to-Text (STT) ]
                (faster-whisper / Google STT)
                                 │
                   [ Function-Calling Router ]
                 (Gemini / OpenAI / Ollama / Rules)
                                 │
     ┌──────────────┬────────────┼────────────┬──────────────┐
     ▼              ▼            ▼            ▼              ▼
[ System &     [ Apps &     [ Browser    [ Media &      [ Persona
  Power ]        Files ]    Automation ]   Music ]        Chat ]
     │              │            │            │              │
     └──────────────┴────────────┼────────────┴──────────────┘
                                 │
                   [ Text-to-Speech (TTS) ]
                 (edge-tts Neural / pyttsx3)
                                 │
                         [ Audio Output ]
```

### Key Subsystems:
- **Wake Word Detection (`core/wake_word.py`):** Always-on listener powered by `openWakeWord` or energy-based keyword activation.
- **Speech-to-Text (`core/listener.py`):** Low-latency local transcription via `faster-whisper` (`base.en` / `tiny.en` int8 quantized) with dynamic silence detection and `speech_recognition` fallback.
- **Text-to-Speech (`core/speaker.py`):** Low-latency British Butler neural voice using `edge-tts` (`en-GB-RyanNeural`) and offline `pyttsx3` fallback.
- **Reasoning / Function-Calling Engine (`core/router.py`, `core/llm.py`):** Dispatches commands to registered tools using Google Gemini, OpenAI, Ollama, or an offline rule engine.
- **Safety Interceptor:** Voice/text confirmation guards for destructive actions (e.g. shutdown, reboot, sleep).

---

## 📁 Project Layout

```
jarvis-assistant/
├── config/
│   ├── config.yaml          # Core settings (voices, sensitivity, directories, models)
│   └── config_loader.py     # YAML configuration manager
├── core/
│   ├── __init__.py
│   ├── wake_word.py         # Wake word listener (openWakeWord / Audio Stream)
│   ├── listener.py          # STT pipeline (faster-whisper + SpeechRecognition)
│   ├── speaker.py           # TTS pipeline (edge-tts + pyttsx3 offline fallback)
│   ├── llm.py               # LLM interface (Gemini, OpenAI, Ollama, Rule Engine)
│   ├── router.py            # Function-calling dispatcher & confirmation manager
│   └── state.py             # Conversation history & pending action tracker
├── modules/
│   ├── __init__.py
│   ├── base.py              # BaseTool class with @tool decorator & JSON schema generator
│   ├── system.py            # Power, volume (PyCAW), battery & CPU metrics, lock
│   ├── apps_and_files.py    # Desktop app launcher (.lnk/registry), fuzzy file search
│   ├── browser.py           # Web search, URL navigation, tab controls (PyAutoGUI)
│   ├── media.py             # YouTube playback, Spotify integration, media keys
│   └── chat.py              # Conversational persona & fallback responses
├── tests/
│   ├── test_modules.py      # Unit tests for tool modules
│   └── test_router.py       # Unit tests for router, state, schemas, rule engine
├── .env.example             # API keys template
├── requirements.txt         # All categorized dependencies
├── main.py                  # CLI entrypoint (--voice, --text, --test)
└── README.md                # Documentation and setup guide
```

---

## 🚀 Quick Setup & Installation

### Step 1: Create and Activate a Virtual Environment

```bash
# Navigate into the project folder
cd C:\Users\hp\.gemini\antigravity-ide\scratch\jarvis-assistant

# Create virtual environment (Python 3.10 - 3.14)
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

> [!NOTE]
> On Windows, if `pyaudio` compilation fails, you can install the pre-compiled wheel using:
> `pip install pipwin && pipwin install pyaudio` or `pip install PyAudio`

### Step 3: Configure API Keys (Optional but Recommended)

Copy the `.env.example` file to `.env` and insert your preferred API key:

```bash
copy .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
# or
OPENAI_API_KEY=your_openai_api_key_here
```

*(If no API key is provided, JARVIS will seamlessly use its built-in offline rule engine!)*

---

## 🎙️ Running JARVIS

### 1. Interactive Text Mode (Quick Test & Debug)
Run without needing a microphone:
```bash
python main.py --text
```

### 2. Full Voice Mode (Hands-Free Wake Word)
```bash
python main.py --voice
```
Say **"Jarvis"** to activate, then state your command!

### 3. Diagnostic Self-Test
Run a self-test of all registered tools and routing engines:
```bash
python main.py --test
```

### 4. Run Unit Test Suite
```bash
python -m unittest discover tests
```

---

## 🗣️ Supported Commands & Voice Prompts

| Subsystem | Voice Command Examples |
| :--- | :--- |
| **System & Hardware** | • *"What is my battery and CPU status?"*<br>• *"Lock the computer"*<br>• *"Set volume to 60 percent"*<br>• *"Mute volume"* / *"Unmute volume"*<br>• *"Shut down the computer"* *(Asks for voice confirmation)*<br>• *"Restart system"* *(Asks for voice confirmation)* |
| **Applications & Files** | • *"Launch Chrome"* / *"Open VS Code"* / *"Open Calculator"*<br>• *"Open Downloads folder"* / *"Open Documents"*<br>• *"Search and open file budget.xlsx"* |
| **Web & Browser** | • *"Search Google for Python async tutorials"*<br>• *"Search YouTube for space exploration"*<br>• *"Open github.com"*<br>• *"Close active tab"* / *"Next tab"* |
| **Media & Music** | • *"Play synthwave on YouTube"*<br>• *"Play Bohemian Rhapsody on Spotify"*<br>• *"Pause music"* / *"Resume playback"*<br>• *"Next track"* / *"Previous track"* |
| **General Conversation**| • *"Hello Jarvis, how are you today?"*<br>• *"Explain how quantum computing works in two sentences"* |

---

## 🛠️ Adding Custom Tools / Modules

Creating and registering new tools is effortless. Simply use the `@tool` decorator in any module:

```python
# modules/weather.py
from modules.base import tool, ToolResult
import requests

@tool(
    name="get_weather",
    description="Get current weather forecast for a specified city.",
    module_name="weather"
)
def get_weather(city: str) -> ToolResult:
    # Your logic here
    return ToolResult(success=True, message=f"The weather in {city} is 22 degrees Celsius and sunny.")
```

The router will **automatically** extract the docstring and argument types, generate the standard JSON Schema, and register it for function calling!
