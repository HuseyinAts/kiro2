"""Cevap anahtari dengesi (rapor madde 4a, 9 Eyl 2026).

OLCUM: canli TYT havuzunda C %24 / A %15,7; 3.000 rastgele cekimde en baskin
sikkin payi p50 %25,2, p99 %32,7, denemelerin %3,4'unde >%30. Gercek OSYM
anahtarlari her sikta ~%20. Karar: sik sirasi degismez, secim sonrasi sinav
boyu tavan (ceil(n*0.25)) ve ayni dersten takas.

Sozlesme
--------
1. yeniden_dengele: uzunluk, sira ve ders dagilimi korunur; id'ler tekil;
   aday varken hicbir sik tavani asmaz; aday yoksa secim degismez (yumusak
   tavan); sikki None olan soru tavana sayilmaz ve takas hedefi olabilir.
2. Motor: DENGE_ASGARI_SORU altinda ek sorgu YOK; ustunde anahtar sorgusu
   kurulur, tavani asan sik ayni dersten takasla tavanin altina iner,
   sonuc uzunlugu ve takas edilmeyen konumlar aynen kalir.
"""

# ruff: noqa: S311 -- tohumlu random.Random deterministik test icin, kripto degil
from __future__ import annotations

import copy
import random
from collections import Counter
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.cevap_anahtari_dengesi import (
    TAVAN_ORANI,
    sik_normalize,
    tavan_hesapla,
    yeniden_dengele,
)

# ----------------------------------------------------------------------
# saf fonksiyonlar
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ham", "beklenen"),
    [
        ("c", "C"),
        (" C) ", "C"),
        ("E", "E"),
        ("", None),
        (None, None),
        ("x", None),
        (3, None),
    ],
)
def test_sik_normalize(ham, beklenen) -> None:
    assert sik_normalize(ham) == beklenen


def test_tavan_hesapla_yuzde_25_yukari_yuvarlar() -> None:
    assert TAVAN_ORANI == 0.25
    assert tavan_hesapla(120) == 30
    assert tavan_hesapla(107) == 27
    assert tavan_hesapla(1) == 1
    assert tavan_hesapla(0) == 1


def _secim(
    dagilim: dict[str, int], ders: str = "MAT"
) -> list[tuple[str, str | None, str]]:
    out: list[tuple[str, str | None, str]] = []
    i = 0
    for sik, n in dagilim.items():
        for _ in range(n):
            out.append((f"{ders}-{i}", sik, ders))
            i += 1
    return out


def test_yeniden_dengele_tavani_asan_sikki_ayni_dersten_takaslar() -> None:
    secim = _secim({"C": 12, "A": 4, "B": 4})  # 20 soru, tavan 5
    havuz = [(f"aday-{i}", "DE"[i % 2]) for i in range(30)]
    rng = random.Random(7)

    sonuc = yeniden_dengele(secim, {"MAT": havuz}, tavan_hesapla(20), rng)

    assert len(sonuc) == len(secim)
    assert [d for _, _, d in sonuc] == [d for _, _, d in secim]
    assert len({sid for sid, _, _ in sonuc}) == len(sonuc)
    sayac = Counter(s for _, s, _ in sonuc)
    assert max(sayac.values()) <= 5, dict(sayac)
    # takas edilmeyen konumlar yerinde
    for eski, yeni in zip(secim, sonuc, strict=True):
        if eski[1] != "C":
            assert eski == yeni


def test_yeniden_dengele_aday_yoksa_secime_dokunmaz() -> None:
    secim = _secim({"C": 12, "A": 8})
    sonuc = yeniden_dengele(secim, {}, tavan_hesapla(20), random.Random(1))
    assert sonuc == secim


def test_yeniden_dengele_baska_dersin_havuzunu_kullanmaz() -> None:
    secim = _secim({"C": 12, "A": 8}, ders="MAT")
    havuz_fiz = [(f"fiz-{i}", "A") for i in range(30)]
    sonuc = yeniden_dengele(
        secim, {"FIZ": havuz_fiz}, tavan_hesapla(20), random.Random(1)
    )
    assert sonuc == secim


def test_yeniden_dengele_aday_tavani_asan_sikka_gecmez() -> None:
    """Adaylarin hepsi zaten tavanda olan sikta ise takas yapilmaz."""
    secim = _secim({"C": 12, "A": 5, "B": 3})  # tavan 5, A tam tavanda
    havuz = [(f"aday-{i}", "A") for i in range(30)]
    sonuc = yeniden_dengele(secim, {"MAT": havuz}, tavan_hesapla(20), random.Random(3))
    assert sonuc == secim


def test_yeniden_dengele_sikki_bilinmeyen_aday_kabul_edilir() -> None:
    secim = _secim({"C": 12, "A": 4, "B": 4})  # yalnizca C tavani (5) asar
    havuz = [(f"aday-{i}", None) for i in range(30)]
    sonuc = yeniden_dengele(secim, {"MAT": havuz}, tavan_hesapla(20), random.Random(3))
    sayac = Counter(s for _, s, _ in sonuc if s is not None)
    assert sayac["C"] == 5
    assert sum(1 for _, s, _ in sonuc if s is None) == 7


def test_yeniden_dengele_canli_dagilim_monte_carlo() -> None:
    """Olculen havuz dagilimiyla (KIMYA C %24 / A %14) 200 cekim: tavan hic asilmaz."""
    rng = random.Random(42)
    dagilim = {"A": 14, "B": 19, "C": 24, "D": 20, "E": 22}
    havuz = [
        (f"k-{i}", s)
        for i, s in enumerate(
            random.Random(1).choices(
                list(dagilim), weights=list(dagilim.values()), k=3000
            )
        )
    ]
    for _ in range(200):
        cekim = [(sid, s, "KIMYA") for sid, s in rng.sample(havuz, 120)]
        sonuc = yeniden_dengele(cekim, {"KIMYA": havuz}, tavan_hesapla(120), rng)
        assert len(sonuc) == 120
        assert len({sid for sid, _, _ in sonuc}) == 120
        assert max(Counter(s for _, s, _ in sonuc).values()) <= 30


# ----------------------------------------------------------------------
# motor entegrasyonu (sahte oturum, gercek DB yok)
# ----------------------------------------------------------------------


class _Oturum:
    """execute() cagri sirasina gore sabit satirlar dondurur."""

    def __init__(self, satirlar: list[list]) -> None:
        self._satirlar = satirlar
        self.ifadeler: list = []

    async def execute(self, stmt, params=None):
        i = len(self.ifadeler)
        self.ifadeler.append(stmt)
        rows = self._satirlar[i] if i < len(self._satirlar) else []
        r = MagicMock()
        r.all.return_value = rows
        r.scalars.return_value.all.return_value = rows
        return r


class _Ctx:
    def __init__(self, oturum) -> None:
        self._o = oturum

    async def __aenter__(self):
        return self._o

    async def __aexit__(self, *exc):
        return False


def _motor_ve_konfig(monkeypatch, oturum, count: int):
    import core.osym_exam_engine as eng
    from models.database import ExamType

    monkeypatch.setattr(eng, "get_db_session_context", lambda: _Ctx(oturum))
    motor = eng.OSYMExamEngine()
    cfg = copy.deepcopy(motor.exam_configs[ExamType.TYT])
    cfg.subject_distribution = {"MATEMATIK": count}
    cfg.total_questions = count
    cfg.difficulty = None
    return motor, cfg


def _sql(stmt) -> str:
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


@pytest.mark.asyncio
async def test_motor_esik_altinda_anahtar_sorgusu_kurmaz(monkeypatch) -> None:
    havuz = [(f"m-{i}", False) for i in range(30)]
    sorular = [SimpleNamespace(id=f"q-{i}") for i in range(10)]
    oturum = _Oturum([havuz, sorular])
    motor, cfg = _motor_ve_konfig(monkeypatch, oturum, count=10)

    sonuc = await motor._select_questions(cfg)

    assert [q.id for q in sonuc] == [q.id for q in sorular]
    assert len(oturum.ifadeler) == 2, [_sql(s) for s in oturum.ifadeler]
    assert not any("correct_answer" in _sql(s) for s in oturum.ifadeler)


@pytest.mark.asyncio
async def test_motor_tavani_asan_sikki_takaslar(monkeypatch) -> None:
    """20 soru, 10'u C (tavan 5): anahtar + aday + yeni-entity sorgulari kurulur,
    C tavanin altina iner, uzunluk 20, takas edilmeyen konumlar yerinde."""
    havuz = [(f"m-{i}", False) for i in range(60)]
    sorular = [SimpleNamespace(id=f"q-{i}") for i in range(20)]
    anahtarlar = [(f"q-{i}", "C" if i < 10 else "ABDE"[i % 4]) for i in range(20)]
    adaylar = [(f"m-{i}", "ABDE"[i % 4]) for i in range(60)]
    aday_nesneleri = [SimpleNamespace(id=f"m-{i}") for i in range(60)]
    oturum = _Oturum([havuz, sorular, anahtarlar, adaylar, aday_nesneleri])
    motor, cfg = _motor_ve_konfig(monkeypatch, oturum, count=20)
    random.seed(11)

    sonuc = await motor._select_questions(cfg)

    assert len(oturum.ifadeler) == 5, [_sql(s) for s in oturum.ifadeler]
    assert "correct_answer" in _sql(oturum.ifadeler[2])
    assert "correct_answer" in _sql(oturum.ifadeler[3])
    assert len(sonuc) == 20
    sik = dict(anahtarlar) | dict(adaylar)
    sayac = Counter(sik[q.id] for q in sonuc)
    assert sayac["C"] == 5, dict(sayac)
    assert len({q.id for q in sonuc}) == 20
    for eski, yeni in zip(sorular, sonuc, strict=True):
        if sik[eski.id] != "C":
            assert eski is yeni
