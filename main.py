import json
import os
import sys
import time
from agent import BhaiAgent
from config import ALWAYS_LISTENING, VOICE_MODE
from health_check import run_all_checks
from tools.voice import listen, listen_for_wake_word, speak

HELP_TEXT = """
Bhai AI v2 — Commands:
━━━━━━━━━━━━━━━━━━━━━━
💬 Normal chat    → bas bol de
📱 WhatsApp       → "Rahul ko 'msg' bhej"  
🌐 Browser search → "DSA binary search dhundh"
🖥️  App open       → "Spotify khol"
📸 Screenshot     → "screenshot le"
👁️  Screen dekh   → "screen pe kya hai"
🔊 Volume         → "volume badhao/ghata/mute"
📋 Clipboard      → "clipboard mein copy kar"
🔒 System         → "PC lock karo/so ja"
📄 PDF            → "notes.pdf padh"
━━━━━━━━━━━━━━━━━━━━━━
'clear' → history reset
'memory' → teri info dekh
'status' → diagnostics chalana
'bye/exit' → band karo
"""


def _get_typed_fallback() -> str | None:
    try:
        typed = input("Type kar de bhai: ").strip()
        return typed or None
    except EOFError:
        return None
    except Exception as err:
        print(f"Arre bhai typed input mein issue: {err}")
        return None


def _get_user_input() -> str | None:
    global VOICE_MODE
    
    if VOICE_MODE == "text":
        return _get_typed_fallback()

    if VOICE_MODE in {"voice", "hybrid"}:
        if ALWAYS_LISTENING:
            woke_up = listen_for_wake_word()
            if not woke_up:
                return None
            heard = listen("Haan bol bhai...")
            if heard:
                return heard
            return _get_typed_fallback() if VOICE_MODE == "hybrid" else None

        heard = listen()
        if heard:
            return heard
        return _get_typed_fallback() if VOICE_MODE == "hybrid" else None

    return _get_typed_fallback()


def main():
    global VOICE_MODE
    
    # Startup checks
    status = run_all_checks(verbose=True)
    
    # Critical failure: Groq bina Bhai kuch nahi kar sakta
    if not status["groq"]["ok"]:
        print("❌ FATAL: Groq API connect nahi ho paayi. Bhai starting band kar raha hai.")
        return

    agent = BhaiAgent()
    
    # Voice mode decide karo based on mic availability
    if not status["microphone"]["ok"]:
        print("⚠️  Mic nahi mila — text mode mein chal raha hu bhai")
        VOICE_MODE = "text"
        os.environ["BHAI_VOICE_MODE"] = "text"
    
    startup_msg = "Bhai v2 ready hai! Kya karna hai bhai?"
    print(startup_msg)
    
    if VOICE_MODE in {"voice", "hybrid"}:
        speak(startup_msg, blocking=False)
    
    # WhatsApp offline warning
    if not status["whatsapp"]["ok"]:
        print("💡 TIP: WhatsApp use karne ke liye bhai-ai folder mein 'npm start' chalaao")

    SPECIAL_COMMANDS = {
        "clear": lambda: (
            agent.history.clear(), 
            agent._save_memory(),
            "History clear kar di bhai! Fresh start 🔄"
        )[2],
        "memory": lambda: f"Memory: {json.dumps(agent.memory['user_preferences'], ensure_ascii=False, indent=2)}",
        "status": lambda: str(run_all_checks(verbose=False)),
        "help": lambda: HELP_TEXT,
    }

    try:
        while True:
            text = _get_user_input()
            if not text:
                continue

            text = text.strip()
            if not text:
                continue

            # Special commands handle kar rahe hain bhai
            cmd_lower = text.lower()
            if cmd_lower in SPECIAL_COMMANDS:
                print(f"\n  Bhai: {SPECIAL_COMMANDS[cmd_lower]()}\n")
                continue
            
            if cmd_lower in ["bye", "exit", "band karo"]:
                print("\nTheek hai bhai, band kar diya. Bye!")
                break

            print(f"\n  Tu: {text}")
            
            # Thinking indicator
            print("  Bhai: ", end="", flush=True)
            start_time = time.time()
            
            reply = agent.handle_input(text)
            
            elapsed = time.time() - start_time
            print(f"{reply}")
            
            # Voice response (non-blocking!)
            if VOICE_MODE in {"voice", "hybrid"}:
                speak(reply, blocking=False)
            
            print()  # spacing

    except KeyboardInterrupt:
        print("\nTheek hai bhai, band kar diya. Bye!")
    except Exception as err:
        print(f"Arre bhai main loop mein gadbad: {err}")


if __name__ == "__main__":
    main()
