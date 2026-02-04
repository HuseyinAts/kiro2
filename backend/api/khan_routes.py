"""
Task 98: Khan Academy API Routes
OAuth, content browsing, progress sync, and certificates
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, UUID4
from datetime import datetime

# PHASE 1 FIX: Corrected import paths (removed 'backend.' prefix)
from core.database import get_db
from models.database import User
from services.khan_academy_client import KhanSubject, KhanContentType, get_khan_client
from services.khan_content_sync import KhanContentSyncService, KhanProgressSyncService
from core.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/khan", tags=["Khan Academy Integration"])


# ============================================
# Request/Response Models
# ============================================


class KhanContentResponse(BaseModel):
    """Khan content response"""

    content_id: str
    title: str
    description: Optional[str]
    content_type: str
    subject: str
    topic: Optional[str]
    video_url: Optional[str]
    duration_seconds: Optional[int]
    thumbnail_url: Optional[str]
    exercise_url: Optional[str]
    problem_count: Optional[int]
    difficulty_level: Optional[str]


class KhanProgressResponse(BaseModel):
    """Khan progress response"""

    content_id: str
    content_title: str
    content_type: str
    started_at: Optional[str]
    completed_at: Optional[str]
    last_accessed: Optional[str]
    video_seconds_watched: int
    video_completed: bool
    problems_attempted: int
    problems_correct: int
    proficiency_level: Optional[str]
    energy_points: int


class KhanCertificateResponse(BaseModel):
    """Khan certificate response"""

    badge_id: str
    badge_name: str
    badge_category: str
    description: Optional[str]
    icon_url: Optional[str]
    verification_url: Optional[str]
    earned_at: str


class SyncStatsResponse(BaseModel):
    """Sync statistics"""

    total_items: int
    new_items: int
    updated_items: int
    errors: int


# ============================================
# Task 98.1: OAuth Authentication
# ============================================


@router.get("/oauth/connect")
async def initiate_khan_oauth(
    redirect_uri: str = Query(..., description="OAuth redirect URI"),
    current_user: User = Depends(get_current_user),
):
    """
    Task 98.1: Initiate Khan Academy OAuth flow

    Step 1: Redirect user to Khan Academy login
    """
    khan_client = get_khan_client(use_mock=False)

    try:
        # Generate unique state for CSRF protection
        import secrets

        state = secrets.token_urlsafe(32)

        # Store state in session (in production, use Redis)
        # For now, we'll return it in response

        auth_url = khan_client.get_authorization_url(
            redirect_uri=redirect_uri, state=state
        )

        return {
            "authorization_url": auth_url,
            "state": state,
            "message": "Redirect user to authorization_url",
        }

    except Exception as e:
        logger.error(f"Failed to initiate OAuth: {e}")
        raise HTTPException(status_code=500, detail="OAuth initialization failed")

    finally:
        await khan_client.close()


@router.get("/oauth/callback")
async def khan_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="CSRF state"),
    redirect_uri: str = Query(..., description="Redirect URI"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 98.1: OAuth callback handler

    Step 2: Exchange code for access token and store
    """
    from models.khan_content import KhanOAuthToken

    khan_client = get_khan_client(use_mock=False)

    try:
        # Exchange code for tokens
        token_data = await khan_client.exchange_code_for_token(
            authorization_code=code, redirect_uri=redirect_uri
        )

        # Store tokens in database
        from sqlalchemy import select

        stmt = select(KhanOAuthToken).where(KhanOAuthToken.user_id == current_user.id)
        result = await db.execute(stmt)
        existing_token = result.scalar_one_or_none()

        if existing_token:
            # Update existing
            existing_token.access_token = token_data["access_token"]
            existing_token.refresh_token = token_data.get("refresh_token")
            existing_token.expires_at = datetime.fromisoformat(token_data["expires_at"])
            existing_token.is_active = True
            existing_token.last_refreshed_at = datetime.now()

        else:
            # Create new
            new_token = KhanOAuthToken(
                user_id=current_user.id,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=datetime.fromisoformat(token_data["expires_at"]),
                scopes=["user:read", "progress:read", "badges:read"],
                is_active=True,
            )
            db.add(new_token)

        await db.commit()

        logger.info(f"[KHAN OAUTH] Successfully connected user {current_user.id}")

        return {
            "success": True,
            "message": "Khan Academy hesabınız başarıyla bağlandı!",
            "expires_at": token_data["expires_at"],
        }

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")

    finally:
        await khan_client.close()


@router.get("/oauth/status")
async def get_oauth_status(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Check if user has connected Khan Academy account
    """
    from models.khan_content import KhanOAuthToken
    from sqlalchemy import select

    stmt = select(KhanOAuthToken).where(
        KhanOAuthToken.user_id == current_user.id, KhanOAuthToken.is_active == True
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()

    if not token:
        return {"connected": False, "message": "Khan Academy hesabı bağlı değil"}

    # Check if expired
    is_expired = datetime.now() >= token.expires_at

    return {
        "connected": True,
        "expires_at": token.expires_at.isoformat(),
        "is_expired": is_expired,
        "khan_user_id": token.khan_user_id,
    }


# ============================================
# Task 98.2: Turkish Content Browsing
# ============================================


@router.get("/content", response_model=List[KhanContentResponse])
async def get_khan_content(
    subject: Optional[KhanSubject] = None,
    content_type: Optional[KhanContentType] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 98.2: Browse Turkish Khan Academy content

    Filters available:
    - subject: math, science, computing, etc.
    - content_type: video, exercise, article
    - difficulty: beginner, intermediate, advanced
    - search: Search in title/description
    """
    from models.khan_content import KhanContent
    from sqlalchemy import select, and_, or_

    # Build query
    filters = [KhanContent.language == "tr"]

    if subject:
        filters.append(KhanContent.subject == subject.value)

    if content_type:
        filters.append(KhanContent.content_type == content_type.value)

    if difficulty:
        filters.append(KhanContent.difficulty_level == difficulty)

    if search:
        filters.append(
            or_(
                KhanContent.title.ilike(f"%{search}%"),
                KhanContent.description.ilike(f"%{search}%"),
            )
        )

    stmt = select(KhanContent).where(and_(*filters))

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    # Order by created date
    stmt = stmt.order_by(KhanContent.created_at.desc())

    result = await db.execute(stmt)
    contents = result.scalars().all()

    return [
        KhanContentResponse(
            content_id=c.khan_content_id,
            title=c.title,
            description=c.description,
            content_type=c.content_type,
            subject=c.subject,
            topic=c.topic,
            video_url=c.video_url,
            duration_seconds=c.duration_seconds,
            thumbnail_url=c.thumbnail_url,
            exercise_url=c.exercise_url,
            problem_count=c.problem_count,
            difficulty_level=c.difficulty_level,
        )
        for c in contents
    ]


@router.get("/content/{content_id}", response_model=KhanContentResponse)
async def get_khan_content_details(content_id: str, db: AsyncSession = Depends(get_db)):
    """Get specific Khan content details"""
    from models.khan_content import KhanContent
    from sqlalchemy import select

    stmt = select(KhanContent).where(KhanContent.khan_content_id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return KhanContentResponse(
        content_id=content.khan_content_id,
        title=content.title,
        description=content.description,
        content_type=content.content_type,
        subject=content.subject,
        topic=content.topic,
        video_url=content.video_url,
        duration_seconds=content.duration_seconds,
        thumbnail_url=content.thumbnail_url,
        exercise_url=content.exercise_url,
        problem_count=content.problem_count,
        difficulty_level=content.difficulty_level,
    )


# ============================================
# Task 98.3: Progress Synchronization
# ============================================


@router.post("/progress/sync")
async def sync_user_progress(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Task 98.3: Bidirectional progress sync

    Pull progress from Khan Academy and push local progress
    """
    from models.khan_content import KhanOAuthToken
    from sqlalchemy import select

    # Get OAuth token
    stmt = select(KhanOAuthToken).where(
        KhanOAuthToken.user_id == current_user.id, KhanOAuthToken.is_active == True
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()

    if not token or not token.khan_user_id:
        raise HTTPException(
            status_code=400,
            detail="Khan Academy hesabı bağlı değil. Önce /oauth/connect kullanın.",
        )

    sync_service = KhanProgressSyncService(db, use_mock=False)

    try:
        stats = await sync_service.sync_bidirectional(
            user_id=str(current_user.id), khan_user_id=token.khan_user_id
        )

        return {
            "success": True,
            "message": "İlerleme senkronizasyonu tamamlandı",
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Progress sync failed: {e}")
        raise HTTPException(status_code=500, detail="Senkronizasyon başarısız")

    finally:
        await sync_service.close()


@router.get("/progress", response_model=List[KhanProgressResponse])
async def get_user_progress(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Task 98.3: Get user's Khan Academy progress

    Returns all progress entries
    """
    from models.khan_content import KhanUserProgress, KhanContent
    from sqlalchemy import select

    stmt = (
        select(KhanUserProgress, KhanContent)
        .join(KhanContent, KhanUserProgress.khan_content_id == KhanContent.id)
        .where(KhanUserProgress.user_id == current_user.id)
        .order_by(KhanUserProgress.last_accessed.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        KhanProgressResponse(
            content_id=content.khan_content_id,
            content_title=content.title,
            content_type=progress.content_type,
            started_at=progress.started_at.isoformat() if progress.started_at else None,
            completed_at=progress.completed_at.isoformat()
            if progress.completed_at
            else None,
            last_accessed=progress.last_accessed.isoformat()
            if progress.last_accessed
            else None,
            video_seconds_watched=progress.video_seconds_watched,
            video_completed=progress.video_completed,
            problems_attempted=progress.problems_attempted,
            problems_correct=progress.problems_correct,
            proficiency_level=progress.proficiency_level,
            energy_points=progress.energy_points,
        )
        for progress, content in rows
    ]


@router.get("/progress/analytics")
async def get_progress_analytics(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Task 98.3: Get user progress analytics

    Summary statistics of Khan Academy learning
    """
    from models.khan_content import KhanUserProgress
    from sqlalchemy import select, func

    # Total energy points
    stmt = select(func.sum(KhanUserProgress.energy_points)).where(
        KhanUserProgress.user_id == current_user.id
    )
    result = await db.execute(stmt)
    total_points = result.scalar_one() or 0

    # Completed videos
    stmt = select(func.count(KhanUserProgress.id)).where(
        KhanUserProgress.user_id == current_user.id,
        KhanUserProgress.video_completed == True,
    )
    result = await db.execute(stmt)
    completed_videos = result.scalar_one()

    # Mastered exercises
    stmt = select(func.count(KhanUserProgress.id)).where(
        KhanUserProgress.user_id == current_user.id,
        KhanUserProgress.proficiency_level == "mastered",
    )
    result = await db.execute(stmt)
    mastered_exercises = result.scalar_one()

    # Total content accessed
    stmt = select(func.count(KhanUserProgress.id)).where(
        KhanUserProgress.user_id == current_user.id
    )
    result = await db.execute(stmt)
    total_accessed = result.scalar_one()

    return {
        "total_energy_points": total_points,
        "completed_videos": completed_videos,
        "mastered_exercises": mastered_exercises,
        "total_content_accessed": total_accessed,
    }


# ============================================
# Task 98.4: Certificate/Badge Integration
# ============================================


@router.get("/badges", response_model=List[KhanCertificateResponse])
async def get_user_badges(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Task 98.4: Get user's Khan Academy badges/certificates
    """
    from models.khan_content import KhanCertificate
    from sqlalchemy import select

    stmt = (
        select(KhanCertificate)
        .where(KhanCertificate.user_id == current_user.id)
        .order_by(KhanCertificate.earned_at.desc())
    )

    result = await db.execute(stmt)
    certificates = result.scalars().all()

    return [
        KhanCertificateResponse(
            badge_id=cert.badge_id,
            badge_name=cert.badge_name,
            badge_category=cert.badge_category,
            description=cert.description,
            icon_url=cert.icon_url,
            verification_url=cert.verification_url,
            earned_at=cert.earned_at.isoformat(),
        )
        for cert in certificates
    ]


@router.post("/badges/sync")
async def sync_user_badges(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Task 98.4: Sync badges from Khan Academy
    """
    from models.khan_content import KhanOAuthToken, KhanCertificate
    from sqlalchemy import select

    # Get OAuth token
    stmt = select(KhanOAuthToken).where(
        KhanOAuthToken.user_id == current_user.id, KhanOAuthToken.is_active == True
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()

    if not token or not token.khan_user_id:
        raise HTTPException(status_code=400, detail="Khan Academy hesabı bağlı değil")

    khan_client = get_khan_client(use_mock=False)

    try:
        # Fetch badges from Khan Academy
        badges = await khan_client.get_user_badges(token.khan_user_id)

        new_badges = 0
        for badge in badges:
            # Check if already exists
            stmt = select(KhanCertificate).where(
                KhanCertificate.badge_id == badge.certificate_id
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                new_cert = KhanCertificate(
                    user_id=current_user.id,
                    khan_user_id=token.khan_user_id,
                    badge_id=badge.certificate_id,
                    badge_name=badge.badge_name,
                    badge_category=badge.badge_category,
                    description=badge.description,
                    icon_url=badge.icon_url,
                    verification_url=badge.verification_url,
                    earned_at=badge.earned_at,
                )
                db.add(new_cert)
                new_badges += 1

        await db.commit()

        return {
            "success": True,
            "total_badges": len(badges),
            "new_badges": new_badges,
            "message": f"{new_badges} yeni rozet eklendi",
        }

    except Exception as e:
        logger.error(f"Badge sync failed: {e}")
        raise HTTPException(status_code=500, detail="Rozet senkronizasyonu başarısız")

    finally:
        await khan_client.close()


# ============================================
# Admin Endpoints
# ============================================


@router.post("/admin/sync/content", response_model=SyncStatsResponse)
async def trigger_content_sync(
    subjects: Optional[List[KhanSubject]] = None,
    use_mock: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: Trigger Khan Academy content sync
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    sync_service = KhanContentSyncService(db, use_mock=use_mock)

    try:
        logger.info(f"[ADMIN] Starting Khan content sync (user: {current_user.email})")

        stats = await sync_service.sync_turkish_content(subjects=subjects)

        return SyncStatsResponse(
            total_items=stats["total_fetched"],
            new_items=stats["new_content"],
            updated_items=stats["updated_content"],
            errors=stats["errors"],
        )

    except Exception as e:
        logger.error(f"Content sync failed: {e}")
        raise HTTPException(status_code=500, detail="Sync failed")

    finally:
        await sync_service.close()


logger.info("[OK] [KHAN ACADEMY] Khan Academy entegrasyon API'si yüklendi (Task 98)")
