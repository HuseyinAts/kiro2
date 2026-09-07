"""Konu seed'inin KOK modunu civiler (SOS dilimi onkosulu).

DB'siz: seed'in saf karar parcalari olculur (parent_id secimi, ebeveyn
invaryant sorgusu). Canliya karsi dogrulama ayri adim (PROVA + --kalici).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "quality"))

from y11_konu_seed import ebeveyn_belirle, yanlis_ebeveyn_sorgusu


def test_kok_modu_ebeveyn_aramaz() -> None:
    """--kok: parent_id NULL yazilir, canlida ebeveyn ARANMAZ.

    Kaynakta SOS/SOC0* kodlari ebeveynsiz; canlida da TYT-KIM-01 gibi kokler
    var. Kok yazmak mevcut sekli izler, uydurma hiyerarsi kurmaz.
    """
    assert ebeveyn_belirle(True, "SOS", None) is None
    # Canlida ayni adli bir satir olsa bile kok modu onu ebeveyn YAPMAZ.
    assert ebeveyn_belirle(True, "SOS", "var-olan-id") is None


def test_kok_disi_modda_eksik_ebeveyn_durdurur() -> None:
    """Kok degilse ebeveyn ZORUNLU -- sessizce koke dusmez (FK/agac bozulur)."""
    with pytest.raises(SystemExit) as hata:
        ebeveyn_belirle(False, "YOKKOD", None)
    assert "YOKKOD" in str(hata.value)


def test_kok_disi_modda_bulunan_ebeveyn_kullanilir() -> None:
    assert ebeveyn_belirle(False, "TAR", "tar-id") == "tar-id"


def test_kok_modunda_invaryant_parent_null_arar() -> None:
    """Kok modunda sorgu "parent_id NULL olmali"ya doner.

    GERILEME KORUMASI: eski sorgu (`parent_id IS DISTINCT FROM $1`) ebeveyn
    NULL iken HER satiri yanlis sayardi -- kontrol ters doner, seed hicbir sey
    yazamazdi.
    """
    sorgu, parametreler = yanlis_ebeveyn_sorgusu(None, ["SOS", "SOC0%"])
    assert "parent_id IS NOT NULL" in sorgu
    assert "IS DISTINCT FROM" not in sorgu
    assert parametreler == [["SOS", "SOC0%"]]


def test_normal_modda_invaryant_ebeveyni_karsilastirir() -> None:
    sorgu, parametreler = yanlis_ebeveyn_sorgusu("tar-id", ["TAR%"])
    assert "IS DISTINCT FROM $1" in sorgu
    assert parametreler == ["tar-id", ["TAR%"]]
