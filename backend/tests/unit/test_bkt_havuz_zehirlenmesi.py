"""bkt_service surec havuzu: test oturumunda kapali, uretim yolu taze havuzla calisir.

Kok neden (9 Eyl 2026, rapor madde 17; CI job 102485364626):
services/bkt_service.py modul yuklenirken `ProcessPoolExecutor(max_workers=4)`
kurar. Linux'ta cocuk surecler ilk `submit`te FORK ile dogar ve o anda aktif
olan `unittest.mock.patch`i (ornegin batch1b'nin `FSRSService.review_card`
mock'u) kalici olarak miras alir; patch parent'ta geri alinsa da cocukta
kalir. Ayni xdist worker'inda sonra kosan test havuz yoluna girince mock
sonucunu alir -> test_fsrs_card_persistence'ta "stability 1.0 != 2.3065",
"scheduled_days tohum degerinde" (mock sozlugunun degerleri birebir).
Windows'ta (spawn) gorunmez; o yuzden yerelde 8/8, CI'da rastgele kirmizi.

Uc test:
1. tests/conftest.py oturum fixture'i havuzu None yapiyor mu (bekci).
2. Havuz yolu, TAZE (patch'siz) bir havuzla surec ici sonucun aynisini
   veriyor mu -- uretim yolunun kendisi olculuyor, test disi birakilmiyor.
3. Mekanizmanin kaniti (yalnizca fork destekleyen platformda): patch
   aktifken fork edilen cocuk, patch bittikten sonra da mock'u dondurur.
   Bu test kodumuzu degil teshisi civiliyor; kirilirsa teshis bayatlamis
   demektir (ornegin havuz spawn'a gecirilirse bu test SKIP/degisir).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import multiprocessing
import os
from typing import Any
from unittest.mock import patch

import pytest

import services.bkt_service  # ruff PLR0402 / mypy attr-defined uzlasisi: tam ad
from services.fsrs_v6_service import FSRSService


def test_oturumda_havuz_kapali() -> None:
    """tests/conftest.py::bkt_surec_havuzu_kapali aktif mi."""
    assert (
        services.bkt_service._global_process_pool is None
    ), "havuz acik: fork ile dogan cocuklar aktif mock patch'lerini miras alir"


def test_havuz_yolu_taze_havuzla_surec_ici_sonucla_ayni() -> None:
    """Uretim yolu (run_in_executor + FSRSService.review_card) taze havuzda dogru."""
    beklenen = FSRSService.review_card(None, None, None, 3, 0)

    async def _havuzda() -> dict:
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as havuz:
            return await asyncio.get_running_loop().run_in_executor(
                havuz, FSRSService.review_card, None, None, None, 3, 0
            )

    sonuc = asyncio.run(_havuzda())
    for anahtar in ("stability", "difficulty", "state", "reps", "degraded"):
        assert sonuc.get(anahtar) == beklenen.get(anahtar), anahtar


def _cocukta_review_card() -> dict[str, Any]:
    sonuc: dict[str, Any] = FSRSService.review_card(None, None, None, 3, 0)
    return sonuc


@pytest.mark.skipif(
    "fork" not in multiprocessing.get_all_start_methods(),
    reason="fork yok (Windows/macOS spawn): mekanizma bu platformda olusmaz",
)
def test_fork_havuzu_aktif_patchi_kalici_miras_alir_mekanizma() -> None:
    """Teshisin kaniti: patch aktifken fork edilen cocuk, patch bittikten sonra da mock'u dondurur."""
    zehir = {"stability": -1.0, "difficulty": -1.0, "state": "zehir", "reps": 99}
    ctx = multiprocessing.get_context("fork")
    with concurrent.futures.ProcessPoolExecutor(max_workers=1, mp_context=ctx) as havuz:
        with patch.object(FSRSService, "review_card", return_value=zehir):
            # Patch aktifken ilk submit -> cocuk BU anda fork edilir.
            havuz.submit(os.getpid).result()
        # Patch bitti: parent'ta gercek fonksiyon geri geldi...
        assert FSRSService.review_card(None, None, None, 3, 0)["state"] != "zehir"
        # ...ama cocuk hala mock'u tasiyor.
        cocuk = havuz.submit(_cocukta_review_card).result()
    assert (
        cocuk["state"] == "zehir"
    ), "fork cocugu patch'i miras almadi -- teshis bayat, conftest notunu guncelle"
