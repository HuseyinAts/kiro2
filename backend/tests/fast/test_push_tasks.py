"""
Streak retention push görevi testleri (P0.1 — retention geri-getirme).

Kapsam:
- build_streak_reminder_notifications: saf fonksiyon, at-risk (user_id, streak)
  satırlarını notification dict'lerine çevirir; 10'dan fazla kullanıcıyı
  truncate ETMEZ (eski `users[:10]` bug'ı).
- _send_streak_reminders_impl: enjekte edilen sahte bağlantıyla her at-risk
  kullanıcı için notifications tablosuna INSERT atar.
- celery_app wiring: görev include + beat_schedule'a kayıtlı.
"""

from __future__ import annotations

import logging

from tasks.push_tasks import (
    _send_streak_reminders_impl,
    build_streak_reminder_notifications,
)

# --- Sahte DB bağlantısı (psycopg2/psycopg ortak context-manager protokolü) ---


class _FakeCursor:
    def __init__(self, select_rows):
        self._select_rows = select_rows
        self.executed: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self._select_rows


class _FakeConn:
    def __init__(self, select_rows):
        self.cursor_obj = _FakeCursor(select_rows)

    def cursor(self):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# --- build_streak_reminder_notifications ---


def test_build_one_notification_per_at_risk_user():
    notifs = build_streak_reminder_notifications([("user-1", 7, "org-1")])
    assert len(notifs) == 1
    n = notifs[0]
    assert n["user_id"] == "user-1"
    assert n["notification_type"] == "uyari"
    assert "7" in n["message"]  # streak sayısı mesajda
    assert n["id"]  # boş olmayan id
    assert n["action_url"] == "/dashboard"


def test_build_does_not_truncate_over_ten_users():
    """Eski bug: users[:10] sadece ilk 10'a hatırlatıcı atıyordu."""
    rows = [(f"u{i}", i + 1, "org-1") for i in range(15)]
    notifs = build_streak_reminder_notifications(rows)
    assert len(notifs) == 15
    assert len({n["id"] for n in notifs}) == 15  # her id benzersiz


# --- _send_streak_reminders_impl (DI ile) ---


def test_impl_inserts_one_notification_per_user_no_truncation():
    rows = [(f"u{i}", 5, "org-1") for i in range(15)]
    conn = _FakeConn(rows)
    result = _send_streak_reminders_impl(connect=lambda _url: conn, db_url="x")

    inserts = [
        e for e in conn.cursor_obj.executed if "INSERT INTO notifications" in e[0]
    ]
    assert len(inserts) == 15  # 10 değil 15
    assert result == {"sent": 15, "status": "sent"}


def test_impl_returns_zero_when_no_at_risk_users():
    conn = _FakeConn([])
    result = _send_streak_reminders_impl(connect=lambda _url: conn, db_url="x")
    inserts = [
        e for e in conn.cursor_obj.executed if "INSERT INTO notifications" in e[0]
    ]
    assert len(inserts) == 0
    assert result == {"sent": 0, "status": "sent"}


# --- celery wiring (regression guard) ---


def test_streak_reminders_registered_in_beat_and_include():
    from core.celery_app import celery_app

    beat_tasks = {v["task"] for v in celery_app.conf.beat_schedule.values()}
    assert "tasks.push_tasks.send_streak_reminders" in beat_tasks
    assert "tasks.push_tasks" in celery_app.conf.include


# --- DSN çözümleme + sır sızıntısı (6 Ağu 2026, canlı log'dan ölçüldü) ---
#
# Yukarıdaki testlerin HEPSİ `db_url="x"` + sahte connect enjekte ediyor, yani
# env'den DSN çözümleme yolu hiç koşulmuyordu. Sonuç: görev üretimde 4 gün
# boyunca her koşuda patladı (`sent: 0, status: error`) ve psycopg2'nin hata
# metni DSN'i gömdüğü için `kiro2_app` parolası worker log'una 14 kez düştü.


def test_sqlalchemy_driver_suffix_stripped_before_psycopg(monkeypatch):
    """DATABASE_URL SQLAlchemy formatındaysa psycopg'a (v3) ham libpq DSN gitmeli.

    Container'da DATABASE_URL = postgresql+asyncpg://... psycopg2 DE psycopg
    (v3) DE '+asyncpg' ekini anlamaz, dizeyi key=value sanır ve `invalid dsn`
    atar.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://kiro2_app:gizli@host.docker.internal:5434/kiro2",  # pragma: allowlist secret
    )
    gorulen: dict[str, str] = {}

    def _spy(url):
        gorulen["url"] = url
        return _FakeConn([])

    _send_streak_reminders_impl(connect=_spy)

    assert "+asyncpg" not in gorulen["url"], (
        "psycopg'a SQLAlchemy DSN'i verildi: " + gorulen["url"].replace("gizli", "***")
    )
    assert gorulen["url"].startswith("postgresql://")


def test_default_connect_uses_psycopg_v3_not_psycopg2(monkeypatch):
    """connect=None verildiginde psycopg (v3) kullanilmali, psycopg2 DEGIL.

    docs/guvenlik-borcu.md SS10.44: Celery worker/beat imajlari (Dockerfile.
    minimal) psycopg2'yi ARTIK kurmuyor (3 Eylul 2026, requirements-minimal.
    txt psycopg[binary] v3'e gecti) -- bu satir hala psycopg2 import etseydi
    gorev her aksam ModuleNotFoundError ile sessizce patlardi. psycopg2'yi
    sys.modules'ten kaldirip import edilemez hale getirerek bu regresyonu
    yakalariz: fonksiyon psycopg2'ye HIC dokunmamali.
    """
    import builtins

    real_import = builtins.__import__

    def _no_psycopg2(name, *args, **kwargs):
        if name == "psycopg2":
            raise ModuleNotFoundError("No module named 'psycopg2' (simulated)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_psycopg2)

    # Gercek psycopg (v3) baglanti denemesi yapar (DB yok, baglanti
    # reddedilir) -- onemli olan psycopg2 import HATASI ALMAMAK.
    sonuc = _send_streak_reminders_impl(db_url="postgresql://x:x@127.0.0.1:1/x")

    assert sonuc["status"] == "error"
    assert "psycopg2" not in sonuc["error"]


def test_notification_carries_organization_id():
    """notifications.organization_id VARCHAR NOT NULL (varsayilansiz).

    DSN kusuru duzeltilince ortaya cikti: baglanti kurulamadigi icin INSERT'e
    hic sira gelmiyordu, bu yuzden eksik kolon gorunmuyordu (seri bagli sebep).
    """
    notifs = build_streak_reminder_notifications([("user-1", 7, "org-42")])
    assert notifs[0]["organization_id"] == "org-42"


def test_insert_includes_organization_id():
    """INSERT kiracı kimligini tasimali; yoksa NOT NULL ihlali."""
    conn = _FakeConn([("u1", 5, "org-42")])
    _send_streak_reminders_impl(connect=lambda _url: conn, db_url="x")

    inserts = [
        e for e in conn.cursor_obj.executed if "INSERT INTO notifications" in e[0]
    ]
    assert len(inserts) == 1
    sql, params = inserts[0]
    assert "organization_id" in sql, "INSERT organization_id kolonunu icermiyor"
    assert "org-42" in params, "Kiracı kimligi parametrelerde yok"


def test_connection_error_does_not_leak_password(caplog):
    """libpq surucusunun hata metni DSN'i gömer; parola ne log'a ne sonuca sızmalı.

    Dönen sözlük Celery sonuç backend'ine de yazıldığı için iki ayrı sızıntı
    yüzeyi var — ikisi de assert ediliyor.
    """
    parola = "sup3r-gizli-parola"

    def _patlayan_connect(url):
        raise RuntimeError(
            'invalid dsn: missing "=" after '
            f'"postgresql+asyncpg://kiro2_app:{parola}@host.docker.internal:5434/kiro2"'
            " in connection info string"
        )

    with caplog.at_level(logging.ERROR):
        sonuc = _send_streak_reminders_impl(connect=_patlayan_connect, db_url="x")

    assert sonuc["status"] == "error"
    assert parola not in sonuc["error"], "Parola dönüş değerinde sızdı"
    assert parola not in caplog.text, "Parola log kaydında sızdı"
