"""Sınıf bekçisi: hiçbir uç auth'suz cevap anahtarı vermemeli.

27-28 Tem 2026'da AYNI SINIF iki kez çıktı, iki farklı yüzeyde:

  1. /api/v1/elasticsearch/questions/search  — oturum gerekiyordu ama her
     öğrenci `correct_answer` + `explanation` alıyordu (64.270 dokümanın
     tamamında dolu).
  2. /api/v1/osym-inspired/examples/{subject} — HİÇBİR kimlik doğrulama
     yoktu; anonim istek `correct_answer` döndürüyordu.

İkisi de tek tek kapatıldı ve kendi testleri var. Bu dosya farklı bir iş
yapıyor: bir SONRAKİ uç eklendiğinde aynı hatanın tekrarlanmasını yakalamak.
Tek uç değil, YÜZEY denetleniyor.

KAPSAM: OpenAPI'den okunan tüm GET uçlarından, yolu soru/sınav/arama ile
ilgili olanlar (28 Tem ölçümü: 647 GET'in 121'i). Tamamını taramak ~2 dk
sürüyor ve çoğu health ucu; dar tutmak testi paket içinde koşulabilir
kılıyor.

YÖNTEM: her uca token OLMADAN GET atılır. 200 dönmesi tek başına kusur
değildir (health, public katalog vb. meşru). Kusur, 200 + gövdede cevap
anahtarı alanı.

28 Tem 2026 taban ölçümü (tüm 647 GET, auth'suz):
    401/403 korunuyor : 465
    200 dönüyor       :  89
    hassas alan       :   0   <- youtube/health'teki `api_key_configured`
                                bir BOOLEAN bayrak, anahtar değil (doğrulandı)
"""

from __future__ import annotations

import os
import re

import httpx
import pytest

pytestmark = [pytest.mark.golden_flow, pytest.mark.e2e]

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 15.0

# Yolu bunlardan birini içeren GET uçları denetlenir.
SURFACE_HINTS = (
    "question",
    "soru",
    "exam",
    "sinav",
    "cat",
    "duel",
    "osym",
    "quiz",
    "practice",
    "elasticsearch",
    "search",
)

# Gövdede görülürse kusur. Alan ADI arıyoruz; `api_key_configured` gibi
# bayrakları elemek için tam anahtar biçimi (`"alan":`) şart koşuluyor.
ANSWER_FIELDS = ("correct_answer", "dogru_cevap", "correctAnswer")

PLACEHOLDERS = {
    "subject": "MATEMATIK",
    "subject_id": "MATEMATIK",
    "exam_type": "TYT",
    "topic_id": "00000000-0000-0000-0000-000000000000",
    "question_id": "00000000-0000-0000-0000-000000000000",
    "session_id": "00000000-0000-0000-0000-000000000000",
}


def _fill(path: str) -> str:
    return re.sub(r"\{([^}]+)\}", lambda m: PLACEHOLDERS.get(m.group(1), "1"), path)


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    c = httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT)
    try:
        c.get("/health")
    except Exception as exc:
        c.close()
        pytest.skip(f"backend {BACKEND_URL} ulaşılamıyor: {exc}")
    yield c
    c.close()


@pytest.fixture(scope="module")
def surface_paths(client: httpx.Client) -> list[str]:
    resp = client.get("/openapi.json")
    if resp.status_code != 200:
        pytest.skip(f"openapi.json alınamadı: {resp.status_code}")
    paths = resp.json().get("paths", {})
    hedef = [
        p
        for p, ops in paths.items()
        if "get" in ops and any(k in p.lower() for k in SURFACE_HINTS)
    ]
    if not hedef:
        pytest.skip("soru-servis yüzeyinde GET ucu bulunamadı")
    return sorted(hedef)


def test_no_endpoint_leaks_answer_key_without_auth(
    client: httpx.Client, surface_paths: list[str]
):
    """Auth'suz hiçbir uç gövdesinde cevap anahtarı alanı olmamalı."""
    sizanlar: list[str] = []
    # Ulaşılamayan uçlar güvenlik bulgusu DEĞİL, ama sessizce yutulmamalı:
    # hepsi ulaşılamaz olsaydı test hiçbir şey ölçmeden yeşil olurdu.
    ulasilamaz: list[str] = []
    denetlenen = 0

    for path in surface_paths:
        try:
            resp = client.get(_fill(path))
        except httpx.HTTPError as exc:
            ulasilamaz.append(f"{path}: {type(exc).__name__}")
            continue
        denetlenen += 1
        if resp.status_code != 200:
            continue
        govde = resp.text
        for alan in ANSWER_FIELDS:
            if f'"{alan}"' in govde:
                sizanlar.append(f"{path} -> {alan}")
                break

    # Bekçinin kendisi çalışmıyorsa yeşil dönmesin.
    assert denetlenen >= len(surface_paths) // 2, (
        f"yüzeyin yarısından azı denetlenebildi ({denetlenen}/{len(surface_paths)}) "
        f"— test anlamlı bir şey ölçmüyor. Ulaşılamayanlar: {ulasilamaz[:5]}"
    )

    assert not sizanlar, (
        f"{len(sizanlar)} uç auth'suz cevap anahtarı sızdırıyor "
        f"({denetlenen} uç denetlendi): {sizanlar[:5]}"
    )
