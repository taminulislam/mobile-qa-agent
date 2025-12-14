# 🤖 Mobile QA Multi-Agent System

A production-ready multi-agent system for automated mobile QA testing of the Obsidian app on Android, built with Google's Agent Development Kit (ADK) and Gemini.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Google ADK](https://img.shields.io/badge/Google-ADK-green?logo=google)
![Gemini](https://img.shields.io/badge/Gemini-2.0-orange)
![Android](https://img.shields.io/badge/Android-API%2034+-brightgreen?logo=android)

## 📋 Overview

This project implements a **Supervisor-Planner-Executor** multi-agent architecture to execute natural language QA test cases on the Obsidian mobile app running in an Android emulator.

### Key Features

- ✅ **Multi-Agent Architecture**: Supervisor, Planner, and Executor agents working in coordination
- ✅ **Vision-Based Testing**: Uses Gemini's vision capabilities to analyze screenshots
- ✅ **Natural Language Test Cases**: Write tests in plain English
- ✅ **Accurate Reporting**: Correctly identifies passing and failing tests
- ✅ **Reasoning Loop**: Distinguishes between step failures and test assertion failures
- ✅ **Modular Design**: Easy to swap LLM models or add new tools

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SUPERVISOR AGENT                         │
│  • Orchestrates test execution                               │
│  • Manages agent coordination                                │
│  • Logs final results (Pass/Fail)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   PLANNER AGENT     │       │   EXECUTOR AGENT    │
│ • Analyzes screen   │◄─────►│ • Executes ADB      │
│ • Decides actions   │       │   commands          │
│ • Uses Gemini       │       │ • Captures screens  │
└─────────────────────┘       └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Android Studio with AVD Manager
- Android Emulator (API 34+, Google Play)
- Obsidian APK installed on emulator
- Gemini API Key (free from [Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mobile-qa-agent.git
   cd mobile-qa-agent
   ```

2. **Create and activate conda environment**
   ```bash
   conda create -n mobile-qa python=3.11 -y
   conda activate mobile-qa
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Start the Android emulator**
   ```bash
   # Windows
   & "$env:ANDROID_HOME\emulator\emulator.exe" -avd YourAVDName -no-snapshot
   ```

6. **Run the tests**
   ```bash
   python main.py --demo
   ```

## 📖 Usage

```bash
# List all available tests
python main.py --list

# Run demo tests (4 tests: 2 pass, 2 fail)
python main.py --demo

# Run all tests
python main.py --all

# Run a specific test
python main.py --test test_create_vault
```

## 📝 Test Cases

| Test Name | Description | Expected |
|-----------|-------------|----------|
| `test_create_vault` | Create a new vault named 'InternVault' | ✅ PASS |
| `test_create_note` | Create note titled 'Meeting Notes' | ✅ PASS |
| `test_search_functionality` | Search for 'Meeting' in notes | ✅ PASS |
| `test_toggle_dark_mode` | Toggle dark/light theme | ✅ PASS |
| `test_appearance_icon_red` | Verify Appearance icon is red | ❌ FAIL |
| `test_print_to_pdf` | Find 'Print to PDF' button | ❌ FAIL |
| `test_enable_calendar_plugin` | Enable 'Calendar View' plugin | ❌ FAIL |

## 📁 Project Structure

```
mobile-qa-agent/
├── agents/
│   ├── planner.py      # Analyzes screenshots, plans actions
│   ├── executor.py     # Executes ADB commands
│   └── supervisor.py   # Orchestrates tests, logs results
├── tools/
│   └── adb_tools.py    # ADB interaction utilities
├── test_cases/
│   └── obsidian_tests.py  # Test case definitions
├── config/
│   └── settings.py     # Configuration
├── utils/
│   └── logger.py       # Logging utilities
├── main.py             # Entry point
├── report.md           # Framework decision memo
├── requirements.txt
└── README.md
```

## 🎥 Demo Video

[Link to demo video showing the agent in action]

## 📊 Results

The system correctly identifies:
- ✅ **Passing tests**: Successfully creates vaults, notes, and navigates the app
- ❌ **Failing tests**: Accurately reports missing features (Print to PDF) and incorrect assertions (icon color)

## 🔧 Configuration

Edit `config/settings.py` to customize:
- `MAX_STEPS`: Maximum steps per test (default: 20)
- `SCREENSHOT_DELAY`: Wait time after actions (default: 1.5s)
- `MODEL_NAME`: Gemini model to use (default: gemini-2.0-flash)

## 📜 Framework Decision

See [report.md](report.md) for the detailed framework analysis comparing Google ADK vs Simular Agent S3.

**TL;DR**: Google ADK was chosen for its native multi-agent support, free Gemini integration, and simpler setup compared to Agent S3's requirement for additional grounding models.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

---

Built with ❤️ using [Google ADK](https://github.com/google/adk-python) and [Gemini](https://ai.google.dev/)
