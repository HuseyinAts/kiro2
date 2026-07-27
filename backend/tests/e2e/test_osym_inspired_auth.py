"""ÖSYM-inspired uçları auth'suz cevap anahtarı veriyordu.

28 Tem 2026 ÖLÇÜMÜ — hiçbir token, hiçbir çerez yok:

    GET /api/v1/osym-inspired/examples/MATEMATIK?count=2
    -> HTTP 200
    -> data[0].correct_answer = 'C'   (+ stem, options, year)

    GET /api/v1/osym-inspired/statistics
    -> HTTP 200, total_osym_questions = 110.858 + ders bazlı kırılım

    GET /api/v1/osym-inspired/style-guide/MATEMATIK
    -> HTTP 200, 50 sorunun analiz edilmiş kök metinleri

Aynı gün kapatılan ES sızıntısından DAHA AĞIR: orada en azından geçerli bir
öğrenci oturumu gerekiyordu, burada hiçbir şey gerekmiyor. İnternete açık bir
kurulumda bu, soru bankasının cevap anahtarının anonim olarak taranabilmesi
demek.

KÖK NEDEN `api/osym_inspired_routes.py`: aynı dosyadaki `/generate` (satır 27)
`Depends(get_current_user)` taşıyor, diğer üç uçta hiç yok. Yani koruma
"unutulmuş", kasıtlı bir tasarım değil. Router `routers/loader.py:76`'da
kayıtlı, yani uçlar canlı.

NEDEN SADECE get_current_user YETMEZ: bu uçlar few-shot prompt üretimi için
var — gerçek ÖSYM sorularını CEVAPLARIYLA döndürüyorlar. Öğrenciye açık bir
oturum bile yeterli olmamalı; içerik-üretim aracı olarak personele (öğretmen/
admin) kapatıldı.

Test, uçları auth'suz çağırır ve 200 DÖNMEMESİNİ şart koşar. Filtre replike
etmez; gerçek HTTP yüzeyini denetler.
"""

from __future__ import annotations

import os

import httpx
import pytest

pytestmark = [pytest.mark.golden_flow, pytest.mark.e2e]

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 30.0

STUDENT = {
    "email": "test@kiro2.com",
    "password": "Kiro2Beta2026@x",  # pragma: allowlist secret
}
TEACHER = {
    "email": "ogretmen@kiro2.com",
    "password": "Kiro2Beta2026@x",  # pragma: allowlist secret
}

# (yol, cevap anahtarı taşıyor mu)
ENDPOINTS = [
    ("/api/v1/osym-inspired/examples/MATEMATIK?count=2", True),
    ("/api/v1/osym-inspired/style-guide/MATEMATIK", False),
    ("/api/v1/osym-inspired/statistics", False),
]

ANSWER_FIELDS = ("correct_answer", "dogru_cevap", "answer")


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
def student_token(client: httpx.Client) -> str:
    resp = client.post("/api/v1/auth/login", json=STUDENT)
    if resp.status_code != 200:
        pytest.skip(f"seed öğrenci girişi başarısız: {resp.status_code}")
    token = resp.json().get("access_token")
    assert token, "login yanıtında access_token yok"
    return token


@pytest.fixture(scope="module")
def teacher_token(client: httpx.Client) -> str:
    resp = client.post("/api/v1/auth/login", json=TEACHER)
    if resp.status_code != 200:
        pytest.skip(f"seed öğretmen girişi başarısız: {resp.status_code}")
    token = resp.json().get("access_token")
    assert token, "login yanıtında access_token yok"
    return token


@pytest.mark.parametrize(("path", "_has_answers"), ENDPOINTS)
def test_osym_inspired_requires_auth(
    client: httpx.Client, path: str, _has_answers: bool
):
    """Auth'suz istek 200 DÖNMEMELİ."""
    resp = client.get(path)
    if resp.status_code == 404:
        pytest.skip(f"{path} yok (router kayıtlı değil?)")

    detay = f"{resp.status_code} {resp.text[:200]}"
    assert resp.status_code != 200, f"{path} auth'suz 200 döndü: {detay}"
    assert resp.status_code in (401, 403), f"{path} beklenmeyen durum: {detay}"


def test_osym_examples_does_not_leak_answers_unauthenticated(client: httpx.Client):
    """Auth'suz çağrıda gövdede cevap anahtarı BULUNMAMALI.

    Ayrı test: durum kodu düzelse bile gövdenin sızdırmadığını ayrıca
    doğrulamak için. 401 dönen bir ucun gövdesinde veri kalmaz, ama bunu
    varsaymak yerine ölçüyoruz.
    """
    resp = client.get(ENDPOINTS[0][0])
    if resp.status_code == 404:
        pytest.skip("uç yok")

    govde = resp.text
    sizanlar = [f for f in ANSWER_FIELDS if f in govde]
    assert not sizanlar, f"auth'suz gövdede cevap alanı: {sizanlar} — {govde[:200]}"


def test_osym_inspired_student_is_not_enough(client: httpx.Client, student_token: str):
    """Öğrenci oturumu da yetmemeli — bu uçlar içerik-üretim aracı.

    Gerçek ÖSYM sorularını cevaplarıyla döndürüyorlar; öğrenci rolüne
    açık olmaları, kapattığımız sızıntının rol-değiştirmiş hâli olurdu.
    """
    resp = client.get(
        ENDPOINTS[0][0], headers={"Authorization": f"Bearer {student_token}"}
    )
    if resp.status_code == 404:
        pytest.skip("uç yok")

    detay = f"{resp.status_code} {resp.text[:200]}"
    assert resp.status_code == 403, f"öğrenci erişebiliyor: {detay}"


def test_osym_examples_still_works_for_staff(client: httpx.Client, teacher_token: str):
    """Öğretmen HÂLÂ erişebilmeli — kapı ayırt etmeli, herkesi bloklamamalı.

    Bu test olmadan yukarıdakiler sahte-yeşil olabilirdi: `require_role`
    bozulup HERKESİ reddetse de "auth'suz 200 dönmüyor" iddiaları geçerdi.
    Kapının çalıştığının kanıtı, doğru rolü GEÇİRMESİ.
    """
    resp = client.get(
        ENDPOINTS[0][0], headers={"Authorization": f"Bearer {teacher_token}"}
    )
    if resp.status_code == 404:
        pytest.skip("uç yok")

    detay = f"{resp.status_code} {resp.text[:200]}"
    assert resp.status_code == 200, f"öğretmen erişemiyor — kapı çok geniş: {detay}"

    data = resp.json().get("data")
    assert isinstance(data, list) and data, f"öğretmene boş sonuç döndü: {detay}"
