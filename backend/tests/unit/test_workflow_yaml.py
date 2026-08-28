"""GitHub Actions workflow dosyalari AYRISTIRILABILIR olmali.

NEDEN BU TEST VAR
-----------------
30 Tem 2026'da olculdu: iki workflow dosyasi GECERSIZ YAML'di ve GitHub
onlari hic okuyamiyordu. Semptom sessizdi — Actions sekmesinde kosum
GORUNUYOR ama `total_jobs=0`, sure 0.0s, sonuc "failure". Yani "kirmizi CI"
gibi gorunen sey aslinda "hic calismayan CI"ydi.

  golden-flows.yml:172  tirnaksiz skalar icinde ": "  (kiran commit d1506c22f, 12 Nis)
  quality-gate.yml:18   `workflow_dispatch:` IKI KEZ  (kiran commit 9eee80d71, 29 May)

Sonuc: golden-flows 447 kosum / 0 basari, quality-gate 291 / 0. Depo kendi
kuralinda ("golden-flows.md kural 1: GF fail = PR MERGE EDILEMEZ") bir
birlestirme kapisi oldugunu yaziyordu; kapi 3,5 aydir MASTER DAHIL hicbir
dalda calismiyordu.

NEDEN `yaml.safe_load` TEK BASINA YETMEZ (olculdu)
--------------------------------------------------
PyYAML mukerrer anahtari SESSIZCE YUTAR — `safe_load` quality-gate.yml'i
"gecerli" der. Yani duz safe_load ile yazilan bir test iki kusurdan yalniz
birini yakalar ve YARIM-VAKUM olur. GitHub'in ayristiricisi ise mukerrer
anahtari reddediyor. Bu yuzden asagida mukerrer-anahtar-farkinda bir
yukleyici kullaniliyor: bu test fix'ten once IKI dosyada da kirmizi.

BU TEST NEYI KORUMAZ
--------------------
Ayristirilabilirlik != calisir olmak. Dosya gecerli olsa bile is atlanabilir,
adim patlayabilir veya tetikleyici dal listesi dar olabilir. Bu test yalnizca
"GitHub dosyayi OKUYABILIYOR mu" sorusunu cevaplar — kirilan sey tam olarak
buydu.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.unit]

WORKFLOW_DIZINI = Path(__file__).resolve().parents[3] / ".github" / "workflows"


class MukerrerAnahtarYukleyici(yaml.SafeLoader):
    """Mukerrer eslesme anahtarini HATA sayar (GitHub'in davranisi)."""


def _mukerrer_reddet(yukleyici: yaml.Loader, dugum: yaml.Node) -> dict:
    eslesme: dict = {}
    for anahtar_dugum, deger_dugum in dugum.value:
        anahtar = yukleyici.construct_object(anahtar_dugum, deep=False)
        if anahtar in eslesme:
            raise yaml.constructor.ConstructorError(
                None,
                None,
                f"tekrarli anahtar: {anahtar!r}",
                anahtar_dugum.start_mark,
            )
        eslesme[anahtar] = yukleyici.construct_object(deger_dugum, deep=False)
    return eslesme


MukerrerAnahtarYukleyici.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mukerrer_reddet
)


def _workflow_dosyalari() -> list[Path]:
    return sorted(
        p
        for p in WORKFLOW_DIZINI.iterdir()
        if p.is_file() and p.suffix in {".yml", ".yaml"}
    )


def test_workflow_dizini_bulunabiliyor():
    """KORLESME GUVENCESI: dizin yolu yanlissa asagidaki test BOS kume uzerinde
    gecer ve hicbir sey korumaz. Bu depoda tam bu sinif hata yasandi
    (0 dosya tarayan bir sir bekcisi yesil gorunuyordu)."""
    assert WORKFLOW_DIZINI.is_dir(), f"workflow dizini yok: {WORKFLOW_DIZINI}"
    assert (
        len(_workflow_dosyalari()) >= 5
    ), f"beklenenden az workflow dosyasi: {[p.name for p in _workflow_dosyalari()]}"


@pytest.mark.parametrize("yol", _workflow_dosyalari(), ids=lambda p: p.name)
def test_workflow_ayristirilabilir(yol: Path):
    """Her workflow dosyasi GitHub'in kabul edecegi sekilde ayristirilabilmeli."""
    metin = yol.read_text(encoding="utf-8")
    try:
        icerik = yaml.load(metin, Loader=MukerrerAnahtarYukleyici)  # noqa: S506
    except yaml.YAMLError as hata:
        pytest.fail(
            f"{yol.name} AYRISTIRILAMIYOR — GitHub bu dosyayi okuyamaz, "
            f"is calistirmadan 'failure' uretir:\n{hata}"
        )
    assert isinstance(
        icerik, dict
    ), f"{yol.name} bir eslesme dondurmeli, {type(icerik).__name__} dondu"
