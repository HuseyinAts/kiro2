"""Tekrarlayan kayitli derslerin dedektorleri — saf, IO'suz.

NEDEN: bu uc ders bir oturumda 4 kez tekrar etti (N802 sekizinci kez).
Doktrin (`.claude/rules/verification.md`): "1. kez fix, 2. kez enforcement,
3. kez ASLA olmasin". N802 sekizde.

Dedektorler saf tutuldu ki hook kosmadan da civilenebilsinler ve mutasyona
girebilsinler.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# .../backend/tests/unit/test_hooks/<bu dosya>
#   parents[0]=test_hooks [1]=unit [2]=tests [3]=backend [4]=kiro2
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / ".claude" / "hooks"))

from ders_dedektorleri import (
    duzeltilemeyen_bulgular,
    ters_tirnak_riski,
    tmp_ad_alani_riski,
)

# Ters tirnak kaynak dosyada CIPLAK yazilmaz — kendisi tuzagin ta kendisi.
TT = chr(96)


# ---------------------------------------------------------------- ters tirnak


@pytest.mark.parametrize(
    "komut",
    [
        f'git commit -m "bkz {TT}L-s230-ast{TT}"',
        f"git commit -m 'a' -m \"b {TT}x{TT} c\"",
        f'git commit -am "fix {TT}foo{TT}"',
    ],
)
def test_ters_tirnak_git_commit_m_icinde_yakalanir(komut: str) -> None:
    """d03674d9d: bash ters tirnagi KOMUT olarak calistirdi, mesaj yutuldu."""
    assert ters_tirnak_riski(komut) is not None


@pytest.mark.parametrize(
    "komut",
    [
        "git commit -F mesaj.txt",
        f'echo "{TT}date{TT}"',
        "git add backend/",
        'git commit -m "duz mesaj, ters tirnak yok"',
    ],
)
def test_ters_tirnak_yanlis_pozitif_uretmez(komut: str) -> None:
    """-F guvenli yol; git disi komutlar bu dedektorun isi DEGIL.

    `echo` satiri bilerek listede: dedektor YALNIZ `git commit -m`e bakar,
    genel bir ters-tirnak polisi degildir. Genel olsaydi her kabuk komutunda
    oterdi ve UYARI KORLUGU yaratirdi — susturulan kontrol olu kontroldur.
    """
    assert ters_tirnak_riski(komut) is None


@pytest.mark.parametrize(
    "komut",
    [
        # heredoc/python icinde VERI olarak gecen metin — komut DEGIL
        f"python - <<'PY'\nd = \"git commit -m ile {TT}x{TT} yazma\"\nPY",
        f"echo 'kural: git commit -m yerine -F kullan, {TT}y{TT}'",
        f"grep -n 'git commit -m' dosya.md  # {TT}z{TT}",
    ],
)
def test_ters_tirnak_veri_olarak_gecen_metni_bloklamaz(komut: str) -> None:
    """S240'ta ILK GERCEK KULLANIMDA isirdi: dedektor kendi commit'imi blokladi.

    Heredoc icinde ders metni olarak 'git commit -m' + ters tirnak geciyordu.
    Dedektor dizeyi KOMUT sandi. `is_git_commit_or_add` zaten dogrusunu yapiyor
    (`startswith`); dedektor o daraltmayi yapmiyordu. Artik yalniz komut
    SEGMENTININ BASINDAKI `git commit` sayilir (bas, `&&`, `;`, `|`, satir sonu).
    """
    assert ters_tirnak_riski(komut) is None


@pytest.mark.parametrize(
    "komut",
    [
        f'cd /repo && git commit -m "x {TT}y{TT}"',
        f'git add . ; git commit -m "x {TT}y{TT}"',
    ],
)
def test_ters_tirnak_zincirlenmis_komutta_yakalanir(komut: str) -> None:
    """Daraltma fazla dar olmamali: `cd X && git commit -m` GERCEK bir commit."""
    assert ters_tirnak_riski(komut) is not None


def test_ters_tirnak_mesaji_cozumu_soyler() -> None:
    """Uyari 'ne yapmali' demezse aliskanliga donusmez."""
    mesaj = ters_tirnak_riski(f'git commit -m "x {TT}y{TT}"')
    assert mesaj is not None
    assert "-F" in mesaj, "cozum (-F ile dosyadan ver) mesajda YOK"


# ---------------------------------------------------------------------- /tmp


@pytest.mark.parametrize(
    "komut",
    [
        "python -c \"open('/tmp/x.txt','w')\"",
        "docker cp /tmp/liste.txt kap:/tmp/liste.txt",
        "cat /tmp/gate.txt",
    ],
)
def test_tmp_ad_alani_yakalanir(komut: str) -> None:
    """bash /tmp = AppData\\Local\\Temp, Python /tmp = C:\\tmp — AYRI."""
    assert tmp_ad_alani_riski(komut) is not None


@pytest.mark.parametrize(
    "komut",
    [
        "pytest backend/tests -q",
        "echo merhaba",
        "docker exec kap python -c \"open('/tmp/x')\"",
    ],
)
def test_tmp_yanlis_pozitif_uretmez(komut: str) -> None:
    """`docker exec` icindeki /tmp KONTEYNER yolu — host ad-alani sorunu yok."""
    assert tmp_ad_alani_riski(komut) is None


# ------------------------------------------------- duzeltilemeyen ruff bulgusu


def test_duzeltilemeyen_bulgu_n802_yakalanir() -> None:
    """ASIL KUSUR: ruff N802'yi GORUYOR ama --fix duzeltemiyor, --quiet yutuyor."""
    cikti = (
        "backend/tests/x.py:12:5: N802 Function name should be lowercase\n"
        "Found 1 error.\n"
    )
    bulgular = duzeltilemeyen_bulgular(cikti)
    assert len(bulgular) == 1
    assert "N802" in bulgular[0]


def test_duzeltilemeyen_bulgu_temiz_ciktida_bos() -> None:
    """Kontrol kolu: temiz cikti 0 bulgu vermeli, yoksa dedektor gurultu uretir."""
    assert duzeltilemeyen_bulgular("All checks passed!\n") == []
    assert duzeltilemeyen_bulgular("") == []


def test_duzeltilemeyen_bulgu_birden_fazla_satiri_korur() -> None:
    """Tek bulgu bildirmek kalanini gizler — sekiz turdur olan tam buydu."""
    cikti = (
        "a.py:1:1: N802 Function name should be lowercase\n"
        "b.py:2:2: S608 Possible SQL injection\n"
        "Found 2 errors.\n"
    )
    assert len(duzeltilemeyen_bulgular(cikti)) == 2


def test_duzeltilemeyen_bulgu_tam_satiri_dondurur() -> None:
    """Yalniz on ek donerse mesaj kural KODUNU tasimaz ve ise yaramaz."""
    cikti = "a.py:1:1: N802 Function name should be lowercase\n"
    assert duzeltilemeyen_bulgular(cikti)[0].endswith("lowercase")


def test_duzeltilemeyen_bulgu_ozet_satirini_saymaz() -> None:
    """'Found N errors.' bir bulgu DEGIL; sayarsa rapor sisirilir."""
    cikti = "Found 2 errors.\n[*] 1 fixable with the `--fix` option.\n"
    assert duzeltilemeyen_bulgular(cikti) == []
