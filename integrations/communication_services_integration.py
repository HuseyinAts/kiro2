"""
KIRO2 - Communication Services Integration
==========================================

Bu modül, iletişim hizmetleri ile entegrasyonu sağlar.
SMS, e-posta, push notification ve video konferans sistemleri desteği.

Desteklenen İletişim Servisleri:
- Türkiye SMS Sağlayıcıları (Netgsm, İletimerkezi, Mutlucell)
- E-posta Servisleri (SendGrid, Amazon SES, Mailgun)
- Push Notification (Firebase, OneSignal, Apple Push)
- Video Konferans (Zoom, Microsoft Teams, Google Meet)
- WhatsApp Business API
- Telegram Bot API
- Discord Integration
- Slack Integration

KVKK uyumlu iletişim veri güvenliği ve kullanıcı onay yönetimi.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, quote

import aiohttp
import jwt
from cryptography.hazmat.primitives import serialization
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from .unified_integration_framework import (
    IntegrationFramework,
    IntegrationType,
    AuthenticationMethod,
    IntegrationConfiguration,
    IntegrationCredentials
)


class CommunicationChannel(Enum):
    """İletişim kanalları"""
    SMS = "sms"
    EMAIL = "email"
    PUSH_NOTIFICATION = "push_notification"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    VIDEO_CONFERENCE = "video_conference"
    IN_APP_NOTIFICATION = "in_app_notification"


class MessageType(Enum):
    """Mesaj türleri"""
    WELCOME = "welcome"
    VERIFICATION = "verification"
    REMINDER = "reminder"
    EXAM_NOTIFICATION = "exam_notification"
    RESULT_NOTIFICATION = "result_notification"
    MARKETING = "marketing"
    SYSTEM_ALERT = "system_alert"
    STUDY_REMINDER = "study_reminder"
    ACHIEVEMENT = "achievement"
    SUPPORT = "support"


class MessageStatus(Enum):
    """Mesaj durumları"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    SPAM = "spam"


class MessagePriority(Enum):
    """Mesaj öncelikleri"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class CommunicationPreferences:
    """İletişim tercihleri (KVKK uyumlu)"""
    user_id: str
    sms_enabled: bool = True
    email_enabled: bool = True
    push_enabled: bool = True
    whatsapp_enabled: bool = False
    telegram_enabled: bool = False
    marketing_consent: bool = False
    study_reminders: bool = True
    exam_notifications: bool = True
    result_notifications: bool = True
    consent_date: datetime = field(default_factory=datetime.now)
    
    def has_consent_for(self, message_type: MessageType) -> bool:
        """Mesaj türü için onay kontrolü"""
        if message_type == MessageType.MARKETING:
            return self.marketing_consent
        elif message_type in [MessageType.STUDY_REMINDER]:
            return self.study_reminders
        elif message_type in [MessageType.EXAM_NOTIFICATION]:
            return self.exam_notifications
        elif message_type in [MessageType.RESULT_NOTIFICATION]:
            return self.result_notifications
        else:
            return True  # Sistem mesajları için onay gerekmiyor


@dataclass
class MessageTemplate:
    """Mesaj şablonu"""
    template_id: str
    name: str
    message_type: MessageType
    channel: CommunicationChannel
    subject_template: Optional[str] = None
    body_template: str = ""
    variables: List[str] = field(default_factory=list)
    language: str = "tr"
    
    def render(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Şablonu render et"""
        rendered_subject = self.subject_template
        rendered_body = self.body_template
        
        for var, value in variables.items():
            if rendered_subject:
                rendered_subject = rendered_subject.replace(f"{{{{{var}}}}}", str(value))
            rendered_body = rendered_body.replace(f"{{{{{var}}}}}", str(value))
        
        return {
            "subject": rendered_subject,
            "body": rendered_body
        }


@dataclass
class CommunicationMessage:
    """İletişim mesajı"""
    message_id: str
    recipient: str
    channel: CommunicationChannel
    message_type: MessageType
    priority: MessagePriority
    subject: Optional[str]
    content: str
    template_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"


@dataclass
class CommunicationResponse:
    """İletişim yanıtı"""
    message_id: str
    provider_message_id: str
    status: MessageStatus
    channel: CommunicationChannel
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    cost: Optional[float] = None
    provider_response: Dict[str, Any] = field(default_factory=dict)


class TurkishSMSProvider:
    """Türkiye SMS sağlayıcısı (Netgsm, İletimerkezi vb.)"""
    
    def __init__(self, provider_name: str, username: str, password: str, 
                 api_key: str, base_url: str):
        self.provider_name = provider_name
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = base_url
        
    async def send_sms(self, phone: str, message: str, 
                      sender: str = "KIRO2") -> CommunicationResponse:
        """SMS gönder"""
        # Telefon numarasını Türkiye formatına çevir
        clean_phone = re.sub(r'[^0-9+]', '', phone)
        if clean_phone.startswith('0'):
            clean_phone = '+90' + clean_phone[1:]
        elif not clean_phone.startswith('+90'):
            clean_phone = '+90' + clean_phone
            
        message_id = f"sms_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Netgsm formatı için örnek
        if self.provider_name.lower() == "netgsm":
            data = {
                "usercode": self.username,
                "password": self.password,
                "gsmno": clean_phone,
                "message": message,
                "msgheader": sender
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/sms/send/get",
                        params=data
                    ) as response:
                        result = await response.text()
                        
                        if result.startswith("00"):
                            return CommunicationResponse(
                                message_id=message_id,
                                provider_message_id=result.split()[1] if len(result.split()) > 1 else "",
                                status=MessageStatus.SENT,
                                channel=CommunicationChannel.SMS,
                                sent_at=datetime.now(),
                                provider_response={"raw_response": result}
                            )
                        else:
                            return CommunicationResponse(
                                message_id=message_id,
                                provider_message_id="",
                                status=MessageStatus.FAILED,
                                channel=CommunicationChannel.SMS,
                                sent_at=datetime.now(),
                                error_message=f"SMS failed: {result}",
                                provider_response={"raw_response": result}
                            )
                            
            except Exception as e:
                return CommunicationResponse(
                    message_id=message_id,
                    provider_message_id="",
                    status=MessageStatus.FAILED,
                    channel=CommunicationChannel.SMS,
                    sent_at=datetime.now(),
                    error_message=str(e)
                )


class EmailServiceProvider:
    """E-posta servis sağlayıcısı"""
    
    def __init__(self, provider_name: str, api_key: str, 
                 from_email: str, base_url: str):
        self.provider_name = provider_name
        self.api_key = api_key
        self.from_email = from_email
        self.base_url = base_url
        
    async def send_email(self, to_email: str, subject: str, 
                        html_content: str, text_content: Optional[str] = None) -> CommunicationResponse:
        """E-posta gönder"""
        message_id = f"email_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # SendGrid formatı için örnek
        if self.provider_name.lower() == "sendgrid":
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject
                    }
                ],
                "from": {"email": self.from_email, "name": "KIRO2"},
                "content": [
                    {"type": "text/html", "value": html_content}
                ]
            }
            
            if text_content:
                data["content"].append({"type": "text/plain", "value": text_content})
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/v3/mail/send",
                        json=data,
                        headers=headers
                    ) as response:
                        if response.status == 202:
                            provider_id = response.headers.get("X-Message-Id", "")
                            return CommunicationResponse(
                                message_id=message_id,
                                provider_message_id=provider_id,
                                status=MessageStatus.SENT,
                                channel=CommunicationChannel.EMAIL,
                                sent_at=datetime.now(),
                                provider_response={"status_code": response.status}
                            )
                        else:
                            error_text = await response.text()
                            return CommunicationResponse(
                                message_id=message_id,
                                provider_message_id="",
                                status=MessageStatus.FAILED,
                                channel=CommunicationChannel.EMAIL,
                                sent_at=datetime.now(),
                                error_message=error_text,
                                provider_response={"status_code": response.status}
                            )
                            
            except Exception as e:
                return CommunicationResponse(
                    message_id=message_id,
                    provider_message_id="",
                    status=MessageStatus.FAILED,
                    channel=CommunicationChannel.EMAIL,
                    sent_at=datetime.now(),
                    error_message=str(e)
                )


class PushNotificationProvider:
    """Push notification sağlayıcısı (Firebase)"""
    
    def __init__(self, server_key: str, project_id: str):
        self.server_key = server_key
        self.project_id = project_id
        self.base_url = "https://fcm.googleapis.com"
        
    async def send_push_notification(self, device_token: str, title: str, 
                                   body: str, data: Optional[Dict] = None) -> CommunicationResponse:
        """Push notification gönder"""
        message_id = f"push_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "to": device_token,
            "notification": {
                "title": title,
                "body": body,
                "icon": "https://kiro2.com/icon.png",
                "click_action": "https://kiro2.com/app"
            }
        }
        
        if data:
            payload["data"] = data
            
        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/fcm/send",
                    json=payload,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if result.get("success") == 1:
                        return CommunicationResponse(
                            message_id=message_id,
                            provider_message_id=result.get("multicast_id", ""),
                            status=MessageStatus.SENT,
                            channel=CommunicationChannel.PUSH_NOTIFICATION,
                            sent_at=datetime.now(),
                            provider_response=result
                        )
                    else:
                        return CommunicationResponse(
                            message_id=message_id,
                            provider_message_id="",
                            status=MessageStatus.FAILED,
                            channel=CommunicationChannel.PUSH_NOTIFICATION,
                            sent_at=datetime.now(),
                            error_message=result.get("results", [{}])[0].get("error", "Unknown error"),
                            provider_response=result
                        )
                        
        except Exception as e:
            return CommunicationResponse(
                message_id=message_id,
                provider_message_id="",
                status=MessageStatus.FAILED,
                channel=CommunicationChannel.PUSH_NOTIFICATION,
                sent_at=datetime.now(),
                error_message=str(e)
            )


class WhatsAppBusinessProvider:
    """WhatsApp Business API sağlayıcısı"""
    
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = "https://graph.facebook.com/v18.0"
        
    async def send_whatsapp_message(self, phone: str, message: str, 
                                  template_name: Optional[str] = None) -> CommunicationResponse:
        """WhatsApp mesajı gönder"""
        message_id = f"whatsapp_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Telefon numarasını temizle
        clean_phone = re.sub(r'[^0-9]', '', phone)
        if clean_phone.startswith('0'):
            clean_phone = '90' + clean_phone[1:]
        elif not clean_phone.startswith('90'):
            clean_phone = '90' + clean_phone
            
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {"body": message}
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    json=payload,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if result.get("messages"):
                        return CommunicationResponse(
                            message_id=message_id,
                            provider_message_id=result["messages"][0]["id"],
                            status=MessageStatus.SENT,
                            channel=CommunicationChannel.WHATSAPP,
                            sent_at=datetime.now(),
                            provider_response=result
                        )
                    else:
                        error_msg = result.get("error", {}).get("message", "Unknown error")
                        return CommunicationResponse(
                            message_id=message_id,
                            provider_message_id="",
                            status=MessageStatus.FAILED,
                            channel=CommunicationChannel.WHATSAPP,
                            sent_at=datetime.now(),
                            error_message=error_msg,
                            provider_response=result
                        )
                        
        except Exception as e:
            return CommunicationResponse(
                message_id=message_id,
                provider_message_id="",
                status=MessageStatus.FAILED,
                channel=CommunicationChannel.WHATSAPP,
                sent_at=datetime.now(),
                error_message=str(e)
            )


class TelegramBotProvider:
    """Telegram Bot API sağlayıcısı"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_telegram_message(self, chat_id: str, message: str, 
                                  parse_mode: str = "HTML") -> CommunicationResponse:
        """Telegram mesajı gönder"""
        message_id = f"telegram_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendMessage",
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        return CommunicationResponse(
                            message_id=message_id,
                            provider_message_id=str(result["result"]["message_id"]),
                            status=MessageStatus.SENT,
                            channel=CommunicationChannel.TELEGRAM,
                            sent_at=datetime.now(),
                            provider_response=result
                        )
                    else:
                        return CommunicationResponse(
                            message_id=message_id,
                            provider_message_id="",
                            status=MessageStatus.FAILED,
                            channel=CommunicationChannel.TELEGRAM,
                            sent_at=datetime.now(),
                            error_message=result.get("description", "Unknown error"),
                            provider_response=result
                        )
                        
        except Exception as e:
            return CommunicationResponse(
                message_id=message_id,
                provider_message_id="",
                status=MessageStatus.FAILED,
                channel=CommunicationChannel.TELEGRAM,
                sent_at=datetime.now(),
                error_message=str(e)
            )


class VideoConferenceProvider:
    """Video konferans sağlayıcısı (Zoom)"""
    
    def __init__(self, api_key: str, api_secret: str, account_id: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_id = account_id
        self.base_url = "https://api.zoom.us/v2"
        
    def _generate_jwt_token(self) -> str:
        """JWT token oluştur"""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": self.api_key,
            "exp": int(time.time()) + 3600  # 1 saat geçerli
        }
        return jwt.encode(payload, self.api_secret, algorithm="HS256")
    
    async def create_meeting(self, topic: str, start_time: datetime, 
                           duration_minutes: int, host_email: str) -> Dict[str, Any]:
        """Zoom toplantısı oluştur"""
        token = self._generate_jwt_token()
        
        meeting_data = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration": duration_minutes,
            "timezone": "Europe/Istanbul",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "waiting_room": True,
                "audio": "voip"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/users/{host_email}/meetings",
                    json=meeting_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            "meeting_id": result["id"],
                            "join_url": result["join_url"],
                            "start_url": result["start_url"],
                            "password": result.get("password"),
                            "topic": result["topic"],
                            "start_time": result["start_time"],
                            "duration": result["duration"]
                        }
                    else:
                        error = await response.json()
                        raise Exception(f"Zoom API error: {error}")
                        
        except Exception as e:
            raise Exception(f"Failed to create Zoom meeting: {e}")


class CommunicationTemplateManager:
    """İletişim şablonu yöneticisi"""
    
    def __init__(self):
        self.templates: Dict[str, MessageTemplate] = {}
        self._initialize_default_templates()
        
    def _initialize_default_templates(self):
        """Varsayılan şablonları başlat"""
        # Hoşgeldin mesajı
        self.templates["welcome_sms"] = MessageTemplate(
            template_id="welcome_sms",
            name="Hoşgeldin SMS",
            message_type=MessageType.WELCOME,
            channel=CommunicationChannel.SMS,
            body_template="KIRO2'ye hoşgeldin {{name}}! YKS'de başarıya giden yolculuğun başlıyor. Şimdi giriş yap: {{login_url}}"
        )
        
        self.templates["welcome_email"] = MessageTemplate(
            template_id="welcome_email",
            name="Hoşgeldin E-posta",
            message_type=MessageType.WELCOME,
            channel=CommunicationChannel.EMAIL,
            subject_template="KIRO2'ye Hoşgeldin {{name}}!",
            body_template="""
            <h1>Merhaba {{name}}!</h1>
            <p>KIRO2'ye katıldığın için çok mutluyuz. Türkiye'nin en kapsamlı YKS hazırlık platformunda seni bekleyen:</p>
            <ul>
                <li>50,000+ TYT ve AYT sorusu</li>
                <li>Canlı dersler ve konu anlatımları</li>
                <li>Kişiselleştirilmiş çalışma planı</li>
                <li>Detaylı performans analizi</li>
            </ul>
            <p><a href="{{login_url}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none;">Şimdi Başla</a></p>
            """
        )
        
        # Doğrulama mesajları
        self.templates["verification_sms"] = MessageTemplate(
            template_id="verification_sms",
            name="Doğrulama SMS",
            message_type=MessageType.VERIFICATION,
            channel=CommunicationChannel.SMS,
            body_template="KIRO2 doğrulama kodun: {{code}}. Bu kodu kimse ile paylaşma."
        )
        
        # Sınav hatırlatıcıları
        self.templates["exam_reminder_push"] = MessageTemplate(
            template_id="exam_reminder_push",
            name="Sınav Hatırlatıcı",
            message_type=MessageType.EXAM_NOTIFICATION,
            channel=CommunicationChannel.PUSH_NOTIFICATION,
            subject_template="Sınavın Yarın!",
            body_template="{{exam_name}} sınavın yarın saat {{exam_time}}'da. Hazır mısın? Son tekrar için uygulamayı aç.",
            variables=["exam_name", "exam_time"]
        )
        
        # Başarı bildirimleri
        self.templates["achievement_push"] = MessageTemplate(
            template_id="achievement_push",
            name="Başarı Bildirimi",
            message_type=MessageType.ACHIEVEMENT,
            channel=CommunicationChannel.PUSH_NOTIFICATION,
            subject_template="Tebrikler! [PARTY]",
            body_template="{{achievement_name}} başarısını kazandın! {{description}}",
            variables=["achievement_name", "description"]
        )
        
        # Çalışma hatırlatıcıları
        self.templates["study_reminder_whatsapp"] = MessageTemplate(
            template_id="study_reminder_whatsapp",
            name="Çalışma Hatırlatıcı WhatsApp",
            message_type=MessageType.STUDY_REMINDER,
            channel=CommunicationChannel.WHATSAPP,
            body_template="""[TARGET] KIRO2 Çalışma Zamanı!

Merhaba {{name}}, bugün {{subject}} konularında çalışma zamanın.

[BOOKS] Bugünün hedefleri:
{{study_goals}}

⏰ Önerilen çalışma süresi: {{duration}} dakika

💪 "Başarı, hazırlık ile fırsat buluştuğunda ortaya çıkar."

Şimdi çalışmaya başla: {{app_url}}"""
        )
    
    def get_template(self, template_id: str) -> Optional[MessageTemplate]:
        """Şablon al"""
        return self.templates.get(template_id)
    
    def add_template(self, template: MessageTemplate):
        """Şablon ekle"""
        self.templates[template.template_id] = template
    
    def render_template(self, template_id: str, variables: Dict[str, str]) -> Dict[str, str]:
        """Şablonu render et"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        return template.render(variables)


class CommunicationServicesIntegration:
    """İletişim Servisleri Entegrasyon Merkezi"""
    
    def __init__(self):
        self.providers: Dict[CommunicationChannel, Any] = {}
        self.template_manager = CommunicationTemplateManager()
        self.integration_framework = IntegrationFramework()
        self.preferences_store: Dict[str, CommunicationPreferences] = {}
        self.message_history: List[CommunicationResponse] = []
        self.logger = logging.getLogger("communication_services")
        
        # Rate limiting ve anti-spam
        self.rate_limits = {
            CommunicationChannel.SMS: {"per_hour": 100, "per_day": 500},
            CommunicationChannel.EMAIL: {"per_hour": 1000, "per_day": 10000},
            CommunicationChannel.WHATSAPP: {"per_hour": 50, "per_day": 200},
            CommunicationChannel.PUSH_NOTIFICATION: {"per_hour": 500, "per_day": 2000}
        }
        
    async def initialize(self):
        """İletişim entegrasyonunu başlat"""
        # Her iletişim kanalı için entegrasyon yapılandır
        channels_config = {
            CommunicationChannel.SMS: {
                "name": "sms_provider",
                "integration_type": IntegrationType.COMMUNICATION,
                "base_url": "https://api.sms-provider.com",
                "auth_method": AuthenticationMethod.API_KEY
            },
            CommunicationChannel.EMAIL: {
                "name": "email_provider",
                "integration_type": IntegrationType.COMMUNICATION,
                "base_url": "https://api.sendgrid.com",
                "auth_method": AuthenticationMethod.BEARER_TOKEN
            },
            CommunicationChannel.PUSH_NOTIFICATION: {
                "name": "push_provider",
                "integration_type": IntegrationType.COMMUNICATION,
                "base_url": "https://fcm.googleapis.com",
                "auth_method": AuthenticationMethod.API_KEY
            },
            CommunicationChannel.WHATSAPP: {
                "name": "whatsapp_provider",
                "integration_type": IntegrationType.COMMUNICATION,
                "base_url": "https://graph.facebook.com",
                "auth_method": AuthenticationMethod.BEARER_TOKEN
            }
        }
        
        for channel, config in channels_config.items():
            integration_config = IntegrationConfiguration(
                name=config["name"],
                integration_type=config["integration_type"],
                base_url=config["base_url"],
                authentication_method=config["auth_method"],
                rate_limit_per_minute=60,
                timeout=30,
                max_retries=3
            )
            
            await self.integration_framework.register_integration(
                channel.value, integration_config
            )
        
        self.logger.info("Communication Services Integration initialized")
    
    def add_provider(self, channel: CommunicationChannel, provider: Any):
        """Sağlayıcı ekle"""
        self.providers[channel] = provider
        self.logger.info(f"Added communication provider for {channel.value}")
    
    def set_user_preferences(self, user_id: str, preferences: CommunicationPreferences):
        """Kullanıcı iletişim tercihlerini ayarla"""
        self.preferences_store[user_id] = preferences
        
    def get_user_preferences(self, user_id: str) -> CommunicationPreferences:
        """Kullanıcı iletişim tercihlerini al"""
        return self.preferences_store.get(user_id, CommunicationPreferences(user_id=user_id))
    
    def _check_rate_limit(self, channel: CommunicationChannel, user_id: str) -> bool:
        """Rate limit kontrolü"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Son 1 saat ve 1 günlük mesajları say
        recent_messages = [
            msg for msg in self.message_history
            if (msg.channel == channel and 
                msg.provider_response.get("user_id") == user_id and
                msg.sent_at > day_ago)
        ]
        
        hourly_count = sum(1 for msg in recent_messages if msg.sent_at > hour_ago)
        daily_count = len(recent_messages)
        
        limits = self.rate_limits[channel]
        return (hourly_count < limits["per_hour"] and 
                daily_count < limits["per_day"])
    
    async def send_message(self, message: CommunicationMessage, 
                          user_id: Optional[str] = None) -> CommunicationResponse:
        """Mesaj gönder"""
        # Kullanıcı tercihlerini kontrol et
        if user_id:
            preferences = self.get_user_preferences(user_id)
            
            # KVKK onay kontrolü
            if not preferences.has_consent_for(message.message_type):
                return CommunicationResponse(
                    message_id=message.message_id,
                    provider_message_id="",
                    status=MessageStatus.FAILED,
                    channel=message.channel,
                    sent_at=datetime.now(),
                    error_message="User has not given consent for this message type"
                )
            
            # Kanal aktiflik kontrolü
            channel_enabled = {
                CommunicationChannel.SMS: preferences.sms_enabled,
                CommunicationChannel.EMAIL: preferences.email_enabled,
                CommunicationChannel.PUSH_NOTIFICATION: preferences.push_enabled,
                CommunicationChannel.WHATSAPP: preferences.whatsapp_enabled,
                CommunicationChannel.TELEGRAM: preferences.telegram_enabled
            }
            
            if not channel_enabled.get(message.channel, True):
                return CommunicationResponse(
                    message_id=message.message_id,
                    provider_message_id="",
                    status=MessageStatus.FAILED,
                    channel=message.channel,
                    sent_at=datetime.now(),
                    error_message=f"User has disabled {message.channel.value} notifications"
                )
            
            # Rate limit kontrolü
            if not self._check_rate_limit(message.channel, user_id):
                return CommunicationResponse(
                    message_id=message.message_id,
                    provider_message_id="",
                    status=MessageStatus.FAILED,
                    channel=message.channel,
                    sent_at=datetime.now(),
                    error_message="Rate limit exceeded"
                )
        
        # Sağlayıcı kontrolü
        if message.channel not in self.providers:
            return CommunicationResponse(
                message_id=message.message_id,
                provider_message_id="",
                status=MessageStatus.FAILED,
                channel=message.channel,
                sent_at=datetime.now(),
                error_message=f"No provider configured for {message.channel.value}"
            )
        
        # Zamanlı mesaj kontrolü
        if message.scheduled_at and message.scheduled_at > datetime.now():
            return CommunicationResponse(
                message_id=message.message_id,
                provider_message_id="",
                status=MessageStatus.PENDING,
                channel=message.channel,
                sent_at=datetime.now(),
                provider_response={"scheduled_at": message.scheduled_at.isoformat()}
            )
        
        # Mesajı gönder
        try:
            provider = self.providers[message.channel]
            
            if message.channel == CommunicationChannel.SMS:
                response = await provider.send_sms(
                    message.recipient, message.content
                )
            elif message.channel == CommunicationChannel.EMAIL:
                response = await provider.send_email(
                    message.recipient, message.subject, message.content
                )
            elif message.channel == CommunicationChannel.PUSH_NOTIFICATION:
                response = await provider.send_push_notification(
                    message.recipient, message.subject, message.content,
                    message.metadata
                )
            elif message.channel == CommunicationChannel.WHATSAPP:
                response = await provider.send_whatsapp_message(
                    message.recipient, message.content
                )
            elif message.channel == CommunicationChannel.TELEGRAM:
                response = await provider.send_telegram_message(
                    message.recipient, message.content
                )
            else:
                raise Exception(f"Unsupported channel: {message.channel}")
            
            # User ID'yi yanıta ekle
            if user_id:
                response.provider_response["user_id"] = user_id
            
            # Mesaj geçmişine ekle
            self.message_history.append(response)
            if len(self.message_history) > 10000:  # Son 10000 mesajı tut
                self.message_history = self.message_history[-10000:]
            
            # Audit log
            self.logger.info(
                f"Message sent - ID: {response.message_id}, "
                f"Channel: {response.channel.value}, "
                f"Status: {response.status.value}, "
                f"Recipient: {message.recipient[:3]}***"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return CommunicationResponse(
                message_id=message.message_id,
                provider_message_id="",
                status=MessageStatus.FAILED,
                channel=message.channel,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    async def send_template_message(self, template_id: str, recipient: str,
                                  variables: Dict[str, str], channel: CommunicationChannel,
                                  message_type: MessageType, user_id: Optional[str] = None,
                                  priority: MessagePriority = MessagePriority.NORMAL) -> CommunicationResponse:
        """Şablon mesajı gönder"""
        try:
            rendered = self.template_manager.render_template(template_id, variables)
            
            message = CommunicationMessage(
                message_id="",
                recipient=recipient,
                channel=channel,
                message_type=message_type,
                priority=priority,
                subject=rendered.get("subject"),
                content=rendered["body"],
                template_id=template_id
            )
            
            return await self.send_message(message, user_id)
            
        except Exception as e:
            self.logger.error(f"Failed to send template message: {e}")
            return CommunicationResponse(
                message_id=f"error_{int(time.time())}",
                provider_message_id="",
                status=MessageStatus.FAILED,
                channel=channel,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    # === KIRO2 İçin Özel Metodlar ===
    
    async def send_kiro2_welcome_sequence(self, user_id: str, name: str, 
                                        phone: str, email: str) -> List[CommunicationResponse]:
        """KIRO2 hoşgeldin mesaj dizisi"""
        responses = []
        
        variables = {
            "name": name,
            "login_url": "https://kiro2.com/login"
        }
        
        # SMS hoşgeldin
        sms_response = await self.send_template_message(
            template_id="welcome_sms",
            recipient=phone,
            variables=variables,
            channel=CommunicationChannel.SMS,
            message_type=MessageType.WELCOME,
            user_id=user_id
        )
        responses.append(sms_response)
        
        # E-posta hoşgeldin (5 dakika sonra)
        email_response = await self.send_template_message(
            template_id="welcome_email",
            recipient=email,
            variables=variables,
            channel=CommunicationChannel.EMAIL,
            message_type=MessageType.WELCOME,
            user_id=user_id
        )
        responses.append(email_response)
        
        return responses
    
    async def send_exam_reminder_notifications(self, user_id: str, exam_name: str,
                                             exam_datetime: datetime, 
                                             notification_channels: List[CommunicationChannel]) -> List[CommunicationResponse]:
        """Sınav hatırlatma bildirimleri"""
        responses = []
        
        variables = {
            "exam_name": exam_name,
            "exam_time": exam_datetime.strftime("%H:%M"),
            "exam_date": exam_datetime.strftime("%d.%m.%Y")
        }
        
        preferences = self.get_user_preferences(user_id)
        
        for channel in notification_channels:
            if channel == CommunicationChannel.PUSH_NOTIFICATION:
                message = CommunicationMessage(
                    message_id="",
                    recipient=f"user_{user_id}",  # Device token gerçekte
                    channel=channel,
                    message_type=MessageType.EXAM_NOTIFICATION,
                    priority=MessagePriority.HIGH,
                    subject="Sınavın Yarın!",
                    content=f"{exam_name} sınavın yarın saat {variables['exam_time']}'da. Hazır mısın?"
                )
                
                response = await self.send_message(message, user_id)
                responses.append(response)
        
        return responses
    
    async def send_study_reminder(self, user_id: str, name: str, subject: str,
                                study_goals: List[str], duration_minutes: int,
                                preferred_channel: CommunicationChannel) -> CommunicationResponse:
        """Çalışma hatırlatıcısı gönder"""
        variables = {
            "name": name,
            "subject": subject,
            "study_goals": "\n".join([f"• {goal}" for goal in study_goals]),
            "duration": str(duration_minutes),
            "app_url": "https://kiro2.com/app"
        }
        
        if preferred_channel == CommunicationChannel.WHATSAPP:
            return await self.send_template_message(
                template_id="study_reminder_whatsapp",
                recipient=f"user_{user_id}_whatsapp",  # WhatsApp number gerçekte
                variables=variables,
                channel=CommunicationChannel.WHATSAPP,
                message_type=MessageType.STUDY_REMINDER,
                user_id=user_id
            )
        else:
            # Varsayılan push notification
            message = CommunicationMessage(
                message_id="",
                recipient=f"user_{user_id}",
                channel=CommunicationChannel.PUSH_NOTIFICATION,
                message_type=MessageType.STUDY_REMINDER,
                priority=MessagePriority.NORMAL,
                subject="Çalışma Zamanı! [BOOKS]",
                content=f"Merhaba {name}, {subject} konularında çalışma zamanın geldi!"
            )
            
            return await self.send_message(message, user_id)
    
    async def create_live_lesson_meeting(self, teacher_email: str, lesson_topic: str,
                                       start_time: datetime, duration_minutes: int) -> Dict[str, Any]:
        """Canlı ders toplantısı oluştur"""
        if CommunicationChannel.VIDEO_CONFERENCE in self.providers:
            provider = self.providers[CommunicationChannel.VIDEO_CONFERENCE]
            return await provider.create_meeting(
                topic=f"KIRO2 Canlı Ders: {lesson_topic}",
                start_time=start_time,
                duration_minutes=duration_minutes,
                host_email=teacher_email
            )
        else:
            raise Exception("Video conference provider not configured")
    
    def get_communication_statistics_for_kiro2(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """KIRO2 için iletişim istatistikleri"""
        messages = self.message_history
        
        if user_id:
            messages = [
                msg for msg in messages 
                if msg.provider_response.get("user_id") == user_id
            ]
        
        stats = {
            "total_messages": len(messages),
            "by_channel": {},
            "by_status": {},
            "by_type": {},
            "success_rate": 0.0,
            "last_24h_count": 0,
            "avg_delivery_time": 0.0
        }
        
        # Kanal bazında istatistikler
        for channel in CommunicationChannel:
            channel_messages = [msg for msg in messages if msg.channel == channel]
            stats["by_channel"][channel.value] = len(channel_messages)
        
        # Durum bazında istatistikler
        for status in MessageStatus:
            status_messages = [msg for msg in messages if msg.status == status]
            stats["by_status"][status.value] = len(status_messages)
        
        # Başarı oranı
        successful = stats["by_status"].get("sent", 0) + stats["by_status"].get("delivered", 0)
        if stats["total_messages"] > 0:
            stats["success_rate"] = (successful / stats["total_messages"]) * 100
        
        # Son 24 saat
        day_ago = datetime.now() - timedelta(days=1)
        stats["last_24h_count"] = len([
            msg for msg in messages if msg.sent_at > day_ago
        ])
        
        return stats


# === KIRO2 İletişim Yöneticisi ===

class KIRO2CommunicationManager:
    """KIRO2 İletişim Yöneticisi"""
    
    def __init__(self):
        self.communication_service = CommunicationServicesIntegration()
        self.initialized = False
        
    async def initialize_for_kiro2(self, communication_credentials: Dict[str, Dict[str, str]]):
        """KIRO2 için iletişim sistemini başlat"""
        await self.communication_service.initialize()
        
        # SMS sağlayıcısı ekle
        if "sms" in communication_credentials:
            creds = communication_credentials["sms"]
            sms_provider = TurkishSMSProvider(
                provider_name=creds["provider"],
                username=creds["username"],
                password=creds["password"],
                api_key=creds["api_key"],
                base_url=creds["base_url"]
            )
            self.communication_service.add_provider(CommunicationChannel.SMS, sms_provider)
        
        # E-posta sağlayıcısı ekle
        if "email" in communication_credentials:
            creds = communication_credentials["email"]
            email_provider = EmailServiceProvider(
                provider_name=creds["provider"],
                api_key=creds["api_key"],
                from_email=creds["from_email"],
                base_url=creds["base_url"]
            )
            self.communication_service.add_provider(CommunicationChannel.EMAIL, email_provider)
        
        # Push notification sağlayıcısı ekle
        if "push" in communication_credentials:
            creds = communication_credentials["push"]
            push_provider = PushNotificationProvider(
                server_key=creds["server_key"],
                project_id=creds["project_id"]
            )
            self.communication_service.add_provider(CommunicationChannel.PUSH_NOTIFICATION, push_provider)
        
        # WhatsApp sağlayıcısı ekle
        if "whatsapp" in communication_credentials:
            creds = communication_credentials["whatsapp"]
            whatsapp_provider = WhatsAppBusinessProvider(
                access_token=creds["access_token"],
                phone_number_id=creds["phone_number_id"]
            )
            self.communication_service.add_provider(CommunicationChannel.WHATSAPP, whatsapp_provider)
        
        # Video konferans sağlayıcısı ekle
        if "zoom" in communication_credentials:
            creds = communication_credentials["zoom"]
            zoom_provider = VideoConferenceProvider(
                api_key=creds["api_key"],
                api_secret=creds["api_secret"],
                account_id=creds["account_id"]
            )
            self.communication_service.add_provider(CommunicationChannel.VIDEO_CONFERENCE, zoom_provider)
        
        self.initialized = True
        logging.info("KIRO2 Communication Manager initialized")
    
    async def setup_student_communication_preferences(self, user_id: str,
                                                    sms_enabled: bool = True,
                                                    email_enabled: bool = True,
                                                    push_enabled: bool = True,
                                                    marketing_consent: bool = False) -> CommunicationPreferences:
        """Öğrenci iletişim tercihlerini ayarla"""
        preferences = CommunicationPreferences(
            user_id=user_id,
            sms_enabled=sms_enabled,
            email_enabled=email_enabled,
            push_enabled=push_enabled,
            marketing_consent=marketing_consent,
            study_reminders=True,
            exam_notifications=True,
            result_notifications=True
        )
        
        self.communication_service.set_user_preferences(user_id, preferences)
        return preferences
    
    async def send_verification_code(self, user_id: str, phone: str, 
                                   verification_code: str) -> CommunicationResponse:
        """Doğrulama kodu gönder"""
        return await self.communication_service.send_template_message(
            template_id="verification_sms",
            recipient=phone,
            variables={"code": verification_code},
            channel=CommunicationChannel.SMS,
            message_type=MessageType.VERIFICATION,
            user_id=user_id,
            priority=MessagePriority.HIGH
        )
    
    async def notify_exam_results(self, user_id: str, student_name: str,
                                exam_name: str, score: float, ranking: int,
                                notification_channels: List[CommunicationChannel]) -> List[CommunicationResponse]:
        """Sınav sonuçlarını bildir"""
        responses = []
        
        for channel in notification_channels:
            if channel == CommunicationChannel.SMS:
                message = CommunicationMessage(
                    message_id="",
                    recipient=f"user_{user_id}_phone",
                    channel=channel,
                    message_type=MessageType.RESULT_NOTIFICATION,
                    priority=MessagePriority.HIGH,
                    subject=None,
                    content=f"KIRO2: {exam_name} sonucun hazır! Puan: {score}, Sıralama: {ranking}. Detaylar için uygulamayı aç."
                )
            elif channel == CommunicationChannel.EMAIL:
                message = CommunicationMessage(
                    message_id="",
                    recipient=f"user_{user_id}_email",
                    channel=channel,
                    message_type=MessageType.RESULT_NOTIFICATION,
                    priority=MessagePriority.HIGH,
                    subject=f"KIRO2: {exam_name} Sonucun Hazır!",
                    content=f"""
                    <h2>Merhaba {student_name}!</h2>
                    <p><strong>{exam_name}</strong> sınavının sonucun hazır:</p>
                    <ul>
                        <li>Puanın: <strong>{score}</strong></li>
                        <li>Sıralaman: <strong>{ranking}</strong></li>
                    </ul>
                    <p>Detaylı analiz ve öneriler için KIRO2 uygulamasını ziyaret et.</p>
                    """
                )
            else:
                continue
            
            response = await self.communication_service.send_message(message, user_id)
            responses.append(response)
        
        return responses


# === Örnek Kullanım ===

async def example_communication_integration():
    """İletişim entegrasyonu örnek kullanımı"""
    
    # İletişim yöneticisini başlat
    manager = KIRO2CommunicationManager()
    
    # Kimlik bilgileri
    credentials = {
        "sms": {
            "provider": "netgsm",
            "username": "test_user",
            "password": "test_pass",
            "api_key": "test_api_key",
            "base_url": "https://api.netgsm.com.tr"
        },
        "email": {
            "provider": "sendgrid",
            "api_key": "SG.test_api_key",
            "from_email": "noreply@kiro2.com",
            "base_url": "https://api.sendgrid.com"
        },
        "push": {
            "server_key": "firebase_server_key",
            "project_id": "kiro2-firebase-project"
        }
    }
    
    await manager.initialize_for_kiro2(credentials)
    
    # Öğrenci iletişim tercihlerini ayarla
    user_id = "kiro2_student_12345"
    preferences = await manager.setup_student_communication_preferences(
        user_id=user_id,
        sms_enabled=True,
        email_enabled=True,
        push_enabled=True,
        marketing_consent=False
    )
    
    print(f"İletişim tercihleri ayarlandı: {preferences}")
    
    # Hoşgeldin mesaj dizisi gönder
    welcome_responses = await manager.communication_service.send_kiro2_welcome_sequence(
        user_id=user_id,
        name="Ahmet Yılmaz",
        phone="+905551234567",
        email="ahmet@test.com"
    )
    
    print(f"Hoşgeldin mesajları gönderildi: {len(welcome_responses)} mesaj")
    
    # Doğrulama kodu gönder
    verification_response = await manager.send_verification_code(
        user_id=user_id,
        phone="+905551234567",
        verification_code="123456"
    )
    
    print(f"Doğrulama kodu durumu: {verification_response.status.value}")
    
    # Sınav sonuçlarını bildir
    result_responses = await manager.notify_exam_results(
        user_id=user_id,
        student_name="Ahmet Yılmaz",
        exam_name="TYT Deneme-5",
        score=385.75,
        ranking=1250,
        notification_channels=[CommunicationChannel.SMS, CommunicationChannel.EMAIL]
    )
    
    print(f"Sınav sonucu bildirimleri: {len(result_responses)} mesaj gönderildi")
    
    # İstatistikleri al
    stats = manager.communication_service.get_communication_statistics_for_kiro2(user_id)
    print(f"İletişim İstatistikleri:")
    print(f"Toplam Mesaj: {stats['total_messages']}")
    print(f"Başarı Oranı: {stats['success_rate']:.1f}%")
    print(f"Son 24 Saat: {stats['last_24h_count']} mesaj")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_communication_integration())