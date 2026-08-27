"""Toplu cevap yaziminin TEK BOZUK OGEYE dayanikliligi (S255 -- Katman C).

NEDEN VAR
---------
`core/osym_exam_engine.py::save_answer` cevaplari bir kuyruga atiyor ve arka
plandaki isci onlari 1000'lik gruplar halinde tek islemde yaziyor. 27 Agu 2026
canli olcumu (`backend/scripts/batch_zehirlenme_probu.py`) sunu gosterdi:

    aday                              zehir_http  yazilan/beklenen  gunluk hata
    T2 "F"      (A-E disi)                   200             1/3             1
    T3 "AB"     (varchar(1) tasmasi)         200             1/3             1
    T4 yabanci question_id (FK)              200             1/3             1
    T5 "  "     (strip -> "")                200             3/3             1

Yani TEK bozuk oge, ayni gruptaki GECERLI cevaplari da goturuyordu; istemci
ise HTTP 200 goruyordu. Kuyruk modul duzeyinde TEK nesnede
(`osym_exam_engine.py:2180`), dolayisiyla dusen cevaplar **baska ogrencilerin**
cevaplari olabiliyordu.

Katman A (girdi kapisi) ve B (soru uyeligi) bugun bilinen dort tetikleyiciyi
kapatiyor. Bu dosya BESINCI, HENUZ BILINMEYEN tetikleyiciye karsi yazilmistir:
toplu yazim duserse ogeler TEK TEK yazilmali, yalnizca gercekten bozuk olan(lar)
dusmelidir. Patlama yaricapi 1000'den 1'e iner.

NEDEN SAHTE OTURUM
------------------
Burada olculen sey KONTROL AKISI ("toplu duserse tek tek dene, sayaci artir").
Gercek PostgreSQL davranisi (bozuk satir tum islemi geri alir) zaten CANLI
olculdu -- yukaridaki tablo. Ikisi birlikte gerekli: sahte oturumla akis,
canli probla gerceklik.
"""

from __future__ import annotations

from typing import Any

import pytest

from core.osym_exam_engine import OSYMExamEngine

pytestmark = [pytest.mark.unit]

BOZUK = "bozuk-oge"


def _oge(qid: str) -> dict[str, Any]:
    return {
        "id": f"id-{qid}",
        "exam_session_id": "oturum-1",
        "question_id": qid,
        "selected_answer": "A",
        "response_time_seconds": 1.0,
        "is_correct": True,
        "answer_changes": 0,
        "time_to_first_answer": 0.0,
    }


class _SahteOturum:
    """`execute` cagrilarini sayan, secili ogede patlayan AsyncSession taklidi."""

    def __init__(self, patlayanlar: set[str]) -> None:
        self.patlayanlar = patlayanlar
        self.execute_cagrilari: list[int] = []
        self.yazilan: list[str] = []

    async def execute(self, stmt: object, params: object = None) -> None:
        ogeler = params if isinstance(params, list) else [params]
        self.execute_cagrilari.append(len(ogeler))
        kotu = [
            o["question_id"] for o in ogeler if o["question_id"] in self.patlayanlar
        ]
        if kotu:
            # PostgreSQL davranisi: islem komple duser, HICBIR oge yazilmaz.
            raise RuntimeError(f"sahte DB reddi: {kotu}")
        self.yazilan.extend(o["question_id"] for o in ogeler)

    async def commit(self) -> None:
        return None


class _SahteBaglam:
    def __init__(self, oturum: _SahteOturum) -> None:
        self._oturum = oturum

    async def __aenter__(self) -> _SahteOturum:
        return self._oturum

    async def __aexit__(self, *_: object) -> bool:
        return False


@pytest.fixture
def motor_ve_oturum(monkeypatch: pytest.MonkeyPatch):
    def _kur(patlayanlar: set[str]) -> tuple[OSYMExamEngine, _SahteOturum]:
        oturum = _SahteOturum(patlayanlar)
        monkeypatch.setattr(
            "core.database.get_db_session_context",
            lambda: _SahteBaglam(oturum),
        )
        return OSYMExamEngine(), oturum

    return _kur


async def test_kontrol_kolu_saglam_batch_tek_islemde_yazilir(motor_ve_oturum) -> None:
    """KONTROL KOLU: saglam batch'te tek-tek yola DUSULMEMELI.

    Her zaman tek tek yazmak testi gecirirdi ama 1000 gidis-donus demektir.
    Bu test o kacamagi kapatir.
    """
    motor, oturum = motor_ve_oturum(set())
    batch = [_oge(f"q{i}") for i in range(4)]

    yazilan, dusen = await motor._toplu_yaz_kurtarmali(object(), batch)

    assert (yazilan, dusen) == (4, 0)
    assert oturum.execute_cagrilari == [4], (
        "saglam batch TEK toplu islemde yazilmali, tek tek DEGIL: "
        f"{oturum.execute_cagrilari}"
    )


async def test_tek_bozuk_oge_komsulari_oldurmez(motor_ve_oturum) -> None:
    """ASIL SOZLESME: bir bozuk oge yalniz KENDISI dusmeli.

    MUTASYON: tek-tek kurtarma dali kaldirilirsa (yazilan, dusen) (0, 4) olur
    ve bu test DUSER.
    """
    motor, oturum = motor_ve_oturum({BOZUK})
    batch = [_oge("q0"), _oge(BOZUK), _oge("q1"), _oge("q2")]

    yazilan, dusen = await motor._toplu_yaz_kurtarmali(object(), batch)

    assert (yazilan, dusen) == (3, 1), f"beklenen (3, 1): {(yazilan, dusen)}"
    assert sorted(oturum.yazilan) == ["q0", "q1", "q2"], (
        "gecerli komsu cevaplar kaybolmus -- zehirlenme sinifi hala acik: "
        f"{oturum.yazilan}"
    )
    # ALET DOGRULAMASI: once TOPLU denendigi ve DUSTUGU olculmeli; yoksa test
    # "hep tek tek yaziyoruz" implementasyonunda da gecerdi.
    assert (
        oturum.execute_cagrilari[0] == 4
    ), f"ilk cagri toplu OLMALI (4 oge): {oturum.execute_cagrilari}"
    assert oturum.execute_cagrilari[1:] == [
        1,
        1,
        1,
        1,
    ], f"dusen batch OGE OGE yeniden denenmeli: {oturum.execute_cagrilari}"


async def test_dusen_cevap_sayaci_artiyor(motor_ve_oturum) -> None:
    """`logger.error` yerine SAYAC: sessiz kayip olculebilir olmali.

    Gunluge yazmak yetmez -- gunluk dondurulmus bir sayi vermez ve
    "bugun kac cevap dustu" sorusu cevaplanamaz.
    """
    motor, _ = motor_ve_oturum({BOZUK})
    once_toplu = motor.toplu_yazim_hata_sayaci
    once_dusen = motor.dusen_cevap_sayaci

    await motor._toplu_yaz_kurtarmali(object(), [_oge("q0"), _oge(BOZUK)])

    assert motor.toplu_yazim_hata_sayaci == once_toplu + 1
    assert motor.dusen_cevap_sayaci == once_dusen + 1


async def test_hepsi_bozuksa_hicbiri_yazilmaz(motor_ve_oturum) -> None:
    """Kurtarma dali bozuk ogeyi SESSIZCE yazilmis saymamali."""
    motor, oturum = motor_ve_oturum({BOZUK})
    batch = [_oge(BOZUK), _oge(BOZUK)]

    yazilan, dusen = await motor._toplu_yaz_kurtarmali(object(), batch)

    assert (yazilan, dusen) == (0, 2)
    assert oturum.yazilan == []
