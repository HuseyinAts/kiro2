"""FSRS çalışma oturumu uçları — frontend'in öğrenme yolu akışı.

NEDEN VAR (2 Ağu 2026, yatırımcı demosu hazırlığı)
--------------------------------------------------
`frontend/src/hooks/useLearningPath.ts:395` ve `:412` bu iki ucu çağırıyor:

    POST /api/v1/fsrs/study-sessions/start
    POST /api/v1/fsrs/study-sessions/{id}/end

Canlı ölçümde ilki **500** veriyordu:

    TypeError: 'session_type' is an invalid keyword argument for FSRSStudySession
    (services/_deprecated/fsrs_service.py:549)

KÖK NEDEN — şema uyuşmazlığı, senkron/async DEĞİL
--------------------------------------------------
Deprecated servis **var olmayan alanlara** yazıyor. Gerçek model
(`models/fsrs_models.py:231`) ve canlı tablo `fsrs_study_sessions` şu 9
kolonu taşıyor (ikisi birebir uyumlu, ölçüldü):

    id · student_id · session_date · duration_minutes · cards_reviewed
    correct_reviews · average_response_time · cultural_context · organization_id

Servisin kullandığı `session_type` `session_start` `session_end`
`cards_learned` alanlarının **hiçbiri yok**. Yani bu iki metot bambaşka bir
şemaya göre yazılmış; "async'e port et" yetmezdi, yeniden yazmak gerekiyordu.

Ayrıca aynı modül senkron ORM kullanıyor (`db.query`, `await`sız `commit`)
ama uçlar `AsyncSession` alıyor — ikinci, bağımsız bir kusur.

BU DOSYA NE YAPAR
-----------------
İki ucu **frontend'in kullandığı cookie kimliğiyle** uçtan uca koşar:
başlat → dönen `session_id` ile bitir. Alet doğrulaması: uydurma bir
oturum kimliği 404 vermeli (500 değil).
"""

from __future__ import annotations

import os

import httpx
import pytest

ARKA_UC = os.getenv("BACKEND_URL", "http://localhost:8000")
ZAMAN_ASIMI = 30.0
OGRENCI = {
    "email": "test@kiro2.com",
    "password": "Kiro2Beta2026@x",
}  # pragma: allowlist secret

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope="module")
def istemci() -> httpx.Client:
    c = httpx.Client(base_url=ARKA_UC, timeout=ZAMAN_ASIMI)
    try:
        c.get("/health")
    except Exception as hata:
        c.close()
        pytest.skip(f"backend {ARKA_UC} erisilemiyor: {hata}")

    yanit = c.post("/api/v1/auth/login/secure", json=OGRENCI)
    if yanit.status_code == 429:
        c.close()
        pytest.skip("hiz siniri (429) — olcum gecersiz olurdu")
    if yanit.status_code != 200:
        c.close()
        pytest.skip(f"cookie girisi yok: {yanit.status_code}")
    yield c
    c.close()


def test_calisma_oturumu_baslatilir(istemci: httpx.Client) -> None:
    """ASIL SOZLESME: uc 500 vermemeli ve bir oturum kimligi dondurmeli.

    Fix'ten ONCE KIRMIZI: TypeError -> 500.
    """
    yanit = istemci.post("/api/v1/fsrs/study-sessions/start")

    assert yanit.status_code != 500, (
        f"study-sessions/start COKTU: {yanit.text[:200]}. "
        "Frontend bunu ogrenme yolu ekraninda cagiriyor "
        "(useLearningPath.ts:395)."
    )
    assert yanit.status_code == 200

    govde = yanit.json()
    oturum_id = govde.get("data", {}).get("session_id")
    assert oturum_id, f"session_id donmedi: {govde}"


def test_calisma_oturumu_bitirilir(istemci: httpx.Client) -> None:
    """Baslat -> bitir zinciri uctan uca calismali (useLearningPath.ts:412)."""
    baslat = istemci.post("/api/v1/fsrs/study-sessions/start")
    if baslat.status_code != 200:
        pytest.fail(f"oturum baslatilamadi: {baslat.status_code} {baslat.text[:150]}")

    oturum_id = baslat.json()["data"]["session_id"]
    bitir = istemci.post(f"/api/v1/fsrs/study-sessions/{oturum_id}/end")

    assert bitir.status_code != 500, f"study-sessions/end COKTU: {bitir.text[:200]}"
    assert bitir.status_code == 200

    ozet = bitir.json().get("data", {})
    assert "duration_minutes" in ozet, f"ozet eksik: {ozet}"


def test_alet_dogrulamasi_uydurma_oturum_404(istemci: httpx.Client) -> None:
    """KONTROL KOLU — var olmayan oturum 404 vermeli, 500 DEGIL.

    Bu test yalnizca "500 gormedim" demenin yeterli olmadigini cakiliyor:
    uc her girdiye 200 donuyorsa yukaridaki yesiller anlamsizdir.
    """
    yanit = istemci.post("/api/v1/fsrs/study-sessions/olmayan-oturum-xyz/end")

    assert yanit.status_code == 404, (
        f"Uydurma oturum icin {yanit.status_code} dondu — 404 bekleniyordu. "
        "500 ise hata yolu hala cokuyor; 200 ise uc girdiyi hic dogrulamiyor."
    )
