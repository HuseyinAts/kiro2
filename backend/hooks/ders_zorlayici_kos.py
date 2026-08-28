#!/usr/bin/env python
"""Ders defterindeki ZORLAYICI testleri koşar — liste defterden TÜRETİLİR.

NEDEN VAR
---------
S231 ölçtü: defterin %29'unun `zorlayici` alanı doluydu ama o zorlayıcıların
**%0'ı otomatik koşuyordu** (pre-commit'te test hook'u yok, CI yalnız main/master).
Dersler "ajan bağlamı" üzerinden işliyordu — bağlam kaybında sessizce bozulan bir
enforcement. S232'de tek bir test (Y12) pre-push'a bağlandı; bu 18 bekçi
dosyasının **1'i** demekti (%5,6).

NEDEN LİSTE SABİT DEĞİL
-----------------------
Hook'a 18 dosyayı elle yazmak bayatlar: yeni ders eklendiğinde listeyi kimse
güncellemez ve enforcement sessizce gerilerken sayı "18" olarak doğru görünür.
Bu, bu deponun tekrar eden kusuru (`L-s219-ilerleme-sayaci-da-bir-olcum-aletidir`).

Bu yüzden liste `ders_kaydi.yaml`'daki `zorlayici:` alanlarından TÜRETİLİR.
Sonuç: bir derse zorlayıcı yazmak = onu otomatik kapıya bağlamak. Defter
dokümantasyon değil, **yük taşıyan** bir yapı hâline gelir.

KAPI DAVRANIŞI
--------------
- `zorlayici` dosyası DİSKTE YOKSA  -> HATA (defter yalan söylüyor)
- pytest kırmızıysa                 -> HATA (push bloke)
- `xfail` beklenen kırmızılar geçer (Y11 gibi açık işler xfail ile işaretli)

Ölçülen maliyet (19 Ağu 2026, A3 sonrası): **19 dosya / 191 toplanan /
182 passed + 9 xfailed + 0 skipped**, ~45 sn.

⚠️ Bu sayı BAYATLAR. Yeni bir derse `zorlayici` yazmak listeyi büyütür ve
buradaki rakam sessizce yanlışlaşır — nitekim bir kez oldu ("18 dosya /
162 passed", `ae830d67d` ile 19'a çıkmıştı). Yük taşıyan sayı burada değil,
`test_ders_kaydi.py::ZORLAYICI_TABANI` cırcırında.
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - yollar dogrulaniyor, shell=False; asagiya bak
import sys
from pathlib import Path

DEPO_KOKU = Path(__file__).resolve().parents[2]
DEFTER = DEPO_KOKU / ".claude" / "lessons" / "ders_kaydi.yaml"
BACKEND = DEPO_KOKU / "backend"


def zorlayicilari_topla() -> list[str]:
    """Defterdeki `zorlayici:` yollarını çıkar (null/~/boş olanlar atlanır)."""
    metin = DEFTER.read_text(encoding="utf-8")
    yollar: list[str] = []
    for ham in re.findall(r"^  zorlayici:\s*(.+?)\s*$", metin, re.M):
        deger = ham.strip().strip("\"'")
        if deger in ("null", "~", ""):
            continue
        yollar.append(deger)
    # sirali + tekil: ayni dosyayi iki kez kosma
    return sorted(set(yollar))


def bicim_gecersizleri(yollar: list[str]) -> list[str]:
    """Bicim kapisi: pytest ARGV'sine girmesi GUVENLI olmayan degerleri dondur.

    Defter bir VERI dosyasi ve degeri dogrudan pytest'in argumanlarina gidiyor.
    "backend/....py" olmayan bir satir pytest BAYRAGINA donusebilir (`-p x`,
    `--co`) ve kapiyi sessizce etkisizlestirebilirdi. Bu yuzden bicim once
    dogrulanir, sonra subprocess'e verilir (shell=False, liste arguman).

    Ayri fonksiyon cunku `main()` sonunda pytest cagiriyor; kapinin kendisini
    test etmek pytest'i tekrar baslatmadan mumkun olmali (ozyineleme yok).

    OLCULDU (S232): burada bir de `y.startswith("-")` dali vardi. Mutasyonla
    silindiginde **16/16 test yine gecti** — cunku bir bayrak (`-p x`, `--co`)
    zaten hem `backend/` on ekini hem `.py` sonekini saglayamaz, yani iki kural
    tarafindan cift kapsaniyor. Hicbir mutasyonla civilenemeyen dal = test
    edilemez agirlik (`L-s214-select-from-her-yerde-degil`), o yuzden KALDIRILDI.
    Geri eklemeden once ayni olcumu tekrarla: dali silip testleri kosur, biri
    kirmiziya donmuyorsa dal bir sey yapmiyordur.
    """
    return [
        y
        for y in yollar
        if ".." in y or not y.startswith("backend/") or not y.endswith(".py")
    ]


# ---------------------------------------------------------------------------
# DSN ENJEKSIYONU — A3 (19 Agu 2026)
#
# OLCULDU: kapi 19 dosya kosuyordu ama `tests/db/test_question_bank_invariants.py`
# her push'ta `sss` (3 skipped, EXIT=0) veriyordu — DSN ve STRICT bayragi yoktu.
# Yani "19 bekci her push'ta" bir DOSYA sayimiydi, ASSERT sayimi degil; hacim ve
# benzersizlik invaryantlari kapaliydi.
#
# STRICT'i KOSULSUZ acmiyoruz: o dosyanin docstring'i (12 Agu) taze bir makinede
# icerik olmamasinin MESRU oldugunu belgeliyor ve her kosumu kirmak gurultu olur.
# Bu yuzden ikisi de yalnizca GERCEK bir postgres DSN cozulunce set edilir.
# ---------------------------------------------------------------------------

# sqlite/aiosqlite: `backend/conftest.py` DATABASE_URL'i buna eziyor. Boyle bir
# DSN'i kabul etmek YANLIS bir DB'yi olcmek olur (`L-s229-test-dsn-sessizce-sqlite-olur`).
_SAHTE_MOTOR_ISARETLERI = ("sqlite", ":memory:")

# `tests/e2e/pg_dsn.py::resolve_pg_dsn` ile AYNI oncelik sirasi.
_DSN_ANAHTARLARI = ("KVKK_VERIFY_DSN", "DATABASE_URL_SYNC", "DATABASE_URL")


def _postgres_mu(dsn: str | None) -> bool:
    """Gercek bir PostgreSQL DSN'i mi — taklit motor DEGIL."""
    if not dsn:
        return False
    d = dsn.strip().strip("\"'").lower()
    if any(m in d for m in _SAHTE_MOTOR_ISARETLERI):
        return False
    return d.startswith("postgresql")


def _env_dosyasi_ayristir(metin: str | None) -> dict[str, str]:
    """`KEY=VALUE` satirlarini oku. Yorum/bos satir atlanir, tirnak soyulur."""
    if not metin:
        return {}
    cikti: dict[str, str] = {}
    for satir in metin.splitlines():
        s = satir.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        anahtar, _, deger = s.partition("=")
        cikti[anahtar.strip()] = deger.strip().strip("\"'")
    return cikti


def dsn_maskele(dsn: str) -> str:
    """Parolayi gizle ama teshis degerini (host/port/db) KORU.

    Kapi her push'ta stdout'a yaziyor; DSN parolasi oraya dusmemeli. Bu depoda
    ayni sinif bir kez yasandi: celery logunda duz-metin DB parolasi (#475).
    """
    if "@" not in dsn or "://" not in dsn:
        return dsn
    sema, _, kalan = dsn.partition("://")
    kimlik, _, adres = kalan.rpartition("@")
    if ":" in kimlik:
        kullanici = kimlik.split(":", 1)[0]
        kimlik = f"{kullanici}:***"
    return f"{sema}://{kimlik}@{adres}"


def dsn_ortami_uret(
    mevcut_env: dict[str, str], env_dosyasi_metni: str | None
) -> dict[str, str]:
    """pytest alt surecine eklenecek ortam degiskenlerini uret.

    Once mevcut ortam (operator elle verdiyse EZILMEZ), sonra `backend/.env`.
    Gercek postgres DSN bulunamazsa BOS dondurur — sessizce sqlite'a DUSULMEZ
    ve STRICT acilmaz (DB'siz makinede push bloklanmaz).
    """
    dosya = _env_dosyasi_ayristir(env_dosyasi_metni)
    for kaynak in (mevcut_env, dosya):
        for anahtar in _DSN_ANAHTARLARI:
            aday = kaynak.get(anahtar)
            if _postgres_mu(aday):
                # Surucu donusumu (postgresql:// -> postgresql+asyncpg://) BURADA
                # YAPILMAZ; tek tanim tuketicide (`tests/e2e/pg_dsn.py`). Ikinci
                # bir tanim ayrisirsa hangisinin kostugu olculemez hale gelir.
                return {
                    "KVKK_VERIFY_DSN": aday.strip().strip("\"'"),
                    "KIRO2_STRICT_DB_INVARIANTS": "1",
                }
    return {}


def main() -> int:
    if not DEFTER.exists():
        print(f"HATA: ders defteri yok: {DEFTER}", file=sys.stderr)
        return 1

    yollar = zorlayicilari_topla()
    if not yollar:
        # Bos liste bir BULGU degil, ALET ARIZASI adayidir (bu deponun dersi).
        print(
            "HATA: defterde hic `zorlayici` bulunamadi — ayrıştırıcı bozuk olabilir",
            file=sys.stderr,
        )
        return 1

    bicimsiz = bicim_gecersizleri(yollar)
    if bicimsiz:
        print(
            "HATA: defterdeki zorlayici degeri gecersiz bicimde "
            "(`backend/...py` olmali, bayrak/ust-dizin YASAK):",
            file=sys.stderr,
        )
        for y in bicimsiz:
            print(f"  {y!r}", file=sys.stderr)
        return 1

    # Defter YALAN SOYLUYOR mu: isaret edilen dosya diskte var mi?
    eksik = [y for y in yollar if not (DEPO_KOKU / y).exists()]
    if eksik:
        print("HATA: defterdeki zorlayici dosyalari DISKTE YOK:", file=sys.stderr)
        for y in eksik:
            print(f"  {y}", file=sys.stderr)
        print("Ders ya duzeltilmeli ya `zorlayici: null` yapilmali.", file=sys.stderr)
        return 1

    # pytest'e backend/ koku uzerinden goreli yol ver
    goreli = [str(Path(y).relative_to("backend")) for y in yollar]
    print(f"[ders-zorlayici] defterden {len(goreli)} bekci dosyasi turetildi")

    env_dosyasi = BACKEND / ".env"
    metin = (
        env_dosyasi.read_text(encoding="utf-8", errors="replace")
        if env_dosyasi.exists()
        else None
    )
    ek_ortam = dsn_ortami_uret(dict(os.environ), metin)
    if ek_ortam:
        print(
            "[ders-zorlayici] DB invaryantlari OLCULECEK — DSN: "
            f"{dsn_maskele(ek_ortam['KVKK_VERIFY_DSN'])}"
        )
    else:
        # Sessiz skip bu deponun tekrar eden kusuru: olcmeyen bekci koruma
        # SAGLAMAZ ama yesil gorunur. Push'u bloklamiyoruz (taze makine mesru),
        # ama durum GORUNUR olmali.
        print(
            "[ders-zorlayici] UYARI: gercek postgres DSN cozulemedi -> "
            "question_bank invaryant bekcileri SKIP edecek. Bu makinede icerik "
            "OLMASI gerekiyorsa backend/.env icindeki DSN'i kontrol et.",
            file=sys.stderr,
        )

    # noqa/nosec gerekcesi: shell=False + liste arguman (kabuk enjeksiyonu YOK),
    # ikili `sys.executable` (PATH'ten cozulmuyor), ve her yol yukaridaki bicim
    # kapisindan gecti. Girdi "untrusted" degil: depo icindeki bir defter satiri.
    sonuc = subprocess.run(  # noqa: S603  # nosec B603
        [
            sys.executable,
            "-m",
            "pytest",
            *goreli,
            "-n0",
            "-q",
            "--no-header",
            "--timeout=180",
        ],
        cwd=BACKEND,
        check=False,
        env={**os.environ, **ek_ortam},
    )
    if sonuc.returncode != 0:
        print(
            "\n[ders-zorlayici] BEKCI KIRMIZI — push bloke. "
            "Ya kusur gercek, ya ders bayat: ikisinden birini duzelt.",
            file=sys.stderr,
        )
    return sonuc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
