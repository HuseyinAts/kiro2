"""requirements-minimal.txt sonuna eksik paketleri ekle."""

path = r"C:\Users\husey\kiro2\backend\requirements-minimal.txt"

with open(path, encoding="utf-8") as f:
    existing = f.read()

additions = """
# ============================================================
# EKSIK PAKETLER — docker log'dan tespit (22 Mart 2026)
# ============================================================

# YouTube routes — YOUTUBE_API_KEY aktif olur
slowapi>=0.1.9

# Analytics export
xlsxwriter>=3.1.0

# Gelismis raporlar / IRT hesaplari
scipy>=1.11.0

# Sifreleme API'si
cryptography>=41.0.0

# Celery gorevleri
celery[redis]>=5.3.0

# 2FA
pyotp>=2.9.0

# Video cozum yukleme
aiofiles>=23.2.0

# Sentry (production hata izleme)
sentry-sdk[fastapi]>=1.40.0

# YouTube HTML scraping
beautifulsoup4>=4.12.0

# Hibrit soru uretimi
anthropic>=0.40.0

# PDF isleme
pdfplumber>=0.10.0
pypdf2>=3.0.0

# Veri analizi
pandas>=2.0.0
"""

if "slowapi" in existing:
    print("UYARI: slowapi zaten mevcut, ekleme atlanıyor.")
else:
    with open(path, "a", encoding="utf-8") as f:
        f.write(additions)
    print(f"OK: {len(additions.splitlines())} satır eklendi")
    # Doğrula
    with open(path, encoding="utf-8") as f:
        new = f.read()
    assert "slowapi" in new
    assert "xlsxwriter" in new
    assert "scipy" in new
    print("Doğrulama geçti — 3 kritik paket confirmed")
