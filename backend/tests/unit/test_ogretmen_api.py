"""
Unit tests for api/ogretmen.py — Teacher Panel API

Covers all 10 endpoints:
  GET  /api/v1/ogretmen/dashboard
  GET  /api/v1/ogretmen/ogrenciler
  GET  /api/v1/ogretmen/ogrenci/{id}/performans
  POST /api/v1/ogretmen/rapor/sinif
  GET  /api/v1/ogretmen/raporlar
  GET  /api/v1/ogretmen/rapor/{id}
  POST /api/v1/ogretmen/bildirim
  GET  /api/v1/ogretmen/bildirimler
  PUT  /api/v1/ogretmen/bildirim/{id}/okundu
  GET  /api/v1/ogretmen/istatistikler

Strategy:
- Isolate via FastAPI dependency_overrides
- Mock ogretmen_servisi at the module level
- Test auth enforcement (student/veli → 403)
- No real DB or network calls
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_teacher(kullanici_id: str = "teacher-001"):
    """Return a Kullanici Pydantic model with OGRETMEN role."""
    from models import Kullanici, KullaniciRolu

    return Kullanici(
        id=kullanici_id,
        email="ogretmen@test.com",
        ad_soyad="Test Öğretmen",
        aktif=True,
        rol=KullaniciRolu.OGRETMEN,
    )


def _make_student(kullanici_id: str = "ogrenci-001"):
    """Return a Kullanici Pydantic model with OGRENCI role."""
    from models import Kullanici, KullaniciRolu

    return Kullanici(
        id=kullanici_id,
        email="ogrenci@test.com",
        ad_soyad="Test Öğrenci",
        aktif=True,
        rol=KullaniciRolu.OGRENCI,
    )


def _make_app(mock_kullanici):
    """Create an isolated FastAPI test app with the ogretmen router."""
    from api.auth import mevcut_kullanici_getir
    from api.ogretmen import router

    app = FastAPI()

    async def _override_auth():
        return mock_kullanici

    app.dependency_overrides[mevcut_kullanici_getir] = _override_auth
    app.include_router(router)
    return app


_SAMPLE_DASHBOARD = {
    "ogretmen_profili": {"ogretmen_id": "t1", "ad_soyad": "Test Öğretmen"},
    "genel_istatistikler": {
        "toplam_ogrenci": 5,
        "aktif_sinavlar": 0,
        "ortalama_basari": 42.5,
        "son_guncelleme": datetime.now(),
    },
    "ogrenci_listesi": [
        {"ogrenci_id": "s1", "aktif": True, "ad_soyad": "Ali Veli"},
    ],
    "son_bildirimler": [],
}

_SAMPLE_OGRENCILER = [
    {
        "ogrenci_id": "s1",
        "ad_soyad": "Ali Veli",
        "email": "ali@test.com",
        "sinif_seviyesi": 11,
        "okul_adi": "Test Lisesi",
        "hedef_sinav": "TYT",
        "son_giris": None,
        "performans": {
            "ortalama_net": 35.0,
            "toplam_sinav": 3,
            "gelisim_trendi": "sabit",
        },
        "aktif": True,
    },
    {
        "ogrenci_id": "s2",
        "ad_soyad": "Zeynep Kaya",
        "email": "zeynep@test.com",
        "sinif_seviyesi": 12,
        "okul_adi": "Test Lisesi",
        "hedef_sinav": "AYT",
        "son_giris": None,
        "performans": {
            "ortalama_net": 55.2,
            "toplam_sinav": 7,
            "gelisim_trendi": "artan",
        },
        "aktif": True,
    },
]

_SAMPLE_PERFORMANS = {
    "ogrenci_bilgileri": {
        "ad_soyad": "Ali Veli",
        "email": "ali@test.com",
        "sinif_seviyesi": 11,
        "hedef_sinav": "TYT",
        "hedef_universiteler": [],
    },
    "genel_istatistikler": {
        "toplam_sinav": 3,
        "ortalama_net": 35.0,
        "en_yuksek_net": 40.0,
        "gelisim_trendi": "sabit",
    },
    "sinav_gecmisi": [],
    "net_trendi": [],
    "konu_performanslari": {"Matematik": 65.0},
    "zayif_konular": [],
    "guclu_konular": ["Matematik"],
    "oneriler": ["Güçlü konularda pekiştirme soruları çözülebilir"],
}

_SAMPLE_RAPOR = {
    "rapor_id": "rapor-uuid-1",
    "ogretmen_id": "teacher-001",
    "olusturma_tarihi": datetime.now(),
    "sinif_istatistikleri": {"toplam_ogrenci": 2, "aktif_ogrenci": 2},
    "konu_performanslari": {},
    "oneriler": ["Düzenli sınav takibi"],
}


# ---------------------------------------------------------------------------
# Auth Enforcement Tests
# ---------------------------------------------------------------------------


class TestAuthEnforcement:
    """Non-teacher users must receive 403 on every endpoint."""

    def setup_method(self):
        student = _make_student()
        self.client = TestClient(_make_app(student), raise_server_exceptions=False)

    def test_dashboard_student_gets_403(self):
        resp = self.client.get("/api/v1/ogretmen/dashboard")
        assert resp.status_code == 403

    def test_ogrenciler_student_gets_403(self):
        resp = self.client.get("/api/v1/ogretmen/ogrenciler")
        assert resp.status_code == 403

    def test_ogrenci_performans_student_gets_403(self):
        resp = self.client.get("/api/v1/ogretmen/ogrenci/s1/performans")
        assert resp.status_code == 403

    def test_sinif_raporu_student_gets_403(self):
        resp = self.client.post("/api/v1/ogretmen/rapor/sinif", json={})
        assert resp.status_code == 403

    def test_raporlar_student_gets_403(self):
        resp = self.client.get("/api/v1/ogretmen/raporlar")
        assert resp.status_code == 403

    def test_rapor_detay_student_gets_403(self):
        resp = self.client.get("/api/v1/ogretmen/rapor/r1")
        assert resp.status_code == 403

    def test_bildirim_gonder_student_gets_403(self):
        resp = self.client.post(
            "/api/v1/ogretmen/bildirim",
            json={"baslik": "Test", "mesaj": "Mesaj"},
        )
        assert resp.status_code == 403

    def test_bildirimler_student_gets_403(self):
        resp = self.client.get("/api/v1/ogretmen/bildirimler")
        assert resp.status_code == 403

    def test_bildirim_okundu_student_gets_403(self):
        resp = self.client.put("/api/v1/ogretmen/bildirim/b1/okundu")
        assert resp.status_code == 403

    def test_istatistikler_student_gets_403(self):
        resp = self.client.get("/api/v1/ogretmen/istatistikler")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Dashboard Tests
# ---------------------------------------------------------------------------


class TestDashboard:
    """Tests for GET /dashboard."""

    def setup_method(self):
        teacher = _make_teacher()
        self.app = _make_app(teacher)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_dashboard_success_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            return_value=_SAMPLE_DASHBOARD,
        ):
            resp = self.client.get("/api/v1/ogretmen/dashboard")
        assert resp.status_code == 200

    def test_dashboard_success_response_structure(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            return_value=_SAMPLE_DASHBOARD,
        ):
            resp = self.client.get("/api/v1/ogretmen/dashboard")
        body = resp.json()
        assert body["success"] is True
        assert "data" in body
        assert "message" in body

    def test_dashboard_service_raises_value_error_returns_400(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            side_effect=ValueError("test error"),
        ):
            resp = self.client.get("/api/v1/ogretmen/dashboard")
        assert resp.status_code == 400

    def test_dashboard_service_raises_generic_exception_returns_500(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            side_effect=RuntimeError("unexpected"),
        ):
            resp = self.client.get("/api/v1/ogretmen/dashboard")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Öğrenci Listesi Tests
# ---------------------------------------------------------------------------


class TestOgrenciListesi:
    """Tests for GET /ogrenciler."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_ogrenciler_success_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_listesi_getir",
            new_callable=AsyncMock,
            return_value=_SAMPLE_OGRENCILER,
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenciler")
        assert resp.status_code == 200

    def test_ogrenciler_response_has_pagination(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_listesi_getir",
            new_callable=AsyncMock,
            return_value=_SAMPLE_OGRENCILER,
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenciler")
        data = resp.json()["data"]
        assert "sayfalama" in data
        sayfalama = data["sayfalama"]
        assert "mevcut_sayfa" in sayfalama
        assert "toplam_ogrenci" in sayfalama

    def test_ogrenciler_pagination_defaults(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_listesi_getir",
            new_callable=AsyncMock,
            return_value=_SAMPLE_OGRENCILER,
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenciler")
        sayfalama = resp.json()["data"]["sayfalama"]
        assert sayfalama["mevcut_sayfa"] == 1
        assert sayfalama["toplam_ogrenci"] == 2

    def test_ogrenciler_custom_page_limit(self):
        large_list = _SAMPLE_OGRENCILER * 5  # 10 students
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_listesi_getir",
            new_callable=AsyncMock,
            return_value=large_list,
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenciler?sayfa=1&limit=3")
        data = resp.json()["data"]
        assert len(data["ogrenciler"]) == 3
        assert data["sayfalama"]["toplam_ogrenci"] == 10

    def test_ogrenciler_empty_list(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_listesi_getir",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenciler")
        data = resp.json()["data"]
        assert data["sayfalama"]["toplam_ogrenci"] == 0
        assert data["ogrenciler"] == []

    def test_ogrenciler_service_error_returns_500(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_listesi_getir",
            new_callable=AsyncMock,
            side_effect=Exception("db error"),
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenciler")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Öğrenci Performans Tests
# ---------------------------------------------------------------------------


class TestOgrenciPerformans:
    """Tests for GET /ogrenci/{id}/performans."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_performans_success_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_detay_performans",
            new_callable=AsyncMock,
            return_value=_SAMPLE_PERFORMANS,
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenci/s1/performans")
        assert resp.status_code == 200

    def test_performans_response_contains_data(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_detay_performans",
            new_callable=AsyncMock,
            return_value=_SAMPLE_PERFORMANS,
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenci/s1/performans")
        body = resp.json()
        assert body["success"] is True
        assert "data" in body

    def test_performans_value_error_returns_400(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_detay_performans",
            new_callable=AsyncMock,
            side_effect=ValueError("erişim yok"),
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenci/s1/performans")
        assert resp.status_code == 400

    def test_performans_generic_error_returns_500(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_detay_performans",
            new_callable=AsyncMock,
            side_effect=RuntimeError("crash"),
        ):
            resp = self.client.get("/api/v1/ogretmen/ogrenci/s1/performans")
        assert resp.status_code == 500

    def test_performans_passes_correct_ids(self):
        mock_service = AsyncMock(return_value=_SAMPLE_PERFORMANS)
        with patch(
            "api.ogretmen.ogretmen_servisi.ogrenci_detay_performans",
            mock_service,
        ):
            self.client.get("/api/v1/ogretmen/ogrenci/target-student/performans")
        call_args = mock_service.call_args
        assert call_args[0][0] == "teacher-001"  # ogretmen_id
        assert call_args[0][1] == "target-student"  # ogrenci_id


# ---------------------------------------------------------------------------
# Sınıf Raporu Tests
# ---------------------------------------------------------------------------


class TestSinifRaporu:
    """Tests for POST /rapor/sinif."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_rapor_olustur_success_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.sinif_raporu_olustur",
            new_callable=AsyncMock,
            return_value=_SAMPLE_RAPOR,
        ):
            resp = self.client.post("/api/v1/ogretmen/rapor/sinif", json={})
        assert resp.status_code == 200

    def test_rapor_olustur_response_structure(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.sinif_raporu_olustur",
            new_callable=AsyncMock,
            return_value=_SAMPLE_RAPOR,
        ):
            resp = self.client.post("/api/v1/ogretmen/rapor/sinif", json={})
        body = resp.json()
        assert body["success"] is True
        assert "data" in body
        assert body["message"] == "Sınıf raporu başarıyla oluşturuldu"

    def test_rapor_olustur_with_date_params(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.sinif_raporu_olustur",
            new_callable=AsyncMock,
            return_value=_SAMPLE_RAPOR,
        ) as mock_svc:
            payload = {
                "baslangic_tarihi": "2026-01-01T00:00:00",
                "bitis_tarihi": "2026-02-01T00:00:00",
                "sinav_tipi": "TYT",
            }
            resp = self.client.post("/api/v1/ogretmen/rapor/sinif", json=payload)
        assert resp.status_code == 200
        mock_svc.assert_called_once()

    def test_rapor_olustur_error_returns_500(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.sinif_raporu_olustur",
            new_callable=AsyncMock,
            side_effect=Exception("failed"),
        ):
            resp = self.client.post("/api/v1/ogretmen/rapor/sinif", json={})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Rapor Listesi Tests
# ---------------------------------------------------------------------------


class TestRaporListesi:
    """Tests for GET /raporlar."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_raporlar_empty_returns_200(self):
        from api.ogretmen import ogretmen_servisi

        original = ogretmen_servisi.sinif_raporlari
        ogretmen_servisi.sinif_raporlari = {}
        try:
            resp = self.client.get("/api/v1/ogretmen/raporlar")
        finally:
            ogretmen_servisi.sinif_raporlari = original
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["toplam_rapor"] == 0

    def test_raporlar_only_returns_own_reports(self):
        """Teacher can only see their own reports."""
        from api.ogretmen import ogretmen_servisi

        now = datetime.now()
        original = ogretmen_servisi.sinif_raporlari
        ogretmen_servisi.sinif_raporlari = {
            "r1": {
                "rapor_id": "r1",
                "ogretmen_id": "teacher-001",  # matches mock teacher
                "olusturma_tarihi": now,
            },
            "r2": {
                "rapor_id": "r2",
                "ogretmen_id": "other-teacher",  # different teacher
                "olusturma_tarihi": now,
            },
        }
        try:
            resp = self.client.get("/api/v1/ogretmen/raporlar")
        finally:
            ogretmen_servisi.sinif_raporlari = original

        data = resp.json()["data"]
        assert data["toplam_rapor"] == 1
        assert data["raporlar"][0]["rapor_id"] == "r1"

    def test_raporlar_limit_query_param(self):
        """Limit parameter restricts returned report count."""
        from api.ogretmen import ogretmen_servisi

        now = datetime.now()
        original = ogretmen_servisi.sinif_raporlari
        ogretmen_servisi.sinif_raporlari = {
            f"r{i}": {
                "rapor_id": f"r{i}",
                "ogretmen_id": "teacher-001",
                "olusturma_tarihi": now,
            }
            for i in range(5)
        }
        try:
            resp = self.client.get("/api/v1/ogretmen/raporlar?limit=2")
        finally:
            ogretmen_servisi.sinif_raporlari = original

        data = resp.json()["data"]
        assert len(data["raporlar"]) == 2
        assert data["toplam_rapor"] == 5  # total count is unaffected by limit


# ---------------------------------------------------------------------------
# Rapor Detay Tests
# ---------------------------------------------------------------------------


class TestRaporDetay:
    """Tests for GET /rapor/{id}."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_rapor_detay_returns_200_for_own_report(self):
        from api.ogretmen import ogretmen_servisi

        now = datetime.now()
        original = ogretmen_servisi.sinif_raporlari
        ogretmen_servisi.sinif_raporlari = {
            "r1": {
                "rapor_id": "r1",
                "ogretmen_id": "teacher-001",
                "olusturma_tarihi": now,
            }
        }
        try:
            resp = self.client.get("/api/v1/ogretmen/rapor/r1")
        finally:
            ogretmen_servisi.sinif_raporlari = original
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_rapor_detay_returns_404_for_missing_report(self):
        from api.ogretmen import ogretmen_servisi

        original = ogretmen_servisi.sinif_raporlari
        ogretmen_servisi.sinif_raporlari = {}
        try:
            resp = self.client.get("/api/v1/ogretmen/rapor/nonexistent")
        finally:
            ogretmen_servisi.sinif_raporlari = original
        assert resp.status_code == 404

    def test_rapor_detay_returns_403_for_other_teachers_report(self):
        from api.ogretmen import ogretmen_servisi

        now = datetime.now()
        original = ogretmen_servisi.sinif_raporlari
        ogretmen_servisi.sinif_raporlari = {
            "r-other": {
                "rapor_id": "r-other",
                "ogretmen_id": "another-teacher",  # different owner
                "olusturma_tarihi": now,
            }
        }
        try:
            resp = self.client.get("/api/v1/ogretmen/rapor/r-other")
        finally:
            ogretmen_servisi.sinif_raporlari = original
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Bildirim Tests
# ---------------------------------------------------------------------------


class TestBildirimGonder:
    """Tests for POST /bildirim."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_bildirim_gonder_success_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.bildirim_gonder",
            new_callable=AsyncMock,
            return_value=True,
        ):
            resp = self.client.post(
                "/api/v1/ogretmen/bildirim",
                json={"baslik": "Test Başlık", "mesaj": "Test mesaj"},
            )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_bildirim_gonder_service_returns_false_gives_400(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.bildirim_gonder",
            new_callable=AsyncMock,
            return_value=False,
        ):
            resp = self.client.post(
                "/api/v1/ogretmen/bildirim",
                json={"baslik": "Test Başlık", "mesaj": "Test mesaj"},
            )
        assert resp.status_code == 400

    def test_bildirim_gonder_missing_baslik_returns_422(self):
        resp = self.client.post(
            "/api/v1/ogretmen/bildirim",
            json={"mesaj": "Başlık olmadan"},
        )
        assert resp.status_code == 422

    def test_bildirim_gonder_missing_mesaj_returns_422(self):
        resp = self.client.post(
            "/api/v1/ogretmen/bildirim",
            json={"baslik": "Başlık var ama mesaj yok"},
        )
        assert resp.status_code == 422

    def test_bildirim_gonder_with_custom_tip(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.bildirim_gonder",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_svc:
            self.client.post(
                "/api/v1/ogretmen/bildirim",
                json={"baslik": "Uyarı", "mesaj": "Dikkat!", "tip": "uyari"},
            )
        payload_sent = mock_svc.call_args[0][1]
        assert payload_sent["tip"] == "uyari"


class TestBildirimlerGetir:
    """Tests for GET /bildirimler."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_bildirimler_empty_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.bildirimler_getir",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = self.client.get("/api/v1/ogretmen/bildirimler")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["toplam"] == 0
        assert data["okunmamis"] == 0

    def test_bildirimler_counts_unread_correctly(self):
        bildirimler = [
            {"bildirim_id": "b1", "baslik": "A", "okundu": False},
            {"bildirim_id": "b2", "baslik": "B", "okundu": True},
            {"bildirim_id": "b3", "baslik": "C", "okundu": False},
        ]
        with patch(
            "api.ogretmen.ogretmen_servisi.bildirimler_getir",
            new_callable=AsyncMock,
            return_value=bildirimler,
        ):
            resp = self.client.get("/api/v1/ogretmen/bildirimler")
        data = resp.json()["data"]
        assert data["toplam"] == 3
        assert data["okunmamis"] == 2


class TestBildirimOkundu:
    """Tests for PUT /bildirim/{id}/okundu."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_bildirim_okundu_success_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.bildirim_okundu_isaretle",
            new_callable=AsyncMock,
            return_value=True,
        ):
            resp = self.client.put("/api/v1/ogretmen/bildirim/b1/okundu")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_bildirim_okundu_not_found_returns_404(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.bildirim_okundu_isaretle",
            new_callable=AsyncMock,
            return_value=False,
        ):
            resp = self.client.put("/api/v1/ogretmen/bildirim/nonexistent/okundu")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# İstatistikler Tests
# ---------------------------------------------------------------------------


class TestIstatistikler:
    """Tests for GET /istatistikler."""

    def setup_method(self):
        teacher = _make_teacher()
        self.client = TestClient(_make_app(teacher), raise_server_exceptions=False)

    def test_istatistikler_success_returns_200(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            return_value=_SAMPLE_DASHBOARD,
        ):
            resp = self.client.get("/api/v1/ogretmen/istatistikler")
        assert resp.status_code == 200

    def test_istatistikler_response_structure(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            return_value=_SAMPLE_DASHBOARD,
        ):
            resp = self.client.get("/api/v1/ogretmen/istatistikler")
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert "genel_ozet" in data
        assert "donem_bilgisi" in data
        assert "ogrenci_aktivitesi" in data

    def test_istatistikler_gun_sayisi_param(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            return_value=_SAMPLE_DASHBOARD,
        ):
            resp = self.client.get("/api/v1/ogretmen/istatistikler?gun_sayisi=7")
        data = resp.json()["data"]
        assert data["donem_bilgisi"]["gun_sayisi"] == 7

    def test_istatistikler_default_gun_sayisi_is_30(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            return_value=_SAMPLE_DASHBOARD,
        ):
            resp = self.client.get("/api/v1/ogretmen/istatistikler")
        data = resp.json()["data"]
        assert data["donem_bilgisi"]["gun_sayisi"] == 30

    def test_istatistikler_active_student_count(self):
        dashboard = dict(_SAMPLE_DASHBOARD)
        dashboard["ogrenci_listesi"] = [
            {"ogrenci_id": "s1", "aktif": True},
            {"ogrenci_id": "s2", "aktif": False},
            {"ogrenci_id": "s3", "aktif": True},
        ]
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            return_value=dashboard,
        ):
            resp = self.client.get("/api/v1/ogretmen/istatistikler")
        aktivite = resp.json()["data"]["ogrenci_aktivitesi"]
        assert aktivite["aktif_ogrenci"] == 2

    def test_istatistikler_error_returns_500(self):
        with patch(
            "api.ogretmen.ogretmen_servisi.ogretmen_dashboard_verisi",
            new_callable=AsyncMock,
            side_effect=RuntimeError("fail"),
        ):
            resp = self.client.get("/api/v1/ogretmen/istatistikler")
        assert resp.status_code == 500
