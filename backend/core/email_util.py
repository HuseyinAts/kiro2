"""Yeniden kullanılabilir SMTP email gönderim util'i.

kvkk_compliance.py'deki gömülü SMTP mantığının sade, paylaşılan hâli.
Config eksikse exception fırlatmaz — False döner (çağıran akışı bloklamaz).
"""

from __future__ import annotations

import logging
import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _build_message(
    to: str, subject: str, html_body: str, from_addr: str
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def send_email(to: str, subject: str, html_body: str, blocking: bool = False) -> bool:
    """Email gönder. Config yoksa False (uyarı loglar). blocking=True testte senkron."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("EMAIL_FROM") or smtp_username or "noreply@kiro2.edu.tr"

    if not (smtp_server and smtp_username and smtp_password):
        logger.warning("SMTP yapılandırılmamış; %s adresine email atlandı", to)
        return False

    msg = _build_message(to, subject, html_body, from_addr)

    def _send() -> None:
        try:
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            logger.info("email gönderildi: %s", to)
        except Exception as e:
            logger.error("email gönderim hatası (%s): %s", to, e)

    if blocking:
        _send()
    else:
        threading.Thread(target=_send, daemon=True).start()
    return True
