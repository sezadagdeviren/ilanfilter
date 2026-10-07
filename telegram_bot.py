import os
import json
import requests
import time

TELEGRAM_BOT_TOKEN = "8812328547:AAH5NxBUs_JWzCMwQ1HkC6X2aQb24qwyppc"
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def get_jobs():
    try:
        with open("public/jobs.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"{BASE_URL}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def get_menu_markup():
    return {
        "inline_keyboard": [
            [{"text": "🏢 Tüm İlanlar", "callback_data": "filter_all"}],
            [{"text": "✅ Bana Uygun", "callback_data": "filter_suitable"}],
            [{"text": "❌ Uygun Değil", "callback_data": "filter_unsuitable"}]
        ]
    }

def format_jobs(jobs, filter_type):
    filtered = jobs
    title = "🏢 *TÜM İLANLAR*\n\n"
    if filter_type == "suitable":
        filtered = [j for j in jobs if j.get("isSuitable")]
        title = "✅ *BANA UYGUN İLANLAR*\n\n"
    elif filter_type == "unsuitable":
        filtered = [j for j in jobs if not j.get("isSuitable")]
        title = "❌ *UYGUN OLMAYAN İLANLAR*\n\n"

    if not filtered:
        return title + "Bu kategoride ilan bulunamadı."

    text = title
    for job in filtered:
        text += f"🔹 *{job['title']}*\n"
        text += f"🏢 {job['institution']} - 📍 {job['city']}\n"
        text += f"💡 _AI Yorumu: {job['aiExplanation']}_\n\n"
    return text[:4000]  # Telegram mesaj limiti

def main():
    print("Telegram botu başlatıldı. Mesajlar dinleniyor...")
    offset = None
    while True:
        try:
            url = f"{BASE_URL}/getUpdates"
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            
            response = requests.get(url, params=params, timeout=40)
            if response.status_code == 200:
                data = response.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    
                    # Normal mesaj geldiğinde
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            send_message(
                                chat_id, 
                                "Kariyer Kapısı İlan Filtresine Hoş Geldiniz! Lütfen görmek istediğiniz ilan türünü seçin:", 
                                get_menu_markup()
                            )
                            
                    # Butona tıklandığında
                    elif "callback_query" in update:
                        callback = update["callback_query"]
                        chat_id = callback["message"]["chat"]["id"]
                        message_id = callback["message"]["message_id"]
                        data_cmd = callback["data"]
                        
                        jobs = get_jobs()
                        
                        if data_cmd == "filter_all":
                            edit_message(chat_id, message_id, format_jobs(jobs, "all"), get_menu_markup())
                        elif data_cmd == "filter_suitable":
                            edit_message(chat_id, message_id, format_jobs(jobs, "suitable"), get_menu_markup())
                        elif data_cmd == "filter_unsuitable":
                            edit_message(chat_id, message_id, format_jobs(jobs, "unsuitable"), get_menu_markup())
            time.sleep(1)
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
