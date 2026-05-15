import asyncio
import os
import tempfile
import threading
import time

import edge_tts
import pygame
import speech_recognition as sr

from config import WAKE_WORD

VOICE = "hi-IN-MadhurNeural"
FALLBACK_VOICE = "en-IN-PrabhatNeural"
LISTEN_TIMEOUT = 6
PHRASE_LIMIT = 12
ENERGY_THRESHOLD = 300

_mixer_ready = False
_recognizer = None
_mic_available = None


def is_mic_available():
    global _mic_available
    if _mic_available is not None:
        return _mic_available
    try:
        mics = sr.Microphone.list_microphone_names()
        _mic_available = len(mics) > 0
        if _mic_available:
            print(f"Mic connected bhai: {mics[0]}")
        else:
            print("Koi mic nahi mila bhai.")
    except Exception:
        _mic_available = False
    return _mic_available


def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = sr.Recognizer()
        _recognizer.energy_threshold = ENERGY_THRESHOLD
        _recognizer.dynamic_energy_threshold = True
        _recognizer.pause_threshold = 0.8
    return _recognizer


def _speech_to_text(audio) -> str | None:
    recognizer = _get_recognizer()
    try:
        text = recognizer.recognize_google(audio, language="hi-IN")
        return text.strip() if text else None
    except sr.UnknownValueError:
        try:
            text = recognizer.recognize_google(audio, language="en-IN")
            return text.strip() if text else None
        except sr.UnknownValueError:
            return None


def listen(prompt_text="Sun raha hu..."):
    global _mic_available
    if not is_mic_available():
        return None

    recognizer = _get_recognizer()
    print(prompt_text)

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(
                    source,
                    timeout=LISTEN_TIMEOUT,
                    phrase_time_limit=PHRASE_LIMIT,
                )
            except sr.WaitTimeoutError:
                return None
        return _speech_to_text(audio)
    except OSError as err:
        print(f"Mic access error: {err}")
        _mic_available = False
        return None
    except Exception as err:
        print(f"Listen error: {err}")
        return None


def listen_for_wake_word():
    global _mic_available
    if not is_mic_available():
        return False

    recognizer = _get_recognizer()
    try:
        with sr.Microphone() as source:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
        heard = _speech_to_text(audio)
        if not heard:
            return False
        normalized = heard.lower()
        return WAKE_WORD in normalized or "bhai" in normalized
    except sr.WaitTimeoutError:
        return False
    except OSError as err:
        print(f"Wake word mic error: {err}")
        _mic_available = False
        return False
    except Exception:
        return False


def _init_mixer():
    global _mixer_ready
    if not _mixer_ready:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        _mixer_ready = True


async def _generate_tts(text, file_path, voice=VOICE):
    try:
        communicator = edge_tts.Communicate(text=text, voice=voice, rate="+5%")
        await communicator.save(file_path)
    except Exception:
        communicator = edge_tts.Communicate(text=text, voice=FALLBACK_VOICE)
        await communicator.save(file_path)


def speak(text, blocking=True):
    if not text or not text.strip():
        return

    tts_text = text if len(text) <= 500 else text[:500] + "..."

    def _play():
        temp_file = None
        try:
            fd, temp_file = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

            asyncio.run(_generate_tts(tts_text, temp_file))
            _init_mixer()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as err:
            print(f"Speak error: {err}")
        finally:
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            time.sleep(0.1)
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

    if blocking:
        _play()
    else:
        thread = threading.Thread(target=_play, daemon=True)
        thread.start()
