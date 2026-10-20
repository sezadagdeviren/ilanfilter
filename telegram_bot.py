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
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, json=payload, timeout=10)

def answer_callback(callback_id):
    requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": callback_id}, timeout=10)

def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"{BASE_URL}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

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
    if filter_type == "suitable":
        filtered = [j for j in jobs if j.get("isSuitable")]
        title = f"✅ *BANA UYGUN İLANLAR ({len(filtered)})*\n\n"
    elif filter_type == "unsuitable":
        filtered = [j for j in jobs if not j.get("isSuitable")]
        title = f"❌ *UYGUN OLMAYAN İLANLAR ({len(filtered)})*\n\n"
    else:
        title = f"🏢 *TÜM İLANLAR ({len(filtered)})*\n\n"

    if not filtered:
        return title + "Bu kategoride ilan bulunamadı."

    text = title
    for i, job in enumerate(filtered[:15]):  # En fazla 15 ilan göster (Telegram mesaj limiti)
        emoji = "✅" if job.get("isSuitable") else "❌"
        text += f"{emoji} *{i+1}. {job.get('title', '')[:80]}*\n"
        text += f"🏢 {job.get('institution', '')}\n"
        text += f"💼 {job.get('type', '')}\n"
        if job.get("aiExplanation"):
            text += f"💡 _{job['aiExplanation'][:100]}_\n"
        text += "\n"
    
    if len(filtered) > 15:
        text += f"_...ve {len(filtered) - 15} ilan daha (web arayüzünden görüntüleyin)_"
    
    return text[:4000]

def main():
    print("Telegram botu başlatıldı. Mesajlar dinleniyor...")
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset

            response = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=40)
            if response.status_code == 200:
                data = response.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]

                        if text == "/start":
                            jobs = get_jobs()
                            suitable = sum(1 for j in jobs if j.get("isSuitable"))
                            msg = f"🤖 *Kariyer Kapısı AI Filtresi*\n\n"
                            msg += f"Toplam *{len(jobs)}* aktif ilan bulundu.\n"
                            msg += f"✅ *{suitable}* tanesi profilinize uygun.\n"
                            msg += f"❌ *{len(jobs) - suitable}* tanesi uygun değil.\n\n"
                            msg += "Görmek istediğiniz kategoriyi seçin:"
                            send_message(chat_id, msg, get_menu_markup())

                    elif "callback_query" in update:
                        callback = update["callback_query"]
                        chat_id = callback["message"]["chat"]["id"]
                        message_id = callback["message"]["message_id"]
                        data_cmd = callback["data"]
                        answer_callback(callback["id"])

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
