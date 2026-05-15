from agent import BhaiAgent
from config import ALWAYS_LISTENING, VOICE_MODE
from tools.voice import listen, listen_for_wake_word, speak


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
    agent = BhaiAgent()
    startup = "Bhai v2 advanced mode mein ready hai. Hey Bhai bol aur command de."
    print(startup)
    if VOICE_MODE in {"voice", "hybrid"}:
        speak(startup)

    try:
        while True:
            text = _get_user_input()
            if not text:
                continue

            print(f"Tu: {text}")
            reply = agent.handle_input(text)
            print(f"Bhai: {reply}")
            if VOICE_MODE in {"voice", "hybrid"}:
                speak(reply)
    except KeyboardInterrupt:
        print("\nTheek hai bhai, band kar diya. Bye!")
    except Exception as err:
        print(f"Arre bhai main loop mein gadbad: {err}")


if __name__ == "__main__":
    main()
