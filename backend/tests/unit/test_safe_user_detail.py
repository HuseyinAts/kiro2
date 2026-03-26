"""Tests for _safe_user_detail helper in auth module."""

from api.auth import _GENERIC_ERROR, _safe_user_detail


class TestSafeUserDetail:
    def test_known_safe_pattern_zaten(self):
        e = ValueError("Bu profil zaten mevcut")
        assert _safe_user_detail(e) == "Bu profil zaten mevcut"

    def test_known_safe_pattern_bulunamadi(self):
        e = ValueError("Kullanıcı bulunamadı")
        assert _safe_user_detail(e) == "Kullanıcı bulunamadı"

    def test_known_safe_pattern_gecersiz(self):
        e = ValueError("Geçersiz email formatı")
        assert _safe_user_detail(e) == "Geçersiz email formatı"

    def test_known_safe_pattern_eksik(self):
        e = ValueError("Eksik alan: ad_soyad")
        assert _safe_user_detail(e) == "Eksik alan: ad_soyad"

    def test_unknown_message_returns_generic(self):
        e = ValueError("Connection refused: postgres:5434")
        assert _safe_user_detail(e) == _GENERIC_ERROR

    def test_empty_message_returns_generic(self):
        e = ValueError("")
        assert _safe_user_detail(e) == _GENERIC_ERROR

    def test_internal_traceback_blocked(self):
        e = ValueError("NoneType has no attribute 'id'")
        assert _safe_user_detail(e) == _GENERIC_ERROR

    def test_sql_error_blocked(self):
        e = ValueError("relation 'users' does not exist")
        assert _safe_user_detail(e) == _GENERIC_ERROR
