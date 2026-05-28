"""KVKK Faz 1 — yaş/reşitlik (veli rızası eşiği) birim testleri.

Karar (2026-05-28): KVKK reşitlik = 18. 18 yaşından küçük kullanıcı için
veli (parental) onayı zorunlu. is_minor 18'in ALTINI True döndürür;
tam 18 olan kişi reşit (False) sayılır.
"""

from datetime import date

import pytest

from core.kvkk_compliance import is_minor


def test_adult_25_year_old_is_not_minor():
    assert is_minor(date(2001, 1, 1), today=date(2026, 5, 28)) is False


def test_15_year_old_is_minor():
    assert is_minor(date(2011, 1, 1), today=date(2026, 5, 28)) is True


def test_17_year_old_is_minor():
    assert is_minor(date(2009, 5, 28), today=date(2026, 5, 28)) is True


def test_exactly_18_today_is_not_minor():
    # 18. doğum günü bugün → reşit sayılır (>= 18 yetişkin)
    assert is_minor(date(2008, 5, 28), today=date(2026, 5, 28)) is False


def test_turns_18_tomorrow_is_still_minor():
    assert is_minor(date(2008, 5, 29), today=date(2026, 5, 28)) is True


def test_leap_day_birthday_boundary():
    # 29 Şubat 2008 doğumlu; 28 Şub 2026'da hâlâ 17 (henüz 18 olmadı)
    assert is_minor(date(2008, 2, 29), today=date(2026, 2, 28)) is True
    # 1 Mart 2026'da 18 olmuş sayılır
    assert is_minor(date(2008, 2, 29), today=date(2026, 3, 1)) is False


def test_today_defaults_to_now_when_omitted():
    # today verilmezse bugünü kullanır; çok eski tarih kesin yetişkin
    assert is_minor(date(1990, 1, 1)) is False


@pytest.mark.parametrize(
    "birth,today,expected",
    [
        (date(2010, 12, 31), date(2026, 5, 28), True),  # 15
        (date(2008, 1, 1), date(2026, 1, 1), False),  # tam 18
        (date(2008, 1, 2), date(2026, 1, 1), True),  # 17, yarın 18
    ],
)
def test_is_minor_parametrized(birth, today, expected):
    assert is_minor(birth, today=today) is expected
