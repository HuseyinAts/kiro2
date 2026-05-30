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

from tasks.push_tasks import (
    _send_streak_reminders_impl,
    build_streak_reminder_notifications,
)

# --- Sahte DB bağlantısı (psycopg2 context-manager protokolü) ---


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
    notifs = build_streak_reminder_notifications([("user-1", 7)])
    assert len(notifs) == 1
    n = notifs[0]
    assert n["user_id"] == "user-1"
    assert n["notification_type"] == "uyari"
    assert "7" in n["message"]  # streak sayısı mesajda
    assert n["id"]  # boş olmayan id
    assert n["action_url"] == "/dashboard"


def test_build_does_not_truncate_over_ten_users():
    """Eski bug: users[:10] sadece ilk 10'a hatırlatıcı atıyordu."""
    rows = [(f"u{i}", i + 1) for i in range(15)]
    notifs = build_streak_reminder_notifications(rows)
    assert len(notifs) == 15
    assert len({n["id"] for n in notifs}) == 15  # her id benzersiz


# --- _send_streak_reminders_impl (DI ile) ---


def test_impl_inserts_one_notification_per_user_no_truncation():
    rows = [(f"u{i}", 5) for i in range(15)]
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
