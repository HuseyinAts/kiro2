"""
KIRO2 - Turkish Education Ministry (MEB) API Integration
========================================================

Bu modül, Türkiye Millî Eğitim Bakanlığı (MEB) API'leri ile entegrasyonu sağlar.
MEB e-Okul, MEBBİS, FATİH projesi ve diğer eğitim sistemleri ile bağlantı kurar.

Desteklenen MEB Sistemleri:
- e-Okul Sistemi (Öğrenci bilgileri, notlar, devamsızlık)
- MEBBİS (Öğretmen ve okul yönetimi)
- FATİH Projesi (Dijital içerik ve etkileşimli tahta)
- MEB Akademi (Öğretmen geliştirme programları)
- EBA (Eğitim Bilişim Ağı) entegrasyonu
- ÖSYM (Öğrenci Seçme ve Yerleştirme Merkezi) bağlantısı

KVKK uyumlu veri işleme ve güvenlik önlemleri içerir.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin

import aiohttp
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .unified_integration_framework import (
    IntegrationFramework,
    IntegrationType,
    AuthenticationMethod,
    IntegrationConfiguration,
    IntegrationCredentials
)


class MEBSystem(Enum):
    """MEB Sistemleri enum class'ı"""
    E_OKUL = "e_okul"                      # e-Okul Sistemi
    MEBBIS = "mebbis"                      # MEBBİS - Öğretmen/Okul Yönetimi
    FATIH = "fatih"                        # FATİH Projesi
    MEB_AKADEMI = "meb_akademi"            # MEB Akademi
    EBA = "eba"                            # Eğitim Bilişim Ağı
    OSYM_BRIDGE = "osym_bridge"            # ÖSYM Bağlantı Köprüsü
    STUDENT_PORTAL = "student_portal"      # Öğrenci Portalı
    TEACHER_PORTAL = "teacher_portal"      # Öğretmen Portalı
    PARENT_PORTAL = "parent_portal"        # Veli Portalı


class MEBEndpointType(Enum):
    """MEB API endpoint türleri"""
    AUTHENTICATION = "auth"
    STUDENT_INFO = "student_info"
    ACADEMIC_RECORDS = "academic_records"
    ATTENDANCE = "attendance"
    EXAM_RESULTS = "exam_results"
    TEACHER_INFO = "teacher_info"
    SCHOOL_INFO = "school_info"
    CURRICULUM = "curriculum"
    DIGITAL_CONTENT = "digital_content"
    COMMUNICATION = "communication"


class StudentType(Enum):
    """Öğrenci türleri"""
    PRIMARY = "ilkokul"
    MIDDLE = "ortaokul"
    HIGH = "lise"
    VOCATIONAL = "meslek_lisesi"
    IMAM_HATIP = "imam_hatip"
    OPEN_HIGH = "acik_lise"


class ExamType(Enum):
    """Sınav türleri"""
    LGS = "lgs"                           # Liselere Geçiş Sınavı
    YKS = "yks"                           # Yükseköğretim Kurumları Sınavı
    TYT = "tyt"                           # Temel Yeterlilik Testi
    AYT = "ayt"                           # Alan Yeterlilik Testi
    MSU = "msu"                           # Mesleki ve Teknik Eğitim Sınavı
    DGS = "dgs"                           # Dikey Geçiş Sınavı
    ALES = "ales"                         # Akademik Personel ve Lisansüstü Eğitimi Giriş Sınavı
    KPSS = "kpss"                         # Kamu Personeli Seçme Sınavı


@dataclass
class MEBCredentials:
    """MEB API kimlik bilgileri"""
    system: MEBSystem
    api_key: str
    secret_key: str
    institution_code: str
    user_id: Optional[str] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    environment: str = "production"  # production, test, sandbox
    
    
@dataclass
class MEBConfiguration:
    """MEB entegrasyon yapılandırması"""
    base_urls: Dict[MEBSystem, str] = field(default_factory=lambda: {
        MEBSystem.E_OKUL: "https://e-okul.meb.gov.tr/api/v2",
        MEBSystem.MEBBIS: "https://mebbis.meb.gov.tr/api/v1",
        MEBSystem.FATIH: "https://fatih.meb.gov.tr/api/v1",
        MEBSystem.MEB_AKADEMI: "https://akademi.meb.gov.tr/api/v1",
        MEBSystem.EBA: "https://eba.gov.tr/api/v2",
        MEBSystem.OSYM_BRIDGE: "https://osym-bridge.meb.gov.tr/api/v1",
        MEBSystem.STUDENT_PORTAL: "https://ogrenci.meb.gov.tr/api/v1",
        MEBSystem.TEACHER_PORTAL: "https://ogretmen.meb.gov.tr/api/v1",
        MEBSystem.PARENT_PORTAL: "https://veli.meb.gov.tr/api/v1"
    })
    
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 100
    cache_ttl: int = 300  # 5 dakika
    kvkk_compliance: bool = True  # KVKK uyumluluk kontrolü
    data_encryption: bool = True  # Veri şifreleme
    audit_logging: bool = True    # Denetim günlükleme


@dataclass
class StudentInfo:
    """Öğrenci bilgi modeli"""
    tc_no: str  # KVKK korumalı
    student_no: str
    name: str
    surname: str
    birth_date: datetime
    student_type: StudentType
    school_code: str
    school_name: str
    class_level: int
    class_branch: str
    parent_tc_no: Optional[str] = None  # KVKK korumalı
    parent_name: Optional[str] = None
    phone: Optional[str] = None  # KVKV korumalı
    email: Optional[str] = None  # KVKK korumalı
    address: Optional[str] = None  # KVKK korumalı
    
    def anonymize(self) -> 'StudentInfo':
        """KVKK uyumlu anonimleştirme"""
        anonymized = StudentInfo(
            tc_no="***masked***",
            student_no=self.student_no,
            name=self.name[0] + "*" * (len(self.name) - 1),
            surname=self.surname[0] + "*" * (len(self.surname) - 1),
            birth_date=datetime(self.birth_date.year, 1, 1),
            student_type=self.student_type,
            school_code=self.school_code,
            school_name=self.school_name,
            class_level=self.class_level,
            class_branch=self.class_branch,
            parent_tc_no="***masked***" if self.parent_tc_no else None,
            parent_name=self.parent_name[0] + "*" * (len(self.parent_name) - 1) if self.parent_name else None,
            phone="***masked***" if self.phone else None,
            email="***masked***" if self.email else None,
            address="***masked***" if self.address else None
        )
        return anonymized


@dataclass
class AcademicRecord:
    """Akademik kayıt modeli"""
    student_no: str
    subject: str
    semester: int
    year: int
    grade: float
    grade_type: str  # yazılı, sözlü, proje, vs.
    teacher_name: str
    exam_date: datetime
    weight: float = 1.0
    
    
@dataclass
class AttendanceRecord:
    """Devamsızlık kaydı modeli"""
    student_no: str
    date: datetime
    status: str  # devam, devamsız, geç kalma, erken çıkış
    lesson: str
    teacher_name: str
    excuse_status: Optional[str] = None  # mazeret durumu
    excuse_document: Optional[str] = None


@dataclass
class ExamResult:
    """Sınav sonuç modeli"""
    student_no: str
    exam_type: ExamType
    exam_year: int
    scores: Dict[str, float]  # Alan bazında puanlar
    ranking: Optional[int] = None
    percentile: Optional[float] = None
    university_preferences: Optional[List[str]] = None
    placement_result: Optional[str] = None


class KVKKDataProtector:
    """KVKK uyumlu veri koruma sınıfı"""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.ECB()
        )
        
    def encrypt_personal_data(self, data: str) -> str:
        """Kişisel verileri şifrele"""
        encryptor = self.cipher.encryptor()
        padded_data = data.ljust((len(data) // 16 + 1) * 16)
        encrypted = encryptor.update(padded_data.encode()) + encryptor.finalize()
        return encrypted.hex()
        
    def decrypt_personal_data(self, encrypted_data: str) -> str:
        """Şifrelenmiş kişisel verileri çöz"""
        decryptor = self.cipher.decryptor()
        encrypted_bytes = bytes.fromhex(encrypted_data)
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
        return decrypted.decode().strip()


class MEBAuditLogger:
    """MEB API denetim günlükleme"""
    
    def __init__(self, logger_name: str = "meb_api"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
    def log_api_call(self, system: MEBSystem, endpoint: str, user_id: str, 
                    success: bool, response_time: float, data_accessed: List[str]):
        """API çağrısını günlükle"""
        self.logger.info(f"MEB API Call - System: {system.value}, "
                        f"Endpoint: {endpoint}, User: {user_id}, "
                        f"Success: {success}, Time: {response_time}ms, "
                        f"Data: {data_accessed}")
        
    def log_data_access(self, user_id: str, student_tc: str, 
                       data_type: str, purpose: str):
        """Veri erişimini günlükle (KVKK uyumlu)"""
        masked_tc = student_tc[:3] + "*" * 8 + student_tc[-2:]
        self.logger.info(f"Data Access - User: {user_id}, "
                        f"Student: {masked_tc}, Type: {data_type}, "
                        f"Purpose: {purpose}")


class MEBAPIIntegration:
    """MEB API Entegrasyon Ana Sınıfı"""
    
    def __init__(self, config: MEBConfiguration):
        self.config = config
        self.credentials: Dict[MEBSystem, MEBCredentials] = {}
        self.audit_logger = MEBAuditLogger()
        self.integration_framework = IntegrationFramework()
        self.kvkk_protector = None
        self.session_cache: Dict[str, Any] = {}
        
        # Rate limiting
        self.rate_limits: Dict[MEBSystem, List[datetime]] = {
            system: [] for system in MEBSystem
        }
        
    async def initialize(self, encryption_key: Optional[bytes] = None):
        """Entegrasyonu başlat"""
        if encryption_key and self.config.data_encryption:
            self.kvkk_protector = KVKKDataProtector(encryption_key)
            
        # Integration framework'ü yapılandır
        for system in MEBSystem:
            integration_config = IntegrationConfiguration(
                name=f"meb_{system.value}",
                integration_type=IntegrationType.GOVERNMENT_API,
                base_url=self.config.base_urls[system],
                authentication_method=AuthenticationMethod.HMAC_SIGNATURE,
                rate_limit_per_minute=self.config.rate_limit_per_minute,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries
            )
            
            await self.integration_framework.register_integration(
                system.value, integration_config
            )
    
    def add_credentials(self, system: MEBSystem, credentials: MEBCredentials):
        """Sistem kimlik bilgilerini ekle"""
        self.credentials[system] = credentials
        
        # Integration framework'e kimlik bilgilerini ekle
        framework_credentials = IntegrationCredentials(
            api_key=credentials.api_key,
            secret_key=credentials.secret_key,
            additional_fields={
                "institution_code": credentials.institution_code,
                "user_id": credentials.user_id,
                "environment": credentials.environment
            }
        )
        
        self.integration_framework.integrations[system.value].credentials = framework_credentials
        
    def _check_rate_limit(self, system: MEBSystem) -> bool:
        """Rate limit kontrolü"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Eski kayıtları temizle
        self.rate_limits[system] = [
            timestamp for timestamp in self.rate_limits[system]
            if timestamp > minute_ago
        ]
        
        if len(self.rate_limits[system]) >= self.config.rate_limit_per_minute:
            return False
            
        self.rate_limits[system].append(now)
        return True
        
    def _generate_hmac_signature(self, system: MEBSystem, data: str) -> str:
        """HMAC imzası oluştur"""
        credentials = self.credentials[system]
        signature = hmac.new(
            credentials.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
        
    async def _make_api_call(self, system: MEBSystem, endpoint: MEBEndpointType,
                           method: str = "GET", data: Optional[Dict] = None,
                           params: Optional[Dict] = None) -> Dict:
        """MEB API çağrısı yap"""
        if not self._check_rate_limit(system):
            raise Exception(f"Rate limit exceeded for {system.value}")
            
        credentials = self.credentials[system]
        base_url = self.config.base_urls[system]
        url = urljoin(base_url, endpoint.value)
        
        # HMAC imzası için veri hazırla
        timestamp = str(int(time.time()))
        request_data = json.dumps(data) if data else ""
        signature_data = f"{method}{url}{timestamp}{request_data}"
        signature = self._generate_hmac_signature(system, signature_data)
        
        headers = {
            "Authorization": f"HMAC {credentials.api_key}:{signature}",
            "X-Timestamp": timestamp,
            "X-Institution-Code": credentials.institution_code,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if credentials.user_id:
            headers["X-User-ID"] = credentials.user_id
            
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                async with session.request(method, url, headers=headers, 
                                         json=data, params=params) as response:
                    response_time = (time.time() - start_time) * 1000
                    response_data = await response.json()
                    
                    success = response.status == 200
                    
                    if self.config.audit_logging:
                        data_accessed = list(response_data.keys()) if isinstance(response_data, dict) else []
                        self.audit_logger.log_api_call(
                            system, endpoint.value, credentials.user_id or "unknown",
                            success, response_time, data_accessed
                        )
                    
                    if not success:
                        raise Exception(f"API call failed: {response_data}")
                        
                    return response_data
                    
        except Exception as e:
            if self.config.audit_logging:
                self.audit_logger.log_api_call(
                    system, endpoint.value, credentials.user_id or "unknown",
                    False, (time.time() - start_time) * 1000, []
                )
            raise
    
    # === e-Okul Sistemi Metodları ===
    
    async def get_student_info(self, student_tc: str, 
                             authorized_user: str) -> Optional[StudentInfo]:
        """Öğrenci bilgilerini al"""
        if self.config.audit_logging:
            self.audit_logger.log_data_access(
                authorized_user, student_tc, "student_info", 
                "KIRO2 exam preparation"
            )
            
        try:
            response = await self._make_api_call(
                MEBSystem.E_OKUL,
                MEBEndpointType.STUDENT_INFO,
                params={"tc_no": student_tc}
            )
            
            student_data = response.get("student")
            if not student_data:
                return None
                
            return StudentInfo(
                tc_no=student_data["tc_no"],
                student_no=student_data["student_no"],
                name=student_data["name"],
                surname=student_data["surname"],
                birth_date=datetime.fromisoformat(student_data["birth_date"]),
                student_type=StudentType(student_data["student_type"]),
                school_code=student_data["school_code"],
                school_name=student_data["school_name"],
                class_level=student_data["class_level"],
                class_branch=student_data["class_branch"],
                parent_tc_no=student_data.get("parent_tc_no"),
                parent_name=student_data.get("parent_name"),
                phone=student_data.get("phone"),
                email=student_data.get("email"),
                address=student_data.get("address")
            )
            
        except Exception as e:
            logging.error(f"Failed to get student info: {e}")
            return None
    
    async def get_academic_records(self, student_no: str, year: int, 
                                 semester: Optional[int] = None) -> List[AcademicRecord]:
        """Öğrenci akademik kayıtlarını al"""
        try:
            params = {"student_no": student_no, "year": year}
            if semester:
                params["semester"] = semester
                
            response = await self._make_api_call(
                MEBSystem.E_OKUL,
                MEBEndpointType.ACADEMIC_RECORDS,
                params=params
            )
            
            records = []
            for record_data in response.get("records", []):
                record = AcademicRecord(
                    student_no=record_data["student_no"],
                    subject=record_data["subject"],
                    semester=record_data["semester"],
                    year=record_data["year"],
                    grade=record_data["grade"],
                    grade_type=record_data["grade_type"],
                    teacher_name=record_data["teacher_name"],
                    exam_date=datetime.fromisoformat(record_data["exam_date"]),
                    weight=record_data.get("weight", 1.0)
                )
                records.append(record)
                
            return records
            
        except Exception as e:
            logging.error(f"Failed to get academic records: {e}")
            return []
    
    async def get_attendance_records(self, student_no: str, 
                                   start_date: datetime, 
                                   end_date: datetime) -> List[AttendanceRecord]:
        """Devamsızlık kayıtlarını al"""
        try:
            params = {
                "student_no": student_no,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            response = await self._make_api_call(
                MEBSystem.E_OKUL,
                MEBEndpointType.ATTENDANCE,
                params=params
            )
            
            records = []
            for record_data in response.get("records", []):
                record = AttendanceRecord(
                    student_no=record_data["student_no"],
                    date=datetime.fromisoformat(record_data["date"]),
                    status=record_data["status"],
                    lesson=record_data["lesson"],
                    teacher_name=record_data["teacher_name"],
                    excuse_status=record_data.get("excuse_status"),
                    excuse_document=record_data.get("excuse_document")
                )
                records.append(record)
                
            return records
            
        except Exception as e:
            logging.error(f"Failed to get attendance records: {e}")
            return []
    
    # === ÖSYM Bridge Metodları ===
    
    async def get_exam_results(self, student_tc: str, exam_type: ExamType,
                             year: int, authorized_user: str) -> Optional[ExamResult]:
        """Sınav sonuçlarını al"""
        if self.config.audit_logging:
            self.audit_logger.log_data_access(
                authorized_user, student_tc, f"{exam_type.value}_results",
                "KIRO2 performance analysis"
            )
            
        try:
            response = await self._make_api_call(
                MEBSystem.OSYM_BRIDGE,
                MEBEndpointType.EXAM_RESULTS,
                params={
                    "tc_no": student_tc,
                    "exam_type": exam_type.value,
                    "year": year
                }
            )
            
            result_data = response.get("result")
            if not result_data:
                return None
                
            return ExamResult(
                student_no=result_data["student_no"],
                exam_type=exam_type,
                exam_year=year,
                scores=result_data["scores"],
                ranking=result_data.get("ranking"),
                percentile=result_data.get("percentile"),
                university_preferences=result_data.get("university_preferences"),
                placement_result=result_data.get("placement_result")
            )
            
        except Exception as e:
            logging.error(f"Failed to get exam results: {e}")
            return None
    
    # === EBA (Eğitim Bilişim Ağı) Metodları ===
    
    async def get_digital_content(self, subject: str, grade_level: int,
                                curriculum_code: str) -> List[Dict]:
        """EBA dijital içeriği al"""
        try:
            response = await self._make_api_call(
                MEBSystem.EBA,
                MEBEndpointType.DIGITAL_CONTENT,
                params={
                    "subject": subject,
                    "grade_level": grade_level,
                    "curriculum_code": curriculum_code
                }
            )
            
            return response.get("content", [])
            
        except Exception as e:
            logging.error(f"Failed to get digital content: {e}")
            return []
    
    # === Toplu İşlem Metodları ===
    
    async def get_student_comprehensive_data(self, student_tc: str,
                                           authorized_user: str,
                                           include_anonymized: bool = True) -> Dict:
        """Öğrenci için kapsamlı veri al"""
        comprehensive_data = {
            "student_info": None,
            "academic_records": [],
            "attendance_records": [],
            "exam_results": []
        }
        
        # Öğrenci bilgileri
        student_info = await self.get_student_info(student_tc, authorized_user)
        if student_info:
            comprehensive_data["student_info"] = student_info.anonymize() if include_anonymized else student_info
            
            # Akademik kayıtlar (son 2 yıl)
            current_year = datetime.now().year
            for year in [current_year - 1, current_year]:
                records = await self.get_academic_records(student_info.student_no, year)
                comprehensive_data["academic_records"].extend(records)
            
            # Devamsızlık kayıtları (son 6 ay)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            attendance = await self.get_attendance_records(
                student_info.student_no, start_date, end_date
            )
            comprehensive_data["attendance_records"] = attendance
            
            # Sınav sonuçları
            if student_info.student_type in [StudentType.HIGH, StudentType.VOCATIONAL, StudentType.IMAM_HATIP]:
                for exam_type in [ExamType.TYT, ExamType.AYT, ExamType.YKS]:
                    result = await self.get_exam_results(
                        student_tc, exam_type, current_year, authorized_user
                    )
                    if result:
                        comprehensive_data["exam_results"].append(result)
                        
        return comprehensive_data
    
    async def batch_student_sync(self, student_tc_list: List[str],
                               authorized_user: str) -> Dict[str, Dict]:
        """Toplu öğrenci senkronizasyonu"""
        results = {}
        
        # Rate limiting için batch'leri böl
        batch_size = min(10, self.config.rate_limit_per_minute // 4)
        
        for i in range(0, len(student_tc_list), batch_size):
            batch = student_tc_list[i:i + batch_size]
            
            tasks = []
            for student_tc in batch:
                task = self.get_student_comprehensive_data(
                    student_tc, authorized_user, include_anonymized=True
                )
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for student_tc, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results[student_tc] = {"error": str(result)}
                else:
                    results[student_tc] = result
            
            # Rate limiting için bekleme
            if i + batch_size < len(student_tc_list):
                await asyncio.sleep(60 / self.config.rate_limit_per_minute)
        
        return results
    
    # === Önbellek Metodları ===
    
    def _get_cache_key(self, system: MEBSystem, endpoint: MEBEndpointType,
                      params: Dict) -> str:
        """Önbellek anahtarı oluştur"""
        param_str = json.dumps(params, sort_keys=True)
        return f"{system.value}:{endpoint.value}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    async def get_cached_or_fetch(self, system: MEBSystem, 
                                endpoint: MEBEndpointType,
                                params: Dict, method: str = "GET") -> Dict:
        """Önbellekten al veya API'den çek"""
        cache_key = self._get_cache_key(system, endpoint, params)
        
        # Önbellekte var mı kontrol et
        if cache_key in self.session_cache:
            cached_data, timestamp = self.session_cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.config.cache_ttl:
                return cached_data
        
        # API'den çek
        data = await self._make_api_call(system, endpoint, method, params=params)
        
        # Önbelleğe kaydet
        self.session_cache[cache_key] = (data, datetime.now().timestamp())
        
        return data
    
    # === Sistem Durumu Metodları ===
    
    async def health_check(self) -> Dict[MEBSystem, bool]:
        """Tüm MEB sistemlerinin sağlık durumunu kontrol et"""
        health_status = {}
        
        for system in MEBSystem:
            if system not in self.credentials:
                health_status[system] = False
                continue
                
            try:
                # Basit bir ping endpoint'i çağır
                await self._make_api_call(
                    system, MEBEndpointType.AUTHENTICATION, 
                    params={"ping": "1"}
                )
                health_status[system] = True
            except:
                health_status[system] = False
                
        return health_status
    
    async def get_integration_statistics(self) -> Dict:
        """Entegrasyon istatistiklerini al"""
        stats = {
            "total_api_calls": sum(len(calls) for calls in self.rate_limits.values()),
            "systems_configured": len(self.credentials),
            "cache_entries": len(self.session_cache),
            "rate_limit_status": {}
        }
        
        for system in MEBSystem:
            remaining_calls = max(0, self.config.rate_limit_per_minute - len(self.rate_limits[system]))
            stats["rate_limit_status"][system.value] = {
                "calls_made": len(self.rate_limits[system]),
                "remaining_calls": remaining_calls
            }
        
        return stats


class MEBIntegrationManager:
    """MEB Entegrasyon Yöneticisi - KIRO2 için ana interface"""
    
    def __init__(self):
        self.config = MEBConfiguration()
        self.integration = MEBAPIIntegration(self.config)
        self.initialized = False
        
    async def initialize_for_kiro2(self, 
                                  institution_code: str,
                                  api_credentials: Dict[str, Dict[str, str]],
                                  encryption_key: bytes):
        """KIRO2 için MEB entegrasyonunu başlat"""
        await self.integration.initialize(encryption_key)
        
        # Her sistem için kimlik bilgilerini yapılandır
        for system_name, creds in api_credentials.items():
            try:
                system = MEBSystem(system_name)
                credentials = MEBCredentials(
                    system=system,
                    api_key=creds["api_key"],
                    secret_key=creds["secret_key"],
                    institution_code=institution_code,
                    user_id=creds.get("user_id"),
                    environment=creds.get("environment", "production")
                )
                
                self.integration.add_credentials(system, credentials)
                
            except ValueError:
                logging.warning(f"Unknown MEB system: {system_name}")
                
        self.initialized = True
        logging.info("MEB Integration initialized for KIRO2")
        
    async def sync_student_data_for_kiro2(self, student_tc_list: List[str],
                                        authorized_user: str) -> Dict:
        """KIRO2 için öğrenci verilerini senkronize et"""
        if not self.initialized:
            raise Exception("MEB Integration not initialized")
            
        return await self.integration.batch_student_sync(
            student_tc_list, authorized_user
        )
        
    async def get_exam_performance_analysis(self, student_tc: str,
                                          authorized_user: str) -> Dict:
        """KIRO2 için sınav performans analizi"""
        comprehensive_data = await self.integration.get_student_comprehensive_data(
            student_tc, authorized_user, include_anonymized=False
        )
        
        analysis = {
            "student_profile": comprehensive_data.get("student_info"),
            "academic_performance": self._analyze_academic_performance(
                comprehensive_data.get("academic_records", [])
            ),
            "attendance_analysis": self._analyze_attendance(
                comprehensive_data.get("attendance_records", [])
            ),
            "exam_readiness": self._assess_exam_readiness(
                comprehensive_data.get("exam_results", [])
            ),
            "recommendations": []
        }
        
        # KIRO2 önerilerini oluştur
        analysis["recommendations"] = self._generate_kiro2_recommendations(analysis)
        
        return analysis
        
    def _analyze_academic_performance(self, records: List[AcademicRecord]) -> Dict:
        """Akademik performans analizi"""
        if not records:
            return {"average": 0, "trend": "unknown", "weak_subjects": []}
            
        # Ders bazında ortalamalar
        subject_grades = {}
        for record in records:
            if record.subject not in subject_grades:
                subject_grades[record.subject] = []
            subject_grades[record.subject].append(record.grade)
        
        subject_averages = {
            subject: sum(grades) / len(grades)
            for subject, grades in subject_grades.items()
        }
        
        overall_average = sum(subject_averages.values()) / len(subject_averages)
        weak_subjects = [
            subject for subject, avg in subject_averages.items()
            if avg < overall_average * 0.8
        ]
        
        return {
            "average": overall_average,
            "subject_averages": subject_averages,
            "weak_subjects": weak_subjects,
            "strong_subjects": [
                subject for subject, avg in subject_averages.items()
                if avg > overall_average * 1.2
            ]
        }
        
    def _analyze_attendance(self, records: List[AttendanceRecord]) -> Dict:
        """Devamsızlık analizi"""
        if not records:
            return {"attendance_rate": 100, "absent_days": 0}
            
        total_days = len(records)
        absent_days = len([r for r in records if r.status == "devamsız"])
        attendance_rate = ((total_days - absent_days) / total_days) * 100
        
        return {
            "attendance_rate": attendance_rate,
            "absent_days": absent_days,
            "total_days": total_days,
            "excused_absences": len([r for r in records if r.excuse_status == "mazeretli"])
        }
        
    def _assess_exam_readiness(self, exam_results: List[ExamResult]) -> Dict:
        """Sınav hazırlık durumu değerlendirmesi"""
        if not exam_results:
            return {"readiness_level": "unknown", "target_areas": []}
            
        # Son sınav sonuçlarını analiz et
        latest_result = max(exam_results, key=lambda x: x.exam_year)
        
        readiness_level = "iyi"
        if latest_result.percentile and latest_result.percentile < 50:
            readiness_level = "geliştirilmeli"
        elif latest_result.percentile and latest_result.percentile < 25:
            readiness_level = "yetersiz"
            
        # Zayıf alanları belirle
        target_areas = []
        for subject, score in latest_result.scores.items():
            if score < 300:  # YKS için düşük puan eşiği
                target_areas.append(subject)
        
        return {
            "readiness_level": readiness_level,
            "target_areas": target_areas,
            "latest_percentile": latest_result.percentile,
            "exam_year": latest_result.exam_year
        }
        
    def _generate_kiro2_recommendations(self, analysis: Dict) -> List[str]:
        """KIRO2 için öneriler oluştur"""
        recommendations = []
        
        # Akademik performans önerileri
        academic = analysis.get("academic_performance", {})
        if academic.get("weak_subjects"):
            recommendations.append(
                f"KIRO2'de {', '.join(academic['weak_subjects'])} derslerinde "
                f"ek çalışma materyalleri ve test çözümlerine odaklanın."
            )
            
        # Devamsızlık önerileri
        attendance = analysis.get("attendance_analysis", {})
        if attendance.get("attendance_rate", 100) < 90:
            recommendations.append(
                "Düzenli ders katılımı başarınızı artıracaktır. "
                "KIRO2 online derslerini kaçırmayın."
            )
            
        # Sınav hazırlık önerileri
        exam_readiness = analysis.get("exam_readiness", {})
        if exam_readiness.get("readiness_level") == "geliştirilmeli":
            recommendations.append(
                "KIRO2'nin adaptif soru çözme sistemini kullanarak "
                "zayıf alanlarınızda yoğunlaşın."
            )
            
        if exam_readiness.get("target_areas"):
            recommendations.append(
                f"Öncelikle {', '.join(exam_readiness['target_areas'])} "
                f"konularında KIRO2'nin özel hazırlık programlarını tamamlayın."
            )
            
        return recommendations


# === Örnek Kullanım ===

async def example_meb_integration():
    """MEB entegrasyonu örnek kullanımı"""
    
    # Entegrasyon yöneticisini başlat
    manager = MEBIntegrationManager()
    
    # KIRO2 için yapılandır
    api_credentials = {
        "e_okul": {
            "api_key": "KIRO2_E_OKUL_API_KEY",
            "secret_key": "KIRO2_E_OKUL_SECRET",
            "user_id": "kiro2_system"
        },
        "osym_bridge": {
            "api_key": "KIRO2_OSYM_API_KEY", 
            "secret_key": "KIRO2_OSYM_SECRET",
            "user_id": "kiro2_system"
        }
    }
    
    encryption_key = b"kiro2_meb_encryption_key_32bytes!"
    
    await manager.initialize_for_kiro2(
        institution_code="KIRO2_EDU_PLATFORM",
        api_credentials=api_credentials,
        encryption_key=encryption_key
    )
    
    # Öğrenci performans analizi
    student_tc = "12345678901"
    authorized_user = "kiro2_teacher_001"
    
    analysis = await manager.get_exam_performance_analysis(
        student_tc, authorized_user
    )
    
    print("KIRO2 MEB Entegrasyon Analizi:")
    print(f"Öğrenci: {analysis['student_profile'].name if analysis['student_profile'] else 'Bilinmiyor'}")
    print(f"Akademik Ortalama: {analysis['academic_performance']['average']:.2f}")
    print(f"Devam Oranı: {analysis['attendance_analysis']['attendance_rate']:.1f}%")
    print(f"Sınav Hazırlık Durumu: {analysis['exam_readiness']['readiness_level']}")
    print("\nKİRO2 Önerileri:")
    for i, recommendation in enumerate(analysis['recommendations'], 1):
        print(f"{i}. {recommendation}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_meb_integration())