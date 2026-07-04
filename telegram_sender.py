import requests
from config import BOT_TOKEN, CHANNEL_ID

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(text, buttons=None):
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    r = requests.post(f"{API}/sendMessage", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

def send_photo(photo_url, caption, buttons=None):
    payload = {"chat_id": CHANNEL_ID, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    r = requests.post(f"{API}/sendPhoto", json=payload, timeout=25)
    if r.status_code >= 400:
        # fallback to text if photo fails
        return send_message(caption, buttons)
    return r.json()
