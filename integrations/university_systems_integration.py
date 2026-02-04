"""
KIRO2 - University Systems Integration Hub
==========================================

Bu modül, Türkiye'deki üniversite sistemleri ile entegrasyonu sağlar.
YÖK, üniversite bilgi sistemleri, öğrenci işleri ve akademik sistemler ile bağlantı kurar.

Desteklenen Üniversite Sistemleri:
- YÖK (Yükseköğretim Kurulu) Atlas sistemi
- Üniversite Bilgi Yönetim Sistemleri (UBYS)
- Öğrenci Bilgi Sistemleri (ÖBS)
- Akademik Bilgi Yönetim Sistemleri (ABYS)
- Bologna Süreci ve AKTS entegrasyonu
- Erasmus+ ve uluslararası değişim programları
- Mezuniyet ve diploma doğrulama sistemleri
- Üniversite kütüphane sistemleri

YKS yerleştirme sonuçları ve tercih analizi desteği.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import xmltodict
from bs4 import BeautifulSoup

from .unified_integration_framework import (
    IntegrationFramework,
    IntegrationType,
    AuthenticationMethod,
    IntegrationConfiguration,
    IntegrationCredentials
)


class UniversitySystem(Enum):
    """Üniversite sistemleri enum class'ı"""
    YOK_ATLAS = "yok_atlas"                    # YÖK Atlas - Genel üniversite bilgileri
    UBYS = "ubys"                              # Üniversite Bilgi Yönetim Sistemi
    OBS = "obs"                                # Öğrenci Bilgi Sistemi
    ABYS = "abys"                              # Akademik Bilgi Yönetim Sistemi
    BOLOGNA = "bologna"                        # Bologna Süreci / AKTS
    ERASMUS = "erasmus"                        # Erasmus+ Sistemi
    DIPLOMA_VERIFICATION = "diploma_verify"    # Diploma Doğrulama
    LIBRARY_SYSTEM = "library"                 # Kütüphane Sistemleri
    YKS_PLACEMENT = "yks_placement"            # YKS Yerleştirme Sistemi
    UNIVERSITY_PORTAL = "uni_portal"           # Üniversite Portalları


class UniversityType(Enum):
    """Üniversite türleri"""
    STATE = "devlet"
    FOUNDATION = "vakif"
    TECHNICAL = "teknik"
    VOCATIONAL = "meslek_yuksekokulu"


class FacultyType(Enum):
    """Fakülte türleri"""
    ENGINEERING = "muhendislik"
    MEDICINE = "tip"
    LAW = "hukuk"
    LITERATURE = "edebiyat"
    ECONOMICS = "iktisat"
    EDUCATION = "egitim"
    SCIENCE = "fen"
    FINE_ARTS = "guzel_sanatlar"
    THEOLOGY = "ilahiyat"
    AGRICULTURE = "ziraat"
    VETERINARY = "veteriner"
    PHARMACY = "eczacilik"
    DENTISTRY = "dis_hekimligi"
    ARCHITECTURE = "mimarlik"
    COMMUNICATION = "iletisim"


class DegreeType(Enum):
    """Derece türleri"""
    ASSOCIATE = "on_lisans"      # Ön Lisans
    BACHELOR = "lisans"          # Lisans
    MASTER = "yuksek_lisans"     # Yüksek Lisans
    DOCTORATE = "doktora"        # Doktora
    SPECIALTY = "uzmanlik"       # Tıp Uzmanlık


@dataclass
class University:
    """Üniversite bilgi modeli"""
    code: str
    name: str
    city: str
    type: UniversityType
    founding_year: int
    rector_name: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    student_count: Optional[int] = None
    academic_staff_count: Optional[int] = None
    faculties: List[str] = field(default_factory=list)
    
    
@dataclass
class Department:
    """Bölüm bilgi modeli"""
    code: str
    name: str
    university_code: str
    faculty_name: str
    faculty_type: FacultyType
    degree_type: DegreeType
    language: str = "Türkçe"
    duration_years: int = 4
    quota: Optional[int] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    placement_count: Optional[int] = None


@dataclass
class YKSPlacement:
    """YKS yerleştirme bilgisi"""
    year: int
    university_code: str
    department_code: str
    exam_type: str  # TYT, AYT, YDT
    quota: int
    placement_count: int
    min_score: float
    max_score: float
    min_ranking: Optional[int] = None
    max_ranking: Optional[int] = None
    additional_requirements: Optional[List[str]] = None


@dataclass
class StudentRecord:
    """Öğrenci kayıt bilgisi"""
    student_id: str
    tc_no: str  # KVKK korumalı
    name: str
    surname: str
    university_code: str
    department_code: str
    degree_type: DegreeType
    enrollment_year: int
    current_semester: int
    gpa: Optional[float] = None
    status: str = "aktif"  # aktif, mezun, ayrılmış, dondurmuş
    
    def anonymize(self) -> 'StudentRecord':
        """KVKK uyumlu anonimleştirme"""
        return StudentRecord(
            student_id=self.student_id,
            tc_no="***masked***",
            name=self.name[0] + "*" * (len(self.name) - 1),
            surname=self.surname[0] + "*" * (len(self.surname) - 1),
            university_code=self.university_code,
            department_code=self.department_code,
            degree_type=self.degree_type,
            enrollment_year=self.enrollment_year,
            current_semester=self.current_semester,
            gpa=self.gpa,
            status=self.status
        )


@dataclass
class AcademicTranscript:
    """Akademik transkript"""
    student_id: str
    courses: List[Dict[str, Any]]
    total_credits: int
    completed_credits: int
    gpa: float
    cgpa: float  # Cumulative GPA
    graduation_status: bool = False
    
    
@dataclass
class DiplomaInfo:
    """Diploma bilgisi"""
    diploma_no: str
    student_tc: str  # KVKK korumalı
    university_code: str
    department_code: str
    degree_type: DegreeType
    graduation_date: datetime
    diploma_date: datetime
    gpa: float
    honors: Optional[str] = None  # takdir, teşekkür, vs.
    verified: bool = False


class UniversitySystemConfiguration:
    """Üniversite sistemleri yapılandırması"""
    
    def __init__(self):
        self.base_urls = {
            UniversitySystem.YOK_ATLAS: "https://yoksis.yok.gov.tr/api/v1",
            UniversitySystem.UBYS: "https://ubys.uni.edu.tr/api/v1",
            UniversitySystem.OBS: "https://obs.uni.edu.tr/api/v1", 
            UniversitySystem.ABYS: "https://abys.uni.edu.tr/api/v1",
            UniversitySystem.BOLOGNA: "https://bologna.yok.gov.tr/api/v1",
            UniversitySystem.ERASMUS: "https://erasmus.ua.gov.tr/api/v1",
            UniversitySystem.DIPLOMA_VERIFICATION: "https://diploma.yok.gov.tr/api/v1",
            UniversitySystem.LIBRARY_SYSTEM: "https://library-api.uni.edu.tr/v1",
            UniversitySystem.YKS_PLACEMENT: "https://tercih.osym.gov.tr/api/v1",
            UniversitySystem.UNIVERSITY_PORTAL: "https://portal.uni.edu.tr/api/v1"
        }
        
        self.timeout = 45  # Üniversite sistemleri yavaş olabilir
        self.max_retries = 5
        self.rate_limit_per_minute = 60
        self.cache_ttl = 600  # 10 dakika (üniversite verileri sık değişmez)


class YOKAtlasClient:
    """YÖK Atlas API İstemcisi"""
    
    def __init__(self, base_url: str, credentials: Dict[str, str]):
        self.base_url = base_url
        self.credentials = credentials
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_universities(self, city: Optional[str] = None,
                             uni_type: Optional[UniversityType] = None) -> List[University]:
        """Üniversite listesini al"""
        params = {}
        if city:
            params["city"] = city
        if uni_type:
            params["type"] = uni_type.value
            
        async with self.session.get(
            f"{self.base_url}/universities",
            params=params,
            headers=self._get_auth_headers()
        ) as response:
            data = await response.json()
            
            universities = []
            for uni_data in data.get("universities", []):
                university = University(
                    code=uni_data["code"],
                    name=uni_data["name"],
                    city=uni_data["city"],
                    type=UniversityType(uni_data["type"]),
                    founding_year=uni_data["founding_year"],
                    rector_name=uni_data.get("rector_name"),
                    website=uni_data.get("website"),
                    phone=uni_data.get("phone"),
                    address=uni_data.get("address"),
                    student_count=uni_data.get("student_count"),
                    academic_staff_count=uni_data.get("academic_staff_count"),
                    faculties=uni_data.get("faculties", [])
                )
                universities.append(university)
                
            return universities
    
    async def get_departments(self, university_code: str,
                            faculty_type: Optional[FacultyType] = None) -> List[Department]:
        """Bölüm listesini al"""
        params = {"university_code": university_code}
        if faculty_type:
            params["faculty_type"] = faculty_type.value
            
        async with self.session.get(
            f"{self.base_url}/departments",
            params=params,
            headers=self._get_auth_headers()
        ) as response:
            data = await response.json()
            
            departments = []
            for dept_data in data.get("departments", []):
                department = Department(
                    code=dept_data["code"],
                    name=dept_data["name"],
                    university_code=dept_data["university_code"],
                    faculty_name=dept_data["faculty_name"],
                    faculty_type=FacultyType(dept_data["faculty_type"]),
                    degree_type=DegreeType(dept_data["degree_type"]),
                    language=dept_data.get("language", "Türkçe"),
                    duration_years=dept_data.get("duration_years", 4),
                    quota=dept_data.get("quota"),
                    min_score=dept_data.get("min_score"),
                    max_score=dept_data.get("max_score"),
                    placement_count=dept_data.get("placement_count")
                )
                departments.append(department)
                
            return departments
    
    async def get_yks_placements(self, year: int, university_code: Optional[str] = None,
                               department_code: Optional[str] = None) -> List[YKSPlacement]:
        """YKS yerleştirme verilerini al"""
        params = {"year": year}
        if university_code:
            params["university_code"] = university_code
        if department_code:
            params["department_code"] = department_code
            
        async with self.session.get(
            f"{self.base_url}/yks-placements",
            params=params,
            headers=self._get_auth_headers()
        ) as response:
            data = await response.json()
            
            placements = []
            for placement_data in data.get("placements", []):
                placement = YKSPlacement(
                    year=placement_data["year"],
                    university_code=placement_data["university_code"],
                    department_code=placement_data["department_code"],
                    exam_type=placement_data["exam_type"],
                    quota=placement_data["quota"],
                    placement_count=placement_data["placement_count"],
                    min_score=placement_data["min_score"],
                    max_score=placement_data["max_score"],
                    min_ranking=placement_data.get("min_ranking"),
                    max_ranking=placement_data.get("max_ranking"),
                    additional_requirements=placement_data.get("additional_requirements")
                )
                placements.append(placement)
                
            return placements
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Yetkilendirme başlıklarını al"""
        return {
            "Authorization": f"Bearer {self.credentials['api_key']}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


class UniversityOBSClient:
    """Üniversite Öğrenci Bilgi Sistemi İstemcisi"""
    
    def __init__(self, university_code: str, base_url: str, credentials: Dict[str, str]):
        self.university_code = university_code
        self.base_url = base_url.replace("uni.edu.tr", f"{university_code}.edu.tr")
        self.credentials = credentials
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> str:
        """OBS sistemine giriş yap ve token al"""
        auth_data = {
            "username": self.credentials["username"],
            "password": self.credentials["password"],
            "institution": self.university_code
        }
        
        async with self.session.post(
            f"{self.base_url}/auth/login",
            json=auth_data
        ) as response:
            data = await response.json()
            return data.get("access_token")
    
    async def get_student_record(self, student_id: str, token: str) -> Optional[StudentRecord]:
        """Öğrenci kaydını al"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with self.session.get(
            f"{self.base_url}/students/{student_id}",
            headers=headers
        ) as response:
            if response.status != 200:
                return None
                
            data = await response.json()
            student_data = data.get("student")
            
            if not student_data:
                return None
                
            return StudentRecord(
                student_id=student_data["student_id"],
                tc_no=student_data["tc_no"],
                name=student_data["name"],
                surname=student_data["surname"],
                university_code=student_data["university_code"],
                department_code=student_data["department_code"],
                degree_type=DegreeType(student_data["degree_type"]),
                enrollment_year=student_data["enrollment_year"],
                current_semester=student_data["current_semester"],
                gpa=student_data.get("gpa"),
                status=student_data.get("status", "aktif")
            )
    
    async def get_academic_transcript(self, student_id: str, token: str) -> Optional[AcademicTranscript]:
        """Akademik transkripti al"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with self.session.get(
            f"{self.base_url}/students/{student_id}/transcript",
            headers=headers
        ) as response:
            if response.status != 200:
                return None
                
            data = await response.json()
            transcript_data = data.get("transcript")
            
            if not transcript_data:
                return None
                
            return AcademicTranscript(
                student_id=transcript_data["student_id"],
                courses=transcript_data["courses"],
                total_credits=transcript_data["total_credits"],
                completed_credits=transcript_data["completed_credits"],
                gpa=transcript_data["gpa"],
                cgpa=transcript_data["cgpa"],
                graduation_status=transcript_data.get("graduation_status", False)
            )


class DiplomaVerificationClient:
    """Diploma doğrulama sistemi istemcisi"""
    
    def __init__(self, base_url: str, credentials: Dict[str, str]):
        self.base_url = base_url
        self.credentials = credentials
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def verify_diploma(self, diploma_no: str, student_tc: str) -> Optional[DiplomaInfo]:
        """Diploma doğrulama"""
        verification_data = {
            "diploma_no": diploma_no,
            "tc_no": student_tc,
            "api_key": self.credentials["api_key"]
        }
        
        async with self.session.post(
            f"{self.base_url}/verify",
            json=verification_data
        ) as response:
            if response.status != 200:
                return None
                
            data = await response.json()
            diploma_data = data.get("diploma")
            
            if not diploma_data or not data.get("verified", False):
                return None
                
            return DiplomaInfo(
                diploma_no=diploma_data["diploma_no"],
                student_tc=diploma_data["student_tc"],
                university_code=diploma_data["university_code"],
                department_code=diploma_data["department_code"],
                degree_type=DegreeType(diploma_data["degree_type"]),
                graduation_date=datetime.fromisoformat(diploma_data["graduation_date"]),
                diploma_date=datetime.fromisoformat(diploma_data["diploma_date"]),
                gpa=diploma_data["gpa"],
                honors=diploma_data.get("honors"),
                verified=True
            )


class UniversitySystemsIntegrationHub:
    """Üniversite Sistemleri Entegrasyon Merkezi"""
    
    def __init__(self):
        self.config = UniversitySystemConfiguration()
        self.integration_framework = IntegrationFramework()
        self.university_credentials: Dict[str, Dict[str, str]] = {}
        self.cache: Dict[str, Any] = {}
        self.logger = logging.getLogger("university_integration")
        
    async def initialize(self):
        """Entegrasyonu başlat"""
        # Her üniversite sistemi için entegrasyon yapılandır
        for system in UniversitySystem:
            integration_config = IntegrationConfiguration(
                name=f"university_{system.value}",
                integration_type=IntegrationType.EDUCATION_SYSTEM,
                base_url=self.config.base_urls[system],
                authentication_method=AuthenticationMethod.BEARER_TOKEN,
                rate_limit_per_minute=self.config.rate_limit_per_minute,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries
            )
            
            await self.integration_framework.register_integration(
                system.value, integration_config
            )
            
        self.logger.info("University Systems Integration Hub initialized")
    
    def add_university_credentials(self, university_code: str, credentials: Dict[str, str]):
        """Üniversite kimlik bilgilerini ekle"""
        self.university_credentials[university_code] = credentials
        
    async def get_all_universities(self, city: Optional[str] = None) -> List[University]:
        """Tüm üniversiteleri al"""
        cache_key = f"universities_{city or 'all'}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                return cached_data
        
        try:
            async with YOKAtlasClient(
                self.config.base_urls[UniversitySystem.YOK_ATLAS],
                self.university_credentials.get("yok", {})
            ) as client:
                universities = await client.get_universities(city=city)
                
                # Önbelleğe kaydet
                self.cache[cache_key] = (universities, time.time())
                return universities
                
        except Exception as e:
            self.logger.error(f"Failed to get universities: {e}")
            return []
    
    async def get_university_departments(self, university_code: str,
                                       faculty_type: Optional[FacultyType] = None) -> List[Department]:
        """Üniversite bölümlerini al"""
        cache_key = f"departments_{university_code}_{faculty_type.value if faculty_type else 'all'}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                return cached_data
        
        try:
            async with YOKAtlasClient(
                self.config.base_urls[UniversitySystem.YOK_ATLAS],
                self.university_credentials.get("yok", {})
            ) as client:
                departments = await client.get_departments(
                    university_code=university_code,
                    faculty_type=faculty_type
                )
                
                # Önbelleğe kaydet
                self.cache[cache_key] = (departments, time.time())
                return departments
                
        except Exception as e:
            self.logger.error(f"Failed to get departments: {e}")
            return []
    
    async def get_yks_placement_data(self, year: int, 
                                   university_code: Optional[str] = None) -> List[YKSPlacement]:
        """YKS yerleştirme verilerini al"""
        cache_key = f"yks_placements_{year}_{university_code or 'all'}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                return cached_data
        
        try:
            async with YOKAtlasClient(
                self.config.base_urls[UniversitySystem.YOK_ATLAS],
                self.university_credentials.get("yok", {})
            ) as client:
                placements = await client.get_yks_placements(
                    year=year,
                    university_code=university_code
                )
                
                # Önbelleğe kaydet
                self.cache[cache_key] = (placements, time.time())
                return placements
                
        except Exception as e:
            self.logger.error(f"Failed to get YKS placements: {e}")
            return []
    
    async def get_student_university_record(self, student_id: str, 
                                          university_code: str) -> Optional[StudentRecord]:
        """Öğrencinin üniversite kaydını al"""
        if university_code not in self.university_credentials:
            self.logger.error(f"No credentials for university: {university_code}")
            return None
        
        try:
            async with UniversityOBSClient(
                university_code,
                self.config.base_urls[UniversitySystem.OBS],
                self.university_credentials[university_code]
            ) as client:
                token = await client.authenticate()
                if not token:
                    return None
                    
                return await client.get_student_record(student_id, token)
                
        except Exception as e:
            self.logger.error(f"Failed to get student record: {e}")
            return None
    
    async def get_student_transcript(self, student_id: str,
                                   university_code: str) -> Optional[AcademicTranscript]:
        """Öğrenci transkriptini al"""
        if university_code not in self.university_credentials:
            return None
        
        try:
            async with UniversityOBSClient(
                university_code,
                self.config.base_urls[UniversitySystem.OBS],
                self.university_credentials[university_code]
            ) as client:
                token = await client.authenticate()
                if not token:
                    return None
                    
                return await client.get_academic_transcript(student_id, token)
                
        except Exception as e:
            self.logger.error(f"Failed to get transcript: {e}")
            return None
    
    async def verify_diploma(self, diploma_no: str, student_tc: str) -> Optional[DiplomaInfo]:
        """Diploma doğrulama"""
        try:
            async with DiplomaVerificationClient(
                self.config.base_urls[UniversitySystem.DIPLOMA_VERIFICATION],
                self.university_credentials.get("diploma_verification", {})
            ) as client:
                return await client.verify_diploma(diploma_no, student_tc)
                
        except Exception as e:
            self.logger.error(f"Failed to verify diploma: {e}")
            return None
    
    # === KIRO2 İçin Özel Metodlar ===
    
    async def analyze_university_preferences_for_kiro2(self, student_scores: Dict[str, float],
                                                      preferred_cities: List[str],
                                                      preferred_faculties: List[FacultyType]) -> Dict:
        """KIRO2 için üniversite tercih analizi"""
        analysis = {
            "recommended_universities": [],
            "reachable_departments": [],
            "backup_options": [],
            "scholarship_opportunities": []
        }
        
        # YKS yerleştirme verilerini al
        current_year = datetime.now().year
        placements = await self.get_yks_placement_data(current_year - 1)
        
        # Öğrencinin puanlarına göre yerleşebileceği bölümleri bul
        for placement in placements:
            # Puan kontrolü
            student_total_score = sum(student_scores.values())
            if (placement.min_score <= student_total_score <= 
                placement.max_score + 50):  # 50 puan tolerans
                
                # Üniversite ve bölüm bilgilerini al
                universities = await self.get_all_universities()
                university = next((u for u in universities 
                                 if u.code == placement.university_code), None)
                
                if university and university.city in preferred_cities:
                    departments = await self.get_university_departments(
                        placement.university_code
                    )
                    department = next((d for d in departments 
                                     if d.code == placement.department_code), None)
                    
                    if (department and 
                        department.faculty_type in preferred_faculties):
                        
                        recommendation = {
                            "university": university,
                            "department": department,
                            "placement_info": placement,
                            "success_probability": self._calculate_success_probability(
                                student_total_score, placement
                            )
                        }
                        
                        if recommendation["success_probability"] > 0.7:
                            analysis["recommended_universities"].append(recommendation)
                        elif recommendation["success_probability"] > 0.4:
                            analysis["reachable_departments"].append(recommendation)
                        else:
                            analysis["backup_options"].append(recommendation)
        
        # Sıralama
        for category in ["recommended_universities", "reachable_departments", "backup_options"]:
            analysis[category].sort(
                key=lambda x: x["success_probability"], 
                reverse=True
            )
        
        return analysis
    
    def _calculate_success_probability(self, student_score: float, 
                                     placement: YKSPlacement) -> float:
        """Yerleşme başarı olasılığını hesapla"""
        score_range = placement.max_score - placement.min_score
        if score_range == 0:
            return 1.0 if student_score >= placement.min_score else 0.0
        
        # Öğrenci puanının yerleştirme aralığındaki konumu
        if student_score < placement.min_score:
            return max(0.0, 1.0 - (placement.min_score - student_score) / 100)
        elif student_score > placement.max_score:
            return 1.0
        else:
            position = (student_score - placement.min_score) / score_range
            return 0.3 + (position * 0.7)  # Min %30, max %100
    
    async def get_kiro2_university_insights(self, university_code: str) -> Dict:
        """KIRO2 için üniversite içgörüleri"""
        insights = {
            "university_info": None,
            "popular_departments": [],
            "placement_trends": {},
            "academic_quality_indicators": {},
            "student_satisfaction": {},
            "career_outcomes": {}
        }
        
        # Üniversite temel bilgileri
        universities = await self.get_all_universities()
        insights["university_info"] = next(
            (u for u in universities if u.code == university_code), None
        )
        
        # Popüler bölümler (yerleşme oranı yüksek)
        departments = await self.get_university_departments(university_code)
        current_year = datetime.now().year
        
        for year in range(current_year - 3, current_year):
            placements = await self.get_yks_placement_data(year, university_code)
            for placement in placements:
                if placement.university_code == university_code:
                    dept_name = next(
                        (d.name for d in departments if d.code == placement.department_code), 
                        placement.department_code
                    )
                    
                    if dept_name not in insights["placement_trends"]:
                        insights["placement_trends"][dept_name] = []
                    
                    insights["placement_trends"][dept_name].append({
                        "year": year,
                        "quota": placement.quota,
                        "placement_count": placement.placement_count,
                        "min_score": placement.min_score,
                        "competition_ratio": placement.quota / max(placement.placement_count, 1)
                    })
        
        return insights
    
    async def batch_university_sync_for_kiro2(self, university_codes: List[str]) -> Dict:
        """KIRO2 için toplu üniversite veri senkronizasyonu"""
        sync_results = {}
        
        for university_code in university_codes:
            try:
                result = {
                    "university_info": None,
                    "departments": [],
                    "placement_data": [],
                    "insights": None,
                    "sync_timestamp": datetime.now().isoformat()
                }
                
                # Üniversite bilgileri
                universities = await self.get_all_universities()
                result["university_info"] = next(
                    (u for u in universities if u.code == university_code), None
                )
                
                if result["university_info"]:
                    # Bölümler
                    result["departments"] = await self.get_university_departments(university_code)
                    
                    # YKS yerleştirme verileri
                    current_year = datetime.now().year
                    for year in range(current_year - 2, current_year + 1):
                        placements = await self.get_yks_placement_data(year, university_code)
                        result["placement_data"].extend(placements)
                    
                    # İçgörüler
                    result["insights"] = await self.get_kiro2_university_insights(university_code)
                
                sync_results[university_code] = result
                
            except Exception as e:
                sync_results[university_code] = {
                    "error": str(e),
                    "sync_timestamp": datetime.now().isoformat()
                }
                self.logger.error(f"Failed to sync university {university_code}: {e}")
        
        return sync_results
    
    # === Önbellek ve Performans ===
    
    def clear_cache(self):
        """Önbelleği temizle"""
        self.cache.clear()
        self.logger.info("University systems cache cleared")
    
    async def preload_popular_data(self):
        """Popüler verileri önceden yükle"""
        try:
            # Büyük şehirlerdeki üniversiteler
            major_cities = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"]
            for city in major_cities:
                await self.get_all_universities(city=city)
            
            # Son 2 yılın YKS verileri
            current_year = datetime.now().year
            for year in range(current_year - 1, current_year + 1):
                await self.get_yks_placement_data(year)
            
            self.logger.info("Popular university data preloaded")
            
        except Exception as e:
            self.logger.error(f"Failed to preload data: {e}")
    
    async def get_system_health(self) -> Dict[str, bool]:
        """Sistem sağlık durumunu kontrol et"""
        health_status = {}
        
        for system in UniversitySystem:
            try:
                # Basit bir test isteği
                integration = self.integration_framework.integrations.get(system.value)
                if integration:
                    # Test URL'sine ping gönder
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{integration.config.base_url}/health",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            health_status[system.value] = response.status == 200
                else:
                    health_status[system.value] = False
                    
            except:
                health_status[system.value] = False
        
        return health_status


# === KIRO2 Entegrasyon Yöneticisi ===

class KIRO2UniversityIntegrationManager:
    """KIRO2 için Üniversite Entegrasyon Yöneticisi"""
    
    def __init__(self):
        self.hub = UniversitySystemsIntegrationHub()
        self.initialized = False
        
    async def initialize_for_kiro2(self, credentials: Dict[str, Dict[str, str]]):
        """KIRO2 için üniversite entegrasyonunu başlat"""
        await self.hub.initialize()
        
        # Kimlik bilgilerini ekle
        for university_code, creds in credentials.items():
            self.hub.add_university_credentials(university_code, creds)
        
        # Popüler verileri önceden yükle
        await self.hub.preload_popular_data()
        
        self.initialized = True
        logging.info("KIRO2 University Integration Manager initialized")
    
    async def get_personalized_university_recommendations(self, 
                                                        student_scores: Dict[str, float],
                                                        preferences: Dict[str, Any]) -> Dict:
        """Kişiselleştirilmiş üniversite önerileri"""
        if not self.initialized:
            raise Exception("University Integration not initialized")
        
        recommendations = await self.hub.analyze_university_preferences_for_kiro2(
            student_scores=student_scores,
            preferred_cities=preferences.get("cities", []),
            preferred_faculties=preferences.get("faculties", [])
        )
        
        # KIRO2 özel analiz ekle
        recommendations["kiro2_analysis"] = {
            "study_plan_suggestions": self._generate_study_plan_suggestions(
                recommendations, student_scores
            ),
            "improvement_areas": self._identify_improvement_areas(
                student_scores, recommendations
            ),
            "timeline_recommendations": self._create_study_timeline(
                recommendations
            )
        }
        
        return recommendations
    
    def _generate_study_plan_suggestions(self, recommendations: Dict, 
                                       scores: Dict[str, float]) -> List[str]:
        """Çalışma planı önerileri oluştur"""
        suggestions = []
        
        if recommendations["recommended_universities"]:
            suggestions.append(
                "Hedef üniversitelerinize odaklanarak mevcut seviyenizi koruyun"
            )
        
        if recommendations["reachable_departments"]:
            suggestions.append(
                "Erişilebilir bölümler için 20-30 puan daha fazla çalışma yapın"
            )
        
        if len(recommendations["backup_options"]) > len(recommendations["recommended_universities"]):
            suggestions.append(
                "Temel konulara dönüp eksikliklerinizi giderin"
            )
        
        return suggestions
    
    def _identify_improvement_areas(self, scores: Dict[str, float], 
                                  recommendations: Dict) -> List[str]:
        """Geliştirilmesi gereken alanları belirle"""
        areas = []
        
        # Düşük puanlı alanlar
        avg_score = sum(scores.values()) / len(scores)
        for subject, score in scores.items():
            if score < avg_score * 0.8:
                areas.append(f"{subject} alanında yoğunlaşın")
        
        return areas
    
    def _create_study_timeline(self, recommendations: Dict) -> Dict:
        """Çalışma zaman çizelgesi oluştur"""
        if recommendations["recommended_universities"]:
            return {"phase": "Koruma ve pekiştirme", "duration": "2-3 ay"}
        elif recommendations["reachable_departments"]:
            return {"phase": "Yoğun çalışma", "duration": "4-6 ay"}
        else:
            return {"phase": "Temel konular", "duration": "6-8 ay"}


# === Örnek Kullanım ===

async def example_university_integration():
    """Üniversite entegrasyonu örnek kullanımı"""
    
    # Entegrasyon yöneticisini başlat
    manager = KIRO2UniversityIntegrationManager()
    
    # Kimlik bilgileri
    credentials = {
        "yok": {
            "api_key": "KIRO2_YOK_API_KEY",
            "username": "kiro2_system"
        },
        "101": {  # İTÜ örneği
            "username": "kiro2_system",
            "password": "secure_password",
            "api_key": "ITU_API_KEY"
        }
    }
    
    await manager.initialize_for_kiro2(credentials)
    
    # Öğrenci puanları
    student_scores = {
        "TYT": 350.5,
        "AYT_Sayısal": 420.8,
        "AYT_Sözel": 380.2
    }
    
    # Öğrenci tercihleri
    preferences = {
        "cities": ["İstanbul", "Ankara", "İzmir"],
        "faculties": [FacultyType.ENGINEERING, FacultyType.SCIENCE]
    }
    
    # Kişiselleştirilmiş öneriler al
    recommendations = await manager.get_personalized_university_recommendations(
        student_scores, preferences
    )
    
    print("KIRO2 Üniversite Önerileri:")
    print(f"Önerilen Üniversiteler: {len(recommendations['recommended_universities'])}")
    print(f"Erişilebilir Bölümler: {len(recommendations['reachable_departments'])}")
    print(f"Yedek Seçenekler: {len(recommendations['backup_options'])}")
    
    if recommendations["kiro2_analysis"]["study_plan_suggestions"]:
        print("\nÇalışma Planı Önerileri:")
        for suggestion in recommendations["kiro2_analysis"]["study_plan_suggestions"]:
            print(f"- {suggestion}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_university_integration())