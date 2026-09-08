"""
Property-Based Tests - Message Latency (REQ-8.2)

Bu modul, hypothesis kullanarak message bus latency icin
property-based testler icerir.

Property 1: Message Latency Bound - End-to-end latency < 50ms (P95)

Boris Cherny Standards: Minimum 100 iterations per property test
"""

import asyncio
import statistics
import sys
import time
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Buradaki satir `sys.path.insert(0, "c:/Users/husey/kiro2/backend")` idi:
# tek bir gelistiricinin diskindeki mutlak yol, commit edilmis halde.
#
# Once "olu satir" diye SILDIM, sonra OLCTUM ve yanildigimi gordum. Bu bes
# dosya tek surecte kosuldugunda (phase1/phase3 blackboard testleri +
# bu dosya):
#     satir VAR  -> 7 passed, 59 skipped
#     satir YOK  -> 8 error, ModuleNotFoundError: No module named 'core.database'
# Yani ekleme yuk tasiyor; toplama sirasina bagli olarak `core.*` cozumunu
# ayakta tutuyor.
#
# Dolayisiyla davranis KORUNUYOR, yalnizca makine bagimliligi kaldiriliyor:
# yol dosyanin kendi konumundan turetiliyor (tests/property -> tests ->
# backend), boylece her makinede ve CI'da ayni sekilde calisiyor.
# Onemli olan VARLIK degil SIRA: `backend` sys.path'te zaten bulunsa bile
# daha geride oldugunda `core` baska bir yerden cozuluyor. Orijinal satir da
# kosulsuz insert(0, ...) yapiyordu; "zaten varsa ekleme" korumasi denendi ve
# hatayi geri getirdi (olculdu). Bu yuzden kosulsuz one aliniyor.
_BACKEND_DIZINI = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, _BACKEND_DIZINI)

from algorithms.multi_agent_blackboard import (  # noqa: E402
    EventType,
    MultiAgentBlackboard,
    Priority,
)


class _SayanAgent:
    """Bildirim sayan minimal agent.

    `MultiAgentBlackboard.register_agent()` icerde `weakref.ref(instance)`
    cagiriyor; bu yuzden agent'in weakref ALINABILIR gercek bir nesne olmasi
    zorunlu. Testler `None` geciyordu ve kayit sessizce basarisiz oluyordu
    (bkz. test_multi_agent_coordination_latency docstring'indeki olcum).

    `_send_notification` abonede callback yoksa `on_blackboard_update`
    ariyor; teslimi UCTAN UCA olcebilmek icin o metot burada.
    """

    def __init__(self, ad: str) -> None:
        self.ad = ad
        self.alinan: list[tuple[str, str]] = []

    async def on_blackboard_update(
        self, key: str, value: object, source_agent: str, event_type: object
    ) -> None:
        self.alinan.append((key, source_agent))


def _kur_ve_olc(
    ajanlar: list["_SayanAgent"], mesaj_sayisi: int, abone_ol: bool
) -> tuple[MultiAgentBlackboard, list[float]]:
    """Blackboard'u CALISAN loop icinde kurar, ayni loop'ta yazar ve olcer.

    Kurulum neden loop ICINDE: `register_agent` ve `subscribe` senkron
    gorunuyorlar ama isi bitirdikten sonra fire-and-forget bir olay yaymak
    icin `asyncio.create_task` cagiriyorlar. Calisan loop yokken bu
    RuntimeError firlatiyor, fonksiyonlarin kendi `except Exception`i yutuyor
    ve KAYIT/ABONELIK ZATEN YAPILMIS OLMASINA RAGMEN False donuyorlar.

    Yani donus degeri yalan soyluyor. Bu bir URETIM KUSURU ve kendi PR'ini
    hak ediyor (duzeltmesi `algorithms/multi_agent_blackboard.py`de
    `_start_cleanup_task`in zaten kullandigi `get_running_loop()` +
    `except RuntimeError` deseni). Buraya rider olarak binmiyor: o dosyaya
    dokunmak diff tabanli ruff/mypy kapilari yuzunden 18 kalemlik ilgisiz
    bir borcu bu PR'a taser.

    Test tarafinda dogru davranis zaten kurulumu loop icinde yapmak.
    """
    sureler: list[float] = []
    loop = asyncio.new_event_loop()
    try:

        async def _kur() -> MultiAgentBlackboard:
            bb = MultiAgentBlackboard()
            for i, ajan in enumerate(ajanlar):
                assert (
                    bb.register_agent(f"agent_{i}", ajan) is True
                ), f"agent_{i} kaydedilemedi -- eski testi bosaltan kusur buydu"
                if abone_ol:
                    assert (
                        bb.subscribe(
                            agent_name=f"agent_{i}",
                            event_types=[EventType.DATA_WRITTEN],
                            key_patterns=["*"],
                        )
                        is True
                    ), f"agent_{i} abone olamadi"
            return bb

        blackboard = loop.run_until_complete(_kur())

        for i in range(mesaj_sayisi):
            baslangic = time.perf_counter()
            loop.run_until_complete(
                blackboard.write(
                    key=f"coord_key_{i}", value=f"value_{i}", source_agent="agent_0"
                )
            )
            sureler.append((time.perf_counter() - baslangic) * 1000)
    finally:
        loop.close()
    return blackboard, sureler


class TestMessageLatencyProperties:
    """Message latency property-based testleri (REQ-8.2)."""

    def setup_method(self):
        """Test setup."""
        self.blackboard = MultiAgentBlackboard()
        self.latencies: list[float] = []

    @given(
        payload_size=st.integers(min_value=10, max_value=10000),
        priority=st.sampled_from(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
    )
    @settings(max_examples=100)
    def test_single_write_latency_bound(self, payload_size: int, priority: str):
        """
        Property 1: Single write latency < 50ms (REQ-8.2)

        For any single write operation, latency MUST be < 50ms.
        """
        blackboard = MultiAgentBlackboard()

        # Register a test agent
        blackboard.register_agent("test_agent", None)

        # Create payload
        payload = "x" * payload_size

        # Measure latency
        start = time.perf_counter()

        # Sync write (blocking)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                blackboard.write(
                    key=f"test_key_{payload_size}",
                    value=payload,
                    source_agent="test_agent",
                    priority=Priority[priority],
                )
            )
        finally:
            loop.close()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Property: Single write should be fast
        assert elapsed_ms < 50, f"Write latency {elapsed_ms:.2f}ms exceeds 50ms"
        assert result is True, "Write should succeed"

    @given(
        num_messages=st.integers(min_value=10, max_value=100),
        payload_size=st.integers(min_value=100, max_value=1000),
    )
    @settings(max_examples=50)
    def test_batch_write_p95_latency(self, num_messages: int, payload_size: int):
        """
        Property 2: Batch write P95 latency < 50ms (REQ-8.2)

        For any batch of messages, P95 latency MUST be < 50ms.
        """
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("batch_agent", None)

        latencies = []
        payload = "y" * payload_size

        loop = asyncio.new_event_loop()
        try:
            for i in range(num_messages):
                start = time.perf_counter()

                loop.run_until_complete(
                    blackboard.write(
                        key=f"batch_key_{i}",
                        value=payload,
                        source_agent="batch_agent",
                        priority=Priority.MEDIUM,
                    )
                )

                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
        finally:
            loop.close()

        # Calculate P95
        if len(latencies) >= 10:
            p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile

            # Property: P95 < 50ms
            assert p95 < 50, f"P95 latency {p95:.2f}ms exceeds 50ms target"

    @given(read_count=st.integers(min_value=10, max_value=100))
    @settings(max_examples=50)
    def test_read_latency_bound(self, read_count: int):
        """
        Property 3: Read latency < 10ms (REQ-8.2)

        For any read operation, latency MUST be < 10ms.
        """
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("read_agent", None)

        # Setup: Write initial data
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                blackboard.write(
                    key="read_test_key", value="test_value", source_agent="read_agent"
                )
            )

            latencies = []

            for _ in range(read_count):
                start = time.perf_counter()
                blackboard.read("read_test_key", "read_agent")
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

            # Property: All reads should be fast
            max_latency = max(latencies)
            assert max_latency < 20, f"Read latency {max_latency:.2f}ms exceeds 20ms"
        finally:
            loop.close()

    @given(
        agent_count=st.integers(min_value=2, max_value=10),
        message_count=st.integers(min_value=5, max_value=20),
    )
    @settings(max_examples=30)
    def test_multi_agent_coordination_latency(
        self, agent_count: int, message_count: int
    ):
        """Property 4: cok-agent'li koordinasyon GERCEKTEN oluyor mu (REQ-8.2).

        ESKI HALI HICBIR SEY OLCMUYORDU. Iki ayri kusuru vardi:

        1) `register_agent(f"agent_{i}", None)` -- kayit SESSIZCE
           BASARISIZDI. `register_agent` icerde `weakref.ref(instance)`
           cagiriyor ve None'a weakref alinamiyor
           ("cannot create weak reference to 'NoneType' object"), hata
           yutuluyor ve False donuyordu. Ardindan `subscribe` de
           "Agent not registered" ile dusuyordu. Olculdu:

               agent  mesaj | kayitli  abone | beklenen bildirim  gercek
                   2      5 |       0      0 |                 5       0
                   5     20 |       0      0 |                80       0
                  10     20 |       0      0 |               180       0

           Yani "multi-agent coordination" testinde SIFIR agent, SIFIR
           abone ve SIFIR bildirim vardi; olculen sey tek-agent'li duz bir
           yazma donguse idi.

        2) Kapi mutlak duvar saatiydi (`avg < 100ms`). Paylasimli CI
           runner'inda bu olcum degil gurultudur: ayni kodda ust uste
           gecti-dustu-gecti (450af87fd gecti, c34cb604d 121.21ms ile
           dustu, master tekrar gecti). Ustelik gercek maliyet olculdu --
           medyan yazma 0.057-0.088 ms, yani esik gercek degerin ~1000
           katiydi. Boyle bir kapi yalnizca runner takildiginda konusur.

        YENI KAPI iki parcali:

        A) TESLIM (deterministik, asil kapi). Kaynak agent kendi olayini
           almaz (`_should_notify` filtreliyor), diger her abone tam olarak
           `message_count` bildirim alir. 180 denemede sapmasiz olculdu:

               agent  mesaj | teslim                      | dispatch
                   2     20 | [0, 20]                     |       20
                   5     20 | [0, 20, 20, 20, 20]         |       80
                  10      5 | [0, 5, 5, 5, 5, 5, 5, 5, 5, 5] |    45

           Bu, gorev yaratildigini degil mesajin agent'a VARDIGINI olcer
           (`on_blackboard_update` gercekten cagriliyor mu).

        B) FELAKET TABANI (mutlak ama MEDYAN). Yazma medyani 50 ms'nin
           altinda olmali. Bu bir performans hedefi degil, imkansizlik
           siniri: yol saf bellek ici Python ve olculen medyanlar
           0.057-0.151 ms, yani ~330 kat pay var. Ancak yola gercekten
           pahali bir sey sizarsa (ag, disk, kilit) konusur.

           Medyan, ortalama degil: 5-20 orneklik bir dizide tek bir
           zamanlayici takilmasi ortalamayi yikar, medyani yikmaz. Eski
           testi CI'da dusuren de buydu (mean 121.21 ms).

        DENENDI VE REDDEDILDI -- goreli oran kapisi. Aboneli/abonesiz medyan
        yazma suresinin orani makine hizini sadelestirdigi icin cazipti;
        olctum ve kuyrugu tutmadi. Kayit ARTIK GERCEKTEN basarili oldugu
        icin kurulum yayin gorevleri de loop'a giriyor ve ilk yazmalarin
        uzerine biniyor. 30'ar tekrar:

               varyant                | oran medyanlari | GORULEN MAKS
               bosaltmasiz            | 1.50 - 2.47     | 9.08
               bosaltmali (sleep(0))  | 1.51 - 2.45     | 7.36
               tek kosum (hypothesis) |                 | 14.5

           Medyanlar kararli, kuyruk degil. Esigi 20-30'a acmak kapiyi
           hicbir seyi yakalamayan bir sus payina cevirirdi -- bu testin
           en basta duzelttigi kusurun aynisi. O yuzden oran kapisi yok;
           koordinasyonun ortamdan bagimsiz olcusu (A) teslim sayisidir.
        """
        ajanlar = [_SayanAgent(f"agent_{i}") for i in range(agent_count)]
        blackboard, sureler = _kur_ve_olc(ajanlar, message_count, abone_ol=True)

        # --- A) TESLIM ---
        assert (
            ajanlar[0].alinan == []
        ), "kaynak agent kendi olayini almamali (_should_notify filtresi)"
        for ajan in ajanlar[1:]:
            assert len(ajan.alinan) == message_count, (
                f"{ajan.ad} {len(ajan.alinan)} bildirim aldi, "
                f"beklenen {message_count} -- fan-out kaybi"
            )
        assert blackboard.metrics["total_notifications"] == message_count * (
            agent_count - 1
        )
        assert blackboard.metrics["total_writes"] == message_count

        # --- B) FELAKET TABANI ---
        # Bu ORTALAMA degil MEDYAN. Fark kritik: 5-20 orneklik bir dizide tek
        # bir zamanlayici takilmasi ortalamayi yikar, medyani yikmaz -- eski
        # testi CI'da dusuren de tam olarak buydu (mean 121.21ms > 100ms).
        #
        # 50 ms bir performans HEDEFI degil, imkansizlik siniri: bu yol saf
        # bellek ici Python (dict yazma + uuid + notify). Olculen medyanlar
        # 0.057-0.151 ms araliginda, yani ~330 kat pay var. Kapi ancak
        # yola gercekten pahali bir sey (ag cagrisi, disk, kilit) sizarsa
        # konusur.
        medyan_ms = statistics.median(sureler)
        assert medyan_ms < 50, (
            f"yazma medyani {medyan_ms:.3f} ms -- bellek ici bir yol icin "
            "imkansiz. Zamanlama gurultusu degil: medyan gurultuye dayanikli."
        )


class TestMessageLatencyEdgeCases:
    """Edge case testleri for message latency."""

    def test_empty_payload_latency(self):
        """Empty payload should have minimal latency."""
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("empty_agent", None)

        start = time.perf_counter()

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                blackboard.write(key="empty_key", value="", source_agent="empty_agent")
            )
        finally:
            loop.close()

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 20, f"Empty payload latency {elapsed_ms:.2f}ms too high"

    def test_large_payload_latency(self):
        """Large payload (100KB) should still meet latency target."""
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("large_agent", None)

        large_payload = "z" * 100_000  # 100KB

        start = time.perf_counter()

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                blackboard.write(
                    key="large_key", value=large_payload, source_agent="large_agent"
                )
            )
        finally:
            loop.close()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Allow more time for large payloads
        assert (
            elapsed_ms < 100
        ), f"Large payload latency {elapsed_ms:.2f}ms exceeds 100ms"

    def test_concurrent_writes_latency(self):
        """Concurrent writes should not significantly increase latency."""
        blackboard = MultiAgentBlackboard()

        for i in range(5):
            blackboard.register_agent(f"concurrent_agent_{i}", None)

        async def run_concurrent_writes():
            async def concurrent_write(agent_id: int) -> float:
                start = time.perf_counter()
                await blackboard.write(
                    key=f"concurrent_key_{agent_id}",
                    value=f"value_{agent_id}",
                    source_agent=f"concurrent_agent_{agent_id}",
                )
                return (time.perf_counter() - start) * 1000

            tasks = [concurrent_write(i) for i in range(5)]
            return await asyncio.gather(*tasks)

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            latencies = loop.run_until_complete(run_concurrent_writes())
        finally:
            loop.close()

        max_latency = max(latencies)
        assert (
            max_latency < 100
        ), f"Concurrent write latency {max_latency:.2f}ms too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-seed=0"])
