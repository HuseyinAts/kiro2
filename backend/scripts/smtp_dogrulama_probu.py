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

Bu prob İKİ katmanı ölçer, ÜÇÜNCÜSÜNÜ ölçemediğini SÖYLER:

  A. SENKRON SMTP  — `send_email(..., blocking=True)`; gerçek TCP + STARTTLS +
                     LOGIN. Kimlik yanlışsa BURADA patlar. ÖLÇÜLÜR.
  B. ÜRETİM YOLU   — gerçek `dogrulama_baslat()`; Redis token sayısı
                     ÖNCESİ/SONRASI karşılaştırılır. ÖLÇÜLÜR.
  C. UÇTAN UCA     — **ÖLÇÜLEMEZ.** Bu prob `docker exec` ile AYRI süreçte
                     koşar; uvicorn log'una düşmez ve daemon thread süreç
                     çıkarken kesilebilir. Yordam Adım 3'te.

🔴 İLK SÜRÜMÜN KUSURU (25 Ağu 2026): Adım 3 `docker logs` taraması yapıp
"SIFIR eşleşme" bekliyordu. O ölçüm YAPISAL OLARAK boştu — orada zaten hiçbir
zaman satır olmayacaktı — ve 0'ı "hata yok" diye okumak YANLIŞ-YEŞİL üretti.
Kusuru yakalayan şey ÖNCESİ/SONRASI sayaç oldu (`0 -> 0`). Mutlak bir sayı durum
hakkında hiçbir şey söylemez; DEĞİŞİM söyler. Bu ders koda gömüldü.

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
    from core.eposta_dogrulama import (
        EpostaDogrulamaStore,
        dogrulama_baslat,
        store_al,
    )

    store = await store_al()
    _yaz("BILGI", f"depo tipi: {type(store).__name__}")

    if not await store.gonderim_hakki_var_mi(hedef):
        _yaz(
            "UYARI",
            "hesap kotası dolu",
            "aynı adrese çok deneme yapıldı; farklı adres kullan veya TTL bekle",
        )
        return False

    # ÖNCE/SONRA sayaç — mutlak sayı ("1 anahtar var") durum hakkında hiçbir şey
    # söylemez, DEĞİŞİM söyler. Eski bir token da 1 gösterirdi.
    from core.eposta_dogrulama import _redis_al

    redis = await _redis_al()
    desen = f"{EpostaDogrulamaStore.KEY_DOGRULAMA}:*"
    once = len(await redis.keys(desen)) if redis else None

    sonuc = await dogrulama_baslat("prob-kullanici", hedef)
    if not sonuc:
        _yaz("HATA", "dogrulama_baslat False döndü", "SMTP veya kota")
        return False

    if redis is None:
        _yaz("UYARI", "Redis yok", "token kalıcılığı ÖLÇÜLEMEDİ (bellek-içi depo)")
    else:
        sonra = len(await redis.keys(desen))
        if sonra <= (once or 0):
            _yaz("HATA", f"Redis token sayısı ARTMADI ({once} -> {sonra})")
            return False
        ttl = await redis.ttl((await redis.keys(desen))[-1])
        _yaz(
            "OK", f"Redis token {once} -> {sonra}", f"TTL {ttl} sn (~{ttl // 3600} sa)"
        )

    _yaz("OK", "dogrulama_baslat True (token üretildi + gövde kuyruğa alındı)")
    _yaz(
        "UYARI",
        "GÖNDERİM BU SÜREÇTE DOĞRULANMADI",
        "`send_email` daemon THREAD'de gönderiyor; bu tek-atımlık `docker exec` "
        "süreci hemen çıkarsa thread KESİLİR. Uçtan uca kanıt için Adım 3'e bak.",
    )

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


def adim_3_uctan_uca_yordam() -> bool:
    """UÇTAN UCA gönderim BU PROBLA ÖLÇÜLEMEZ — nedeni ve doğru yordam.

    🔴 İLK SÜRÜMÜN KUSURU (25 Ağu 2026'da yakalandı): burada `docker logs`
    taraması öneriliyor ve "SIFIR eşleşme" bekleniyordu. O ölçüm YAPISAL OLARAK
    boştu: bu prob `docker exec` ile AYRI bir süreçte koşuyor, log'ları
    uvicorn'un akışına HİÇ düşmüyor. Yani orada her zaman 0 çıkacaktı ve 0'ı
    "hata yok" diye okumak YANLIŞ-YEŞİL üretiyordu.

    Yakalayan şey ÖNCESİ/SONRASI sayaç oldu (`0 -> 0`): mutlak bir sayı durum
    hakkında hiçbir şey söylemez, DEĞİŞİM söyler.

    Bu adım artık ölçüm YAPMAZ; ölçmediğini SÖYLER ve doğru yordamı verir.
    """
    print("\n=== ADIM 3: uçtan uca gönderim — BU PROBLA ÖLÇÜLEMEZ ===")
    _yaz(
        "OLCULMEDI",
        "gönderimin ULAŞTIĞI bu süreçten doğrulanamaz",
        "prob `docker exec` ile ayrı süreçte koşar; uvicorn log'una düşmez ve "
        "daemon thread süreç çıkarken kesilebilir.",
    )
    _yaz("BILGI", "DOĞRU YORDAM — host'ta, ÖNCESİ/SONRASI sayaçla:")
    print(
        '  ONCE=$(docker logs kiro2-backend 2>&1 | grep -ci "gönderildi")\n'
        "  curl -s -X POST http://localhost:8000/api/v1/auth/kayit \\\n"
        "       -H \"Content-Type: application/json\" -d '{...gerçek e-posta...}'\n"
        "  sleep 8\n"
        '  SONRA=$(docker logs kiro2-backend 2>&1 | grep -ci "gönderildi")\n'
        "  # SONRA > ONCE olmalı. Eşitse gönderim OLMADI."
    )
    _yaz(
        "BILGI",
        "⚠️ /auth/eposta-dogrula/gonder NÖTR yanıt döner",
        "adres kayıtlı DEĞİLSE de HTTP 200 verir (kullanıcı sayımı koruması). "
        "200 gördün diye gönderildi SANMA — sayaç bak.",
    )
    _yaz("BILGI", "SON ÖLÇÜM İNSANDA: gerçek kutuya düştü mü (spam dahil)")
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
    adim_3_uctan_uca_yordam()
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
