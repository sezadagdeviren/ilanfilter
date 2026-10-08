"""
Kural tabanlı ön analiz: Gemini API rate-limit aşıldığında bile çalışır.
İlan başlığındaki anahtar kelimelere bakarak hızlı filtreleme yapar.
Daha sonra Gemini API'si soğuyunca gerçek AI analizi yapılır.
"""
import json

UYGUN_OLMAYAN_KEYWORDS = [
    "askeri", "subay", "tabip", "diş tabibi", "pilot", "jandarma",
    "muvazzaf", "görevde yükselme", "yeterlik sınavı", "icra müdür",
    "yüksek lisans eğitimi", "yurt dışı", "öğretmen", "beden eğitimi",
    "hukuk", "muhasebe uzman", "uzman yardımcı", "meslek personeli",
    "personel alım", "açıktan atama"
]

BILGISAYAR_KEYWORDS = [
    "bilişim", "yazılım", "bilgisayar", "it ", " it,", "teknoloji",
    "siber", "veri", "database", "network", "sistem analiz"
]

def rule_based_analyze(job):
    title_lower = job["title"].lower()
    type_lower  = job["type"].lower()

    # Askeri, pilot, tabip vb. → kesinlikle uygun değil
    for kw in UYGUN_OLMAYAN_KEYWORDS:
        if kw in title_lower:
            return False, f"'{kw.title()}' içerdiği için yeni mezun bilgisayar mühendisi profiline uygun değil."

    # Bilgisayar/bilişim geçiyorsa → uygun olabilir
    for kw in BILGISAYAR_KEYWORDS:
        if kw in title_lower or kw in type_lower:
            return True, f"Bilişim/yazılım alanında ilan ({job['type']}), profil uyuyor olabilir — AI ile doğrulayın."

    # Genel sözleşmeli / memur ilanları → uygun olmayabilir
    return False, "Bilgisayar mühendisliğiyle doğrudan ilgili bir alan görünmüyor, AI analizi önerilir."

with open("public/jobs.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

changed = 0
for job in jobs:
    if not job.get("aiScanned"):  # Sadece taranmamış olanları güncelle
        suitable, explanation = rule_based_analyze(job)
        job["isSuitable"]    = suitable
        job["aiExplanation"] = f"[Kural Bazlı] {explanation}"
        job["aiScanned"]     = False  # Hâlâ AI taranmadı olarak işaretle
        changed += 1

with open("public/jobs.json", "w", encoding="utf-8") as f:
    json.dump(jobs, f, ensure_ascii=False, indent=2)

suitable = sum(1 for j in jobs if j["isSuitable"])
print(f"✅ {changed} ilan kural bazlı analiz edildi.")
print(f"📊 Toplam: {len(jobs)} | ✅ Uygun: {suitable} | ❌ Uygun Değil: {len(jobs)-suitable}")
