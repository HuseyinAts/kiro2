"""Golden Flow merge kapisi — junit raporunu degerlendirir (A.2).

BU DOSYA NEDEN VAR
------------------
Kapi mantigi `.github/workflows/golden-flows.yml` icinde **inline heredoc**
Python'du: hicbir testi yoktu ve olamazdi. `tests/unit/test_workflow_yaml.py`
yalnizca YAML'in ayristirilabildigini kontrol ediyor. Yani merge'i bloklayan
kapinin kendisi olculmemis koddu — bu deponun kapatmaya calistigi
"bekci yalan soyluyor" sinifi. Sozlesme: `tests/unit/test_gf_esik_kapisi.py`.

1 AGU 2026 CANLI OLCUMU (kapinin esigi ILK KEZ olculdu)
--------------------------------------------------------
    cd backend && pytest tests/e2e/test_golden_flows.py -m golden_flow \
        --junitxml=gf-olcum.xml

    178 test  ->  164 GECTI · 12 DUSTU · 2 ATLANDI   (94 saniye)

Atlanan ikisi de belgeli: `gf4w2` (seed'e bagli due-card yok) ve `gf1wb`
(deploy Bearer-only, refresh cookie yok). Yani eski `ESIK = 150` bugun
ULASILABILIRDI — "esik yanlissa kapi kalici kirmizi olur" endisesi olcumle
curudu. Kusur baska yerdeydi:

  1. **Sabit esik suite buyudukce gevser.** golden-flows.md "yeni ust-duzey
     ozellik -> yeni GF testi" diyor. 250 teste cikildiginda `gecen >= 150`
     kurali 90 skip'i YESIL gecirir; esigin engellemek icin konuldugu
     "skip yalani" zamanla geri gelir. (Olculdu: v1 mantigi bu senaryoyu
     gecirdi -> `test_esik_suite_buyudukce_gevsemiyor` KIRMIZI dondu.)
  2. **`hata` hesaplaniyordu ama assert EDILMIYORDU.** 170 gecen + 8 dusen
     kombinasyonu eski kuraldan YESIL geciyordu; kirik akisi yalnizca
     pytest'in kendi cikis kodu yakaliyordu, kapi degil.
  3. Sinir yoktu: 6 atlama ile 148 atlama arasinda kural farki yoktu.

YENI KURAL — mutlak "gecen" sayisina bagli DEGIL, bu yuzden bayatlamaz:

    toplam >= TOPLAM_TABANI   (suite kuculmedi / collection cokmedi)
    hata   == 0               (golden-flows.md: kirik akisla merge YASAK)
    atlanan <= AZAMI_ATLANAN  (skip yalani)
"""

from __future__ import annotations

import sys

# Gerekce icin bkz. sayimlari_cikar(): girdi kendi CI kosumumuzun ciktisi.
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

# 1 Agu 2026 olcumu: 2 atlama (ikisi de belgeli). 5 pay birakildi; bu sayiyi
# YUKSELTMEK, skip'i yesil saymaya geri donmek demektir — bilincli karar olsun.
AZAMI_ATLANAN = 5

# 1 Agu 2026 olcumu: 178 test toplandi. Taban, testlerin silinmesini veya
# collection cokusunun "tertemiz gecti" gibi gorunmesini engeller.
TOPLAM_TABANI = 170


def sayimlari_cikar(xml_metni: str) -> dict[str, int]:
    """junit XML'den toplam/gecen/atlanan/hata sayimlarini cikarir.

    Hem `<testsuite>` hem `<testsuites>` kokunu okur (pytest surumune gore
    degisir); `errors` de `hata`ya dahildir — collection/fixture cokusu
    sessizce gecmemeli.
    """

    # uretiyor (gf-results.xml), disaridan gelen bir belge degil. `defusedxml`
    # yalnizca bunun icin yeni bir uretim bagimliligi olurdu.
    kok = ET.fromstring(xml_metni)  # noqa: S314  # nosec B314
    paketler = [kok] if kok.tag == "testsuite" else list(kok)
    toplam = sum(int(p.get("tests", 0)) for p in paketler)
    hata = sum(int(p.get("failures", 0)) + int(p.get("errors", 0)) for p in paketler)
    atlanan = sum(int(p.get("skipped", 0)) for p in paketler)
    return {
        "toplam": toplam,
        "gecen": toplam - hata - atlanan,
        "atlanan": atlanan,
        "hata": hata,
    }


def kapi_karari(sayimlar: dict[str, int]) -> str | None:
    """Kapi ihlalini aciklar; ihlal yoksa None."""
    toplam = sayimlar["toplam"]
    atlanan = sayimlar["atlanan"]
    hata = sayimlar["hata"]

    if toplam == 0:
        return "0 test kosuldu — kapi bos, yesil sayilamaz"
    if toplam < TOPLAM_TABANI:
        return (
            f"yalniz {toplam} test toplandi (taban {TOPLAM_TABANI}). Testler "
            "silinmis veya collection cokmus olabilir — 'hepsi gecti' yaniltici."
        )
    if hata:
        return (
            f"{hata} Golden Flow DUSTU. golden-flows.md: kirik Golden Flow ile "
            "merge YASAK — once regresyonu duzelt."
        )
    if atlanan > AZAMI_ATLANAN:
        return (
            f"{atlanan} test ATLANDI (azami {AZAMI_ATLANAN}). Skip FAIL uretmez; "
            "esik olmadan is yanlislikla yesil biterdi (30 Tem 2026: 148/178 skip)."
        )
    return None


def main(argv: list[str]) -> int:
    # Windows konsolu cp1254; Turkce/tire karakteri UnicodeEncodeError yapabilir.
    # `getattr` ile: pytest capture gibi sarmalayicilarda `reconfigure` olmayabilir.
    for akis in (sys.stdout, sys.stderr):
        yeniden_ayarla = getattr(akis, "reconfigure", None)
        if yeniden_ayarla is not None:
            yeniden_ayarla(encoding="utf-8", errors="replace")

    rapor = Path(argv[1] if len(argv) > 1 else "gf-results.xml")
    if not rapor.exists():
        print(
            f"::error::{rapor} YOK — kosum raporu uretilmedi, kapi dogrulanamaz",
            file=sys.stderr,
        )
        return 1
    sayimlar = sayimlari_cikar(rapor.read_text(encoding="utf-8"))
    print(
        "toplam={toplam} gecen={gecen} atlanan={atlanan} hata={hata}".format(**sayimlar)
    )
    karar = kapi_karari(sayimlar)
    if karar:
        print(f"::error::{karar}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
