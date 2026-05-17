import json
from pathlib import Path
from typing import Any, Dict, List

from groq import Groq

from config import GROQ_API_KEY, GROQ_CHAT_MODEL, MEMORY_FILE, SYSTEM_PROMPT
from tools import browser, desktop, file_reader, whatsapp

# Saare intents update kar diye bhai taaki LLM ko pata chale kya kya kar sakta hai
VALID_INTENTS = {
    "whatsapp_message",
    "browser_search",
    "open_app",
    "close_app",
    "file_read",
    "screenshot",
    "analyze_screen",
    "system_info",
    "clipboard",
    "volume_control",
    "press_key",
    "mouse_click",
    "system_action",
    "focus_window",
    "normal_chat",
}


class BhaiAgent:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.memory_path = Path(MEMORY_FILE)
        self.memory = self._load_memory()
        self.history: List[Dict[str, str]] = list(self.memory.get("conversation_history", []))

    def _default_memory(self) -> Dict[str, Any]:
        return {
            "user_preferences": {
                "naam": "",
                "favorite_apps": [],
                "common_contacts": [],
            },
            "conversation_history": [],
        }

    def _load_memory(self) -> Dict[str, Any]:
        if not self.memory_path.exists():
            memory = self._default_memory()
            self.memory_path.write_text(json.dumps(memory, indent=2), encoding="utf-8")
            return memory

        content = self.memory_path.read_text(encoding="utf-8").strip()
        if not content:
            memory = self._default_memory()
            self.memory_path.write_text(json.dumps(memory, indent=2), encoding="utf-8")
            return memory

        loaded = json.loads(content)
        if "user_preferences" not in loaded:
            loaded["user_preferences"] = self._default_memory()["user_preferences"]
        if "conversation_history" not in loaded:
            loaded["conversation_history"] = []
        return loaded

    def _save_memory(self):
        self.memory["conversation_history"] = self.history[-20:]
        self.memory_path.write_text(json.dumps(self.memory, indent=2), encoding="utf-8")

    def _remember(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self.history = self.history[-20:]
        self._save_memory()

    def _extract_json(self, text: str) -> Dict[str, Any]:
        payload = (text or "").strip()
        start = payload.find("{")
        end = payload.rfind("}")
        if start == -1 or end == -1 or end < start:
            return {}
        try:
            return json.loads(payload[start : end + 1])
        except Exception:
            return {}

    def _detect_intent_llm(self, user_text: str) -> Dict[str, Any]:
        if not self.client:
            return {"intent": "normal_chat", "params": {}}

        # Intent detection prompt ko aur powerful banaya bhai with examples
        schema_text = (
            'Return strict JSON only: {"intent":"...", "params":{...}}. '
            f"Valid intents only: {', '.join(VALID_INTENTS)}. "
            "\nExamples for intents:\n"
            "- close_app: params.app_name -> 'Spotify band karo'\n"
            "- volume_control: params.action (up|down|mute|unmute) -> 'volume badhao', 'mute karo'\n"
            "- analyze_screen: params.question -> 'screen pe kya hai'\n"
            "- press_key: params.key -> 'ctrl+c', 'alt+tab', 'win+d'\n"
            "- mouse_click: params.x, params.y, params.button (left|right), params.double (bool) -> 'yahan click karo'\n"
            "- system_action: params.action (lock|sleep|restart|shutdown) -> 'PC lock karo', 'so ja', 'restart karo'\n"
            "- focus_window: params.app_name -> 'Chrome pe focus karo'\n"
            "- screenshot: params.url (optional) -> 'screenshot lo'\n"
            "- browser_search: params.action (search_web|open_url), params.query, params.url\n"
            "- whatsapp_message: params.action (send_message|send_file), params.contact, params.message, params.filepath\n"
            "- file_read: params.action (read_pdf|read_image|list_files|read_file), params.path, params.folder\n"
            "- clipboard: params.action (copy|get), params.text\n"
            "Never return markdown."
        )

        result = self.client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an intent parser for Bhai AI. Detect exactly what the user wants to do based on the input."},
                {"role": "user", "content": f"{schema_text}\n\nInput: {user_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        parsed = self._extract_json(result.choices[0].message.content or "")
        intent = parsed.get("intent", "normal_chat")
        if intent not in VALID_INTENTS:
            intent = "normal_chat"
        params = parsed.get("params") if isinstance(parsed.get("params"), dict) else {}
        return {"intent": intent, "params": params}

    def detectIntent(self, text: str) -> Dict[str, Any]:
        return self._detect_intent_llm(text)

    def _update_preferences(self, user_text: str):
        if not self.client:
            return

        prefs = self.memory.get("user_preferences", {})
        result = self.client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract user preferences from the message. Return strict JSON only with keys: "
                        "naam (string), favorite_apps (array of strings), common_contacts (array of strings). "
                        "If no update, return current values unchanged."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Current prefs:\n{json.dumps(prefs, ensure_ascii=False)}\n\n"
                        f"Message:\n{user_text}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        updated = self._extract_json(result.choices[0].message.content or "")
        if not isinstance(updated, dict):
            return

        self.memory["user_preferences"] = {
            "naam": str(updated.get("naam", prefs.get("naam", ""))).strip(),
            "favorite_apps": list(dict.fromkeys([str(x).strip() for x in updated.get("favorite_apps", prefs.get("favorite_apps", [])) if str(x).strip()])),
            "common_contacts": list(dict.fromkeys([str(x).strip() for x in updated.get("common_contacts", prefs.get("common_contacts", [])) if str(x).strip()])),
        }
        self._save_memory()

    def _summarize_search_results(self, query: str, raw_results: str) -> str:
        # Search results ko chhota aur crisp banane ke liye bhai taaki user ko zyada na padhna pade
        if not self.client:
            return raw_results
        result = self.client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "Tu Bhai hai. Search results ko 3-4 line Hinglish summary mein de aur important links bhi include kar."},
                {"role": "user", "content": f"Query: {query}\n\nResults:\n{raw_results}"}
            ],
            temperature=0.5,
        )
        summary = (result.choices[0].message.content or "").strip()
        return f"{summary}\n\n---\n{raw_results}"

    def _chat_with_groq(self, text: str) -> str:
        if not self.client:
            return "Arre bhai GROQ_API_KEY missing hai, .env set kar."

        prefs = self.memory.get("user_preferences", {})
        naam = prefs.get("naam", "")
        contacts = prefs.get("common_contacts", [])
        
        # User details handle kar rahe hain bhai context ke liye taaki personal feel aaye
        context_instructions = f"User ka naam: {naam if naam else 'Anjaan'}. "
        if contacts:
            context_instructions += f"User ke common contacts: {', '.join(contacts)}. Inhe use karke suggestions de sakte ho WhatsApp ke liye. "
        if naam:
            context_instructions += f"Hamesha koshish karo ki user ko unke naam '{naam}' se address karo kabhi kabhi. "

        memory_block = f"User preferences: {json.dumps(prefs, ensure_ascii=False)}"
        dynamic_system = f"{self.system_prompt}\n\n{context_instructions}"

        messages = [
            {"role": "system", "content": dynamic_system},
            {"role": "system", "content": memory_block},
            *self.history
        ]
        messages.append({"role": "user", "content": text})

        result = self.client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=messages,
            temperature=0.7,
        )
        reply = (result.choices[0].message.content or "").strip() or "Bhai blank reply aa gaya."

        self._remember("user", text)
        self._remember("assistant", reply)
        self._update_preferences(text)
        return reply

    def handle_input(self, text: str) -> str:
        if not text or not text.strip():
            return "Bol na bhai, kya karna hai?"

        try:
            parsed = self._detect_intent_llm(text.strip())
            intent = parsed["intent"]
            params = parsed.get("params", {})
        except Exception as err:
            return f"Arre bhai intent parse mein issue aa gaya: {err}"

        try:
            # 1. App control (Open/Close/Focus)
            if intent == "open_app":
                return desktop.open_app(params.get("app_name") or params.get("app") or text)

            if intent == "close_app":
                # Spotify band karo types commands ke liye
                return desktop.close_app(params.get("app_name") or text)

            if intent == "focus_window":
                # Window switch ya focus karne ke liye
                return desktop.focus_window(params.get("app_name") or text)

            # 2. Browser logic
            if intent == "browser_search":
                action = (params.get("action") or "search_web").strip().lower()
                if action == "open_url":
                    return browser.open_url(params.get("url"))
                
                query = params.get("query") or text
                raw_results = browser.search_web(query)
                # Results summarize karke return karenge bhai
                return self._summarize_search_results(query, raw_results)

            # 3. WhatsApp automation
            if intent == "whatsapp_message":
                action = (params.get("action") or "send_message").strip().lower()
                if action == "send_file":
                    return whatsapp.send_file(
                        contact=params.get("contact"),
                        filepath=params.get("filepath"),
                        caption=params.get("caption"),
                    )
                return whatsapp.send_message(
                    contact=params.get("contact"),
                    message=params.get("message"),
                )

            # 4. File reading & listing
            if intent == "file_read":
                action = (params.get("action") or "").strip().lower()
                if action == "list_files":
                    return file_reader.list_files(params.get("folder") or ".")
                path = params.get("path")
                if action == "read_pdf":
                    return file_reader.read_pdf(path)
                if action == "read_image":
                    return file_reader.read_image(path)
                return file_reader.read_file(path)

            # 5. Vision / Screen Analysis
            if intent == "screenshot":
                target_url = params.get("url")
                if target_url:
                    return browser.take_screenshot(target_url)
                shot_path = desktop.take_screenshot()
                return shot_path if shot_path.startswith("Arre bhai") else f"Screenshot save kar diya: {shot_path}"

            if intent == "analyze_screen":
                # Vision model use karke screen analyze karna
                question = params.get("question", "Is screenshot mein kya dikh raha hai? Hinglish mein bata.")
                return desktop.analyze_screen(question)

            # 6. System & Desktop tools (Volume, Keys, Mouse, etc.)
            if intent == "system_info":
                return desktop.get_system_info()

            if intent == "clipboard":
                action = (params.get("action") or "").strip().lower()
                if action == "copy":
                    return desktop.copy_to_clipboard(params.get("text", ""))
                return desktop.get_clipboard()

            if intent == "volume_control":
                # Volume control functions call kar rahe hain
                return desktop.volume_control(params.get("action", "up"))

            if intent == "press_key":
                # Keyboard shortcuts types actions
                return desktop.press_key(params.get("key", ""))

            if intent == "mouse_click":
                # Mouse interaction
                return desktop.mouse_click(
                    x=params.get("x"),
                    y=params.get("y"),
                    button=params.get("button", "left"),
                    double=params.get("double", False)
                )

            if intent == "system_action":
                # Lock/Sleep/Restart/Shutdown
                return desktop.system_action(params.get("action", ""))

            # 7. Normal Chat (Fallback)
            return self._chat_with_groq(text)

        except Exception as err:
            return f"Arre bhai action chalane mein gadbad ho gayi: {err}"

    def handleInput(self, text: str) -> str:
        # Backward compatibility ke liye bhai
        return self.handle_input(text)
