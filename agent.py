import json
from pathlib import Path
from typing import Any, Dict, List

from groq import Groq

from config import GROQ_API_KEY, GROQ_CHAT_MODEL, MEMORY_FILE, SYSTEM_PROMPT
from tools import browser, desktop, file_reader, whatsapp

VALID_INTENTS = {
    "whatsapp_message",
    "browser_search",
    "open_app",
    "file_read",
    "screenshot",
    "system_info",
    "clipboard",
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
        return json.loads(payload[start : end + 1])

    def _detect_intent_llm(self, user_text: str) -> Dict[str, Any]:
        if not self.client:
            return {"intent": "normal_chat", "params": {}}

        schema_text = (
            'Return strict JSON only: {"intent":"...", "params":{...}}. '
            "Valid intents only: whatsapp_message, browser_search, open_app, file_read, "
            "screenshot, system_info, clipboard, normal_chat. "
            "For browser actions use intent browser_search and params.action as search_web|open_url. "
            "For file actions use intent file_read and params.action as read_pdf|read_image|list_files. "
            "For whatsapp use params.action as send_message|send_file. "
            "For clipboard use params.action as copy|get. "
            "Never return markdown."
        )

        result = self.client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an intent parser for Bhai AI."},
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

    def detectIntent(self, text: str) -> Dict[str, Any]:  # Backward compatibility
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

    def _chat_with_groq(self, text: str) -> str:
        if not self.client:
            return "Arre bhai GROQ_API_KEY missing hai, .env set kar."

        prefs = self.memory.get("user_preferences", {})
        memory_block = f"User preferences: {json.dumps(prefs, ensure_ascii=False)}"
        messages = [{"role": "system", "content": self.system_prompt}, {"role": "system", "content": memory_block}, *self.history]
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
            if intent == "open_app":
                return desktop.open_app(params.get("app_name") or params.get("app") or text)

            if intent == "browser_search":
                action = (params.get("action") or "search_web").strip().lower()
                if action == "open_url":
                    return browser.open_url(params.get("url"))
                return browser.search_web(params.get("query") or text)

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

            if intent == "screenshot":
                target_url = params.get("url")
                if target_url:
                    return browser.take_screenshot(target_url)
                shot_path = desktop.take_screenshot()
                return shot_path if shot_path.startswith("Arre bhai") else f"Screenshot save kar diya: {shot_path}"

            if intent == "system_info":
                return desktop.get_system_info()

            if intent == "clipboard":
                action = (params.get("action") or "").strip().lower()
                if action == "copy":
                    return desktop.copy_to_clipboard(params.get("text", ""))
                return desktop.get_clipboard()

            return self._chat_with_groq(text)
        except Exception as err:
            return f"Arre bhai action chalane mein gadbad ho gayi: {err}"

    def handleInput(self, text: str) -> str:  # Backward compatibility
        return self.handle_input(text)
