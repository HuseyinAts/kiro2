"""Y2 - register_agent/subscribe SENKRON baglamdan cagrildiginda dogru sonucu dondurmeli.

OLCULEN KUSUR (8 Eyl 2026):
Ikisi de isini BITIRDIKTEN sonra fire-and-forget bir olay yaymak icin
`asyncio.create_task` cagiriyordu. `create_task` CALISAN bir loop ister;
senkron baglamdan cagrildiginda RuntimeError firliyor, fonksiyonun kendi
`except Exception` blogu bunu yutuyor ve fonksiyon **False** donuyordu --
oysa kayit/abonelik zaten yapilmis oluyordu (dict'e yazma create_task'tan
ONCE).

Yani donus degeri yalan soyluyordu: "basarisiz" diyor, is ise olmus.

Bunu nasil bulduk: `test_multi_agent_coordination_latency` uc kosumda
gecti-dustu-gecti. Zamanlama gurultusu sanip bakinca testin SIFIR agent'la
kostugu ortaya cikti; kok neden buydu.

URETIM ETKISI test hatasindan buyuk: donus degerini kontrol eden herhangi
bir cagiran (`if not blackboard.register_agent(...): ...`) basarili bir
kaydi basarisiz sanip iptal eder ya da tekrar dener -- tekrar deneme de
"Agent already registered" ile yine False doner.

DOGRU DESEN ayni dosyada iki fonksiyon yukarida zaten vardi:
`_start_cleanup_task` -> `get_running_loop()` + `except RuntimeError`.
Iki cagri yeri bu desenden atlanmisti.

MUTASYON: `_gorev_baslat`taki `except RuntimeError` dalini kaldir ->
bu dosyadaki testler duser.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIZINI = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, _BACKEND_DIZINI)

os.environ.setdefault("TESTING", "true")

from algorithms.multi_agent_blackboard import (  # noqa: E402
    EventType,
    MultiAgentBlackboard,
)


class _SahteAgent:
    """register_agent weakref.ref() cagirdigi icin gercek bir nesne gerekir."""

    def __init__(self, ad: str) -> None:
        self.ad = ad

    async def on_blackboard_update(
        self, key: str, value: object, source_agent: str, event_type: object
    ) -> None:
        return None


def test_register_agent_senkron_baglamda_true_donmeli() -> None:
    """Calisan loop YOKKEN kayit basarili olmali VE True donmeli.

    Eski hali: kayit yapiliyordu ama fonksiyon False donuyordu.
    """
    bb = MultiAgentBlackboard()
    ajan = _SahteAgent("agent_0")

    sonuc = bb.register_agent("agent_0", ajan)

    assert sonuc is True, (
        "senkron baglamda register_agent False dondu -- olculen kusur buydu: "
        "create_task RuntimeError firlatiyor ve except Exception yutuyor"
    )
    assert "agent_0" in bb.registered_agents, "kayit gercekten yapilmis olmali"


def test_subscribe_senkron_baglamda_true_donmeli() -> None:
    """Ayni kusur subscribe icin de vardi."""
    bb = MultiAgentBlackboard()
    bb.register_agent("agent_0", _SahteAgent("agent_0"))

    sonuc = bb.subscribe(
        agent_name="agent_0",
        event_types=[EventType.DATA_WRITTEN],
        key_patterns=["*"],
    )

    assert sonuc is True, "senkron baglamda subscribe False dondu"
    assert len(bb.subscriptions["agent_0"]) == 1, "abonelik gercekten eklenmis olmali"


def test_calisan_loop_icinde_de_true_donmeli() -> None:
    """Duzeltme loop ICINDEKI davranisi bozmamali (regresyon korumasi)."""

    async def _kur() -> tuple[bool, bool]:
        bb = MultiAgentBlackboard()
        a = bb.register_agent("agent_0", _SahteAgent("agent_0"))
        b = bb.subscribe(
            agent_name="agent_0",
            event_types=[EventType.DATA_WRITTEN],
            key_patterns=["*"],
        )
        # Yayin gorevlerinin bitmesine izin ver, sonra kapan.
        await asyncio.sleep(0)
        return a, b

    kayit, abone = asyncio.run(_kur())
    assert kayit is True
    assert abone is True


def test_gorev_baslat_loop_yokken_false_doner() -> None:
    """Yardimcinin sozlesmesi: loop yoksa False, varsa True.

    Coroutine kapatiliyor; aksi halde "coroutine was never awaited"
    RuntimeWarning'i cikardi.
    """
    bb = MultiAgentBlackboard()

    async def _bos() -> None:
        return None

    assert bb._gorev_baslat(_bos()) is False

    # NOT: iddia coroutine ICINDE. Disariya `bool` dondurup burada test
    # etmek CI mypy'sinde (1.11.2) `no-any-return` veriyordu -- orada
    # `algorithms.*` untyped goruldugu icin donus Any'ye dusuyor. Yerel
    # pre-commit mypy'si bunu gormuyor (bkz. yerel/CI surum farki tuzagi).
    async def _icerde() -> None:
        assert bb._gorev_baslat(_bos()) is True

    asyncio.run(_icerde())


@pytest.mark.parametrize("ad", ["agent_a", "agent_b"])
def test_kayit_sonrasi_ikinci_kayit_false_doner(ad: str) -> None:
    """Gercek False vakasi korunmali: ayni ad iki kez kaydedilemez.

    Duzeltme "her zaman True dondur" degil; yalnizca loop yoklugundan
    kaynaklanan YANLIS False kalkti.
    """
    bb = MultiAgentBlackboard()
    ajan = _SahteAgent(ad)

    assert bb.register_agent(ad, ajan) is True
    assert (
        bb.register_agent(ad, ajan) is False
    ), "ayni agent ikinci kez kaydedilirse hala False donmeli"
