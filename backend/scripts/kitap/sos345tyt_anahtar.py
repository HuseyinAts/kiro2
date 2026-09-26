#!/usr/bin/env python
"""345 2025 TYT Sosyal Bilgiler: cevap anahtari (Faz 1) -- ham okumalardan turer.

KAYNAK
------
Kitabin sonundaki basili CEVAP ANAHTARI tablosu (s306-312): 30 GUN x
'OSYM TADINDA SORULAR k' satirlari, hucreler '1.C 2.B ...'. Sayfa alti
serit YOK.

KANALLAR
--------
1. Iki bagimsiz okuma (A: sayfa sirasi; B: parcalar alttan uste, satirlar
   sagdan sola), sayfa basina ayri okuyucu, 2.5x.
2. Fark varsa goz karari (5x); karar A ya da B'den biri olmak ZORUNDA.
3. Piksel glif en-yakin-komsu LOO (ekran goruntusu ister; sonucu ham
   dosyada kayitli, burada yalniz dogrulanir).
4. Hucre sayisi == okuyucu simgesi sayisi (capa taramasi): test test,
   sayfa sirasinda simgeler anahtar sayilariyla tuketilir.

Soru cozulmez; tek kaynak basili tablo.

CIKTI
-----
veriseti/zkitap/cikti/345_2025_tyt_sosyal_cevap_anahtari.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_sosyal_"
HAM = CIKTI / f"{ON}ham_okumalar.json"
TARAMA = CIKTI / f"{ON}capa_taramasi.json"
HEDEF = CIKTI / f"{ON}cevap_anahtari.json"
ONEK = "SOS345"
BEKLENEN_TEST = 150
BEKLENEN_SORU = 1233
_YER = re.compile(r"^G(\d{2})T(\d+)#(\d+)$")


def iki_okuma(ham: dict) -> dict[tuple[int, int], tuple[str, str]]:
    """(gun, test) -> (A, B) harf dizileri; anahtar kumeleri esit olmali."""
    a = {(x["gun"], x["test"]): x["cevaplar"] for x in ham["anahtar_okumalari"]["A"]}
    b = {(x["gun"], x["test"]): x["cevaplar"] for x in ham["anahtar_okumalari"]["B"]}
    if len(a) != len(ham["anahtar_okumalari"]["A"]) or len(b) != len(
        ham["anahtar_okumalari"]["B"]
    ):
        raise SystemExit("ayni (gun, test) iki kez okunmus")
    if set(a) != set(b):
        raise SystemExit(f"A/B test kumesi farkli: {sorted(set(a) ^ set(b))[:5]}")
    for k, av in a.items():
        for s in (av, b[k]):
            if not re.fullmatch(r"[ABCDE]+", s):
                raise SystemExit(f"{k}: bicim disi girdi {s!r}")
        if len(av) != len(b[k]):
            raise SystemExit(f"{k}: A/B hucre sayisi farkli")
    return {k: (a[k], b[k]) for k in a}


def birlestir(okumalar: dict, farklar: dict[str, str]) -> dict[tuple[int, int], str]:
    """A == B ise o; degilse goz karari (A ya da B'den biri). Kararsiz fark durur."""
    kullanilan = set()
    out = {}
    for (g, t), (a, b) in okumalar.items():
        harf = []
        for i, (x, y) in enumerate(zip(a, b, strict=True), 1):
            yer = f"G{g:02d}T{t}#{i}"
            if x == y:
                if yer in farklar:
                    raise SystemExit(f"{yer}: gereksiz goz karari (A == B)")
                harf.append(x)
                continue
            if yer not in farklar:
                raise SystemExit(f"{yer}: A/B farki ({x}/{y}) goz karari yok")
            k = farklar[yer]
            if k not in (x, y):
                raise SystemExit(f"{yer}: goz karari {k} ne A ne B")
            kullanilan.add(yer)
            harf.append(k)
        out[(g, t)] = "".join(harf)
    if set(farklar) - kullanilan:
        raise SystemExit(
            f"kullanilmayan goz karari: {sorted(set(farklar) - kullanilan)}"
        )
    return out


def simge_sirasi(tarama: dict) -> list[tuple[int, str, int]]:
    """Sayfa sirasi, sutun L sonra R, yukaridan asagi: (sayfa, sutun, sira)."""
    out = []
    for n in sorted(int(k) for k in tarama["sayfalar"]):
        s = tarama["sayfalar"][str(n)]
        for t in ("L", "R"):
            for i, _ in enumerate(sorted(s["simge"][t])):
                out.append((n, t, i))
    return out


def cevaplar_uret(anahtar: dict[tuple[int, int], str], simgeler: list) -> list[dict]:
    """Testler (gun, test) sirasinda simgeleri tuketir; SOS345-Tnnn ardisik birim."""
    if sum(len(v) for v in anahtar.values()) != len(simgeler):
        raise SystemExit(
            f"hucre {sum(len(v) for v in anahtar.values())} != simge {len(simgeler)}"
        )
    out, i = [], 0
    for sira, ((g, t), harf) in enumerate(sorted(anahtar.items()), 1):
        birim = f"{ONEK}-T{sira:03d}"
        for j, c in enumerate(harf, 1):
            n, sut, s = simgeler[i]
            i += 1
            out.append(
                {
                    "birim": birim,
                    "soru": j,
                    "cevap": c,
                    "gun": g,
                    "test": t,
                    "dosya": n,
                    "sutun": sut,
                    "sutun_sira": s,
                }
            )
    return out


def glif_dogrula(ham: dict, cevaplar: list[dict]) -> None:
    gl = ham["glif"]
    if gl["hucre"] != len(cevaplar) or gl["uyum"] != gl["hucre"] or gl["uyumsuz"]:
        raise SystemExit("glif kanali tam uyumlu degil")


def main() -> None:
    ham = json.loads(HAM.read_text("ascii"))
    tarama = json.loads(TARAMA.read_text("ascii"))
    ok = iki_okuma(ham)
    anahtar = birlestir(ok, ham["goz_kararlari"]["farklar"])
    if len(anahtar) != BEKLENEN_TEST:
        raise SystemExit(f"test {len(anahtar)} != {BEKLENEN_TEST}")
    cev = cevaplar_uret(anahtar, simge_sirasi(tarama))
    if len(cev) != BEKLENEN_SORU:
        raise SystemExit(f"soru {len(cev)} != {BEKLENEN_SORU}")
    glif_dogrula(ham, cev)
    ayni = sum(1 for a, b in ok.values() for x, y in zip(a, b, strict=True) if x == y)
    veri = {
        "kaynak": "345 2025 TYT Sosyal Bilgiler Soru Bankasi",
        "arac": "scripts/kitap/sos345tyt_anahtar.py",
        "nereden": "kitap sonu cevap anahtari tablosu (s306-312)",
        "dogrulama": {
            "a_esittir_b_hucre": ayni,
            "goz_karari": len(ham["goz_kararlari"]["farklar"]),
            "glif_loo_uyum": ham["glif"]["uyum"],
            "hucre_sayisi_esittir_simge": True,
        },
        "toplam_cevap": len(cev),
        "test_sayisi": len(anahtar),
        "harf_dagilimi": {h: sum(1 for c in cev if c["cevap"] == h) for h in "ABCDE"},
        "cevaplar": cev,
    }
    HEDEF.write_text(
        json.dumps(veri, ensure_ascii=True, indent=1) + "\n",
        encoding="ascii",
        newline="\n",
    )
    goz = len(ham["goz_kararlari"]["farklar"])
    print(f"{len(cev)} cevap, {len(anahtar)} test, A==B {ayni}, goz {goz}")


if __name__ == "__main__":
    main()
