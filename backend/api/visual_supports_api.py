"""
Visual Supports API - Görsel Destekler REST API
Task 81: Görsel Destekler (REQ-50.73 - REQ-50.88)

API Endpoints:
- Mind Maps (Kavram Haritaları)
- Infographics (İnfografikler)
- Visual Vocabulary (Resimli Sözlük)
- Color Coding (Renk Kodlama)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from services.visual_supports_service import (
    visual_supports_service,
    MindMap,
    Infographic,
    VisualVocabularyCard,
    ColorCodingScheme,
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
    user_id: Optional[str] = None


class MindMapNodeUpdateRequest(BaseModel):
    """Kavram haritası düğüm güncelleme isteği"""

    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None


class InfographicCreateRequest(BaseModel):
    """İnfografik oluşturma isteği"""

    title: str
    subject: str
    topic: str
    template: str
    data: List[Dict[str, Any]]
    user_id: Optional[str] = None


class VocabularyCardCreateRequest(BaseModel):
    """Kelime kartı oluşturma isteği"""

    word: str
    definition: str
    image_url: str
    category: str
    example_sentence: Optional[str] = None
    synonyms: Optional[List[str]] = None
    difficulty_level: int = 1


class ColorSchemeCreateRequest(BaseModel):
    """Renk şeması oluşturma isteği"""

    name: str
    description: str
    categories: Dict[str, str]
    user_id: Optional[str] = None


class ColorMappingUpdateRequest(BaseModel):
    """Renk eşleştirme güncelleme isteği"""

    category: str
    new_color: str


# ============================================================================
# Mind Maps API (Kavram Haritaları) - REQ-50.73-76
# ============================================================================


@router.post("/mind-maps", response_model=MindMap)
async def create_mind_map(request: MindMapCreateRequest):
    """
    REQ-50.73: Kavram haritası oluştur

    Mind map generation algoritması ile içerikten otomatik kavram haritası oluşturur.
    """
    try:
        mind_map = visual_supports_service.generate_mind_map(
            title=request.title,
            subject=request.subject,
            topic=request.topic,
            content=request.content,
            user_id=request.user_id,
        )
        return mind_map
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Mind map creation failed: {str(e)}"
        )


@router.get("/mind-maps/{mind_map_id}", response_model=MindMap)
async def get_mind_map(mind_map_id: str):
    """
    REQ-50.74: Kavram haritasını getir (interactive exploration)

    Kavram haritasını tüm düğümleri ve ilişkileri ile birlikte getirir.
    Frontend'de interaktif olarak keşfedilebilir.
    """
    mind_map = visual_supports_service.get_mind_map(mind_map_id)
    if not mind_map:
        raise HTTPException(status_code=404, detail="Mind map not found")
    return mind_map


@router.get("/mind-maps/{mind_map_id}/export")
async def export_mind_map(
    mind_map_id: str, format: str = Query("json", regex="^(json|svg|png)$")
):
    """
    REQ-50.75: Kavram haritasını dışa aktar

    Desteklenen formatlar: json, svg, png
    """
    result = visual_supports_service.export_mind_map(mind_map_id, format)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.patch("/mind-maps/{mind_map_id}/nodes/{node_id}")
async def update_mind_map_node(
    mind_map_id: str, node_id: str, request: MindMapNodeUpdateRequest
):
    """
    REQ-50.76: Kavram haritası düğümünü güncelle (drag-and-drop support)

    Düğüm pozisyonu, rengi, etiketi vb. güncellenebilir.
    Frontend'de drag-and-drop ile kullanılır.
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
async def create_infographic(request: InfographicCreateRequest):
    """
    REQ-50.77: İnfografik oluştur (visual summary generation)

    Verilen veri ve şablona göre otomatik infografik oluşturur.
    """
    try:
        infographic = visual_supports_service.generate_infographic(
            title=request.title,
            subject=request.subject,
            topic=request.topic,
            template=request.template,
            data=request.data,
            user_id=request.user_id,
        )
        return infographic
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Infographic creation failed: {str(e)}"
        )


@router.get("/infographics/templates")
async def get_infographic_templates():
    """
    REQ-50.79: İnfografik şablonlarını getir (customizable templates)

    Mevcut tüm infografik şablonlarını listeler.
    """
    templates = visual_supports_service.get_infographic_templates()
    return {"templates": templates}


@router.get("/infographics/{infographic_id}/export")
async def export_infographic(
    infographic_id: str, format: str = Query("png", regex="^(json|svg|png|pdf)$")
):
    """
    REQ-50.80: İnfografiği dışa aktar (farklı format seçenekleri)

    Desteklenen formatlar: json, svg, png, pdf
    """
    result = visual_supports_service.export_infographic(infographic_id, format)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============================================================================
# Visual Vocabulary API (Resimli Sözlük) - REQ-50.81-84
# ============================================================================


@router.post("/vocabulary-cards", response_model=VisualVocabularyCard)
async def create_vocabulary_card(request: VocabularyCardCreateRequest):
    """
    REQ-50.81: Görsel kelime kartı oluştur (image-word associations)

    Kelime, tanım, görsel ve kategori ile kelime kartı oluşturur.
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Card creation failed: {str(e)}")


@router.get("/vocabulary-cards/search", response_model=List[VisualVocabularyCard])
async def search_vocabulary_cards(
    query: str = Query(..., min_length=1),
    category: Optional[str] = None,
    difficulty_level: Optional[int] = Query(None, ge=1, le=5),
):
    """
    REQ-50.83: Resimli sözlükte arama yap (searchable image database)

    Kelime veya tanımda arama yapar, kategori ve zorluk seviyesine göre filtreler.
    """
    cards = visual_supports_service.search_vocabulary_cards(
        query=query, category=category, difficulty_level=difficulty_level
    )
    return cards


@router.get("/vocabulary-cards/progress/{user_id}")
async def get_vocabulary_progress(user_id: str):
    """
    REQ-50.82: Kelime öğrenme ilerlemesini getir (visual vocabulary builder)

    Kullanıcının kelime öğrenme ilerlemesini ve istatistiklerini döner.
    """
    progress = visual_supports_service.get_vocabulary_builder_progress(user_id)
    return progress


# ============================================================================
# Color Coding API (Renk Kodlama) - REQ-50.85-88
# ============================================================================


@router.post("/color-schemes", response_model=ColorCodingScheme)
async def create_color_scheme(request: ColorSchemeCreateRequest):
    """
    REQ-50.85: Renk kodlama şeması oluştur (color-coded categories)

    Özel renk şeması oluşturur.
    """
    try:
        scheme = visual_supports_service.create_color_scheme(
            name=request.name,
            description=request.description,
            categories=request.categories,
            user_id=request.user_id,
        )
        return scheme
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Color scheme creation failed: {str(e)}"
        )


@router.get("/color-schemes/{scheme_id}", response_model=ColorCodingScheme)
async def get_color_scheme(scheme_id: str):
    """
    REQ-50.86: Renk şemasını getir (consistent color scheme)

    Belirtilen renk şemasını getirir.
    """
    scheme = visual_supports_service.get_color_scheme(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Color scheme not found")
    return scheme


@router.get("/color-schemes", response_model=List[ColorCodingScheme])
async def get_default_color_schemes():
    """
    REQ-50.86: Varsayılan renk şemalarını getir

    Tüm varsayılan renk şemalarını listeler.
    """
    schemes = visual_supports_service.get_default_color_schemes()
    return schemes


@router.patch("/color-schemes/{scheme_id}/mapping")
async def update_color_mapping(scheme_id: str, request: ColorMappingUpdateRequest):
    """
    REQ-50.87: Renk eşleştirmesini özelleştir (customizable color mapping)

    Belirli bir kategorinin rengini günceller.
    """
    success = visual_supports_service.customize_color_mapping(
        scheme_id=scheme_id, category=request.category, new_color=request.new_color
    )
    if not success:
        raise HTTPException(status_code=404, detail="Color scheme not found")
    return {"success": True, "message": "Color mapping updated successfully"}


@router.post("/color-schemes/{scheme_id}/save-preferences")
async def save_color_preferences(scheme_id: str, user_id: str = Query(...)):
    """
    REQ-50.88: Kullanıcı renk tercihlerini kaydet

    Kullanıcının seçtiği renk şemasını kaydeder.
    """
    result = visual_supports_service.save_user_color_preferences(user_id, scheme_id)
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
