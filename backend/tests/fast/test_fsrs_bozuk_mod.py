"""FSRS bozuk mod ve reps sozlesmesi -- 9 Eyl 2026 canli veri bulgusundan.

OLCUM (canli DB, fsrs_cards, 107 satir):
    stability=2.3 difficulty=5.0 olan satir : 106
    scheduled_days=0 olan satir             : 106
    state='review' olan satir               : 107
    reps araligi                            : 1..40

Bu imza `services/fsrs_v6_service.py` icindeki "fsrs paketi yok" dalinin
birebir ciktisiydi: stability/difficulty girdiden degismeden geri donuyor,
due_date her cagrida BUGUNE sabitleniyor, aralik tablosu (days) hesaplanip
kullanilmadan atiliyordu. reps=40 olan bir kart bile "bugun tekrar et"
durumunda kaliyordu -- yani aralikli tekrar araliklamiyordu.

Bu testler o dalin bir daha sessizce yanlis veri uretmemesini sabitler.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services import fsrs_v6_service
from services.fsrs_v6_service import FSRSService


@pytest.fixture
def bozuk_mod(monkeypatch: pytest.MonkeyPatch) -> None:
    """fsrs paketi yokmus gibi davran."""
    monkeypatch.setattr(fsrs_v6_service, "_FSRS_AVAILABLE", False)
    monkeypatch.setattr(fsrs_v6_service, "SCHEDULER", None)


class TestBozukMod:
    def test_bozuk_modda_uydurma_psikometri_donmez(self, bozuk_mod: None) -> None:
        """stability/difficulty None olmali -- 2.3/5.0 sabiti DEGIL.

        Eski davranis `stability or 2.3` idi; girdi None ise 2.3, degilse
        girdinin kendisi donuyordu. Iki durumda da deger olculmus gibi
        DB'ye yaziliyordu.
        """
        sonuc = FSRSService.review_card(None, None, None, 3, 0)

        assert sonuc["degraded"] is True
        assert sonuc["stability"] is None, (
            "Bozuk modda stability uydurulmamali; None donmeli ki cagiran "
            f"DB'ye yazmasin. Donen: {sonuc['stability']!r}"
        )
        assert sonuc["difficulty"] is None

    def test_bozuk_modda_stability_girdiyi_aynen_dondurmez(
        self, bozuk_mod: None
    ) -> None:
        """Donguyu kiran asil dava: 40 tekrar sonra bile stability sabit kalmisti."""
        sonuc = FSRSService.review_card(2.3, 5.0, None, 3, 39)

        assert sonuc["stability"] != 2.3
        assert sonuc["stability"] is None

    @pytest.mark.parametrize(
        ("rating", "beklenen_gun"),
        [(1, 1), (2, 3), (3, 7), (4, 14)],
    )
    def test_bozuk_modda_due_date_ileri_kayar(
        self, bozuk_mod: None, rating: int, beklenen_gun: int
    ) -> None:
        """due_date bugune sabitlenmemeli -- aralik tablosu kullanilmali.

        Eski kod `days`i hesapliyor ama due_date'i `datetime.now()` olarak
        donduruyordu; degisken kullanilmadan atiliyordu. Canli tabloda 4
        farkli due_date gunu vardi ve hepsi gece yarisiydi.
        """
        simdi = datetime.now(UTC)
        sonuc = FSRSService.review_card(None, None, None, rating, 0)

        assert sonuc["scheduled_days"] == beklenen_gun
        gecen = sonuc["due_date"] - simdi
        assert gecen > timedelta(days=beklenen_gun - 1), (
            f"due_date ileri kaymadi: rating={rating} beklenen ~{beklenen_gun} "
            f"gun, donen {sonuc['due_date']}"
        )

    def test_bozuk_mod_sessiz_degil(
        self, bozuk_mod: None, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Her cagri ERROR seviyesinde loglanmali.

        Onceki halde uyari yalnizca import aninda bir kez veriliyordu; 106
        bozuk satir hicbir calisma-zamani sinyali uretmeden yazildi.
        """
        import logging

        with caplog.at_level(logging.ERROR, logger=fsrs_v6_service.__name__):
            FSRSService.review_card(None, None, None, 3, 0)

        kayitlar = [k.message for k in caplog.records]
        assert any(
            "BOZUK MOD" in m for m in kayitlar
        ), f"Bozuk mod calisti ama ERROR log yok: {kayitlar!r}"


class TestRepsSozlesmesi:
    """reps her zaman int donmeli -- asla None.

    fsrs kutuphanesinde `card.step` kart Review durumuna gectiginde None olur.
    Eski kod bunu dogrudan "reps" diye donduruyordu; donen degeri bir sonraki
    cagriya geri besleyen her cagirici `min(None, 1)` ile TypeError aliyordu.
    """

    def test_reps_asla_none_donmez(self) -> None:
        stab: float | None = None
        diff: float | None = None
        due: datetime | None = None
        reps = 0

        for tur in range(1, 6):
            sonuc = FSRSService.review_card(stab, diff, due, 3, reps)
            assert sonuc["reps"] is not None, f"tur {tur}: reps None dondu"
            assert isinstance(sonuc["reps"], int)
            stab = sonuc["stability"]
            diff = sonuc["difficulty"]
            due = sonuc["due_date"]
            reps = sonuc["reps"]

        assert reps == 5, "reps gercek bir sayac olmali, step proxy'si degil"

    def test_reps_none_girdisi_cokmez(self) -> None:
        """DB'den None okunan reps TypeError uretmemeli."""
        sonuc = FSRSService.review_card(None, None, None, 3, None)  # type: ignore[arg-type]
        assert sonuc["reps"] == 1


@pytest.mark.skipif(
    not fsrs_v6_service._FSRS_AVAILABLE,
    reason="fsrs paketi yok -- gercek zamanlama dogrulanamaz",
)
class TestGercekZamanlama:
    """fsrs kurulu oldugunda aralik gercekten buyumeli."""

    def test_ardisik_good_tekrarlarinda_stability_buyur(self) -> None:
        stab: float | None = None
        diff: float | None = None
        due: datetime | None = None
        reps = 0
        stabiliteler: list[float] = []

        for _ in range(4):
            sonuc = FSRSService.review_card(stab, diff, due, 3, reps)
            stab = sonuc["stability"]
            diff = sonuc["difficulty"]
            due = sonuc["due_date"]
            reps = sonuc["reps"]
            assert stab is not None
            stabiliteler.append(stab)

        assert (
            stabiliteler[-1] > stabiliteler[0]
        ), f"Ardisik Good tekrarlarinda stability buyumedi: {stabiliteler}"

    def test_scheduled_days_dolu_doner(self) -> None:
        sonuc = FSRSService.review_card(None, None, None, 3, 0)
        assert sonuc["scheduled_days"] is not None
        assert sonuc["scheduled_days"] >= 0
