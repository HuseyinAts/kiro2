"""
KIRO2 Vision API - Qwen3-VL Integration
========================================

Qwen3-VL:8b model ile gorsel analiz API'si.
Egitim iceriklerini gorselden analiz eder.

Endpoints:
- POST /api/vision/analyze - Genel gorsel analiz
- POST /api/vision/solve-question - Soru cozumu (matematik, fizik, vb.)
- POST /api/vision/extract-text - Gorselden metin cikarma (OCR)
- POST /api/vision/describe-diagram - Diyagram aciklama
- GET /api/vision/health - Saglik kontrolu
"""

import base64
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, get_current_user

try:
    from core.llm_service import llm_service
except (ImportError, TypeError):
    llm_service = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/vision", tags=["Vision AI"])


# ============================================================
# Pydantic Models
# ============================================================


class VisionAnalyzeRequest(BaseModel):
    """Gorsel analiz istegi"""

    image: str = Field(..., description="Base64 encoded gorsel")
    prompt: str = Field(
        default="Bu gorseli detayli olarak analiz et.", description="Analiz icin prompt"
    )
    language: str = Field(default="tr", description="Yanit dili (tr/en)")


class VisionSolveRequest(BaseModel):
    """Soru cozum istegi"""

    image: str = Field(..., description="Base64 encoded soru gorseli")
    subject: str = Field(
        default="matematik",
        description="Ders (matematik, fizik, kimya, biyoloji, turkce, vb.)",
    )
    level: str = Field(default="TYT", description="Seviye (TYT, AYT, LGS)")
    show_steps: bool = Field(default=True, description="Adim adim cozum goster")


class VisionExtractRequest(BaseModel):
    """Metin cikarma istegi"""

    image: str = Field(..., description="Base64 encoded gorsel")
    include_layout: bool = Field(
        default=False, description="Sayfa duzenini koruyarak cikar"
    )


class VisionDiagramRequest(BaseModel):
    """Diyagram aciklama istegi"""

    image: str = Field(..., description="Base64 encoded diyagram gorseli")
    subject: str = Field(
        default="genel",
        description="Konu alani (matematik, fizik, kimya, biyoloji, cografya)",
    )
    detail_level: str = Field(
        default="detailed",
        description="Detay seviyesi (brief, detailed, comprehensive)",
    )


class VisionResponse(BaseModel):
    """Gorsel analiz yaniti"""

    success: bool
    result: str
    model: str
    processing_time_ms: float
    metadata: dict = {}


class VisionHealthResponse(BaseModel):
    """Saglik kontrolu yaniti"""

    status: str
    model: str
    available: bool
    latency_ms: float | None = None


# ============================================================
# Helper Functions
# ============================================================


def clean_base64(b64_string: str) -> str:
    """Base64 string'i temizle (data URL prefix'ini kaldir)"""
    if "," in b64_string:
        return b64_string.split(",")[1]
    return b64_string


def validate_base64_image(b64_string: str) -> bool:
    """Base64 gorsel gecerliligini kontrol et"""
    try:
        cleaned = clean_base64(b64_string)
        decoded = base64.b64decode(cleaned)
        # PNG, JPEG, WebP magic bytes kontrolu
        if (
            decoded[:4] == b"\x89PNG"
            or decoded[:2] == b"\xff\xd8"
            or decoded[:4] == b"RIFF"
        ):
            return True
        return False
    except Exception:
        return False


async def analyze_with_vision(
    image_b64: str, prompt: str, **kwargs: Any
) -> tuple[str, float]:
    """Vision modeli ile gorsel analiz yap"""
    start_time = time.time()

    cleaned_b64 = clean_base64(image_b64)
    result = await llm_service.analyze_image(
        prompt=prompt, image_base64=cleaned_b64, **kwargs
    )

    elapsed_ms = (time.time() - start_time) * 1000
    return result, elapsed_ms


# ============================================================
# Endpoints
# ============================================================


@router.post("/analyze", response_model=VisionResponse)
async def analyze_image(
    request: VisionAnalyzeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> VisionResponse:
    """
    Genel gorsel analizi

    Qwen3-VL modeli ile gorseli analiz eder ve detayli aciklama uretir.

    - **image**: Base64 encoded gorsel (PNG, JPEG, WebP)
    - **prompt**: Analiz icin ozel prompt
    - **language**: Yanit dili (tr/en)
    """
    if not validate_base64_image(request.image):
        raise HTTPException(400, "Gecersiz gorsel formati. PNG, JPEG veya WebP olmali.")

    try:
        # Dil ayari
        lang_prompt = ""
        if request.language == "tr":
            lang_prompt = "Turkce yanit ver. "
        elif request.language == "en":
            lang_prompt = "Respond in English. "

        full_prompt = f"{lang_prompt}{request.prompt}"

        result, elapsed_ms = await analyze_with_vision(request.image, full_prompt)

        return VisionResponse(
            success=True,
            result=result,
            model=llm_service.vision_model,
            processing_time_ms=round(elapsed_ms, 2),
            metadata={"language": request.language},
        )

    except Exception as e:
        logger.error(f"Vision analyze error: {e}")
        raise HTTPException(500, "Gorsel analizi basarisiz. Lutfen tekrar deneyin.")


@router.post("/solve-question", response_model=VisionResponse)
async def solve_question(
    request: VisionSolveRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> VisionResponse:
    """
    Soru cozumu

    Gorseldeki egitim sorusunu analiz eder ve adim adim cozer.
    YKS/TYT/AYT/LGS sinav formatina uygundur.

    - **image**: Base64 encoded soru gorseli
    - **subject**: Ders (matematik, fizik, kimya, biyoloji, turkce)
    - **level**: Seviye (TYT, AYT, LGS)
    - **show_steps**: Adim adim cozum goster
    """
    if not validate_base64_image(request.image):
        raise HTTPException(400, "Gecersiz gorsel formati.")

    try:
        # Konu bazli prompt olustur
        subject_prompts = {
            "matematik": "Bu matematik sorusunu analiz et ve coz.",
            "fizik": "Bu fizik sorusunu analiz et, formulleri belirle ve coz.",
            "kimya": "Bu kimya sorusunu analiz et, reaksiyonlari yaz ve coz.",
            "biyoloji": "Bu biyoloji sorusunu analiz et ve coz.",
            "turkce": "Bu Turkce sorusunu analiz et ve cevapla.",
            "tarih": "Bu tarih sorusunu analiz et ve cevapla.",
            "cografya": "Bu cografya sorusunu analiz et ve cevapla.",
        }

        base_prompt = subject_prompts.get(
            request.subject.lower(), "Bu soruyu analiz et ve coz."
        )

        # Adim adim cozum istegi
        step_instruction = ""
        if request.show_steps:
            step_instruction = """

Cozum adimlarini su formatta ver:
1. Soruyu anlama: Sorunun ne istedigini acikla
2. Verilen bilgiler: Gorseldeki verileri listele
3. Cozum yontemi: Hangi yontemi kullanacagini belirt
4. Adim adim cozum: Her adimi detayli goster
5. Sonuc: Dogru cevabi ve secenegi belirt (varsa)
"""

        # Seviye bilgisi
        level_info = f"\nSeviye: {request.level}. Bu seviyeye uygun detayda acikla."

        full_prompt = f"""Turkce yanit ver.
{base_prompt}
{level_info}
{step_instruction}"""

        result, elapsed_ms = await analyze_with_vision(request.image, full_prompt)

        return VisionResponse(
            success=True,
            result=result,
            model=llm_service.vision_model,
            processing_time_ms=round(elapsed_ms, 2),
            metadata={
                "subject": request.subject,
                "level": request.level,
                "show_steps": request.show_steps,
            },
        )

    except Exception as e:
        logger.error(f"Vision solve error: {e}")
        raise HTTPException(500, "Soru cozumu basarisiz. Lutfen tekrar deneyin.")


@router.post("/extract-text", response_model=VisionResponse)
async def extract_text(
    request: VisionExtractRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> VisionResponse:
    """
    Gorselden metin cikarma (OCR)

    Qwen3-VL ile gelismis OCR - el yazisi, basili metin ve formulleri tanir.

    - **image**: Base64 encoded gorsel
    - **include_layout**: Sayfa duzenini koruyarak cikar
    """
    if not validate_base64_image(request.image):
        raise HTTPException(400, "Gecersiz gorsel formati.")

    try:
        layout_instruction = ""
        if request.include_layout:
            layout_instruction = (
                " Sayfa duzenini (basliklari, paragraflari, listeleri) koruyarak cikar."
            )

        prompt = f"""Bu gorseldeki tum metinleri oku ve yaz.
Matematiksel ifadeleri LaTeX formatinda goster.
El yazisi varsa onu da oku.{layout_instruction}

Sadece okudugun metni yaz, yorum ekleme."""

        result, elapsed_ms = await analyze_with_vision(request.image, prompt)

        return VisionResponse(
            success=True,
            result=result,
            model=llm_service.vision_model,
            processing_time_ms=round(elapsed_ms, 2),
            metadata={"include_layout": request.include_layout},
        )

    except Exception as e:
        logger.error(f"Vision OCR error: {e}")
        raise HTTPException(500, "Metin cikarma basarisiz. Lutfen tekrar deneyin.")


@router.post("/describe-diagram", response_model=VisionResponse)
async def describe_diagram(
    request: VisionDiagramRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> VisionResponse:
    """
    Diyagram aciklama

    Egitim diyagramlarini (grafikler, sekillar, akis diyagramlari) aciklar.

    - **image**: Base64 encoded diyagram gorseli
    - **subject**: Konu alani
    - **detail_level**: Detay seviyesi (brief, detailed, comprehensive)
    """
    if not validate_base64_image(request.image):
        raise HTTPException(400, "Gecersiz gorsel formati.")

    try:
        # Detay seviyesi
        detail_map = {
            "brief": "Kisa ve oz bir aciklama yap (2-3 cumle).",
            "detailed": "Detayli bir aciklama yap. Tum onemli elemanlari belirt.",
            "comprehensive": "Kapsamli bir analiz yap. Her elemani, iliskilerini ve egitimsel onemini acikla.",
        }

        detail_instruction = detail_map.get(
            request.detail_level, detail_map["detailed"]
        )

        # Konu bazli ek talimatlar
        subject_extras = {
            "matematik": " Geometrik sekilleri, grafikleri ve matematiksel iliskileri vurgula.",
            "fizik": " Kuvvet vektorlerini, hareket yonlerini ve fiziksel buyuklukleri belirt.",
            "kimya": " Molekul yapilarini, baglari ve reaksiyon mekanizmalarini acikla.",
            "biyoloji": " Hucre yapilarini, organ sistemlerini ve biyolojik surecleri tanimla.",
            "cografya": " Harita elemanlarini, koordinatlari ve cografi ozellikleri belirt.",
        }

        extra = subject_extras.get(request.subject.lower(), "")

        prompt = f"""Turkce yanit ver.
Bu egitim diyagramini analiz et ve acikla.
Konu alani: {request.subject}

{detail_instruction}{extra}

Diyagramdaki:
- Ana elemanlari
- Oklar veya baglantilari
- Etiketleri ve yazilari
- Renk kodlamalarini (varsa)
ayri ayri belirt."""

        result, elapsed_ms = await analyze_with_vision(request.image, prompt)

        return VisionResponse(
            success=True,
            result=result,
            model=llm_service.vision_model,
            processing_time_ms=round(elapsed_ms, 2),
            metadata={"subject": request.subject, "detail_level": request.detail_level},
        )

    except Exception as e:
        logger.error(f"Vision diagram error: {e}")
        raise HTTPException(500, "Diyagram aciklama basarisiz. Lutfen tekrar deneyin.")


@router.post("/analyze-upload", response_model=VisionResponse)
async def analyze_upload(
    file: UploadFile = File(...),
    prompt: str = Form(default="Bu gorseli detayli olarak analiz et."),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> VisionResponse:
    """
    Dosya yukleme ile gorsel analizi

    - **file**: Gorsel dosyasi (PNG, JPEG, WebP, max 10MB)
    - **prompt**: Analiz icin prompt
    """
    # Dosya turu kontrolu
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Gecersiz dosya turu. Izin verilen: {allowed_types}")

    # Boyut kontrolu (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Dosya boyutu 10MB'dan buyuk olamaz.")

    try:
        # Base64'e cevir
        image_b64 = base64.b64encode(contents).decode("utf-8")

        full_prompt = f"Turkce yanit ver. {prompt}"

        result, elapsed_ms = await analyze_with_vision(image_b64, full_prompt)

        return VisionResponse(
            success=True,
            result=result,
            model=llm_service.vision_model,
            processing_time_ms=round(elapsed_ms, 2),
            metadata={"filename": file.filename},
        )

    except Exception as e:
        logger.error(f"Vision upload error: {e}")
        raise HTTPException(500, "Gorsel analizi basarisiz. Lutfen tekrar deneyin.")


@router.get("/health", response_model=VisionHealthResponse)
async def health_check() -> VisionHealthResponse:
    """Vision servisi saglik kontrolu — S-18: inference yapmadan durum döndür"""
    try:
        # S-18: Her çağrıda gerçek inference yapmak DoS vektörü.
        # Sadece servisin ayakta olup olmadığını kontrol et.
        return VisionHealthResponse(
            status="healthy",
            model=llm_service.vision_model,
            available=True,
            latency_ms=0.0,
        )

    except Exception as e:
        logger.warning(f"Vision health check failed: {e}")
        return VisionHealthResponse(
            status=f"unhealthy: {e!s}",
            model=llm_service.vision_model,
            available=False,
            latency_ms=None,
        )


@router.get("/info")
async def get_info(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Vision servisi bilgisi"""
    model_info = llm_service.get_model_info()

    return {
        "vision_model": model_info.get("vision_model", "qwen3-vl:8b"),
        "text_model": model_info.get("model", "qwen3:14b"),
        # S-17: İç altyapı adresi (localhost:11434) dışarı sızdırılmaz
        "provider": model_info.get("provider", "ollama"),
        "capabilities": [
            "image_analysis",
            "question_solving",
            "ocr",
            "diagram_description",
            "handwriting_recognition",
            "latex_extraction",
        ],
        "supported_formats": ["PNG", "JPEG", "WebP"],
        "max_file_size_mb": 10,
    }
