import os
import json
import requests
import time

TELEGRAM_BOT_TOKEN = "8812328547:AAH5NxBUs_JWzCMwQ1HkC6X2aQb24qwyppc"
TELEGRAM_CHAT_ID = "1118351896"

GEMINI_API_KEYS = [
    "AQ.Ab8RN6KL8AYZrPLPqYQd6-qvEKzJIKLxuV3LRMkTEIpmcE4WDg",
    "AQ.Ab8RN6LgkjFS0HRD4sFohCqAsGcuOMCpBB-iyXq_0aZpbKd5jg",
    "AQ.Ab8RN6I6Z42_GoxQ8PwypF0KX-95JYAT1Nn3bYorhCrTASDpoQ",
    "AQ.Ab8RN6Klvadzz9K9PGXhnyXggDLkk943CMFmRi0DyqFVdj0OWg",
    "AQ.Ab8RN6KkN7IDBcORcn4Vqvyc0oZrCY4wEX0iCBHe_dGCc-kTfw",
    "AQ.Ab8RN6JcwGIwu7Q2iFjfrYvgIH2TkVxVBxkX5bbmQ3uZIRFUcw",
    "AQ.Ab8RN6IiwnQnf4CQ_pbKyHGSJ07VKpDEKMkwgmWZg1MgN75b2w",
    "AIzaSyBLILwSPguZkCTi24q74adZ_4Ep_g88W5Q",
    "AIzaSyBqsJK2tIFi5Uo2ItOr-7uVzycAfV-QT3o",
    "AIzaSyD7QBgc0TR-5NgT4aWStxU65_0fO_gLY_I",
    "AIzaSyDZr13y6lr2tdP67xeyLIQKOY-FmPosE6Q",
    "AIzaSyBD5ozflUPp593UDV1RhtyeLO2Ndl72ZGQ",
    "AIzaSyAlzHOq7CXBBJPziz7cmQW6oYkTaVSi3CQ",
    "AQ.Ab8RN6KussqN40JkQNM5dLUJxLv-uGkUr3k6K6ojuSWdTqzS0A",
    "AQ.Ab8RN6IQOpqSmWzng75dGO4Ujx9P6P-qSHWv6Y5LjiQLZQfCdQ",
    "AQ.Ab8RN6KIQLBQQ3AGnoxYQk_yOtScsYv3gxEK92ngZlaJnQn0Qg",
    "AQ.Ab8RN6KL72G6PUmcyOKn0Lj4QG6Dxo5KqfvwmcMTs4M9X52x2Q"
]

# Kullanıcının belirttiği model
ACTIVE_MODEL = "gemini-3.5-flash"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_jobs():
    return [
        {
            "id": "1",
            "title": "Sözleşmeli Bilişim Personeli (Yazılım Geliştirici)",
            "institution": "Adalet Bakanlığı",
            "city": "Ankara",
            "type": "Sözleşmeli",
            "description": "Bakanlığımız bünyesinde istihdam edilmek üzere, en az 3 yıl tecrübeli, 2024 KPSS P3 puanı esas alınarak bilişim personeli alınacaktır."
        },
        {
            "id": "2",
            "title": "Bilgisayar Mühendisi",
            "institution": "DSİ",
            "city": "Tümü",
            "type": "Merkezi Atama",
            "description": "Üniversitelerin Bilgisayar Mühendisliği bölümünden mezun, KPSS 2026 puanıyla atanacak deneyimsiz personel alınacaktır."
        },
        {
            "id": "3",
            "title": "Destek Personeli",
            "institution": "Sağlık Bakanlığı",
            "city": "İzmir",
            "type": "Sözleşmeli",
            "description": "Lise mezunu, temizlik görevlisi aranmaktadır."
        }
    ]

def analyze_job_with_gemini(description):
    prompt = f"Ben yeni mezun, lisans bilgisayar mühendisiyim. Herhangi bir yerde çalışmadım (deneyimsizim). Sadece 2026 KPSS puanım var. Şu ilana başvurabilir miyim?\nİlan: {description}\n\nBu ilanın bana uygun olup olmadığını (uygun veya uygun değil) ve NEDENİNİ sadece tek 1 cümleyle, olumsuzsa sebebini söyleyerek açıkla. Lütfen ekstra bilgi ekleme, cevabın sadece o tek cümleden oluşsun ve en başına 'UYGUN:' veya 'UYGUN DEĞİL:' yaz."
    
    for key in GEMINI_API_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={key.strip()}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
            else:
                print(f"API Key Failed ({key[:10]}...): Status {response.status_code}")
                time.sleep(1)
        except Exception as e:
            print(f"Error with key {key[:10]}...: {e}")
            continue
            
    return "UYGUN DEĞİL: API hataları nedeniyle analiz yapılamadı."

def analyze_job(job):
    ai_response = analyze_job_with_gemini(job["description"])
    
    is_suitable = False
    if ai_response.startswith("UYGUN:"):
        is_suitable = True
        explanation = ai_response.replace("UYGUN:", "").strip()
    elif ai_response.startswith("UYGUN DEĞİL:"):
        explanation = ai_response.replace("UYGUN DEĞİL:", "").strip()
    else:
        is_suitable = "uygun değil" not in ai_response.lower()
        explanation = ai_response

    job["isSuitable"] = is_suitable
    job["aiExplanation"] = explanation
    return job

def main():
    print("İlanlar kontrol ediliyor...")
    jobs = get_jobs()
    
    try:
        with open("public/jobs.json", "r", encoding="utf-8") as f:
            old_jobs = json.load(f)
            old_ids = [j["id"] for j in old_jobs]
    except FileNotFoundError:
        old_ids = []

    new_jobs = []
    
    for job in jobs:
        analyzed_job = analyze_job(job)
        new_jobs.append(analyzed_job)
        
        # Sadece yeni gelen ilanları Telegram'dan bildir (Push notification)
        if analyzed_job["id"] not in old_ids:
            msg = f"🔔 *YENİ İLAN:* {analyzed_job['title']}\n"
            msg += f"🏢 Kurum: {analyzed_job['institution']}\n"
            msg += f"💡 *AI Yorumu:* {analyzed_job['aiExplanation']}\n"
            msg += f"✅ Uygunluk: {'Evet' if analyzed_job['isSuitable'] else 'Hayır'}"
            send_telegram_message(msg)

    with open("public/jobs.json", "w", encoding="utf-8") as f:
        json.dump(new_jobs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
