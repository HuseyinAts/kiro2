"""email_util.send_email unit testleri."""

from core import email_util


def test_send_email_returns_false_when_smtp_unconfigured(monkeypatch):
    monkeypatch.delenv("SMTP_SERVER", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    ok = email_util.send_email("veli@example.com", "Konu", "<p>merhaba</p>")
    assert ok is False  # config yoksa sessizce False, exception yok


def test_send_email_builds_message_with_html(monkeypatch):
    captured = {}

    class _FakeSMTP:
        def __init__(self, server, port):
            captured["server"] = server
            captured["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            captured["starttls"] = True

        def login(self, u, p):
            captured["login"] = (u, p)

        def send_message(self, msg):
            captured["to"] = msg["To"]
            captured["subject"] = msg["Subject"]

    monkeypatch.setenv("SMTP_SERVER", "smtp.test")
    monkeypatch.setenv("SMTP_USERNAME", "user@test")
    monkeypatch.setenv("SMTP_PASSWORD", "pw")
    monkeypatch.setattr(email_util.smtplib, "SMTP", _FakeSMTP)

    ok = email_util.send_email(
        "veli@example.com", "KIRO2 Veli Onayı", "<p>link</p>", blocking=True
    )
    assert ok is True
    assert captured["to"] == "veli@example.com"
    assert captured["subject"] == "KIRO2 Veli Onayı"
    assert captured["starttls"] is True
