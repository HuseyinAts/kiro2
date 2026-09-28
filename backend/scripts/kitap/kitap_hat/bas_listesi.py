"""Iki gecisli test siniri ('Matematigin Ilaci' duzeni: her sayfanin kendi seridi,
numara sayfalar boyunca surer) -- 1. gecis okumalarindan BAS_SAYFALARI.

AKIS
----
1. Profilde `TEST_SINIRI = "bas_listesi"`, `BAS_SAYFALARI = tuple(range(1, N+1))`
   (her test sayfasi ayri birim) ile `tarama --yaz`; serit okumalari A / B
   (sayfa basina) `<VERAF>_serit/okuma_A.json`, `okuma_B.json`.
2. `bas_listesi --profil K gecis1`: A == B, sayfa capa == hucre, seridi '1.'
   ile baslayan sayfalar (BAS), numara ardisikligi. Kapi: fark varsa exit 1.
3. `bas_listesi --profil K yaz`: profildeki BAS_SAYFALARI / BEKLENEN_TEST
   satirlarini olculen listeyle degistirir.
4. `tarama --yaz` (test = bas sayfasindan sonrakine kadar).
5. `bas_listesi --profil K grupla`: sayfa birimli okuma_A/B'yi
   okuma_A/B_sayfa.json'a tasir, yeni testlere gore birlestirilmis okuma_A/B yazar.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.bas_listesi --profil K gecis1|yaz|grupla
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any

from scripts.kitap.kitap_hat import ortak


def serit_dizini(p: ModuleType) -> Path:
    return Path(ortak.VERAFILM / f"{p.VERAF}_serit")


def okuma(p: ModuleType, k: str, sayfa: bool = False) -> list[dict]:
    ad = f"okuma_{k}_sayfa.json" if sayfa else f"okuma_{k}.json"
    testler: list[dict] = json.loads((serit_dizini(p) / ad).read_text("utf-8"))[
        "testler"
    ]
    return testler


def baski_duzelt(
    p: ModuleType, sayfa_okuma: list[dict], test_sayfalari: list[int]
) -> list[dict]:
    """Profilin SERIT_NUMARA_BASKI_HATASI listesi: {sayfa: (basili, sira)}.
    Kitapta yanlis basilmis serit numaralari (ornek '6 7 8 10 11 12', 6 iki
    kez / 9 yok) sayfa okumasinda sira numarasiyla degistirilir; okunan basili
    dizi profildekiyle AYNI olmali (yoksa exit). Harfler dokunulmaz."""
    hata = getattr(p, "SERIT_NUMARA_BASKI_HATASI", {})
    if not hata:
        return sayfa_okuma
    by = dict(zip(test_sayfalari, sayfa_okuma, strict=True))
    out = [dict(t) for t in sayfa_okuma]
    yeni = dict(zip(test_sayfalari, out, strict=True))
    for n, (basili, sira) in hata.items():
        h = by[n]["hucreler"]
        if tuple(x[0] for x in h) != tuple(basili):
            raise SystemExit(
                f"s{n}: okunan numaralar {[x[0] for x in h]} != profil {basili}"
            )
        yeni[n]["hucreler"] = [[s, x[1]] for s, x in zip(sira, h, strict=True)]
    return out


def gecis1_olc(
    okuma_a: list[dict], okuma_b: list[dict], testler: list[dict]
) -> dict[str, Any]:
    """Sayfa birimli iki okuma + tarama testleri -> fark listeleri ve bas sayfalari.

    okuma_a/b: [{test, konu, test_no, hucreler: [[no, harf], ...]}]; testler:
    capa_taramasi['testler'] (1. geciste her test tek sayfa)."""
    a = {t["test"]: t for t in okuma_a}
    b = {t["test"]: t for t in okuma_b}
    hucre_farki = [i for i in a if a[i]["hucreler"] != b.get(i, {}).get("hucreler")]
    bant_farki = [
        i
        for i in a
        if i in b and (a[i]["konu"], a[i]["test_no"]) != (b[i]["konu"], b[i]["test_no"])
    ]
    bas: list[int] = []
    capa_farki: list[tuple[int, int, int, int | None]] = []
    kopuk: list[tuple[int, list[int]]] = []
    onceki: tuple[int, int] | None = None
    for t in testler:
        i, n = t["test"], t["sayfalar"][0]
        h = a[i]["hucreler"] if i in a else []
        nums = [x[0] for x in h]
        if nums and nums[0] == 1:
            bas.append(n)
        if len(h) != len(t["capalar"]):
            capa_farki.append((n, len(t["capalar"]), len(h), nums[0] if nums else None))
        # sayfa ici ardisik degil YA DA devam sayfasi onceki sayfanin son+1'i degil
        ardisik = nums == list(range(nums[0], nums[0] + len(nums))) if nums else True
        devam_kopuk = (
            bool(nums)
            and nums[0] != 1
            and (onceki is None or onceki[0] != n - 1 or onceki[1] + 1 != nums[0])
        )
        if not ardisik or devam_kopuk:
            kopuk.append((n, nums))
        if nums:
            onceki = (n, nums[-1])
    return {
        "hucre_farki": hucre_farki,
        "bant_farki": bant_farki,
        "capa_farki": capa_farki,
        "kopuk": kopuk,
        "bas": bas,
    }


def profil_yaz(prof: Path, bas: list[int]) -> None:
    s = prof.read_text("ascii")
    s, n1 = re.subn(
        r"^BAS_SAYFALARI.*$",
        "BAS_SAYFALARI: tuple[int, ...] = " + repr(tuple(bas)),
        s,
        flags=re.M,
    )
    s, n2 = re.subn(
        r"^BEKLENEN_TEST = \d+$", f"BEKLENEN_TEST = {len(bas)}", s, flags=re.M
    )
    if n1 != 1 or n2 != 1:
        raise SystemExit(
            f"profilde BAS_SAYFALARI / BEKLENEN_TEST satiri bulunamadi ({n1}, {n2})"
        )
    prof.write_text(s, "ascii")


def grupla(sayfa_okuma: list[dict], tarama: dict[str, Any]) -> list[dict]:
    """Sayfa birimli okumayi (1. gecis test sirasi = test sayfalari artan)
    2. gecis testlerine gore birlestirir: konu/test_no ilk sayfadan, hucreler
    sayfa sirasiyla ard arda."""
    sayfa_sira = sorted(
        int(n) for n, v in tarama["sayfalar"].items() if v["tur"] == "test"
    )
    if len(sayfa_sira) != len(sayfa_okuma):
        raise SystemExit(
            f"test sayfasi {len(sayfa_sira)} != sayfa okumasi {len(sayfa_okuma)}"
        )
    by = dict(zip(sayfa_sira, sayfa_okuma, strict=True))
    out = []
    for t in tarama["testler"]:
        ilk = by[t["sayfalar"][0]]
        h = [c for n in t["sayfalar"] for c in by[n]["hucreler"]]
        out.append(
            {
                "test": t["test"],
                "konu": ilk["konu"],
                "test_no": ilk["test_no"],
                "hucreler": h,
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("komut", choices=["gecis1", "yaz", "grupla"])
    args = ap.parse_args()
    p = ortak.profil(args.profil)
    tarama = ortak.oku(p, "capa_taramasi")
    sayfa_sira = sorted(
        int(n) for n, v in tarama["sayfalar"].items() if v["tur"] == "test"
    )
    if args.komut in ("gecis1", "yaz"):
        # grupla sonrasi okuma_A/B test birimlidir; ham sayfa okumasi _sayfa'da.
        ham = (serit_dizini(p) / "okuma_A_sayfa.json").exists()
        v = gecis1_olc(
            baski_duzelt(p, okuma(p, "A", sayfa=ham), sayfa_sira),
            baski_duzelt(p, okuma(p, "B", sayfa=ham), sayfa_sira),
            tarama["testler"],
        )
        print("A!=B hucre:", v["hucre_farki"])
        print("bant farki:", v["bant_farki"][:30])
        print("capa != hucre (sayfa, capa, hucre, ilk no):", v["capa_farki"])
        print("ardisiklik kopuk (sayfa, numaralar):", v["kopuk"][:20])
        print("BAS", len(v["bas"]))
        print("BAS_SAYFALARI =", tuple(v["bas"]))
        if v["hucre_farki"] or v["capa_farki"] or v["kopuk"]:
            raise SystemExit(1)
        if args.komut == "yaz":
            profil_yaz(Path(p.__file__), v["bas"])
            print(
                f"profil yazildi: BAS_SAYFALARI {len(v['bas'])}, BEKLENEN_TEST {len(v['bas'])}"
            )
        return
    o = serit_dizini(p)
    for k in "AB":
        f, fs = o / f"okuma_{k}.json", o / f"okuma_{k}_sayfa.json"
        if not fs.exists():
            fs.write_text(f.read_text("utf-8"), "utf-8")
        out = grupla(baski_duzelt(p, okuma(p, k, sayfa=True), sayfa_sira), tarama)
        f.write_text(
            json.dumps({"okuyucu": k, "testler": out}, ensure_ascii=False), "utf-8"
        )
        print(k, len(out), sum(len(x["hucreler"]) for x in out))


if __name__ == "__main__":
    main()
