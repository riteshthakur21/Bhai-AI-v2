from agent import BhaiAgent
from tools.voice import listen, speak


def _get_typed_fallback():
    try:
        typed = input("Mic off lag raha hai, yahan type kar de: ").strip()
        return typed or None
    except EOFError:
        return None
    except Exception as err:
        print(f"Arre bhai typing input mein issue: {err}")
        return None


def main():
    agent = BhaiAgent()
    startup = "Bhai ready hai, bol kya karna hai"
    print(startup)
    speak(startup)

    try:
        while True:
            text = listen()
            if not text:
                text = _get_typed_fallback()
            if not text:
                continue

            print(f"Tu: {text}")
            reply = agent.handleInput(text)
            print(f"Bhai: {reply}")
            speak(reply)
    except KeyboardInterrupt:
        print("\nTheek hai bhai, graceful exit kar raha hu. Bye!")
    except Exception as err:
        print(f"Arre bhai main loop mein gadbad: {err}")


if __name__ == "__main__":
    main()
