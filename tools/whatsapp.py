import requests


def send_message(contact, message):
    try:
        if not contact or not message:
            return "Contact aur message dono chahiye bhai."

        response = requests.post(
            "http://localhost:3001/send",
            json={"contact": contact, "message": message},
            timeout=10,
        )

        if 200 <= response.status_code < 300:
            return "Bhej diya bhai! ✅"

        return f"Arre bhai WhatsApp server ne error diya: {response.status_code} {response.text}"
    except requests.RequestException as err:
        return f"Arre bhai WhatsApp bhejne mein gadbad: {err}"
    except Exception as err:
        return f"Arre bhai kuch gadbad ho gayi: {err}"
