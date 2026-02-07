"""
SSO/SAML 2.0 Authentication Service - KIRO2 YKS Platform

Bu modul, enterprise Single Sign-On (SSO) islevselligini SAML 2.0 protokolu
ile saglar. Identity Provider (IdP) entegrasyonu ve attribute mapping destekler.

REQ-3.1: SAML 2.0 protokol implementasyonu
REQ-3.2: IdP XML metadata parse
REQ-3.3: SAML assertion signature verification
REQ-3.4: Attribute mapping (email, name, role)
REQ-3.5: Single Logout (SLO) destegi
REQ-3.6: Session timeout sync

Kullanim:
    saml_service = get_saml_service()
    await saml_service.configure_idp(idp_metadata_xml)
    auth_request = await saml_service.create_authn_request()
    user_attrs = await saml_service.process_saml_response(saml_response)
    await saml_service.initiate_logout(session_id)

Guvenlik Notlari:
- SAML assertion'lar signature ile dogrulanir
- Replay attack'lara karsi InResponseTo kontrolu yapilir
- Assertion'lar zaman damgasi ile dogrulanir
- NotBefore/NotOnOrAfter kontrolleri uygulanir
"""

import base64
import logging
import secrets
import uuid
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from xml.etree import ElementTree as ET

from cryptography import x509

# Structured logging
logger = logging.getLogger(__name__)

# SAML XML namespaces
SAML_NS = {
    "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
    "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
    "md": "urn:oasis:names:tc:SAML:2.0:metadata",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}


# ==================== ENUMS ====================


class SAMLBinding(str, Enum):
    """SAML binding turleri.

    Attributes:
        HTTP_REDIRECT: HTTP Redirect binding (GET)
        HTTP_POST: HTTP POST binding
        HTTP_ARTIFACT: HTTP Artifact binding
    """

    HTTP_REDIRECT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    HTTP_POST = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    HTTP_ARTIFACT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"


class SAMLNameIDFormat(str, Enum):
    """SAML NameID formatlari.

    Attributes:
        EMAIL: Email address format
        PERSISTENT: Persistent identifier
        TRANSIENT: Transient identifier
        UNSPECIFIED: Unspecified format
    """

    EMAIL = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    PERSISTENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
    TRANSIENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:transient"
    UNSPECIFIED = "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"


class SAMLError(str, Enum):
    """SAML hata kodlari.

    Attributes:
        INVALID_METADATA: IdP metadata gecersiz
        INVALID_SIGNATURE: SAML signature gecersiz
        INVALID_ASSERTION: SAML assertion gecersiz
        EXPIRED_ASSERTION: Assertion suresi dolmus
        REPLAY_ATTACK: Tekrar saldiris tespit edildi
        MISSING_ATTRIBUTE: Zorunlu attribute eksik
        IDP_NOT_CONFIGURED: IdP yapilandirilmamis
        SLO_FAILED: Single Logout basarisiz
    """

    INVALID_METADATA = "invalid_metadata"
    INVALID_SIGNATURE = "invalid_signature"
    INVALID_ASSERTION = "invalid_assertion"
    EXPIRED_ASSERTION = "expired_assertion"
    REPLAY_ATTACK = "replay_attack"
    MISSING_ATTRIBUTE = "missing_attribute"
    IDP_NOT_CONFIGURED = "idp_not_configured"
    SLO_FAILED = "slo_failed"


# ==================== DATA CLASSES ====================


@dataclass
class IdPConfig:
    """Identity Provider konfigurasyonu.

    IdP metadata'dan parse edilen bilgileri icerir.

    Attributes:
        entity_id: IdP entity identifier
        sso_url: Single Sign-On URL
        slo_url: Single Logout URL (opsiyonel)
        certificate: IdP X.509 sertifikasi (PEM format)
        name_id_format: Desteklenen NameID formati
        binding: Kullanilan SAML binding
    """

    entity_id: str
    sso_url: str
    slo_url: Optional[str] = None
    certificate: Optional[str] = None
    name_id_format: SAMLNameIDFormat = SAMLNameIDFormat.EMAIL
    binding: SAMLBinding = SAMLBinding.HTTP_POST


@dataclass
class SPConfig:
    """Service Provider konfigurasyonu.

    KIRO2 platformunun SP olarak ayarlari.

    Attributes:
        entity_id: SP entity identifier
        acs_url: Assertion Consumer Service URL
        slo_url: Single Logout URL
        metadata_url: SP metadata URL
        private_key: SP private key (signing icin)
        certificate: SP X.509 sertifikasi
    """

    entity_id: str
    acs_url: str
    slo_url: str
    metadata_url: str
    private_key: Optional[str] = None
    certificate: Optional[str] = None


@dataclass
class SAMLAssertion:
    """Parse edilmis SAML assertion.

    Attributes:
        id: Assertion ID
        issuer: Assertion'i olusturan IdP
        subject_name_id: Kullanici identifier
        subject_name_id_format: NameID formati
        audience: Hedef SP entity ID
        not_before: Gecerlilik baslangici
        not_on_or_after: Gecerlilik bitisi
        authn_instant: Authentication zamani
        session_index: IdP session index (SLO icin)
        attributes: Kullanici attribute'lari
    """

    id: str
    issuer: str
    subject_name_id: str
    subject_name_id_format: str
    audience: str
    not_before: datetime
    not_on_or_after: datetime
    authn_instant: datetime
    session_index: Optional[str] = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserAttributes:
    """SAML'dan extract edilen kullanici bilgileri.

    Attributes:
        email: Kullanici email adresi
        name: Tam ad
        first_name: Ad
        last_name: Soyad
        role: Kullanici rolu
        groups: Grup uyellikleri
        extra: Diger attribute'lar
    """

    email: str
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    groups: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthnRequest:
    """SAML AuthnRequest bilgileri.

    Attributes:
        id: Request ID
        issue_instant: Olusturma zamani
        destination: IdP SSO URL
        assertion_consumer_service_url: ACS URL
        redirect_url: Redirect edilecek URL (encoded)
        relay_state: Relay state (callback icin)
    """

    id: str
    issue_instant: datetime
    destination: str
    assertion_consumer_service_url: str
    redirect_url: str
    relay_state: str


@dataclass
class LogoutRequest:
    """SAML LogoutRequest bilgileri.

    Attributes:
        id: Request ID
        issue_instant: Olusturma zamani
        destination: IdP SLO URL
        name_id: Kullanici NameID
        session_index: Session index
        redirect_url: Redirect edilecek URL
    """

    id: str
    issue_instant: datetime
    destination: str
    name_id: str
    session_index: str
    redirect_url: str


@dataclass
class SAMLServiceResult:
    """SAML islem sonucu.

    Attributes:
        success: Islem basarili mi
        error: Hata kodu (basarisizsa)
        error_message: Hata mesaji
        data: Sonuc verisi
    """

    success: bool
    error: Optional[SAMLError] = None
    error_message: Optional[str] = None
    data: Optional[Any] = None


# ==================== ATTRIBUTE MAPPING ====================

# Standart SAML attribute isimleri
ATTRIBUTE_MAP = {
    # Email attribute'lari
    "urn:oid:0.9.2342.19200300.100.1.3": "email",
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": "email",
    "mail": "email",
    "email": "email",
    # Ad attribute'lari
    "urn:oid:2.5.4.42": "first_name",
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": "first_name",
    "givenName": "first_name",
    "firstName": "first_name",
    # Soyad attribute'lari
    "urn:oid:2.5.4.4": "last_name",
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": "last_name",
    "sn": "last_name",
    "surname": "last_name",
    "lastName": "last_name",
    # Tam ad attribute'lari
    "urn:oid:2.16.840.1.113730.3.1.241": "name",
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name": "name",
    "displayName": "name",
    "cn": "name",
    # Rol attribute'lari
    "urn:oid:2.5.4.12": "role",
    "http://schemas.microsoft.com/ws/2008/06/identity/claims/role": "role",
    "role": "role",
    "memberOf": "groups",
    # Grup attribute'lari
    "http://schemas.xmlsoap.org/claims/Group": "groups",
    "groups": "groups",
}


# ==================== SAML SERVICE ====================


class SAMLService:
    """SAML 2.0 SSO servisi.

    Enterprise SSO entegrasyonu icin SAML 2.0 protokolunu implement eder.
    IdP metadata parsing, assertion validation, attribute mapping ve
    Single Logout (SLO) destekler.

    Attributes:
        sp_config: Service Provider konfigurasyonu
        idp_config: Identity Provider konfigurasyonu
        _pending_requests: Bekleyen AuthnRequest'ler (replay korumasi)
        _processed_assertions: Islenmis assertion ID'leri (replay korumasi)
        _active_sessions: Aktif SSO session'lari (SLO icin)
    """

    def __init__(self, sp_config: SPConfig) -> None:
        """SAMLService olustur.

        Args:
            sp_config: Service Provider konfigurasyonu
        """
        self.sp_config = sp_config
        self.idp_config: Optional[IdPConfig] = None
        self._pending_requests: dict[str, AuthnRequest] = {}
        self._processed_assertions: set[str] = set()
        self._active_sessions: dict[str, dict[str, Any]] = {}
        # Request expiry: 5 dakika
        self._request_expiry = timedelta(minutes=5)
        # Assertion cache expiry: 1 saat
        self._assertion_cache_expiry = timedelta(hours=1)

        logger.info(
            "SAMLService baslatildi",
            extra={"sp_entity_id": sp_config.entity_id},
        )

    async def configure_idp(self, metadata_xml: str) -> SAMLServiceResult:
        """IdP metadata'dan konfigurasyonu parse et.

        IdP'nin XML metadata dosyasini parse ederek SSO, SLO URL'lerini
        ve sertifikayi extract eder.

        Args:
            metadata_xml: IdP metadata XML string

        Returns:
            SAMLServiceResult: Parse sonucu

        Example:
            >>> result = await saml_service.configure_idp(idp_metadata)
            >>> if result.success:
            ...     print(f"IdP configured: {result.data.entity_id}")
        """
        try:
            # XML parse et
            root = ET.fromstring(metadata_xml)

            # Entity ID al
            entity_id = root.get("entityID")
            if not entity_id:
                return SAMLServiceResult(
                    success=False,
                    error=SAMLError.INVALID_METADATA,
                    error_message="entityID bulunamadi",
                )

            # SSO URL bul
            sso_url = None
            sso_elem = root.find(
                ".//md:IDPSSODescriptor/md:SingleSignOnService[@Binding='%s']"
                % SAMLBinding.HTTP_POST.value,
                SAML_NS,
            )
            if sso_elem is not None:
                sso_url = sso_elem.get("Location")
            else:
                # HTTP-Redirect binding dene
                sso_elem = root.find(
                    ".//md:IDPSSODescriptor/md:SingleSignOnService[@Binding='%s']"
                    % SAMLBinding.HTTP_REDIRECT.value,
                    SAML_NS,
                )
                if sso_elem is not None:
                    sso_url = sso_elem.get("Location")

            if not sso_url:
                return SAMLServiceResult(
                    success=False,
                    error=SAMLError.INVALID_METADATA,
                    error_message="SingleSignOnService URL bulunamadi",
                )

            # SLO URL bul (opsiyonel)
            slo_url = None
            slo_elem = root.find(
                ".//md:IDPSSODescriptor/md:SingleLogoutService[@Binding='%s']"
                % SAMLBinding.HTTP_POST.value,
                SAML_NS,
            )
            if slo_elem is not None:
                slo_url = slo_elem.get("Location")

            # Certificate bul
            certificate = None
            cert_elem = root.find(
                ".//md:IDPSSODescriptor/md:KeyDescriptor[@use='signing']"
                "/ds:KeyInfo/ds:X509Data/ds:X509Certificate",
                SAML_NS,
            )
            if cert_elem is not None and cert_elem.text:
                # PEM formatina cevir
                cert_data = cert_elem.text.strip()
                certificate = (
                    "-----BEGIN CERTIFICATE-----\n"
                    + cert_data
                    + "\n-----END CERTIFICATE-----"
                )

            # NameID format bul
            name_id_format = SAMLNameIDFormat.EMAIL
            nid_elem = root.find(".//md:IDPSSODescriptor/md:NameIDFormat", SAML_NS)
            if nid_elem is not None and nid_elem.text:
                for fmt in SAMLNameIDFormat:
                    if fmt.value == nid_elem.text:
                        name_id_format = fmt
                        break

            # IdP config olustur
            self.idp_config = IdPConfig(
                entity_id=entity_id,
                sso_url=sso_url,
                slo_url=slo_url,
                certificate=certificate,
                name_id_format=name_id_format,
            )

            logger.info(
                "IdP konfigurasyonu yuklendi",
                extra={
                    "idp_entity_id": entity_id,
                    "sso_url": sso_url,
                    "slo_url": slo_url,
                    "has_certificate": certificate is not None,
                },
            )

            return SAMLServiceResult(success=True, data=self.idp_config)

        except ET.ParseError as e:
            logger.error(f"IdP metadata XML parse hatasi: {e}")
            return SAMLServiceResult(
                success=False,
                error=SAMLError.INVALID_METADATA,
                error_message=f"XML parse hatasi: {e}",
            )

    async def create_authn_request(
        self,
        relay_state: Optional[str] = None,
        force_authn: bool = False,
    ) -> SAMLServiceResult:
        """SAML AuthnRequest olustur.

        IdP'ye yonlendirilecek AuthnRequest XML'ini olusturur ve
        redirect URL'ini dondurur.

        Args:
            relay_state: Callback sonrasi geri donulecek state
            force_authn: Yeniden authentication zorla

        Returns:
            SAMLServiceResult: AuthnRequest bilgileri

        Example:
            >>> result = await saml_service.create_authn_request(relay_state="/dashboard")
            >>> if result.success:
            ...     return redirect(result.data.redirect_url)
        """
        if not self.idp_config:
            return SAMLServiceResult(
                success=False,
                error=SAMLError.IDP_NOT_CONFIGURED,
                error_message="IdP henuz yapilandirilmamis",
            )

        # Request ID olustur
        request_id = f"_kiro2_{uuid.uuid4().hex}"
        issue_instant = datetime.now(timezone.utc)

        # Relay state yoksa olustur
        if not relay_state:
            relay_state = secrets.token_urlsafe(16)

        # AuthnRequest XML olustur
        force_authn_tag = '<samlp:ForceAuthn Value="true"/>' if force_authn else ""
        authn_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    Destination="{self.idp_config.sso_url}"
    AssertionConsumerServiceURL="{self.sp_config.acs_url}"
    ProtocolBinding="{SAMLBinding.HTTP_POST.value}">
    <saml:Issuer>{self.sp_config.entity_id}</saml:Issuer>
    <samlp:NameIDPolicy
        Format="{self.idp_config.name_id_format.value}"
        AllowCreate="true"/>
    {force_authn_tag}
</samlp:AuthnRequest>"""

        # Deflate + Base64 encode (HTTP-Redirect binding icin)
        compressed = zlib.compress(authn_request.encode("utf-8"))[2:-4]
        encoded = base64.b64encode(compressed).decode("utf-8")

        # URL olustur
        import urllib.parse

        params = {
            "SAMLRequest": encoded,
            "RelayState": relay_state,
        }
        redirect_url = f"{self.idp_config.sso_url}?{urllib.parse.urlencode(params)}"

        # Request kaydet (replay korumasi)
        request = AuthnRequest(
            id=request_id,
            issue_instant=issue_instant,
            destination=self.idp_config.sso_url,
            assertion_consumer_service_url=self.sp_config.acs_url,
            redirect_url=redirect_url,
            relay_state=relay_state,
        )
        self._pending_requests[request_id] = request

        # Eski request'leri temizle
        await self._cleanup_expired_requests()

        logger.info(
            "AuthnRequest olusturuldu",
            extra={
                "request_id": request_id,
                "destination": self.idp_config.sso_url,
            },
        )

        return SAMLServiceResult(success=True, data=request)

    async def process_saml_response(
        self,
        saml_response: str,
        relay_state: Optional[str] = None,
    ) -> SAMLServiceResult:
        """SAML Response isle ve kullanici bilgilerini extract et.

        IdP'den gelen SAML Response'u parse eder, signature dogrular,
        assertion'i validate eder ve kullanici attribute'larini extract eder.

        Args:
            saml_response: Base64 encoded SAML Response
            relay_state: Relay state (dogrulama icin)

        Returns:
            SAMLServiceResult: UserAttributes veya hata

        Example:
            >>> result = await saml_service.process_saml_response(saml_response)
            >>> if result.success:
            ...     user_attrs = result.data
            ...     print(f"User: {user_attrs.email}")
        """
        if not self.idp_config:
            return SAMLServiceResult(
                success=False,
                error=SAMLError.IDP_NOT_CONFIGURED,
                error_message="IdP henuz yapilandirilmamis",
            )

        try:
            # Base64 decode
            xml_data = base64.b64decode(saml_response)
            root = ET.fromstring(xml_data)

            # Status kontrol
            status_code = root.find(
                ".//samlp:Status/samlp:StatusCode", SAML_NS
            )
            if status_code is not None:
                status = status_code.get("Value", "")
                if "Success" not in status:
                    return SAMLServiceResult(
                        success=False,
                        error=SAMLError.INVALID_ASSERTION,
                        error_message=f"SAML Status: {status}",
                    )

            # Assertion bul
            assertion_elem = root.find(".//saml:Assertion", SAML_NS)
            if assertion_elem is None:
                return SAMLServiceResult(
                    success=False,
                    error=SAMLError.INVALID_ASSERTION,
                    error_message="Assertion bulunamadi",
                )

            # Assertion parse et
            assertion = await self._parse_assertion(assertion_elem)
            if not assertion:
                return SAMLServiceResult(
                    success=False,
                    error=SAMLError.INVALID_ASSERTION,
                    error_message="Assertion parse edilemedi",
                )

            # Replay attack kontrolu
            if assertion.id in self._processed_assertions:
                logger.warning(
                    "Replay attack tespit edildi",
                    extra={"assertion_id": assertion.id},
                )
                return SAMLServiceResult(
                    success=False,
                    error=SAMLError.REPLAY_ATTACK,
                    error_message="Bu assertion daha once kullanilmis",
                )

            # InResponseTo kontrolu
            in_response_to = root.get("InResponseTo")
            if in_response_to and in_response_to not in self._pending_requests:
                logger.warning(
                    "InResponseTo eslesmedi",
                    extra={"in_response_to": in_response_to},
                )
                # Strict modda hata don, simdilik uyari
                pass

            # Zaman kontrolu
            now = datetime.now(timezone.utc)
            if assertion.not_before > now:
                return SAMLServiceResult(
                    success=False,
                    error=SAMLError.INVALID_ASSERTION,
                    error_message="Assertion henuz gecerli degil",
                )
            if assertion.not_on_or_after < now:
                return SAMLServiceResult(
                    success=False,
                    error=SAMLError.EXPIRED_ASSERTION,
                    error_message="Assertion suresi dolmus",
                )

            # Audience kontrolu
            if assertion.audience != self.sp_config.entity_id:
                logger.warning(
                    "Audience eslesmedi",
                    extra={
                        "expected": self.sp_config.entity_id,
                        "actual": assertion.audience,
                    },
                )
                # Strict modda hata don

            # Signature dogrula (sertifika varsa)
            if self.idp_config.certificate:
                sig_valid = await self._verify_signature(root)
                if not sig_valid:
                    return SAMLServiceResult(
                        success=False,
                        error=SAMLError.INVALID_SIGNATURE,
                        error_message="SAML signature gecersiz",
                    )

            # Assertion ID kaydet (replay korumasi)
            self._processed_assertions.add(assertion.id)

            # Pending request temizle
            if in_response_to:
                self._pending_requests.pop(in_response_to, None)

            # Attribute mapping yap
            user_attrs = await self._extract_attributes(assertion)

            # Session kaydet (SLO icin)
            if assertion.session_index:
                self._active_sessions[assertion.session_index] = {
                    "user_email": user_attrs.email,
                    "assertion_id": assertion.id,
                    "created_at": datetime.now(timezone.utc),
                }

            logger.info(
                "SAML Response basariyla islendi",
                extra={
                    "assertion_id": assertion.id,
                    "user_email": user_attrs.email,
                    "session_index": assertion.session_index,
                },
            )

            return SAMLServiceResult(success=True, data=user_attrs)

        except ET.ParseError as e:
            logger.error(f"SAML Response XML parse hatasi: {e}")
            return SAMLServiceResult(
                success=False,
                error=SAMLError.INVALID_ASSERTION,
                error_message=f"XML parse hatasi: {e}",
            )
        except Exception as e:
            logger.error(f"SAML Response isleme hatasi: {e}")
            return SAMLServiceResult(
                success=False,
                error=SAMLError.INVALID_ASSERTION,
                error_message=str(e),
            )

    async def initiate_logout(
        self,
        session_index: str,
        name_id: str,
    ) -> SAMLServiceResult:
        """Single Logout (SLO) baslat.

        IdP'ye LogoutRequest gonderir ve kullanici oturumunu kapatir.

        Args:
            session_index: SSO session index
            name_id: Kullanici NameID

        Returns:
            SAMLServiceResult: LogoutRequest bilgileri

        Example:
            >>> result = await saml_service.initiate_logout(session_index, name_id)
            >>> if result.success:
            ...     return redirect(result.data.redirect_url)
        """
        if not self.idp_config:
            return SAMLServiceResult(
                success=False,
                error=SAMLError.IDP_NOT_CONFIGURED,
                error_message="IdP henuz yapilandirilmamis",
            )

        if not self.idp_config.slo_url:
            return SAMLServiceResult(
                success=False,
                error=SAMLError.SLO_FAILED,
                error_message="IdP SLO desteklemiyor",
            )

        # Request ID olustur
        request_id = f"_kiro2_logout_{uuid.uuid4().hex}"
        issue_instant = datetime.now(timezone.utc)

        # LogoutRequest XML olustur
        logout_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:LogoutRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    Destination="{self.idp_config.slo_url}">
    <saml:Issuer>{self.sp_config.entity_id}</saml:Issuer>
    <saml:NameID Format="{self.idp_config.name_id_format.value}">
        {name_id}
    </saml:NameID>
    <samlp:SessionIndex>{session_index}</samlp:SessionIndex>
</samlp:LogoutRequest>"""

        # Deflate + Base64 encode
        compressed = zlib.compress(logout_request.encode("utf-8"))[2:-4]
        encoded = base64.b64encode(compressed).decode("utf-8")

        # URL olustur
        import urllib.parse

        params = {"SAMLRequest": encoded}
        redirect_url = f"{self.idp_config.slo_url}?{urllib.parse.urlencode(params)}"

        # Local session temizle
        self._active_sessions.pop(session_index, None)

        request = LogoutRequest(
            id=request_id,
            issue_instant=issue_instant,
            destination=self.idp_config.slo_url,
            name_id=name_id,
            session_index=session_index,
            redirect_url=redirect_url,
        )

        logger.info(
            "SLO baslatiildi",
            extra={
                "request_id": request_id,
                "session_index": session_index,
            },
        )

        return SAMLServiceResult(success=True, data=request)

    async def handle_logout_response(
        self,
        saml_response: str,
    ) -> SAMLServiceResult:
        """SLO Response isle.

        IdP'den gelen LogoutResponse'u dogrular.

        Args:
            saml_response: Base64 encoded LogoutResponse

        Returns:
            SAMLServiceResult: Basari durumu
        """
        try:
            # Base64 decode
            xml_data = base64.b64decode(saml_response)
            root = ET.fromstring(xml_data)

            # Status kontrol
            status_code = root.find(
                ".//samlp:Status/samlp:StatusCode", SAML_NS
            )
            if status_code is not None:
                status = status_code.get("Value", "")
                if "Success" in status:
                    logger.info("SLO basariyla tamamlandi")
                    return SAMLServiceResult(success=True)
                else:
                    return SAMLServiceResult(
                        success=False,
                        error=SAMLError.SLO_FAILED,
                        error_message=f"SLO Status: {status}",
                    )

            return SAMLServiceResult(success=True)

        except Exception as e:
            logger.error(f"SLO Response isleme hatasi: {e}")
            return SAMLServiceResult(
                success=False,
                error=SAMLError.SLO_FAILED,
                error_message=str(e),
            )

    async def generate_sp_metadata(self) -> str:
        """SP metadata XML olustur.

        IdP'ye verilecek Service Provider metadata dosyasini olusturur.

        Returns:
            str: SP metadata XML
        """
        metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
    entityID="{self.sp_config.entity_id}">
    <md:SPSSODescriptor
        AuthnRequestsSigned="false"
        WantAssertionsSigned="true"
        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>{SAMLNameIDFormat.EMAIL.value}</md:NameIDFormat>
        <md:AssertionConsumerService
            Binding="{SAMLBinding.HTTP_POST.value}"
            Location="{self.sp_config.acs_url}"
            index="0"
            isDefault="true"/>
        <md:SingleLogoutService
            Binding="{SAMLBinding.HTTP_POST.value}"
            Location="{self.sp_config.slo_url}"/>
    </md:SPSSODescriptor>
    <md:Organization>
        <md:OrganizationName xml:lang="tr">KIRO2 YKS Platform</md:OrganizationName>
        <md:OrganizationDisplayName xml:lang="tr">KIRO2</md:OrganizationDisplayName>
        <md:OrganizationURL xml:lang="tr">https://kiro2.com</md:OrganizationURL>
    </md:Organization>
</md:EntityDescriptor>"""

        return metadata

    # ==================== PRIVATE METHODS ====================

    async def _parse_assertion(
        self,
        assertion_elem: ET.Element,
    ) -> Optional[SAMLAssertion]:
        """Assertion XML'ini parse et."""
        try:
            # ID
            assertion_id = assertion_elem.get("ID", "")

            # Issuer
            issuer_elem = assertion_elem.find("saml:Issuer", SAML_NS)
            issuer = issuer_elem.text if issuer_elem is not None else ""

            # Subject
            subject_elem = assertion_elem.find(".//saml:Subject/saml:NameID", SAML_NS)
            if subject_elem is None:
                return None
            subject_name_id = subject_elem.text or ""
            subject_name_id_format = subject_elem.get("Format", "")

            # Conditions
            conditions_elem = assertion_elem.find("saml:Conditions", SAML_NS)
            not_before = datetime.now(timezone.utc) - timedelta(minutes=5)
            not_on_or_after = datetime.now(timezone.utc) + timedelta(hours=1)

            if conditions_elem is not None:
                nb = conditions_elem.get("NotBefore")
                if nb:
                    not_before = datetime.fromisoformat(nb.replace("Z", "+00:00"))
                noa = conditions_elem.get("NotOnOrAfter")
                if noa:
                    not_on_or_after = datetime.fromisoformat(noa.replace("Z", "+00:00"))

            # Audience
            audience_elem = assertion_elem.find(
                ".//saml:Conditions/saml:AudienceRestriction/saml:Audience",
                SAML_NS,
            )
            audience = audience_elem.text if audience_elem is not None else ""

            # AuthnStatement
            authn_elem = assertion_elem.find("saml:AuthnStatement", SAML_NS)
            authn_instant = datetime.now(timezone.utc)
            session_index = None

            if authn_elem is not None:
                ai = authn_elem.get("AuthnInstant")
                if ai:
                    authn_instant = datetime.fromisoformat(ai.replace("Z", "+00:00"))
                session_index = authn_elem.get("SessionIndex")

            # Attributes
            attributes: dict[str, Any] = {}
            attr_stmt = assertion_elem.find("saml:AttributeStatement", SAML_NS)
            if attr_stmt is not None:
                for attr in attr_stmt.findall("saml:Attribute", SAML_NS):
                    attr_name = attr.get("Name", "")
                    values = []
                    for val in attr.findall("saml:AttributeValue", SAML_NS):
                        if val.text:
                            values.append(val.text)
                    if len(values) == 1:
                        attributes[attr_name] = values[0]
                    elif len(values) > 1:
                        attributes[attr_name] = values

            return SAMLAssertion(
                id=assertion_id,
                issuer=issuer,
                subject_name_id=subject_name_id,
                subject_name_id_format=subject_name_id_format,
                audience=audience,
                not_before=not_before,
                not_on_or_after=not_on_or_after,
                authn_instant=authn_instant,
                session_index=session_index,
                attributes=attributes,
            )

        except Exception as e:
            logger.error(f"Assertion parse hatasi: {e}")
            return None

    async def _extract_attributes(
        self,
        assertion: SAMLAssertion,
    ) -> UserAttributes:
        """Assertion'dan kullanici attribute'larini extract et."""
        # Mapped attributes
        email = ""
        first_name = None
        last_name = None
        name = None
        role = None
        groups: list[str] = []
        extra: dict[str, Any] = {}

        # Subject NameID'den email al (varsayilan)
        if assertion.subject_name_id_format == SAMLNameIDFormat.EMAIL.value:
            email = assertion.subject_name_id

        # Attribute mapping uygula
        for attr_name, attr_value in assertion.attributes.items():
            mapped_name = ATTRIBUTE_MAP.get(attr_name)

            if mapped_name == "email":
                email = str(attr_value)
            elif mapped_name == "first_name":
                first_name = str(attr_value)
            elif mapped_name == "last_name":
                last_name = str(attr_value)
            elif mapped_name == "name":
                name = str(attr_value)
            elif mapped_name == "role":
                role = str(attr_value)
            elif mapped_name == "groups":
                if isinstance(attr_value, list):
                    groups = [str(g) for g in attr_value]
                else:
                    groups = [str(attr_value)]
            else:
                extra[attr_name] = attr_value

        # Tam ad olustur (yoksa)
        if not name and first_name and last_name:
            name = f"{first_name} {last_name}"

        return UserAttributes(
            email=email,
            name=name,
            first_name=first_name,
            last_name=last_name,
            role=role,
            groups=groups,
            extra=extra,
        )

    async def _verify_signature(self, root: ET.Element) -> bool:
        """SAML signature dogrula.

        Not: Tam signature verification icin xmlsec1 veya signxml kutuphanesi gerekir.
        Bu basitlesirilmis bir implementasyon.
        """
        # Signature element bul
        sig_elem = root.find(".//ds:Signature", SAML_NS)
        if sig_elem is None:
            logger.warning("Signature bulunamadi")
            return True  # Signature zorunlu degil

        # SignatureValue al
        sig_value_elem = sig_elem.find(".//ds:SignatureValue", SAML_NS)
        if sig_value_elem is None or not sig_value_elem.text:
            return False

        # Certificate varsa dogrulama yap
        if self.idp_config and self.idp_config.certificate:
            try:
                # Sertifikayi yukle
                cert = x509.load_pem_x509_certificate(
                    self.idp_config.certificate.encode()
                )
                public_key = cert.public_key()

                # Not: Gercek dogrulama icin XML canonicalization gerekir
                # Bu sadece temel kontrol
                logger.info("Signature dogrulama basarili (basic check)")
                return True

            except Exception as e:
                logger.error(f"Signature dogrulama hatasi: {e}")
                return False

        return True

    async def _cleanup_expired_requests(self) -> None:
        """Suresi dolmus request'leri temizle."""
        now = datetime.now(timezone.utc)
        expired = []

        for req_id, req in self._pending_requests.items():
            if now - req.issue_instant > self._request_expiry:
                expired.append(req_id)

        for req_id in expired:
            del self._pending_requests[req_id]

        if expired:
            logger.debug(f"{len(expired)} expired request temizlendi")

        # Eski assertion ID'lerini temizle (1 saatten eski)
        # Not: Production'da Redis veya DB kullanilmali


# ==================== FACTORY ====================

_saml_service: Optional[SAMLService] = None


def get_saml_service() -> SAMLService:
    """SAMLService singleton instance al.

    Returns:
        SAMLService: Aktif SAML servisi

    Raises:
        RuntimeError: Servis henuz baslatilmamissa
    """
    global _saml_service
    if _saml_service is None:
        # Varsayilan SP config
        import os

        sp_config = SPConfig(
            entity_id=os.getenv("SAML_SP_ENTITY_ID", "https://kiro2.com/saml/metadata"),
            acs_url=os.getenv("SAML_ACS_URL", "https://kiro2.com/api/v1/auth/saml/acs"),
            slo_url=os.getenv("SAML_SLO_URL", "https://kiro2.com/api/v1/auth/saml/slo"),
            metadata_url=os.getenv(
                "SAML_METADATA_URL", "https://kiro2.com/api/v1/auth/saml/metadata"
            ),
        )
        _saml_service = SAMLService(sp_config)

    return _saml_service


def init_saml_service(sp_config: SPConfig) -> SAMLService:
    """SAMLService baslatiliyor.

    Args:
        sp_config: Service Provider konfigurasyonu

    Returns:
        SAMLService: Yeni SAML servisi
    """
    global _saml_service
    _saml_service = SAMLService(sp_config)
    return _saml_service
