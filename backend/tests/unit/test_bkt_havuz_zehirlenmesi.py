"""bkt_service yurutucu sozlesmesi: surec havuzu YOK, saf hesap thread'de, mock'lar dogrudan.

Tarihce (9 Eyl 2026, rapor madde 17-18): modul yuklenirken kurulan
`ProcessPoolExecutor(max_workers=4)` Linux'ta fork ile dogup o an aktif
`unittest.mock.patch`i cocuga kalici miras birakiyordu -> CI'da rastgele
kirmizi. Olcum havuzun hesabin kendisi kadar pickle+IPC maliyeti ekledigini
gosterdi (review_card: surec-ici 1.65 / thread 1.47 / surec havuzu 2.70 ms;
ilk cagri p95 578 ms). Havuz kaldirildi; `_loop_disinda` thread havuzunu
(`run_in_executor(None, ...)`) kullaniyor.

Uc bekci:
1. Modulde surec havuzu geri gelmesin (import + sembol).
2. Gercek fonksiyon event loop thread'inde DEGIL, baska thread'de kosar
   (loop bloklanmiyor) ve sonucu surec ici sonucla ayni.
3. MagicMock / AsyncMock dogrudan cagrilir (AsyncMock coroutine dondurur;
   thread'e gonderilse await edilemezdi) -- mock'lu test dosyalari bu
   sozlesmeye dayaniyor.
Mutasyon: eski ProcessPoolExecutor satiri geri konunca 1 FAILED; mock dali
silinince 3 FAILED.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import threading
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import services.bkt_service  # tam ad: ruff PLR0402 / mypy attr-defined uzlasisi
from services.fsrs_v6_service import FSRSService


def test_modulde_surec_havuzu_yok() -> None:
    """AST ile: docstring'deki tarihce metni degil, gercek cagri/import aranir."""
    agac = ast.parse(inspect.getsource(services.bkt_service))
    cagrilar = [
        ast.unparse(n.func)
        for n in ast.walk(agac)
        if isinstance(n, ast.Call)
        and ast.unparse(n.func).endswith("ProcessPoolExecutor")
    ]
    assert not cagrilar, f"surec havuzu geri gelmis (madde 17/18): {cagrilar}"
    moduller = {
        alias.name
        for n in ast.walk(agac)
        if isinstance(n, ast.Import | ast.ImportFrom)
        for alias in n.names
    } | {n.module or "" for n in ast.walk(agac) if isinstance(n, ast.ImportFrom)}
    assert "concurrent.futures" not in moduller
    assert not hasattr(services.bkt_service, "_global_process_pool")


def test_gercek_fonksiyon_loop_disinda_thread_de_kosar() -> None:
    gorulen: dict[str, Any] = {}

    def hesap(x: int) -> int:
        gorulen["thread"] = threading.current_thread().name
        return x * 2

    async def _kos() -> int:
        gorulen["loop_thread"] = threading.current_thread().name
        sonuc: int = await services.bkt_service._loop_disinda(hesap, 21)
        return sonuc

    assert asyncio.run(_kos()) == 42
    assert (
        gorulen["thread"] != gorulen["loop_thread"]
    ), "hesap loop thread'inde kostu (bloklama)"

    beklenen = FSRSService.review_card(None, None, None, 3, 0)
    sonuc = asyncio.run(
        services.bkt_service._loop_disinda(
            FSRSService.review_card, None, None, None, 3, 0
        )
    )
    for anahtar in ("stability", "difficulty", "state", "reps", "degraded"):
        assert sonuc.get(anahtar) == beklenen.get(anahtar), anahtar


def test_mocklar_dogrudan_cagrilir() -> None:
    sync_mock = MagicMock(return_value={"stability": -1.0})
    async_mock = AsyncMock(return_value=(0.5, 0.3))

    async def _kos() -> tuple[Any, Any]:
        a = await services.bkt_service._loop_disinda(sync_mock, 1, 2)
        b = await services.bkt_service._loop_disinda(async_mock, [], [])
        return a, b

    a, b = asyncio.run(_kos())
    assert a == {"stability": -1.0}
    assert b == (0.5, 0.3)
    sync_mock.assert_called_once_with(1, 2)
    async_mock.assert_awaited_once_with([], [])
