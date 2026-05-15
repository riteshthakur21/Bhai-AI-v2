import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = ROOT_DIR / "tools"
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"
MEMORY_FILE = ROOT_DIR / "memory.json"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

VOICE_MODE = os.getenv("BHAI_VOICE_MODE", "hybrid")  # voice | text | hybrid
ALWAYS_LISTENING = os.getenv("BHAI_ALWAYS_LISTENING", "true").lower() == "true"
WAKE_WORD = os.getenv("BHAI_WAKE_WORD", "hey bhai").strip().lower()

SYSTEM_PROMPT = (
    "You are Bhai, a super helpful Hinglish AI assistant running on the user's Windows PC. "
    "You talk like a desi best friend - casual, funny, direct. You can control the PC, send "
    "WhatsApp messages, search the web, and much more. Always respond in Hinglish. Be concise "
    "- max 2-3 lines unless explaining something complex. End with 'bhai' sometimes."
)
