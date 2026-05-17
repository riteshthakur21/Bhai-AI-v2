# Bhai AI (v2)

![Language](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)

Bhai AI v2 ek **Python voice-first desktop assistant** hai jo Hinglish mein baat karta hai aur real machine actions perform karta hai. Ye aapka desktop automation companion hai jo casual aur funny Hinglish tone mein interact karta hai.

## 🚀 Startup Flow

```text
[Startup]
   |
   ▼
[Health Checks] 🔍
   |-- Groq API (Fatal if fails)
   |-- Mic Check (Fallback to Text if fails)
   |-- WhatsApp Server Check
   |-- Chrome/Selenium Check
   |
   ▼
[Wait for Wake Word] 🎤 ("Hey Bhai", "Bhai", etc.)
   |
   ▼
[Listen to Command] 👂
   |
   ▼
[Intent Detection] 🧠 (Groq LLM)
   |
   ▼
[Execute Action] ⚙️ (Tools)
   |
   ▼
[Hinglish Reply] 🔊 (Edge-TTS)
```

## 🛠️ Voice Commands

| Category | Commands (Examples) | Action |
|---|---|---|
| **Chat** | `kaisa hai bhai?`, `joke suna` | Normal AI conversation |
| **Browser** | `DSA search kar`, `youtube.com khol` | Web search & navigation |
| **Desktop** | `notepad khol`, `chrome band kar` | App launch & termination |
| **System** | `volume badhao`, `mute kar de` | Volume & system control |
| **Vision** | `screen pe kya hai`, `screenshot le` | Screen analysis & capture |
| **WhatsApp** | `Rahul ko hi bhej` | Message/File via local bridge |
| **Files** | `notes.pdf summarize kar` | PDF/Image reading |

## ⚙️ .env Configuration

Root directory mein `.env` file banaye:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
BHAI_VOICE_MODE=hybrid
BHAI_ALWAYS_LISTENING=true
BHAI_WAKE_WORD=hey bhai
```

## ⚠️ Troubleshooting

- **Mic nahi chal raha?**
  - Check hardware connection. Failsafe: Bhai automatically **Text Mode** switch kar lega.
- **WhatsApp Offline?**
  - Make sure `bhai-ai` v1 folder mein `npm start` chal raha hai (Port 3001).
- **Groq Error?**
  - Verify `GROQ_API_KEY` in `.env`. Key expired ya galat hone pe startup fail hoga.
- **Chrome Error?**
  - ChromeDriver automatically update hota hai, but manual install ke liye Chrome version check karein.

## 📦 Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 📜 Special Commands

- `help`: Saare features aur commands ki list.
- `clear`: Purani conversation history delete karein.
- `memory`: Dekhein Bhai ko aapke baare mein kya pata hai.
- `status`: Diagnostic checks dobara run karein.
- `bye` / `exit`: Assistant band karne ke liye.
