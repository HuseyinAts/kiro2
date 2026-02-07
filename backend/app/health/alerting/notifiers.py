"""
Alert Notifiers

Bu modul, farklı kanallardan alert bildirimi gönderen
notifier sınıflarını içerir.

Desteklenen kanallar:
- Slack webhook
- Email (SMTP)
- SMS (Twilio)
- Log (fallback)
"""

import asyncio
import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import httpx

from .alert_manager import Alert, AlertSeverity

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """Base notifier sınıfı."""

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """
        Alert bildirimi gönderir.

        Args:
            alert: Alert instance

        Returns:
            True ise başarılı
        """
        pass


@dataclass
class SlackConfig:
    """Slack webhook konfigürasyonu."""
    webhook_url: str
    channel: Optional[str] = None
    username: str = "KIRO2 Health Monitor"
    icon_emoji: str = ":hospital:"


class SlackNotifier(BaseNotifier):
    """
    Slack webhook notifier.

    Slack'e alert bildirimi gönderir.
    """

    SEVERITY_COLORS = {
        AlertSeverity.CRITICAL: "#FF0000",  # Kırmızı
        AlertSeverity.WARNING: "#FFA500",   # Turuncu
        AlertSeverity.INFO: "#36A64F"       # Yeşil
    }

    SEVERITY_EMOJIS = {
        AlertSeverity.CRITICAL: ":rotating_light:",
        AlertSeverity.WARNING: ":warning:",
        AlertSeverity.INFO: ":information_source:"
    }

    def __init__(self, config: SlackConfig):
        """
        SlackNotifier sınıfını başlatır.

        Args:
            config: Slack konfigürasyonu
        """
        self.config = config
        logger.info("SlackNotifier başlatıldı")

    async def send(self, alert: Alert) -> bool:
        """
        Slack'e alert gönderir.

        Args:
            alert: Alert instance

        Returns:
            True ise başarılı
        """
        try:
            payload = self._build_payload(alert)

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.config.webhook_url,
                    json=payload
                )

                if response.status_code == 200:
                    logger.debug(f"Slack alert gönderildi: {alert.id}")
                    return True
                else:
                    logger.error(
                        f"Slack alert gönderilemedi: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Slack notifier hatası: {e}")
            return False

    def _build_payload(self, alert: Alert) -> dict:
        """Slack message payload oluşturur."""
        emoji = self.SEVERITY_EMOJIS.get(alert.severity, ":bell:")
        color = self.SEVERITY_COLORS.get(alert.severity, "#808080")

        # Details string oluştur
        details_text = "\n".join(
            f"• *{k}*: {v}"
            for k, v in alert.details.items()
        ) if alert.details else "No additional details"

        payload = {
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji,
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} {alert.severity.value.upper()} Alert",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Type:*\n{alert.type.value}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Endpoint:*\n`{alert.endpoint}`"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Message:*\n{alert.message}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Details:*\n{details_text}"
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Alert ID: `{alert.id}` | Time: {alert.timestamp.isoformat()}"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        if self.config.channel:
            payload["channel"] = self.config.channel

        return payload


@dataclass
class EmailConfig:
    """Email SMTP konfigürasyonu."""
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    to_emails: List[str]
    use_tls: bool = True


class EmailNotifier(BaseNotifier):
    """
    Email SMTP notifier.

    SMTP üzerinden email alert gönderir.
    """

    def __init__(self, config: EmailConfig):
        """
        EmailNotifier sınıfını başlatır.

        Args:
            config: Email konfigürasyonu
        """
        self.config = config
        logger.info("EmailNotifier başlatıldı")

    async def send(self, alert: Alert) -> bool:
        """
        Email alert gönderir.

        Args:
            alert: Alert instance

        Returns:
            True ise başarılı
        """
        try:
            # Email oluştur
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._build_subject(alert)
            msg["From"] = self.config.from_email
            msg["To"] = ", ".join(self.config.to_emails)

            # HTML body
            html_body = self._build_html_body(alert)
            msg.attach(MIMEText(html_body, "html"))

            # Sync SMTP call in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email, msg)

            logger.debug(f"Email alert gönderildi: {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Email notifier hatası: {e}")
            return False

    def _send_email(self, msg: MIMEMultipart) -> None:
        """Sync email gönderimi."""
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.username, self.config.password)
            server.send_message(msg)

    def _build_subject(self, alert: Alert) -> str:
        """Email subject oluşturur."""
        severity_prefix = {
            AlertSeverity.CRITICAL: "🚨 CRITICAL",
            AlertSeverity.WARNING: "⚠️ WARNING",
            AlertSeverity.INFO: "ℹ️ INFO"
        }
        prefix = severity_prefix.get(alert.severity, "ALERT")
        return f"[KIRO2] {prefix}: {alert.message}"

    def _build_html_body(self, alert: Alert) -> str:
        """HTML email body oluşturur."""
        severity_colors = {
            AlertSeverity.CRITICAL: "#FF0000",
            AlertSeverity.WARNING: "#FFA500",
            AlertSeverity.INFO: "#36A64F"
        }
        color = severity_colors.get(alert.severity, "#808080")

        details_html = "<br>".join(
            f"<strong>{k}:</strong> {v}"
            for k, v in alert.details.items()
        ) if alert.details else "No additional details"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{ border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: #f9f9f9; }}
                .severity {{ color: {color}; font-weight: bold; font-size: 18px; }}
                .details {{ margin-top: 10px; padding: 10px; background: #fff; border: 1px solid #ddd; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h1>KIRO2 Health Alert</h1>
            <div class="alert-box">
                <p class="severity">{alert.severity.value.upper()}: {alert.message}</p>
                <p><strong>Type:</strong> {alert.type.value}</p>
                <p><strong>Endpoint:</strong> <code>{alert.endpoint}</code></p>
                <div class="details">
                    <strong>Details:</strong><br>
                    {details_html}
                </div>
            </div>
            <div class="footer">
                <p>Alert ID: {alert.id}</p>
                <p>Time: {alert.timestamp.isoformat()}</p>
                <p>This is an automated message from KIRO2 Health Monitoring System.</p>
            </div>
        </body>
        </html>
        """


@dataclass
class TwilioConfig:
    """Twilio SMS konfigürasyonu."""
    account_sid: str
    auth_token: str
    from_number: str
    to_numbers: List[str]


class SMSNotifier(BaseNotifier):
    """
    Twilio SMS notifier.

    Kritik alertler için SMS gönderir.
    Sadece CRITICAL severity için kullanılmalıdır.
    """

    def __init__(self, config: TwilioConfig):
        """
        SMSNotifier sınıfını başlatır.

        Args:
            config: Twilio konfigürasyonu
        """
        self.config = config
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.account_sid}/Messages.json"
        logger.info("SMSNotifier başlatıldı")

    async def send(self, alert: Alert) -> bool:
        """
        SMS alert gönderir.

        Not: Sadece CRITICAL alertler için SMS gönderilir.

        Args:
            alert: Alert instance

        Returns:
            True ise başarılı
        """
        # Sadece kritik alertler için SMS gönder
        if alert.severity != AlertSeverity.CRITICAL:
            logger.debug(f"SMS atlandı (non-critical): {alert.id}")
            return True

        message = self._build_message(alert)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                for to_number in self.config.to_numbers:
                    response = await client.post(
                        self.api_url,
                        auth=(self.config.account_sid, self.config.auth_token),
                        data={
                            "From": self.config.from_number,
                            "To": to_number,
                            "Body": message
                        }
                    )

                    if response.status_code not in [200, 201]:
                        logger.error(
                            f"SMS gönderilemedi ({to_number}): {response.status_code}"
                        )

            logger.debug(f"SMS alert gönderildi: {alert.id}")
            return True

        except Exception as e:
            logger.error(f"SMS notifier hatası: {e}")
            return False

    def _build_message(self, alert: Alert) -> str:
        """SMS mesajı oluşturur (160 karakter limiti)."""
        # SMS kısa olmalı
        message = f"KIRO2 CRITICAL: {alert.message[:80]}. Endpoint: {alert.endpoint[:30]}"
        return message[:160]


class LogNotifier(BaseNotifier):
    """
    Log-based notifier (fallback).

    Diğer notifier'lar başarısız olduğunda kullanılır.
    """

    async def send(self, alert: Alert) -> bool:
        """
        Alert'i loglar.

        Args:
            alert: Alert instance

        Returns:
            True (her zaman başarılı)
        """
        log_message = (
            f"[{alert.severity.value.upper()}] {alert.type.value}\n"
            f"Endpoint: {alert.endpoint}\n"
            f"Message: {alert.message}\n"
            f"Details: {alert.details}\n"
            f"ID: {alert.id}"
        )

        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical(log_message)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return True
