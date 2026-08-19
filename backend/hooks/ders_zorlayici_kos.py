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

Ölçülen maliyet (19 Ağu 2026): 18 dosya / 162 passed + 8 xfailed.
"""

from __future__ import annotations

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
