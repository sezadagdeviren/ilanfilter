import json
import requests
import time
import re
import io
import urllib.request
from bs4 import BeautifulSoup
import datetime
import hashlib
import base64
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    "gemini-3.5-flash-lite",    # ✅ 500 RPD / 15 RPM - En yüksek kotalı ve hızlı
    "gemini-3.1-flash-lite",    # ✅ 500 RPD / 15 RPM - Yedek yüksek kotalı
    "gemini-2.5-flash",         # ✅ 20 RPD / 5 RPM - Sağlam birincil
    "gemini-2.5-flash-lite",    # ✅ 20 RPD / 10 RPM - Yedek
]
KARIYER_KAPISI_API = "https://api.kariyerkapisi.gov.tr/api"
ILAN_GOV_TR_API = "https://www.ilan.gov.tr/api/api/services/app"

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

# ─── ilan.gov.tr Modülü (Kamu Personel Alım ve Sınavları) ────────────────────

def fetch_ilan_gov_tr_jobs():
    """ilan.gov.tr Kamu Personel Alım ve Sınavları (Kategori: 44) ilanlarını çeker."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Content-Type": "application/json-patch+json",
        "Accept": "text/plain",
        "x-request-origin": "IGT-UI",
        "x-requested-with": "XMLHttpRequest",
        "Origin": "https://www.ilan.gov.tr",
        "Referer": "https://www.ilan.gov.tr/ilan/kategori/44/kamu-personel-alim-ve-sinavlari?currentPage=0"
    }

    try:
        skip = 0
        while True:
            payload = {
                "keys": {"txv": [44]},
                "skipCount": skip,
                "maxResultCount": 20
            }
            r = requests.post(
                f"{ILAN_GOV_TR_API}/Ad/AdsByFilter",
                json=payload, headers=headers, verify=False, timeout=15
            )
            if r.status_code != 200:
                break

            ads = r.json().get("result", {}).get("ads", [])
            if not ads:
                break

            for a in ads:
                ad_id = str(a.get("id", ""))
                title = a.get("title", "").strip()
                institution = a.get("advertiserName", "").strip() or title
                url_str = a.get("urlStr", "")
                detail_link = f"https://www.ilan.gov.tr{url_str}" if url_str else f"https://www.ilan.gov.tr/ilan/{ad_id}"
                city = a.get("addressCityName") or extract_city(institution + " " + title)

                jobs.append({
                    "id": f"igt_{ad_id}",
                    "igt_id": ad_id,
                    "title": title,
                    "institution": institution,
                    "department": "Kamu Personel Alımı",
                    "type": "Kamu Personel Alımı",
                    "status": "Aktif",
                    "startDate": a.get("publishStartDate", ""),
                    "endDate": "",
                    "detailLink": detail_link,
                    "city": city.capitalize() if city else "Tüm Türkiye",
                    "isSuitable": None,
                    "aiExplanation": "",
                    "aiScanned": False,
                })

            skip += len(ads)
            if len(ads) < 20:
                break

        print(f"✅ ilan.gov.tr'den {len(jobs)} ilan başarıyla çekildi.")
    except Exception as e:
        print(f"⚠️ ilan.gov.tr çekilirken hata oluştu: {e}")

    return jobs

def fetch_job_details(job):
    """İlanın detay metnini API'den veya Resmi Gazete PDF'sinden çeker.
    Eğer PDF taranmış resimse (metin çıkmıyorsa) veya metin varsa ikisini de döndürebilir:
    Dönüş: (metin, pdf_base64)
    """
    if job.get("pdf_link"):
        pdf_bytes = None
        for attempt in range(2):
            try:
                r_pdf = requests.get(
                    job["pdf_link"],
                    headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'},
                    timeout=25
                )
                if r_pdf.status_code == 200:
                    pdf_bytes = r_pdf.content
                    break
            except Exception as e:
                if attempt == 1:
                    print(f"      [!] PDF indirme hatası ({job['pdf_link']}): {e}")
                time.sleep(2)

        if not pdf_bytes:
            # PDF indirilemediyse hata verip boş dön
            return "", None

        text = ""
        if PyPDF2:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    page_t = page.extract_text()
                    if page_t:
                        text += page_t + "\n"
            except Exception as pe:
                print(f"      [!] PyPDF2 metin çıkarma hatası: {pe}")

        # Eğer çıkarılan metin 150 karakterden azsa (taranmış görsel PDF ise)
        # PDF'i doğrudan Gemini'ye görsel olarak göndermek için base64'e çevirelim
        pdf_b64 = None
        if len(text.strip()) < 150 and len(pdf_bytes) < 15 * 1024 * 1024:
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

        return text.strip(), pdf_b64

    if job.get("igt_id"):
        url = f"{ILAN_GOV_TR_API}/AdDetail/GetAdDetail"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "x-request-origin": "IGT-UI",
            "x-requested-with": "XMLHttpRequest",
            "Referer": "https://www.ilan.gov.tr/"
        }
        try:
            r = requests.get(url, params={"id": job["igt_id"]}, headers=headers, verify=False, timeout=10)
            if r.status_code == 200:
                content_html = r.json().get("result", {}).get("content", "")
                if content_html:
                    soup = BeautifulSoup(content_html, "html.parser")
                    clean_text = soup.get_text(separator=" ", strip=True)
                    return clean_text, None
        except Exception as e:
            print(f"      [!] ilan.gov.tr detay çekme hatası: {e}")
        return "", None

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
            return data.get("ilanMetni", ""), None
    except:
        pass
    return "", None

# ─── Gemini AI ────────────────────────────────────────────────────────────────

def call_gemini(prompt, pdf_base64=None):
    global current_key_index
    n_keys = len(GEMINI_API_KEYS)
    
    if n_keys == 0:
        return None, None, None

    # İçerik parçalarını hazırla
    parts = []
    if pdf_base64:
        parts.append({"inlineData": {"mimeType": "application/pdf", "data": pdf_base64}})
    parts.append({"text": prompt})

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
                        json={"contents": [{"parts": parts}]},
                        headers={"Content-Type": "application/json"},
                        timeout=50
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
    # 1. Önce ilanın detay metnini ve varsa taranmış PDF base64 verisini çekelim
    ilan_metni, pdf_b64 = fetch_job_details(job)
    
    # 2. İlan detay metni çok uzunsa prompt limitlerine takılmamak için kırpalım
    if ilan_metni and len(ilan_metni) > 6000:
        ilan_metni_kirpilmis = ilan_metni[:6000] + "..."
    else:
        ilan_metni_kirpilmis = ilan_metni

    # Eğer hem detay metni hem de PDF çekilemediyse (bağlantı/timeout hatası)
    if not ilan_metni and not pdf_b64:
        job["isSuitable"] = None
        job["aiExplanation"] = "İlan detayına/PDF'e ulaşılamadı (Bağlantı hatası, tekrar denenecek)."
        job["aiScanned"] = False
        return None

    if pdf_b64:
        metin_tanim = "Ekli taranmış PDF belgesindeki ilan tablosunu ve başvuru şartlarını incele."
    else:
        metin_tanim = f"İLAN DETAY METNİ:\n{ilan_metni_kirpilmis}"

    prompt = (
        "Sen bir İK ve Kariyer uzmanısın. Kullanıcı profili şudur:\n"
        "- Yeni mezun lisans Bilgisayar Mühendisliği mezunu\n"
        "- Deneyimsiz (hiçbir yerde çalışmamış, tecrübesi 0)\n"
        "- 2026 KPSS puanı var (2024 KPSS puanı YOK)\n"
        "- Ekstra sertifikası veya tecrübe belgesi yok\n\n"
        f"İlan Başlığı: {job['title']}\n"
        f"İlan Türü: {job['type']}\n"
        f"Kurum: {job['institution']}\n\n"
        f"{metin_tanim}\n\n"
        "KURALLAR:\n"
        "1. Cevabının EN BAŞINA sadece 'UYGUN:' veya 'UYGUN DEĞİL:' yaz.\n"
        "2. ASLA 'kullanıcı şartları sağlamamaktadır', 'pozisyonlara uygun değildir', 'eğitim düzeyi uymamaktadır' gibi genel/yuvarlak/ezbere cümleler kurma!\n"
        "3. İlanda hangi unvan/kadroların açıldığını incele ve elenme nedenini SOMUT OLARAK açıkla.\n"
        "Örnek doğru açıklamalar:\n"
        "- 'UYGUN DEĞİL: İlanda Mühendis kadrosu açılmış ancak Bilgisayar değil Çevre ve Harita Mühendisliği mezuniyeti istenmektedir.'\n"
        "- 'UYGUN DEĞİL: İlandaki Bilgisayar Mühendisi kadrosu için en az 3 yıl mesleki tecrübe şartı aranmaktadır.'\n"
        "- 'UYGUN DEĞİL: Kadrolar yalnızca Hemşire, Röntgen Teknisyeni ve Destek Personelinden oluşmaktadır; mühendislik alımı yoktur.'\n"
        "- 'UYGUN DEĞİL: İlandaki lisans kadroları için 2024 KPSS P3 puanı zorunlu tutulmuştur.'\n\n"
        "Şimdi ilanı incele ve tek 1 net cümleyle sonucu yaz."
    )

    result, used_key, used_model = call_gemini(prompt, pdf_base64=pdf_b64)
    
    source_name = "Kariyer Kapısı"
    if "ilan.gov.tr" in job.get("detailLink", ""):
        source_name = "ilan.gov.tr"
    elif "resmigazete" in job.get("detailLink", ""):
        source_name = "Resmi Gazete"

    ai_log_entry = {
        "job_id": job["id"],
        "job_title": job["title"],
        "source": source_name,
        "pdf_link": job.get("pdf_link", ""),
        "extracted_text": ilan_metni if ilan_metni else ("[Taranmış Görsel PDF Gönderildi]" if pdf_b64 else ""),
        "ai_key_used": f"key_{used_key[:4]}...{used_key[-4:]}" if used_key else "none",
        "ai_model_used": used_model,
        "prompt_text": prompt,
        "response_text": result
    }

    if result is None:
        job["isSuitable"] = None
        job["aiExplanation"] = "API hatası: Keyler geçersiz veya kota dolu, analiz yapılamadı (Tekrar denenecek)."
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
    time.sleep(1)
    return ai_log_entry

# ─── Telegram ─────────────────────────────────────────────────────────────────

def format_job_message(job):
    """İlan için standart Telegram mesajı üretir."""
    is_uygun = job.get('isSuitable')
    if is_uygun is True:
        durum_baslik = "✅ *UYGUN İLAN BULUNDU*"
        uygunluk_etiketi = "✅ Uygun"
    elif is_uygun is False:
        durum_baslik = "❌ *UYGUN DEĞİL*"
        uygunluk_etiketi = "❌ Uygun Değil"
    else:
        durum_baslik = "⏳ *AI İNCELEMESİ BEKLİYOR*"
        uygunluk_etiketi = "⏳ Henüz Taranmadı"
        
    end_date_str = job.get('endDate', '')
    if 'T' in end_date_str:
        date_part = end_date_str.split('T')[0]
        parts = date_part.split('-')
        if len(parts) == 3:
            end_date_str = f"{parts[2]}.{parts[1]}.{parts[0]}"
            
    sehir_etiketi = job.get('city', 'Tüm Türkiye')
    aciklama = job.get('aiExplanation', 'Detay analizi bekleniyor...')
        
    msg = (
        f"{durum_baslik}\n\n"
        f"📋 *{job['title']}*\n"
        f"🏢 {job['institution']}\n"
        f"💼 {job['type']}\n"
        f"📍 Şehir: {sehir_etiketi}\n"
    )
    if end_date_str:
        msg += f"📅 Son: {end_date_str}\n"
        
    msg += (
        f"🤖 AI Tarandı: {uygunluk_etiketi}\n\n"
        f"💡 *AI Yorumu:*\n_{aciklama}_\n"
    )
    if job.get("detailLink"):
        msg += f"\n🔗 [İlana Git]({job['detailLink']})"
    return msg

def send_telegram(text):
    """Genel duyuru ve sistem uyarıları için standart mesaj atar."""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"  Telegram hata: {e}")
    return None

def send_or_edit_telegram_job(job):
    """
    İlanı Telegram'a gönderir veya mevcut mesajı günceller (editMessageText).
    Başarılı olursa job['telegram_message_id'] değerini günceller.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    text = format_job_message(job)
    msg_id = job.get("telegram_message_id")

    # Eğer daha önce Telegram'a gönderilmişse -> DÜZENLE (editMessageText)
    if msg_id:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "message_id": msg_id,
                    "text": text,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            # Eğer mesaj içeriği aynıysa Telegram HTTP 400 döner (message is not modified) - bu normaldir
            if r.status_code == 200:
                print(f"  ✏️ Telegram mesajı güncellendi (ID: {msg_id}) -> {job['title'][:40]}...")
                return
            elif "message is not modified" in r.text:
                return
            else:
                print(f"  [!] Telegram düzenleme hatası, yeni mesaj denenecek: {r.text[:80]}")
        except Exception as e:
            print(f"  [!] Telegram edit hata: {e}")

    # Mesaj ID yoksa veya düzenleme yapılamadıysa -> YENİ GÖNDER (sendMessage)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        if r.status_code == 200:
            new_id = r.json().get("result", {}).get("message_id")
            job["telegram_message_id"] = new_id
            print(f"  📱 Telegram yeni bildirimi gönderildi (ID: {new_id}) -> {job['title'][:40]}...")
    except Exception as e:
        print(f"  [!] Telegram gönderme hata: {e}")

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

    print("🚀 ilan.gov.tr ilanları çekiliyor...")
    jobs_ilan_gov_tr = fetch_ilan_gov_tr_jobs()

    def normalize_for_dedup(text):
        if not text:
            return ""
        t = text.lower()
        replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'}
        for k, v in replacements.items():
            t = t.replace(k, v)
        # Rektörlük, başkanlık, müdürlük gibi ekleri atalım
        for suffix in ['rektorlugunden', 'rektorlugu', 'baskanligindan', 'baskanligi', 'genel mudurlugu', 'mudurlugu', 'bakanligi']:
            t = t.replace(suffix, '')
        return re.sub(r'[^a-z0-9]', '', t)

    # 3 Platformdan gelen ilanları birleştir ve Mükerrerleri Temizle (Deduplication)
    # Öncelik sırası: Kariyer Kapısı > ilan.gov.tr > Resmi Gazete
    merged_jobs = []
    seen_institutions = []

    for job_group in [jobs_kariyer, jobs_ilan_gov_tr, jobs_resmi_gazete]:
        for job in job_group:
            norm_inst = normalize_for_dedup(job.get("institution", ""))
            norm_title = normalize_for_dedup(job.get("title", ""))

            # Eğer çok kısa bir kurum ismi değilse kontrol et
            is_dup = False
            if len(norm_inst) >= 6:
                for existing_norm in seen_institutions:
                    if len(existing_norm) >= 6 and (norm_inst in existing_norm or existing_norm in norm_inst):
                        is_dup = True
                        break

            if not is_dup:
                merged_jobs.append(job)
                if len(norm_inst) >= 6:
                    seen_institutions.append(norm_inst)

    jobs = merged_jobs
    
    if not jobs:
        print("❌ İlanlar alınamadı, çıkılıyor.")
        return

    # Mevcut verileri yeni çekilen listeyle eşleştir
    # DİKKAT: Sadece başarıyla taranmış (aiScanned=True ve isSuitable is not None) ve hata içermeyen ilanları önbellekten al
    for job in jobs:
        job_id = job["id"]
        if job_id in existing:
            prev = existing[job_id]
            # Telegram mesaj ID'sini kesinlikle koru (böylece mesaj tekrar atılmayacak, gereğinde düzenlenecek)
            if prev.get("telegram_message_id"):
                job["telegram_message_id"] = prev["telegram_message_id"]
                
            prev_exp = prev.get("aiExplanation", "")
            # Eğer önceden taranmış ve API hatası almamışsa önbellekten al
            if prev.get("aiScanned") and prev.get("isSuitable") is not None and "hata" not in prev_exp.lower() and "ulaşılamadı" not in prev_exp.lower():
                job["isSuitable"] = prev["isSuitable"]
                job["aiExplanation"] = prev["aiExplanation"]
                job["aiScanned"] = True

    try:
        with open("public/ai_logs.json", "r", encoding="utf-8") as f:
            ai_logs_data = json.load(f)
    except FileNotFoundError:
        ai_logs_data = []

    consecutive_api_errors = 0

    for i, job in enumerate(jobs):
        job_id = job["id"]

        if job.get("aiScanned"):
            status_tag = "📦 önbellekten"
            emoji = "✅" if job["isSuitable"] else "❌"
            scanned_tag = "✓"
            print(f"[{i+1}/{len(jobs)}] {emoji} {scanned_tag} {status_tag} → {job['title'][:50]}...")
            
            # Eğer ilan taranmış ama henüz Telegram'a gitmemişse Telegram'a ilet
            if not job.get("telegram_message_id"):
                send_or_edit_telegram_job(job)
                with open("public/jobs.json", "w", encoding="utf-8") as f:
                    json.dump(jobs, f, ensure_ascii=False, indent=2)
            continue
            
        print(f"[{i+1}/{len(jobs)}] 🔍 AI tarıyor: {job['title'][:65]}...")
        
        # Analyze'den dönen objeyi kaydet
        ai_log_entry = analyze_job(job)
        if ai_log_entry:
            ai_logs_data.append(ai_log_entry)
            
        if not job["aiScanned"]:
            consecutive_api_errors += 1
            status_tag = "⚠️ API Hatası (Tekrar denenecek)"
        else:
            consecutive_api_errors = 0
            status_tag = "🤖 AI taradı"
            # Tarama tamamlandı: Telegram'a gönder veya mevcut mesajı YERİNDE DÜZENLE (editMessageText)
            send_or_edit_telegram_job(job)

        # HER İLAN BİTTİĞİNDE KAYDET (Incremental save)
        with open("public/jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
            
        with open("public/ai_logs.json", "w", encoding="utf-8") as f:
            json.dump(ai_logs_data, f, ensure_ascii=False, indent=2)

        emoji = "✅" if job.get("isSuitable") is True else ("❌" if job.get("isSuitable") is False else "⏳")
        scanned_tag = "✓" if job["aiScanned"] else "⚠"
        print(f"        {emoji} {scanned_tag} {status_tag} → {job['aiExplanation'][:70]}")

        # Eğer üst üste 3 ilanda API hatası alınırsa (tüm keyler tükenmiş/kota dolmuşsa)
        if consecutive_api_errors >= 3:
            err_alert = "⚠️ *DİKKAT:* Gemini API anahtarları tükendi veya kota aşıldı! Kalan ilanlar bir sonraki çalıştırmada tekrar taranacak."
            print(f"\n🚨 {err_alert}\n")
            send_telegram(err_alert)
            break

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
