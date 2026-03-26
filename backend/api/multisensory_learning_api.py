"""
Multisensory Learning API - Çoklu Duyusal Öğrenme REST API
Task 82: Çoklu Duyusal Öğrenme (REQ-50.89 - REQ-50.104)
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.dependencies import AuthenticatedUser, get_current_user
from services.multisensory_learning_service import (
    AnimationType,
    EducationalVideo,
    InteractiveAnimation,
    LearningModality,
    MultimodalContent,
    VRARContent,
    multisensory_learning_service,
)

router = APIRouter(prefix="/api/v1/multisensory", tags=["Multisensory Learning"])


# Request Models
class MultimodalContentRequest(BaseModel):
    title: str
    subject: str
    topic: str
    modalities: list[LearningModality]
    visual_content: dict[str, Any] | None = None
    audio_content: dict[str, Any] | None = None
    kinesthetic_content: dict[str, Any] | None = None
    interactive_elements: list[dict[str, Any]] | None = None


class AnimationRequest(BaseModel):
    title: str
    animation_type: AnimationType
    steps: list[dict[str, Any]]
    duration_ms: int = 5000


class VideoRequest(BaseModel):
    title: str
    description: str
    url: str
    duration_seconds: int
    subject: str
    topic: str
    subtitles: list[dict[str, Any]] | None = None
    thumbnail_url: str | None = None


class VRContentRequest(BaseModel):
    title: str
    description: str
    scene_url: str
    models_3d: list[dict[str, Any]]
    interactions: list[str]


class ARContentRequest(BaseModel):
    title: str
    description: str
    overlay_data: dict[str, Any]
    models_3d: list[dict[str, Any]]


# Multimodal Content Endpoints (REQ-50.89-92)
@router.post("/multimodal", response_model=MultimodalContent)
async def create_multimodal_content(
    request: MultimodalContentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.89: Çoklu modal içerik oluştur"""
    try:
        content = multisensory_learning_service.create_multimodal_content(
            title=request.title,
            subject=request.subject,
            topic=request.topic,
            modalities=request.modalities,
            visual_content=request.visual_content,
            audio_content=request.audio_content,
            kinesthetic_content=request.kinesthetic_content,
            interactive_elements=request.interactive_elements,
        )
        return content
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/multimodal/{content_id}/synchronize")
async def synchronize_media(
    content_id: str,
    sync_points: list[dict[str, Any]],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.90: Medya senkronizasyonu"""
    success = multisensory_learning_service.synchronize_media(content_id, sync_points)
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"success": True, "message": "Media synchronized"}


@router.post("/multimodal/{content_id}/interactive-element")
async def add_interactive_element(
    content_id: str,
    element_type: str,
    element_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.91: İnteraktif element ekle"""
    success = multisensory_learning_service.add_interactive_element(
        content_id, element_type, element_data
    )
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"success": True, "message": "Interactive element added"}


@router.post("/preferences")
async def save_preferences(
    preferred_modalities: list[LearningModality],
    settings: dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.92: Kullanıcı tercihlerini kaydet"""
    result = multisensory_learning_service.save_user_preferences(
        current_user.id, preferred_modalities, settings
    )
    return result


# Animation Endpoints (REQ-50.93-96)
@router.post("/animations", response_model=InteractiveAnimation)
async def create_animation(
    request: AnimationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.93: İnteraktif animasyon oluştur"""
    try:
        animation = multisensory_learning_service.create_animation(
            title=request.title,
            animation_type=request.animation_type,
            steps=request.steps,
            duration_ms=request.duration_ms,
        )
        return animation
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/animations/{animation_id}/steps")
async def get_animation_steps(
    animation_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """REQ-50.94: Animasyon adımlarını getir"""
    steps = multisensory_learning_service.get_animation_steps(animation_id)
    if not steps:
        raise HTTPException(status_code=404, detail="Animation not found")
    return {"steps": steps}


@router.post("/animations/{animation_id}/control")
async def control_animation(
    animation_id: str,
    action: str,
    value: Any | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.95: Animasyon kontrolü (pause/replay)"""
    result = multisensory_learning_service.control_animation(
        animation_id, action, value
    )
    if not result["success"]:
        raise HTTPException(
            status_code=400, detail=result.get("error", "Control failed")
        )
    return result


@router.patch("/animations/{animation_id}/speed")
async def set_animation_speed(
    animation_id: str,
    speed: float = Query(..., ge=0.5, le=2.0),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.96: Animasyon hızını ayarla"""
    success = multisensory_learning_service.set_playback_speed(animation_id, speed)
    if not success:
        raise HTTPException(status_code=404, detail="Animation not found")
    return {"success": True, "speed": speed}


# Video Endpoints (REQ-50.97-100)
@router.post("/videos", response_model=EducationalVideo)
async def add_video(
    request: VideoRequest, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """REQ-50.97: Eğitim videosu ekle"""
    try:
        video = multisensory_learning_service.add_video(
            title=request.title,
            description=request.description,
            url=request.url,
            duration_seconds=request.duration_seconds,
            subject=request.subject,
            topic=request.topic,
            subtitles=request.subtitles,
            thumbnail_url=request.thumbnail_url,
        )
        return video
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/videos/{video_id}/subtitles")
async def add_subtitles(
    video_id: str,
    language: str,
    subtitle_data: list[dict[str, Any]],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.98: Video altyazı ekle"""
    success = multisensory_learning_service.add_subtitles(
        video_id, language, subtitle_data
    )
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"success": True, "message": "Subtitles added"}


@router.patch("/videos/{video_id}/speed")
async def set_video_speed(
    video_id: str,
    speed: float = Query(..., ge=0.5, le=2.0),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.99: Video hızını ayarla"""
    success = multisensory_learning_service.set_video_playback_speed(video_id, speed)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"success": True, "speed": speed}


@router.get("/videos/{video_id}/wcag-compliance")
async def check_wcag_compliance(
    video_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """REQ-50.100: WCAG uyumluluğunu kontrol et"""
    result = multisensory_learning_service.ensure_wcag_compliance(video_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# VR/AR Endpoints (REQ-50.101-104)
@router.post("/vr", response_model=VRARContent)
async def create_vr_content(
    request: VRContentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.101: VR içerik oluştur"""
    try:
        content = multisensory_learning_service.create_vr_content(
            title=request.title,
            description=request.description,
            scene_url=request.scene_url,
            models_3d=request.models_3d,
            interactions=request.interactions,
        )
        return content
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/ar", response_model=VRARContent)
async def create_ar_overlay(
    request: ARContentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.102: AR overlay oluştur"""
    try:
        content = multisensory_learning_service.create_ar_overlay(
            title=request.title,
            description=request.description,
            overlay_data=request.overlay_data,
            models_3d=request.models_3d,
        )
        return content
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/vr-ar/{content_id}/interaction")
async def enable_3d_interaction(
    content_id: str,
    interaction_type: str,
    settings: dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.103: 3D model interaksiyonu etkinleştir"""
    success = multisensory_learning_service.enable_3d_interaction(
        content_id, interaction_type, settings
    )
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"success": True, "message": "3D interaction enabled"}


@router.post("/vr-ar/{content_id}/save-experience")
async def save_immersive_experience(
    content_id: str,
    experience_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """REQ-50.104: Immersive learning experience kaydet"""
    result = multisensory_learning_service.save_immersive_experience(
        content_id, current_user.id, experience_data
    )
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Save failed"))
    return result


@router.get("/health")
async def health_check():
    """Multisensory Learning API sağlık kontrolü"""
    return {
        "status": "healthy",
        "service": "Multisensory Learning API",
        "version": "1.0.0",
        "features": [
            "Multimodal Content (Görsel+İşitsel+Kinestetik)",
            "Interactive Animations",
            "Educational Videos",
            "VR/AR Support",
        ],
    }
