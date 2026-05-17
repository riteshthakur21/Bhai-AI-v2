import requests
import os
from groq import Groq
from config import GROQ_API_KEY, GROQ_CHAT_MODEL

def check_groq() -> tuple[bool, str]:
    """Groq API key valid hai aur working hai?"""
    if not GROQ_API_KEY:
        return False, "GROQ_API_KEY .env mein nahi hai bhai!"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[{"role":"user","content":"hi"}],
            max_tokens=5
        )
        return True, "Groq API connected ✅"
    except Exception as e:
        return False, f"Groq error: {e}"

def check_whatsapp_server() -> tuple[bool, str]:
    """Node.js WhatsApp server chal raha hai?"""
    try:
        r = requests.get("http://localhost:3001/status", timeout=3)
        if r.status_code == 200:
            return True, "WhatsApp server online ✅"
        return False, f"WhatsApp server error: {r.status_code}"
    except requests.ConnectionError:
        return False, (
            "WhatsApp server offline ⚠️  "
            "(bhai-ai v1 folder mein 'npm start' chala)"
        )
    except Exception as e:
        return False, f"WhatsApp check error: {e}"

def check_microphone() -> tuple[bool, str]:
    """Mic available hai?"""
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        if mics:
            return True, f"Mic ready: {mics[0]} ✅"
        return False, "Koi mic nahi mila ⚠️ (text mode use hoga)"
    except Exception as e:
        return False, f"Mic check error: {e}"

def check_chrome() -> tuple[bool, str]:
    """Chrome/Selenium available hai?"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--log-level=3")
        
        s = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options=opts)
        driver.quit()
        return True, "Chrome/Selenium ready ✅"
    except Exception as e:
        return False, f"Chrome error: {e}"

def run_all_checks(verbose=True) -> dict:
    checks = {
        "groq": check_groq,
        "whatsapp": check_whatsapp_server,
        "microphone": check_microphone,
        "chrome": check_chrome,
    }
    results = {}
    if verbose:
        print("\n🔍 Bhai AI — Startup Check Chal Raha Hai...\n")
    
    for name, fn in checks.items():
        ok, msg = fn()
        results[name] = {"ok": ok, "msg": msg}
        if verbose:
            print(f"  {'✅' if ok else '⚠️ '} {msg}")
            
    if verbose:
        print()
    return results
