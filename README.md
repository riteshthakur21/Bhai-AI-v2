# Bhai AI (v2)

![Language](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)

## What is Bhai AI?

Bhai AI v2 ek **Python voice-first desktop assistant** hai jo Hinglish mein baat karta hai aur real machine actions bhi perform karta hai—browser search/open, app open/close, screenshot, volume control, WhatsApp send (bridge API), file read/summarize, aur normal AI chat.

## Features

- 🎤 **Voice input** (SpeechRecognition; Hindi/English fallback)
- 🔊 **Voice output** (Edge TTS + pygame playback)
- 🧠 **Hinglish AI chat** via Groq (`llama-3.3-70b-versatile`)
- 🌐 **Browser automation** (DuckDuckGo search + URL open using Selenium)
- 🖥️ **Desktop control** (open/close apps, type text, screenshot, volume)
- 👀 **Screen analysis** (screenshot + Groq vision model)
- 📄 **PDF summary** support
- 🖼️ **Image analysis** support (PNG/JPG/JPEG)
- 📲 **WhatsApp message send** via local Node API bridge (`http://localhost:3001/send`)
- 📝 **Typed fallback input** when mic is unavailable

## Project Structure

```text
bhai-v2/
├─ main.py                     # Runtime loop (listen -> intent -> reply -> speak)
├─ agent.py                    # Intent parser + orchestrator for all tools
├─ config.py                   # Loads GROQ_API_KEY from .env
├─ requirements.txt            # Python dependencies list
├─ .env                        # Local environment variables
└─ tools/
   ├─ __init__.py              # Tools package marker (currently empty)
   ├─ voice.py                 # Speech-to-text + text-to-speech helpers
   ├─ browser.py               # Selenium browser search/open utilities
   ├─ desktop.py               # App/system/keyboard/mouse/screenshot controls
   ├─ file_reader.py           # PDF + image analysis with Groq
   └─ whatsapp.py              # WhatsApp send via local HTTP bridge server
```

## Prerequisites

1. Python 3.13+ (project was executed with 3.13 artifacts)
2. pip
3. Chrome browser (for Selenium)
4. Audio input/output setup (mic + speaker)
5. Groq API key
6. For WhatsApp command support: `bhai-ai` v1 server running on port `3001`

**Dependencies (`requirements.txt`)**

- groq
- SpeechRecognition
- edge-tts
- pyautogui
- pygetwindow
- psutil
- selenium
- webdriver-manager
- Pillow
- pdfplumber
- pygame
- pyperclip
- python-dotenv
- requests
- difflib

## Installation & Setup

1. Create and activate virtual environment (recommended):

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create/update `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

4. (Optional but needed for WhatsApp messages) Start v1 bridge server:

```bash
cd ..\bhai-ai
node server.js
```

## How to Run

```bash
python main.py
```

## How to Use (Examples)

**Browser**

- `chrome pe DSA search kar`
- `youtube.com khol`
- `google website khol`

**Desktop**

- `notepad app khol`
- `chrome band kar`
- `type kar bhai ye line paste kar de`
- `screenshot le`
- `screen dekh aur bata`
- `volume up` / `volume down` / `mute`

**WhatsApp**

- `RiyaDi ko msg kar hi`
- `RiyaDi ko kal milte hain bhej`

**File Reader**

- `notes.pdf summarize kar`
- `photo.jpg padh`

## Tools & Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core runtime |
| Groq SDK (`groq`) | Chat + vision summarization |
| SpeechRecognition | Voice input |
| edge-tts | Text-to-speech generation |
| pygame | Audio playback |
| Selenium + webdriver-manager | Browser automation |
| pyautogui | Keyboard/mouse/volume controls |
| psutil | Process management for app closing |
| Pillow/ImageGrab | Screenshot capture |
| pdfplumber | PDF text extraction |
| requests | WhatsApp bridge API calls |
| python-dotenv | Environment variable loading |

## Known Limitations

- WhatsApp v2 mein direct automation nahi hai; local Node server (`localhost:3001/send`) mandatory hai.
- Intent parsing regex-based hai, toh phrasing mismatch par command miss ho sakta hai.
- `tools.voice.listen_for_wake_word()` exists, but main loop currently continuous listening mode use karta hai.
- Desktop automation Windows-oriented commands/maps pe tuned hai.

## Future Plans

- 🧷 Direct WhatsApp integration without external bridge
- 🗣️ Stable wake-word driven conversation mode
- 🧠 Richer intent handling for natural/free-form Hinglish
- 🧭 Safer guardrails for desktop/system actions
