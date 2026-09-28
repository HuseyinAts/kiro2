"""Kirpim kutularindan soru gorselleri + ortme olcumu (profil gudumlu; acil2021tyt_kirp deseni).

Gorseller git'e girmez; her kutu `<onek>_kirpim_kutulari.json` icinde durdugu
icin her ortamda yeniden uretilir.

OKUYUCU DISKI BEYAZLATILIR
--------------------------
FERNUS diski (lila / mor glif / notr gri golge / mor-lila kenar) simge
merkezi (glif sol-ust + p.DISK_MERKEZ) etrafinda p.BEYAZ_YARICAP icinde ve
YALNIZ okuyucu renklerinde beyazlatilir; kitabin siyah metnine ve renkli
cizimlerine dokunulmaz.

ORTME OLCUMU
------------
Disk opaktir; altinda kalan kitap icerigi goruntude YOKTUR. Beyazlatmadan
ONCE diskin disindaki halkada (p.HALKA) kitap murekkebi aranir; diskin
sagindaki 90 derece haric (sorunun kendi numarasi). Halka pikseli >=
ORTME_ESIK dusen kirpim `ortme` ile raporlanir; okuyucu ortulen karakteri
[??] yazar, tahmin etmez.

KENAR / KESIK KAPISI
--------------------
Beyazlatilmis kutunun dort kenarindaki 2 px'lik seritte koyu piksel sayilir
(`kenar_olc`). sol/sag > KENAR_EN_COK -> `kenar` (sutun siniri murekkebe
giriyor); ust/alt > KENAR_EN_COK -> `kesik` (kutu soruyu kesiyor: SAYFA_ALTI,
serit ortusmesi ya da bos bant yanlis). Ikisinden biri varsa exit 1; ortme_olcumu
yine yazilir. `metin hazirla` bu sayilara bakar, kesik kirpim okuyucuya gitmez.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.kirp --profil K [--ornek N] [--cikti DIZIN]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from types import ModuleType

import numpy as np
from PIL import Image

from scripts.kitap.kitap_hat import ortak

DISK_RENK = (240, 238, 247)
GLIF_ESIK = 120
DISK_ESIK = 40
GOLGE_EN_AZ = 215
GOLGE_FARK = 12
MOR_FARK = 18
SOL_GRI = 185
KOYU = 160
KENAR_EN_COK = 3
KENAR_KALINLIK = 2
# ust/alt seridinde koselerden KOSE_PAY px icerisi olculur: sutun sinirina
# bitisik sayfa susu (acl23ag test bandi cercevesinin kirmizi dikey kenari,
# x 711-712, sag sinir 716) kesik degildir; soru metni koseye gelmez.
KOSE_PAY = 6
ORTME_ESIK = 4
LEKE_DOYGUN = 60


def kenar_olc(g: np.ndarray, kutu: list[int]) -> dict[str, int]:
    """Kutunun dort kenarindaki KENAR_KALINLIK piksellik seritte koyu (< KOYU)
    piksel sayisi. g: beyazlatilmis kartin kanal minimumu (2B).

    Dogru kalibrasyonda dort serit de bostur: sol/sag sutun sinirlari
    murekkebin disindadir; ust, bir onceki sorudan >= BOSLUK bos satirla
    ayrilir; alt ya sonraki kutunun ustu-1 (bos bant) ya da SAYFA_ALTI /
    serit ustudur. Serite murekkep dusmesi = kutu icerigi kesiyor (ya da
    sinir yanlis olculmus)."""
    x0, y0, x1, y1 = kutu
    k, c = KENAR_KALINLIK, KOSE_PAY
    return {
        "sol": int((g[y0:y1, x0 : x0 + k] < KOYU).sum()),
        "sag": int((g[y0:y1, x1 - k : x1] < KOYU).sum()),
        "ust": int((g[y0 : y0 + k, x0 + c : x1 - c] < KOYU).sum()),
        "alt": int((g[y1 - k : y1, x0 + c : x1 - c] < KOYU).sum()),
    }


def kenar_ihlali(olcum: dict[str, int]) -> bool:
    return max(olcum.values()) > KENAR_EN_COK


def murekkep_araligi(g: np.ndarray, kutu: list[int], pay: int = 40) -> list[int]:
    """Kutunun satirlarinda, sinirlarin `pay` px disina kadar, koyu murekkebin
    [x_min, x_max] araligi (kenar ihlalinde SUTUNLAR duzeltmesi icin)."""
    x0, y0, x1, y1 = kutu
    xa, xb = max(0, x0 - pay), min(g.shape[1], x1 + pay)
    xs = np.where((g[y0:y1, xa:xb] < KOYU).any(axis=0))[0]
    if not len(xs):
        return [x0, x1]
    return [int(xs.min()) + xa, int(xs.max()) + xa]


def merkezler(p: ModuleType, glif: list[list[int]]) -> list[list[int]]:
    dy, dx = p.DISK_MERKEZ
    return [[gy + dy, gx + dx] for gy, gx in glif]


def _okuyucu_rengi(a: np.ndarray) -> np.ndarray:
    ai = a.astype(np.int16)
    fark_glif = np.abs(ai - np.array(ortak.GLIF_RENK)).sum(axis=2)
    fark_disk = np.abs(ai - np.array(DISK_RENK)).sum(axis=2)
    enb, enk = ai.max(axis=2), ai.min(axis=2)
    golge = (enb - enk < GOLGE_FARK) & (enb >= GOLGE_EN_AZ)
    r, gg, bb = ai[..., 0], ai[..., 1], ai[..., 2]
    mor = (bb - r > MOR_FARK) & (bb - gg > MOR_FARK) & (r >= gg - 8)
    renk: np.ndarray = (fark_glif < GLIF_ESIK) | (fark_disk < DISK_ESIK) | golge | mor
    return renk


def _pencere(shape: tuple[int, ...], gy: int, gx: int, r: int):
    y0, y1 = max(0, gy - r), min(shape[0], gy + r + 1)
    x0, x1 = max(0, gx - r), min(shape[1], gx + r + 1)
    yy, xx = np.ogrid[y0:y1, x0:x1]
    return (
        (slice(y0, y1), slice(x0, x1)),
        np.hypot(yy - gy, xx - gx),
        np.arctan2(yy - gy, xx - gx),
        (xx - gx) + 0 * yy,
    )


def okuyucu_maskesi(
    p: ModuleType, a: np.ndarray, merkez: list[list[int]]
) -> np.ndarray:
    """Kart koordinatli goruntude okuyucu katmani pikselleri (konum + renk)."""
    maske = np.zeros(a.shape[:2], bool)
    renk = _okuyucu_rengi(a)
    if hasattr(p, "numara_maskesi"):
        # Renkli (mavi) basili numara diskle ortusebilir; kenar yumusatma
        # pikselleri 'mor' kuralina girer -- numara rengi korunur.
        renk &= ~p.numara_maskesi(a.astype(int))
    ai = a.astype(np.int16)
    notr = (ai.max(axis=2) - ai.min(axis=2) < GOLGE_FARK) & (ai.max(axis=2) >= SOL_GRI)
    for gy, gx in merkez:
        sl, r, _, dx = _pencere(a.shape, gy, gx, p.BEYAZ_YARICAP + 2)
        maske[sl] |= (r <= p.BEYAZ_YARICAP) & (renk[sl] | ((dx < -5) & notr[sl]))
    return maske


def ortme_halkalari(
    p: ModuleType, a: np.ndarray, merkez: list[list[int]]
) -> list[dict]:
    """Beyazlatmadan ONCE: diskin disindaki halkada kitap murekkebi."""
    koyu = (a.min(axis=2) < KOYU) & ~_okuyucu_rengi(a)
    h0, h1 = p.HALKA
    out = []
    for gy, gx in merkez:
        sl, r, aci, _ = _pencere(a.shape, gy, gx, h1 + 1)
        halka = (r >= h0) & (r <= h1) & (np.abs(aci) > np.pi / 4)
        ys, xs = np.where(halka & koyu[sl])
        if len(ys) >= ORTME_ESIK:
            out.append(
                {
                    "simge": [gy, gx],
                    "ys": (ys + sl[0].start).tolist(),
                    "xs": (xs + sl[1].start).tolist(),
                }
            )
    return out


def sayfa_no_lekesi(p: ModuleType, a: np.ndarray) -> np.ndarray:
    """Profilde LEKE penceresi varsa sayfa numarasi rozetinin doygun lekesi."""
    m = np.zeros(a.shape[:2], bool)
    leke = getattr(p, "LEKE", None)
    if not leke:
        return m
    ai = a.astype(np.int16)
    y0, x0, x1 = leke
    m[y0:, x0:x1] = (ai.max(axis=2) - ai.min(axis=2))[y0:, x0:x1] > LEKE_DOYGUN
    return m


def beyaz_sayfa(
    p: ModuleType, kaynak: Path, n: int, glif: list[list[int]]
) -> tuple[np.ndarray, list[dict]]:
    a = ortak.kart(p, kaynak, n).astype(np.uint8)
    m = merkezler(p, glif)
    halka = ortme_halkalari(p, a, m)
    a[okuyucu_maskesi(p, a, m)] = 255
    a[sayfa_no_lekesi(p, a)] = 255
    return a, halka


def _kenar_kaydet(
    g: np.ndarray, k: dict, s: int, kenar: list[dict], kesik: list[dict]
) -> None:
    """sol/sag ihlali -> `kenar` (sutun siniri murekkebe giriyor; murekkep_x ile);
    ust/alt ihlali -> `kesik` (kutu soruyu kesiyor: alt sinir / serit / bos bant)."""
    olcum = kenar_olc(g, k["kutu"])
    if not kenar_ihlali(olcum):
        return
    kayit = {"birim": k["birim"], "soru": k["soru"], "dosya": s, **olcum}
    if max(olcum["ust"], olcum["alt"]) > KENAR_EN_COK:
        kesik.append(kayit)
    else:
        # Sutun sinirini duzeltmek icin: bu satirlarda murekkebin gercek x
        # araligi (sinirin 40 px disina kadar bakilir).
        kayit["murekkep_x"] = murekkep_araligi(g, k["kutu"])
        kenar.append(kayit)


def _ortme_kayitlari(k: dict, s: int, halkalar: list[dict]) -> list[dict]:
    x0, y0, x1, y1 = k["kutu"]
    out = []
    for h in halkalar:
        icte = sum(
            1
            for yy, xx in zip(h["ys"], h["xs"], strict=True)
            if x0 <= xx < x1 and y0 <= yy < y1
        )
        if icte >= ORTME_ESIK:
            out.append(
                {
                    "birim": k["birim"],
                    "soru": k["soru"],
                    "dosya": s,
                    "simge": h["simge"],
                    "piksel": icte,
                }
            )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("--ornek", type=int, default=0)
    ap.add_argument("--cikti", default=None)
    args = ap.parse_args()
    p = ortak.profil(args.profil)
    cikti = (
        Path(args.cikti)
        if args.cikti
        else ortak.KOK / "backend" / f"_{p.VERAF}_gecici" / "kirpim"
    )
    veri = ortak.oku(p, "kirpim_kutulari")
    kutular = veri["kutular"]
    if len(kutular) != p.BEKLENEN_SORU:
        raise SystemExit(f"kutu sayisi {len(kutular)} != {p.BEKLENEN_SORU}")
    if args.ornek:
        kutular = kutular[: args.ornek]
    tarama = ortak.oku(p, "capa_taramasi")
    kaynak = ortak.kaynak_dizin(p)
    cikti.mkdir(parents=True, exist_ok=True)
    sayfada: dict[int, list[dict]] = {}
    for k in kutular:
        sayfada.setdefault(k["dosya"], []).append(k)
    kenar: list[dict] = []
    kesik: list[dict] = []
    ortme: list[dict] = []
    for s in sorted(sayfada):
        a, halkalar = beyaz_sayfa(p, kaynak, s, tarama["sayfalar"][str(s)]["glif"])
        g = a.min(axis=2)
        for k in sayfada[s]:
            x0, y0, x1, y1 = k["kutu"]
            _kenar_kaydet(g, k, s, kenar, kesik)
            ortme += _ortme_kayitlari(k, s, halkalar)
            Image.fromarray(a[y0:y1, x0:x1]).save(
                cikti / f"{k['birim']}_{k['soru']:02d}.png"
            )
    n = sum(len(v) for v in sayfada.values())
    osoru = len({(o["birim"], o["soru"]) for o in ortme})
    print(
        f"uretildi {n} gorsel -> {cikti}; kenar {len(kenar)}; kesik {len(kesik)}; "
        f"ortme {len(ortme)} halka / {osoru} soru"
    )
    for x in kenar[:15]:
        print("   kenar", x)
    for x in kesik[:15]:
        print("   KESIK", x)
    if not args.ornek:
        h0, h1 = p.HALKA
        ortak.yaz(
            p,
            "ortme_olcumu",
            {
                "kaynak": p.KAYNAK_ADI,
                "arac": "scripts/kitap/kitap_hat/kirp.py",
                "ne_olculdu": (
                    f"Beyazlatmadan ONCE her okuyucu diskinin disindaki halkada (yaricap {h0}-"
                    f"{h1}, sag 90 derece haric) koyu (< {KOYU}) kitap murekkebi. Kirpima >= "
                    f"{ORTME_ESIK} halka pikseli dusen soru 'ortme' tasir. Disk opak; altindaki icerik "
                    f"goruntude yoktur. KENAR: beyazlatilmis kutunun {KENAR_KALINLIK} px'lik sol/sag "
                    f"seridinde > {KENAR_EN_COK} koyu piksel. KESIK: ust/alt seridinde > "
                    f"{KENAR_EN_COK} koyu piksel = kutu soruyu kesiyor (alt sinir / serit yanlis)."
                ),
                "kenar_kapisi_ihlali": len(kenar),
                "kesik_kapisi_ihlali": len(kesik),
                "ortme_soru": osoru,
                "kenar": kenar,
                "kesik": kesik,
                "ortme": ortme,
            },
        )
    if kenar or kesik:
        # Kapi: kesik ya da kenar ihlali olan kirpim okumaya gitmez (metin hazirla
        # da ortme_olcumu'na bakar). JSON yine yazildi ki bakilabilsin.
        raise SystemExit(1)


if __name__ == "__main__":
    main()
