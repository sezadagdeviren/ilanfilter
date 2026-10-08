import requests
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

# Ana sayfadan JS dosyalarını bulalım
r = requests.get("https://kariyerkapisi.gov.tr/isealim", headers=headers, timeout=15)
html = r.text

# Tüm script src'lerini bul
scripts = re.findall(r'src="(/js/[^"]+)"', html)
print("JS dosyaları:")
for s in scripts:
    print(f"  {s}")

# AJAX çağrılarını, form aksiyonlarını, data-url vs. bul
ajax_patterns = re.findall(r'(url|action|href|data-url)\s*[:=]\s*["\']([^"\']*)["\']', html)
print("\nURL'ler:")
for pattern in ajax_patterns:
    print(f"  {pattern[0]}: {pattern[1]}")

# "ilan" veya "api" içeren her şeyi bul
ilan_refs = re.findall(r'["\']([^"\']*(?:ilan|Ilan|api|Api|API)[^"\']*)["\']', html, re.IGNORECASE)
print("\nİlan/API referansları:")
for ref in ilan_refs:
    print(f"  {ref}")

# Infrastructure.js dosyasını çekelim
infra_scripts = [s for s in scripts if 'Infrastructure' in s or 'ilan' in s.lower() or 'isealim' in s.lower()]
print(f"\nAltyapı script'leri: {infra_scripts}")

# Tüm .js dosyalarını kontrol edelim
all_scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
print("\nTüm JS dosyaları:")
for s in all_scripts:
    print(f"  {s}")

# En önemli olanı: sayfanın alt kısmındaki inline JavaScript
inline_js = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"\nInline script blokları: {len(inline_js)}")
for i, js in enumerate(inline_js):
    if len(js.strip()) > 10:
        print(f"\n--- Script {i} ---")
        print(js.strip()[:800])
