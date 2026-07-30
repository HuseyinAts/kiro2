"""
Pydantic Schemas for Zemberek NLP Tools

Defines input/output schemas for all 9 tools as per spec design.md.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

# ============================================
# Enums
# ============================================


class EntityType(str, Enum):
    """Entity types for Named Entity Recognition (REQ-5)"""

    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    DATE = "DATE"
    TIME = "TIME"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    UNKNOWN = "UNKNOWN"


# ============================================
# Morphological Analysis (REQ-1)
# ============================================


class MorphologyAnalysis(BaseModel):
    """Single morphological analysis result."""

    root: str = Field(..., description="Kelime kökü")
    lemma: str = Field(..., description="Lemma (sözlük formu)")
    pos: str = Field(..., description="Part of speech (isim, fiil, etc.)")
    suffixes: list[str] = Field(default_factory=list, description="Ekler listesi")
    morphemes: list[str] = Field(default_factory=list, description="Morfem listesi")
    formatted: str = Field(default="", description="Formatlanmış analiz")
    is_proper_noun: bool = Field(default=False, description="Özel isim mi")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Güven skoru")


class WordAnalysis(BaseModel):
    """Analysis result for a single word."""

    word: str = Field(..., description="Analiz edilen kelime")
    analyses: list[MorphologyAnalysis] = Field(
        default_factory=list, description="Analiz sonuçları"
    )
    analysis_count: int = Field(default=0, description="Analiz sayısı")
    error: Optional[str] = Field(default=None, description="Hata mesajı (varsa)")


class MorphologyResult(BaseModel):
    """Complete morphological analysis result."""

    text: str = Field(..., description="Orijinal metin")
    word_analyses: list[WordAnalysis] = Field(..., description="Kelime analizleri")
    total_words: int = Field(..., description="Toplam kelime sayısı")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")


# ============================================
# Lemmatization (REQ-2)
# ============================================


class LemmaResult(BaseModel):
    """Lemma result for a single word."""

    word: str = Field(..., description="Orijinal kelime")
    lemma: str = Field(..., description="Lemma (kök form)")


class LemmatizationResult(BaseModel):
    """Complete lemmatization result."""

    text: str = Field(..., description="Orijinal metin")
    lemmas: list[LemmaResult] = Field(..., description="Lemma sonuçları")
    total_words: int = Field(..., description="Toplam kelime sayısı")
    throughput_wps: float = Field(default=0.0, description="İşlem hızı (kelime/saniye)")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")


# ============================================
# Spell Check (REQ-3)
# ============================================


class SpellCheckWord(BaseModel):
    """Spell check result for a single word."""

    word: str = Field(..., description="Kontrol edilen kelime")
    is_correct: bool = Field(..., description="Yazım doğru mu")
    suggestions: list[str] = Field(
        default_factory=list, description="Düzeltme önerileri"
    )
    error_type: Optional[str] = Field(
        default=None, description="Hata tipi (diacritic, typo, etc.)"
    )


class SpellCheckResult(BaseModel):
    """Complete spell check result."""

    text: str = Field(..., description="Orijinal metin")
    words: list[SpellCheckWord] = Field(..., description="Kelime kontrol sonuçları")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Doğruluk oranı")
    error_count: int = Field(default=0, description="Hata sayısı")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")


# ============================================
# Tokenization (REQ-4)
# ============================================


class TokenizationResult(BaseModel):
    """Complete tokenization result."""

    text: str = Field(..., description="Orijinal metin")
    tokens: list[str] = Field(..., description="Token listesi")
    token_count: int = Field(..., description="Token sayısı")
    # BPE subword tokenization (REQ-4.6)
    subword_tokens: Optional[list[str]] = Field(
        default=None, description="BPE subword token listesi (use_subword=true ise)"
    )
    subword_token_count: Optional[int] = Field(
        default=None, description="BPE subword token sayısı"
    )
    has_url: bool = Field(default=False, description="URL içeriyor mu")
    has_email: bool = Field(default=False, description="Email içeriyor mu")
    has_number: bool = Field(default=False, description="Sayı içeriyor mu")
    has_abbreviation: bool = Field(default=False, description="Kısaltma içeriyor mu")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")


# ============================================
# Named Entity Recognition (REQ-5)
# ============================================


class NamedEntity(BaseModel):
    """A named entity found in text."""

    text: str = Field(..., description="Entity metni")
    type: str = Field(..., description="Entity tipi (PERSON, LOCATION, ORGANIZATION)")
    start: int = Field(..., ge=0, description="Başlangıç pozisyonu")
    end: int = Field(..., ge=0, description="Bitiş pozisyonu")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Güven skoru")


class NERResult(BaseModel):
    """Complete NER result."""

    text: str = Field(..., description="Orijinal metin")
    entities: list[NamedEntity] = Field(..., description="Bulunan entity'ler")
    entity_count: int = Field(default=0, description="Entity sayısı")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")


# ============================================
# Sentence Segmentation (REQ-6)
# ============================================


class Sentence(BaseModel):
    """A segmented sentence."""

    text: str = Field(..., description="Cümle metni")
    index: int = Field(..., ge=0, description="Cümle indexi")
    start: int = Field(default=0, ge=0, description="Başlangıç pozisyonu")
    end: int = Field(default=0, ge=0, description="Bitiş pozisyonu")


class SentenceSegmentationResult(BaseModel):
    """Complete segmentation result."""

    text: str = Field(..., description="Orijinal metin")
    sentences: list[Sentence] = Field(..., description="Cümleler")
    sentence_count: int = Field(..., description="Cümle sayısı")
    has_question: bool = Field(default=False, description="Soru cümlesi var mı")
    has_dialog: bool = Field(default=False, description="Diyalog var mı")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")


# ============================================
# Normalization (REQ-7)
# ============================================


class NormalizationChange(BaseModel):
    """A single normalization change."""

    original: str = Field(..., description="Orijinal metin")
    normalized: str = Field(..., description="Normalize edilmiş metin")
    change_type: str = Field(default="unknown", description="Değişiklik tipi")
    position: int = Field(default=0, ge=0, description="Pozisyon")


class NormalizationResult(BaseModel):
    """Complete normalization result."""

    original: str = Field(..., description="Orijinal metin")
    normalized: str = Field(..., description="Normalize edilmiş metin")
    changes: list[NormalizationChange] = Field(
        default_factory=list, description="Yapılan değişiklikler"
    )
    change_count: int = Field(default=0, description="Değişiklik sayısı")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")


# ============================================
# Health Check (REQ-8.6)
# ============================================


class ComponentStatus(BaseModel):
    """Status of a Zemberek component."""

    name: str = Field(..., description="Bileşen adı")
    available: bool = Field(..., description="Kullanılabilir mi")
    latency_ms: Optional[float] = Field(default=None, description="Gecikme (ms)")


class HealthCheckResult(BaseModel):
    """Complete health check result."""

    status: str = Field(..., description="Genel durum (healthy/unhealthy)")
    backend_mode: str = Field(..., description="Backend modu (jpype/http)")
    jpype_initialized: bool = Field(default=False, description="JPype başlatıldı mı")
    jvm_memory_mb: Optional[int] = Field(
        default=None, description="JVM bellek kullanımı (MB)"
    )
    components: dict[str, bool] = Field(
        default_factory=dict, description="Bileşen durumları"
    )
    cache: Optional[dict[str, Any]] = Field(default=None, description="Cache durumu")
    version: str = Field(default="1.0.0", description="Server versiyonu")


# ============================================
# Entity Linking (Advanced Feature)
# ============================================


class LinkedEntity(BaseModel):
    """An entity linked to knowledge base."""

    text: str = Field(..., description="Entity metni")
    type: str = Field(..., description="Entity tipi")
    start: int = Field(..., ge=0, description="Başlangıç pozisyonu")
    end: int = Field(..., ge=0, description="Bitiş pozisyonu")
    kb_id: Optional[str] = Field(default=None, description="Knowledge base ID")
    kb_label: Optional[str] = Field(default=None, description="KB etiketi")
    kb_description: Optional[str] = Field(default=None, description="KB açıklaması")
    kb_url: Optional[str] = Field(default=None, description="KB URL")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Güven skoru")


class EntityLinkResult(BaseModel):
    """Complete entity linking result."""

    text: str = Field(..., description="Orijinal metin")
    linked_entities: list[LinkedEntity] = Field(
        default_factory=list, description="Bağlanmış entity'ler"
    )
    unlinked_entities: list[LinkedEntity] = Field(
        default_factory=list, description="Bağlanmamış entity'ler"
    )
    total_entities: int = Field(default=0, description="Toplam entity sayısı")
    linked_count: int = Field(default=0, description="Bağlanan entity sayısı")
    link_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Bağlanma oranı")
    backend: str = Field(default="jpype", description="Kullanılan backend")
    cached: bool = Field(default=False, description="Cache'den mi geldi")
