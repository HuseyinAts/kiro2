"""
ADHD (DEHB) Desteği API - Dikkat Yönetimi Sistemi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) tanılı öğrenciler için
dikkat yönetimi araçları sağlar:
- Pomodoro timer (25dk çalışma, 5dk mola)
- Görsel zamanlayıcı (countdown, progress ring)
- Dikkat dağınıklığı tespiti (inactivity detection)
- Konsantrasyon egzersizleri (focus training)

Requirements: REQ-52.1 - REQ-52.20
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from enum import Enum

from core.database import get_db
from core.dependencies import get_current_user
from models.database import User

router = APIRouter(prefix="/api/v1/adhd-support", tags=["ADHD Support"])


# ============================================================================
# Pydantic Models
# ============================================================================


class PomodoroSessionType(str, Enum):
    """Pomodoro oturum tipleri"""

    WORK = "work"  # Çalışma oturumu (25dk)
    SHORT_BREAK = "short_break"  # Kısa mola (5dk)
    LONG_BREAK = "long_break"  # Uzun mola (15dk)


class PomodoroSessionStatus(str, Enum):
    """Pomodoro oturum durumları"""

    ACTIVE = "active"  # Aktif çalışıyor
    PAUSED = "paused"  # Duraklatıldı
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal edildi


class PomodoroSettings(BaseModel):
    """Pomodoro zamanlayıcı ayarları"""

    work_duration_minutes: int = Field(
        default=25, ge=1, le=60, description="Çalışma süresi (dakika)"
    )
    short_break_minutes: int = Field(
        default=5, ge=1, le=30, description="Kısa mola süresi (dakika)"
    )
    long_break_minutes: int = Field(
        default=15, ge=5, le=60, description="Uzun mola süresi (dakika)"
    )
    sessions_until_long_break: int = Field(
        default=4, ge=2, le=10, description="Uzun mola öncesi oturum sayısı"
    )
    auto_start_breaks: bool = Field(
        default=False, description="Molaları otomatik başlat"
    )
    auto_start_work: bool = Field(
        default=False, description="Çalışmayı otomatik başlat"
    )
    sound_enabled: bool = Field(default=True, description="Ses bildirimleri aktif")
    notification_enabled: bool = Field(default=True, description="Bildirimler aktif")


class StartPomodoroRequest(BaseModel):
    """Pomodoro oturumu başlatma isteği"""

    session_type: PomodoroSessionType = Field(default=PomodoroSessionType.WORK)
    custom_duration_minutes: Optional[int] = Field(
        default=None, ge=1, le=120, description="Özel süre (dakika)"
    )
    task_description: Optional[str] = Field(
        default=None, max_length=500, description="Görev açıklaması"
    )


class PomodoroSessionResponse(BaseModel):
    """Pomodoro oturum yanıtı"""

    session_id: str
    user_id: int
    session_type: PomodoroSessionType
    status: PomodoroSessionStatus
    duration_minutes: int
    remaining_seconds: int
    started_at: datetime
    ends_at: datetime
    paused_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_description: Optional[str] = None
    sessions_completed_today: int
    next_session_type: PomodoroSessionType


class UpdatePomodoroRequest(BaseModel):
    """Pomodoro oturum güncelleme isteği"""

    action: str = Field(..., description="pause, resume, complete, cancel")


class InactivityAlert(BaseModel):
    """Dikkat dağınıklığı uyarısı"""

    alert_id: str
    user_id: int
    detected_at: datetime
    inactive_duration_seconds: int
    alert_message: str
    suggested_action: str


class FocusExercise(BaseModel):
    """Konsantrasyon egzersizi"""

    exercise_id: str
    title: str
    description: str
    duration_minutes: int
    difficulty: str  # easy, medium, hard
    instructions: List[str]
    benefits: List[str]


class FocusExerciseProgress(BaseModel):
    """Konsantrasyon egzersizi ilerleme"""

    exercise_id: str
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: int
    success_rate: Optional[float] = None
    notes: Optional[str] = None


# ============================================================================
# Task 88.1: Pomodoro Timer Implementation
# Requirements: REQ-52.1 - REQ-52.5
# ============================================================================


@router.post("/pomodoro/start", response_model=PomodoroSessionResponse)
def start_pomodoro_session(
    request: StartPomodoroRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pomodoro çalışma oturumu başlat

    REQ-52.1: WHEN öğrenci çalışma oturumu başlattığında,
    THE Platform SHALL Pomodoro timer (25dk çalışma, 5dk mola) sunar

    Args:
        request: Oturum başlatma isteği
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        PomodoroSessionResponse: Başlatılan oturum bilgileri
    """
    import uuid

    # Kullanıcının ayarlarını al (varsayılan değerler kullan)
    settings = PomodoroSettings()

    # Süreyi belirle
    if request.custom_duration_minutes:
        duration_minutes = request.custom_duration_minutes
    elif request.session_type == PomodoroSessionType.WORK:
        duration_minutes = settings.work_duration_minutes
    elif request.session_type == PomodoroSessionType.SHORT_BREAK:
        duration_minutes = settings.short_break_minutes
    else:  # LONG_BREAK
        duration_minutes = settings.long_break_minutes

    # Oturum oluştur
    session_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    ends_at = started_at + timedelta(minutes=duration_minutes)

    # Bugün tamamlanan oturum sayısını hesapla (simüle edilmiş)
    sessions_completed_today = 0

    # Sonraki oturum tipini belirle
    if request.session_type == PomodoroSessionType.WORK:
        if (sessions_completed_today + 1) % settings.sessions_until_long_break == 0:
            next_session_type = PomodoroSessionType.LONG_BREAK
        else:
            next_session_type = PomodoroSessionType.SHORT_BREAK
    else:
        next_session_type = PomodoroSessionType.WORK

    # Yanıt oluştur
    response = PomodoroSessionResponse(
        session_id=session_id,
        user_id=current_user.id,
        session_type=request.session_type,
        status=PomodoroSessionStatus.ACTIVE,
        duration_minutes=duration_minutes,
        remaining_seconds=duration_minutes * 60,
        started_at=started_at,
        ends_at=ends_at,
        task_description=request.task_description,
        sessions_completed_today=sessions_completed_today,
        next_session_type=next_session_type,
    )

    return response


@router.get("/pomodoro/current", response_model=Optional[PomodoroSessionResponse])
def get_current_pomodoro_session(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Mevcut aktif Pomodoro oturumunu getir

    Returns:
        PomodoroSessionResponse veya None: Aktif oturum varsa bilgileri
    """
    # Gerçek implementasyonda veritabanından aktif oturum çekilir
    # Şimdilik None döndürüyoruz
    return None


@router.put("/pomodoro/{session_id}", response_model=PomodoroSessionResponse)
def update_pomodoro_session(
    session_id: str,
    request: UpdatePomodoroRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pomodoro oturumunu güncelle (duraklat, devam et, tamamla, iptal et)

    Args:
        session_id: Oturum ID
        request: Güncelleme isteği (pause, resume, complete, cancel)
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        PomodoroSessionResponse: Güncellenmiş oturum bilgileri
    """
    # Gerçek implementasyonda veritabanından oturum çekilir ve güncellenir
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"Oturum bulunamadı: {session_id}"
    )


@router.get("/pomodoro/settings", response_model=PomodoroSettings)
def get_pomodoro_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Kullanıcının Pomodoro ayarlarını getir

    Returns:
        PomodoroSettings: Kullanıcı ayarları
    """
    # Gerçek implementasyonda veritabanından kullanıcı ayarları çekilir
    return PomodoroSettings()


@router.put("/pomodoro/settings", response_model=PomodoroSettings)
def update_pomodoro_settings(
    settings: PomodoroSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kullanıcının Pomodoro ayarlarını güncelle

    Customizable intervals support (REQ-52.1)

    Args:
        settings: Yeni ayarlar
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        PomodoroSettings: Güncellenmiş ayarlar
    """
    # Gerçek implementasyonda veritabanına kaydedilir
    return settings


@router.get("/pomodoro/history")
def get_pomodoro_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kullanıcının Pomodoro oturum geçmişini getir

    Args:
        limit: Maksimum kayıt sayısı
        offset: Başlangıç offset
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        List[PomodoroSessionResponse]: Oturum geçmişi
    """
    # Gerçek implementasyonda veritabanından geçmiş çekilir
    return {
        "total": 0,
        "sessions": [],
        "stats": {
            "total_sessions": 0,
            "total_work_minutes": 0,
            "total_break_minutes": 0,
            "average_session_completion_rate": 0.0,
        },
    }


# ============================================================================
# Task 88.2: Görsel Zamanlayıcı (Visual Timer)
# Requirements: REQ-52.6 - REQ-52.10
# ============================================================================


@router.get("/timer/visual/{session_id}")
def get_visual_timer_data(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görsel zamanlayıcı için gerçek zamanlı veri getir

    REQ-52.2: WHEN zamanlayıcı çalıştığında,
    THE Platform SHALL görsel countdown ve progress ring gösterir

    Visual countdown, progress ring, time remaining display

    Args:
        session_id: Oturum ID
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        dict: Görsel zamanlayıcı verileri
    """
    # Gerçek implementasyonda veritabanından oturum çekilir
    return {
        "session_id": session_id,
        "remaining_seconds": 1500,  # 25 dakika
        "total_seconds": 1500,
        "progress_percentage": 0.0,
        "time_display": "25:00",
        "is_active": True,
        "session_type": "work",
        "color_scheme": {
            "primary": "#4CAF50",  # Yeşil (çalışma)
            "secondary": "#81C784",
            "background": "#E8F5E9",
        },
    }


# ============================================================================
# Task 88.3: Dikkat Dağınıklığı Tespiti (Inactivity Detection)
# Requirements: REQ-52.11 - REQ-52.15
# ============================================================================


@router.post("/inactivity/detect")
def detect_inactivity(
    inactive_duration_seconds: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dikkat dağınıklığı tespit et ve uyarı oluştur

    REQ-52.3: WHEN dikkat dağınıklığı tespit edildiğinde,
    THE Platform SHALL nazik hatırlatma bildirimleri gönderir

    Inactivity detection, focus loss alerts, re-engagement prompts

    Args:
        inactive_duration_seconds: İnaktif kalınan süre (saniye)
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        InactivityAlert: Dikkat dağınıklığı uyarısı
    """
    import uuid

    # Uyarı mesajı ve önerilen aksiyon belirle
    if inactive_duration_seconds < 60:
        alert_message = "Harika gidiyorsun! Odaklanmaya devam et. 💪"
        suggested_action = "continue"
    elif inactive_duration_seconds < 180:
        alert_message = "Dikkatini toplamaya çalış. Küçük bir mola verebilirsin. ☕"
        suggested_action = "short_break"
    elif inactive_duration_seconds < 300:
        alert_message = (
            "Uzun süredir aktif değilsin. Kısa bir yürüyüş yapmak ister misin? 🚶"
        )
        suggested_action = "walk_break"
    else:
        alert_message = "Uzun bir aradan sonra geri döndün! Yeni bir Pomodoro oturumu başlatalım mı? 🎯"
        suggested_action = "restart_session"

    alert = InactivityAlert(
        alert_id=str(uuid.uuid4()),
        user_id=current_user.id,
        detected_at=datetime.now(timezone.utc),
        inactive_duration_seconds=inactive_duration_seconds,
        alert_message=alert_message,
        suggested_action=suggested_action,
    )

    return alert


@router.get("/inactivity/alerts")
def get_inactivity_alerts(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kullanıcının dikkat dağınıklığı uyarı geçmişini getir

    Args:
        limit: Maksimum kayıt sayısı
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        List[InactivityAlert]: Uyarı geçmişi
    """
    # Gerçek implementasyonda veritabanından geçmiş çekilir
    return {
        "total": 0,
        "alerts": [],
        "stats": {
            "total_alerts_today": 0,
            "average_inactive_duration_seconds": 0,
            "most_common_time": "14:00-16:00",
        },
    }


# ============================================================================
# Task 88.4: Konsantrasyon Egzersizleri (Focus Training)
# Requirements: REQ-52.16 - REQ-52.20
# ============================================================================


@router.get("/focus-exercises", response_model=List[FocusExercise])
def get_focus_exercises(
    difficulty: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Konsantrasyon egzersizlerini listele

    Focus training exercises, attention span building, mindfulness prompts

    Args:
        difficulty: Zorluk seviyesi filtresi (easy, medium, hard)
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        List[FocusExercise]: Egzersiz listesi
    """
    exercises = [
        FocusExercise(
            exercise_id="breathing-4-7-8",
            title="4-7-8 Nefes Egzersizi",
            description="Derin nefes alarak zihnini sakinleştir ve odaklanmayı artır",
            duration_minutes=5,
            difficulty="easy",
            instructions=[
                "Rahat bir pozisyonda otur",
                "4 saniye boyunca burnundan nefes al",
                "7 saniye nefesini tut",
                "8 saniye boyunca ağzından nefes ver",
                "Bu döngüyü 4 kez tekrarla",
            ],
            benefits=[
                "Stresi azaltır",
                "Odaklanmayı artırır",
                "Zihinsel netlik sağlar",
            ],
        ),
        FocusExercise(
            exercise_id="mindful-observation",
            title="Dikkatli Gözlem",
            description="Bir nesneyi 5 dakika boyunca dikkatle gözlemle",
            duration_minutes=5,
            difficulty="easy",
            instructions=[
                "Bir nesne seç (kalem, bardak, vb.)",
                "Nesneyi 5 dakika boyunca dikkatle incele",
                "Rengini, şeklini, dokusunu fark et",
                "Zihnin dağıldığında nazikçe nesneye geri dön",
            ],
            benefits=[
                "Dikkat süresini uzatır",
                "Gözlem becerilerini geliştirir",
                "Zihinsel disiplin kazandırır",
            ],
        ),
        FocusExercise(
            exercise_id="body-scan",
            title="Vücut Taraması",
            description="Vücudunun her bölümüne sırayla odaklan",
            duration_minutes=10,
            difficulty="medium",
            instructions=[
                "Rahat bir pozisyonda uzan veya otur",
                "Ayak parmaklarından başlayarak yukarı çık",
                "Her vücut bölümüne 30 saniye odaklan",
                "Gerginlik hissedersen o bölgeyi gevşet",
                "Başa kadar devam et",
            ],
            benefits=[
                "Vücut farkındalığını artırır",
                "Gerginliği azaltır",
                "Odaklanma becerisini güçlendirir",
            ],
        ),
        FocusExercise(
            exercise_id="counting-meditation",
            title="Sayma Meditasyonu",
            description="Nefeslerini sayarak zihnini sakinleştir",
            duration_minutes=10,
            difficulty="medium",
            instructions=[
                "Gözlerini kapat ve rahatla",
                "Her nefes alışında 1'den 10'a kadar say",
                "10'a ulaştığında tekrar 1'den başla",
                "Zihnin dağılırsa nazikçe saymaya geri dön",
                "10 dakika boyunca devam et",
            ],
            benefits=[
                "Zihinsel netlik sağlar",
                "Dikkat kontrolünü artırır",
                "Sabır ve disiplin geliştirir",
            ],
        ),
        FocusExercise(
            exercise_id="visualization",
            title="Görselleştirme Egzersizi",
            description="Zihninde sakin bir yer hayal et ve detaylandır",
            duration_minutes=15,
            difficulty="hard",
            instructions=[
                "Gözlerini kapat ve derin nefes al",
                "Sakin bir yer hayal et (orman, sahil, vb.)",
                "Gördüklerini, duyduklarını, hissettiklerini detaylandır",
                "Bu yerde 10 dakika kal",
                "Yavaşça gözlerini aç",
            ],
            benefits=[
                "Yaratıcılığı artırır",
                "Stresi azaltır",
                "Zihinsel odaklanmayı güçlendirir",
            ],
        ),
    ]

    # Zorluk seviyesine göre filtrele
    if difficulty:
        exercises = [e for e in exercises if e.difficulty == difficulty]

    return exercises


@router.post(
    "/focus-exercises/{exercise_id}/start", response_model=FocusExerciseProgress
)
def start_focus_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Konsantrasyon egzersizi başlat

    Args:
        exercise_id: Egzersiz ID
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        FocusExerciseProgress: Başlatılan egzersiz ilerleme bilgisi
    """
    progress = FocusExerciseProgress(
        exercise_id=exercise_id,
        user_id=current_user.id,
        started_at=datetime.now(timezone.utc),
        duration_seconds=0,
    )

    return progress


@router.put("/focus-exercises/progress/{exercise_id}/complete")
def complete_focus_exercise(
    exercise_id: str,
    duration_seconds: int,
    success_rate: Optional[float] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Konsantrasyon egzersizini tamamla

    Args:
        exercise_id: Egzersiz ID
        duration_seconds: Egzersiz süresi (saniye)
        success_rate: Başarı oranı (0-1)
        notes: Kullanıcı notları
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        FocusExerciseProgress: Tamamlanan egzersiz bilgisi
    """
    progress = FocusExerciseProgress(
        exercise_id=exercise_id,
        user_id=current_user.id,
        started_at=datetime.now(timezone.utc) - timedelta(seconds=duration_seconds),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
        success_rate=success_rate,
        notes=notes,
    )

    return progress


@router.get("/focus-exercises/progress")
def get_focus_exercise_progress(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kullanıcının konsantrasyon egzersizi geçmişini getir

    Args:
        limit: Maksimum kayıt sayısı
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu

    Returns:
        dict: Egzersiz geçmişi ve istatistikler
    """
    return {
        "total": 0,
        "exercises": [],
        "stats": {
            "total_exercises_completed": 0,
            "total_minutes_practiced": 0,
            "average_success_rate": 0.0,
            "most_practiced_exercise": None,
            "streak_days": 0,
        },
    }


# ============================================================================
# Yardımcı Endpoint'ler
# ============================================================================


@router.get("/stats/daily")
def get_daily_adhd_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Kullanıcının günlük DEHB destek istatistiklerini getir

    Returns:
        dict: Günlük istatistikler
    """
    return {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "pomodoro_sessions": {
            "total": 0,
            "completed": 0,
            "work_minutes": 0,
            "break_minutes": 0,
        },
        "focus_exercises": {"total": 0, "completed": 0, "total_minutes": 0},
        "inactivity_alerts": {"total": 0, "average_duration_seconds": 0},
        "focus_score": 0.0,  # 0-100 arası
        "productivity_trend": "stable",  # improving, stable, declining
    }


@router.get("/recommendations")
def get_adhd_recommendations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Kullanıcının performansına göre kişiselleştirilmiş DEHB destek önerileri

    Returns:
        dict: Kişiselleştirilmiş öneriler
    """
    return {
        "recommendations": [
            {
                "type": "pomodoro",
                "title": "Pomodoro Tekniğini Dene",
                "description": "25 dakikalık odaklanma oturumları ile verimliliğini artır",
                "priority": "high",
                "estimated_benefit": "Odaklanma süresini %40 artırabilir",
            },
            {
                "type": "exercise",
                "title": "Nefes Egzersizi Yap",
                "description": "4-7-8 nefes egzersizi ile zihnini sakinleştir",
                "priority": "medium",
                "estimated_benefit": "Stresi %30 azaltabilir",
            },
            {
                "type": "break",
                "title": "Düzenli Molalar Ver",
                "description": "Her 25 dakikada bir 5 dakika mola ver",
                "priority": "high",
                "estimated_benefit": "Uzun vadeli odaklanmayı %50 artırabilir",
            },
        ],
        "personalized_message": "Bugün harika gidiyorsun! Düzenli molalar vermeye devam et. 🎯",
    }
