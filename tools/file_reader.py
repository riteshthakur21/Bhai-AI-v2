import base64
from pathlib import Path

import pdfplumber
from groq import Groq

from config import GROQ_API_KEY


def _get_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY missing hai bhai.")
    return Groq(api_key=GROQ_API_KEY)


def _summarize_pdf(file_path):
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")

    text = "\n".join(text_parts).strip()
    if not text:
        return "Bhai PDF mein readable text nahi mila."

    text = text[:15000]
    client = _get_client()
    result = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Tu Bhai assistant hai. Hinglish mein chhota spoken-friendly summary de.",
            },
            {
                "role": "user",
                "content": f"Is PDF ka summary de, main points pe focus kar:\n\n{text}",
            },
        ],
        temperature=0.5,
    )
    return (result.choices[0].message.content or "").strip() or "Bhai summary blank aa gayi."


def _analyze_image(file_path):
    with open(file_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode("utf-8")

    ext = Path(file_path).suffix.lower().replace(".", "") or "png"
    mime = "jpeg" if ext == "jpg" else ext
    client = _get_client()
    result = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Is image ko Hinglish mein short summary ke saath samjha."},
                    {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{encoded}"}},
                ],
            }
        ],
        temperature=0.5,
    )
    return (result.choices[0].message.content or "").strip() or "Bhai image summary blank aa gayi."


def read_file(file_path):
    try:
        if not file_path:
            return "File path de bhai."

        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Arre bhai file nahi mili: {path}"

        ext = path.suffix.lower()
        if ext == ".pdf":
            return _summarize_pdf(str(path))
        if ext in {".png", ".jpg", ".jpeg"}:
            return _analyze_image(str(path))

        return "Bhai abhi sirf PDF ya image padh sakta hu."
    except Exception as err:
        return f"Arre bhai file padhne mein gadbad: {err}"
