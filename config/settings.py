"""
Configuration settings for Mobile QA Multi-Agent System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
SCREENSHOTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model Configuration
MODEL_NAME = "gemini-2.5-flash"  # Free tier model

# ADB Configuration
ADB_PATH = os.getenv("ADB_PATH", "adb")  # Uses system adb by default

# Emulator Configuration
EMULATOR_SERIAL = os.getenv("EMULATOR_SERIAL", "emulator-5554")

# Screen Configuration (Pixel 8 Pro)
SCREEN_WIDTH = 1344
SCREEN_HEIGHT = 2992

# Agent Configuration
MAX_STEPS = 20  # Maximum steps per test case
SCREENSHOT_DELAY = 2.0  # Seconds to wait after action before screenshot
ACTION_DELAY = 1.0  # Seconds between actions (increased for reliability)

# Logging
LOG_LEVEL = "INFO"
