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


def kenar_olc(
    g: np.ndarray, kutu: list[int], olcum: tuple[int, int] | None = None
) -> dict[str, int]:
    """Kutunun dort kenarindaki KENAR_KALINLIK piksellik seritte koyu (< KOYU)
    piksel sayisi. g: beyazlatilmis kartin kanal minimumu (2B).

    Dogru kalibrasyonda dort serit de bostur: sol/sag sutun sinirlari
    murekkebin disindadir; ust, bir onceki sorudan >= BOSLUK bos satirla
    ayrilir; alt ya sonraki kutunun ustu-1 (bos bant) ya da SAYFA_ALTI /
    serit ustudur. Serite murekkep dusmesi = kutu icerigi kesiyor (ya da
    sinir yanlis olculmus).

    olcum: ust/alt seridinin DAR x araligi (ortak.olcum_sinir / profil
    SUTUN_OLCUM_PAY). Sutunlar arasi dikey ayrac ya da sirt yazisi sutun
    araligina giriyorsa (BS24FZ x 368 / 373) her kutunun alt seridinde
    murekkep gorunur; kesik kapisi bos yere doner."""
    x0, y0, x1, y1 = kutu
    k, c = KENAR_KALINLIK, KOSE_PAY
    ux0, ux1 = olcum if olcum else (x0, x1)
    return {
        "sol": int((g[y0:y1, x0 : x0 + k] < KOYU).sum()),
        "sag": int((g[y0:y1, x1 - k : x1] < KOYU).sum()),
        "ust": int((g[y0 : y0 + k, ux0 + c : ux1 - c] < KOYU).sum()),
        "alt": int((g[y1 - k : y1, ux0 + c : ux1 - c] < KOYU).sum()),
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
    # Renk / notr siniflamasi piksel basinadir (komsuluk yok): yalniz disk
    # pencerelerinde hesaplanir. Tum sayfada hesap kutu+kirp suresinin %85'iydi
    # (APO19FZ cProfile: 448 sayfada 153 / 173 sn); cikti bit bit ayni
    # (tests/unit/test_kitap_hat_kancalar: pencere == tam sayfa).
    maske = np.zeros(a.shape[:2], bool)
    for gy, gx in merkez:
        sl, r, _, dx = _pencere(a.shape, gy, gx, p.BEYAZ_YARICAP + 2)
        w = a[sl]
        renk = _okuyucu_rengi(w)
        if hasattr(p, "numara_maskesi"):
            # Renkli (mavi) basili numara diskle ortusebilir; kenar yumusatma
            # pikselleri 'mor' kuralina girer -- numara rengi korunur.
            renk &= ~p.numara_maskesi(w.astype(int))
        wi = w.astype(np.int16)
        notr = (wi.max(axis=2) - wi.min(axis=2) < GOLGE_FARK) & (
            wi.max(axis=2) >= SOL_GRI
        )
        maske[sl] |= (r <= p.BEYAZ_YARICAP) & (renk | ((dx < -5) & notr))
    return maske


def ortme_halkalari(
    p: ModuleType, a: np.ndarray, merkez: list[list[int]]
) -> list[dict]:
    """Beyazlatmadan ONCE: diskin disindaki halkada kitap murekkebi."""
    h0, h1 = p.HALKA
    out = []
    for gy, gx in merkez:
        sl, r, aci, _ = _pencere(a.shape, gy, gx, h1 + 1)
        w = a[sl]
        koyu = (w.min(axis=2) < KOYU) & ~_okuyucu_rengi(w)
        halka = (r >= h0) & (r <= h1) & (np.abs(aci) > np.pi / 4)
        ys, xs = np.where(halka & koyu)
        if len(ys) >= ORTME_ESIK:
            out.append(
                {
                    "simge": [gy, gx],
                    "ys": (ys + sl[0].start).tolist(),
                    "xs": (xs + sl[1].start).tolist(),
                }
            )
    return out


def sayfa_no_lekesi(p: ModuleType, a: np.ndarray, n: int | None = None) -> np.ndarray:
    """Profilde LEKE penceresi varsa sayfa numarasi rozetinin doygun lekesi.
    SUS_PARITE {0: pencereler, 1: pencereler}: yerlesim paritesine gore ek SUS
    pencereleri (orta ayrac ve ustundeki dikey yazi cift / tek sayfada farkli
    x'te; tek pencere digerinin kirmizi numarasini da beyazlatirdi)."""
    m = np.zeros(a.shape[:2], bool)
    leke = getattr(p, "LEKE", None)
    sus = tuple(getattr(p, "SUS_BOLGELERI", ()))
    if n is not None and hasattr(p, "SUS_PARITE"):
        sus += tuple(p.SUS_PARITE[ortak.parite(p, n)])
    if not leke and not sus:
        return m
    ai = a.astype(np.int16)
    doygun = (ai.max(axis=2) - ai.min(axis=2)) > LEKE_DOYGUN
    if leke:
        y0, x0, x1 = leke
        m[y0:, x0:x1] = doygun[y0:, x0:x1]
    # SUS_BOLGELERI: (y0, y1, x0, x1) pencerelerinde doygun (renkli) sayfa susu
    # (Aktif duzeni: pembe sekmenin koyu kivrimi, sutun sonu mavi ucgenler);
    # siyah metin doygun degil, dokunulmaz.
    for y0, y1, x0, x1 in sus:
        m[y0:y1, x0:x1] |= doygun[y0:y1, x0:x1]
    return m


def beyaz_sayfa(
    p: ModuleType, kaynak: Path, n: int, glif: list[list[int]]
) -> tuple[np.ndarray, list[dict]]:
    a = ortak.kart(p, kaynak, n).astype(np.uint8)
    m = merkezler(p, glif)
    halka = ortme_halkalari(p, a, m)
    a[okuyucu_maskesi(p, a, m)] = 255
    a[sayfa_no_lekesi(p, a, n)] = 255
    return a, halka


def _kenar_kaydet(
    g: np.ndarray,
    k: dict,
    s: int,
    kenar: list[dict],
    *,
    kesik: list[dict],
    olcum: tuple[int, int] | None = None,
) -> None:
    """sol/sag ihlali -> `kenar` (sutun siniri murekkebe giriyor; murekkep_x ile);
    ust/alt ihlali -> `kesik` (kutu soruyu kesiyor: alt sinir / serit / bos bant)."""
    sonuc = kenar_olc(g, k["kutu"], olcum)
    if not kenar_ihlali(sonuc):
        return
    kayit = {"birim": k["birim"], "soru": k["soru"], "dosya": s, **sonuc}
    if max(sonuc["ust"], sonuc["alt"]) > KENAR_EN_COK:
        kesik.append(kayit)
    else:
        # Sutun sinirini duzeltmek icin: bu satirlarda murekkebin gercek x
        # araligi (sinirin 40 px disina kadar bakilir).
        kayit["murekkep_x"] = murekkep_araligi(g, k["kutu"])
        kenar.append(kayit)


def goz_onayi_ayir(
    p: object, kesik: list[dict], ad: str = "KESIK_GOZ_ONAY"
) -> tuple[list[dict], list[dict], list[str]]:
    """KESIK_GOZ_ONAY (profil, dosya adlari): iki soru arasindaki bos bant 1-3
    satir oldugu icin alt serit sikkin kuyruguna degiyor ama kirpim gozle tam.
    Bu kayitlar kapiyi tetiklemez (`kesik_goz_onayli`). Onayli ad olculen
    kesikler arasinda yoksa `bayat` doner; cagiran kapiyi durdurur (duzeltilmis
    kutunun onayi sessizce kalmasin). Donus: (kalan kesik, onayli, bayat).

    ad="KENAR_GOZ_ONAY": ayni kural kenar kaydina (icerik sutun sinirina 1 px
    kala biten soru; sinirin otesi ayrac sekmesi -- APO19FZ T039_05)."""
    onay = set(getattr(p, ad, ()))
    onayli = [x for x in kesik if ortak.dosya_adi(x["birim"], x["soru"]) in onay]
    kalan = [x for x in kesik if x not in onayli]
    bayat = sorted(onay - {ortak.dosya_adi(x["birim"], x["soru"]) for x in onayli})
    return kalan, onayli, bayat


def _onayli_ayir(
    p: object, kayit: list[dict], ad: str, ornek: bool
) -> tuple[list[dict], list[dict]]:
    """goz_onayi_ayir + bayat onay kapisi (ornek kosuda kapi yok)."""
    kalan, onayli, bayat = goz_onayi_ayir(p, kayit, ad)
    if bayat and not ornek:
        raise SystemExit(f"{ad} bayat (olculen kayit yok): {bayat}")
    if ad != "KESIK_GOZ_ONAY":
        for x in onayli:
            print("   kenar (goz onayli)", x)
    return kalan, onayli


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


def _sayfa_kirp(
    arg: tuple[str, str, int, list, list[dict], str],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Bir sayfanin kutulari: beyazlat, kenar/kesik olc, ortme, PNG yaz (havuz isi)."""
    kod, kaynak, s, glif, kutular, cikti = arg
    p = ortak.profil(kod)
    a, halkalar = beyaz_sayfa(p, Path(kaynak), s, glif)
    g = a.min(axis=2)
    kenar: list[dict] = []
    kesik: list[dict] = []
    ortme: list[dict] = []
    for k in kutular:
        x0, y0, x1, y1 = k["kutu"]
        _kenar_kaydet(
            g,
            k,
            s,
            kenar,
            kesik=kesik,
            olcum=ortak.olcum_sinir(p, s, k["sutun"], x0, x1),
        )
        ortme += _ortme_kayitlari(k, s, halkalar)
        # compress_level 1: piksel ayni, kodlama ~5x hizli (dosya biraz buyuk).
        Image.fromarray(a[y0:y1, x0:x1]).save(
            Path(cikti) / f"{k['birim']}_{k['soru']:02d}.png", compress_level=1
        )
    return kenar, kesik, ortme


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
    isler = [
        (
            ortak.profil_kodu(p),
            str(kaynak),
            s,
            tarama["sayfalar"][str(s)]["glif"],
            sayfada[s],
            str(cikti),
        )
        for s in sorted(sayfada)
    ]
    # Sayfalar bagimsiz: surec havuzu (sirali birlestirme -> cikti sirasi ayni).
    for ke, ks, om in ortak.paralel(_sayfa_kirp, isler):
        kenar += ke
        kesik += ks
        ortme += om
    kesik, onayli = _onayli_ayir(p, kesik, "KESIK_GOZ_ONAY", bool(args.ornek))
    kenar, kenar_onayli = _onayli_ayir(p, kenar, "KENAR_GOZ_ONAY", bool(args.ornek))
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
    for x in onayli:
        print("   kesik (goz onayli)", x)
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
                "kesik_goz_onayli": onayli,
                **({"kenar_goz_onayli": kenar_onayli} if kenar_onayli else {}),
                "ortme": ortme,
            },
        )
    if kenar or kesik:
        # Kapi: kesik ya da kenar ihlali olan kirpim okumaya gitmez (metin hazirla
        # da ortme_olcumu'na bakar). JSON yine yazildi ki bakilabilsin.
        raise SystemExit(1)


if __name__ == "__main__":
    main()
