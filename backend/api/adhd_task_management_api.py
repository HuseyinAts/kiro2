"""
ADHD (DEHB) Desteği API - Görev Yönetimi Sistemi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül DEHB tanılı öğrenciler için görev yönetimi araçları sağlar:
- Öncelik sıralaması (Priority ranking)
- Renk kodlama (Color coding)
- Eisenhower Matrix (Urgent/Important)
- Otomatik önceliklendirme

Requirements: REQ-52.41 - REQ-52.60
Task: 90.3, 90.4
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

from core.database import get_db
from core.dependencies import get_current_user
from models.database import User

router = APIRouter(prefix="/api/adhd-support/tasks", tags=["ADHD Task Management"])


# ============================================================================
# Enums
# ============================================================================


class TaskPriority(str, Enum):
    """Görev öncelik seviyeleri"""

    CRITICAL = "critical"  # Kritik (En yüksek öncelik)
    HIGH = "high"  # Yüksek
    MEDIUM = "medium"  # Orta
    LOW = "low"  # Düşük
    NONE = "none"  # Önceliksiz


class TaskStatus(str, Enum):
    """Görev durumları"""

    TODO = "todo"  # Yapılacak
    IN_PROGRESS = "in_progress"  # Devam ediyor
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal edildi
    ON_HOLD = "on_hold"  # Beklemede


class TaskCategory(str, Enum):
    """Görev kategorileri"""

    STUDY = "study"  # Ders çalışma
    EXAM = "exam"  # Sınav
    HOMEWORK = "homework"  # Ödev
    REVIEW = "review"  # Tekrar
    PRACTICE = "practice"  # Pratik
    OTHER = "other"  # Diğer


class EisenhowerQuadrant(str, Enum):
    """Eisenhower Matrix kadranları"""

    Q1_URGENT_IMPORTANT = "q1_urgent_important"  # Acil ve Önemli (Kırmızı)
    Q2_NOT_URGENT_IMPORTANT = "q2_not_urgent_important"  # Önemli ama Acil Değil (Yeşil)
    Q3_URGENT_NOT_IMPORTANT = "q3_urgent_not_important"  # Acil ama Önemli Değil (Sarı)
    Q4_NOT_URGENT_NOT_IMPORTANT = (
        "q4_not_urgent_not_important"  # Ne Acil Ne Önemli (Gri)
    )


# ============================================================================
# Color Schemes
# ============================================================================

PRIORITY_COLORS = {
    TaskPriority.CRITICAL: "#DC2626",  # Kırmızı (Red-600)
    TaskPriority.HIGH: "#EA580C",  # Turuncu (Orange-600)
    TaskPriority.MEDIUM: "#CA8A04",  # Sarı (Yellow-600)
    TaskPriority.LOW: "#16A34A",  # Yeşil (Green-600)
    TaskPriority.NONE: "#6B7280",  # Gri (Gray-500)
}

STATUS_COLORS = {
    TaskStatus.TODO: "#3B82F6",  # Mavi (Blue-500)
    TaskStatus.IN_PROGRESS: "#8B5CF6",  # Mor (Purple-500)
    TaskStatus.COMPLETED: "#10B981",  # Yeşil (Green-500)
    TaskStatus.CANCELLED: "#EF4444",  # Kırmızı (Red-500)
    TaskStatus.ON_HOLD: "#F59E0B",  # Amber (Amber-500)
}

CATEGORY_COLORS = {
    TaskCategory.STUDY: "#3B82F6",  # Mavi
    TaskCategory.EXAM: "#DC2626",  # Kırmızı
    TaskCategory.HOMEWORK: "#8B5CF6",  # Mor
    TaskCategory.REVIEW: "#10B981",  # Yeşil
    TaskCategory.PRACTICE: "#F59E0B",  # Amber
    TaskCategory.OTHER: "#6B7280",  # Gri
}

QUADRANT_COLORS = {
    EisenhowerQuadrant.Q1_URGENT_IMPORTANT: "#DC2626",  # Kırmızı
    EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT: "#10B981",  # Yeşil
    EisenhowerQuadrant.Q3_URGENT_NOT_IMPORTANT: "#F59E0B",  # Sarı
    EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT: "#9CA3AF",  # Gri
}


# ============================================================================
# Pydantic Models
# ============================================================================


class CreateTaskRequest(BaseModel):
    """Görev oluşturma isteği"""

    title: str = Field(..., min_length=1, max_length=200, description="Görev başlığı")
    description: Optional[str] = Field(
        None, max_length=1000, description="Görev açıklaması"
    )
    category: TaskCategory = Field(
        default=TaskCategory.OTHER, description="Görev kategorisi"
    )
    due_date: Optional[datetime] = Field(None, description="Bitiş tarihi")
    estimated_duration_minutes: Optional[int] = Field(
        None, ge=1, le=480, description="Tahmini süre (dakika)"
    )
    is_urgent: bool = Field(default=False, description="Acil mi?")
    is_important: bool = Field(default=False, description="Önemli mi?")
    parent_task_id: Optional[str] = Field(
        None, description="Ana görev ID (alt görev için)"
    )


class UpdateTaskRequest(BaseModel):
    """Görev güncelleme isteği"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[TaskCategory] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=480)
    is_urgent: Optional[bool] = None
    is_important: Optional[bool] = None
    completed_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Görev yanıtı"""

    task_id: str
    user_id: int
    title: str
    description: Optional[str]
    category: TaskCategory
    status: TaskStatus
    priority: TaskPriority
    eisenhower_quadrant: EisenhowerQuadrant
    due_date: Optional[datetime]
    estimated_duration_minutes: Optional[int]
    is_urgent: bool
    is_important: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    parent_task_id: Optional[str]
    subtasks_count: int
    # Renk bilgileri
    priority_color: str
    status_color: str
    category_color: str
    quadrant_color: str


class TaskListResponse(BaseModel):
    """Görev listesi yanıtı"""

    tasks: List[TaskResponse]
    total_count: int
    by_priority: dict
    by_status: dict
    by_category: dict
    by_quadrant: dict


class PriorityRecommendation(BaseModel):
    """Öncelik önerisi"""

    task_id: str
    current_priority: TaskPriority
    recommended_priority: TaskPriority
    reason: str
    confidence_score: float  # 0.0 - 1.0


class ColorSchemeResponse(BaseModel):
    """Renk şeması yanıtı"""

    priority_colors: dict
    status_colors: dict
    category_colors: dict
    quadrant_colors: dict


# ============================================================================
# In-Memory Storage (Gerçek uygulamada database kullanılmalı)
# ============================================================================

tasks_db = {}  # task_id -> task_data


# ============================================================================
# Helper Functions
# ============================================================================


def calculate_eisenhower_quadrant(
    is_urgent: bool, is_important: bool
) -> EisenhowerQuadrant:
    """
    Eisenhower Matrix kadranını hesapla

    REQ-52.52: Urgent/important matrix
    """
    if is_urgent and is_important:
        return EisenhowerQuadrant.Q1_URGENT_IMPORTANT
    elif not is_urgent and is_important:
        return EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT
    elif is_urgent and not is_important:
        return EisenhowerQuadrant.Q3_URGENT_NOT_IMPORTANT
    else:
        return EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT


def calculate_automatic_priority(
    is_urgent: bool,
    is_important: bool,
    due_date: Optional[datetime],
    category: TaskCategory,
) -> TaskPriority:
    """
    Otomatik öncelik hesapla

    REQ-52.53: Automatic prioritization

    Algoritma:
    1. Eisenhower Matrix'e göre temel öncelik
    2. Bitiş tarihine göre ayarlama
    3. Kategoriye göre ince ayar
    """
    # Eisenhower Matrix'e göre temel öncelik
    quadrant = calculate_eisenhower_quadrant(is_urgent, is_important)

    if quadrant == EisenhowerQuadrant.Q1_URGENT_IMPORTANT:
        base_priority = TaskPriority.CRITICAL
    elif quadrant == EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT:
        base_priority = TaskPriority.HIGH
    elif quadrant == EisenhowerQuadrant.Q3_URGENT_NOT_IMPORTANT:
        base_priority = TaskPriority.MEDIUM
    else:
        base_priority = TaskPriority.LOW

    # Bitiş tarihine göre ayarlama
    if due_date:
        days_until_due = (due_date - datetime.now()).days

        if days_until_due <= 1:  # 1 gün veya daha az
            if base_priority == TaskPriority.HIGH:
                base_priority = TaskPriority.CRITICAL
            elif base_priority == TaskPriority.MEDIUM:
                base_priority = TaskPriority.HIGH
        elif days_until_due <= 3:  # 3 gün veya daha az
            if base_priority == TaskPriority.MEDIUM:
                base_priority = TaskPriority.HIGH

    # Kategoriye göre ince ayar
    if category == TaskCategory.EXAM:
        # Sınav görevleri her zaman yüksek öncelikli
        if base_priority == TaskPriority.LOW:
            base_priority = TaskPriority.MEDIUM
        elif base_priority == TaskPriority.MEDIUM:
            base_priority = TaskPriority.HIGH

    return base_priority


def get_task_colors(task_data: dict) -> dict:
    """
    Görev için renk bilgilerini al

    REQ-52.56: Priority-based colors
    REQ-52.57: Status colors
    REQ-52.58: Category colors
    """
    return {
        "priority_color": PRIORITY_COLORS[task_data["priority"]],
        "status_color": STATUS_COLORS[task_data["status"]],
        "category_color": CATEGORY_COLORS[task_data["category"]],
        "quadrant_color": QUADRANT_COLORS[task_data["eisenhower_quadrant"]],
    }


def count_subtasks(task_id: str) -> int:
    """Alt görev sayısını hesapla"""
    return sum(1 for task in tasks_db.values() if task.get("parent_task_id") == task_id)


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/create", response_model=TaskResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Yeni görev oluştur

    REQ-52.41: Task decomposition algorithm
    REQ-52.51: Priority levels
    REQ-52.53: Automatic prioritization
    """
    task_id = str(uuid.uuid4())

    # Eisenhower kadranını hesapla
    quadrant = calculate_eisenhower_quadrant(request.is_urgent, request.is_important)

    # Otomatik öncelik hesapla
    priority = calculate_automatic_priority(
        request.is_urgent, request.is_important, request.due_date, request.category
    )

    task_data = {
        "task_id": task_id,
        "user_id": current_user.id,
        "title": request.title,
        "description": request.description,
        "category": request.category,
        "status": TaskStatus.TODO,
        "priority": priority,
        "eisenhower_quadrant": quadrant,
        "due_date": request.due_date,
        "estimated_duration_minutes": request.estimated_duration_minutes,
        "is_urgent": request.is_urgent,
        "is_important": request.is_important,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "completed_at": None,
        "parent_task_id": request.parent_task_id,
    }

    tasks_db[task_id] = task_data

    # Renk bilgilerini ekle
    colors = get_task_colors(task_data)

    return TaskResponse(**task_data, subtasks_count=0, **colors)


@router.get("/list", response_model=TaskListResponse)
async def list_tasks(
    status_filter: Optional[TaskStatus] = None,
    priority_filter: Optional[TaskPriority] = None,
    category_filter: Optional[TaskCategory] = None,
    quadrant_filter: Optional[EisenhowerQuadrant] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görevleri listele (filtreleme ve sıralama ile)

    REQ-52.51: Priority levels
    REQ-52.54: Urgent/important matrix
    """
    # Kullanıcının görevlerini filtrele
    user_tasks = [
        task for task in tasks_db.values() if task["user_id"] == current_user.id
    ]

    # Filtreleme
    if status_filter:
        user_tasks = [t for t in user_tasks if t["status"] == status_filter]
    if priority_filter:
        user_tasks = [t for t in user_tasks if t["priority"] == priority_filter]
    if category_filter:
        user_tasks = [t for t in user_tasks if t["category"] == category_filter]
    if quadrant_filter:
        user_tasks = [
            t for t in user_tasks if t["eisenhower_quadrant"] == quadrant_filter
        ]

    # Öncelik sıralaması (CRITICAL -> HIGH -> MEDIUM -> LOW -> NONE)
    priority_order = {
        TaskPriority.CRITICAL: 0,
        TaskPriority.HIGH: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.LOW: 3,
        TaskPriority.NONE: 4,
    }
    user_tasks.sort(key=lambda t: (priority_order[t["priority"]], t["created_at"]))

    # İstatistikler
    by_priority = {}
    by_status = {}
    by_category = {}
    by_quadrant = {}

    for task in user_tasks:
        by_priority[task["priority"]] = by_priority.get(task["priority"], 0) + 1
        by_status[task["status"]] = by_status.get(task["status"], 0) + 1
        by_category[task["category"]] = by_category.get(task["category"], 0) + 1
        by_quadrant[task["eisenhower_quadrant"]] = (
            by_quadrant.get(task["eisenhower_quadrant"], 0) + 1
        )

    # TaskResponse nesnelerine dönüştür
    task_responses = []
    for task in user_tasks:
        colors = get_task_colors(task)
        task_responses.append(
            TaskResponse(
                **task, subtasks_count=count_subtasks(task["task_id"]), **colors
            )
        )

    return TaskListResponse(
        tasks=task_responses,
        total_count=len(task_responses),
        by_priority=by_priority,
        by_status=by_status,
        by_category=by_category,
        by_quadrant=by_quadrant,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görev detayını getir

    REQ-52.42: Subtask generation
    """
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Görev bulunamadı"
        )

    task_data = tasks_db[task_id]

    if task_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu göreve erişim yetkiniz yok",
        )

    colors = get_task_colors(task_data)

    return TaskResponse(**task_data, subtasks_count=count_subtasks(task_id), **colors)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görevi güncelle

    REQ-52.55: Automatic prioritization
    """
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Görev bulunamadı"
        )

    task_data = tasks_db[task_id]

    if task_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu görevi güncelleme yetkiniz yok",
        )

    # Güncelleme
    update_data = request.dict(exclude_unset=True)

    for key, value in update_data.items():
        if value is not None:
            task_data[key] = value

    # Eisenhower kadranını yeniden hesapla
    if "is_urgent" in update_data or "is_important" in update_data:
        task_data["eisenhower_quadrant"] = calculate_eisenhower_quadrant(
            task_data["is_urgent"], task_data["is_important"]
        )

    # Önceliği yeniden hesapla (manuel öncelik verilmediyse)
    if "priority" not in update_data:
        task_data["priority"] = calculate_automatic_priority(
            task_data["is_urgent"],
            task_data["is_important"],
            task_data["due_date"],
            task_data["category"],
        )

    task_data["updated_at"] = datetime.now()

    colors = get_task_colors(task_data)

    return TaskResponse(**task_data, subtasks_count=count_subtasks(task_id), **colors)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görevi sil

    REQ-52.43: Manageable chunks
    """
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Görev bulunamadı"
        )

    task_data = tasks_db[task_id]

    if task_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Bu görevi silme yetkiniz yok"
        )

    # Alt görevleri de sil
    subtask_ids = [
        tid for tid, t in tasks_db.items() if t.get("parent_task_id") == task_id
    ]
    for subtask_id in subtask_ids:
        del tasks_db[subtask_id]

    del tasks_db[task_id]


@router.get("/{task_id}/subtasks", response_model=List[TaskResponse])
async def get_subtasks(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görevin alt görevlerini getir

    REQ-52.42: Subtask generation
    REQ-52.44: Manageable chunks
    """
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Görev bulunamadı"
        )

    parent_task = tasks_db[task_id]

    if parent_task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu göreve erişim yetkiniz yok",
        )

    # Alt görevleri bul
    subtasks = [
        task for task in tasks_db.values() if task.get("parent_task_id") == task_id
    ]

    # Öncelik sıralaması
    priority_order = {
        TaskPriority.CRITICAL: 0,
        TaskPriority.HIGH: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.LOW: 3,
        TaskPriority.NONE: 4,
    }
    subtasks.sort(key=lambda t: (priority_order[t["priority"]], t["created_at"]))

    # TaskResponse nesnelerine dönüştür
    subtask_responses = []
    for task in subtasks:
        colors = get_task_colors(task)
        subtask_responses.append(
            TaskResponse(
                **task, subtasks_count=count_subtasks(task["task_id"]), **colors
            )
        )

    return subtask_responses


@router.post("/{task_id}/recommend-priority", response_model=PriorityRecommendation)
async def recommend_priority(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görev için öncelik önerisi al

    REQ-52.53: Automatic prioritization
    REQ-52.55: Automatic prioritization
    """
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Görev bulunamadı"
        )

    task_data = tasks_db[task_id]

    if task_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu göreve erişim yetkiniz yok",
        )

    # Otomatik öncelik hesapla
    recommended_priority = calculate_automatic_priority(
        task_data["is_urgent"],
        task_data["is_important"],
        task_data["due_date"],
        task_data["category"],
    )

    # Öneri nedeni oluştur
    quadrant = task_data["eisenhower_quadrant"]
    reason_parts = []

    if quadrant == EisenhowerQuadrant.Q1_URGENT_IMPORTANT:
        reason_parts.append("Görev hem acil hem önemli")
    elif quadrant == EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT:
        reason_parts.append("Görev önemli ancak acil değil")
    elif quadrant == EisenhowerQuadrant.Q3_URGENT_NOT_IMPORTANT:
        reason_parts.append("Görev acil ancak önemli değil")
    else:
        reason_parts.append("Görev ne acil ne önemli")

    if task_data["due_date"]:
        days_until_due = (task_data["due_date"] - datetime.now()).days
        if days_until_due <= 1:
            reason_parts.append("Bitiş tarihi çok yakın (1 gün veya daha az)")
        elif days_until_due <= 3:
            reason_parts.append("Bitiş tarihi yaklaşıyor (3 gün veya daha az)")

    if task_data["category"] == TaskCategory.EXAM:
        reason_parts.append("Sınav kategorisi yüksek öncelikli")

    reason = ". ".join(reason_parts) + "."

    # Güven skoru hesapla
    confidence = 0.8  # Temel güven
    if task_data["due_date"]:
        confidence += 0.1  # Bitiş tarihi varsa güven artar
    if task_data["is_urgent"] or task_data["is_important"]:
        confidence += 0.1  # Acil veya önemli ise güven artar
    confidence = min(confidence, 1.0)

    return PriorityRecommendation(
        task_id=task_id,
        current_priority=task_data["priority"],
        recommended_priority=recommended_priority,
        reason=reason,
        confidence_score=confidence,
    )


@router.get("/colors/scheme", response_model=ColorSchemeResponse)
async def get_color_scheme():
    """
    Renk şemasını getir

    REQ-52.56: Priority-based colors
    REQ-52.57: Status colors
    REQ-52.58: Category colors
    REQ-52.59: Quadrant colors
    """
    return ColorSchemeResponse(
        priority_colors=PRIORITY_COLORS,
        status_colors=STATUS_COLORS,
        category_colors=CATEGORY_COLORS,
        quadrant_colors=QUADRANT_COLORS,
    )


@router.get("/stats/summary")
async def get_task_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Görev istatistiklerini getir

    REQ-52.45: Progress tracking
    REQ-52.60: Visual feedback
    """
    user_tasks = [
        task for task in tasks_db.values() if task["user_id"] == current_user.id
    ]

    total_tasks = len(user_tasks)
    completed_tasks = sum(1 for t in user_tasks if t["status"] == TaskStatus.COMPLETED)
    in_progress_tasks = sum(
        1 for t in user_tasks if t["status"] == TaskStatus.IN_PROGRESS
    )

    # Öncelik dağılımı
    by_priority = {}
    for priority in TaskPriority:
        count = sum(1 for t in user_tasks if t["priority"] == priority)
        by_priority[priority.value] = {
            "count": count,
            "color": PRIORITY_COLORS[priority],
        }

    # Eisenhower Matrix dağılımı
    by_quadrant = {}
    for quadrant in EisenhowerQuadrant:
        count = sum(1 for t in user_tasks if t["eisenhower_quadrant"] == quadrant)
        by_quadrant[quadrant.value] = {
            "count": count,
            "color": QUADRANT_COLORS[quadrant],
        }

    # Tamamlanma oranı
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completion_rate": round(completion_rate, 2),
        "by_priority": by_priority,
        "by_quadrant": by_quadrant,
    }


@router.get("/health")
async def health_check():
    """
    Sağlık kontrolü

    REQ-52.60: System reliability
    """
    return {
        "status": "healthy",
        "service": "ADHD Task Management API",
        "tasks_count": len(tasks_db),
        "timestamp": datetime.now().isoformat(),
    }
