#!/usr/bin/env python
"""345 2025 TYT Turkce: soru kirpim kutularini uretir (sos345tyt_kutu.py deseni).

CAPA
----
Faz 1 olcumu: basili (camgobegi) soru numarasi sayisi (2070) == anahtar
tablosu hucre sayisi; sorular sayfa sirasinda numaralara dagitilir
(sutun_sira). Numara BIRINCIL kanaldir: okuyucu simgesi bu kitapta soruya
degil BLOGA konur (2067 simge / 2070 soru; 'OSYM KOSESI' kutusu, ortak parca
'a - b. sorulari ...', oncullu soru girisi tek simge tasir). Numara sayisi
tutmazsa sutuna kutu URETILMEZ (tahmin yok).

BLOK USTU
---------
Onceki sorunun numarasi ile bu sorunun numarasi arasinda (numaranin 12 px
altina kadar) simge varsa kutu ustu aramasi simgenin ustunden baslar: blok
(ortak parca, oncul, kose kutusu) sorunun kirpimina girer. Simge yoksa
(blogun ikinci sorusu) arama numaradan baslar.

ORTAK PARCA
-----------
'a - b. sorulari asagidaki parcaya gore cevaplayiniz.' gruplarinda (10 grup,
ORTAK_GRUPLAR) ilk sorunun kirpimi parcayi icerir; sonraki soruya ilk
sorunun parca bolgesi (kutu ustu .. ilk numara) `ortak_parca` olarak
yazilir ve kirp adimi onu soru goruntusunun ustune ekler.

DIKEY KURAL
-----------
- Tavan: kirmizi konu adi bandi varsa son satiri + BANT_PAY, yoksa TAVAN.
- Kutu ustu: blok ustunden yukari ilk >= BOSLUK satirlik bos bandin alt ucu -
  UST_PAY (murekkep: min kanal < MUREKKEP); bant UST_EN_COK px'ten yukarida
  kaliyorsa 25 px ustune kadar >= 3 satirlik kisa bant.
- Kutu alti: sonraki kutunun ustu - 1; sutunun son sorusunda SAYFA_ALTI.
  Sayfa alti serit YOK; sayfa numarasi bandi SAYFA_NO_UST'ten asagida.

YATAY KURAL
-----------
Sutun ayraci dikey cizgisi (y 150-880, x 355-390'da en dolu sutun):
    sol [4, cizgi-2]   sag [cizgi+3, 738]

KULLANIM
--------
    python backend/scripts/kitap/tur345tyt_kutu.py
    python backend/scripts/kitap/tur345tyt_kutu.py --yaz
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acil25_geo_kirp import okuyucu_maskesi
from tur345tyt_tarama import kart, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
TARAMA = CIKTI / "345_2025_tyt_turkce_capa_taramasi.json"
ANAHTAR = CIKTI / "345_2025_tyt_turkce_cevap_anahtari.json"
HEDEF = CIKTI / "345_2025_tyt_turkce_kirpim_kutulari.json"

KART_G, KART_Y = 742, 979
UST_PAY = 3
BOSLUK = 10
MUREKKEP = 170
UST_EN_COK = 70
NUMARA_X0 = {"L": 55, "R": 375}
BANT_PAY = 4
SAYFA_ALTI = 925
SAYFA_NO_UST = 930
# Sayfa ust bandi (rozet, OSYM TADINDA logosu, KAZANIM ODAKLI yazisi) y < 112:
# ilk sorunun kutusu bu satirdan yukari cikmaz.
TAVAN = 112
EN_KISA = 30
BEKLENEN_KUTU = 2070
# Sayfa ust bandi (rozet / 'KAZANIM ODAKLI SORULAR' / 'OSYM TADINDA' basligi)
# bu satirin ustunde; soru capasi burada olamaz.
UST_BANT_ALTI = 112
SIMGE_ALT = 12  # simge numaranin en cok bu kadar altinda (ayni satir)
SIMGE_YARI = 7  # simge merkezinden ust kenarina
CIZGI_ARALIK = (355, 390)
CIZGI_DOLULUK = 0.6
VARSAYILAN_CIZGI = {0: 372, 1: 369}
KENAR = (4, 738)


def ara_cizgi(a: np.ndarray, d: int) -> int:
    """Sutun ayraci x'i (olculemezse parite varsayilani)."""
    x0, x1 = CIZGI_ARALIK
    dolu = (a[150:880, x0:x1].min(axis=2) < 245).mean(axis=0)
    x = int(np.argmax(dolu))
    return x0 + x if dolu[x] >= CIZGI_DOLULUK else VARSAYILAN_CIZGI[d % 2]


def bant_tavani(a: np.ndarray) -> int:
    """Unite adi bandinin (kirmizi) son satiri + BANT_PAY; bant yoksa TAVAN."""
    b = a[90:150].astype(np.int16)
    kir = ((b[..., 0] > 150) & (b[..., 1] < 90) & (b[..., 2] < 90)).sum(axis=1)
    ys = np.where(kir > 0)[0]
    return max(int(ys.max()) + 90 + BANT_PAY, TAVAN) if len(ys) else TAVAN


def sutun_siniri(t: str, cizgi: int) -> tuple[int, int]:
    return (KENAR[0], cizgi - 2) if t == "L" else (cizgi + 3, KENAR[1])


def sutun_simgeleri(sayfa: dict, t: str) -> list[list[int]]:
    # Tarama simgeleri zaten sutuna ayirdi (SIMGE_X araliklari, kim345tyt_tarama).
    return sorted(sayfa["simge"][t])


def _tum_simgeler(s: dict, d: int, disari: list[list[int]]) -> list[list[int]]:
    """Beyazlatilacak TUM okuyucu simgeleri [cy, cx]: soru capalari + sutun disi + serit ustu."""
    out = [list(m) for t in "LR" for m in s["simge"][t]]
    return out + [[cy, cx] for n, cy, cx in disari if n == d]


def _ust(
    y: int, tavan: int, murekkep: np.ndarray, bosluk: int = BOSLUK, pay: int = UST_PAY
) -> int:
    """Capadan yukari: ilk >= bosluk satirlik bos bandin alt ucu - pay."""
    bos = 0
    r = y - 1
    while r >= tavan:
        if murekkep[r]:
            bos = 0
        else:
            bos += 1
            if bos >= bosluk:
                return max(tavan, r + bosluk - pay)
        r -= 1
    return tavan


def _capa_sec(s: dict, t: str, k: int) -> tuple[list[list[int]], str] | None:
    """Sutunun capasi: ust bandin altindaki basili numaralar, sayisi anahtardan sutuna dusen soru sayisina (k) esitse."""
    num = [n for n in s["numara"][t] if n[0] >= UST_BANT_ALTI]
    if len(num) == k:
        return [[n[0], n[1]] for n in sorted(num)], "numara"
    return None


def blok_ustleri(capa: list[list[int]], simge: list[list[int]]) -> list[int]:
    """Her soru icin kutu ustu aramasinin baslangici: onceki numara ile bu numara
    (her ikisi + SIMGE_ALT) arasindaki en ustteki simgenin ustu, yoksa numaranin ustu."""
    out = []
    for i, (y0, y1) in enumerate(capa):
        # simge en yakin (ustteki) numaraya aittir: onceki numaranin ortasi + SIMGE_ALT alt sinir
        onceki = (capa[i - 1][0] + capa[i - 1][1]) // 2 + SIMGE_ALT if i else 0
        orta = (y0 + y1) // 2
        ust = [m[0] for m in simge if onceki < m[0] <= orta + SIMGE_ALT]
        out.append(min([y0, *[m - SIMGE_YARI for m in ust]]))
    return out


def _ustler(
    capa: list[list[int]],
    blok: list[int],
    tavan0: int,
    murekkep: np.ndarray,
    sayac: Counter[str],
) -> list[int]:
    out = []
    for i, y in enumerate(blok):
        tavan = capa[i - 1][1] + 1 if i else tavan0
        if y < capa[i][0] - SIMGE_ALT:
            sayac["blok_simgesi"] += 1
        u = _ust(y, tavan, murekkep)
        if u < y - UST_EN_COK:
            u = _ust(y, max(tavan, y - 25), murekkep, bosluk=3, pay=1)
            sayac["tavan_asimi"] += 1
        out.append(min(u, y - UST_PAY))
    return out


KOSE_RENK = np.array([240, 125, 25])
KOSE_YAN_SATIR = 12
KOSE_BOY = (22, 40)  # 'OSYM KOSESI' etiketinin turuncu dairesi (olculdu: 30x30)


def _kose_duzelt(
    a: np.ndarray,
    x0: int,
    x1: int,
    *,
    capa: list[list[int]],
    ustler: list[int],
    sayac: Counter[str],
) -> list[int]:
    """'OSYM KOSESI' kutusu: kutu ustu etiketin ustu olur.

    Kose kutusu onceki sorunun son siklarina 10 px'ten yakin basilabildigi icin
    bos-bant kurali ust siniri onceki sorunun icine tasir (gozle: T046, T052,
    T086, T127, T128). Onceki capanin altinda, capanin ustunde ya da yaninda
    turuncu etiket dairesi varsa kutu ustu = min(etiket ustu, capa ustu) - 1
    (yalniz asagi kaydirir).
    """
    from scipy import ndimage

    b = a[:, x0:x1].astype(np.int16)
    tur = np.abs(b - KOSE_RENK).sum(axis=2) < 70
    lab, _ = ndimage.label(tur, np.ones((3, 3), bool))
    etiket = []
    for sl in ndimage.find_objects(lab):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if KOSE_BOY[0] <= h <= KOSE_BOY[1] and KOSE_BOY[0] <= w <= KOSE_BOY[1]:
            etiket.append(sl[0].start)
    out = list(ustler)
    for i in range(1, len(capa)):
        onceki = capa[i - 1][1]
        # etiket capanin ustunde ya da yaninda (sag tarafta, ayni satirda)
        adaylar = [y for y in etiket if onceki < y < capa[i][1] + 20]
        # Okuyucu diski (beyazlatilir) onceki sorunun son satirina degebilir:
        # sinir min(etiket, capa) - 1 (gozle: T046 E satiri capanin ~2 px
        # ustunde biter; - 3 satirin alt kenarini kesiyordu).
        ust = min([*adaylar, capa[i][0]]) - 1 if adaylar else None
        if ust is not None:
            # Onceki sorunun son satiri etiketin hemen ustune kadar inebilir
            # (T046: satir alti capa ustunden 1-2 px asagida): etiket ustune
            # kadar notr murekkep tasiyan son satirin bir alti.
            et = min(adaylar)
            # harf alt kenari kenar yumusatmasiyla acik gri: esik 200
            notr = ((b.max(axis=2) - b.min(axis=2)) < 50) & (b.min(axis=2) < 200)
            satir = np.where(notr[ust:et].any(axis=1))[0]
            if len(satir):
                ust = ust + int(satir.max()) + 1
            # Bu kitapta onceki sorunun son sik satiri etiketin YANINDA (ayni
            # yukseklikte, solda) bitebilir (gozle: T071_04): etiket ustunden
            # asagi notr murekkepli satirlar atlanir (en cok KOSE_YAN_SATIR).
            n = 0
            while notr[ust].any() and n < KOSE_YAN_SATIR:
                ust += 1
                n += 1
        if ust is not None and ust > out[i]:
            out[i] = ust
            sayac["kose_etiketi"] += 1
    return out


def _sutun_kutulari(
    qs: list[dict],
    capa: list[list[int]],
    kanal: str,
    a: np.ndarray,
    t: str,
    *,
    simge: list[list[int]],
    cizgi: int,
    tavan0: int,
    sayac: Counter[str],
    kesim: list[str],
) -> list[dict]:
    x0, x1 = sutun_siniri(t, cizgi)
    xg = max(x0, NUMARA_X0[t] - 3)
    murekkep = (a[:, xg:x1].min(axis=2) < MUREKKEP).any(axis=1)
    ustler = _ustler(capa, blok_ustleri(capa, simge), tavan0, murekkep, sayac)
    ustler = _kose_duzelt(a, x0, x1, capa=capa, ustler=ustler, sayac=sayac)
    b = a[:, x0:x1].astype(np.int16)
    notr = (((b.max(axis=2) - b.min(axis=2)) < 40) & (b.min(axis=2) < 140)).sum(axis=1)
    out = []
    for i, q in enumerate(qs):
        if int(notr[ustler[i] - 3 : ustler[i] + 3].sum()):
            kesim.append(f"{q['birim']}_{q['soru']:02d}")
        alt = ustler[i + 1] - 1 if i + 1 < len(qs) else SAYFA_ALTI
        out.append(
            {
                "birim": q["birim"],
                "soru": q["soru"],
                "dosya": q["dosya"],
                "sutun": t,
                "sutun_sira": q["sutun_sira"],
                "kutu": [x0, ustler[i], x1, alt],
                "capa": capa[i],
                "capa_kanali": kanal,
            }
        )
    return out


def kutulari_uret() -> dict[str, Any]:
    tt = json.loads(TARAMA.read_text("ascii"))
    tarama = tt["sayfalar"]
    disari = tt["sutun_disi_simge"] + tt["serit_simgesi"]
    anahtar = json.loads(ANAHTAR.read_text("ascii"))["cevaplar"]
    kaynak = kaynak_dizin()
    sutunlar: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for c in anahtar:
        sutunlar[(c["dosya"], c["sutun"])].append(c)
    kutular: list[dict] = []
    kutusuz: list[dict] = []
    kanal: Counter[str] = Counter()
    sayac: Counter[str] = Counter()
    kesim: list[str] = []
    cizgiler: dict[str, int] = {}
    for d in sorted({k[0] for k in sutunlar}):
        s = tarama[str(d)]
        a = kart(kaynak, d).astype(np.uint8)
        a[okuyucu_maskesi(a, _tum_simgeler(s, d, disari))] = 255
        tavan0 = bant_tavani(a)
        cizgi = ara_cizgi(a, d)
        cizgiler[str(d)] = cizgi
        for t in "LR":
            qs = sorted(sutunlar.get((d, t), []), key=lambda c: c["sutun_sira"])
            if not qs:
                continue
            secim = _capa_sec(s, t, len(qs))
            if secim is None:
                kutusuz += [
                    {"birim": q["birim"], "soru": q["soru"], "dosya": d, "sutun": t}
                    for q in qs
                ]
                continue
            capa, kaynak_kanal = secim
            kanal[kaynak_kanal] += 1
            kutular += _sutun_kutulari(
                qs,
                capa,
                kaynak_kanal,
                a,
                t,
                simge=sorted(s["simge"][t]),
                cizgi=cizgi,
                tavan0=tavan0,
                sayac=sayac,
                kesim=kesim,
            )
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
    n_ortak = ortak_parcalar(kutular)
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    return {
        "kaynak": "345 2025 TYT Turkce Soru Bankasi",
        "arac": "scripts/kitap/tur345tyt_kutu.py",
        "kart": [589, 43, KART_G, KART_Y],
        "capa": "sutun basina basili soru numarasi (toplam == anahtar hucre sayisi); blok ustu okuyucu simgesinden",
        "kural": (
            f"Kutu ustu: capadan yukari ilk {BOSLUK} satirlik bos bandin alt ucu - {UST_PAY} "
            f"(tavan onceki capa / unite adi bandi + {BANT_PAY}); alti sonraki kutunun "
            f"ustu - 1, sutun sonunda {SAYFA_ALTI}."
        ),
        "sutun_kanali": dict(kanal),
        "ust_kurali_sayaci": dict(sayac),
        "kesim_metne_degen_kutu": kesim,
        "ara_cizgi": cizgiler,
        "ortak_parca_eklenen_soru": n_ortak,
        "kutu_sayisi": len(kutular),
        "kutusuz_soru": len(kutusuz),
        "yukseklik": {"min": yuk[0], "medyan": yuk[len(yuk) // 2], "max": yuk[-1]}
        if yuk
        else None,
        "kutular": kutular,
        "kutusuz": kutusuz,
    }


# 'a - b. sorulari asagidaki parcaya gore cevaplayiniz.' gruplari (birim, ilk, son).
# Olculdu: kirmizi cerceveli baslik 9 (sutun basinda; tt_ortak_bul), 'OSYM
# KOSESI' icinde cercevesiz baslik 1 (T050 3-4, gozle). Grubun ilk sorusunun
# kirpimi parcayi zaten icerir (simge basliktadir); sonraki sorunun kirpiminin
# ustune parca eklenir (kirp adimi) -- goruntu tek basina cozulebilir olsun.
ORTAK_GRUPLAR: tuple[tuple[str, int, int], ...] = (
    ("TRT345-T048", 1, 2),
    ("TRT345-T049", 1, 2),
    ("TRT345-T050", 1, 2),
    ("TRT345-T050", 3, 4),
    ("TRT345-T051", 1, 2),
    ("TRT345-T053", 1, 2),
    ("TRT345-T054", 1, 2),
    ("TRT345-T055", 1, 2),
    ("TRT345-T205", 10, 11),
    ("TRT345-T207", 3, 4),
)
ORTAK_EN_AZ = 150  # parca (kutu ustu .. ilk numara) en az bu kadar yuksek


def ortak_parcalar(kutular: list[dict]) -> int:
    """Grubun sonraki sorularina ilk sorunun parca bolgesini ekler; eklenen soru sayisi."""
    ad = {(k["birim"], k["soru"]): k for k in kutular}
    n = 0
    for birim, ilk, son in ORTAK_GRUPLAR:
        i = ad[(birim, ilk)]
        x0, y0, x1, _ = i["kutu"]
        parca = [x0, y0, x1, i["capa"][0] - 2]
        for s in range(ilk + 1, son + 1):
            ad[(birim, s)]["ortak_parca"] = {
                "ilk_soru": ilk,
                "kutu": parca,
                "dosya": i["dosya"],
            }
            n += 1
    return n


def kapilar(veri: dict[str, Any]) -> list[str]:  # noqa: PLR0912
    hata = []
    if veri["kutu_sayisi"] != BEKLENEN_KUTU or veri["kutusuz_soru"]:
        hata.append(f"kutu {veri['kutu_sayisi']} / kutusuz {veri['kutusuz_soru']}")
    for k in veri["kutular"]:
        o = k.get("ortak_parca")
        if o and o["kutu"][3] - o["kutu"][1] < ORTAK_EN_AZ:
            hata.append(f"ortak parca kisa: {k['birim']}_{k['soru']:02d}")
    if sum(1 for k in veri["kutular"] if k.get("ortak_parca")) != sum(
        s - i for _, i, s in ORTAK_GRUPLAR
    ):
        hata.append("ortak parca eklenen soru sayisi")
    for k in veri["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        ad = f"{k['dosya']}{k['sutun']}#{k['sutun_sira']}"
        if not (0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y):
            hata.append(f"kart disi/ters: {ad} {k['kutu']}")
        if y1 - y0 < EN_KISA:
            hata.append(f"cok kisa: {ad} {y1 - y0}px")
        if y1 >= SAYFA_NO_UST:
            hata.append(f"sayfa numarasi sizintisi: {ad} {y1} >= {SAYFA_NO_UST}")
        # capa merkezi kutuda (kose kutusunda ust sinir capanin ustunden 1-3 px
        # asagida olabilir; disk beyazlatilir)
        if not y0 <= (k["capa"][0] + k["capa"][1]) // 2 < y1:
            hata.append(f"capa kutu disinda: {ad}")
    grup = defaultdict(list)
    for k in veri["kutular"]:
        grup[(k["dosya"], k["sutun"])].append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        if [k["sutun_sira"] for k in g] != list(range(len(g))):
            hata.append(f"sira bozuk: {anahtar}")
        for a, c in itertools.pairwise(g):
            if a["kutu"][3] >= c["kutu"][1]:
                hata.append(f"cakisma: {anahtar}")
            if a["kutu"][3] >= c["capa"][0]:
                hata.append(f"sonraki capa ustteki kutuda: {anahtar}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true", help="JSON dosyasini guncelle")
    args = ap.parse_args()
    veri = kutulari_uret()
    hata = kapilar(veri)
    print(f"kutu sayisi: {veri['kutu_sayisi']}  kutusuz: {veri['kutusuz_soru']}")
    print(
        f"sutun kanali: {veri['sutun_kanali']}  ust kurali: {veri['ust_kurali_sayaci']}"
    )
    print(f"ust kesimi notr metne degen kutu: {veri['kesim_metne_degen_kutu']}")
    print(f"yukseklik: {veri['yukseklik']}")
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    if args.yaz:
        HEDEF.write_text(
            json.dumps(veri, indent=1) + "\n", encoding="ascii", newline="\n"
        )
        print("yazildi:", HEDEF)


if __name__ == "__main__":
    main()
