# 🤖 Agentic AI Sidekick

An autonomous, locally-running AI Sidekick built with **Python, LangGraph, and Arduino**. 
This project bridges the gap between digital Large Language Models and physical workflow environments, allowing your agent to interact with the real world, your browser, and your local OS.

## ✨ Features

- **💡 Physical Hardware Control (Arduino):** Controls a custom Arduino Uno setup over USB to physically toggle desk lighting or engage a visual Pomodoro LED timer.
- **📄 Document Parsing (Unstructured):** Reads and extracts text from local lecture slides (`.pptx`) and files to generate highly formatted study notes.
- **🌐 Browser Automation (Playwright):** Hijacks a local browser window to autonomously navigate to YouTube and search for video tutorials based on your queries.
- **🔔 Native OS Reminders (Linux `at`):** Taps into the Linux scheduling daemon to push native desktop notifications and reminders to the host system.

## 🛠️ Tech Stack

- **Framework:** `LangChain` / `LangGraph`
- **LLM Routing:** OpenRouter (Claude 4.6 Sonnet)
- **UI:** `Rich` (Interactive Terminal UI)
- **Hardware Integration:** Python `pyserial` ↔️ C++ (`Arduino Uno R4 WiFi`)
- **Browser Control:** `playwright`
- **OS Integration:** Python `subprocess` ↔️ Linux `at` & `notify-send`

## 🚀 Setup & Installation

### 1. Python Environment
```bash
# Clone the repository
git clone https://github.com/revant-999/AISIDEKICK.git
cd AISIDEKICK

# Create and activate a Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
playwright install
```

### 2. Linux Dependencies (For Desktop Notifications)
If you're on Ubuntu/Debian, install the `at` daemon:
```bash
sudo apt update && sudo apt install at -y
sudo systemctl enable --now atd
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
OPENROUTER_API_KEY=your_openrouter_api_key
SERPER_API_KEY=your_serper_api_key
ARDUINO_PORT=/dev/ttyACM0
```

### 4. Hardware Setup (Arduino)
1. Wire an LED to **Pin 9** on your Arduino Uno.
2. Flash the `arduino_sidekick/arduino_sidekick.ino` sketch using the Arduino IDE.
3. Plug the Arduino into your computer via USB.

## 💻 Usage

Run the terminal interface:
```bash
python cli.py
```

Try asking your agent:
> *"Turn on the study light and set a Pomodoro timer for 25 minutes."*
> *"Read the presentation in my sandbox folder and generate concise study notes."*
> *"Open a YouTube search explaining Agentic AI."*
> *"Remind me to drink water in 10 minutes."*

---

*Connecting LLMs to the real world is the future. Feel free to fork and build your own tools into the sidekick!*
