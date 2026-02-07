"""
Task 93: OSB Settings API
OSB (Otizm Spektrum Bozukluğu) kullanıcı ayarları API endpoints
"""
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models.database import User
from models.osb_settings import OSBSettings
from core.structured_logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/osb/settings", tags=["OSB Support - Settings"])


# Request/Response Models
class OSBSettingsRequest(BaseModel):
    """OSB ayarları güncelleme request"""

    osb_mode_enabled: bool = True

    # Layout settings
    consistent_layout_enabled: bool = True
    layout_type: str = Field(default="default", pattern="^(default|centered|wide)$")
    predictable_elements: bool = True

    # Navigation settings
    fixed_navigation_enabled: bool = True
    navigation_position: str = Field(default="top", pattern="^(top|left|bottom)$")
    navigation_variant: str = Field(
        default="horizontal", pattern="^(horizontal|vertical)$"
    )

    # Color settings
    consistent_colors_enabled: bool = True
    theme_changes_disabled: bool = True
    high_contrast_mode: bool = False

    # Icon settings
    standard_icons_enabled: bool = True
    show_icon_labels: bool = True
    icon_size: str = Field(default="24", pattern="^(16|20|24|32|40|48)$")

    # Accessibility
    reduced_motion: bool = True
    no_animations: bool = False
    no_shadows: bool = True


class OSBSettingsResponse(BaseModel):
    """OSB ayarları response"""

    id: str
    user_id: str
    osb_mode_enabled: bool

    # Layout
    consistent_layout_enabled: bool
    layout_type: str
    predictable_elements: bool

    # Navigation
    fixed_navigation_enabled: bool
    navigation_position: str
    navigation_variant: str

    # Colors
    consistent_colors_enabled: bool
    theme_changes_disabled: bool
    high_contrast_mode: bool

    # Icons
    standard_icons_enabled: bool
    show_icon_labels: bool
    icon_size: str

    # Accessibility
    reduced_motion: bool
    no_animations: bool
    no_shadows: bool

    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


# Endpoints


@router.get("/", response_model=OSBSettingsResponse)
async def get_osb_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Kullanıcının OSB ayarlarını getir
    Yoksa varsayılan ayarlar ile oluştur
    """
    try:
        settings = (
            db.query(OSBSettings).filter(OSBSettings.user_id == current_user.id).first()
        )

        if not settings:
            # Varsayılan ayarlarla oluştur
            settings = OSBSettings(
                user_id=current_user.id,
                osb_mode_enabled=True,
                consistent_layout_enabled=True,
                layout_type="default",
                predictable_elements=True,
                fixed_navigation_enabled=True,
                navigation_position="top",
                navigation_variant="horizontal",
                consistent_colors_enabled=True,
                theme_changes_disabled=True,
                high_contrast_mode=False,
                standard_icons_enabled=True,
                show_icon_labels=True,
                icon_size="24",
                reduced_motion=True,
                no_animations=False,
                no_shadows=True,
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

            logger.info(f"OSB settings created for user {current_user.id}")

        return OSBSettingsResponse(
            id=str(settings.id),
            user_id=settings.user_id,
            osb_mode_enabled=settings.osb_mode_enabled,
            consistent_layout_enabled=settings.consistent_layout_enabled,
            layout_type=settings.layout_type,
            predictable_elements=settings.predictable_elements,
            fixed_navigation_enabled=settings.fixed_navigation_enabled,
            navigation_position=settings.navigation_position,
            navigation_variant=settings.navigation_variant,
            consistent_colors_enabled=settings.consistent_colors_enabled,
            theme_changes_disabled=settings.theme_changes_disabled,
            high_contrast_mode=settings.high_contrast_mode,
            standard_icons_enabled=settings.standard_icons_enabled,
            show_icon_labels=settings.show_icon_labels,
            icon_size=settings.icon_size,
            reduced_motion=settings.reduced_motion,
            no_animations=settings.no_animations,
            no_shadows=settings.no_shadows,
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error getting OSB settings: {e}")
        raise HTTPException(status_code=500, detail="OSB ayarları alınamadı")


@router.put("/", response_model=OSBSettingsResponse)
async def update_osb_settings(
    request: OSBSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    OSB ayarlarını güncelle
    """
    try:
        settings = (
            db.query(OSBSettings).filter(OSBSettings.user_id == current_user.id).first()
        )

        if not settings:
            # Yoksa oluştur
            settings = OSBSettings(user_id=current_user.id)
            db.add(settings)

        # Update all fields
        settings.osb_mode_enabled = request.osb_mode_enabled
        settings.consistent_layout_enabled = request.consistent_layout_enabled
        settings.layout_type = request.layout_type
        settings.predictable_elements = request.predictable_elements
        settings.fixed_navigation_enabled = request.fixed_navigation_enabled
        settings.navigation_position = request.navigation_position
        settings.navigation_variant = request.navigation_variant
        settings.consistent_colors_enabled = request.consistent_colors_enabled
        settings.theme_changes_disabled = request.theme_changes_disabled
        settings.high_contrast_mode = request.high_contrast_mode
        settings.standard_icons_enabled = request.standard_icons_enabled
        settings.show_icon_labels = request.show_icon_labels
        settings.icon_size = request.icon_size
        settings.reduced_motion = request.reduced_motion
        settings.no_animations = request.no_animations
        settings.no_shadows = request.no_shadows

        db.commit()
        db.refresh(settings)

        logger.info(f"OSB settings updated for user {current_user.id}")

        return OSBSettingsResponse(
            id=str(settings.id),
            user_id=settings.user_id,
            osb_mode_enabled=settings.osb_mode_enabled,
            consistent_layout_enabled=settings.consistent_layout_enabled,
            layout_type=settings.layout_type,
            predictable_elements=settings.predictable_elements,
            fixed_navigation_enabled=settings.fixed_navigation_enabled,
            navigation_position=settings.navigation_position,
            navigation_variant=settings.navigation_variant,
            consistent_colors_enabled=settings.consistent_colors_enabled,
            theme_changes_disabled=settings.theme_changes_disabled,
            high_contrast_mode=settings.high_contrast_mode,
            standard_icons_enabled=settings.standard_icons_enabled,
            show_icon_labels=settings.show_icon_labels,
            icon_size=settings.icon_size,
            reduced_motion=settings.reduced_motion,
            no_animations=settings.no_animations,
            no_shadows=settings.no_shadows,
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error updating OSB settings: {e}")
        raise HTTPException(status_code=500, detail="OSB ayarları güncellenemedi")


@router.post("/reset", response_model=Dict)
async def reset_osb_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    OSB ayarlarını varsayılana sıfırla
    """
    try:
        settings = (
            db.query(OSBSettings).filter(OSBSettings.user_id == current_user.id).first()
        )

        if not settings:
            settings = OSBSettings(user_id=current_user.id)
            db.add(settings)
        else:
            # Reset to defaults
            settings.osb_mode_enabled = True
            settings.consistent_layout_enabled = True
            settings.layout_type = "default"
            settings.predictable_elements = True
            settings.fixed_navigation_enabled = True
            settings.navigation_position = "top"
            settings.navigation_variant = "horizontal"
            settings.consistent_colors_enabled = True
            settings.theme_changes_disabled = True
            settings.high_contrast_mode = False
            settings.standard_icons_enabled = True
            settings.show_icon_labels = True
            settings.icon_size = "24"
            settings.reduced_motion = True
            settings.no_animations = False
            settings.no_shadows = True

        db.commit()

        logger.info(f"OSB settings reset for user {current_user.id}")

        return {"success": True, "message": "OSB ayarları varsayılana sıfırlandı"}

    except Exception as e:
        logger.error(f"Error resetting OSB settings: {e}")
        raise HTTPException(status_code=500, detail="OSB ayarları sıfırlanamadı")


@router.get("/presets", response_model=Dict)
async def get_osb_presets():
    """
    Hazır OSB ayar profilleri getir
    """
    return {
        "presets": [
            {
                "id": "full_osb",
                "name": "Tam OSB Desteği",
                "description": "Tüm OSB özellikleri aktif",
                "settings": {
                    "osb_mode_enabled": True,
                    "consistent_layout_enabled": True,
                    "layout_type": "default",
                    "predictable_elements": True,
                    "fixed_navigation_enabled": True,
                    "navigation_position": "top",
                    "navigation_variant": "horizontal",
                    "consistent_colors_enabled": True,
                    "theme_changes_disabled": True,
                    "high_contrast_mode": False,
                    "standard_icons_enabled": True,
                    "show_icon_labels": True,
                    "icon_size": "32",
                    "reduced_motion": True,
                    "no_animations": True,
                    "no_shadows": True,
                },
            },
            {
                "id": "high_contrast_osb",
                "name": "Yüksek Kontrast OSB",
                "description": "OSB + yüksek kontrast görsel",
                "settings": {
                    "osb_mode_enabled": True,
                    "consistent_layout_enabled": True,
                    "layout_type": "default",
                    "predictable_elements": True,
                    "fixed_navigation_enabled": True,
                    "navigation_position": "top",
                    "navigation_variant": "horizontal",
                    "consistent_colors_enabled": True,
                    "theme_changes_disabled": True,
                    "high_contrast_mode": True,
                    "standard_icons_enabled": True,
                    "show_icon_labels": True,
                    "icon_size": "40",
                    "reduced_motion": True,
                    "no_animations": True,
                    "no_shadows": True,
                },
            },
            {
                "id": "minimal_osb",
                "name": "Minimal OSB",
                "description": "Temel OSB özellikleri",
                "settings": {
                    "osb_mode_enabled": True,
                    "consistent_layout_enabled": True,
                    "layout_type": "centered",
                    "predictable_elements": True,
                    "fixed_navigation_enabled": True,
                    "navigation_position": "top",
                    "navigation_variant": "horizontal",
                    "consistent_colors_enabled": True,
                    "theme_changes_disabled": True,
                    "high_contrast_mode": False,
                    "standard_icons_enabled": True,
                    "show_icon_labels": False,
                    "icon_size": "24",
                    "reduced_motion": True,
                    "no_animations": False,
                    "no_shadows": False,
                },
            },
        ]
    }


@router.post("/apply-preset/{preset_id}", response_model=OSBSettingsResponse)
async def apply_osb_preset(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hazır OSB profilini uygula
    """
    # Get presets
    presets_data = await get_osb_presets()
    presets = presets_data["presets"]

    # Find preset
    preset = next((p for p in presets if p["id"] == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail="Profil bulunamadı")

    # Apply preset
    preset_settings = OSBSettingsRequest(**preset["settings"])
    return await update_osb_settings(preset_settings, current_user, db)
