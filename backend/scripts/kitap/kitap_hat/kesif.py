"""Yeni kitap / yeni seri kesfi -- profil ISTEMEZ; yerlesim sabitlerini olcer,
profil taslagi basar.

Neyi olcer (hepsi kart koordinati; KART ortak varsayilan):
* glif      : sayfa basina okuyucu simgesi sayisi; sol-ust x histogrami parite
              basina -> SIMGE_X adaylari (sol/sag kume modu), GLIF_BOY.
* numara    : glifin sagindaki pencerede dort on ayar maskesinin (kirmizi /
              mavi / camgobegi / siyah) numara boyunda blob bulma orani ->
              numara_maskesi onerisi; secilen maskeyle blob dx / dy / h / w
              dagilimi -> PENCERE, NUMARA_H, NUMARA_DX.
* sutun     : glifli sayfalarda x murekkep projeksiyonu parite basina; sol
              baslangic, orta bosluk, sag bitis -> SUTUNLAR.
* dikey     : y projeksiyonu; tam genislik (>= %60) ve serit genisligi
              (250-340 px) yatay cizgi satirlari -> UST_BANT / SAYFA_ALTI /
              serit adaylari; glifli sayfalarda en alt murekkep satiri.
* sayfa     : sayfa basina glif / serit adayi / ust bant sari-kirmizi piksel
              -> TEST_SAYFALARI aralik onerisi.
* goz       : --goz ile ornek sayfalarin kart ustune SIMGE_X / sutun / serit
              cizgili PNG montaji (gozle tek bakista dogrulama).

Arac tahmin etmez: dagilimi ve modu basar; kesin degerler olcum + gozle
profile yazilir (gozle dogrulanacaklar taslakta `# GOZ:` ile isaretli).

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.kesif --klasor "<screenshots alt klasor globu>"
        [--ornek 40] [--goz 3] [--cikti AD]
Cikti: veriseti/zkitap/cikti/_kesif_<AD>.json / .txt (git disi; '_' onekli).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from scripts.kitap.kitap_hat import ortak

KART = (589, 43, 1331, 1022)
GLIF_P = SimpleNamespace(GLIF_GENISLET=True, GLIF_BOY=(12, 17, 12, 17))
PENCERE_GENIS = (-8, 70, 6, 60)  # glif sol-ustune gore genis arama penceresi
NUMARA_H = (6, 16)
NUMARA_W_EN_COK = 30
SERIT_GENISLIK = (250, 340)
TAM_GENISLIK_ORAN = 0.6


def klasor_bul(glob: str) -> Path:
    k = [p for p in ortak.EKRAN.iterdir() if p.is_dir() and p.match(glob)]
    if len(k) != 1:
        raise SystemExit(f"klasor {glob!r}: {len(k)} eslesme {[x.name for x in k]}")
    return Path(k[0])


def kart(d: Path, n: int) -> np.ndarray:
    img = Image.open(d / f"sayfa_{n:04d}.png").convert("RGB")
    if img.size != ortak.BEKLENEN_BOYUT:
        raise SystemExit(f"BOYUT UYUSMAZLIGI s{n}: {img.size}")
    return np.asarray(img.crop(KART)).astype(int)


def numara_bloblari(
    m: np.ndarray, gy: int, gx: int, pencere: tuple[int, int, int, int] = PENCERE_GENIS
) -> list[tuple[int, int, int, int]]:
    """Maske penceresinde numara boyunda bloblar: (dy, dx, h, w) glife gore."""
    py0, py1, px0, px1 = pencere
    y0, x0 = max(0, gy + py0), gx + px0
    w = m[y0 : gy + py1, x0 : gx + px1]
    lab, _ = ndimage.label(ndimage.binary_dilation(w, np.ones((3, 3), bool)))
    out = []
    for s in ndimage.find_objects(lab):
        h, ww = s[0].stop - s[0].start, s[1].stop - s[1].start
        if NUMARA_H[0] <= h <= NUMARA_H[1] and ww <= NUMARA_W_EN_COK:
            out.append((s[0].start + y0 - gy, s[1].start + x0 - gx, h, ww))
    return sorted(out, key=lambda b: (b[0], b[1]))


def en_uzun_kosu(v: np.ndarray, bosluk: int = 3) -> tuple[int, int]:
    """<= bosluk px araliklarla birlesen True kosularinin en uzunu (x0, x1);
    hicbiri yoksa (0, -1). Serit cercevesi hucre sinirlarinda kisa kesintili,
    kesikli sayfa cizgileri de bu payla tek kosu olur."""
    kosu: list[list[int]] = []
    bas = None
    for i, x in enumerate([*v.tolist(), False]):
        if x and bas is None:
            bas = i
        elif not x and bas is not None:
            if kosu and bas - kosu[-1][1] <= bosluk:
                kosu[-1][1] = i - 1
            else:
                kosu.append([bas, i - 1])
            bas = None
    if not kosu:
        return 0, -1
    en = max(kosu, key=lambda k: k[1] - k[0])
    return en[0], en[1]


def yatay_cizgiler(a: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Koyu (<200) yatay cizgi satirlari: (y, genislik, x0, x1) -- satirdaki EN
    UZUN kesintisiz kosu serit genisliginde (SERIT_GENISLIK) ya da tam genislikte
    (>= TAM_GENISLIK_ORAN * kart). Ayni satirdaki metin (acl24mg s183: sik satiri
    serit hizasinda) kosuyu uzatmaz. Bitisik satirlar (kalinlik) tek cizgi."""
    k = a.max(axis=2) < 200
    out = []
    for y in range(a.shape[0]):
        if int(k[y].sum()) < SERIT_GENISLIK[0] * 0.8:
            continue
        x0, x1 = en_uzun_kosu(k[y])
        g = x1 - x0 + 1
        if (
            SERIT_GENISLIK[0] <= g <= SERIT_GENISLIK[1]
            or g >= TAM_GENISLIK_ORAN * a.shape[1]
        ):
            out.append((y, g, x0, x1))
    # ardisik satirlari (kalinlik) tek cizgiye indir: son satir
    tek: list[tuple[int, int, int, int]] = []
    for c in out:
        if tek and c[0] - tek[-1][0] <= 1 and abs(c[1] - tek[-1][1]) <= 6:
            tek[-1] = c
        else:
            tek.append(c)
    return tek


def x_projeksiyon(a: np.ndarray, y0: int = 70, y1: int = 880) -> np.ndarray:
    v: np.ndarray = (a[y0:y1].min(axis=2) < 200).sum(axis=0)
    return v


BOS_ORAN = 0.002  # projeksiyonda 'murekkepsiz' esigi (en yuksek sutunun binde 2'si)


def murekkep_araligi(v: np.ndarray) -> list[int] | None:
    xs = np.where(v > BOS_ORAN * v.max())[0] if v.max() > 0 else np.array([])
    return [int(xs.min()), int(xs.max())] if len(xs) else None


def orta_bosluk(v: np.ndarray, x0: int = 300, x1: int = 420) -> tuple[int, int] | None:
    """[x0, x1) icinde en uzun murekkepsiz (< BOS_ORAN * max) kosu (bas, son);
    orta ayrac cizgisi / dikey yazi ince oldugu icin kosu ikiye bolunebilir,
    en uzunu alinir (sutun siniri = kosunun iki ucu; GOZ ile duzeltilir)."""
    esik = BOS_ORAN * v.max()
    en, cur = None, None
    for x in range(x0, x1 + 1):
        bos = x < x1 and v[x] <= esik
        if bos and cur is None:
            cur = x
        elif not bos and cur is not None:
            if en is None or (x - cur) > (en[1] - en[0] + 1):
                en = (cur, x - 1)
            cur = None
    return en


def metin_seridi(a: np.ndarray, y0: int = 860, x0: int = 300) -> list[int] | None:
    """Sayfa altinda duz metin cevap seridi adayi (acl25pl deseni: '1.C 2.B ...'):
    y >= y0, x >= x0 koyu (max < 120) satirlarin en alttaki kumesi; yukseklik
    <= 14, >= 60 piksel. [y0, y1, x0, x1] ya da None."""
    k = a[y0:, x0:].max(axis=2) < 120
    dolu = k.sum(axis=1)
    # bitisik satir kumeleri (tam genislik satirlar = sayfa cizgisi, kume degil)
    kumeler: list[list[int]] = []
    for y in range(k.shape[0]):
        if dolu[y] == 0 or dolu[y] > 0.6 * k.shape[1]:
            continue
        if kumeler and y - kumeler[-1][-1] <= 1:
            kumeler[-1].append(y)
        else:
            kumeler.append([y])
    # alttan yukari ilk 'serit gibi' kume: alcak, genis, dolu (sayfa numarasi dar)
    for kume in kumeler[::-1]:
        ya, yb = kume[0], kume[-1]
        if yb - ya + 1 > 14:
            continue
        xs = np.where(k[ya : yb + 1].any(axis=0))[0]
        # acl25pl s7: 4 hucreli serit 90 px genis, 139 px dolu; sayfa numarasi 7 px genis
        if int(k[ya : yb + 1].sum()) >= 60 and xs.max() - xs.min() >= 60:
            return [ya + y0, yb + y0, int(xs.min()) + x0, int(xs.max()) + x0]
    return None


def sayfa_olc(a: np.ndarray) -> dict[str, Any]:
    """Tek sayfa: glifler, maske basina numara blob isabeti, cizgiler, bant renkleri."""
    glif = ortak.glifler(GLIF_P, a)
    maskeler = {ad: f(a) for ad, f in ortak.NUMARA_MASKELERI.items()}
    isabet: dict[str, list[tuple[int, int, int, int]]] = {ad: [] for ad in maskeler}
    for gy, gx in glif:
        for ad, m in maskeler.items():
            bl = numara_bloblari(m, gy, gx)
            if bl:
                isabet[ad].append(bl[0])  # en ustteki (numara satiri) ilk blob
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sari = int(((r > 230) & (g > 160) & (b < 120))[10:60].sum(axis=1).max())
    kir = int(ortak.kirmizi(a)[0:80].sum(axis=1).max())
    koyu = int((a[60:900].max(axis=2) < 120).sum())
    cizgi = yatay_cizgiler(a)
    alt = [c for c in cizgi if c[0] >= 780]
    # glifli sayfada sutunlarin en alt murekkebi (altlik cizgilerinin ustunde)
    en_alt = None
    ms = metin_seridi(a) if glif else None
    if glif:
        tavan = min((c[0] for c in alt), default=a.shape[0])
        if ms:
            tavan = min(tavan, ms[0])
        ys = np.where((a[:tavan].min(axis=2) < 160).any(axis=1))[0]
        en_alt = int(ys.max()) if len(ys) else None
    return {
        "glif": glif,
        "isabet": isabet,
        "sari_bant": sari,
        "kirmizi_bant": kir,
        "koyu": koyu,
        "cizgi": cizgi,
        "alt_cizgi": alt,
        "metin_seridi": ms,
        "en_alt_murekkep": en_alt,
        "x_proj": x_projeksiyon(a) if glif else None,
    }


def _mod(c: Counter, tol: int = 3) -> int | None:
    """Histogram modu (+-tol komsulariyla en agir deger)."""
    if not c:
        return None
    return int(max(c, key=lambda x: sum(v for k, v in c.items() if abs(k - x) <= tol)))


def maske_sec(isabet: dict[str, int], glif_top: int) -> str | None:
    """Numara rengi: siyah maske her glifin yaninda (soru metni) bir sey bulur;
    renkli bir maske gliflerin en az yarisinda numara boyunda blob buluyorsa
    numara renklidir. Camgobegi mavinin alt kumesi: esitse dar olan."""
    if not glif_top:
        return None
    renkli = {k: v for k, v in isabet.items() if k != "siyah"}
    secilen = max(renkli, key=lambda k: renkli[k]) if renkli else None
    if secilen is None or renkli[secilen] < 0.5 * glif_top:
        return "siyah"
    if secilen == "mavi" and renkli.get("camgobegi", 0) >= 0.9 * renkli["mavi"]:
        return "camgobegi"
    return secilen


def sutun_olc(proj: np.ndarray, n: int) -> dict[str, Any]:
    """x projeksiyonundan (n glifli sayfa toplami) sutun adaylari.

    Her satirda murekkepli sutun = dikey cizgi (kart cercevesi, orta ayrac):
    metin degil; cerceve kenarlari murekkep araligindan cikarilir, ortadaki
    ayrac sutun sinirinin ipucu olur ('Ilaci' duzeninde bosluk yok, dikey
    'ACIL MATEMATIK' yazisi + cizgi var)."""
    v = proj.copy()
    cizgi_sutun = v >= 0.5 * (880 - 70) * n
    xs = np.arange(len(v))
    v[cizgi_sutun & ((xs < 30) | (xs > 710))] = 0
    ayrac = [int(x) for x in np.where(cizgi_sutun)[0] if 330 <= x <= 420]
    bos = orta_bosluk(v)
    return {
        "murekkep_x": murekkep_araligi(v),
        "orta_bosluk": list(bos) if bos else None,
        "ayrac": ayrac,
        "orta_profil": [(x, int(v[x])) for x in range(330, 420) if v[x] > 0][:40],
    }


def _numara_dagilimi(
    sayfalar: dict[int, dict[str, Any]], secilen: str | None
) -> tuple[Counter, Counter, Counter, Counter]:
    """Secilen maskeyle bulunan numara bloblarinin dy / dx / h / w histogramlari."""
    dy: Counter[int] = Counter()
    dx: Counter[int] = Counter()
    hh: Counter[int] = Counter()
    ww: Counter[int] = Counter()
    if secilen:
        for v in sayfalar.values():
            for d_y, d_x, h, w in v["isabet"][secilen]:
                dy[d_y] += 1
                dx[d_x] += 1
                hh[h] += 1
                ww[w] += 1
    return dy, dx, hh, ww


def topla(sayfalar: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Sayfa olcumlerinden profil adaylari."""
    simge: dict[int, dict[str, Counter[int]]] = {
        0: {"L": Counter(), "R": Counter()},
        1: {"L": Counter(), "R": Counter()},
    }
    isabet: Counter[str] = Counter()
    glif_top = 0
    proj = {0: np.zeros(KART[2] - KART[0]), 1: np.zeros(KART[2] - KART[0])}
    proj_n = {0: 0, 1: 0}
    cizgi_ust: dict[int, Counter] = {0: Counter(), 1: Counter()}
    cizgi_alt: dict[int, Counter] = {0: Counter(), 1: Counter()}
    serit_x: dict[int, Counter] = {0: Counter(), 1: Counter()}
    en_alt: dict[int, Counter] = {0: Counter(), 1: Counter()}
    metin_serit: dict[int, Counter] = {0: Counter(), 1: Counter()}
    for n, v in sayfalar.items():
        par = n % 2
        if v["metin_seridi"]:
            ms = v["metin_seridi"]
            metin_serit[par][(ms[0], ms[1], ms[2] // 10 * 10)] += 1
        for _gy, gx in v["glif"]:
            simge[par]["L" if gx < 200 else "R"][gx] += 1
        glif_top += len(v["glif"])
        for ad, bl in v["isabet"].items():
            isabet[ad] += len(bl)
        if v["x_proj"] is not None:
            proj[par] += v["x_proj"]
            proj_n[par] += 1
            if v["en_alt_murekkep"] is not None:
                en_alt[par][v["en_alt_murekkep"]] += 1
        for y, _g, _x0, _x1 in v["cizgi"]:
            if y < 120:
                cizgi_ust[par][y] += 1
        for y, g, x0, _x1 in v["alt_cizgi"]:
            cizgi_alt[par][y] += 1
            if SERIT_GENISLIK[0] <= g <= SERIT_GENISLIK[1]:
                serit_x[par][x0] += 1
    secilen = maske_sec(dict(isabet), glif_top)
    dy, dx, hh, ww = _numara_dagilimi(sayfalar, secilen)
    sutun = {par: sutun_olc(proj[par], proj_n[par]) for par in (0, 1) if proj_n[par]}
    return {
        "glif_toplam": glif_top,
        "simge_x": {
            par: {s: (_mod(c), sorted(c.items())[:12]) for s, c in d.items()}
            for par, d in simge.items()
        },
        "numara_isabet": dict(isabet),
        "numara_maskesi": secilen,
        "numara_dy": sorted(dy.items()),
        "numara_dx": sorted(dx.items()),
        "numara_h": sorted(hh.items()),
        "numara_w": sorted(ww.items()),
        "sutun": sutun,
        "ust_cizgi": {par: sorted(c.items()) for par, c in cizgi_ust.items()},
        "alt_cizgi": {par: sorted(c.items()) for par, c in cizgi_alt.items()},
        "serit_x0": {par: sorted(c.items())[:10] for par, c in serit_x.items()},
        "metin_seridi": {par: c.most_common(6) for par, c in metin_serit.items()},
        "en_alt_murekkep": {par: sorted(c.items())[-8:] for par, c in en_alt.items()},
    }


def sayfa_ozeti(
    sayfalar: dict[int, dict[str, Any]],
) -> tuple[list[str], list[list[int]]]:
    """Sayfa basina kisa etiket ve 'glifli + serit adayli' ardisik araliklar
    (TEST_SAYFALARI adayi; kapsam gozle kesinlesir)."""
    satir, aralik = [], []
    cur: list[int] | None = None
    for n in sorted(sayfalar):
        v = sayfalar[n]
        serit_cizgi = any(
            SERIT_GENISLIK[0] <= c[1] <= SERIT_GENISLIK[1] for c in v["alt_cizgi"]
        )
        serit = serit_cizgi or bool(v["metin_seridi"])
        etiket = f"{n}:g{len(v['glif'])}{'s' if serit_cizgi else 'm' if serit else ''}"
        if v["sari_bant"] > 60:
            etiket += "Y"
        if v["kirmizi_bant"] > 600:
            etiket += "K"
        if not v["glif"] and v["koyu"] < 2000:
            etiket += "-kapak"
        satir.append(etiket)
        if v["glif"] and serit:
            if cur is not None and n == cur[1] + 1:
                cur[1] = n
            else:
                cur = [n, n]
                aralik.append(cur)
        else:
            cur = None
    return satir, aralik


def taslak(ad: str, t: dict[str, Any], aralik: list[list[int]], sayfa_n: int) -> str:
    sx = t["simge_x"]
    dy = [k for k, _ in t["numara_dy"]]
    dx = [k for k, _ in t["numara_dx"]]
    hh = [k for k, _ in t["numara_h"]]
    s = t["sutun"]

    def sut(par: int) -> str:
        v = s.get(par)
        if not v or not v["murekkep_x"]:
            return "None"
        mx = v["murekkep_x"]
        if v[
            "ayrac"
        ]:  # orta ayrac cizgisi: sinirlar cizginin iki yani (dikey yazi payi)
            ay = v["ayrac"][0]
            return f'{{"L": ({mx[0] - 2}, {ay - 8}), "R": ({ay + 10}, {mx[1] + 2})}}'
        if not v["orta_bosluk"]:
            return "None"
        ob = v["orta_bosluk"]
        return f'{{"L": ({mx[0] - 2}, {ob[0] - 1}), "R": ({ob[1] + 2}, {mx[1] + 2})}}'

    def yl(par: int, ad: str) -> str:
        c = t[ad][par]
        return repr(c[:6]) if c else "None"

    return "\n".join(
        [
            f"# --- kesif taslagi: {ad} ({sayfa_n} sayfa; glif {t['glif_toplam']}) ---",
            f"KART = {KART}",
            f"BEKLENEN_SAYFA = {sayfa_n}",
            f"TEST_SAYFALARI = {tuple(tuple(x) for x in aralik)}  # GOZ: glif + serit adayi araliklari",
            "GLIF_GENISLET = True",
            "GLIF_BOY = (12, 17, 12, 17)",
            "SIMGE_X = {1: {"
            f'"L": {sx[1]["L"][0]}, "R": {sx[1]["R"][0]}}}, 0: {{"L": {sx[0]["L"][0]}, '
            f'"R": {sx[0]["R"][0]}}}}}  # mod; histogram JSON\'da',
            "SIMGE_TOLERANS = 16",
            f'numara_maskesi = ortak.NUMARA_MASKELERI["{t["numara_maskesi"]}"]  # isabet {t["numara_isabet"]}',
            f"PENCERE = ({(min(dy) - 2) if dy else -6}, {(max(dy) + 14) if dy else 34}, "
            f"{(min(dx) - 2) if dx else 6}, 52)  # dy {dy[:1]}..{dy[-1:]}, dx {dx[:1]}..{dx[-1:]}",
            f"NUMARA_H = ({min(hh) if hh else 6}, {max(hh) if hh else 16})",
            "NUMARA_W_EN_COK = 30",
            f"NUMARA_DX = ({(min(dx) - 4) if dx else 8}, {(max(dx) + 4) if dx else 44})",
            "SERIT_SIMGE_PAY = 10",
            f"SUTUNLAR = {{0: {sut(0)}, 1: {sut(1)}}}  # GOZ: murekkep x + orta ayrac / bosluk",
            f"# orta ayrac cizgisi x: cift {s.get(0, {}).get('ayrac')} tek "
            f"{s.get(1, {}).get('ayrac')}; bosluk: cift {s.get(0, {}).get('orta_bosluk')} "
            f"tek {s.get(1, {}).get('orta_bosluk')}",
            f"UST_BANT = ...  # GOZ: ust cizgiler cift {yl(0, 'ust_cizgi')} tek {yl(1, 'ust_cizgi')} (+3)",
            f"SAYFA_ALTI = ...  # GOZ: en alt murekkep cift {yl(0, 'en_alt_murekkep')} tek "
            f"{yl(1, 'en_alt_murekkep')}; alt cizgiler cift {yl(0, 'alt_cizgi')} tek {yl(1, 'alt_cizgi')}",
            f"# serit cizgisi x0 adaylari cift {yl(0, 'serit_x0')} tek {yl(1, 'serit_x0')}",
            f"# duz metin serit (y0, y1, x0~) cift {yl(0, 'metin_seridi')} tek {yl(1, 'metin_seridi')}",
            "# -> anahtar_bolgesi on ayari: cerceveli serit (2 cizgi) / duz metin / tablo -- GOZ",
            "SERIT_PAY = 4",
            "DISK_MERKEZ = (10, 8)",
            "BEYAZ_YARICAP = 17",
            "HALKA = (19, 23)",
        ]
    )


def goz_montaji(
    d: Path,
    sayfalar: dict[int, dict[str, Any]],
    t: dict[str, Any],
    adet: int,
    yol: Path,
) -> None:
    """Glifli ilk `adet` sayfa: SIMGE_X (mavi), sutun sinirlari (yesil), yatay
    cizgiler (kirmizi), glifler (mor kutu) kart ustune cizilir; yan yana montaj."""
    secim = [n for n in sorted(sayfalar) if sayfalar[n]["glif"]][:adet]
    ims = []
    for n in secim:
        im = Image.fromarray(kart(d, n).astype("uint8"))
        cz = ImageDraw.Draw(im)
        par = n % 2
        for s in ("L", "R"):
            x = t["simge_x"][par][s][0]
            if x is not None:
                cz.line([(x, 0), (x, im.height)], fill=(0, 0, 255), width=1)
        su = t["sutun"].get(par)
        if su and su["murekkep_x"]:
            xs = (
                list(su["murekkep_x"])
                + list(su["orta_bosluk"] or [])
                + list(su["ayrac"][:1])
            )
            for x in xs:
                cz.line([(x, 0), (x, im.height)], fill=(0, 160, 0), width=1)
        for y, _g, x0, x1 in sayfalar[n]["cizgi"]:
            cz.line([(x0, y), (x1, y)], fill=(255, 0, 0), width=2)
        for gy, gx in sayfalar[n]["glif"]:
            cz.rectangle(
                [gx - 2, gy - 2, gx + 18, gy + 18], outline=(160, 0, 200), width=2
            )
        cz.text((5, 5), f"s{n}", fill=(255, 0, 0))
        ims.append(im)
    if not ims:
        return
    m = Image.new(
        "RGB", (sum(i.width + 6 for i in ims), max(i.height for i in ims)), "white"
    )
    x = 0
    for i in ims:
        m.paste(i, (x, 0))
        x += i.width + 6
    m.save(yol)
    print("goz montaji:", yol, m.size)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--klasor", required=True, help="screenshots alt klasor globu")
    ap.add_argument("--ornek", type=int, default=0, help="yalniz ilk N sayfa")
    ap.add_argument("--goz", type=int, default=0, help="goz montajina kac glifli sayfa")
    ap.add_argument("--cikti", default=None, help="cikti adi (_kesif_<AD>)")
    args = ap.parse_args()
    d = klasor_bul(args.klasor)
    ad = args.cikti or "".join(ch if ch.isalnum() else "_" for ch in d.name)[:40]
    dosyalar = sorted(d.glob("sayfa_*.png"))
    if args.ornek:
        dosyalar = dosyalar[: args.ornek]
    sayfalar: dict[int, dict[str, Any]] = {}
    for f in dosyalar:
        n = int(f.stem[-4:])
        sayfalar[n] = sayfa_olc(kart(d, n))
    t = topla(sayfalar)
    satir, aralik = sayfa_ozeti(sayfalar)
    metin = taslak(ad, t, aralik, len(dosyalar))
    print(metin)
    print("\nsayfa ozeti (n:g<glif>[s=serit adayi][Y sari bant][K kirmizi bant]):")
    print(" ".join(satir))
    ortak.CIKTI.mkdir(parents=True, exist_ok=True)
    (ortak.CIKTI / f"_kesif_{ad}.txt").write_text(
        metin + "\n\n" + " ".join(satir) + "\n", "ascii"
    )
    ozet = dict(t)
    ozet["sayfa"] = {
        n: {k: v for k, v in s.items() if k not in ("x_proj", "isabet")}
        for n, s in sayfalar.items()
    }
    (ortak.CIKTI / f"_kesif_{ad}.json").write_text(
        json.dumps(ozet, ensure_ascii=True, default=int), "ascii"
    )
    print(f"yazildi: {ortak.CIKTI / f'_kesif_{ad}.txt'} / .json")
    if args.goz:
        goz_montaji(d, sayfalar, t, args.goz, ortak.CIKTI / f"_kesif_{ad}_goz.png")


if __name__ == "__main__":
    main()
