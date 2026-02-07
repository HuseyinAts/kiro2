"""
İçerik Yönetim Sistemi - Pydantic Modelleri
Teknofest 2025 Eğitim Eylemci Platformu
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4
import re
from urllib.parse import urlparse


class ContentType(str, Enum):
    """İçerik türleri"""

    MAKALE = "makale"
    VIDEO = "video"
    QUIZ = "quiz"
    INFOGRAFIK = "infografik"
    PODCAST = "podcast"
    DOKUMAN = "dokuman"


class InteractionType(str, Enum):
    """Etkileşim türleri"""

    VIEW = "view"
    LIKE = "like"
    SHARE = "share"
    COMMENT = "comment"
    BOOKMARK = "bookmark"
    DOWNLOAD = "download"


class MakaleIcerik(BaseModel):
    """Makale içerik modeli"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    baslik: str = Field(..., min_length=3, max_length=200, description="Makale başlığı")
    icerik: str = Field(..., min_length=50, description="Makale içeriği")
    ozet: Optional[str] = Field(None, max_length=500, description="Makale özeti")
    kategori: str = Field(..., description="Makale kategorisi")
    yazar: str = Field(..., description="Makale yazarı")
    yazar_id: Optional[str] = Field(None, description="Yazar kullanıcı ID'si")
    etiketler: List[str] = Field(default_factory=list, description="Makale etiketleri")
    okunma_suresi: int = Field(
        default=1, ge=1, description="Tahmini okuma süresi (dakika)"
    )
    goruntuleme_sayisi: int = Field(default=0, ge=0, description="Görüntülenme sayısı")
    begeni_sayisi: int = Field(default=0, ge=0, description="Beğeni sayısı")
    yayinlanma_tarihi: datetime = Field(default_factory=datetime.now)
    guncellenme_tarihi: Optional[datetime] = Field(None)
    aktif: bool = Field(default=True, description="İçerik aktif mi?")
    dil: str = Field(default="tr", description="İçerik dili")
    zorluk_seviyesi: Optional[str] = Field(None, description="Zorluk seviyesi")

    @field_validator("baslik")
    @classmethod
    def validate_baslik(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Başlık en az 3 karakter olmalıdır")
        return v.strip()

    @field_validator("etiketler")
    @classmethod
    def validate_etiketler(cls, v):
        if len(v) > 10:
            raise ValueError("En fazla 10 etiket eklenebilir")
        # Etiketleri küçük harfe çevir
        return [tag.lower().strip() for tag in v if tag.strip()]

    @field_validator("okunma_suresi")
    @classmethod
    def calculate_reading_time(cls, v, info):
        if info.data and "icerik" in info.data and info.data["icerik"]:
            # Ortalama okuma hızı: 200 kelime/dakika
            kelime_sayisi = len(info.data["icerik"].split())
            hesaplanan_sure = max(1, kelime_sayisi // 200)
            return hesaplanan_sure
        return v

    def get_summary(self, max_length: int = 150) -> str:
        """Otomatik özet oluştur"""
        if self.ozet:
            return self.ozet

        # Basit özet oluşturma
        sentences = self.icerik.split(".")
        summary = sentences[0] if sentences else self.icerik

        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary

    model_config = ConfigDict()


class VideoIcerik(BaseModel):
    """Video içerik modeli"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    baslik: str = Field(..., min_length=3, max_length=200, description="Video başlığı")
    aciklama: Optional[str] = Field(
        None, max_length=1000, description="Video açıklaması"
    )
    video_url: str = Field(..., description="Video URL'i")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL'i")
    kategori: str = Field(..., description="Video kategorisi")
    platform: str = Field(default="youtube", description="Video platformu")
    platform_id: Optional[str] = Field(None, description="Platform video ID'si")
    sure: int = Field(
        default=0, ge=0, le=14400, description="Video süresi (saniye)"
    )  # Max 4 saat
    kalite: str = Field(default="720p", description="Video kalitesi")
    dil: str = Field(default="tr", description="Video dili")
    altyazi_var: bool = Field(default=False, description="Altyazı var mı?")
    yayinlayan: str = Field(..., description="Video yayınlayan")
    yayinlayan_id: Optional[str] = Field(None, description="Yayınlayan kullanıcı ID'si")
    izlenme_sayisi: int = Field(default=0, ge=0, description="İzlenme sayısı")
    begeni_sayisi: int = Field(default=0, ge=0, description="Beğeni sayısı")
    yayinlanma_tarihi: datetime = Field(default_factory=datetime.now)
    guncellenme_tarihi: Optional[datetime] = Field(None)
    aktif: bool = Field(default=True, description="İçerik aktif mi?")
    zorluk_seviyesi: Optional[str] = Field(None, description="Zorluk seviyesi")

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, v):
        """Video URL validasyonu"""
        allowed_domains = [
            "youtube.com",
            "youtu.be",
            "www.youtube.com",
            "vimeo.com",
            "www.vimeo.com",
            "dailymotion.com",
            "www.dailymotion.com",
        ]

        try:
            parsed = urlparse(v)
            if not any(domain in parsed.netloc for domain in allowed_domains):
                raise ValueError(
                    f'Desteklenmeyen video platformu. Desteklenen: {", ".join(allowed_domains)}'
                )
        except Exception:
            raise ValueError("Geçersiz URL formatı")

        return v

    @field_validator("sure")
    @classmethod
    def validate_duration(cls, v):
        if v > 14400:  # 4 saat
            raise ValueError("Video süresi 4 saatten fazla olamaz")
        return v

    def get_duration_minutes(self) -> int:
        """Video süresini dakika olarak döndür"""
        return self.sure // 60

    def get_duration_formatted(self) -> str:
        """Video süresini HH:MM:SS formatında döndür"""
        hours = self.sure // 3600
        minutes = (self.sure % 3600) // 60
        seconds = self.sure % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def extract_platform_id(self) -> Optional[str]:
        """URL'den platform ID'sini çıkar"""
        if "youtube.com" in self.video_url or "youtu.be" in self.video_url:
            # YouTube ID çıkarma
            patterns = [
                r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
                r"youtu\.be\/([0-9A-Za-z_-]{11})",
            ]
            for pattern in patterns:
                match = re.search(pattern, self.video_url)
                if match:
                    return match.group(1)

        return None

    model_config = ConfigDict()


class QuizIcerik(BaseModel):
    """Quiz içerik modeli"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    baslik: str = Field(..., min_length=3, max_length=200)
    aciklama: Optional[str] = Field(None, max_length=500)
    kategori: str = Field(...)
    olusturan: str = Field(...)
    olusturan_id: Optional[str] = Field(None)
    soru_sayisi: int = Field(default=0, ge=0)
    sure_limiti: Optional[int] = Field(None, ge=60)  # Minimum 1 dakika
    zorluk_seviyesi: str = Field(default="orta")
    aktif: bool = Field(default=True)
    olusturulma_tarihi: datetime = Field(default_factory=datetime.now)
    guncellenme_tarihi: Optional[datetime] = Field(None)

    model_config = ConfigDict()


class ContentInteraction(BaseModel):
    """İçerik etkileşim modeli"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="Kullanıcı ID'si")
    content_id: str = Field(..., description="İçerik ID'si")
    content_type: ContentType = Field(..., description="İçerik türü")
    interaction_type: InteractionType = Field(..., description="Etkileşim türü")
    interaction_data: Optional[Dict[str, Any]] = Field(
        None, description="Ek etkileşim verisi"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = Field(None, description="Oturum ID'si")
    device_info: Optional[Dict[str, str]] = Field(None, description="Cihaz bilgisi")

    model_config = ConfigDict()


class ContentStats(BaseModel):
    """İçerik istatistik modeli"""

    content_id: str = Field(..., description="İçerik ID'si")
    content_type: ContentType = Field(..., description="İçerik türü")
    total_views: int = Field(default=0, ge=0)
    total_likes: int = Field(default=0, ge=0)
    total_shares: int = Field(default=0, ge=0)
    total_comments: int = Field(default=0, ge=0)
    total_bookmarks: int = Field(default=0, ge=0)
    average_rating: Optional[float] = Field(None, ge=0, le=5)
    engagement_rate: Optional[float] = Field(None, ge=0, le=100)
    last_updated: datetime = Field(default_factory=datetime.now)

    def calculate_engagement_rate(self) -> float:
        """Etkileşim oranını hesapla"""
        if self.total_views == 0:
            return 0.0

        total_interactions = (
            self.total_likes
            + self.total_shares
            + self.total_comments
            + self.total_bookmarks
        )

        return (total_interactions / self.total_views) * 100

    model_config = ConfigDict()


class ContentFilter(BaseModel):
    """İçerik filtreleme modeli"""

    content_types: Optional[List[ContentType]] = Field(None)
    kategoriler: Optional[List[str]] = Field(None)
    etiketler: Optional[List[str]] = Field(None)
    zorluk_seviyesi: Optional[str] = Field(None)
    dil: Optional[str] = Field(None)
    baslangic_tarihi: Optional[datetime] = Field(None)
    bitis_tarihi: Optional[datetime] = Field(None)
    min_sure: Optional[int] = Field(None, ge=0)
    max_sure: Optional[int] = Field(None, ge=0)
    sadece_aktif: bool = Field(default=True)

    @field_validator("max_sure")
    @classmethod
    def validate_sure_range(cls, v, info):
        if (
            v is not None
            and info.data
            and "min_sure" in info.data
            and info.data["min_sure"] is not None
        ):
            if v < info.data["min_sure"]:
                raise ValueError("Maksimum süre minimum süreden küçük olamaz")
        return v


class ContentSearchRequest(BaseModel):
    """İçerik arama isteği modeli"""

    query: str = Field(..., min_length=2, max_length=100)
    filters: Optional[ContentFilter] = Field(None)
    sort_by: str = Field(default="relevance")  # relevance, date, popularity, rating
    sort_order: str = Field(default="desc")  # asc, desc
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    highlight: bool = Field(default=True)

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v):
        allowed_values = ["relevance", "date", "popularity", "rating", "duration"]
        if v not in allowed_values:
            raise ValueError(
                f'sort_by değeri şunlardan biri olmalı: {", ".join(allowed_values)}'
            )
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError('sort_order değeri "asc" veya "desc" olmalı')
        return v


class BulkContentImport(BaseModel):
    """Toplu içerik yükleme modeli"""

    task_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="Yükleyen kullanıcı ID'si")
    file_name: str = Field(..., description="Yüklenen dosya adı")
    file_type: str = Field(..., description="Dosya türü (csv, json)")
    total_records: int = Field(default=0, ge=0)
    processed_records: int = Field(default=0, ge=0)
    successful_records: int = Field(default=0, ge=0)
    failed_records: int = Field(default=0, ge=0)
    status: str = Field(default="pending")  # pending, processing, completed, failed
    error_details: Optional[List[Dict[str, Any]]] = Field(None)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed_statuses = ["pending", "processing", "completed", "failed", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(
                f'Status şunlardan biri olmalı: {", ".join(allowed_statuses)}'
            )
        return v

    def get_progress_percentage(self) -> float:
        """İlerleme yüzdesini hesapla"""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100

    def get_success_rate(self) -> float:
        """Başarı oranını hesapla"""
        if self.processed_records == 0:
            return 0.0
        return (self.successful_records / self.processed_records) * 100

    model_config = ConfigDict()
