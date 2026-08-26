"""Kayıt → doğrulama e-postası UÇTAN UCA probu (#441 Adım 3, HOST tarafında).

NEDEN AYRI BİR PROB
-------------------
Kardeş `smtp_dogrulama_probu.py` **konteyner içinde** `docker exec` ile koşar ve
kendi docstring'inde (:25-27, :203-215) uçtan uca gönderimi **ÖLÇEMEDİĞİNİ**
söyler: log'ları uvicorn akışına düşmez, daemon thread süreç çıkarken kesilir.
Verdiği doğru yordam host tarafında öncesi/sonrası sayaçtı — bu dosya o yordamı
çalıştırılabilir hâle getirir.

Fark ölçülebilir: burada istek **gerçek uvicorn sürecine** gider, dolayısıyla
`core/email_util.py:77` (`email gönderildi: %s`) ve `:79` (`email gönderim
hatası`) satırları `docker logs kiro2-backend` akışına GERÇEKTEN düşer.

🔴 ALET DOĞRULAMASI ZORUNLU (S252 dersi)
----------------------------------------
Bir ölçüm adımının YEŞİL olması, o adımın bir şey ÖLÇTÜĞÜNÜ kanıtlamaz.
S252'de `docker logs | grep hata` → "0 eşleşme" görüp yeşil sayan bir adım
YAPISAL OLARAK boştu: orada hiçbir zaman satır olmayacaktı. Bu yüzden burada
her sayaç ÖNCESİ/SONRASI ölçülür **ve** ayrıca bir kontrol kolu koşar:
kayıt isteğinin kendisi uvicorn erişim log'unda görünmeli. Kontrol kolu
kıpırdamazsa log okuma kırıktır → bulgu değil ALET ARIZASI raporlanır.

⚠️ LOG SEVİYESİ TUZAĞI: başarı satırı `logger.info` (`email_util.py:77`). Kök
seviye WARNING ise "0 başarı / 0 hata" çıkar ve bu "gönderilmedi" ile ayırt
edilemez.

🔴 İLK SÜRÜMÜN KUSURU (26 Ağu 2026, ilk koşumda yakalandı): bu belirsizliği
çözmek için `docker exec … python -c "logging.getLogger().getEffectiveLevel()"`
çalıştırılıyordu. O ölçüm **başka bir süreci** okuyordu — uygulamanın logging
kurulumunu hiç koşmamış taze bir yorumlayıcı, doğal olarak varsayılan `WARNING`
döndürdü. Sonuç: gerçek sayaç `2 -> 4` ARTMIŞKEN adım `[OLCULMEDI]` damgası
vurdu — **yanlış-SIFIR**, bir ilerleme sayacındaki tek kabul edilemez hata türü.
Ve bu, `smtp_dogrulama_probu.py`'nin :29-33'te belgelediği hatanın **aynısıydı**:
ölçümü ölçtüğü şeyden farklı bir süreçte yapmak.

Meta-ölçüm KALDIRILDI. Delta'nın kendisi zaten kendini doğrular:
  Δ(gönderildi) ≥ 1        -> KANITLANDI (hem INFO görünür hem gönderim oldu)
  Δ(hata)       ≥ 1        -> BAŞARISIZ  (sebep log satırında)
  ikisi de 0               -> [OLCULMEDI]; "gönderilmedi" ile "INFO bastırıldı"
                              ayırt EDİLEMEZ, ayırt etme yordamı basılır.

Kullanım (host, depo kökünden):
    python backend/scripts/kayit_e2e_probu.py --hedef ornek+etiket@gmail.com

Sır YAZDIRMAZ: şifre üretilir, hiçbir yere basılmaz.
"""

from __future__ import annotations

import argparse
import json
import secrets
import subprocess  # nosec B404 - salt-okunur olcum aleti; argv LISTE, shell yok
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

BACKEND = "kiro2-backend"
REDIS = "kiro2-redis"
PSQL = r"C:/Program Files/PostgreSQL/18/bin/psql.exe"
API = "http://localhost:8000/api/v1"

# core/email_util.py:77 ve :79 — birebir bu biçimlerden türetildi.
DESEN_GONDERILDI = "email gönderildi:"
DESEN_HATA = "email gönderim hatası"

# Adında "TOKEN" YOK — ruff S105 değeri değil DEĞİŞKEN ADINI deseniyor ve
# `DESEN_TOKEN` "hardcoded password" yanlış-pozitifi üretiyordu (kapı bunu
# reddetti). Kaynak modül aynı tuzağı aynı çözümle geçmiş:
# `core/eposta_dogrulama.py:184-186` (`KEY_TOKEN` -> `KEY_DOGRULAMA`).
DESEN_DOGRULAMA_ANAHTARI = "eposta_dogrulama_token:*"  # <- KEY_DOGRULAMA (:187)


def _yaz(durum: str, baslik: str, ayrinti: str = "") -> None:
    print(f"[{durum:^10}] {baslik}" + (f"  — {ayrinti}" if ayrinti else ""))


def _kos(argv: list[str], girdi: bytes | None = None) -> str:
    """Alt süreç çıktısını UTF-8 olarak oku. Windows konsol kod sayfası bozmasın."""
    sonuc = subprocess.run(  # nosec B603 - argv LISTE (shell yok); operator aleti
        argv, capture_output=True, input=girdi, check=False
    )
    return (sonuc.stdout + sonuc.stderr).decode("utf-8", errors="replace")


def _loglar() -> str:
    return _kos(["docker", "logs", BACKEND])


def _sayac(metin: str, desen: str) -> int:
    return metin.count(desen)


def _redis_token_sayisi() -> int:
    cikti = _kos(
        [
            "docker",
            "exec",
            REDIS,
            "redis-cli",
            "--scan",
            "--pattern",
            DESEN_DOGRULAMA_ANAHTARI,
        ]
    )
    return len([s for s in cikti.splitlines() if s.strip()])


def _psql(sql: str, **degisken: str) -> str:
    """Salt-okunur ölçüm sorgusu; değerler `-v` ile bağlanır.

    f-string ile gömmek enjeksiyon biçimidir (`.claude/rules/security.md`),
    argüman operatörden gelse bile.

    🔴 `-c` DEĞİL `-f -` KULLANILIYOR — ölçüldü (26 Ağu 2026, kontrol kolu
    `SELECT :'hedef'`): `-c` dizeyi psql'in kendi ayrıştırıcısına sokmadan
    doğrudan sunucuya yollar, dolayısıyla `:'ad'` yerine geçmez ve sunucu
    `syntax error at or near ":"` verir. Değişken ikamesi yalnız dosya/stdin
    yolunda çalışır.
    """
    argv = [PSQL, "-U", "postgres", "-p", "5434", "-d", "kiro2", "-t", "-A"]
    for ad, deger in degisken.items():
        argv += ["-v", f"{ad}={deger}"]
    return _kos([*argv, "-f", "-"], girdi=sql.encode("utf-8")).strip()


def _sifre_uret() -> str:
    """Politikayı karşılayan rastgele şifre: büyük+küçük+rakam+özel, ardışık yok."""
    return "Kx" + secrets.token_urlsafe(9).replace("-", "q").replace("_", "w") + "!7Vm"


def main() -> int:
    ap = argparse.ArgumentParser(description="Kayıt → doğrulama e-postası E2E probu")
    ap.add_argument("--hedef", required=True, help="GERÇEK, teslim edilebilir adres")
    ap.add_argument(
        "--bekleme", type=int, default=12, help="gönderim için bekleme (sn)"
    )
    arg = ap.parse_args()

    print("=== ADIM 0: alet doğrulaması ===")
    log0 = _loglar()
    if not log0.strip():
        _yaz("ALET-ARIZA", "docker logs BOŞ", "ölçüm yapılamaz, bulgu raporlanamaz")
        return 2
    _yaz("OK", f"log akışı okunuyor ({len(log0.splitlines())} satır)")

    print("\n=== ADIM 1: ÖNCESİ sayaçlar ===")
    once = {
        "log_satir": len(log0.splitlines()),
        "gonderildi": _sayac(log0, DESEN_GONDERILDI),
        "hata": _sayac(log0, DESEN_HATA),
        "redis_token": _redis_token_sayisi(),
        "kullanici": int(_psql("SELECT count(*) FROM users") or 0),
    }
    for k, v in once.items():
        _yaz("ONCE", f"{k:14} = {v}")

    print("\n=== ADIM 2: GERÇEK /auth/kayit ===")
    govde = {
        "email": arg.hedef,
        "ad_soyad": "A1 Prob Kullanici",
        "sifre": _sifre_uret(),
        "rol": "ogrenci",
        "birth_date": "2000-01-01",
    }
    ham = _kos(
        [
            "curl",
            "-s",
            "-w",
            "\\n__HTTP__%{http_code}",
            "--max-time",
            "45",
            "-X",
            "POST",
            f"{API}/auth/kayit",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            "@-",
        ],
        girdi=json.dumps(govde, ensure_ascii=False).encode("utf-8"),
    )
    kod = ham.rsplit("__HTTP__", 1)[-1].strip() if "__HTTP__" in ham else "?"
    yanit = ham.rsplit("\n__HTTP__", 1)[0]
    _yaz("BILGI", f"HTTP {kod}", yanit[:220])
    if kod not in ("200", "201"):
        _yaz("DUR", "kayıt başarısız — zincirin geri kalanı ölçülemez")
        return 1
    _yaz(
        "BILGI",
        "⚠️ HTTP 200 GÖNDERİM KANITI DEĞİLDİR",
        "karar aşağıdaki ÖNCESİ/SONRASI sayaçlarda",
    )

    print(f"\n=== ADIM 3: {arg.bekleme} sn bekleniyor (daemon thread) ===")
    time.sleep(arg.bekleme)

    print("\n=== ADIM 4: SONRASI sayaçlar ===")
    log1 = _loglar()
    sonra = {
        "log_satir": len(log1.splitlines()),
        "gonderildi": _sayac(log1, DESEN_GONDERILDI),
        "hata": _sayac(log1, DESEN_HATA),
        "redis_token": _redis_token_sayisi(),
        "kullanici": int(_psql("SELECT count(*) FROM users") or 0),
    }

    # KONTROL KOLU: log akışı hiç kıpırdamadıysa okuma kırıktır.
    if sonra["log_satir"] <= once["log_satir"]:
        _yaz(
            "ALET-ARIZA",
            f"log satır sayısı ARTMADI ({once['log_satir']} -> {sonra['log_satir']})",
            "istek uvicorn'a ulaştı ama log okunamıyor; sayaçlar GEÇERSİZ",
        )
        return 2
    _yaz("OK", f"kontrol kolu: log {once['log_satir']} -> {sonra['log_satir']}")

    basarili = True
    for ad in ("kullanici", "redis_token"):
        delta = sonra[ad] - once[ad]
        tamam = delta >= 1
        basarili &= tamam
        _yaz(
            "OK" if tamam else "HATA",
            f"{ad:14} {once[ad]} -> {sonra[ad]}  (Δ{delta:+d})",
            "" if tamam else "en az +1 bekleniyordu",
        )

    # Gönderim yargısı YALNIZ delta'dan çıkar. Log seviyesini ayrı bir süreçte
    # ölçmek ilk sürümde yanlış-SIFIR üretti (bkz. modül docstring'i).
    gon_delta = sonra["gonderildi"] - once["gonderildi"]
    hata_delta = sonra["hata"] - once["hata"]
    if hata_delta > 0:
        basarili = False
        yeni = [s for s in log1.splitlines() if DESEN_HATA in s][-hata_delta:]
        _yaz("HATA", f"hata           Δ+{hata_delta}", (yeni[0] if yeni else "")[:220])
    elif gon_delta > 0:
        _yaz(
            "OK",
            f"gonderildi     {once['gonderildi']} -> {sonra['gonderildi']}"
            f"  (Δ{gon_delta:+d})",
            "SMTP sunucusu mesajı kabul etti (email_util.py:77 istisnasız geçti)",
        )
        _yaz("OK", f"hata           {once['hata']} -> {sonra['hata']}  (Δ0)")
    else:
        basarili = False
        _yaz(
            "OLCULMEDI",
            "gönderildi Δ0 ve hata Δ0 — AYIRT EDİLEMEZ",
            "ya gönderim olmadı ya INFO bastırıldı. Ayırt et: "
            '`docker exec kiro2-backend python -c "import logging;'
            "logging.getLogger('core.email_util').info('x')\"` DEĞİL "
            "(ayrı süreç, aynı hata) — bunun yerine `docker logs kiro2-backend "
            '| grep -c "core.email_util"` ile o logger\'ın canlı süreçte HİÇ '
            "satır yazıp yazmadığına bak.",
        )

    print("\n=== ADIM 5: yeni kullanıcının DB durumu ===")
    satir = _psql(
        "SELECT is_verified::text || '|' || is_active::text || '|' || role::text "
        "|| '|' || (created_at >= TIMESTAMPTZ '2026-08-22 00:00:00+00')::text "
        "FROM users WHERE email = :'hedef'",
        hedef=arg.hedef,
    )
    if not satir:
        _yaz("HATA", "kullanıcı DB'de bulunamadı")
        basarili = False
    else:
        dogrulanmis, aktif, rol, muaf_degil = satir.split("|")
        _yaz("OK" if dogrulanmis == "false" else "HATA", f"is_verified = {dogrulanmis}")
        _yaz("OK" if aktif == "true" else "HATA", f"is_active   = {aktif}")
        _yaz("BILGI", f"role        = {rol}")
        _yaz(
            "OK" if muaf_degil == "true" else "UYARI",
            f"muafiyet dışı = {muaf_degil}",
            "kapı açılırsa bu hesap doğrulamadan giremez (istenen davranış)",
        )

    print("\n=== SONUÇ ===")
    if basarili:
        _yaz("YESIL", "üretim yolu ölçüldü: kullanıcı + token + gönderim satırı")
        _yaz(
            "OLCULMEDI",
            "KUTUYA ULAŞTI MI",
            "bu makineden ölçülemez — insan teyidi gerekir (spam dahil)",
        )
    else:
        _yaz("KIRMIZI", "zincirde ölçülen bir adım beklenen deltayı vermedi")
    return 0 if basarili else 1


if __name__ == "__main__":
    raise SystemExit(main())
