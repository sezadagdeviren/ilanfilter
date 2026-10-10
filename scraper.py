import json
import requests
import time
import re
import io
import urllib.request
from bs4 import BeautifulSoup
import datetime
import hashlib

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Birden fazla key virgülle ayrılarak verilebilir (Örn: "KEY1,KEY2,KEY3")
keys_env = os.environ.get("GEMINI_API_KEYS", "")
GEMINI_API_KEYS = [k.strip() for k in keys_env.split(",")] if keys_env else []

ACTIVE_MODELS = [
    "gemini-2.5-flash",         # ✅ Çalışıyor - birincil model
    "gemini-2.5-flash-lite",    # ✅ Daha hafif, yedek
]
KARIYER_KAPISI_API = "https://api.kariyerkapisi.gov.tr/api"

# Hata verene kadar aynı key ile devam edeceğiz
current_key_index = 0

CITIES = ["ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AMASYA", "ANKARA", "ANTALYA", "ARTVİN", "AYDIN", "BALIKESİR", "BİLECİK", "BİNGÖL", "BİTLİS", "BOLU", "BURDUR", "BURSA", "ÇANAKKALE", "ÇANKIRI", "ÇORUM", "DENİZLİ", "DİYARBAKIR", "EDİRNE", "ELAZIĞ", "ERZİNCAN", "ERZURUM", "ESKİŞEHİR", "GAZİANTEP", "GİRESUN", "GÜMÜŞHANE", "HAKKARİ", "HATAY", "ISPARTA", "MERSİN", "İSTANBUL", "İZMİR", "KARS", "KASTAMONU", "KAYSERİ", "KIRKLARELİ", "KIRŞEHİR", "KOCAELİ", "KONYA", "KÜTAHYA", "MALATYA", "MANİSA", "KAHRAMANMARAŞ", "MARDİN", "MUĞLA", "MUŞ", "NEVŞEHİR", "NİĞDE", "ORDU", "RİZE", "SAKARYA", "SAMSUN", "SİİRT", "SİNOP", "SİVAS", "TEKİRDAĞ", "TOKAT", "TRABZON", "TUNCELİ", "ŞANLIURFA", "UŞAK", "VAN", "YOZGAT", "ZONGULDAK", "AKSARAY", "BAYBURT", "KARAMAN", "KIRIKKALE", "BATMAN", "ŞIRNAK", "BARTIN", "ARDAHAN", "IĞDIR", "YALOVA", "KARABÜK", "KİLİS", "OSMANİYE", "DÜZCE"]

def extract_city(text):
    text_upper = text.upper()
    for city in CITIES:
        if city in text_upper:
            return city.capitalize()
    return "Tüm Türkiye"

def fetch_jobs(retries=3):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://kariyerkapisi.gov.tr",
        "Referer": "https://kariyerkapisi.gov.tr/isealim"
    }
    payload = {"krM_ID": 0, "searchText": "", "il": "0", "ilanTuru": "0"}

    for attempt in range(retries):
        try:
            r = requests.post(
                f"{KARIYER_KAPISI_API}/ilan/GetIseAlimPage",
                json=payload, headers=headers, timeout=20
            )
            if r.status_code == 200:
                raw = r.json().get("searchIlan", [])
                print(f"✅ {len(raw)} ilan çekildi.")
                jobs = []
                for ilan in raw:
                    is_type1 = ilan.get("ilanTipi") == 1
                    jobs.append({
                        "id": ilan.get("guid", ""),
                        "title": ilan.get("ilanBaslik", ""),
                        "institution": ilan.get("kurumAdi", ""),
                        "department": ilan.get("birimAdi", ""),
                        "type": ilan.get("ilanTuru", ""),
                        "status": ilan.get("sonDurumu", ""),
                        "startDate": ilan.get("basTarih", ""),
                        "endDate": ilan.get("bitTarih", ""),
                        "detailLink": (
                            f"https://kariyerkapisi.gov.tr/IlanDetay?i={ilan.get('guid','')}"
                            if is_type1 else ilan.get("basvuruLinki", "")
                        ),
                        "city": extract_city(ilan.get("kurumAdi", "") + " " + ilan.get("ilanBaslik", "")),
                        "isSuitable": None,
                        "aiExplanation": "",
                        "aiScanned": False,
                    })
                return jobs
        except Exception as e:
            print(f"  Bağlantı hatası (deneme {attempt+1}/{retries}): {e}")
            time.sleep(5)
    return []

# ─── Resmi Gazete Modülü ─────────────────────────────────────────────────────

def fetch_resmi_gazete_jobs():
    jobs = []
    try:
        today = datetime.datetime.now()
        url = f'https://www.resmigazete.gov.tr/ilanlar/eskiilanlar/{today.year}/{today.month:02d}/{today.year}{today.month:02d}{today.day:02d}-4.htm'
        base_url = f'https://www.resmigazete.gov.tr/ilanlar/eskiilanlar/{today.year}/{today.month:02d}/'
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('windows-1254', errors='replace')
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # <b> etiketleri ile PDF linklerini eşleştirerek kurumları çıkar
        for b in soup.find_all('b'):
            text = b.text.strip().replace('\n', ' ').replace('\r', ' ')
            text = ' '.join(text.split())  # Çoklu boşlukları temizle
            if len(text) > 10 and any(kw in text.upper() for kw in ['ÜNİVERSİTE', 'BAŞKANLI', 'REKTÖR', 'BAKANLI', 'MÜDÜRLÜ', 'KURUM']):
                
                # En yakın PDF linkini bul
                a_tag = b.find_next('a')
                pdf_url = ""
                if a_tag and a_tag.get('href') and '.pdf' in a_tag.get('href', '').lower():
                    href = a_tag.get('href')
                    if href.startswith('http'):
                        pdf_url = href
                    else:
                        pdf_url = base_url + href
                
                # Benzersiz bir ID üret
                unique_str = f"{url}_{text}"
                job_id = hashlib.md5(unique_str.encode()).hexdigest()
                
                jobs.append({
                    "id": job_id,
                    "title": text,
                    "institution": text.replace("Rektörlüğünden:", "").replace("Başkanlığından:", "").strip(),
                    "department": "Resmi Gazete İlanı",
                    "type": "Kamu Personeli Alımı",
                    "status": "Aktif",
                    "startDate": today.strftime("%Y-%m-%dT00:00:00"),
                    "endDate": (today + datetime.timedelta(days=15)).strftime("%Y-%m-%dT23:59:00"),
                    "detailLink": url,
                    "pdf_link": pdf_url,
                    "city": extract_city(text),
                    "isSuitable": None,
                    "aiExplanation": "",
                    "aiScanned": False,
                })
        print(f"✅ Resmi Gazete'den {len(jobs)} ilan başarıyla çekildi.")
    except Exception as e:
        print(f"⚠️ Resmi Gazete çekilirken hata oluştu: {e}")
    
    return jobs

def fetch_job_details(job):
    """İlanın detay metnini API'den veya Resmi Gazete PDF'sinden çeker."""
    if job.get("pdf_link"):
        try:
            import urllib.request
            req = urllib.request.Request(job["pdf_link"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                pdf_bytes = response.read()
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"      [!] PDF okuma hatası ({job['pdf_link']}): {e}")
            return ""

    url = f"{KARIYER_KAPISI_API}/ilan/GetIlanPreviewPublic"
    payload = {"ilanGuid": job["id"]}
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://kariyerkapisi.gov.tr",
        "Referer": f"https://kariyerkapisi.gov.tr/IlanDetay?i={job['id']}"
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("ilanMetni", "")
    except:
        pass
    return ""

# ─── Gemini AI ────────────────────────────────────────────────────────────────

def call_gemini(prompt):
    global current_key_index
    n_keys = len(GEMINI_API_KEYS)
    
    if n_keys == 0:
        return None, None, None

    for attempt in range(2):
        tried_keys = 0
        while tried_keys < n_keys:
            key = GEMINI_API_KEYS[current_key_index]
            
            # Bu key için modelleri sırayla dene
            for model in ACTIVE_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key.strip()}"
                try:
                    r = requests.post(
                        url,
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                        headers={"Content-Type": "application/json"},
                        timeout=20
                    )
                    if r.status_code == 200:
                        # Başarılı! Aynı key ile devam edeceğiz
                        res_text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        return res_text, key.strip(), model
                    else:
                        print(f"      [!] Model hatası ({model}): HTTP {r.status_code}")
                except Exception as e:
                    print(f"      [!] Bağlantı hatası ({model}): {e}")
            
            # Bu key'deki tüm modeller başarısız olduysa, sonraki key'e geç
            current_key_index = (current_key_index + 1) % n_keys
            tried_keys += 1

        if attempt == 0:
            print("  ⏳ Tüm keyler ve modeller tükendi, 30 saniye bekleniyor...")
            time.sleep(30)

    return None, None, None

# ─── AI Analiz ────────────────────────────────────────────────────────────────

def analyze_job(job):
    # 1. Önce ilanın detay metnini çekelim
    ilan_metni = fetch_job_details(job)
    
    # 2. İlan detay metni çok uzunsa prompt limitlerine takılmamak için kırpalım
    if len(ilan_metni) > 6000:
        ilan_metni = ilan_metni[:6000] + "..."
        
    prompt = (
        "Sen bir İK uzmanısın. Kullanıcı profili şudur:\n"
        "- Yeni mezun lisans bilgisayar mühendisi\n"
        "- Deneyimsiz (hiçbir yerde çalışmamış)\n"
        "- 2026 KPSS puanı var (2024 KPSS puanı YOK)\n"
        "- Ekstra sertifikası yok\n\n"
        f"İlan Başlığı: {job['title']}\n"
        f"İlan Türü: {job['type']}\n"
        f"Kurum: {job['institution']}\n\n"
        f"İLAN DETAY METNİ:\n{ilan_metni}\n\n"
        "Lütfen bu ilanı incele. Özellikle şunlara dikkat et:\n"
        "1. 2024 KPSS puanı mı istiyor yoksa 2026 KPSS puanı mı? (Kullanıcıda sadece 2026 var, 2024 isteniyorsa direkt elenir)\n"
        "2. Deneyim/tecrübe istiyor mu? (Kullanıcı yeni mezun ve deneyimsiz, tecrübe isteniyorsa elenir)\n"
        "3. Belirli sertifikalar/belgeler istiyor mu?\n"
        "4. Mezuniyet şartı bilgisayar mühendisliğine uygun mu?\n\n"
        "Cevabının EN BAŞINA sadece 'UYGUN:' veya 'UYGUN DEĞİL:' yaz ve ardından nedenini tek 1 cümle ile net olarak belirt. "
        "Örnek: 'UYGUN DEĞİL: 2024 KPSS puanı istendiği için elendi.' veya "
        "'UYGUN DEĞİL: 3 yıl deneyim şartı arandığı için elendi.' Başka hiçbir şey yazma."
    )

    result, used_key, used_model = call_gemini(prompt)
    
    ai_log_entry = {
        "job_id": job["id"],
        "job_title": job["title"],
        "source": "Kariyer Kapısı" if "kariyerkapisi" in job["detailLink"] else "Resmi Gazete",
        "ai_key_used": used_key,
        "ai_model_used": used_model,
        "prompt_text": prompt,
        "response_text": result
    }

    if result is None:
        job["isSuitable"] = False
        job["aiExplanation"] = "API'ye ulaşılamadı, analiz yapılamadı."
        job["aiScanned"] = False
    elif result.startswith("UYGUN DEĞİL:"):
        job["isSuitable"] = False
        job["aiExplanation"] = result.replace("UYGUN DEĞİL:", "").strip()
        job["aiScanned"] = True
    elif result.startswith("UYGUN:"):
        job["isSuitable"] = True
        job["aiExplanation"] = result.replace("UYGUN:", "").strip()
        job["aiScanned"] = True
    else:
        # Format dışı cevap geldiyse
        job["isSuitable"] = "uygun değil" not in result.lower()
        job["aiExplanation"] = result
        job["aiScanned"] = True
        
    # Limit yememek için bekle
    time.sleep(2)
    return ai_log_entry

# ─── Telegram ─────────────────────────────────────────────────────────────────

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"  Telegram hata: {e}")

# ─── Ana Akış ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Kariyer Kapısı AI İlan Tarayıcı (Detaylı)")
    print("=" * 55)

    try:
        with open("public/jobs.json", "r", encoding="utf-8") as f:
            existing = {j["id"]: j for j in json.load(f)}
    except FileNotFoundError:
        existing = {}

    print("🚀 Kariyer Kapısı ilanları çekiliyor...")
    jobs_kariyer = fetch_jobs()
    
    print("🚀 Resmi Gazete ilanları çekiliyor...")
    jobs_resmi_gazete = fetch_resmi_gazete_jobs()
    
    # İki platformdan gelen ilanları birleştir ve Mükerrerleri Temizle (Deduplication)
    # Kariyer Kapısı öncelikli olacak (daha detaylı bilgi var)
    kariyer_titles = [j["institution"].lower().strip() for j in jobs_kariyer]
    unique_resmi_gazete = []
    
    for r_job in jobs_resmi_gazete:
        r_inst = r_job["institution"].lower().strip()
        # Eğer resmi gazete kurum ismi kariyer kapısındaki isimlerin içinde varsa (veya tersi) ekleme
        is_duplicate = False
        for k_inst in kariyer_titles:
            if r_inst in k_inst or k_inst in r_inst:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_resmi_gazete.append(r_job)
            
    jobs = jobs_kariyer + unique_resmi_gazete
    
    if not jobs:
        print("❌ İlanlar alınamadı, çıkılıyor.")
        return

    # Mevcut verileri yeni çekilen listeyle eşleştir
    for job in jobs:
        job_id = job["id"]
        if job_id in existing and existing[job_id].get("aiScanned"):
            job["isSuitable"] = existing[job_id]["isSuitable"]
            job["aiExplanation"] = existing[job_id]["aiExplanation"]
            job["aiScanned"] = True

    try:
        with open("public/ai_logs.json", "r", encoding="utf-8") as f:
            ai_logs_data = json.load(f)
    except FileNotFoundError:
        ai_logs_data = []

    new_scanned = []

    for i, job in enumerate(jobs):
        job_id = job["id"]

        if job.get("aiScanned"):
            status_tag = "📦 önbellekten"
            emoji = "✅" if job["isSuitable"] else "❌"
            scanned_tag = "✓"
            print(f"[{i+1}/{len(jobs)}] {emoji} {scanned_tag} {status_tag} → {job['title'][:50]}...")
            continue
            
        print(f"[{i+1}/{len(jobs)}] 🔍 AI tarıyor: {job['title'][:65]}...")
        
        # Analyze'den dönen objeyi referans olarak atamaya gerek yok, çünkü aynı objeyi update ediyor
        ai_log_entry = analyze_job(job)
        if ai_log_entry:
            ai_logs_data.append(ai_log_entry)
            
        status_tag = "🤖 AI taradı" if job["aiScanned"] else "❌ AI Hata"

        # HER İLAN BİTTİĞİNDE KAYDET (Incremental save)
        with open("public/jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
            
        with open("public/ai_logs.json", "w", encoding="utf-8") as f:
            json.dump(ai_logs_data, f, ensure_ascii=False, indent=2)

        emoji = "✅" if job["isSuitable"] else "❌"
        scanned_tag = "✓" if job["aiScanned"] else "⚠"
        print(f"        {emoji} {scanned_tag} {status_tag} → {job['aiExplanation'][:70]}")

        if job_id not in existing:
            new_scanned.append(job)

    # İşlem tamamlandıktan sonra fazladan kaydetmeye gerek yok, son state zaten kaydedildi
    for job in new_scanned:
        is_uygun = job.get('isSuitable', False)
        durum_baslik = "✅ *UYGUN İLAN*" if is_uygun else "❌ *UYGUN DEĞİL*"
        
        # Tarihi formatla (2026-10-19T23:59:00 -> 19.10.2026)
        end_date_str = job.get('endDate', '')
        if 'T' in end_date_str:
            date_part = end_date_str.split('T')[0]
            parts = date_part.split('-')
            if len(parts) == 3:
                end_date_str = f"{parts[2]}.{parts[1]}.{parts[0]}"
                
        uygunluk_etiketi = "✅ Uygun" if is_uygun else "❌ Uygun Değil"
        sehir_etiketi = job.get('city', 'Tüm Türkiye')
            
        msg = (
            f"{durum_baslik}\n\n"
            f"📋 *{job['title']}*\n"
            f"🏢 {job['institution']}\n"
            f"💼 {job['type']}\n"
            f"📍 Şehir: {sehir_etiketi}\n"
            f"📅 Son: {end_date_str}\n"
            f"🤖 AI Tarandı\n"
            f"{uygunluk_etiketi}\n\n"
            f"💡 *AI Yorumu:*\n_{job['aiExplanation']}_\n"
        )
        if job.get("detailLink"):
            msg += f"\n🔗 [İlana Git]({job['detailLink']})"
        send_telegram(msg)
        print(f"  📱 Telegram bildirimi gönderildi: {job['title'][:50]}")

    suitable = sum(1 for j in jobs if j["isSuitable"])
    scanned  = sum(1 for j in jobs if j["aiScanned"])
    print(f"\n📊 Toplam: {len(jobs)} | 🤖 AI tarandı: {scanned} | ✅ Uygun: {suitable} | ❌ Uygun Değil: {len(jobs)-suitable}")
    print("✅ public/jobs.json başarıyla güncellendi.")

    # AI Loglarını public/ai_logs.json dosyasına yazalım
    with open("public/ai_logs.json", "w", encoding="utf-8") as f:
        json.dump(ai_logs_data, f, ensure_ascii=False, indent=2)
    print("✅ public/ai_logs.json başarıyla güncellendi.")

if __name__ == "__main__":
    main()
