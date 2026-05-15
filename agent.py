import re

from groq import Groq

from config import GROQ_API_KEY
from tools import browser, desktop, file_reader, whatsapp


class BhaiAgent:
    def __init__(self):
        self.system_prompt = (
            "You are Bhai, a casual Hinglish AI assistant. Talk like a desi best friend. "
            "Mix Hindi-English naturally. Be funny, helpful, direct. Keep responses short "
            "and spoken-friendly — no bullet points, no markdown. End with 'bhai' sometimes."
        )
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.history = []

    def _remember(self, role, content):
        self.history.append({"role": role, "content": content})
        if len(self.history) > 20:
            self.history = self.history[-20:]

    def detectIntent(self, text):
        raw = (text or "").strip()
        lower = raw.lower()

        if re.search(r"\bscreenshot le\b|\bscreen capture kar\b", lower):
            return {"intent": "screenshot"}

        if "screen dekh aur bata" in lower:
            return {"intent": "analyze_screen"}

        type_prefix = re.match(r"^type kar\s+(.+)$", raw, re.IGNORECASE)
        if type_prefix:
            return {"intent": "keyboard_type", "text": type_prefix.group(1).strip()}

        type_suffix = re.match(r"^(.+)\s+type karo$", raw, re.IGNORECASE)
        if type_suffix:
            return {"intent": "keyboard_type", "text": type_suffix.group(1).strip()}

        if "volume up" in lower:
            return {"intent": "volume", "action": "up"}
        if "volume down" in lower:
            return {"intent": "volume", "action": "down"}
        if "volume mute" in lower or lower.strip() == "mute":
            return {"intent": "volume", "action": "mute"}

        open_site_match = re.match(r"^([a-z0-9\-\.]+\.[a-z]{2,})(?:\s+website)?\s+khol$", lower)
        if open_site_match:
            return {"intent": "browser_open", "url": open_site_match.group(1).strip()}

        website_khol_match = re.match(r"^(.+?)\s+website\s+khol$", lower)
        if website_khol_match:
            base = website_khol_match.group(1).strip().replace(" ", "")
            return {"intent": "browser_open", "url": f"{base}.com"}

        search_match = re.match(r"^(.+?)\s+search\s+kar$", raw, re.IGNORECASE)
        if search_match:
            return {"intent": "browser_search", "query": search_match.group(1).strip()}

        dhundh_match = re.match(r"^(.+?)\s+dhundh$", raw, re.IGNORECASE)
        if dhundh_match:
            return {"intent": "browser_search", "query": dhundh_match.group(1).strip()}

        msg_match = re.match(r"^(.+?)\s+ko\s+msg\s+kar\s+(.+)$", raw, re.IGNORECASE)
        if msg_match:
            return {
                "intent": "whatsapp_msg",
                "contact": msg_match.group(1).strip(),
                "message": msg_match.group(2).strip(),
            }

        bhej_match = re.match(r"^(.+?)\s+ko\s+(.+)\s+bhej$", raw, re.IGNORECASE)
        if bhej_match:
            return {
                "intent": "whatsapp_msg",
                "contact": bhej_match.group(1).strip(),
                "message": bhej_match.group(2).strip(),
            }

        file_read_match = re.match(r"^(.+?)\s+(?:padh|summarize kar)$", raw, re.IGNORECASE)
        if file_read_match:
            return {"intent": "file_read", "path": file_read_match.group(1).strip()}

        close_match = re.match(r"^(.+?)\s+(?:band kar|close kar)$", raw, re.IGNORECASE)
        if close_match:
            return {"intent": "close_app", "app": close_match.group(1).strip()}

        open_match_1 = re.match(r"^(.+?)\s+app\s+khol$", raw, re.IGNORECASE)
        if open_match_1:
            return {"intent": "open_app", "app": open_match_1.group(1).strip()}

        open_match_2 = re.match(r"^(.+?)\s+khol de$", raw, re.IGNORECASE)
        if open_match_2:
            return {"intent": "open_app", "app": open_match_2.group(1).strip()}

        open_match_3 = re.match(r"^open\s+(.+)$", raw, re.IGNORECASE)
        if open_match_3:
            return {"intent": "open_app", "app": open_match_3.group(1).strip()}

        return {"intent": "groq_chat"}

    def _chat_with_groq(self, text):
        if not self.client:
            return "Arre bhai GROQ_API_KEY missing hai, .env set kar."

        messages = [{"role": "system", "content": self.system_prompt}, *self.history]
        messages.append({"role": "user", "content": text})

        result = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
        )
        reply = (result.choices[0].message.content or "").strip() or "Bhai blank reply aa gaya."

        self._remember("user", text)
        self._remember("assistant", reply)
        return reply

    def handleInput(self, text):
        try:
            parsed = self.detectIntent(text)
            intent = parsed.get("intent")

            if intent == "open_app":
                return desktop.open_app(parsed.get("app"))
            if intent == "close_app":
                return desktop.close_app(parsed.get("app"))
            if intent == "screenshot":
                shot = desktop.take_screenshot()
                if shot.startswith("Arre bhai"):
                    return shot
                return f"Screenshot le liya bhai! Path: {shot}"
            if intent == "analyze_screen":
                return desktop.analyze_screen()
            if intent == "keyboard_type":
                return desktop.keyboard_type(parsed.get("text"))
            if intent == "volume":
                return desktop.volume_control(parsed.get("action"))
            if intent == "browser_search":
                return browser.search(parsed.get("query"))
            if intent == "browser_open":
                return browser.open_url(parsed.get("url"))
            if intent == "whatsapp_msg":
                return whatsapp.send_message(parsed.get("contact"), parsed.get("message"))
            if intent == "file_read":
                return file_reader.read_file(parsed.get("path"))
            return self._chat_with_groq(text)
        except Exception as err:
            return f"Arre bhai kuch gadbad ho gayi: {err}"
