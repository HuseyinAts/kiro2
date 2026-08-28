"""Teacher Co-Pilot API (2026 Q3-Q4)

Öğretmenlerin sınıflarındaki öğrencilerin ZPD (Yakınsal Gelişim Alanı) seviyelerini,
FSRS-6 unutma eğrilerini (% Retention) ve yapay zeka tarafından üretilen
Kavram Yanılgısı (Misconception Risk) uyarılarını sunan API servisleridir.
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.ddos_protection import limiter
from core.mock_endpoint_flags import is_real_impl

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/teacher-copilot", tags=["teacher-copilot"])

# --- MOCK BEYANI (7 Agu 2026) --------------------------------------------
# Bu ucların DONDURDUGU HER SEY SABIT. Olculdu: total_students=32 sabit, ZPD
# dagilimi bu sayinin %25/%60/%15'i, FSRS oranlari sabit (84.2 / 48).
# Gercek uygulama yazilamiyor cunku veri canlida yok:
#     user_item_fsrs             = 1 satir
#     student_learning_profiles  = 2 satir
#     student_question_flags     = 0 satir
# Bagladigimizda pano bos gorunurdu. Bu yuzden mock KALIYOR ama KENDINI
# beyan ediyor (`data_source`) ve bayrak sistemine kayitli.
# Veri birikince: gercek toplayiciyi yaz -> bayragi true cevir -> 501 kalkar.
_FLAG_DASHBOARD = "teacher_copilot.dashboard_analytics"
_FLAG_ALERTS = "teacher_copilot.misconception_alerts"

_NO_REAL_IMPL_DETAIL = (
    "Bu ucun gercek uygulamasi henuz yok; bayrak true olsa bile sessizce mock "
    "veri donulmez. Gerekli veri canlida yetersiz (user_item_fsrs=1, "
    "student_learning_profiles=2, student_question_flags=0)."
)


def _guard_real_impl(flag: str) -> None:
    """Bayrak true ise 501 at — sessiz mock, operatore yalan soylemektir.

    Depo emsali: gorev #318-321 (dispatcher + NotImplementedError scaffold).
    """
    if is_real_impl(flag):
        raise HTTPException(status_code=501, detail=_NO_REAL_IMPL_DETAIL)


def _get_auth_dep():
    try:
        from core.dependencies import get_current_user

        return Depends(get_current_user)
    except ImportError:
        _is_dev = os.getenv("ENVIRONMENT", "development") == "development"
        if _is_dev:

            async def _noop_auth() -> None:
                return None

            return Depends(_noop_auth)
        raise RuntimeError("Auth required in production.")


def _get_db_dep():
    try:
        from core.dependencies import get_db

        return Depends(get_db)
    except ImportError:

        async def _noop_db() -> None:
            return None

        return Depends(_noop_db)


_auth_dep = _get_auth_dep()
_db_dep = _get_db_dep()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ZPDDistribution(BaseModel):
    scaffolding_needed: int = Field(
        ..., description="Rehberlik / Destek İhtiyacı Olan Öğrenciler"
    )
    independent_mastery: int = Field(
        ..., description="Bağımsız Çözüm Seviyesindeki Öğrenciler"
    )
    advanced_mastery: int = Field(
        ..., description="İleri / Zirve Seviyedeki Öğrenciler"
    )
    scaffolding_percentage: float = 25.0
    independent_percentage: float = 60.0
    advanced_percentage: float = 15.0


class FSRSRetentionSummary(BaseModel):
    average_retention_rate: float = Field(
        ..., description="Sınıf Ortalama Hafızada Tutma Oranı (%)"
    )
    decay_risk_cards_count: int = Field(
        ..., description="Unutma Riski Taşıyan Kart Sayısı"
    )
    decay_risk_topics: list[str] = Field(default_factory=list)
    recommended_review_date: str = ""


class MisconceptionAlert(BaseModel):
    alert_id: str
    class_id: str
    subject: str
    topic: str
    risk_level: str = "HIGH"  # HIGH, MEDIUM, LOW
    affected_students_count: int
    misconception_title: str
    ai_socratic_recommendation: str
    created_at: str


class TeacherCoPilotAnalyticsResponse(BaseModel):
    class_id: str
    class_name: str
    total_students: int
    zpd_distribution: ZPDDistribution
    fsrs_retention: FSRSRetentionSummary
    misconception_alerts: list[MisconceptionAlert]
    timestamp: str


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
@router.get("/dashboard-analytics")
@limiter.limit("20/minute")
async def get_dashboard_analytics(
    request: Request,
    response: Response,
    class_id: str = Query(default="12-A"),
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> dict[str, Any]:
    """Öğretmen Co-Pilot ZPD & FSRS unutma eğrisi analitiğini döndürür.

    UYARI: Bu uç SABIT (mock) veri döndürür — yanıttaki `data_source` alanına bak.
    """
    _guard_real_impl(_FLAG_DASHBOARD)
    now_iso = datetime.now(UTC).isoformat()

    # MOCK / Real DB Aggregation Fallback
    total_students = 32
    if db is not None:
        try:
            r = await db.execute(
                text(
                    "SELECT COUNT(*) FROM users WHERE is_active = true AND role = 'student'"
                )
            )
            count = r.scalar_one_or_none()
            if count and count > 0:
                total_students = min(count, 50)
        except Exception as e:
            logger.debug(f"DB student count fallback: {e}")

    scaffolding_count = max(1, int(total_students * 0.25))
    independent_count = max(1, int(total_students * 0.60))
    advanced_count = max(1, total_students - scaffolding_count - independent_count)

    zpd = ZPDDistribution(
        scaffolding_needed=scaffolding_count,
        independent_mastery=independent_count,
        advanced_mastery=advanced_count,
        scaffolding_percentage=round((scaffolding_count / total_students) * 100, 1),
        independent_percentage=round((independent_count / total_students) * 100, 1),
        advanced_percentage=round((advanced_count / total_students) * 100, 1),
    )

    fsrs = FSRSRetentionSummary(
        average_retention_rate=84.2,
        decay_risk_cards_count=48,
        decay_risk_topics=[
            "Türevde Ekstremum Noktaları",
            "Trigonometri Toplam-Fark Formülleri",
            "Paragrafta Anlatım Biçimleri",
        ],
        recommended_review_date="2026-08-10",
    )

    alerts = [
        MisconceptionAlert(
            alert_id="alert-01",
            class_id=class_id,
            subject="Matematik",
            topic="Türev",
            risk_level="HIGH",
            affected_students_count=12,
            misconception_title="Teğet Eğimi ile Yerel Ekstremum Karıştırılması",
            ai_socratic_recommendation="Öğrencilere türevin sıfır olduğu her noktanın ekstremum olmadığını gösteren karşıt örnek (f(x)=x³) sorusu yöneltin.",
            created_at=now_iso,
        ),
        MisconceptionAlert(
            alert_id="alert-02",
            class_id=class_id,
            subject="Fizik",
            topic="Kuvvet ve Hareket",
            risk_level="MEDIUM",
            affected_students_count=8,
            misconception_title="Net Kuvvet Sıfırken Hızın Sıfır Kabul Edilmesi",
            ai_socratic_recommendation="Eylemsizlik prensibini hatırlatarak 'Sabit hızla ilerleyen bir araca etki eden net kuvvet nedir?' Sokratik sorusunu sorun.",
            created_at=now_iso,
        ),
    ]

    resp_data = TeacherCoPilotAnalyticsResponse(
        class_id=class_id,
        class_name=f"Sınıf {class_id} (YKS Sayısal Maratonu)",
        total_students=total_students,
        zpd_distribution=zpd,
        fsrs_retention=fsrs,
        misconception_alerts=alerts,
        timestamp=now_iso,
    )

    return {
        "success": True,
        "data_source": "mock",
        "data": resp_data.model_dump(),
        "timestamp": now_iso,
    }


@router.get("/misconception-alerts")
@limiter.limit("20/minute")
async def get_misconception_alerts(
    request: Request,
    response: Response,
    class_id: str = Query(default="12-A"),
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> dict[str, Any]:
    """Sınıf bazlı detaylı AI Kavram Yanılgısı risk listesini döndürür.

    UYARI: Bu uç SABIT (mock) veri döndürür — yanıttaki `data_source` alanına bak.
    Öğrenci adları bilerek sentetik: gerçekçi ad kullanmak, mock'u gerçek
    sandırır (Blocker #6'da uydurma öğrenci fallback'i tam bu yüzden silindi).
    """
    _guard_real_impl(_FLAG_ALERTS)
    now_iso = datetime.now(UTC).isoformat()
    return {
        "success": True,
        "data_source": "mock",
        "class_id": class_id,
        "alerts": [
            {
                "alert_id": "alert-01",
                "subject": "Matematik",
                "topic": "Türev",
                "risk_level": "HIGH",
                "affected_students": [
                    "[ÖRNEK] Öğrenci 1",
                    "[ÖRNEK] Öğrenci 2",
                    "[ÖRNEK] Öğrenci 3",
                    "[ÖRNEK] Öğrenci 4",
                ],
                "misconception": "Türevin sıfır olduğu her noktayı yerel ekstremum sanma hatası",
                "socratic_prompt": "x³ fonksiyonunun x=0'daki türevi kaçtır ve bu nokta dönüm noktası mıdır?",
            },
            {
                "alert_id": "alert-02",
                "subject": "Fizik",
                "topic": "Elektrik",
                "risk_level": "MEDIUM",
                "affected_students": ["[ÖRNEK] Öğrenci 5", "[ÖRNEK] Öğrenci 6"],
                "misconception": "Paralel bağlı dirençlerde toplam direncin artacağını düşünme",
                "socratic_prompt": "Paralel kola yeni bir direnç eklendiğinde devrenin eşdeğer direnci nasıl değişir?",
            },
        ],
        "timestamp": now_iso,
    }
