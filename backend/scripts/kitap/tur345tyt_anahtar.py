#!/usr/bin/env python
"""345 2025 TYT Turkce: cevap anahtari (Faz 1) -- ham okumalardan turer.

KAYNAK
------
Kitabin sonundaki basili CEVAP ANAHTARI tablosu (s432-439): konu basliklari
altinda 'Kazanim Odakli Sorular k' (KO), 'OSYM Tadinda Sorular k' (OT),
'Orijinal Sorular k' (OR), 'Karma Sorular k' (KA) satirlari, hucreler
'1.C 2.B ...'. Sayfa alti serit YOK. Tablonun test sirasi kitabin test
sirasidir (sayfa ust bandi okumasiyla dogrulanir: harita).

KANALLAR
--------
1. Iki bagimsiz okuma (A: parcalar ustten, hucreler soldan; B: parcalar
   alttan, hucreler sagdan), iki sayfa bir okuyucu, 2.5x. '?' = kararsiz.
2. Fark (ya da '?') varsa goz karari; karar A ya da B'den biri olmak ZORUNDA.
3. Piksel glif en-yakin-komsu LOO: uyumsuz her hucre goz karari ya da goz
   teyidi tasimak ZORUNDA (harfler 6 px; kanal destekleyici).
4. Hucre sayisi == basili soru numarasi sayisi (capa taramasi): testler
   sirayla, sayfa sirasinda (L sonra R, yukaridan asagi) numaralari tuketir.
   Okuyucu simgesi bu kitapta bloga konur (OSYM kosesi / ortak parca tek
   simge), soru capasi degildir.

Soru cozulmez; tek kaynak basili tablo.

CIKTI
-----
veriseti/zkitap/cikti/345_2025_tyt_turkce_cevap_anahtari.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_turkce_"
HAM = CIKTI / f"{ON}ham_okumalar.json"
TARAMA = CIKTI / f"{ON}capa_taramasi.json"
HEDEF = CIKTI / f"{ON}cevap_anahtari.json"
ONEK = "TRT345"
BEKLENEN_TEST = 207
BEKLENEN_SORU = 2070
TURLER = ("KO", "OT", "OR", "KA")
_KIMLIK = ("sayfa", "konu", "tur", "no")


def iki_okuma(ham: dict) -> list[dict]:
    """Test sirasinda [{sira, sayfa, konu, tur, no, a, b}]; A ve B ayni testleri ayni sirada okumali."""
    a, b = ham["anahtar_okumalari"]["A"], ham["anahtar_okumalari"]["B"]
    if len(a) != len(b):
        raise SystemExit(f"A/B test sayisi farkli: {len(a)} / {len(b)}")
    out = []
    for i, (x, y) in enumerate(zip(a, b, strict=True), 1):
        if tuple(x[k] for k in _KIMLIK) != tuple(y[k] for k in _KIMLIK):
            raise SystemExit(f"T{i:03d}: A/B test kimligi farkli")
        if x["tur"] not in TURLER:
            raise SystemExit(f"T{i:03d}: taninmayan tur {x['tur']!r}")
        for s in (x["cevaplar"], y["cevaplar"]):
            if not re.fullmatch(r"[ABCDE?]+", s):
                raise SystemExit(f"T{i:03d}: bicim disi girdi {s!r}")
        if len(x["cevaplar"]) != len(y["cevaplar"]):
            raise SystemExit(f"T{i:03d}: A/B hucre sayisi farkli")
        out.append(
            {
                "sira": i,
                **{k: x[k] for k in _KIMLIK},
                "a": x["cevaplar"],
                "b": y["cevaplar"],
            }
        )
    return out


def birlestir(okumalar: list[dict], farklar: dict[str, str]) -> dict[int, str]:
    """A == B (ve '?' degil) ise o; degilse goz karari (A ya da B'den biri). Kararsiz fark durur."""
    kullanilan = set()
    out = {}
    for t in okumalar:
        harf = []
        for i, (x, y) in enumerate(zip(t["a"], t["b"], strict=True), 1):
            yer = f"T{t['sira']:03d}#{i}"
            if x == y and x != "?":
                if yer in farklar:
                    raise SystemExit(f"{yer}: gereksiz goz karari (A == B)")
                harf.append(x)
                continue
            if yer not in farklar:
                raise SystemExit(f"{yer}: A/B farki ({x}/{y}) goz karari yok")
            k = farklar[yer]
            if k not in (x, y) or k == "?":
                raise SystemExit(f"{yer}: goz karari {k} ne A ne B")
            kullanilan.add(yer)
            harf.append(k)
        out[t["sira"]] = "".join(harf)
    if set(farklar) - kullanilan:
        raise SystemExit(
            f"kullanilmayan goz karari: {sorted(set(farklar) - kullanilan)}"
        )
    return out


def numara_sirasi(tarama: dict) -> list[tuple[int, str, int]]:
    """Sayfa sirasi, sutun L sonra R, yukaridan asagi: (sayfa, sutun, sira)."""
    out = []
    for n in sorted(int(k) for k in tarama["sayfalar"]):
        s = tarama["sayfalar"][str(n)]
        for t in ("L", "R"):
            for i, _ in enumerate(sorted(s["numara"][t])):
                out.append((n, t, i))
    return out


def cevaplar_uret(
    okumalar: list[dict], anahtar: dict[int, str], numaralar: list
) -> list[dict]:
    """Testler sirayla numaralari tuketir; TRT345-Tnnn ardisik birim."""
    if sum(len(v) for v in anahtar.values()) != len(numaralar):
        raise SystemExit(
            f"hucre {sum(len(v) for v in anahtar.values())} != numara {len(numaralar)}"
        )
    out, i = [], 0
    for t in okumalar:
        birim = f"{ONEK}-T{t['sira']:03d}"
        for j, c in enumerate(anahtar[t["sira"]], 1):
            n, sut, s = numaralar[i]
            i += 1
            out.append(
                {
                    "birim": birim,
                    "soru": j,
                    "cevap": c,
                    "tur": t["tur"],
                    "no": t["no"],
                    "dosya": n,
                    "sutun": sut,
                    "sutun_sira": s,
                }
            )
    return out


def glif_dogrula(ham: dict, cevaplar: list[dict]) -> None:
    """Glif uyumsuzlarinin her biri goz karari ya da goz teyidi tasimali; teyit son harfle ayni."""
    gl = ham["glif"]
    if gl["hucre"] != len(cevaplar) or gl["uyum"] + len(gl["uyumsuz"]) != gl["hucre"]:
        raise SystemExit("glif sayimi tutarsiz")
    son = {f"T{int(c['birim'][-3:]):03d}#{c['soru']}": c["cevap"] for c in cevaplar}
    farklar = ham["goz_kararlari"]["farklar"]
    teyit = gl["goz_teyit"]
    for yer, _okuma, _komsu, _benzer in gl["uyumsuz"]:
        if yer in farklar:
            continue
        if yer not in teyit or teyit[yer] != son[yer]:
            raise SystemExit(f"{yer}: glif uyumsuz, goz teyidi yok")
    if set(teyit) - {u[0] for u in gl["uyumsuz"]}:
        raise SystemExit("glif uyumsuzu olmayan goz teyidi")


def main() -> None:
    ham = json.loads(HAM.read_text("ascii"))
    tarama = json.loads(TARAMA.read_text("ascii"))
    ok = iki_okuma(ham)
    anahtar = birlestir(ok, ham["goz_kararlari"]["farklar"])
    if len(anahtar) != BEKLENEN_TEST:
        raise SystemExit(f"test {len(anahtar)} != {BEKLENEN_TEST}")
    cev = cevaplar_uret(ok, anahtar, numara_sirasi(tarama))
    if len(cev) != BEKLENEN_SORU:
        raise SystemExit(f"soru {len(cev)} != {BEKLENEN_SORU}")
    glif_dogrula(ham, cev)
    ayni = sum(
        1
        for t in ok
        for x, y in zip(t["a"], t["b"], strict=True)
        if x == y and x != "?"
    )
    veri = {
        "kaynak": "345 2025 TYT Turkce Soru Bankasi",
        "arac": "scripts/kitap/tur345tyt_anahtar.py",
        "nereden": "kitap sonu cevap anahtari tablosu (s432-439)",
        "dogrulama": {
            "a_esittir_b_hucre": ayni,
            "goz_karari": len(ham["goz_kararlari"]["farklar"]),
            "glif_loo_uyum": ham["glif"]["uyum"],
            "glif_goz_teyit": len(ham["glif"]["goz_teyit"]),
            "hucre_sayisi_esittir_numara": True,
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
