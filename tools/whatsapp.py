from pathlib import Path

import requests

BASE_URL = "http://localhost:3001"
SEND_MESSAGE_ENDPOINT = f"{BASE_URL}/send"
SEND_FILE_ENDPOINT = f"{BASE_URL}/send-file"
STATUS_ENDPOINT = f"{BASE_URL}/status"


def is_server_online() -> bool:
    """Check karo ki WhatsApp bridge server online hai ya nahi."""
    try:
        r = requests.get(STATUS_ENDPOINT, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def send_message(contact: str, message: str) -> str:
    if not is_server_online():
        return (
            "Arre bhai WhatsApp server offline hai! 😅\n"
            "bhai-ai folder mein jaake 'npm start' chala phir dobara bol."
        )

    try:
        if not contact or not message:
            return "Contact aur message dono chahiye bhai."

        response = requests.post(
            SEND_MESSAGE_ENDPOINT,
            json={"contact": contact, "message": message},
            timeout=12,
        )
        if 200 <= response.status_code < 300:
            return "WhatsApp message bhej diya bhai! ✅"
        return f"Arre bhai WhatsApp server error de raha hai: {response.status_code} {response.text}"
    except requests.ConnectionError:
        return "Arre bhai WhatsApp server connect nahi ho raha. Port 3001 pe Node server on kar le."
    except requests.Timeout:
        return "Arre bhai WhatsApp request timeout ho gaya. Server busy lag raha hai."
    except requests.RequestException as err:
        return f"Arre bhai WhatsApp bhejne mein issue aa gaya: {err}"


def send_file(contact: str, filepath: str, caption: str = "") -> str:
    if not is_server_online():
        return (
            "Arre bhai WhatsApp server offline hai! 😅\n"
            "bhai-ai folder mein jaake 'npm start' chala phir dobara bol."
        )

    try:
        if not contact or not filepath:
            return "Contact aur file path dono de bhai."

        file_path = Path(filepath).expanduser().resolve()
        if not file_path.exists():
            return f"Arre bhai file nahi mili: {file_path}"

        payload = {
            "contact": contact,
            "filepath": str(file_path),
            "caption": caption or "",
        }
        response = requests.post(SEND_FILE_ENDPOINT, json=payload, timeout=20)
        if 200 <= response.status_code < 300:
            return f"File bhej di bhai: {file_path.name} ✅"
        return f"Arre bhai file send failed: {response.status_code} {response.text}"
    except requests.ConnectionError:
        return "Arre bhai WhatsApp file server se connect nahi ho pa raha. localhost:3001 check kar."
    except requests.Timeout:
        return "Arre bhai file bhejte time timeout aa gaya. Thoda chhota file try kar."
    except requests.RequestException as err:
        return f"Arre bhai file bhejne mein network issue: {err}"
