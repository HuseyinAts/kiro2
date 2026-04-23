"""
Visual Supports API - Görsel Destekler REST API
Task 81: Görsel Destekler (REQ-50.73 - REQ-50.88)

API Endpoints:
- Mind Maps (Kavram Haritaları)
- Infographics (İnfografikler)
- Visual Vocabulary (Resimli Sözlük)
- Color Coding (Renk Kodlama)
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.dependencies import get_current_user
from services.visual_supports_service import (
    ColorCodingScheme,
    Infographic,
    MindMap,
    VisualVocabularyCard,
    visual_supports_service,
)

router = APIRouter(prefix="/api/v1/visual-supports", tags=["Visual Supports"])


# ============================================================================
# Request/Response Models
# ============================================================================


class MindMapCreateRequest(BaseModel):
    """Kavram haritası oluşturma isteği"""

    title: str
    subject: str
    topic: str
    content: str


class MindMapNodeUpdateRequest(BaseModel):
    """Kavram haritası düğüm güncelleme isteği"""

    label: str | None = None
    description: str | None = None
    color: str | None = None
    x: float | None = None
    y: float | None = None


class InfographicCreateRequest(BaseModel):
    """İnfografik oluşturma isteği"""

    title: str
    subject: str
    topic: str
    template: str
    data: list[dict[str, Any]]


class VocabularyCardCreateRequest(BaseModel):
    """Kelime kartı oluşturma isteği"""

    word: str
    definition: str
    image_url: str
    category: str
    example_sentence: str | None = None
    synonyms: list[str] | None = None
    difficulty_level: int = 1


class ColorSchemeCreateRequest(BaseModel):
    """Renk şeması oluşturma isteği"""

    name: str
    description: str
    categories: dict[str, str]


class ColorMappingUpdateRequest(BaseModel):
    """Renk eşleştirme güncelleme isteği"""

    category: str
    new_color: str


# ============================================================================
# Mind Maps API (Kavram Haritaları) - REQ-50.73-76
# ============================================================================


@router.post("/mind-maps", response_model=MindMap)
async def create_mind_map(
    request: MindMapCreateRequest,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.73: Kavram haritası oluştur
    """
    try:
        mind_map = visual_supports_service.generate_mind_map(
            title=request.title,
            subject=request.subject,
            topic=request.topic,
            content=request.content,
            user_id=str(current_user.id),
        )
        return mind_map
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/mind-maps/{mind_map_id}", response_model=MindMap)
async def get_mind_map(
    mind_map_id: str,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.74: Kavram haritasını getir (interactive exploration)
    """
    mind_map = visual_supports_service.get_mind_map(mind_map_id)
    if not mind_map:
        raise HTTPException(status_code=404, detail="Mind map not found")
    return mind_map


@router.get("/mind-maps/{mind_map_id}/export")
async def export_mind_map(
    mind_map_id: str,
    format: str = Query("json", regex="^(json|svg|png)$"),
    current_user=Depends(get_current_user),
):
    """
    REQ-50.75: Kavram haritasını dışa aktar
    """
    result = visual_supports_service.export_mind_map(mind_map_id, format)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.patch("/mind-maps/{mind_map_id}/nodes/{node_id}")
async def update_mind_map_node(
    mind_map_id: str,
    node_id: str,
    request: MindMapNodeUpdateRequest,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.76: Kavram haritası düğümünü güncelle (drag-and-drop support)
    """
    updates = request.dict(exclude_unset=True)
    success = visual_supports_service.update_mind_map_node(
        mind_map_id, node_id, updates
    )
    if not success:
        raise HTTPException(status_code=404, detail="Mind map or node not found")
    return {"success": True, "message": "Node updated successfully"}


# ============================================================================
# Infographics API (İnfografikler) - REQ-50.77-80
# ============================================================================


@router.post("/infographics", response_model=Infographic)
async def create_infographic(
    request: InfographicCreateRequest,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.77: İnfografik oluştur (visual summary generation)
    """
    try:
        infographic = visual_supports_service.generate_infographic(
            title=request.title,
            subject=request.subject,
            topic=request.topic,
            template=request.template,
            data=request.data,
            user_id=str(current_user.id),
        )
        return infographic
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/infographics/templates")
async def get_infographic_templates(
    current_user=Depends(get_current_user),
):
    """
    REQ-50.79: İnfografik şablonlarını getir (customizable templates)
    """
    templates = visual_supports_service.get_infographic_templates()
    return {"templates": templates}


@router.get("/infographics/{infographic_id}/export")
async def export_infographic(
    infographic_id: str,
    format: str = Query("png", regex="^(json|svg|png|pdf)$"),
    current_user=Depends(get_current_user),
):
    """
    REQ-50.80: İnfografiği dışa aktar
    """
    result = visual_supports_service.export_infographic(infographic_id, format)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============================================================================
# Visual Vocabulary API (Resimli Sözlük) - REQ-50.81-84
# ============================================================================


@router.post("/vocabulary-cards", response_model=VisualVocabularyCard)
async def create_vocabulary_card(
    request: VocabularyCardCreateRequest,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.81: Görsel kelime kartı oluştur (image-word associations)
    """
    try:
        card = visual_supports_service.create_vocabulary_card(
            word=request.word,
            definition=request.definition,
            image_url=request.image_url,
            category=request.category,
            example_sentence=request.example_sentence,
            synonyms=request.synonyms,
            difficulty_level=request.difficulty_level,
        )
        return card
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/vocabulary-cards/search", response_model=list[VisualVocabularyCard])
async def search_vocabulary_cards(
    query: str = Query(..., min_length=1),
    category: str | None = None,
    difficulty_level: int | None = Query(None, ge=1, le=5),
    current_user=Depends(get_current_user),
):
    """
    REQ-50.83: Resimli sözlükte arama yap (searchable image database)
    """
    cards = visual_supports_service.search_vocabulary_cards(
        query=query, category=category, difficulty_level=difficulty_level
    )
    return cards


@router.get("/vocabulary-cards/progress")
async def get_vocabulary_progress(
    current_user=Depends(get_current_user),
):
    """
    REQ-50.82: Kelime öğrenme ilerlemesini getir (visual vocabulary builder)
    """
    progress = visual_supports_service.get_vocabulary_builder_progress(
        str(current_user.id)
    )
    return progress


# ============================================================================
# Color Coding API (Renk Kodlama) - REQ-50.85-88
# ============================================================================


@router.post("/color-schemes", response_model=ColorCodingScheme)
async def create_color_scheme(
    request: ColorSchemeCreateRequest,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.85: Renk kodlama şeması oluştur (color-coded categories)
    """
    try:
        scheme = visual_supports_service.create_color_scheme(
            name=request.name,
            description=request.description,
            categories=request.categories,
            user_id=str(current_user.id),
        )
        return scheme
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/color-schemes/{scheme_id}", response_model=ColorCodingScheme)
async def get_color_scheme(
    scheme_id: str,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.86: Renk şemasını getir (consistent color scheme)
    """
    scheme = visual_supports_service.get_color_scheme(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Color scheme not found")
    return scheme


@router.get("/color-schemes", response_model=list[ColorCodingScheme])
async def get_default_color_schemes(
    current_user=Depends(get_current_user),
):
    """
    REQ-50.86: Varsayılan renk şemalarını getir
    """
    schemes = visual_supports_service.get_default_color_schemes()
    return schemes


@router.patch("/color-schemes/{scheme_id}/mapping")
async def update_color_mapping(
    scheme_id: str,
    request: ColorMappingUpdateRequest,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.87: Renk eşleştirmesini özelleştir (customizable color mapping)
    """
    success = visual_supports_service.customize_color_mapping(
        scheme_id=scheme_id, category=request.category, new_color=request.new_color
    )
    if not success:
        raise HTTPException(status_code=404, detail="Color scheme not found")
    return {"success": True, "message": "Color mapping updated successfully"}


@router.post("/color-schemes/{scheme_id}/save-preferences")
async def save_color_preferences(
    scheme_id: str,
    current_user=Depends(get_current_user),
):
    """
    REQ-50.88: Kullanıcı renk tercihlerini kaydet
    """
    result = visual_supports_service.save_user_color_preferences(
        str(current_user.id), scheme_id
    )
    if not result["success"]:
        raise HTTPException(
            status_code=404, detail=result.get("error", "Unknown error")
        )
    return result


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def health_check():
    """Visual Supports API sağlık kontrolü"""
    return {
        "status": "healthy",
        "service": "Visual Supports API",
        "version": "1.0.0",
        "features": [
            "Mind Maps (Kavram Haritaları)",
            "Infographics (İnfografikler)",
            "Visual Vocabulary (Resimli Sözlük)",
            "Color Coding (Renk Kodlama)",
        ],
    }
