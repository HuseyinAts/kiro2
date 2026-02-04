"""
KIRO2 - Payment Gateway Integration System
==========================================

Bu modül, Türkiye'deki ödeme sağlayıcıları ile entegrasyonu sağlar.
Türk bankacılık sistemi, kredi kartları ve dijital ödeme çözümleri desteği.

Desteklenen Ödeme Sağlayıcıları:
- İyzico (Türkiye'nin lider ödeme çözümü)
- PayTR (Türk ödeme sistemi)
- Garanti BBVA POS sistemleri
- İş Bankası POS sistemleri  
- Akbank POS sistemleri
- Ziraat Bankası POS sistemleri
- Halkbank POS sistemleri
- PayPal (uluslararası ödemeler)
- Stripe (global ödeme altyapısı)
- Masterpass (dijital cüzdan)
- BKM Express (Türkiye dijital ödeme)

KVKK uyumlu ödeme veri güvenliği ve PCI DSS sertifikası gereksinimleri.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
from cryptography.fernet import Fernet

from .unified_integration_framework import (
    IntegrationFramework,
    IntegrationType,
    AuthenticationMethod,
    IntegrationConfiguration,
    IntegrationCredentials
)


class PaymentProvider(Enum):
    """Ödeme sağlayıcıları"""
    IYZICO = "iyzico"
    PAYTR = "paytr"
    GARANTI_BBVA = "garanti_bbva"
    IS_BANKASI = "is_bankasi"
    AKBANK = "akbank"
    ZIRAAT = "ziraat"
    HALKBANK = "halkbank"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    MASTERPASS = "masterpass"
    BKM_EXPRESS = "bkm_express"


class PaymentMethod(Enum):
    """Ödeme yöntemleri"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    INSTALLMENT = "installment"
    BKM_EXPRESS = "bkm_express"
    MASTERPASS = "masterpass"
    PAYPAL = "paypal"


class PaymentStatus(Enum):
    """Ödeme durumları"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIAL_REFUNDED = "partial_refunded"


class Currency(Enum):
    """Para birimleri"""
    TRY = "TRY"  # Türk Lirası
    USD = "USD"  # Amerikan Doları
    EUR = "EUR"  # Euro
    GBP = "GBP"  # İngiliz Sterlini


class TransactionType(Enum):
    """İşlem türleri"""
    PAYMENT = "payment"
    REFUND = "refund"
    AUTHORIZATION = "authorization"
    CAPTURE = "capture"
    VOID = "void"


@dataclass
class PaymentCard:
    """Ödeme kartı bilgileri (PCI DSS uyumlu)"""
    card_holder_name: str
    card_number: str  # Şifrelenmiş
    expiry_month: int
    expiry_year: int
    cvv: str  # Şifrelenmiş
    
    def __post_init__(self):
        """Kart bilgilerini doğrula"""
        if not self.card_holder_name.strip():
            raise ValueError("Card holder name is required")
        if self.expiry_month < 1 or self.expiry_month > 12:
            raise ValueError("Invalid expiry month")
        if len(str(self.expiry_year)) != 4:
            raise ValueError("Invalid expiry year")
    
    def get_masked_card_number(self) -> str:
        """Maskelenmiş kart numarası"""
        if len(self.card_number) >= 10:
            return f"{self.card_number[:4]}****{self.card_number[-4:]}"
        return "****"
    
    def is_expired(self) -> bool:
        """Kartın süresinin dolup dolmadığını kontrol et"""
        now = datetime.now()
        expiry_date = datetime(self.expiry_year, self.expiry_month, 1)
        return now > expiry_date


@dataclass
class BillingAddress:
    """Fatura adresi"""
    name: str
    surname: str
    address: str
    city: str
    country: str = "Türkiye"
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class PaymentRequest:
    """Ödeme talebi"""
    transaction_id: str
    amount: Decimal
    currency: Currency
    description: str
    customer_id: str
    customer_email: str
    payment_method: PaymentMethod
    billing_address: BillingAddress
    card_info: Optional[PaymentCard] = None
    installment_count: int = 1
    callback_url: Optional[str] = None
    success_url: Optional[str] = None
    failure_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ödeme talebini doğrula"""
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
        if self.installment_count < 1 or self.installment_count > 12:
            raise ValueError("Invalid installment count")


@dataclass
class PaymentResponse:
    """Ödeme yanıtı"""
    transaction_id: str
    provider_transaction_id: str
    status: PaymentStatus
    amount: Decimal
    currency: Currency
    provider: PaymentProvider
    payment_method: PaymentMethod
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    payment_url: Optional[str] = None  # 3D Secure URL
    authorization_code: Optional[str] = None
    installment_count: int = 1
    provider_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefundRequest:
    """İade talebi"""
    original_transaction_id: str
    refund_amount: Decimal
    reason: str
    refund_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.refund_id:
            self.refund_id = f"refund_{int(time.time())}_{uuid.uuid4().hex[:8]}"


@dataclass 
class RefundResponse:
    """İade yanıtı"""
    refund_id: str
    original_transaction_id: str
    provider_refund_id: str
    status: PaymentStatus
    refund_amount: Decimal
    currency: Currency
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PaymentSecurityManager:
    """Ödeme güvenlik yöneticisi - PCI DSS uyumlu"""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        
    def encrypt_card_data(self, card_data: str) -> str:
        """Kart verilerini şifrele"""
        encrypted = self.cipher.encrypt(card_data.encode())
        return encrypted.decode()
        
    def decrypt_card_data(self, encrypted_data: str) -> str:
        """Şifrelenmiş kart verilerini çöz"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
        
    def hash_sensitive_data(self, data: str) -> str:
        """Hassas verileri hash'le"""
        return hashlib.sha256(data.encode()).hexdigest()
        
    def generate_payment_token(self, payment_request: PaymentRequest) -> str:
        """Ödeme token'ı oluştur"""
        token_data = f"{payment_request.transaction_id}_{payment_request.customer_id}_{int(time.time())}"
        return self.hash_sensitive_data(token_data)


class IyzicoPaymentProvider:
    """İyzico ödeme sağlayıcısı"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        
    def _generate_auth_header(self, request_body: str, uri: str) -> str:
        """İyzico auth header oluştur"""
        random_key = str(uuid.uuid4())
        timestamp = str(int(time.time()))
        
        hash_str = (
            f"{self.api_key}{random_key}{self.secret_key}{request_body}{uri}"
        )
        
        authorization_params = [
            f"apiKey:{self.api_key}",
            f"randomKey:{random_key}",
            f"signature:{hashlib.sha1(hash_str.encode()).hexdigest()}",
            f"timestamp:{timestamp}"
        ]
        
        return f"IYZWSv2 {':'.join(authorization_params)}"
    
    async def process_payment(self, payment_request: PaymentRequest,
                            security_manager: PaymentSecurityManager) -> PaymentResponse:
        """İyzico ile ödeme işle"""
        uri = "/payment/auth"
        
        # İyzico ödeme verilerini hazırla
        iyzico_request = {
            "locale": "tr",
            "conversationId": payment_request.transaction_id,
            "price": str(payment_request.amount),
            "paidPrice": str(payment_request.amount),
            "currency": payment_request.currency.value,
            "installment": payment_request.installment_count,
            "basketId": payment_request.transaction_id,
            "paymentChannel": "WEB",
            "paymentGroup": "PRODUCT",
            "callbackUrl": payment_request.callback_url,
            "buyer": {
                "id": payment_request.customer_id,
                "name": payment_request.billing_address.name,
                "surname": payment_request.billing_address.surname,
                "gsmNumber": payment_request.billing_address.phone,
                "email": payment_request.customer_email,
                "identityNumber": "11111111111",  # Test TC
                "lastLoginDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "registrationDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "registrationAddress": payment_request.billing_address.address,
                "ip": "85.34.78.112",  # Test IP
                "city": payment_request.billing_address.city,
                "country": payment_request.billing_address.country,
                "zipCode": payment_request.billing_address.postal_code or "34732"
            },
            "shippingAddress": {
                "contactName": f"{payment_request.billing_address.name} {payment_request.billing_address.surname}",
                "city": payment_request.billing_address.city,
                "country": payment_request.billing_address.country,
                "address": payment_request.billing_address.address,
                "zipCode": payment_request.billing_address.postal_code or "34732"
            },
            "billingAddress": {
                "contactName": f"{payment_request.billing_address.name} {payment_request.billing_address.surname}",
                "city": payment_request.billing_address.city,
                "country": payment_request.billing_address.country,
                "address": payment_request.billing_address.address,
                "zipCode": payment_request.billing_address.postal_code or "34732"
            },
            "basketItems": [
                {
                    "id": "KIRO2_SUBSCRIPTION",
                    "name": payment_request.description,
                    "category1": "Education",
                    "category2": "Online Learning",
                    "itemType": "VIRTUAL",
                    "price": str(payment_request.amount)
                }
            ]
        }
        
        # Kart bilgilerini ekle
        if payment_request.card_info:
            decrypted_card = security_manager.decrypt_card_data(
                payment_request.card_info.card_number
            )
            decrypted_cvv = security_manager.decrypt_card_data(
                payment_request.card_info.cvv
            )
            
            iyzico_request["paymentCard"] = {
                "cardHolderName": payment_request.card_info.card_holder_name,
                "cardNumber": decrypted_card,
                "expireMonth": f"{payment_request.card_info.expiry_month:02d}",
                "expireYear": f"{payment_request.card_info.expiry_year}",
                "cvc": decrypted_cvv,
                "registerCard": 0
            }
        
        request_body = json.dumps(iyzico_request, ensure_ascii=False)
        auth_header = self._generate_auth_header(request_body, uri)
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{uri}",
                    data=request_body.encode('utf-8'),
                    headers=headers
                ) as response:
                    response_data = await response.json()
                    
                    # İyzico yanıtını parse et
                    if response_data.get("status") == "success":
                        status = PaymentStatus.SUCCESS
                        if response_data.get("threeDSHtmlContent"):
                            status = PaymentStatus.PROCESSING
                    else:
                        status = PaymentStatus.FAILED
                    
                    return PaymentResponse(
                        transaction_id=payment_request.transaction_id,
                        provider_transaction_id=response_data.get("paymentId", ""),
                        status=status,
                        amount=payment_request.amount,
                        currency=payment_request.currency,
                        provider=PaymentProvider.IYZICO,
                        payment_method=payment_request.payment_method,
                        created_at=datetime.now(),
                        processed_at=datetime.now() if status == PaymentStatus.SUCCESS else None,
                        error_message=response_data.get("errorMessage"),
                        error_code=response_data.get("errorCode"),
                        payment_url=response_data.get("threeDSHtmlContent"),
                        authorization_code=response_data.get("authCode"),
                        installment_count=payment_request.installment_count,
                        provider_response=response_data
                    )
                    
        except Exception as e:
            return PaymentResponse(
                transaction_id=payment_request.transaction_id,
                provider_transaction_id="",
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                provider=PaymentProvider.IYZICO,
                payment_method=payment_request.payment_method,
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    async def process_refund(self, refund_request: RefundRequest) -> RefundResponse:
        """İyzico ile iade işle"""
        uri = "/payment/refund"
        
        iyzico_refund = {
            "locale": "tr",
            "conversationId": refund_request.refund_id,
            "paymentTransactionId": refund_request.original_transaction_id,
            "price": str(refund_request.refund_amount),
            "reason": refund_request.reason
        }
        
        request_body = json.dumps(iyzico_refund, ensure_ascii=False)
        auth_header = self._generate_auth_header(request_body, uri)
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{uri}",
                    data=request_body.encode('utf-8'),
                    headers=headers
                ) as response:
                    response_data = await response.json()
                    
                    status = (PaymentStatus.REFUNDED 
                             if response_data.get("status") == "success"
                             else PaymentStatus.FAILED)
                    
                    return RefundResponse(
                        refund_id=refund_request.refund_id,
                        original_transaction_id=refund_request.original_transaction_id,
                        provider_refund_id=response_data.get("paymentId", ""),
                        status=status,
                        refund_amount=refund_request.refund_amount,
                        currency=Currency.TRY,
                        created_at=datetime.now(),
                        processed_at=datetime.now() if status == PaymentStatus.REFUNDED else None,
                        error_message=response_data.get("errorMessage")
                    )
                    
        except Exception as e:
            return RefundResponse(
                refund_id=refund_request.refund_id,
                original_transaction_id=refund_request.original_transaction_id,
                provider_refund_id="",
                status=PaymentStatus.FAILED,
                refund_amount=refund_request.refund_amount,
                currency=Currency.TRY,
                created_at=datetime.now(),
                error_message=str(e)
            )


class PayTRPaymentProvider:
    """PayTR ödeme sağlayıcısı"""
    
    def __init__(self, merchant_id: str, merchant_key: str, merchant_salt: str, base_url: str):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.merchant_salt = merchant_salt
        self.base_url = base_url
    
    def _generate_token(self, payment_request: PaymentRequest) -> str:
        """PayTR token oluştur"""
        hash_str = (
            f"{self.merchant_id}{payment_request.customer_email}"
            f"{payment_request.transaction_id}{int(payment_request.amount * 100)}"
            f"{payment_request.currency.value}{payment_request.success_url}"
            f"{payment_request.failure_url}{self.merchant_salt}"
        )
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    async def process_payment(self, payment_request: PaymentRequest,
                            security_manager: PaymentSecurityManager) -> PaymentResponse:
        """PayTR ile ödeme işle"""
        token = self._generate_token(payment_request)
        
        paytr_data = {
            "merchant_id": self.merchant_id,
            "user_ip": "85.34.78.112",  # Test IP
            "merchant_oid": payment_request.transaction_id,
            "email": payment_request.customer_email,
            "payment_amount": int(payment_request.amount * 100),  # Kuruş cinsinden
            "currency": payment_request.currency.value,
            "test_mode": "1",  # Test modu
            "non_3d": "0",  # 3D Secure zorunlu
            "merchant_ok_url": payment_request.success_url,
            "merchant_fail_url": payment_request.failure_url,
            "user_name": f"{payment_request.billing_address.name} {payment_request.billing_address.surname}",
            "user_address": payment_request.billing_address.address,
            "user_phone": payment_request.billing_address.phone or "05551234567",
            "user_basket": json.dumps([
                [payment_request.description, str(payment_request.amount), 1]
            ]),
            "debug_on": "1",
            "installment_count": payment_request.installment_count,
            "paytr_token": token
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/odeme/api/get-token",
                    data=paytr_data
                ) as response:
                    response_text = await response.text()
                    
                    if response_text.startswith("TOKEN:"):
                        payment_token = response_text.split(":")[1]
                        payment_url = f"{self.base_url}/odeme/guvenli/{payment_token}"
                        
                        return PaymentResponse(
                            transaction_id=payment_request.transaction_id,
                            provider_transaction_id=payment_token,
                            status=PaymentStatus.PROCESSING,
                            amount=payment_request.amount,
                            currency=payment_request.currency,
                            provider=PaymentProvider.PAYTR,
                            payment_method=payment_request.payment_method,
                            created_at=datetime.now(),
                            payment_url=payment_url,
                            installment_count=payment_request.installment_count
                        )
                    else:
                        return PaymentResponse(
                            transaction_id=payment_request.transaction_id,
                            provider_transaction_id="",
                            status=PaymentStatus.FAILED,
                            amount=payment_request.amount,
                            currency=payment_request.currency,
                            provider=PaymentProvider.PAYTR,
                            payment_method=payment_request.payment_method,
                            created_at=datetime.now(),
                            error_message=response_text
                        )
                        
        except Exception as e:
            return PaymentResponse(
                transaction_id=payment_request.transaction_id,
                provider_transaction_id="",
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                provider=PaymentProvider.PAYTR,
                payment_method=payment_request.payment_method,
                created_at=datetime.now(),
                error_message=str(e)
            )


class PaymentGatewayIntegration:
    """Ödeme Geçidi Entegrasyon Sistemi"""
    
    def __init__(self):
        self.providers: Dict[PaymentProvider, Any] = {}
        self.security_manager: Optional[PaymentSecurityManager] = None
        self.integration_framework = IntegrationFramework()
        self.transaction_log: List[PaymentResponse] = []
        self.logger = logging.getLogger("payment_gateway")
        
        # Fraud detection basit kurallar
        self.fraud_rules = {
            "max_amount_per_hour": Decimal("5000.00"),
            "max_transactions_per_hour": 10,
            "blocked_countries": ["XX", "YY"],  # Test ülke kodları
            "min_card_age_months": 3
        }
        
    async def initialize(self, encryption_key: bytes):
        """Ödeme entegrasyonunu başlat"""
        self.security_manager = PaymentSecurityManager(encryption_key)
        
        # Integration framework'ü yapılandır
        for provider in PaymentProvider:
            integration_config = IntegrationConfiguration(
                name=f"payment_{provider.value}",
                integration_type=IntegrationType.PAYMENT_GATEWAY,
                base_url="https://api.payment-provider.com",  # Placeholder
                authentication_method=AuthenticationMethod.API_KEY,
                rate_limit_per_minute=60,
                timeout=30,
                max_retries=3
            )
            
            await self.integration_framework.register_integration(
                provider.value, integration_config
            )
        
        self.logger.info("Payment Gateway Integration initialized")
    
    def add_provider(self, provider: PaymentProvider, provider_instance: Any):
        """Ödeme sağlayıcısı ekle"""
        self.providers[provider] = provider_instance
        self.logger.info(f"Added payment provider: {provider.value}")
    
    def _check_fraud_rules(self, payment_request: PaymentRequest) -> List[str]:
        """Dolandırıcılık kurallarını kontrol et"""
        violations = []
        
        # Miktar kontrolü
        if payment_request.amount > self.fraud_rules["max_amount_per_hour"]:
            violations.append(f"Amount exceeds hourly limit: {self.fraud_rules['max_amount_per_hour']}")
        
        # Ülke kontrolü  
        if payment_request.billing_address.country in self.fraud_rules["blocked_countries"]:
            violations.append(f"Blocked country: {payment_request.billing_address.country}")
        
        # Saatlik işlem kontrolü
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_transactions = [
            t for t in self.transaction_log 
            if t.created_at > hour_ago and 
               t.status in [PaymentStatus.SUCCESS, PaymentStatus.PROCESSING]
        ]
        
        if len(recent_transactions) >= self.fraud_rules["max_transactions_per_hour"]:
            violations.append("Too many transactions in the last hour")
        
        return violations
    
    async def process_payment(self, payment_request: PaymentRequest,
                            preferred_provider: Optional[PaymentProvider] = None) -> PaymentResponse:
        """Ödeme işle"""
        if not self.security_manager:
            raise Exception("Payment gateway not initialized")
        
        # Fraud kontrolü
        fraud_violations = self._check_fraud_rules(payment_request)
        if fraud_violations:
            self.logger.warning(f"Fraud violations detected: {fraud_violations}")
            return PaymentResponse(
                transaction_id=payment_request.transaction_id,
                provider_transaction_id="",
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                provider=preferred_provider or PaymentProvider.IYZICO,
                payment_method=payment_request.payment_method,
                created_at=datetime.now(),
                error_message=f"Payment blocked: {', '.join(fraud_violations)}"
            )
        
        # Sağlayıcı seç
        if preferred_provider and preferred_provider in self.providers:
            provider = preferred_provider
        else:
            # Varsayılan sağlayıcı seçimi (Türkiye için İyzico)
            if payment_request.currency == Currency.TRY:
                provider = PaymentProvider.IYZICO
            else:
                provider = PaymentProvider.STRIPE
        
        if provider not in self.providers:
            return PaymentResponse(
                transaction_id=payment_request.transaction_id,
                provider_transaction_id="",
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                provider=provider,
                payment_method=payment_request.payment_method,
                created_at=datetime.now(),
                error_message=f"Provider {provider.value} not configured"
            )
        
        # Kart bilgilerini şifrele
        if payment_request.card_info:
            if not payment_request.card_info.card_number.startswith("enc_"):
                payment_request.card_info.card_number = (
                    "enc_" + self.security_manager.encrypt_card_data(
                        payment_request.card_info.card_number
                    )
                )
            if not payment_request.card_info.cvv.startswith("enc_"):
                payment_request.card_info.cvv = (
                    "enc_" + self.security_manager.encrypt_card_data(
                        payment_request.card_info.cvv
                    )
                )
        
        # Ödeme işle
        try:
            provider_instance = self.providers[provider]
            response = await provider_instance.process_payment(
                payment_request, self.security_manager
            )
            
            # Başarılı işlemleri günlükle
            self.transaction_log.append(response)
            if len(self.transaction_log) > 1000:  # Son 1000 işlemi tut
                self.transaction_log = self.transaction_log[-1000:]
            
            # Audit log
            self.logger.info(
                f"Payment processed - ID: {response.transaction_id}, "
                f"Status: {response.status.value}, "
                f"Provider: {response.provider.value}, "
                f"Amount: {response.amount} {response.currency.value}"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Payment processing failed: {e}")
            return PaymentResponse(
                transaction_id=payment_request.transaction_id,
                provider_transaction_id="",
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                provider=provider,
                payment_method=payment_request.payment_method,
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    async def process_refund(self, refund_request: RefundRequest,
                           provider: PaymentProvider) -> RefundResponse:
        """İade işle"""
        if provider not in self.providers:
            return RefundResponse(
                refund_id=refund_request.refund_id,
                original_transaction_id=refund_request.original_transaction_id,
                provider_refund_id="",
                status=PaymentStatus.FAILED,
                refund_amount=refund_request.refund_amount,
                currency=Currency.TRY,
                created_at=datetime.now(),
                error_message=f"Provider {provider.value} not configured"
            )
        
        try:
            provider_instance = self.providers[provider]
            response = await provider_instance.process_refund(refund_request)
            
            self.logger.info(
                f"Refund processed - ID: {response.refund_id}, "
                f"Status: {response.status.value}, "
                f"Amount: {response.refund_amount}"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Refund processing failed: {e}")
            return RefundResponse(
                refund_id=refund_request.refund_id,
                original_transaction_id=refund_request.original_transaction_id,
                provider_refund_id="",
                status=PaymentStatus.FAILED,
                refund_amount=refund_request.refund_amount,
                currency=Currency.TRY,
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def get_transaction_history(self, customer_id: Optional[str] = None,
                              limit: int = 100) -> List[PaymentResponse]:
        """İşlem geçmişi al"""
        transactions = self.transaction_log
        
        if customer_id:
            transactions = [
                t for t in transactions 
                if t.provider_response.get("customer_id") == customer_id
            ]
        
        return sorted(transactions, key=lambda x: x.created_at, reverse=True)[:limit]
    
    async def get_payment_methods_for_kiro2(self, currency: Currency,
                                          amount: Decimal) -> List[Dict[str, Any]]:
        """KIRO2 için uygun ödeme yöntemlerini al"""
        methods = []
        
        if currency == Currency.TRY:
            # Türk Lirası için mevcut yöntemler
            methods.extend([
                {
                    "method": PaymentMethod.CREDIT_CARD.value,
                    "provider": PaymentProvider.IYZICO.value,
                    "name": "Kredi Kartı",
                    "description": "Visa, MasterCard, Troy kartlarınızla güvenle ödeme",
                    "installment_options": [1, 2, 3, 6, 9, 12] if amount >= 100 else [1],
                    "fee_percentage": 2.95,
                    "processing_time": "Anında"
                },
                {
                    "method": PaymentMethod.BKM_EXPRESS.value,
                    "provider": PaymentProvider.BKM_EXPRESS.value,
                    "name": "BKM Express",
                    "description": "Türkiye'nin dijital ödeme sistemi",
                    "installment_options": [1],
                    "fee_percentage": 1.95,
                    "processing_time": "Anında"
                },
                {
                    "method": PaymentMethod.BANK_TRANSFER.value,
                    "provider": PaymentProvider.ZIRAAT.value,
                    "name": "Banka Havalesi",
                    "description": "EFT/Havale ile ödeme",
                    "installment_options": [1],
                    "fee_percentage": 0.0,
                    "processing_time": "1-2 İş Günü"
                }
            ])
        
        # Uluslararası ödeme yöntemleri
        if currency in [Currency.USD, Currency.EUR]:
            methods.extend([
                {
                    "method": PaymentMethod.PAYPAL.value,
                    "provider": PaymentProvider.PAYPAL.value,
                    "name": "PayPal",
                    "description": "Güvenli uluslararası ödeme",
                    "installment_options": [1],
                    "fee_percentage": 3.49,
                    "processing_time": "Anında"
                },
                {
                    "method": PaymentMethod.CREDIT_CARD.value,
                    "provider": PaymentProvider.STRIPE.value,
                    "name": "International Credit Card",
                    "description": "Visa, MasterCard, Amex",
                    "installment_options": [1],
                    "fee_percentage": 2.99,
                    "processing_time": "Anında"
                }
            ])
        
        return methods
    
    def calculate_kiro2_subscription_pricing(self, base_price: Decimal,
                                           duration_months: int,
                                           payment_method: PaymentMethod,
                                           installments: int = 1) -> Dict[str, Any]:
        """KIRO2 abonelik fiyatlandırması hesapla"""
        # Süre indirimleri
        duration_discounts = {
            1: 0.0,    # Aylık
            3: 0.10,   # 3 aylık %10 indirim  
            6: 0.15,   # 6 aylık %15 indirim
            12: 0.25   # Yıllık %25 indirim
        }
        
        discount = duration_discounts.get(duration_months, 0.0)
        discounted_price = base_price * (1 - discount)
        total_price = discounted_price * duration_months
        
        # Ödeme yöntemi ücretleri
        fee_percentage = 0.0
        if payment_method == PaymentMethod.CREDIT_CARD:
            fee_percentage = 2.95
        elif payment_method == PaymentMethod.BKM_EXPRESS:
            fee_percentage = 1.95
        elif payment_method == PaymentMethod.PAYPAL:
            fee_percentage = 3.49
        
        payment_fee = total_price * (fee_percentage / 100)
        final_price = total_price + payment_fee
        
        # Taksit hesaplaması
        installment_amount = final_price / installments if installments > 1 else final_price
        
        return {
            "base_price": float(base_price),
            "duration_months": duration_months,
            "discount_percentage": discount * 100,
            "discounted_monthly_price": float(discounted_price),
            "subtotal": float(total_price),
            "payment_fee": float(payment_fee),
            "fee_percentage": fee_percentage,
            "final_price": float(final_price),
            "installments": installments,
            "installment_amount": float(installment_amount),
            "currency": "TRY",
            "savings": float(base_price * duration_months - total_price) if discount > 0 else 0
        }


class KIRO2PaymentManager:
    """KIRO2 Ödeme Yöneticisi"""
    
    def __init__(self):
        self.gateway = PaymentGatewayIntegration()
        self.initialized = False
        
        # KIRO2 abonelik planları
        self.subscription_plans = {
            "basic": {
                "name": "Temel Plan",
                "monthly_price": Decimal("29.90"),
                "features": ["TYT Hazırlık", "Temel Sorular", "Video Dersler"]
            },
            "premium": {
                "name": "Premium Plan", 
                "monthly_price": Decimal("49.90"),
                "features": ["TYT + AYT Hazırlık", "Tüm Sorular", "Canlı Dersler", "Kişisel Mentor"]
            },
            "ultimate": {
                "name": "Ultimate Plan",
                "monthly_price": Decimal("79.90"),
                "features": ["Tüm İçerik", "1-1 Özel Ders", "Sınırsız Deneme", "Üniversite Danışmanlığı"]
            }
        }
    
    async def initialize_for_kiro2(self, payment_credentials: Dict[str, Dict[str, str]],
                                 encryption_key: bytes):
        """KIRO2 için ödeme sistemini başlat"""
        await self.gateway.initialize(encryption_key)
        
        # İyzico sağlayıcısı ekle
        if "iyzico" in payment_credentials:
            creds = payment_credentials["iyzico"]
            iyzico_provider = IyzicoPaymentProvider(
                api_key=creds["api_key"],
                secret_key=creds["secret_key"],
                base_url=creds.get("base_url", "https://sandbox-api.iyzipay.com")
            )
            self.gateway.add_provider(PaymentProvider.IYZICO, iyzico_provider)
        
        # PayTR sağlayıcısı ekle
        if "paytr" in payment_credentials:
            creds = payment_credentials["paytr"]
            paytr_provider = PayTRPaymentProvider(
                merchant_id=creds["merchant_id"],
                merchant_key=creds["merchant_key"],
                merchant_salt=creds["merchant_salt"],
                base_url=creds.get("base_url", "https://www.paytr.com")
            )
            self.gateway.add_provider(PaymentProvider.PAYTR, paytr_provider)
        
        self.initialized = True
        logging.info("KIRO2 Payment Manager initialized")
    
    async def create_subscription_payment(self, customer_id: str, customer_email: str,
                                        plan: str, duration_months: int,
                                        billing_address: BillingAddress,
                                        card_info: Optional[PaymentCard] = None,
                                        payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD,
                                        installments: int = 1) -> PaymentResponse:
        """KIRO2 abonelik ödemesi oluştur"""
        if not self.initialized:
            raise Exception("Payment manager not initialized")
        
        if plan not in self.subscription_plans:
            raise ValueError(f"Invalid subscription plan: {plan}")
        
        plan_info = self.subscription_plans[plan]
        pricing = self.gateway.calculate_kiro2_subscription_pricing(
            base_price=plan_info["monthly_price"],
            duration_months=duration_months,
            payment_method=payment_method,
            installments=installments
        )
        
        # Ödeme talebi oluştur
        transaction_id = f"kiro2_sub_{customer_id}_{int(time.time())}"
        
        payment_request = PaymentRequest(
            transaction_id=transaction_id,
            amount=Decimal(str(pricing["final_price"])),
            currency=Currency.TRY,
            description=f"KIRO2 {plan_info['name']} - {duration_months} Ay",
            customer_id=customer_id,
            customer_email=customer_email,
            payment_method=payment_method,
            billing_address=billing_address,
            card_info=card_info,
            installment_count=installments,
            success_url="https://kiro2.com/payment/success",
            failure_url="https://kiro2.com/payment/failure",
            callback_url="https://kiro2.com/payment/callback",
            metadata={
                "plan": plan,
                "duration_months": duration_months,
                "pricing_breakdown": pricing
            }
        )
        
        # Ödemeyi işle
        return await self.gateway.process_payment(payment_request)
    
    def get_subscription_pricing(self, plan: str, duration_months: int,
                               payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD,
                               installments: int = 1) -> Dict[str, Any]:
        """Abonelik fiyatlandırmasını al"""
        if plan not in self.subscription_plans:
            raise ValueError(f"Invalid subscription plan: {plan}")
        
        plan_info = self.subscription_plans[plan]
        pricing = self.gateway.calculate_kiro2_subscription_pricing(
            base_price=plan_info["monthly_price"],
            duration_months=duration_months,
            payment_method=payment_method,
            installments=installments
        )
        
        pricing["plan_info"] = plan_info
        return pricing
    
    async def get_available_payment_methods(self) -> List[Dict[str, Any]]:
        """Mevcut ödeme yöntemlerini al"""
        return await self.gateway.get_payment_methods_for_kiro2(
            Currency.TRY, Decimal("50.00")
        )


# === Örnek Kullanım ===

async def example_payment_integration():
    """Ödeme entegrasyonu örnek kullanımı"""
    
    # Ödeme yöneticisini başlat
    manager = KIRO2PaymentManager()
    
    # Kimlik bilgileri
    credentials = {
        "iyzico": {
            "api_key": "sandbox-test-api-key",
            "secret_key": "sandbox-test-secret-key",
            "base_url": "https://sandbox-api.iyzipay.com"
        },
        "paytr": {
            "merchant_id": "test-merchant-id",
            "merchant_key": "test-merchant-key", 
            "merchant_salt": "test-merchant-salt"
        }
    }
    
    encryption_key = Fernet.generate_key()
    
    await manager.initialize_for_kiro2(credentials, encryption_key)
    
    # Fatura adresi
    billing_address = BillingAddress(
        name="Ahmet",
        surname="Yılmaz",
        address="Test Mahallesi, Test Sokak No: 1",
        city="İstanbul",
        country="Türkiye",
        postal_code="34000",
        phone="05551234567",
        email="ahmet@test.com"
    )
    
    # Kart bilgileri (test)
    card_info = PaymentCard(
        card_holder_name="AHMET YILMAZ",
        card_number="5528790000000008",  # Test kart
        expiry_month=12,
        expiry_year=2030,
        cvv="123"
    )
    
    # Abonelik fiyatlandırması
    pricing = manager.get_subscription_pricing(
        plan="premium",
        duration_months=6,
        payment_method=PaymentMethod.CREDIT_CARD,
        installments=3
    )
    
    print("KIRO2 Premium Plan - 6 Aylık:")
    print(f"Temel Fiyat: {pricing['base_price']} TL/ay")
    print(f"İndirim: %{pricing['discount_percentage']}")
    print(f"Alt Toplam: {pricing['subtotal']} TL")
    print(f"Ödeme Ücreti: {pricing['payment_fee']} TL")
    print(f"Toplam: {pricing['final_price']} TL")
    print(f"Taksit: {pricing['installments']}x{pricing['installment_amount']:.2f} TL")
    print(f"Tasarruf: {pricing['savings']} TL")
    
    # Ödeme oluştur
    payment_response = await manager.create_subscription_payment(
        customer_id="kiro2_user_12345",
        customer_email="ahmet@test.com",
        plan="premium",
        duration_months=6,
        billing_address=billing_address,
        card_info=card_info,
        payment_method=PaymentMethod.CREDIT_CARD,
        installments=3
    )
    
    print(f"\nÖdeme Durumu: {payment_response.status.value}")
    print(f"İşlem ID: {payment_response.transaction_id}")
    if payment_response.payment_url:
        print(f"3D Secure URL: {payment_response.payment_url}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_payment_integration())