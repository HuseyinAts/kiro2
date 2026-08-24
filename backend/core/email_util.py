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


def _smtp_kimlik() -> tuple[str | None, str | None, str | None]:
    """Gönderim için gereken ÜÇ değer — bu modüldeki **tek kaynak**.

    F20 (#466): dogrulayicilar `SMTP_HOST`, tuketiciler `SMTP_SERVER` okuyordu.
    Operator dokumante edilen SMTP_HOST'u doldurdugunda startup validator
    GECIYOR ama gonderim burada sessizce False donuyordu — yanlis pozitif
    saglik sinyali. Iki ad da kabul ediliyor; SMTP_HOST tercih edilir cunku
    dogrulayicilarin ve .env sablonunun kullandigi ad odur.

    Kontrolü KOPYALAYAN her yeni çağıran aynı ayrışmayı yeniden üretir; bu
    yüzden `send_email` de `smtp_yapilandirilmis_mi()` de buradan okur.
    """
    return (
        os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER"),
        os.getenv("SMTP_USERNAME"),
        os.getenv("SMTP_PASSWORD"),
    )


def smtp_yapilandirilmis_mi() -> bool:
    """`send_email` gerçekten gönderebilir mi?

    "Gönderebilir" ile "yapılandırılmış görünüyor" AYNI ŞEY OLMALI — aksi halde
    e-posta doğrulama kapısı açılır ama doğrulama postası hiç gitmez
    (bkz. `core/eposta_dogrulama.kapi_engeli`).
    """
    return all(_smtp_kimlik())


def send_email(to: str, subject: str, html_body: str, blocking: bool = False) -> bool:
    """Email gönder. Config yoksa False (uyarı loglar). blocking=True testte senkron."""
    smtp_server, smtp_username, smtp_password = _smtp_kimlik()
    smtp_port = os.getenv("SMTP_PORT", "587")
    from_addr = os.getenv("EMAIL_FROM") or smtp_username or "noreply@kiro2.edu.tr"

    if not smtp_yapilandirilmis_mi():
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
