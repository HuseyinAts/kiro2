"""Unit tests for Teacher Co-Pilot API (2026 Q3-Q4)."""

import os

import pytest

os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient

from api.teacher_copilot_api import _auth_dep, _db_dep
from core.ddos_protection import limiter
from core.dependencies import get_current_user, get_db
from main import create_app

# Disable limiter globally for offline unit tests
limiter.enabled = False
limiter._check_request_limit = lambda *args, **kwargs: None

app = create_app()


class DummyUser:
    id = "teacher-123"
    email = "teacher@kiro2.edu"
    role = "teacher"


@pytest.fixture(autouse=True)
def override_auth_and_db():
    dummy = DummyUser()
    app.dependency_overrides[get_current_user] = lambda: dummy
    app.dependency_overrides[get_db] = lambda: None
    if hasattr(_auth_dep, "dependency"):
        app.dependency_overrides[_auth_dep.dependency] = lambda: dummy
    if hasattr(_db_dep, "dependency"):
        app.dependency_overrides[_db_dep.dependency] = lambda: None

    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False

    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_dashboard_analytics_labels_itself_as_mock():
    """Yanit KENDINI mock olarak beyan etmeli.

    Olculdu (7 Agu 2026): total_students=32 sabit, ZPD dagilimi bu sayinin
    %25/%60/%15'i, FSRS oranlari sabit (84.2 / 48). Gercek veri yok:
    user_item_fsrs=1 satir, student_learning_profiles=2, flags=0.
    Etiketsiz mock, S204'un "3 pano mock" satis blocker listesine gorunmez
    bir 4. kalem ekler. Bu yuzden sozlesme: yanit data_source tasir.
    """
    response = client.get("/api/v1/teacher-copilot/dashboard-analytics?class_id=12-A")
    assert response.status_code == 200
    assert response.json()["data_source"] == "mock"


def test_misconception_alerts_labels_itself_as_mock():
    response = client.get("/api/v1/teacher-copilot/misconception-alerts?class_id=12-A")
    assert response.status_code == 200
    assert response.json()["data_source"] == "mock"


def test_mock_data_has_no_fabricated_student_names():
    """Uydurma ogrenci adi YASAK (Blocker #6 emsali).

    Ogretmen panosunda "Ahmet Y." gibi gercekci adlar, mock veriyi gercek
    sanmaya yol acar. Sentetik oldugu goze carpan etiketler kullanilmali.
    """
    response = client.get("/api/v1/teacher-copilot/misconception-alerts?class_id=12-A")
    govde = response.text
    for uydurma in (
        "Ahmet Y.",
        "Zeynep K.",
        "Mehmet T.",
        "Elif B.",
        "Can D.",
        "Ayşe M.",
    ):
        assert uydurma not in govde, f"Uydurma ogrenci adi sizdi: {uydurma}"


def test_real_impl_flag_raises_instead_of_silently_serving_mock(monkeypatch, tmp_path):
    """Bayrak true iken SESSIZCE mock donmemeli — gercek uygulama YOK.

    Depo emsali: gorev #318-321 (dispatcher + NotImplementedError). Sessiz
    mock, bayragi ceviren operatore "gercek veri akiyor" yalanini soyler.
    """
    from core.mock_endpoint_flags import reset_cache

    bayrak = tmp_path / "flags.json"
    bayrak.write_text('{"teacher_copilot.dashboard_analytics": true}', encoding="utf-8")
    monkeypatch.setenv("MOCK_FLAGS_PATH", str(bayrak))
    reset_cache()
    try:
        response = client.get("/api/v1/teacher-copilot/dashboard-analytics")
        assert (
            response.status_code == 501
        ), "Bayrak true ama gercek uygulama yok — 501 donmeli, sessizce mock DEGIL"
    finally:
        reset_cache()


def test_teacher_copilot_dashboard_analytics():
    response = client.get("/api/v1/teacher-copilot/dashboard-analytics?class_id=12-A")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "zpd_distribution" in data["data"]
    assert "fsrs_retention" in data["data"]
    assert "misconception_alerts" in data["data"]
    assert data["data"]["class_id"] == "12-A"
    assert data["data"]["total_students"] > 0


def test_teacher_copilot_misconception_alerts():
    response = client.get("/api/v1/teacher-copilot/misconception-alerts?class_id=12-A")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["class_id"] == "12-A"
    assert len(data["alerts"]) > 0
    assert "misconception" in data["alerts"][0]
