"""
FSRS v6 Servisi (fsrs paketi kullanarak)

FAZ-1 Gorev 1.3 — Master Plan v2.0
py-fsrs yerine 'fsrs' paketi kullanilir (pip install fsrs).

Not: Detayli Turkce optimize FSRS icin fsrs_service.py kullanin.
Bu dosya master plan'in gerektirdigi sade fsrs wrapper.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fsrs import Card, Rating, Scheduler

    _FSRS_AVAILABLE = True
except ImportError:
    _FSRS_AVAILABLE = False
    logger.warning("fsrs paketi bulunamadi. pip install fsrs")

SCHEDULER = None
if _FSRS_AVAILABLE:
    SCHEDULER = Scheduler(
        desired_retention=0.90,
        maximum_interval=365,
    )

_RATING_MAP: dict[int, Any] = {}
if _FSRS_AVAILABLE:
    _RATING_MAP = {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy,
    }


class FSRSService:
    """
    FSRS v6 soru tekrar zamanlama servisi.
    fsrs==6.3.1 paketi ile 3 yeniden yapilmistir.
    """

    @staticmethod
    def first_review(rating_int: int) -> tuple[float, float]:
        """
        Yeni kart icin ilk tekrar.

        Args:
            rating_int: 1=Again, 2=Hard, 3=Good, 4=Easy

        Returns:
            (stability, difficulty) tuple
        """
        if not _FSRS_AVAILABLE or SCHEDULER is None:
            return 2.3, 5.0

        rating = _RATING_MAP.get(rating_int, Rating.Good)
        card = Card()
        card, _ = SCHEDULER.review_card(card, rating)
        return card.stability, card.difficulty

    @staticmethod
    def review_card(
        stability: float | None,
        difficulty: float | None,
        due_date: datetime | None,
        rating_int: int,
        reps: int,
    ) -> dict[str, Any]:
        """
        Mevcut karti guncelle ve sonraki tekrar tarihini hesapla.

        Args:
            stability: Mevcut kart stabilitesi (None ise yeni kart)
            difficulty: Mevcut kart zorlugu (None ise yeni kart)
            due_date: Mevcut bitis tarihi (None ise simdi)
            rating_int: 1=Again, 2=Hard, 3=Good, 4=Easy
            reps: Tekrar sayisi

        Returns:
            {
                "degraded": bool,          # True ise fsrs paketi yok
                "stability": float | None, # degraded'da None -- uydurma deger yok
                "difficulty": float | None,# degraded'da None
                "due_date": datetime,
                "scheduled_days": int | None,
                "state": str,
                "reps": int,               # her zaman int, asla None
                "lapses": int,
            }

        NOT (sozlesme): `degraded=True` iken `stability` ve `difficulty` None
        doner. Cagiran bu alanlari DB'ye YAZMAMALIDIR -- yoksa psikometrik
        olmayan sabitler gercek olcum gibi saklanir.
        """
        if not _FSRS_AVAILABLE or SCHEDULER is None:
            # BOZUK MOD -- fsrs paketi yok. Gercek stability/difficulty
            # hesaplanamaz. Burada UYDURMA psikometrik deger URETMIYORUZ:
            # cagirana "degraded" bayragi ile bildiriyoruz, o da bu alanlari
            # DB'ye yazmiyor (bkz. services/bkt_service.py).
            #
            # Neden bu kadar sert: 20-21 Agu 2026'da bu dal sessizce calisti ve
            # fsrs_cards tablosuna 107 satirin 106'sini stability=2.3,
            # difficulty=5.0, scheduled_days=0, state='review' olarak yazdi --
            # yani tekrar araligi hic buyumedi, reps=40 olan kart bile hep
            # "bugun tekrar et" durumunda kaldi. Aralik tablosu (days) o zaman
            # hesaplaniyor ama KULLANILMIYORDU; due_date her seferinde bugune
            # sabitleniyordu. Asagida hem aralik kullaniliyor hem de her cagri
            # loglaniyor.
            days = {1: 1, 2: 3, 3: 7, 4: 14}.get(rating_int, 7)
            logger.error(
                "FSRS BOZUK MOD: fsrs paketi yok, aralik kaba tabloyla "
                "hesaplandi (rating=%s -> %s gun). Psikometrik alanlar "
                "yazilmayacak. Duzeltme: pip install fsrs==6.3.1",
                rating_int,
                days,
            )
            return {
                "degraded": True,
                "stability": None,
                "difficulty": None,
                "due_date": datetime.now(UTC).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                + timedelta(days=days),
                "scheduled_days": days,
                "state": "review",
                "reps": (reps or 0) + 1,
                "lapses": 0,
            }

        rating = _RATING_MAP.get(rating_int, Rating.Good)
        card = Card()

        # Mevcut kart durumunu restore et
        if stability is not None and stability > 0:
            card.stability = stability
        if difficulty is not None and difficulty > 0:
            card.difficulty = difficulty
        if due_date is not None:
            card.due = due_date
        # step: learning adımı (0=yeni kart, 1=ilk adım tamamlandı, sonrası Review'a geçer)
        # reps DB kolonunu step proxy olarak kullan — 2+ reps = Review state'e geçmiş kart
        # `reps or 0`: cagiran DB'den None okuyabilir; min(None, 1) TypeError verir.
        card.step = min(reps or 0, 1)

        tekrar_ani = datetime.now(UTC)
        card, _ = SCHEDULER.review_card(card, rating)

        # card.step kart Review durumuna gectiginde None olur. Bunu "reps" diye
        # dondurmek tekrar sayacini kaybediyor ve degeri geri besleyen her
        # cagiriciyi bir sonraki turda TypeError ile dusuruyordu. reps artik
        # gercek bir sayac: girdi + 1.
        yeni_reps = (reps or 0) + 1

        # scheduled_days: tekrar aninden yeni bitis tarihine kadar olan aralik.
        # Anchor olarak eski due_date DEGIL tekrar ani kullanilir -- gecikmis
        # bir kartta eski due gecmiste kalir ve arayi sisirirdi.
        planlanan_gun = None
        if card.due is not None:
            planlanan_gun = max(0, (card.due - tekrar_ani).days)

        return {
            "degraded": False,
            "stability": card.stability,
            "difficulty": card.difficulty,
            "due_date": card.due,
            "scheduled_days": planlanan_gun,
            "state": card.state.name.lower(),
            "reps": yeni_reps,
            "lapses": 0,  # fsrs kütüphanesi lapses takip etmiyor
        }

    @staticmethod
    def retrievability(stability: float, days_elapsed: float) -> float:
        """
        Hatirlanabilirlik hesapla: R = (1 + days/S/9)^(-1)

        Args:
            stability: Kart stabilitesi (gun cinsinden)
            days_elapsed: Gecen gun sayisi

        Returns:
            Hatirlanabilirlik [0.0, 1.0]
        """
        if stability <= 0:
            return 0.0
        w20 = 0.1542
        factor = 0.9 ** (-1.0 / w20) - 1
        return float((1 + factor * days_elapsed / stability) ** (-w20))

    @staticmethod
    def next_interval(stability: float) -> float:
        """
        Sonraki tekrar araliklarini hesapla (gun).

        Args:
            stability: Kart stabilitesi

        Returns:
            Gun sayisi (minimum 1)
        """
        w20 = 0.1542
        factor = 0.9 ** (-1.0 / w20) - 1
        return float(max(1, stability / factor * (0.9 ** (-1.0 / w20) - 1)))
