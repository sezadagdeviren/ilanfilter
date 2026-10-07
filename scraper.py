import os
import json
import requests
import time

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Birden fazla Gemini anahtarı kullanıyoruz (Virgülle ayrılmış olarak GitHub Secrets'tan alınabilir veya doğrudan gömülebilir)
# GitHub Actions'da secret kısmına GEMINI_API_KEYS olarak aralarında virgül olan string koyulursa kod okuyabilir.
GEMINI_API_KEYS = os.environ.get("GEMINI_API_KEYS", "").split(",")

# Fallback için doğrudan dosya içine yazdığımız anahtarlar (Eğer environment'dan gelmezse)
if not GEMINI_API_KEYS or GEMINI_API_KEYS[0] == "":
    GEMINI_API_KEYS = [
        "AIzaSyBLILwSPguZkCTi24q74adZ_4Ep_g88W5Q",
        "AIzaSyBqsJK2tIFi5Uo2ItOr-7uVzycAfV-QT3o",
        "AIzaSyD7QBgc0TR-5NgT4aWStxU65_0fO_gLY_I",
        "AIzaSyDZr13y6lr2tdP67xeyLIQKOY-FmPosE6Q",
        "AIzaSyBD5ozflUPp593UDV1RhtyeLO2Ndl72ZGQ",
        "AIzaSyAlzHOq7CXBBJPziz7cmQW6oYkTaVSi3CQ"
    ]

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram ayarları eksik!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_jobs():
    # Burada kariyer kapısından veriler çekilir. 
    # Şimdilik örnek veri döndürüyoruz. Gerçek URL entegrasyonu bot engellemelerini aşmayı gerektirebilir.
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
        }
    ]

def analyze_job_with_gemini(description):
    prompt = f"Ben yeni mezun, lisans bilgisayar mühendisiyim. Herhangi bir yerde çalışmadım (deneyimsizim). Sadece 2026 KPSS puanım var. Şu ilana başvurabilir miyim?\nİlan: {description}\n\nBu ilanın bana uygun olup olmadığını (uygun veya uygun değil) ve NEDENİNİ sadece tek 1 cümleyle, olumsuzsa sebebini söyleyerek açıkla. Lütfen ekstra bilgi ekleme, cevabın sadece o tek cümleden oluşsun ve en başına 'UYGUN:' veya 'UYGUN DEĞİL:' yaz."
    
    for key in GEMINI_API_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key.strip()}"
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
                time.sleep(1) # API limitini aşmamak için bekle ve diğerine geç
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
        # Fallback format kontrolü
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
        
        # Sadece yeni gelen ilanları Telegram'dan bildir
        if analyzed_job["id"] not in old_ids:
            msg = f"🔔 *YENİ İLAN:* {analyzed_job['title']}\n"
            msg += f"🏢 Kurum: {analyzed_job['institution']}\n"
            msg += f"📍 Şehir: {analyzed_job['city']}\n"
            msg += f"💡 *AI Yorumu:* {analyzed_job['aiExplanation']}\n"
            msg += f"✅ Uygunluk: {'Evet' if analyzed_job['isSuitable'] else 'Hayır'}"
            send_telegram_message(msg)
            print(f"Bidirim gönderildi: {analyzed_job['title']}")

    with open("public/jobs.json", "w", encoding="utf-8") as f:
        json.dump(new_jobs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
