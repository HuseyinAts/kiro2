"""Kitabin uc migration'ini profilden ve olculen JSON'lardan URETIR.

  <n>_<kod>_konu_agaci.py   : kitabin bolum / konu agaci (konu_haritasi.json)
  <n+1>_<kod>_eski_hat_pasif : modern karsiligi olan eski hat satirlari pasif
                               (mukerrer_adaylari.json eski_hat, modern id guard)
  <n+2>_<kod>_beta_onay      : toplu beta sahibi onayi (dislama kurali sabit)

Desen 0074 / 0075 / 0076 (acil2021tyt) ile birebir; yalniz kitap sabitleri
degisir. Sablonlar `kitap_hat/sablon/*.tmpl` duz metindir; `@@AD@@`
belirtecleri str.replace ile doldurulur (kod icinde SQL bicimlendirilmez).
Beta hedef sayisi ithal + eski hat pasif SONRASI yerel DB'de olculup
(`beta_olc`) `--beta-hedef N/M` ile verilir (baslikta yazilir; test dogrular).
Uretilen dosyalar sonra `ruff format` ile bicimlenir.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.migration_uret --profil K --no 77 \
        --onceki 0076_acl21t_beta_onay --tarih 2026-09-28 \
        [--beta-hedef 300/350 --beta-olcum olcum.txt]
"""

from __future__ import annotations

import argparse
import re
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.metin_olcum import soru_hash

VERSIYON = ortak.KOK / "backend" / "alembic" / "versions"
SABLON = Path(__file__).resolve().parent / "sablon"


def _kac(s: str) -> str:
    """Python kaynak literali: ASCII, Turkce harf kacisli."""
    out = []
    for c in s:
        if c in '\\"':
            out.append("\\" + c)
        elif ord(c) < 128:
            out.append(c)
        else:
            out.append("\\u" + format(ord(c), "04x"))
    return '"' + "".join(out) + '"'


def _ic(s: str) -> str:
    """Tirnaksiz ASCII kacisli metin (docstring icin)."""
    return _kac(s)[1:-1]


def adlar(p: ModuleType, no: int) -> dict[str, str]:
    k = p.KOD.lower()
    return {
        "agac_dosya": f"{no:04d}_{k}_konu_agaci.py",
        "agac_rev": f"{no:04d}_{k}_agac",
        "eski_dosya": f"{no + 1:04d}_{k}_eski_hat_pasif.py",
        "eski_rev": f"{no + 1:04d}_{k}_eski_hat_pasif",
        "beta_dosya": f"{no + 2:04d}_{k}_beta_onay.py",
        "beta_rev": f"{no + 2:04d}_{k}_beta_onay",
    }


def doldur(sablon: str, degerler: dict[str, Any], no: int) -> str:
    metin = (SABLON / f"{sablon}.tmpl").read_text("ascii")
    sayac = (SABLON / "sayac.tmpl").read_text("ascii")
    degerler = {**degerler, "SAYAC": sayac, "NO": f"{no:04d}"}
    for _ in range(2):  # SAYAC icindeki @@NO@@ ikinci turda dolar
        for k, v in degerler.items():
            metin = metin.replace(f"@@{k}@@", str(v))
    kalan = re.findall(r"@@[A-Z_]+@@", metin)
    if kalan:
        raise SystemExit(f"{sablon}: doldurulmamis belirtec {sorted(set(kalan))}")
    return metin


def _ortak_degerler(p: ModuleType, tarih: str) -> dict[str, Any]:
    return {
        "KAYNAK_ADI": _ic(p.KAYNAK_ADI),
        "KAYNAK_LITERAL": _kac(p.KAYNAK_ADI),
        "KOD": p.KOD,
        "KOD_KUCUK": p.KOD.lower(),
        "KOD_ONEKI": p.KOD_ONEKI,
        "KOK_KOD": p.KOK_KOD,
        "ALAN": p.ALAN,
        "CIKTI_ONEK": p.CIKTI_ONEK,
        "TARIH": tarih,
    }


def agac(p: ModuleType, no: int, onceki: str, tarih: str) -> str:
    h = ortak.oku(p, "konu_haritasi")
    a = adlar(p, no)
    return doldur(
        "agac",
        {
            **_ortak_degerler(p, tarih),
            "REV": a["agac_rev"],
            "ONCEKI": onceki,
            "TEST_SAYISI": h["test_sayisi"],
            "SORU_SAYISI": sum(t["soru_sayisi"] for t in h["testler"]),
            "BOLUMLER": "\n".join(
                f"    ({_kac(b['kod'])}, {_kac(b['ad'])})," for b in h["bolumler"]
            ),
            "KONULAR": "\n".join(
                f"    ({_kac(k['kod'])}, {_kac(k['ad'])}, {_kac(k['bolum'])}),"
                for k in h["konular"]
            ),
        },
        no,
    )


def eski_ciftleri(p: ModuleType) -> list[tuple[str, str, str, Any]]:
    muk = ortak.oku(p, "mukerrer_adaylari")
    metin = {s["dosya"]: s for s in ortak.oku(p, "metin")["sorular"]}
    out = []
    for e in muk["eski_hat"]:
        if not e["modern_karsilik"]:
            continue
        s = metin[e["en_yakin_bizim"]]
        h = soru_hash(s["govde"], {x: s["sikler"][x] for x in "ABCDE"})
        out.append(
            (
                e["db_id"],
                e["en_yakin_bizim"].removeprefix(f"{p.KOD}-"),
                str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
                e["basili_sayfa"],
            )
        )
    return out


def eski(p: ModuleType, no: int, tarih: str) -> str:
    a = adlar(p, no)
    muk = ortak.oku(p, "mukerrer_adaylari")
    return doldur(
        "eski",
        {
            **_ortak_degerler(p, tarih),
            "REV": a["eski_rev"],
            "ONCEKI": a["agac_rev"],
            "OZET": "\n".join(
                f"    {_ic(k)}: {v['satir']} satir, {v['aktif']} aktif, "
                f"{v['modern_karsilik']} modern karsilik"
                for k, v in muk["eski_hat_ozet"].items()
            ),
            "ESKI_KAYNAKLAR": "\n".join(f"    {_kac(k)}," for k in p.ESKI_KAYNAKLAR),
            "ESKI_MODERN": "\n".join(
                f"    ({_kac(e)}, {_kac(k)}, {_kac(m)}),  # s{s}"
                for e, k, m, s in eski_ciftleri(p)
            ),
        },
        no + 1,
    )


def beta(p: ModuleType, no: int, tarih: str, hedef: str, olcum: str) -> str:
    a = adlar(p, no)
    ham = ortak.oku(p, "ham_okumalar")
    io = ortak.oku(p, "ikinci_okuma")["sonuc"]
    return doldur(
        "beta",
        {
            **_ortak_degerler(p, tarih),
            "REV": a["beta_rev"],
            "ONCEKI": a["eski_rev"],
            "HEDEF": hedef,
            "OLCUM": olcum,
            "YONTEM_BELGESI": p.YONTEM_BELGESI,
            "HUCRE": sum(len(t["hucreler"]) for t in ham["okuma_a"]["testler"]),
            "GLIF_UYUM": ham["glif"]["uyum"],
            "GLIF_HUCRE": ham["glif"]["hucre"],
            "GLIF_DISI": len(ham["glif"]["kapsam_disi_test"]),
            "FARKLI_SORU": io["farkli_soru"],
        },
        no + 2,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("--no", type=int, required=True)
    ap.add_argument("--onceki", required=True)
    ap.add_argument("--tarih", required=True)
    ap.add_argument("--beta-hedef", default=None, help="N/M")
    ap.add_argument("--beta-olcum", default="", help="kapi yuku olcum metni dosyasi")
    a = ap.parse_args()
    p = ortak.profil(a.profil)
    ad = adlar(p, a.no)
    for rev in ("agac_rev", "eski_rev", "beta_rev"):
        if len(ad[rev]) > 32:
            raise SystemExit(f"revizyon adi 32'yi asiyor: {ad[rev]}")
    (VERSIYON / ad["agac_dosya"]).write_text(agac(p, a.no, a.onceki, a.tarih), "ascii")
    (VERSIYON / ad["eski_dosya"]).write_text(eski(p, a.no, a.tarih), "ascii")
    print("yazildi", ad["agac_dosya"], ad["eski_dosya"])
    if a.beta_hedef:
        olcum = Path(a.beta_olcum).read_text("ascii").rstrip() if a.beta_olcum else ""
        (VERSIYON / ad["beta_dosya"]).write_text(
            beta(p, a.no, a.tarih, a.beta_hedef, olcum), "ascii"
        )
        print("yazildi", ad["beta_dosya"])


if __name__ == "__main__":
    main()
