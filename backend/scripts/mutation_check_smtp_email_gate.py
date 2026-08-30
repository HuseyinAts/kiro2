"""Mutasyon testi — SMTP `send_email`/`smtp_yapilandirilmis_mi` kapısı gerçekten hassas mı?

Yeşil bir test, ölçtüğünü sandığı şeyi ölçmüyor olabilir (#466: doğrulayıcı
`SMTP_HOST` okuyordu, tüketici `SMTP_SERVER` -- kapı "hazır" derken gönderim
sessizce atlanıyordu). Bu script `core/email_util.py` ve
`core/eposta_dogrulama.py`'yi sırayla, TEK TEK geçici olarak BOZAR, hedef
testleri koşar ve doğru testlerin KIRMIZIYA döndüğünü doğrular; sonra her
mutasyonu `git checkout` ile harfi harfine geri yükler ve geri yüklemeyi
`git status` ile doğrular.

Kullanım:
    cd backend && python scripts/mutation_check_smtp_email_gate.py

Çıkış kodu 0 = her mutasyon yakalandı. 1 = taban zaten kırmızı, ankraj tekil
değil, en az bir mutasyon fark edilmedi (o değişmez test edilmiyor demektir),
veya geri alım doğrulanamadı.
"""

from __future__ import annotations

import subprocess  # nosec - yalnız sabit pytest/git komutları koşturur, dış girdi yok
import sys
from pathlib import Path
from typing import TypedDict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

BACKEND = Path(__file__).resolve().parent.parent
KOK = BACKEND.parent
HEDEF = [
    "tests/unit/test_eposta_kapi_sirasi.py",
    "tests/unit/test_eposta_dogrulama.py",
]


class _Mutasyon(TypedDict):
    ad: str
    dosya: str
    eski: list[str]
    yeni: list[str]
    beklenen_en_az: int


MUTASYONLAR: list[_Mutasyon] = [
    {
        "ad": "M1 SMTP on kosulu kaldirilir (sira yaptirimi olur)",
        "dosya": "core/eposta_dogrulama.py",
        "eski": ["    if not smtp_yapilandirilmis_mi():"],
        "yeni": ["    if False:"],
        "beklenen_en_az": 2,
    },
    {
        "ad": "M2 SMTP kontrolu GEVSETILIR (yalniz host) -- #466 ayrismasi",
        "dosya": "core/email_util.py",
        "eski": ["    return all(_smtp_kimlik())"],
        "yeni": ["    return bool(_smtp_kimlik()[0])"],
        "beklenen_en_az": 2,
    },
    {
        "ad": "M3 gurultu susturulur (sessiz varsayilan)",
        "dosya": "core/eposta_dogrulama.py",
        "eski": [
            '        logger.error("E-posta doğrulama kapısı AÇILAMADI: %s", engel)'
        ],
        "yeni": ["        pass"],
        "beklenen_en_az": 1,
    },
    {
        "ad": "M4 send_email kendi kontrolune geri doner (tek kaynak bozulur)",
        "dosya": "core/email_util.py",
        "eski": ["    if not smtp_yapilandirilmis_mi():"],
        "yeni": ["    if not (smtp_server and smtp_username):"],
        "beklenen_en_az": 1,
    },
]


def satir_sonu(veri: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in veri else b"\n"


def kosum() -> tuple[int, str]:
    sonuc = subprocess.run(  # nosec - sabit pytest komutu, dis girdi yok
        [
            sys.executable,
            "-m",
            "pytest",
            *HEDEF,
            "-q",
            "--tb=no",
            "-p",
            "no:cacheprovider",
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    cikti = sonuc.stdout or ""
    dusen = sum(1 for s in cikti.splitlines() if s.startswith(("FAILED ", "ERROR ")))
    ozet = next(
        (s for s in reversed(cikti.splitlines()) if " passed" in s or " failed" in s),
        "(ozet yok)",
    )
    return dusen, ozet.strip()


def geri_al(bagil: str) -> bool:
    # yol MUTASYONLAR'daki sabit degerlerden gelir, dis girdi yok
    subprocess.run(  # nosec - sabit git komutu, dis girdi yok
        ["git", "checkout", "HEAD", "--", f"backend/{bagil}"], cwd=KOK, check=True
    )
    return (
        subprocess.run(  # nosec - sabit git komutu, dis girdi yok
            ["git", "status", "--short", "--untracked-files=no", f"backend/{bagil}"],
            cwd=KOK,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        == ""
    )


def main() -> int:
    print("=== TABAN (mutasyonsuz) ===")
    dusen, ozet = kosum()
    print(f"  {ozet}")
    if dusen:
        print(f"  !!! TABAN KIRMIZI ({dusen}) -- olcum gecersiz")
        return 1

    olduruldu = 0
    for m in MUTASYONLAR:
        yol = BACKEND / m["dosya"]
        veri = yol.read_bytes()
        se = satir_sonu(veri)
        ankraj = se.join(s.encode("utf-8") for s in m["eski"])
        adet = veri.count(ankraj)
        print(f"\n{m['ad']}")
        if adet != 1:
            print(f"  !!! ANKRAJ TEKIL DEGIL (adet={adet}) -- OLCUM GECERSIZ")
            continue
        yol.write_bytes(
            veri.replace(ankraj, se.join(s.encode("utf-8") for s in m["yeni"]))
        )
        dusen, ozet = kosum()
        temiz = geri_al(m["dosya"])
        oldu = dusen >= m["beklenen_en_az"]
        olduruldu += 1 if oldu else 0
        print(f"  pytest: {ozet}")
        print(f"  dusen : {dusen} (en az {m['beklenen_en_az']})")
        print(f"  yargi : {'OLDU' if oldu else 'HAYATTA KALDI'}")
        print(f"  geri alim dogrulandi: {temiz}")
        if not temiz:
            print("  !!! GERI ALIM BASARISIZ -- DUR")
            return 1

    print(f"\n=== SONUC: {olduruldu}/{len(MUTASYONLAR)} ===")
    return 0 if olduruldu == len(MUTASYONLAR) else 1


if __name__ == "__main__":
    raise SystemExit(main())
