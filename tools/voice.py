import asyncio
import os
import tempfile
import threading
import time

import edge_tts
import pygame
import speech_recognition as sr

# ─── SETTINGS ────────────────────────────────────────────────────────────────
VOICE = "hi-IN-MadhurNeural"       # Hinglish male voice
FALLBACK_VOICE = "en-IN-PrabhatNeural"  # Fallback agar primary fail ho
LISTEN_TIMEOUT = 6                  # Kitne sec wait kare
PHRASE_LIMIT = 12                   # Max phrase length in sec
ENERGY_THRESHOLD = 300              # Mic sensitivity
WAKE_WORD = "bhai"                  # Wake word

_mixer_ready = False
_recognizer = None
_mic_available = None  # Cache mic availability


# ─── MIC CHECK ───────────────────────────────────────────────────────────────
def is_mic_available():
    global _mic_available
    if _mic_available is not None:
        return _mic_available
    try:
        mics = sr.Microphone.list_microphone_names()
        _mic_available = len(mics) > 0
        if _mic_available:
            print(f"Mic mila bhai: {mics[0]}")
        else:
            print("Koi mic nahi mila bhai.")
    except Exception:
        _mic_available = False
    return _mic_available


# ─── RECOGNIZER (singleton) ──────────────────────────────────────────────────
def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = sr.Recognizer()
        _recognizer.energy_threshold = ENERGY_THRESHOLD
        _recognizer.dynamic_energy_threshold = True   # Auto adjust
        _recognizer.pause_threshold = 0.8             # Silence ke baad stop
    return _recognizer


# ─── LISTEN ──────────────────────────────────────────────────────────────────
def listen(prompt_text="Sun raha hu..."):
    """
    Mic se awaaz suno aur text return karo.
    Returns: str ya None
    """
    if not is_mic_available():
        return None

    recognizer = _get_recognizer()
    print(prompt_text)

    try:
        with sr.Microphone() as source:
            # Sirf pehli baar noise adjust karo — baaki dynamic hai
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(
                    source,
                    timeout=LISTEN_TIMEOUT,
                    phrase_time_limit=PHRASE_LIMIT
                )
            except sr.WaitTimeoutError:
                return None  # Silence — normal hai

        # Google Speech Recognition — hi-IN primary, en-IN fallback
        try:
            text = recognizer.recognize_google(audio, language="hi-IN")
            return text.strip() if text else None
        except sr.UnknownValueError:
            # Hindi mein samajh nahi aaya, English try karo
            try:
                text = recognizer.recognize_google(audio, language="en-IN")
                return text.strip() if text else None
            except sr.UnknownValueError:
                return None

    except OSError as e:
        print(f"Mic access error: {e}")
        _mic_available = False
        return None
    except Exception as e:
        print(f"Listen error: {e}")
        return None


# ─── WAKE WORD LISTEN ────────────────────────────────────────────────────────
def listen_for_wake_word():
    """
    Sirf wake word "Bhai" ke liye short listen karo.
    Returns True agar wake word suna.
    """
    if not is_mic_available():
        return False

    recognizer = _get_recognizer()
    try:
        with sr.Microphone() as source:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
        text = recognizer.recognize_google(audio, language="hi-IN").lower()
        return WAKE_WORD in text
    except Exception:
        return False


# ─── MIXER INIT ──────────────────────────────────────────────────────────────
def _init_mixer():
    global _mixer_ready
    if not _mixer_ready:
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            _mixer_ready = True
        except Exception as e:
            print(f"Mixer init error: {e}")


# ─── TTS GENERATE ────────────────────────────────────────────────────────────
async def _generate_tts(text, file_path, voice=VOICE):
    """Edge TTS se audio file banao."""
    try:
        comm = edge_tts.Communicate(text=text, voice=voice, rate="+5%")
        await comm.save(file_path)
    except Exception:
        # Fallback voice try karo
        comm = edge_tts.Communicate(text=text, voice=FALLBACK_VOICE)
        await comm.save(file_path)


# ─── SPEAK ───────────────────────────────────────────────────────────────────
def speak(text, blocking=True):
    """
    Text ko voice mein convert karke play karo.
    blocking=False: background mein play karo (non-blocking)
    """
    if not text or not text.strip():
        return

    # Bahut lamba text chhota karo TTS ke liye
    tts_text = text if len(text) <= 500 else text[:500] + "..."

    def _play():
        temp_file = None
        try:
            # Temp file banao
            fd, temp_file = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

            # TTS generate karo
            asyncio.run(_generate_tts(tts_text, temp_file))

            # Play karo
            _init_mixer()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            # Playback complete hone ka wait karo
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)

        except Exception as e:
            print(f"Speak error: {e}")
        finally:
            # File cleanup — thoda wait karo release ke liye
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            time.sleep(0.1)
            try:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

    if blocking:
        _play()
    else:
        # Background thread mein play karo
        t = threading.Thread(target=_play, daemon=True)
        t.start()


# ─── QUICK BEEP (feedback) ───────────────────────────────────────────────────
def beep():
    """Listening start hone pe short beep — user ko pata chale."""
    try:
        import winsound
        winsound.Beep(800, 150)
    except Exception:
        pass  # Windows nahi hai toh skip


# ─── TEST ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Voice test chal raha hai...")
    speak("Bhai ready hai, test chal raha hai!")
    print("Bol kuch:")
    result = listen()
    print(f"Suna: {result}")