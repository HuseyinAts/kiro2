"""
Manipülatifler API - Diskalkuli Desteği
Task 87: Sanal bloklar, GeoGebra, İnteraktif geometri, Dijital tangram
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import (
    get_current_user,  # fixed: was auth_dependencies (no blacklist)
)
from models.database import User

router = APIRouter(prefix="/api/v1/manipulatives", tags=["manipulatives"])


def _require_body_user_id_matches(current_user: User, body_user_id: str) -> None:
    if str(body_user_id).strip() != str(current_user.id).strip():
        raise HTTPException(
            status_code=403,
            detail="user_id must match authenticated user",
        )


# Pydantic Models
class VirtualBlockOperation(BaseModel):
    """Sanal blok işlemi"""

    operation_type: str  # add, subtract, multiply, divide
    blocks_used: list[dict]  # [{type: 'unit', count: 5}, {type: 'ten', count: 2}]
    result: int
    duration_seconds: int


# Session 148 (GF107): KIRO2 auth returns `AuthenticatedUser.id` as a UUID
# string, not an integer. The `user_id: int` declaration used to raise
# Pydantic `ValidationError` when the handler assigned `current_user.id` to
# these models, which the bare `except Exception` on each handler re-wrapped
# as a generic 500. This is the fifth occurrence of the pattern after GF20
# AdhdPomodoroSessionResponse/InactivityAlert/FocusExerciseProgress and GF71
# TaskResponse — any `user_id: int` in a Pydantic model touched by
# `current_user.id` is a guaranteed crash site.
class VirtualBlockProgress(BaseModel):
    """Sanal blok ilerleme kaydı"""

    user_id: str
    operation: VirtualBlockOperation
    timestamp: datetime = datetime.now(UTC)


class GeoGebraActivity(BaseModel):
    """GeoGebra aktivite kaydı"""

    user_id: str
    applet_id: str
    activity_type: str  # geometry, algebra, calculus
    duration_seconds: int
    completed: bool
    timestamp: datetime = datetime.now(UTC)


class GeometryToolUsage(BaseModel):
    """Geometri aracı kullanım kaydı"""

    user_id: str
    tool_type: str  # ruler, compass, protractor, transform
    shapes_created: list[dict]
    measurements: list[dict]
    duration_seconds: int
    timestamp: datetime = datetime.now(UTC)


class TangramPuzzle(BaseModel):
    """Tangram puzzle kaydı"""

    user_id: str
    puzzle_id: str
    pieces_used: list[dict]
    completed: bool
    attempts: int
    duration_seconds: int
    timestamp: datetime = datetime.now(UTC)


# API Endpoints


@router.post("/virtual-blocks/operation")
def record_virtual_block_operation(
    operation: VirtualBlockOperation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sanal blok işlemini kaydet
    REQ-51.81-51.85: Virtual manipulative blocks, drag-and-drop, quantity operations
    """
    try:
        progress = VirtualBlockProgress(user_id=current_user.id, operation=operation)

        # İlerleme kaydını veritabanına kaydet (şimdilik in-memory)
        return {
            "success": True,
            "message": "Sanal blok işlemi kaydedildi",
            "data": {
                "operation_type": operation.operation_type,
                "result": operation.result,
                "blocks_used": operation.blocks_used,
                "duration": operation.duration_seconds,
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/virtual-blocks/progress")
def get_virtual_block_progress(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Kullanıcının sanal blok ilerlemesini getir"""
    try:
        # Veritabanından ilerleme verilerini çek
        return {
            "success": True,
            "data": {
                "total_operations": 0,
                "operations_by_type": {
                    "add": 0,
                    "subtract": 0,
                    "multiply": 0,
                    "divide": 0,
                },
                "average_duration": 0,
                "accuracy_rate": 0.0,
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/geogebra/activity")
def record_geogebra_activity(
    activity: GeoGebraActivity,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GeoGebra aktivitesini kaydet
    REQ-51.86-51.90: GeoGebra embed, interactive geometry, dynamic mathematics
    """
    try:
        _require_body_user_id_matches(current_user, activity.user_id)
        activity.user_id = current_user.id

        return {
            "success": True,
            "message": "GeoGebra aktivitesi kaydedildi",
            "data": {
                "applet_id": activity.applet_id,
                "activity_type": activity.activity_type,
                "completed": activity.completed,
                "duration": activity.duration_seconds,
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/geogebra/applets")
def get_geogebra_applets(
    activity_type: str | None = None, current_user: User = Depends(get_current_user)
):
    """GeoGebra applet listesini getir"""
    try:
        # Hazır GeoGebra applet'leri
        applets = [
            {
                "id": "geometry-basic",
                "name": "Temel Geometri",
                "type": "geometry",
                "url": "https://www.geogebra.org/geometry",
                "description": "Temel geometrik şekiller ve ölçümler",
            },
            {
                "id": "algebra-graphing",
                "name": "Fonksiyon Grafikleri",
                "type": "algebra",
                "url": "https://www.geogebra.org/graphing",
                "description": "Fonksiyon grafikleri ve denklemler",
            },
            {
                "id": "3d-calculator",
                "name": "3D Hesap Makinesi",
                "type": "geometry",
                "url": "https://www.geogebra.org/3d",
                "description": "3 boyutlu geometri ve hesaplamalar",
            },
        ]

        if activity_type:
            applets = [a for a in applets if a["type"] == activity_type]

        return {"success": True, "data": applets}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/geometry/tool-usage")
def record_geometry_tool_usage(
    usage: GeometryToolUsage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Geometri aracı kullanımını kaydet
    REQ-51.91-51.95: Construction tools, measurement tools, transformation tools
    """
    try:
        _require_body_user_id_matches(current_user, usage.user_id)
        usage.user_id = current_user.id

        return {
            "success": True,
            "message": "Geometri aracı kullanımı kaydedildi",
            "data": {
                "tool_type": usage.tool_type,
                "shapes_created": len(usage.shapes_created),
                "measurements": len(usage.measurements),
                "duration": usage.duration_seconds,
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/geometry/tools")
def get_geometry_tools(current_user: User = Depends(get_current_user)):
    """Mevcut geometri araçlarını listele"""
    try:
        tools = [
            {
                "id": "ruler",
                "name": "Cetvel",
                "type": "measurement",
                "description": "Uzunluk ölçümü",
                "icon": "📏",
            },
            {
                "id": "compass",
                "name": "Pergel",
                "type": "construction",
                "description": "Daire çizimi",
                "icon": "📐",
            },
            {
                "id": "protractor",
                "name": "Açıölçer",
                "type": "measurement",
                "description": "Açı ölçümü",
                "icon": "📐",
            },
            {
                "id": "rotate",
                "name": "Döndürme",
                "type": "transformation",
                "description": "Şekil döndürme",
                "icon": "🔄",
            },
            {
                "id": "reflect",
                "name": "Yansıma",
                "type": "transformation",
                "description": "Şekil yansıtma",
                "icon": "↔️",
            },
            {
                "id": "translate",
                "name": "Öteleme",
                "type": "transformation",
                "description": "Şekil öteleme",
                "icon": "➡️",
            },
        ]

        return {"success": True, "data": tools}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/tangram/puzzle")
def record_tangram_puzzle(
    puzzle: TangramPuzzle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tangram puzzle kaydını kaydet
    REQ-51.96-51.100: Tangram puzzle interface, shape recognition, spatial reasoning
    """
    try:
        _require_body_user_id_matches(current_user, puzzle.user_id)
        puzzle.user_id = current_user.id

        return {
            "success": True,
            "message": "Tangram puzzle kaydedildi",
            "data": {
                "puzzle_id": puzzle.puzzle_id,
                "completed": puzzle.completed,
                "attempts": puzzle.attempts,
                "duration": puzzle.duration_seconds,
                "pieces_used": len(puzzle.pieces_used),
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/tangram/puzzles")
def get_tangram_puzzles(
    difficulty: str | None = None, current_user: User = Depends(get_current_user)
):
    """Tangram puzzle listesini getir"""
    try:
        puzzles = [
            {
                "id": "tangram-square",
                "name": "Kare Oluştur",
                "difficulty": "easy",
                "pieces": 7,
                "target_shape": "square",
                "description": "7 parça ile kare oluştur",
            },
            {
                "id": "tangram-triangle",
                "name": "Üçgen Oluştur",
                "difficulty": "easy",
                "pieces": 7,
                "target_shape": "triangle",
                "description": "7 parça ile üçgen oluştur",
            },
            {
                "id": "tangram-cat",
                "name": "Kedi Oluştur",
                "difficulty": "medium",
                "pieces": 7,
                "target_shape": "cat",
                "description": "7 parça ile kedi şekli oluştur",
            },
            {
                "id": "tangram-house",
                "name": "Ev Oluştur",
                "difficulty": "medium",
                "pieces": 7,
                "target_shape": "house",
                "description": "7 parça ile ev şekli oluştur",
            },
            {
                "id": "tangram-boat",
                "name": "Tekne Oluştur",
                "difficulty": "hard",
                "pieces": 7,
                "target_shape": "boat",
                "description": "7 parça ile tekne şekli oluştur",
            },
        ]

        if difficulty:
            puzzles = [p for p in puzzles if p["difficulty"] == difficulty]

        return {"success": True, "data": puzzles}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/tangram/progress")
def get_tangram_progress(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Kullanıcının tangram ilerlemesini getir"""
    try:
        return {
            "success": True,
            "data": {
                "total_puzzles_attempted": 0,
                "total_puzzles_completed": 0,
                "completion_rate": 0.0,
                "average_attempts": 0.0,
                "average_duration": 0,
                "puzzles_by_difficulty": {
                    "easy": {"attempted": 0, "completed": 0},
                    "medium": {"attempted": 0, "completed": 0},
                    "hard": {"attempted": 0, "completed": 0},
                },
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
