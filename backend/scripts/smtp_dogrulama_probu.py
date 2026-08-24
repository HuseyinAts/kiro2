"""SMTP + e-posta doğrulama zinciri canlı probu (#441 kabul testi).

NEDEN VAR
---------
`EPOSTA_DOGRULAMA_ZORUNLU=true` yapmak GERİ ALINAMAZ bir taahhüttür: kapı açıkken
SMTP çalışmıyorsa `is_verified=false` olan kullanıcılar (24 Ağu 2026 ölçümü: 29)
ne giriş yapabilir ne doğrulama postası alabilir — kalıcı kilitlenme
(`core/eposta_dogrulama.kapi_engeli`). Bu yüzden bayrak açılmadan ÖNCE zincirin
UCTAN UCA çalıştığı ölçülmeli.

NEDEN "HTTP 200" veya "True" YETMEZ
-----------------------------------
`core/email_util.send_email` varsayılan olarak **daemon thread'de** gönderiyor
(:85) ve gönderim daha başlamadan `True` dönüyor (:88). Hata yalnızca
`logger.error` ile görünüyor. Yani:

    dogrulama_baslat() -> True   ≠   "e-posta gitti"

Bu prob bu yüzden ÜÇ bağımsız katman ölçer ve hiçbirini diğerinin yerine saymaz:

  A. SENKRON SMTP  — `send_email(..., blocking=True)`; gerçek TCP + STARTTLS +
                     LOGIN. Kimlik yanlışsa BURADA patlar.
  B. ÜRETİM YOLU   — gerçek `dogrulama_baslat()`; token üretimi + Redis + tek
                     e-posta gövdesi. Taklit yok.
  C. LOG           — `email gönderim hatası` taraması; A ve B yeşilken bile
                     thread içinde sessiz hata olabilir.

Kullanım (konteyner içinde, PYTHONPATH=/app):
    docker exec -i -e PYTHONPATH=/app -w /app kiro2-backend \
        python scripts/smtp_dogrulama_probu.py --hedef ornek@gmail.com

Sır YAZDIRMAZ: değişkenlerin yalnız VARLIĞI raporlanır, değeri asla.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

GEREKLI = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM")


def _yaz(durum: str, baslik: str, ayrinti: str = "") -> None:
    print(f"[{durum:^6}] {baslik}" + (f"  — {ayrinti}" if ayrinti else ""))


def adim_0_degiskenler() -> bool:
    """Değişkenlerin VARLIĞI. Değer asla yazdırılmaz."""
    print("\n=== ADIM 0: ortam değişkenleri ===")
    eksik = []
    for ad in GEREKLI:
        var = bool(os.environ.get(ad, "").strip())
        # SMTP_PORT dışındakiler sır; yalnızca var/yok. Port sır değil, yazdırılır.
        deger = f"={os.environ['SMTP_PORT']}" if (ad == "SMTP_PORT" and var) else ""
        _yaz("VAR" if var else "YOK", f"{ad}{deger}")
        if not var:
            eksik.append(ad)
    if eksik:
        _yaz("DUR", f"{len(eksik)}/5 değişken tanımsız", ", ".join(eksik))
        return False

    port = os.environ["SMTP_PORT"].strip()
    if port == "465":
        _yaz(
            "DUR",
            "SMTP_PORT=465 YANLIŞ",
            "email_util.py:74 `smtplib.SMTP` + `starttls()` kullanıyor (implicit "
            "TLS değil). 465 bağlantıyı astırır. 587 kullan.",
        )
        return False

    kullanici = os.environ["SMTP_USERNAME"].strip()
    gonderen = os.environ["EMAIL_FROM"].strip()
    if "gmail" in os.environ.get("SMTP_HOST", "") and kullanici != gonderen:
        _yaz(
            "UYARI",
            "EMAIL_FROM != SMTP_USERNAME",
            "Gmail farklı gönderen adresini reddeder (553).",
        )
    return True


def adim_1_senkron_smtp(hedef: str) -> bool:
    """Gerçek TCP + STARTTLS + LOGIN. Kimlik yanlışsa BURADA patlar."""
    print("\n=== ADIM 1: senkron SMTP (blocking=True) ===")
    from core.email_util import send_email, smtp_yapilandirilmis_mi

    if not smtp_yapilandirilmis_mi():
        _yaz("DUR", "smtp_yapilandirilmis_mi() False", "kod kimliği görmüyor")
        return False
    _yaz("OK", "smtp_yapilandirilmis_mi() True")

    import logging

    yakalanan: list[str] = []

    class _Yakala(logging.Handler):
        def emit(self, kayit: logging.LogRecord) -> None:
            if kayit.levelno >= logging.ERROR:
                yakalanan.append(kayit.getMessage())

    kok = logging.getLogger()
    tutucu = _Yakala()
    kok.addHandler(tutucu)
    try:
        sonuc = send_email(
            hedef,
            "KIRO2 — SMTP kurulum probu (#441)",
            "<p>Bu e-postayı görüyorsanız SMTP zinciri <b>çalışıyor</b>.</p>"
            "<p>Bu bir kurulum probudur; işlem gerektirmez.</p>",
            blocking=True,
        )
    finally:
        kok.removeHandler(tutucu)

    if yakalanan:
        _yaz("HATA", "SMTP gönderiminde hata", yakalanan[0][:200])
        return False
    if not sonuc:
        _yaz("HATA", "send_email False döndü")
        return False
    _yaz("OK", f"senkron gönderim hatasız tamamlandı -> {hedef}")
    return True


async def adim_2_uretim_yolu(hedef: str) -> bool:
    """GERÇEK `dogrulama_baslat()`: token + Redis + tek gövde. Taklit yok."""
    print("\n=== ADIM 2: üretim yolu (dogrulama_baslat) ===")
    from core.eposta_dogrulama import dogrulama_baslat, store_al

    store = await store_al()
    _yaz("BILGI", f"depo tipi: {type(store).__name__}")

    if not await store.gonderim_hakki_var_mi(hedef):
        _yaz(
            "UYARI",
            "hesap kotası dolu",
            "aynı adrese çok deneme yapıldı; farklı adres kullan veya TTL bekle",
        )
        return False

    sonuc = await dogrulama_baslat("prob-kullanici", hedef)
    if not sonuc:
        _yaz("HATA", "dogrulama_baslat False döndü", "SMTP veya kota")
        return False
    _yaz("OK", "dogrulama_baslat True (token üretildi + gövde kuyruğa alındı)")

    frontend = os.environ.get("FRONTEND_URL", "http://localhost:3001").rstrip("/")
    if frontend.endswith(":3001"):
        _yaz(
            "UYARI",
            f"FRONTEND_URL={frontend}",
            "S248: :3001 Vite dev portu; Docker'da frontend :3000. Link ölü "
            "porta gidebilir.",
        )
    else:
        _yaz("OK", f"doğrulama linki tabanı: {frontend}/eposta-dogrula?token=…")
    return True


def adim_3_log_taramasi() -> bool:
    """A ve B yeşilken bile thread içinde sessiz hata olabilir."""
    print("\n=== ADIM 3: log taraması ===")
    _yaz(
        "BILGI",
        "host'ta koştur:",
        "docker logs --tail 200 kiro2-backend 2>&1 | grep -i "
        '"email gönderim hatası\\|GÖNDERİLEMEDİ\\|SMTPAuth"',
    )
    _yaz("BILGI", "beklenen: SIFIR eşleşme")
    return True


def adim_4_kapi_durumu() -> None:
    """Bayrak açılabilir mi — SEBEP döndürür."""
    print("\n=== ADIM 4: kapı durumu ===")
    from core.eposta_dogrulama import kapi_engeli

    engel = kapi_engeli()
    if engel is None:
        _yaz("OK", "kapı KAPANABİLİR", "EPOSTA_DOGRULAMA_ZORUNLU açık ve SMTP hazır")
    elif engel.startswith("EPOSTA_DOGRULAMA_ZORUNLU"):
        _yaz("BEKLE", "bayrak henüz açılmadı", engel)
        _yaz(
            "BILGI",
            "SIRA",
            "1-3 yeşilse .env.mvp'ye EPOSTA_DOGRULAMA_ZORUNLU=true ekle + recreate",
        )
    else:
        _yaz("DUR", "bayrak AÇIK ama SMTP hazır DEĞİL — kilitlenme riski", engel)


def main() -> int:
    ayristirici = argparse.ArgumentParser(description="SMTP + doğrulama zinciri probu")
    ayristirici.add_argument(
        "--hedef", required=True, help="test postasının gideceği gerçek adres"
    )
    ayristirici.add_argument(
        "--yalniz-olc",
        action="store_true",
        help="e-posta GÖNDERME, yalnız değişken/kapı durumunu raporla",
    )
    arg = ayristirici.parse_args()

    if not adim_0_degiskenler():
        adim_4_kapi_durumu()
        return 1
    if arg.yalniz_olc:
        adim_4_kapi_durumu()
        return 0
    if not adim_1_senkron_smtp(arg.hedef):
        adim_4_kapi_durumu()
        return 1
    if not asyncio.run(adim_2_uretim_yolu(arg.hedef)):
        adim_4_kapi_durumu()
        return 1
    adim_3_log_taramasi()
    adim_4_kapi_durumu()

    print(
        "\n>>> ADIM 1 ve 2 YEŞİL. Şimdi KUTUNU KONTROL ET: iki e-posta gelmiş "
        "olmalı (prob + doğrulama linki).\n"
        ">>> Kutuya DÜŞMEDİYSE bayrağı AÇMA — 'gönderildi' ile 'ulaştı' ayrı "
        "ölçümlerdir (spam klasörüne de bak)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
