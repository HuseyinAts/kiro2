"""
Curator API — Faz 3.1 Curator UI Backend

Manuel curator review için admin-only endpoint'ler.
`bronze_clean` (84,905) + `pending` (2,775) + `legacy_v3_unaudited` (20,231)
quality_review_status değerlerine sahip soruları sıraya sokar ve
curator verdict'ini kaydeder.

Verdict mapping (Convention v2):
  - verify  → auto_judged_high  (Gold tier)
  - reject  → rejected
  - archive → archived

`pipeline_metadata.curator_verdict` JSON field'ına audit trail yazılır.
`audit_logs` tablosuna her verdict için satır eklenir.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import AuthenticatedUser, get_current_admin_user, get_db
from models.question_bank import QuestionBankItem
from models.student_question_flag import StudentQuestionFlag

logger = logging.getLogger(__name__)

PATTERN_UUID_OR_TEST = r"^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[a-zA-Z0-9_-]{1,36})$"

router = APIRouter(prefix="/api/v1/curator", tags=["Curator"])


# ============================================================================
# Convention — izinli giriş ve çıkış değerleri
# ============================================================================
ALLOWED_QUEUE_STATUSES: frozenset[str] = frozenset(
    {"bronze_clean", "pending", "legacy_v3_unaudited", "unverified"}
)

VERDICT_TO_STATUS: dict[str, str] = {
    "verify": "auto_judged_high",
    "reject": "rejected",
    "archive": "archived",
}


# ============================================================================
# Pydantic Models
# ============================================================================
class StudentFlagInfo(BaseModel):
    """Tek bir soru için öğrenci hata bildirimi özeti (flag_type bazlı)."""

    flag_type: str
    count: int
    notes: list[str] = Field(default_factory=list)


class QueueItem(BaseModel):
    """Curator kuyruğundaki tek bir soru."""

    id: str
    question_text: str
    options: dict[str, str | None] = Field(
        ..., description="A-E seçenekleri (E opsiyonel)"
    )
    correct_answer: str
    subject_area: str
    difficulty_level: str
    quality_review_status: str
    image_url: str | None = Field(
        None, description="question_image_url kolonu (DB'de image_url yok)"
    )
    misconception_tags: list[str] | None = None
    solution_steps: list[str] | None = None
    similar_question_ids: list[str] | None = None
    dispute_suggestion: dict[str, Any] | None = Field(
        None,
        description=(
            "Kör-çözüm cevap-hatası önerisi: {suggested, db, reason, conf}. "
            "İki bağımsız kör solver DB'ye karşı hemfikir; curator hızlı onay için."
        ),
    )
    student_flags: list[StudentFlagInfo] | None = Field(
        None,
        description="Öğrenci hata bildirimleri (flag_type bazlı sayı + notlar)",
    )
    flag_count: int | None = Field(
        None, description="Bu soruya ait toplam çözülmemiş öğrenci flag sayısı"
    )

    model_config = ConfigDict(from_attributes=False)


class QueueResponse(BaseModel):
    """Sayfalı kuyruk yanıtı."""

    items: list[QueueItem]
    total: int
    page: int
    per_page: int


class VerdictRequest(BaseModel):
    """Curator verdict payload'ı."""

    question_id: str = Field(..., min_length=1, pattern=PATTERN_UUID_OR_TEST)
    verdict: Literal["verify", "reject", "archive"]
    notes: str | None = Field(None, max_length=2000)
    reviewer_velocity_seconds: int | None = Field(None, ge=0, le=3600)
    error_type: str | None = Field(
        None,
        max_length=64,
        description="Reject/archive verdict'leri için hata sınıflandırma",
    )


class VerdictResponse(BaseModel):
    """Verdict işlendi yanıtı."""

    question_id: str
    previous_status: str | None
    new_status: str
    reviewed_by: str
    reviewed_at: datetime


class StatsResponse(BaseModel):
    """Curator istatistikleri."""

    pending_count: int = Field(..., description="bronze_clean status sayısı")
    bronze_clean_count: int
    legacy_v3_unaudited_count: int
    pending_status_count: int
    verified_count: int = Field(..., description="Lifetime curator_verdict=verify")
    rejected_today: int = Field(..., description="Bugün rejected (UTC)")
    flagged_count: int = Field(
        0,
        description="Öğrenci tarafından flag'lenmiş (çözülmemiş, aktif) distinct soru",
    )
    avg_velocity_sec: float | None = Field(
        None, description="Ortalama curator review velocity (saniye)"
    )


# ============================================================================
# Helper'lar
# ============================================================================
def _json_to_list(value: Any) -> list[str] | None:
    """JSON kolon değerini (dict | list | str | None) list[str]'e dönüştür.

    JSON kolonlar SQLAlchemy tarafından dict/list olarak dönebilir ya da
    raw string olarak (asyncpg edge case'i) gelebilir.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, dict):
        # dict ise key veya value listesi olarak normalize et (key'ler tag)
        return [str(k) for k in value]
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            return _json_to_list(decoded)
        except (json.JSONDecodeError, ValueError):
            return [value]
    return None


def _row_to_queue_item(row: QuestionBankItem) -> QueueItem:
    """ORM row'unu QueueItem Pydantic modeline çevir."""
    difficulty = row.difficulty_level
    # Enum ise .value, str ise olduğu gibi
    difficulty_str = (
        difficulty.value if hasattr(difficulty, "value") else str(difficulty)
    )

    # pipeline_metadata.dispute_suggestion: kör-çözüm cevap-hatası önerisi
    # (str veya dict olabilir; raw SQL row'da JSON string gelebilir).
    _pm = getattr(row, "pipeline_metadata", None) or {}
    if isinstance(_pm, str):
        try:
            _pm = json.loads(_pm)
        except (ValueError, TypeError):
            _pm = {}
    dispute_suggestion = (
        _pm.get("dispute_suggestion") if isinstance(_pm, dict) else None
    )

    return QueueItem(
        id=str(row.id),
        question_text=row.question_text,
        options={
            "A": row.option_a,
            "B": row.option_b,
            "C": row.option_c,
            "D": row.option_d,
            "E": row.option_e,
        },
        correct_answer=row.correct_answer,
        subject_area=row.subject_area,
        difficulty_level=difficulty_str,
        quality_review_status=row.quality_review_status,
        image_url=row.question_image_url,
        # Bu üç kolon DB'de var ama ORM model'inde tanımlı değil.
        # Hem ORM hem raw SQL row için getattr ile defansif erişim.
        misconception_tags=_json_to_list(getattr(row, "misconception_tags", None)),
        solution_steps=_json_to_list(getattr(row, "solution_steps", None)),
        similar_question_ids=_json_to_list(getattr(row, "similar_question_ids", None)),
        dispute_suggestion=dispute_suggestion,
    )


async def _write_audit_log(
    db: AsyncSession,
    *,
    admin_id: str,
    question_id: str,
    verdict: str,
    previous_status: str | None,
    new_status: str,
    notes: str | None,
    velocity: int | None,
    error_type: str | None,
    request: Request | None,
) -> None:
    """audit_logs tablosuna raw SQL ile satır ekle.

    İki AuditLog ORM modeli aynı tabloyu hedefliyor (extend_existing trap);
    bu yüzden ORM yerine raw SQL kullanıyoruz. Şema:
      id, user_id, action, resource_type, resource_id,
      old_values (json), new_values (json), ip_address, user_agent, created_at
    """
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    audit_id = str(uuid.uuid4())
    new_values = {
        "verdict": verdict,
        "notes": notes,
        "velocity_seconds": velocity,
        "error_type": error_type,
        "new_status": new_status,
    }
    old_values = {"previous_status": previous_status}

    try:
        await db.execute(
            text(
                """
                INSERT INTO audit_logs (
                    id, user_id, action, resource_type, resource_id,
                    old_values, new_values, ip_address, user_agent, created_at
                )
                VALUES (
                    :id, :user_id, :action, :resource_type, :resource_id,
                    CAST(:old_values AS json), CAST(:new_values AS json),
                    :ip_address, :user_agent, NOW()
                )
                """
            ),
            {
                "id": audit_id,
                "user_id": str(admin_id),
                "action": f"curator.verdict.{verdict}",
                "resource_type": "question_bank",
                "resource_id": question_id,
                "old_values": json.dumps(old_values),
                "new_values": json.dumps(new_values),
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
    except Exception as e:
        # Audit log hatası ana işlemi bozmamalı, sadece logla
        logger.warning(
            "Audit log write failed for question %s verdict %s: %s",
            question_id,
            verdict,
            e,
        )


# ============================================================================
# Endpoints
# ============================================================================
@router.get("/queue", response_model=QueueResponse)
async def get_queue(
    status_filter: str = Query(
        "bronze_clean",
        alias="status",
        description="quality_review_status filter (bronze_clean/pending/legacy_v3_unaudited/unverified)",
    ),
    subject: str | None = Query(None, description="subject_area (UPPERCASE)"),
    difficulty: str | None = Query(
        None, description="difficulty_level enum value (EASY/MEDIUM/HARD vb.)"
    ),
    has_diagram: bool | None = Query(
        None, description="True → image_url IS NOT NULL; False → image_url IS NULL"
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=200),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> QueueResponse:
    """Curator review kuyruğunu sayfalı şekilde döndür.

    Sıralama: md5(id) — random ama deterministic, kuyruğun curator'lar
    arasında dağıtılmasını sağlar.
    """
    if status_filter not in ALLOWED_QUEUE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status '{status_filter}'. "
                f"Allowed: {sorted(ALLOWED_QUEUE_STATUSES)}"
            ),
        )

    # Filtreler
    base_query = select(QuestionBankItem).where(
        QuestionBankItem.quality_review_status == status_filter,
        QuestionBankItem.is_active.is_(True),
    )
    count_query = select(func.count(QuestionBankItem.id)).where(
        QuestionBankItem.quality_review_status == status_filter,
        QuestionBankItem.is_active.is_(True),
    )

    if subject:
        # Subject identifier'a normalize_tr UYGULAMA — ASCII upper yeterli
        subject_db_val = subject.strip().upper()
        base_query = base_query.where(QuestionBankItem.subject_area == subject_db_val)
        count_query = count_query.where(QuestionBankItem.subject_area == subject_db_val)

    if difficulty:
        difficulty_val = difficulty.strip().upper()
        base_query = base_query.where(
            QuestionBankItem.difficulty_level == difficulty_val
        )
        count_query = count_query.where(
            QuestionBankItem.difficulty_level == difficulty_val
        )

    if has_diagram is not None:
        if has_diagram:
            base_query = base_query.where(
                QuestionBankItem.question_image_url.is_not(None)
            )
            count_query = count_query.where(
                QuestionBankItem.question_image_url.is_not(None)
            )
        else:
            base_query = base_query.where(QuestionBankItem.question_image_url.is_(None))
            count_query = count_query.where(
                QuestionBankItem.question_image_url.is_(None)
            )

    # Toplam sayı (ORM tarafı yeterli)
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

    # ORM SELECT — `misconception_tags`, `solution_steps`,
    # `similar_question_ids` ve `reviewed_at` kolonları artık ORM model'inde
    # tanımlı (Session 179, migration `curator_audit_20260521`).
    # Sıralama: md5(id) — random ama deterministic, kuyruğun curator'lar
    # arasında dağıtılmasını sağlar.
    paged_query = (
        base_query.order_by(func.md5(QuestionBankItem.id))
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    rows_result = await db.execute(paged_query)
    rows = rows_result.scalars().all()

    items = [_row_to_queue_item(row) for row in rows]
    return QueueResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/flagged", response_model=QueueResponse)
async def get_flagged_queue(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=200),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> QueueResponse:
    """Öğrenci tarafından flag'lenmiş (çözülmemiş) soruları curator kuyruğuna getir.

    Köprü: `student_question_flags` (resolved_at IS NULL) → `question_bank` join.
    Sıralama: en çok flag alan + en yeni soru üstte (öğrenci sinyali güçlü olan
    önce gözden geçirilsin). Soru hangi statüde olursa olsun (gold dahil) görünür.
    """
    # 1) Çözülmemiş flag'i olan distinct question_id + flag sayısı + en yeni tarih.
    #    question_bank join ile is_active=TRUE filtrelenir (pasifleştirilmiş soru
    #    curator'a sızmasın — /queue ile tutarlı).
    flag_agg = (
        select(
            StudentQuestionFlag.question_id.label("qid"),
            func.count().label("cnt"),
            func.max(StudentQuestionFlag.created_at).label("latest"),
        )
        .join(
            QuestionBankItem,
            QuestionBankItem.id == StudentQuestionFlag.question_id,
        )
        .where(
            StudentQuestionFlag.resolved_at.is_(None),
            QuestionBankItem.is_active.is_(True),
        )
        .group_by(StudentQuestionFlag.question_id)
        .subquery()
    )

    total = int(
        (await db.execute(select(func.count()).select_from(flag_agg))).scalar() or 0
    )
    if total == 0:
        return QueueResponse(items=[], total=0, page=page, per_page=per_page)

    # 2) Sayfalı, sıralı question_id listesi (en çok flag → en yeni)
    page_qids_stmt = (
        select(flag_agg.c.qid)
        .order_by(flag_agg.c.cnt.desc(), flag_agg.c.latest.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    qids = [r[0] for r in (await db.execute(page_qids_stmt)).all()]
    if not qids:
        return QueueResponse(items=[], total=total, page=page, per_page=per_page)

    # 3) question_bank içerikleri (sıra qids ile korunur)
    q_rows = (
        (
            await db.execute(
                select(QuestionBankItem).where(QuestionBankItem.id.in_(qids))
            )
        )
        .scalars()
        .all()
    )
    q_by_id = {str(r.id): r for r in q_rows}

    # 4) Flag detayları (flag_type + not) — question_id bazlı grupla
    detail_rows = (
        await db.execute(
            select(
                StudentQuestionFlag.question_id,
                StudentQuestionFlag.flag_type,
                StudentQuestionFlag.note,
            ).where(
                StudentQuestionFlag.question_id.in_(qids),
                StudentQuestionFlag.resolved_at.is_(None),
            )
        )
    ).all()

    flags_by_qid: dict[str, dict[str, dict[str, Any]]] = {}
    for qid, ftype, note in detail_rows:
        per_type = flags_by_qid.setdefault(str(qid), {})
        entry = per_type.setdefault(ftype, {"count": 0, "notes": []})
        entry["count"] += 1
        if note:
            entry["notes"].append(note)

    # 5) qids sırasını koruyarak QueueItem'ları kur
    items: list[QueueItem] = []
    for qid in qids:
        row = q_by_id.get(str(qid))
        if row is None:
            # FK CASCADE normalde önler; soru silinmişse atla
            continue
        item = _row_to_queue_item(row)
        per_type = flags_by_qid.get(str(qid), {})
        item.student_flags = [
            StudentFlagInfo(flag_type=ft, count=v["count"], notes=v["notes"])
            for ft, v in sorted(
                per_type.items(), key=lambda kv: kv[1]["count"], reverse=True
            )
        ]
        item.flag_count = sum(v["count"] for v in per_type.values())
        items.append(item)

    return QueueResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("/verdict", response_model=VerdictResponse)
async def post_verdict(
    body: VerdictRequest,
    request: Request,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> VerdictResponse:
    """Curator verdict'ini uygula:
    - quality_review_status'u verdict mapping'ine göre güncelle
    - reviewed_by = admin.id
    - pipeline_metadata.curator_verdict alanına audit trail JSON ekle
    - audit_logs tablosuna satır yaz
    """
    new_status = VERDICT_TO_STATUS.get(body.verdict)
    if new_status is None:
        # Pydantic Literal zaten doğrulamış olmalı ama defansif
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verdict '{body.verdict}'",
        )

    # Mevcut soruyu yükle (FOR UPDATE ile concurrent verdict'i önleyebiliriz
    # ama şimdilik basit bir SELECT yeterli)
    fetch_stmt = select(QuestionBankItem).where(
        QuestionBankItem.id == body.question_id,
        QuestionBankItem.is_active.is_(True)
    )
    row_result = await db.execute(fetch_stmt)
    row: QuestionBankItem | None = row_result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {body.question_id} not found",
        )

    previous_status = row.quality_review_status
    reviewed_at = datetime.now(UTC)

    # pipeline_metadata'ya curator_verdict ekle (mevcut JSON'ı koru)
    existing_metadata: dict[str, Any] = dict(row.pipeline_metadata or {})
    existing_metadata["curator_verdict"] = {
        "verdict": body.verdict,
        "notes": body.notes,
        "velocity_seconds": body.reviewer_velocity_seconds,
        "error_type": body.error_type,
        "previous_status": previous_status,
        "reviewer_id": str(admin.id),
        "reviewed_at": reviewed_at.isoformat(),
    }

    row.quality_review_status = new_status
    row.pipeline_metadata = existing_metadata
    row.reviewed_by = str(admin.id)
    # Faz 3.6 (Session 179): kolon-level audit timestamp.
    # JSON-embedded pipeline_metadata.curator_verdict.reviewed_at ile birlikte
    # tutulur (column = fast stats; JSON = full audit trail).
    row.reviewed_at = reviewed_at

    # Köprü (flag→curator): bu soruya ait çözülmemiş öğrenci flag'lerini de kapat.
    # reject/archive → flag "confirmed" (öğrenci haklıydı); verify → "rejected"
    # (yanlış alarm). Aynı transaction içinde; flag yoksa no-op.
    flag_resolution = (
        "confirmed" if body.verdict in ("reject", "archive") else "rejected"
    )
    await db.execute(
        update(StudentQuestionFlag)
        .where(
            StudentQuestionFlag.question_id == body.question_id,
            StudentQuestionFlag.resolved_at.is_(None),
        )
        .values(
            resolution=flag_resolution,
            resolved_at=reviewed_at,
            resolved_by=str(admin.id),
        )
    )

    # Audit log yaz (commit'ten önce — atomik)
    await _write_audit_log(
        db,
        admin_id=str(admin.id),
        question_id=body.question_id,
        verdict=body.verdict,
        previous_status=previous_status,
        new_status=new_status,
        notes=body.notes,
        velocity=body.reviewer_velocity_seconds,
        error_type=body.error_type,
        request=request,
    )

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error("Curator verdict commit failed for %s: %s", body.question_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database commit failed",
        ) from e

    # Kalite kapısı havuzunu tazele. Öğrenci-yüzü seçim `mv_safe_for_beta`
    # matview'ini okuyor; bu yargı orada görünene kadar REDDEDİLEN bir soru
    # servis edilmeye devam eder (Ders #31'in zaman-penceresi hâli).
    # Fire-and-forget: yargı DB'ye YAZILDIKTAN sonra çalışır, bu yüzden HİÇBİR
    # hata uca sızmamalı — aksi halde küratör "500 aldım" deyip aynı yargıyı
    # tekrar verir, oysa veri çoktan yazılmıştır. try/except import'u da kapsıyor:
    # modül eksikse (deploy kazası) uç yine 200 döner, yalnız yenileme gecikir.
    # asyncio.to_thread: kombu publish BLOKLAYICI I/O'dur; broker yavaşsa event
    # loop'u kilitleyip tüm eşzamanlı istekleri geciktirirdi.
    try:
        from tasks.quality_gate_tasks import schedule_safe_pool_refresh

        await asyncio.to_thread(schedule_safe_pool_refresh)
    except Exception as exc:
        logger.warning("safe_pool_refresh_dispatch_failed: %s", exc)

    return VerdictResponse(
        question_id=body.question_id,
        previous_status=previous_status,
        new_status=new_status,
        reviewed_by=str(admin.id),
        reviewed_at=reviewed_at,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    """Curator dashboard için özet istatistikler.

    Tek SQL sorgusunda tüm metrikleri topla (postgres JSON path operatorleri
    kullanılır; pipeline_metadata JSON tipindedir, jsonb cast gerekli).
    """
    sql = text(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE quality_review_status = 'bronze_clean'
            ) AS bronze_clean_count,
            COUNT(*) FILTER (
                WHERE quality_review_status = 'legacy_v3_unaudited'
            ) AS legacy_v3_unaudited_count,
            COUNT(*) FILTER (
                WHERE quality_review_status = 'pending'
            ) AS pending_status_count,
            COUNT(*) FILTER (
                WHERE (pipeline_metadata::jsonb -> 'curator_verdict' ->> 'verdict')
                      = 'verify'
            ) AS verified_count,
            COUNT(*) FILTER (
                WHERE quality_review_status = 'rejected'
                  AND (pipeline_metadata::jsonb -> 'curator_verdict'
                       ->> 'reviewed_at')::timestamptz
                      >= date_trunc('day', NOW() AT TIME ZONE 'UTC')
            ) AS rejected_today,
            AVG(
                NULLIF(
                    (pipeline_metadata::jsonb -> 'curator_verdict'
                     ->> 'velocity_seconds'),
                    ''
                )::numeric
            ) AS avg_velocity_sec
        FROM question_bank
        WHERE is_active = TRUE
        """
    )

    result = await db.execute(sql)
    row = result.first()

    # Öğrenci flag'lenmiş (çözülmemiş, aktif) distinct soru — 🚩 sekmesi rozeti.
    flagged_count = int(
        (
            await db.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT f.question_id)
                    FROM student_question_flags f
                    JOIN question_bank q ON q.id = f.question_id
                    WHERE f.resolved_at IS NULL AND q.is_active = TRUE
                    """
                )
            )
        ).scalar()
        or 0
    )

    if row is None:
        return StatsResponse(
            pending_count=0,
            bronze_clean_count=0,
            legacy_v3_unaudited_count=0,
            pending_status_count=0,
            verified_count=0,
            rejected_today=0,
            flagged_count=flagged_count,
            avg_velocity_sec=None,
        )

    bronze_clean_count = int(row.bronze_clean_count or 0)
    avg_velocity = row.avg_velocity_sec
    return StatsResponse(
        pending_count=bronze_clean_count,  # backward-compat alias
        bronze_clean_count=bronze_clean_count,
        legacy_v3_unaudited_count=int(row.legacy_v3_unaudited_count or 0),
        pending_status_count=int(row.pending_status_count or 0),
        verified_count=int(row.verified_count or 0),
        rejected_today=int(row.rejected_today or 0),
        flagged_count=flagged_count,
        avg_velocity_sec=float(avg_velocity) if avg_velocity is not None else None,
    )
