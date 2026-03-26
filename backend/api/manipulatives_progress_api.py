"""
Manipülatifler İlerleme ve Rozet API - Task 87.9
REQ-51.101-51.105: Progress tracking, visualization, achievement badges
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from core.database import get_db
from core.auth_dependencies import get_current_user
from models.database import (
    User,
    ManipulativeProgress,
    ManipulativeActivity,
)
from models.user_badge import UserBadge

router = APIRouter(prefix="/api/v1/manipulatives/progress", tags=["manipulatives-progress"])


# Pydantic Models
class Badge(BaseModel):
    """Rozet modeli"""

    id: str
    name: str
    description: str
    icon: str
    earned: bool
    earnedDate: str | None = None


# API Endpoints


@router.get("/progress/dashboard")
async def get_progress_dashboard(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Tüm manipülatifler için ilerleme panosunu getir
    REQ-51.101: Progress tracking
    """
    try:
        # Fetch all progress records for the user
        progress_records = (
            db.query(ManipulativeProgress)
            .filter(ManipulativeProgress.user_id == current_user.id)
            .all()
        )

        # Initialize progress data structure
        progress_data = {}

        # Process virtualBlocks
        virtual_blocks = [
            p for p in progress_records if p.manipulative_type == "virtualBlocks"
        ]
        if virtual_blocks:
            operations_by_type = {}
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
            activities_by_type = {}
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
            shapes_by_type = {}
            total_shapes = 0
            measurements_count = 0
            tools_used = set()

            for record in geometry:
                if record.activity_type:
                    if record.activity_type == "measurement":
                        measurements_count += record.operation_count
                    else:
                        shapes_by_type[record.activity_type] = record.operation_count
                        total_shapes += record.operation_count

                # Extract tools from activity_data
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
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/badges")
async def get_user_badges(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Kullanıcının rozetlerini getir
    REQ-51.103: Achievement badges
    """
    try:
        # Fetch earned badges from database
        earned_badges = (
            db.query(UserBadge).filter(UserBadge.user_id == current_user.id).all()
        )
        earned_badge_ids = {b.badge_id: b.earned_at for b in earned_badges}

        # Fetch progress data to check badge conditions
        progress_records = (
            db.query(ManipulativeProgress)
            .filter(ManipulativeProgress.user_id == current_user.id)
            .all()
        )

        # Calculate metrics for badge conditions
        virtual_blocks_ops = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "virtualBlocks"
        )
        geogebra_activities = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "geogebra"
        )
        geometry_shapes = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "geometry" and p.activity_type != "measurement"
        )
        tangram_completed = sum(
            p.completion_count
            for p in progress_records
            if p.manipulative_type == "tangram"
        )
        measurements = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "geometry" and p.activity_type == "measurement"
        )

        # Check for consecutive days (perfect week)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_activities = (
            db.query(func.date(ManipulativeActivity.created_at))
            .filter(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= seven_days_ago,
            )
            .distinct()
            .count()
        )

        # Check for speed learner (fast operations)
        fast_activities = (
            db.query(ManipulativeActivity)
            .filter(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.completed == True,
                ManipulativeActivity.duration_seconds <= 30,
                ManipulativeActivity.duration_seconds > 0,
            )
            .count()
        )

        # Check all tools used
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

        # Total tangram puzzles (assuming 10 puzzles available)
        TOTAL_TANGRAM_PUZZLES = 10

        # Define all badges with conditions
        badge_definitions = [
            {
                "id": "first-block",
                "name": "İlk Blok",
                "description": "İlk sanal blok işlemini tamamla",
                "icon": "🧱",
                "condition": virtual_blocks_ops >= 1,
            },
            {
                "id": "math-explorer",
                "name": "Matematik Kaşifi",
                "description": "10 farklı GeoGebra aktivitesi tamamla",
                "icon": "🔍",
                "condition": geogebra_activities >= 10,
            },
            {
                "id": "geometry-master",
                "name": "Geometri Ustası",
                "description": "30 şekil çiz",
                "icon": "📐",
                "condition": geometry_shapes >= 30,
            },
            {
                "id": "tangram-solver",
                "name": "Tangram Çözücü",
                "description": "5 tangram puzzle'ı tamamla",
                "icon": "🧩",
                "condition": tangram_completed >= 5,
            },
            {
                "id": "block-master",
                "name": "Blok Ustası",
                "description": "50 blok işlemi tamamla",
                "icon": "🏆",
                "condition": virtual_blocks_ops >= 50,
            },
            {
                "id": "geogebra-expert",
                "name": "GeoGebra Uzmanı",
                "description": "25 GeoGebra aktivitesi tamamla",
                "icon": "⭐",
                "condition": geogebra_activities >= 25,
            },
            {
                "id": "shape-artist",
                "name": "Şekil Sanatçısı",
                "description": "50 şekil çiz",
                "icon": "🎨",
                "condition": geometry_shapes >= 50,
            },
            {
                "id": "tangram-champion",
                "name": "Tangram Şampiyonu",
                "description": "Tüm tangram puzzle'larını tamamla",
                "icon": "🥇",
                "condition": tangram_completed >= TOTAL_TANGRAM_PUZZLES,
            },
            {
                "id": "measurement-pro",
                "name": "Ölçüm Profesyoneli",
                "description": "50 ölçüm yap",
                "icon": "📏",
                "condition": measurements >= 50,
            },
            {
                "id": "perfect-week",
                "name": "Mükemmel Hafta",
                "description": "7 gün üst üste manipülatif kullan",
                "icon": "🔥",
                "condition": recent_activities >= 7,
            },
            {
                "id": "speed-learner",
                "name": "Hızlı Öğrenci",
                "description": "10 işlemi ortalama 30 saniyede tamamla",
                "icon": "⚡",
                "condition": fast_activities >= 10,
            },
            {
                "id": "all-tools",
                "name": "Araç Koleksiyoncusu",
                "description": "Tüm geometri araçlarını kullan",
                "icon": "🛠️",
                "condition": has_all_tools,
            },
        ]

        # Build response
        badges = []
        for badge_def in badge_definitions:
            badge_id = badge_def["id"]
            is_earned = badge_id in earned_badge_ids

            # If condition met but not yet earned, auto-award it
            if badge_def["condition"] and not is_earned:
                new_badge = UserBadge(
                    user_id=current_user.id,
                    badge_id=badge_id,
                    earned_at=datetime.now(timezone.utc),
                    auto_awarded=True,
                )
                db.add(new_badge)
                db.commit()
                earned_badge_ids[badge_id] = new_badge.earned_at
                is_earned = True

            badges.append(
                {
                    "id": badge_id,
                    "name": badge_def["name"],
                    "description": badge_def["description"],
                    "icon": badge_def["icon"],
                    "earned": is_earned,
                    "earnedDate": earned_badge_ids[badge_id].strftime("%Y-%m-%d")
                    if is_earned
                    else None,
                }
            )

        return {"success": True, "data": badges}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/progress/summary")
async def get_progress_summary(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Kullanıcının genel ilerleme özetini getir
    REQ-51.102: Progress visualization
    """
    try:
        # Fetch all progress records
        progress_records = (
            db.query(ManipulativeProgress)
            .filter(ManipulativeProgress.user_id == current_user.id)
            .all()
        )

        # Calculate total time spent (in seconds)
        total_time_spent = sum(p.total_duration_seconds for p in progress_records)

        # Calculate total activities
        total_activities = sum(p.operation_count for p in progress_records)

        # Calculate mastery percentage (average of all mastery levels)
        mastery_percentage = 0
        if progress_records:
            mastery_percentage = int(
                sum(p.mastery_level for p in progress_records) / len(progress_records)
            )

        # Count earned badges
        badges_earned = (
            db.query(UserBadge).filter(UserBadge.user_id == current_user.id).count()
        )
        badges_total = 12  # Total number of available badges

        # Calculate current streak
        # Get distinct activity dates ordered by date
        activity_dates = (
            db.query(func.date(ManipulativeActivity.created_at))
            .filter(ManipulativeActivity.user_id == current_user.id)
            .distinct()
            .order_by(func.date(ManipulativeActivity.created_at).desc())
            .all()
        )

        current_streak = 0
        if activity_dates:
            current_date = datetime.now(timezone.utc).date()
            expected_date = current_date

            for (activity_date,) in activity_dates:
                if (
                    activity_date == expected_date
                    or activity_date == expected_date - timedelta(days=1)
                ):
                    current_streak += 1
                    expected_date = activity_date - timedelta(days=1)
                else:
                    break

        # Get last activity date
        last_activity = (
            db.query(ManipulativeActivity)
            .filter(ManipulativeActivity.user_id == current_user.id)
            .order_by(ManipulativeActivity.created_at.desc())
            .first()
        )

        last_activity_date = (
            last_activity.created_at.isoformat() if last_activity else None
        )

        # Find favorite tool (most used manipulative type)
        manipulative_counts = {}
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

        # Weekly goal progress (current week)
        current_week = datetime.now(timezone.utc).isocalendar()[1]
        current_year = datetime.now(timezone.utc).year

        week_start = datetime.now(timezone.utc) - timedelta(days=datetime.now(timezone.utc).weekday())
        weekly_activities = (
            db.query(ManipulativeActivity)
            .filter(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= week_start,
            )
            .count()
        )

        weekly_target = 20  # Default weekly goal
        weekly_percentage = (
            int((weekly_activities / weekly_target) * 100) if weekly_target > 0 else 0
        )

        # Get recent activities (last 3)
        recent_activity_records = (
            db.query(ManipulativeActivity)
            .filter(ManipulativeActivity.user_id == current_user.id)
            .order_by(ManipulativeActivity.created_at.desc())
            .limit(3)
            .all()
        )

        recent_activities = []
        for activity in recent_activity_records:
            details = "Aktivite tamamlandı"
            if activity.details:
                if isinstance(activity.details, dict):
                    # Extract meaningful details from JSON
                    if "operation" in activity.details:
                        details = f"{activity.details['operation']} işlemi tamamlandı"
                    elif "puzzle_name" in activity.details:
                        details = f"{activity.details['puzzle_name']} puzzle'ı çözüldü"
                    elif "shapes_count" in activity.details:
                        details = f"{activity.details['shapes_count']} şekil çizildi"
                else:
                    details = str(activity.details)

            recent_activities.append(
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
            "recent_activities": recent_activities,
        }

        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/badges/{badge_id}/claim")
async def claim_badge(
    badge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Rozet talep et (kullanıcı şartları sağladıysa)
    REQ-51.104: Badge earning system
    """
    try:
        # Check if badge already earned
        existing_badge = (
            db.query(UserBadge)
            .filter(
                UserBadge.user_id == current_user.id, UserBadge.badge_id == badge_id
            )
            .first()
        )

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
        progress_records = (
            db.query(ManipulativeProgress)
            .filter(ManipulativeProgress.user_id == current_user.id)
            .all()
        )

        # Calculate metrics for validation
        virtual_blocks_ops = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "virtualBlocks"
        )
        geogebra_activities = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "geogebra"
        )
        geometry_shapes = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "geometry" and p.activity_type != "measurement"
        )
        tangram_completed = sum(
            p.completion_count
            for p in progress_records
            if p.manipulative_type == "tangram"
        )
        measurements = sum(
            p.operation_count
            for p in progress_records
            if p.manipulative_type == "geometry" and p.activity_type == "measurement"
        )

        # Check for consecutive days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_activities = (
            db.query(func.date(ManipulativeActivity.created_at))
            .filter(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= seven_days_ago,
            )
            .distinct()
            .count()
        )

        # Check for speed learner
        fast_activities = (
            db.query(ManipulativeActivity)
            .filter(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.completed == True,
                ManipulativeActivity.duration_seconds <= 30,
                ManipulativeActivity.duration_seconds > 0,
            )
            .count()
        )

        # Check all tools used
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

        # Define badge conditions
        TOTAL_TANGRAM_PUZZLES = 10
        badge_conditions = {
            "first-block": virtual_blocks_ops >= 1,
            "math-explorer": geogebra_activities >= 10,
            "geometry-master": geometry_shapes >= 30,
            "tangram-solver": tangram_completed >= 5,
            "block-master": virtual_blocks_ops >= 50,
            "geogebra-expert": geogebra_activities >= 25,
            "shape-artist": geometry_shapes >= 50,
            "tangram-champion": tangram_completed >= TOTAL_TANGRAM_PUZZLES,
            "measurement-pro": measurements >= 50,
            "perfect-week": recent_activities >= 7,
            "speed-learner": fast_activities >= 10,
            "all-tools": has_all_tools,
        }

        # Validate badge condition
        if badge_id not in badge_conditions:
            raise HTTPException(
                status_code=404, detail=f"Rozet '{badge_id}' bulunamadı!"
            )

        if not badge_conditions[badge_id]:
            raise HTTPException(
                status_code=400, detail=f"Rozet '{badge_id}' için şartlar sağlanmadı!"
            )

        # Award the badge
        new_badge = UserBadge(
            user_id=current_user.id,
            badge_id=badge_id,
            earned_at=datetime.now(timezone.utc),
            auto_awarded=False,  # Manually claimed
        )
        db.add(new_badge)
        db.commit()

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
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/progress/weekly")
async def get_weekly_progress(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Haftalık ilerleme grafiği için veri
    REQ-51.105: Weekly progress tracking
    """
    try:
        # Calculate last 7 days date range
        today = datetime.now(timezone.utc)
        seven_days_ago = today - timedelta(days=6)  # Include today, so 7 days total

        # Turkish day names
        day_names = [
            "Pazartesi",
            "Salı",
            "Çarşamba",
            "Perşembe",
            "Cuma",
            "Cumartesi",
            "Pazar",
        ]

        # Initialize weekly data structure
        weekly_data = []
        daily_counts = {}
        daily_times = {}

        # Fetch activities for the last 7 days
        activities = (
            db.query(
                func.date(ManipulativeActivity.created_at).label("activity_date"),
                func.count(ManipulativeActivity.id).label("activity_count"),
                func.sum(ManipulativeActivity.duration_seconds).label("total_time"),
            )
            .filter(
                ManipulativeActivity.user_id == current_user.id,
                ManipulativeActivity.created_at >= seven_days_ago,
            )
            .group_by(func.date(ManipulativeActivity.created_at))
            .all()
        )

        # Build lookup dictionary
        for activity_date, count, total_time in activities:
            daily_counts[activity_date] = count
            daily_times[activity_date] = total_time or 0

        # Build weekly data for each day
        for i in range(7):
            current_date = (seven_days_ago + timedelta(days=i)).date()
            day_of_week = current_date.weekday()  # Monday = 0, Sunday = 6
            day_name = day_names[day_of_week]

            activity_count = daily_counts.get(current_date, 0)
            time_seconds = daily_times.get(current_date, 0)

            weekly_data.append(
                {"day": day_name, "activities": activity_count, "time": time_seconds}
            )

        # Calculate summary statistics
        total_activities = sum(d["activities"] for d in weekly_data)
        total_time = sum(d["time"] for d in weekly_data)
        avg_daily_activities = total_activities / 7 if weekly_data else 0

        # Find most active day
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
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
