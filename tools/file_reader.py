import base64
from pathlib import Path

import pdfplumber
from groq import Groq

from config import GROQ_API_KEY, GROQ_CHAT_MODEL, GROQ_VISION_MODEL


def _get_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY missing hai bhai.")
    return Groq(api_key=GROQ_API_KEY)


def read_pdf(path: str) -> str:
    try:
        if not path:
            return "PDF path de bhai."

        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            return f"Arre bhai PDF nahi mila: {file_path}"
        if file_path.suffix.lower() != ".pdf":
            return "Ye PDF file nahi hai bhai."

        text_parts = []
        with pdfplumber.open(str(file_path)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")

        text = "\n".join(text_parts).strip()
        if not text:
            return "Bhai PDF mein readable text nahi mila."

        text = text[:15000]
        client = _get_client()
        result = client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "Tu Bhai assistant hai. Hinglish mein concise PDF summary de."},
                {"role": "user", "content": f"Is PDF ka summary de, main points aur action items nikaal:\n\n{text}"},
            ],
            temperature=0.4,
        )
        return (result.choices[0].message.content or "").strip() or "Bhai summary blank aa gayi."
    except Exception as err:
        return f"Arre bhai PDF padhne mein gadbad: {err}"


def read_image(path: str) -> str:
    try:
        if not path:
            return "Image path de bhai."

        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            return f"Arre bhai image nahi mili: {file_path}"
        if file_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            return "Bhai abhi PNG/JPG/JPEG/WEBP image read kar sakta hu."

        with open(file_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")

        ext = file_path.suffix.lower().replace(".", "") or "png"
        mime = "jpeg" if ext == "jpg" else ext
        client = _get_client()
        result = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is image ko Hinglish mein samjha aur short description de."},
                        {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{encoded}"}},
                    ],
                }
            ],
            temperature=0.4,
        )
        return (result.choices[0].message.content or "").strip() or "Bhai image summary blank aa gayi."
    except Exception as err:
        return f"Arre bhai image read mein gadbad: {err}"


def list_files(folder: str) -> str:
    try:
        folder_path = Path(folder or ".").expanduser().resolve()
        if not folder_path.exists() or not folder_path.is_dir():
            return f"Arre bhai valid folder nahi mila: {folder_path}"

        items = sorted(folder_path.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
        if not items:
            return f"Bhai folder empty hai: {folder_path}"

        lines = []
        for item in items[:100]:
            marker = "DIR" if item.is_dir() else "FILE"
            lines.append(f"[{marker}] {item.name}")
        return f"Folder listing ({folder_path}) bhai:\n" + "\n".join(lines)
    except Exception as err:
        return f"Arre bhai folder list mein gadbad: {err}"


def read_file(path: str) -> str:
    try:
        if not path:
            return "File path de bhai."
        file_path = Path(path).expanduser().resolve()
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return read_pdf(str(file_path))
        if ext in {".png", ".jpg", ".jpeg", ".webp"}:
            return read_image(str(file_path))
        return f"Bhai abhi is type ko support nahi karta: {ext or 'unknown'}"
    except Exception as err:
        return f"Arre bhai file read mein gadbad: {err}"
