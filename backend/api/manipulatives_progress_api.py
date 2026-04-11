"""
Manipülatifler İlerleme ve Rozet API - Task 87.9
REQ-51.101-51.105: Progress tracking, visualization, achievement badges

Session 147 (GF95): Wave 10 three-part trap rewrite. All 5 handlers were
sync `def` + `Depends(get_db)` (deprecated sync shim) against an async
engine, which raises MissingGreenlet on every ORM call. Rewritten to
`async def` + `Depends(get_async_session)` + `await db.execute(select(...))`.
Identical rewrite pattern to instant_feedback_api.py (Session 145 GF86/GF87).
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import get_current_user
from models.database import (
    ManipulativeActivity,
    ManipulativeProgress,
    User,
)
from models.user_badge import UserBadge

router = APIRouter(
    prefix="/api/v1/manipulatives/progress", tags=["manipulatives-progress"]
)


# Pydantic Models
class Badge(BaseModel):
    """Rozet modeli"""

    id: str
    name: str
    description: str
    icon: str
    earned: bool
    earnedDate: str | None = None


# Total number of tangram puzzles (shared constant)
TOTAL_TANGRAM_PUZZLES = 10


def _evaluate_badge_conditions(
    progress_records: list[ManipulativeProgress],
    recent_activity_days: int,
    fast_activity_count: int,
) -> dict[str, bool]:
    """Pure function: compute badge conditions from already-loaded data."""
    virtual_blocks_ops = sum(
        p.operation_count
        for p in progress_records
        if p.manipulative_type == "virtualBlocks"
    )
    geogebra_activities = sum(
        p.operation_count for p in progress_records if p.manipulative_type == "geogebra"
    )
    geometry_shapes = sum(
        p.operation_count
        for p in progress_records
        if p.manipulative_type == "geometry" and p.activity_type != "measurement"
    )
    tangram_completed = sum(
        p.completion_count for p in progress_records if p.manipulative_type == "tangram"
    )
    measurements = sum(
        p.operation_count
        for p in progress_records
        if p.manipulative_type == "geometry" and p.activity_type == "measurement"
    )

    all_tools = set()
    for record in progress_records:
        if (
            record.manipulative_type == "geometry"
            and record.activity_data
            and "tools" in record.activity_data
        ):
            all_tools.update(record.activity_data["tools"])

    required_tools = {
        "line",
        "circle",
        "rectangle",
        "triangle",
        "ruler",
        "protractor",
    }
    has_all_tools = required_tools.issubset(all_tools)

    return {
        "first-block": virtual_blocks_ops >= 1,
        "math-explorer": geogebra_activities >= 10,
        "geometry-master": geometry_shapes >= 30,
        "tangram-solver": tangram_completed >= 5,
        "block-master": virtual_blocks_ops >= 50,
        "geogebra-expert": geogebra_activities >= 25,
        "shape-artist": geometry_shapes >= 50,
        "tangram-champion": tangram_completed >= TOTAL_TANGRAM_PUZZLES,
        "measurement-pro": measurements >= 50,
        "perfect-week": recent_activity_days >= 7,
        "speed-learner": fast_activity_count >= 10,
        "all-tools": has_all_tools,
    }


# API Endpoints


@router.get("/progress/dashboard")
async def get_progress_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Tüm manipülatifler için ilerleme panosunu getir
    REQ-51.101: Progress tracking
    """
    try:
        result = await db.execute(
            select(ManipulativeProgress).where(
                ManipulativeProgress.user_id == current_user.id
            )
        )
        progress_records = result.scalars().all()

        progress_data: dict = {}

        # Process virtualBlocks
        virtual_blocks = [
            p for p in progress_records if p.manipulative_type == "virtualBlocks"
        ]
        if virtual_blocks:
            operations_by_type: dict = {}
            total_ops = 0
            total_duration = 0
            total_mastery = 0

            for record in virtual_blocks:
                if record.activity_type:
                    operations_by_type[record.activity_type] = record.operation_count
                total_ops += record.operation_count
                total_duration += record.total_duration_seconds
                total_mastery += record.mastery_level

            avg_duration = (total_duration / total_ops) if total_ops > 0 else 0
            avg_mastery = (total_mastery / len(virtual_blocks)) if virtual_blocks else 0

            progress_data["virtualBlocks"] = {
                "total_operations": total_ops,
                "operations_by_type": operations_by_type,
                "avg_duration": int(avg_duration),
                "mastery_level": int(avg_mastery),
            }

        # Process geogebra
        geogebra = [p for p in progress_records if p.manipulative_type == "geogebra"]
        if geogebra:
            activities_by_type: dict = {}
            total_activities = 0
            total_completed = 0
            total_duration = 0

            for record in geogebra:
                if record.activity_type:
                    activities_by_type[record.activity_type] = record.operation_count
                total_activities += record.operation_count
                total_completed += record.completion_count
                total_duration += record.total_duration_seconds

            completion_rate = (
                (total_completed / total_activities) if total_activities > 0 else 0
            )
            avg_duration = (
                (total_duration / total_activities) if total_activities > 0 else 0
            )

            progress_data["geogebra"] = {
                "total_activities": total_activities,
                "activities_by_type": activities_by_type,
                "completion_rate": round(completion_rate, 2),
                "avg_duration": int(avg_duration),
            }

        # Process geometry
        geometry = [p for p in progress_records if p.manipulative_type == "geometry"]
        if geometry:
            shapes_by_type: dict = {}
            total_shapes = 0
            measurements_count = 0
            tools_used: set = set()

            for record in geometry:
                if record.activity_type:
                    if record.activity_type == "measurement":
                        measurements_count += record.operation_count
                    else:
                        shapes_by_type[record.activity_type] = record.operation_count
                        total_shapes += record.operation_count

                if record.activity_data and "tools" in record.activity_data:
                    tools_used.update(record.activity_data["tools"])

            progress_data["geometry"] = {
                "total_shapes": total_shapes,
                "shapes_by_type": shapes_by_type,
                "measurements_count": measurements_count,
                "tools_used": list(tools_used),
            }

        # Process tangram
        tangram = [p for p in progress_records if p.manipulative_type == "tangram"]
        if tangram:
            total_attempted = 0
            total_completed = 0
            total_attempts = 0

            for record in tangram:
                total_attempted += record.operation_count
                total_completed += record.completion_count
                if record.activity_data and "avg_attempts" in record.activity_data:
                    total_attempts += (
                        record.activity_data["avg_attempts"] * record.operation_count
                    )

            completion_rate = (
                (total_completed / total_attempted) if total_attempted > 0 else 0
            )
            avg_attempts = (
                (total_attempts / total_attempted) if total_attempted > 0 else 0
            )

            progress_data["tangram"] = {
                "puzzles_attempted": total_attempted,
                "puzzles_completed": total_completed,
                "completion_rate": round(completion_rate, 3),
                "avg_attempts": round(avg_attempts, 1),
            }

        return {"success": True, "data": progress_data}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/badges")
async def get_user_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Kullanıcının rozetlerini getir
    REQ-51.103: Achievement badges
    """
    try:
        earned_result = await db.execute(
            select(UserBadge).where(UserBadge.user_id == current_user.id)
        )
        earned_badges = earned_result.scalars().all()
        earned_badge_ids = {b.badge_id: b.earned_at for b in earned_badges}

        progress_result = await db.execute(
            select(ManipulativeProgress).where(
                ManipulativeProgress.user_id == current_user.id
            )
        )
        progress_records = list(progress_result.scalars().all())

        # Check for consecutive days (perfect week)
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        recent_days_result = await db.execute(
            select(func.date(ManipulativeActivity.created_at))
            .where(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= seven_days_ago,
            )
            .distinct()
        )
        recent_activities_count = len(recent_days_result.all())

        # Check for speed learner
        fast_result = await db.execute(
            select(func.count(ManipulativeActivity.id)).where(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.completed.is_(True),
                ManipulativeActivity.duration_seconds <= 30,
                ManipulativeActivity.duration_seconds > 0,
            )
        )
        fast_activities = fast_result.scalar() or 0

        conditions = _evaluate_badge_conditions(
            progress_records,
            recent_activity_days=recent_activities_count,
            fast_activity_count=fast_activities,
        )

        badge_metadata = {
            "first-block": ("İlk Blok", "İlk sanal blok işlemini tamamla", "🧱"),
            "math-explorer": (
                "Matematik Kaşifi",
                "10 farklı GeoGebra aktivitesi tamamla",
                "🔍",
            ),
            "geometry-master": ("Geometri Ustası", "30 şekil çiz", "📐"),
            "tangram-solver": ("Tangram Çözücü", "5 tangram puzzle'ı tamamla", "🧩"),
            "block-master": ("Blok Ustası", "50 blok işlemi tamamla", "🏆"),
            "geogebra-expert": (
                "GeoGebra Uzmanı",
                "25 GeoGebra aktivitesi tamamla",
                "⭐",
            ),
            "shape-artist": ("Şekil Sanatçısı", "50 şekil çiz", "🎨"),
            "tangram-champion": (
                "Tangram Şampiyonu",
                "Tüm tangram puzzle'larını tamamla",
                "🥇",
            ),
            "measurement-pro": ("Ölçüm Profesyoneli", "50 ölçüm yap", "📏"),
            "perfect-week": (
                "Mükemmel Hafta",
                "7 gün üst üste manipülatif kullan",
                "🔥",
            ),
            "speed-learner": (
                "Hızlı Öğrenci",
                "10 işlemi ortalama 30 saniyede tamamla",
                "⚡",
            ),
            "all-tools": ("Araç Koleksiyoncusu", "Tüm geometri araçlarını kullan", "🛠️"),
        }

        badges = []
        for badge_id, (name, description, icon) in badge_metadata.items():
            is_earned = badge_id in earned_badge_ids
            condition_met = conditions.get(badge_id, False)

            # Auto-award if condition met but not yet earned
            if condition_met and not is_earned:
                new_badge = UserBadge(
                    user_id=current_user.id,
                    badge_id=badge_id,
                    earned_at=datetime.now(UTC),
                    auto_awarded=True,
                )
                db.add(new_badge)
                await db.commit()
                earned_badge_ids[badge_id] = new_badge.earned_at
                is_earned = True

            badges.append(
                {
                    "id": badge_id,
                    "name": name,
                    "description": description,
                    "icon": icon,
                    "earned": is_earned,
                    "earnedDate": earned_badge_ids[badge_id].strftime("%Y-%m-%d")
                    if is_earned
                    else None,
                }
            )

        return {"success": True, "data": badges}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/progress/summary")
async def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Kullanıcının genel ilerleme özetini getir
    REQ-51.102: Progress visualization
    """
    try:
        progress_result = await db.execute(
            select(ManipulativeProgress).where(
                ManipulativeProgress.user_id == current_user.id
            )
        )
        progress_records = list(progress_result.scalars().all())

        total_time_spent = sum(p.total_duration_seconds for p in progress_records)
        total_activities = sum(p.operation_count for p in progress_records)

        mastery_percentage = 0
        if progress_records:
            mastery_percentage = int(
                sum(p.mastery_level for p in progress_records) / len(progress_records)
            )

        badges_result = await db.execute(
            select(func.count(UserBadge.id)).where(UserBadge.user_id == current_user.id)
        )
        badges_earned = badges_result.scalar() or 0
        badges_total = 12

        # Calculate current streak
        activity_dates_result = await db.execute(
            select(func.date(ManipulativeActivity.created_at))
            .where(ManipulativeActivity.user_id == current_user.id)
            .distinct()
            .order_by(func.date(ManipulativeActivity.created_at).desc())
        )
        activity_dates = activity_dates_result.all()

        current_streak = 0
        if activity_dates:
            current_date = datetime.now(UTC).date()
            expected_date = current_date

            for row in activity_dates:
                activity_date = row[0]
                if (
                    activity_date == expected_date
                    or activity_date == expected_date - timedelta(days=1)
                ):
                    current_streak += 1
                    expected_date = activity_date - timedelta(days=1)
                else:
                    break

        # Last activity
        last_result = await db.execute(
            select(ManipulativeActivity)
            .where(ManipulativeActivity.user_id == current_user.id)
            .order_by(ManipulativeActivity.created_at.desc())
            .limit(1)
        )
        last_activity = last_result.scalar_one_or_none()

        last_activity_date = (
            last_activity.created_at.isoformat() if last_activity else None
        )

        # Favorite tool
        manipulative_counts: dict = {}
        for record in progress_records:
            manipulative_counts[record.manipulative_type] = (
                manipulative_counts.get(record.manipulative_type, 0)
                + record.operation_count
            )

        favorite_tool = (
            max(manipulative_counts, key=manipulative_counts.get)
            if manipulative_counts
            else None
        )

        # Weekly goal progress
        week_start = datetime.now(UTC) - timedelta(days=datetime.now(UTC).weekday())
        weekly_result = await db.execute(
            select(func.count(ManipulativeActivity.id)).where(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= week_start,
            )
        )
        weekly_activities = weekly_result.scalar() or 0

        weekly_target = 20
        weekly_percentage = (
            int((weekly_activities / weekly_target) * 100) if weekly_target > 0 else 0
        )

        # Recent activities (last 3)
        recent_result = await db.execute(
            select(ManipulativeActivity)
            .where(ManipulativeActivity.user_id == current_user.id)
            .order_by(ManipulativeActivity.created_at.desc())
            .limit(3)
        )
        recent_activity_records = recent_result.scalars().all()

        recent_activities_list = []
        for activity in recent_activity_records:
            details = "Aktivite tamamlandı"
            if activity.details:
                if isinstance(activity.details, dict):
                    if "operation" in activity.details:
                        details = f"{activity.details['operation']} işlemi tamamlandı"
                    elif "puzzle_name" in activity.details:
                        details = f"{activity.details['puzzle_name']} puzzle'ı çözüldü"
                    elif "shapes_count" in activity.details:
                        details = f"{activity.details['shapes_count']} şekil çizildi"
                else:
                    details = str(activity.details)

            recent_activities_list.append(
                {
                    "type": activity.manipulative_type,
                    "date": activity.created_at.isoformat(),
                    "details": details,
                }
            )

        summary = {
            "total_time_spent": total_time_spent,
            "total_activities": total_activities,
            "mastery_percentage": mastery_percentage,
            "badges_earned": badges_earned,
            "badges_total": badges_total,
            "current_streak": current_streak,
            "last_activity_date": last_activity_date,
            "favorite_tool": favorite_tool,
            "weekly_goal_progress": {
                "current": weekly_activities,
                "target": weekly_target,
                "percentage": weekly_percentage,
            },
            "recent_activities": recent_activities_list,
        }

        return {"success": True, "data": summary}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/badges/{badge_id}/claim")
async def claim_badge(
    badge_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Rozet talep et (kullanıcı şartları sağladıysa)
    REQ-51.104: Badge earning system
    """
    try:
        existing_result = await db.execute(
            select(UserBadge).where(
                UserBadge.user_id == current_user.id,
                UserBadge.badge_id == badge_id,
            )
        )
        existing_badge = existing_result.scalar_one_or_none()

        if existing_badge:
            return {
                "success": False,
                "message": f"Rozet '{badge_id}' zaten kazanılmış!",
                "data": {
                    "badge_id": badge_id,
                    "earned_date": existing_badge.earned_at.isoformat(),
                },
            }

        # Fetch progress data to validate badge conditions
        progress_result = await db.execute(
            select(ManipulativeProgress).where(
                ManipulativeProgress.user_id == current_user.id
            )
        )
        progress_records = list(progress_result.scalars().all())

        # Check for consecutive days
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        recent_days_result = await db.execute(
            select(func.date(ManipulativeActivity.created_at))
            .where(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= seven_days_ago,
            )
            .distinct()
        )
        recent_activities_count = len(recent_days_result.all())

        # Check for speed learner
        fast_result = await db.execute(
            select(func.count(ManipulativeActivity.id)).where(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.completed.is_(True),
                ManipulativeActivity.duration_seconds <= 30,
                ManipulativeActivity.duration_seconds > 0,
            )
        )
        fast_activities = fast_result.scalar() or 0

        conditions = _evaluate_badge_conditions(
            progress_records,
            recent_activity_days=recent_activities_count,
            fast_activity_count=fast_activities,
        )

        if badge_id not in conditions:
            raise HTTPException(
                status_code=404, detail=f"Rozet '{badge_id}' bulunamadı!"
            )

        if not conditions[badge_id]:
            raise HTTPException(
                status_code=400, detail=f"Rozet '{badge_id}' için şartlar sağlanmadı!"
            )

        # Award the badge
        new_badge = UserBadge(
            user_id=current_user.id,
            badge_id=badge_id,
            earned_at=datetime.now(UTC),
            auto_awarded=False,
        )
        db.add(new_badge)
        await db.commit()

        return {
            "success": True,
            "message": f"Rozet '{badge_id}' kazanıldı!",
            "data": {
                "badge_id": badge_id,
                "earned_date": new_badge.earned_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/progress/weekly")
async def get_weekly_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Haftalık ilerleme grafiği için veri
    REQ-51.105: Weekly progress tracking
    """
    try:
        today = datetime.now(UTC)
        seven_days_ago = today - timedelta(days=6)

        day_names = [
            "Pazartesi",
            "Salı",
            "Çarşamba",
            "Perşembe",
            "Cuma",
            "Cumartesi",
            "Pazar",
        ]

        weekly_data = []
        daily_counts: dict = {}
        daily_times: dict = {}

        # Fetch activities for the last 7 days
        activities_result = await db.execute(
            select(
                func.date(ManipulativeActivity.created_at).label("activity_date"),
                func.count(ManipulativeActivity.id).label("activity_count"),
                func.sum(ManipulativeActivity.duration_seconds).label("total_time"),
            )
            .where(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= seven_days_ago,
            )
            .group_by(func.date(ManipulativeActivity.created_at))
        )

        for row in activities_result.all():
            activity_date, count, total_time = row
            daily_counts[activity_date] = count
            daily_times[activity_date] = total_time or 0

        for i in range(7):
            current_date = (seven_days_ago + timedelta(days=i)).date()
            day_of_week = current_date.weekday()
            day_name = day_names[day_of_week]

            activity_count = daily_counts.get(current_date, 0)
            time_seconds = daily_times.get(current_date, 0)

            weekly_data.append(
                {"day": day_name, "activities": activity_count, "time": time_seconds}
            )

        total_activities = sum(d["activities"] for d in weekly_data)
        total_time = sum(d["time"] for d in weekly_data)
        avg_daily_activities = total_activities / 7 if weekly_data else 0

        most_active_day = "Pazartesi"
        max_activities = 0
        for day_data in weekly_data:
            if day_data["activities"] > max_activities:
                max_activities = day_data["activities"]
                most_active_day = day_data["day"]

        return {
            "success": True,
            "data": {
                "week": weekly_data,
                "total_activities": total_activities,
                "total_time": total_time,
                "avg_daily_activities": round(avg_daily_activities, 1),
                "most_active_day": most_active_day,
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
