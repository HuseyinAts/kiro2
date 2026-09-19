#!/usr/bin/env python
"""C1CELL 2024 TYT-AYT Geometri: KIRPIM KAPISI (birim cevap-sayisi dogrulamasi).

NE ISE YARAR
------------
Kirpim (soru gorseli kesme) yapmadan ONCE her birimin (test) soru sayisinin
dogru oldugunu bagimsiz iki kaynaktan garanti eder:
  (a) SIMGE sayisi  -- her sorunun bir okuyucu-dugmesi (simge) var; sayfa
      basina simge sayimi Faz 0 taramasindan gelir (faz0_c1.json 'yer').
  (b) CEVAP sayisi N -- test sonu cevap seridindeki numara adedi; 163 serit
      8 montaj halinde gorsel okundu (c1cell_2024_geometri_cevap_anahtari.json).
Bir birimde simge_sayisi == N ise birim kirpima UYGUN; degilse BAYRAK (elle
inceleme). Boylece siniflandirici/simge-dedektoru hatasi kirpima sizmaz.

NEDEN GEREKLI -- IDDIA DEGIL OLCUM
----------------------------------
Faz 0'da tek sinyal (salmon arka-plan, serit, OCR, gorsel desen) tek basina
%100 dogru cikmadi. Garanti tek bir yukari-akis sinyalinden degil, bu yapisal
kapidan gelir: iki bagimsiz sayimin esitligi.

SEGMENTASYON -- 'N'e GERI TOPLA
-------------------------------
Birim serit sayfasinda biter. Baslangic: serit sayfasindan GERIYE dogru simge
biriktirilir; toplam tam N olunca birim baslangici bulunur (onceki serit
sinirinda durur). Bir sayfa grubu N'i tam veremezse (asar ya da sinira dayanir)
birim BAYRAK olur -- bu, gercek bir simge-sayim anomalisidir.

SIMGE DUZELTME OVERLAY -- HAM OLCUME DOKUNULMAZ
----------------------------------------------
Faz 0 simge-dedektoru, bir testin ilk sayfasindaki KONU-KUTUSU (pembe formul
kutusu) isaretini ya da sekil ogesini bazen soru simgesi sayar. Bu yanlis-
pozitifler gorsel dogrulanip c1cell_2024_geometri_simge_duzeltme.json
overlay'ine yazildi (kaldirilacak [x,y] + gerekce). Ham faz0_c1.json'a
DOKUNULMAZ; kapi overlay'i uygular. Ilk turda 4 birim bu yuzden bayrakti
(s14, s69, s148, s150); overlay ile 163/163 gecti.

MUTASYON-DOGRULAMA
------------------
Kapi trivial gecmiyor: bir birimin N'sini bozunca ya da bir sayfadan gercek
simge cikarinca bayrak sayisi artar (test edildi). Temizde bayrak=0.

GIRDI
-----
  backend/_geo1_gecici/faz0_c1.json             ham simge/'yer' (Faz 0 taramasi)
  backend/_geo1_gecici/c1_sayfa_tipi_kesin.json sayfa -> soru|konu_ogren (bilgi amacli)
  veriseti/zkitap/cikti/c1cell_2024_geometri_cevap_anahtari.json  N/birim
  veriseti/zkitap/cikti/c1cell_2024_geometri_simge_duzeltme.json  overlay
Ham yapisal veri (faz0) _geo1_gecici scratch'te durur; Faz 0 tarayicisi
(_faz0_genel.py) ile yeniden uretilebilir -- git'e girmez.

CIKTI
-----
  veriseti/zkitap/cikti/c1cell_2024_geometri_kapi_raporu.json  (163 birim, gecer)

KULLANIM
--------
    python backend/scripts/kitap/c1cell_geo_kapi.py
"""

from __future__ import annotations

import json
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
GECICI = KOK / "backend" / "_geo1_gecici"
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"

FAZ0 = GECICI / "faz0_c1.json"
CEVAP = CIKTI / "c1cell_2024_geometri_cevap_anahtari.json"
DUZELTME = CIKTI / "c1cell_2024_geometri_simge_duzeltme.json"
RAPOR = CIKTI / "c1cell_2024_geometri_kapi_raporu.json"


def _yakin(a, b, tol=3):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def simge_sayilari(faz0_yol, duzeltme_yol):
    """Ham 'yer' konumlarini oku, overlay'deki yanlis-pozitifleri dus, sayfa->simge dondur."""
    faz = json.loads(Path(faz0_yol).read_text("utf-8"))
    duz = (
        json.loads(Path(duzeltme_yol).read_text("utf-8"))
        if Path(duzeltme_yol).exists()
        else {}
    )
    simge: dict[int, int] = {}
    for d in faz:
        p = d["sayfa"]
        ys = [list(pt) for pt in d.get("yer", [])]
        giris = duz.get(str(p))
        kal = giris.get("kaldir", []) if isinstance(giris, dict) else []
        ys = [pt for pt in ys if not any(_yakin(pt, k) for k in kal)]
        simge[p] = len(ys)
    return simge


def birim_cevap_sayilari(cevap_yol):
    """Cevap anahtarindan birim -> (serit son_sayfa, N) turet."""
    anahtar = json.loads(Path(cevap_yol).read_text("utf-8"))["anahtar"]
    birim: dict[int, dict[str, int]] = {}
    for kayit in anahtar:
        b = kayit["birim"]
        birim.setdefault(b, {"son_sayfa": kayit["son_sayfa"], "n": 0})
        birim[b]["n"] += 1
    return [birim[b] for b in sorted(birim)]


def kapi_uygula(simge, birimler):
    """'N'e geri topla segmentasyonu; her birim icin gecer/bayrak dondur."""
    sonuc: list[dict] = []
    prev = 0
    for i, bi in enumerate(birimler, 1):
        P = bi["son_sayfa"]
        N = bi["n"]
        lb = prev + 1
        toplam = 0
        bas = None
        p = P
        while p >= lb:
            toplam += simge.get(p, 0)
            if toplam == N:
                bas = p
                break
            if toplam > N:
                break
            p -= 1
        gecer = bas is not None
        sonuc.append(
            {
                "birim": i,
                "serit": P,
                "bas_sayfa": bas,
                "sayfalar": list(range(bas, P + 1)) if bas else list(range(lb, P + 1)),
                "cevap_N": N,
                "gecer": gecer,
            }
        )
        prev = P
    return sonuc


def main():
    if not FAZ0.exists():
        raise SystemExit(
            f"HAM YAPISAL VERI YOK: {FAZ0}\n"
            "Faz 0 tarayicisini calistir (_faz0_genel.py) -- faz0 git'e girmez."
        )
    simge = simge_sayilari(FAZ0, DUZELTME)
    birimler = birim_cevap_sayilari(CEVAP)
    sonuc = kapi_uygula(simge, birimler)
    gecen = [b for b in sonuc if b["gecer"]]
    bayrak = [b for b in sonuc if not b["gecer"]]

    rapor = {
        "kaynak": "C1CELL 2024 TYT-AYT Geometri Soru Bankasi",
        "yontem": (
            "birim segmentasyonu: serit sayfasindan geriye simge biriktir, "
            "toplam N olunca birim baslar (onceki serit sinirinda). "
            "kural: her birimde simge sayisi cevap sayisina esit."
        ),
        "ozet": {"toplam": len(sonuc), "gecen": len(gecen), "bayrak": len(bayrak)},
        "birimler": sonuc,
    }
    Path(RAPOR).write_text(
        json.dumps(rapor, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print(f"birim: {len(sonuc)}  gecen: {len(gecen)}  bayrak: {len(bayrak)}")
    print(f"gecen birim toplam soru: {sum(b['cevap_N'] for b in gecen)}")
    for b in bayrak:
        print(
            f"  BAYRAK birim {b['birim']} (s{b['serit']}): N={b['cevap_N']} sayfalar={b['sayfalar']}"
        )
    print(f"yazildi {RAPOR.relative_to(KOK)}")


if __name__ == "__main__":
    main()
