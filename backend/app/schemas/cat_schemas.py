"""
KIRO2 — CAT API Schemas
========================
Request/Response Pydantic modelleri.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Request ──────────────────────────────────────────────────────


class StartSessionRequest(BaseModel):
    subject_id: str = Field(..., description="Ders kodu (örn: MATEMATIK, TURKCE)")

    model_config = ConfigDict(
        json_schema_extra={"example": {"subject_id": "MATEMATIK"}}
    )


class SubmitAnswerRequest(BaseModel):
    question_id: str = Field(..., description="Yanıtlanan soru ID'si")
    selected_option: str | None = Field(
        None, min_length=1, max_length=1, description="Seçilen şık (A/B/C/D)"
    )
    answer: str | None = Field(None, description="selected_option aliası")
    response_ms: int | None = Field(
        None,
        ge=0,
        le=300_000,
        description="Yanıt süresi (ms), opsiyonel — fatigue detection için",
    )

    def get_selected(self) -> str:
        """selected_option veya answer field'ından seçimi al."""
        return (self.selected_option or self.answer or "").upper()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "660e8400-e29b-41d4-a716-446655440001",
                "selected_option": "B",
                "response_ms": 12500,
            }
        }
    )


# ── Response ─────────────────────────────────────────────────────


class IRTInfo(BaseModel):
    difficulty: float
    discrimination: float
    guessing: float


class QuestionResponse(BaseModel):
    question_id: str
    stem: str
    options: dict[str, Any]  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    topic_id: str
    subject_id: str
    irt: IRTInfo
    # Image fields (optional — frontend renders only if question_image_url present)
    question_image_url: str | None = None
    image_alt_text: str | None = None
    image_width: int | None = None
    image_height: int | None = None


class FeedbackResponse(BaseModel):
    is_correct: bool
    correct_option: str | None = None  # Bitiş sonrası açıklanabilir


class StartSessionResponse(BaseModel):
    session_id: str
    question: QuestionResponse
    theta: float = Field(description="Mevcut θ tahmini")
    se: float = Field(description="Standart hata (0→1, düşük=iyi)")
    n_questions: int
    phase: str  # warm_up | core
    is_complete: bool = False


class SubmitAnswerResponse(BaseModel):
    is_complete: bool
    theta: float
    se: float
    n_questions: int
    termination_reason: str | None = None
    next_question: QuestionResponse | None = None
    phase: str | None = None
    feedback: FeedbackResponse


class SessionStateResponse(BaseModel):
    session_id: str
    state: str  # active | completed | abandoned
    theta: float
    se: float
    n_questions: int
    warm_up_done: bool


# ── POST /api/v1/cat/next — yerleştirme adaptörü ─────────────────
# Alan adları frontend sözleşmesiyle BİREBİR (Türkçe, camelCase):
# frontend/src/kiro/api/api-client.ts:356-366 CatNextArgs / CatNextResult.
# Bu şemalar snake_case'e çevrilmez — sözleşme kaynağı istemcidir.

# Ekranın SEVIYE sözlüğünde fallback YOKTUR; dördüncü bir değer TypeError üretir.
# Tip alias olarak tanımlanır (satır-içi Literal[...] yazımı repo formatlayıcısı
# tarafından tırnaksız bırakılıp ForwardRef'e dönüşüyor).
SeviyeBandi = Literal["zayif", "orta", "guclu"]


class CatNextRequest(BaseModel):
    oturumId: str | None = Field(  # noqa: N815
        None, description="Sunucunun cat_sid çerezine alternatif"
    )
    maddeId: str | None = Field(  # noqa: N815
        None, description="Cevaplanan sorunun id'si; yoksa yeni oturum"
    )
    secim: int | None = Field(
        None,
        ge=0,
        le=4,
        description="0-tabanlı şık indeksi (0=A). null = 'Emin değilim'",
    )
    madde: int | None = Field(
        None, ge=0, description="İstemci sayacı — sunucu OTORİTER, yalnız teşhis için"
    )


class CatNextItem(BaseModel):
    """Öğrenciye giden madde. `dogru` alanı KASITLI OLARAK YOKTUR."""

    id: str
    b: float
    konu: str
    soru: str
    secenekler: list[str]


class CatUygulananItem(BaseModel):
    """Uygulanmış bir madde ve SONRASINDAKİ θ/SE — motor panelinin yakınsama grafiği."""

    b: float
    ok: bool
    theta: float
    se: float


class CatNextResponse(BaseModel):
    item: CatNextItem
    theta: float
    se: float
    done: bool
    seviye: SeviyeBandi
    topPct: int  # noqa: N815
    netTahmini: int  # noqa: N815
    madde: int
    kalanTahmini: int  # noqa: N815
    guvenilirlik: int
    uygulananlar: list[CatUygulananItem]
