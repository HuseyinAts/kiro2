"""
KIRO2 YOLO Question Detection API
==================================
Soru tespit API endpoint'leri.

Endpoints:
- POST /api/yolo/detect - Görsel üzerinde soru tespiti
- POST /api/yolo/detect-batch - Toplu tespit
- POST /api/yolo/crop-questions - Soruları kırp
- GET /api/yolo/model-info - Model bilgileri
"""

import base64
import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from core.dependencies import AuthenticatedUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/yolo",
    tags=["YOLO Question Detection"],
    responses={404: {"description": "Not found"}},
)


# ==================== Pydantic Models ====================


class BoundingBoxResponse(BaseModel):
    """Bounding box yanıtı"""

    x1: int
    y1: int
    x2: int
    y2: int
    width: int
    height: int


class DetectionResponse(BaseModel):
    """Tek tespit yanıtı"""

    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBoxResponse


class MetadataResponse(BaseModel):
    """Metadata yanıtı"""

    kitap: DetectionResponse | None = None
    test_no: DetectionResponse | None = None
    sayfa: DetectionResponse | None = None
    konu: DetectionResponse | None = None
    cevaplar: DetectionResponse | None = None
    cozum: DetectionResponse | None = None


class ImageSizeResponse(BaseModel):
    """Görsel boyutu yanıtı"""

    width: int
    height: int


class DetectionResultResponse(BaseModel):
    """Tespit sonucu yanıtı"""

    image_path: str | None = None
    image_size: ImageSizeResponse
    total_detections: int
    questions_count: int
    detections: list[DetectionResponse]
    questions: list[DetectionResponse]
    metadata: dict
    processing_time_ms: float


class CroppedQuestionResponse(BaseModel):
    """Kırpılmış soru yanıtı"""

    question_index: int
    class_name: str
    confidence: float
    bbox: BoundingBoxResponse
    image_base64: str
    image_width: int
    image_height: int


class ModelInfoResponse(BaseModel):
    """Model bilgisi yanıtı"""

    model_path: str
    model_loaded: bool
    device: str
    confidence_threshold: float
    iou_threshold: float
    classes: dict
    num_classes: int


# ==================== Helper Functions ====================


def get_detector() -> Any:
    """YOLO detector'ı lazy load et.

    Returns:
        YOLO question detector instance

    Raises:
        HTTPException: Model yüklenemezse
    """
    try:
        from services.yolo_question_detector import get_question_detector

        return get_question_detector()
    except ImportError as e:
        logger.error(f"YOLO detector import hatası: {e}")
        raise HTTPException(
            status_code=500, detail="YOLO modülü yüklenemedi. Ultralytics kurulu mu?"
        )
    except FileNotFoundError as e:
        logger.error(f"YOLO model bulunamadı: {e}")
        raise HTTPException(
            status_code=500,
            detail="YOLO model dosyası bulunamadı (models/yolo11_best.pt)",
        )


async def read_upload_file(file: UploadFile) -> bytes:
    """Upload dosyasını oku"""
    content = await file.read()
    await file.seek(0)  # Reset for potential re-read
    return content


# ==================== API Endpoints ====================


@router.post(
    "/detect",
    response_model=DetectionResultResponse,
    summary="Görsel üzerinde soru tespiti",
    description="""
    Yüklenen görsel üzerinde YOLO11x ile soru tespiti yapar.
    
    Tespit edilen sınıflar:
    - soru (0): Soru blokları (mAP50: %99.1)
    - konu (1): Konu başlığı (mAP50: %97.0)
    - cevaplar (2): Cevap anahtarı (mAP50: %95.0)
    - test_no (3): Test numarası (mAP50: %95.9)
    - sayfa (4): Sayfa numarası (mAP50: %98.0)
    - cozum (5): Çözüm bölümü
    - kitap (6): Kaynak kitap
    """,
)
async def detect_questions(
    file: UploadFile = File(..., description="Sınav sayfası görseli (PNG, JPG)"),
    confidence: float = Query(0.25, ge=0.0, le=1.0, description="Minimum güven eşiği"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Görsel üzerinde soru tespiti yap."""

    # Dosya türü kontrolü
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya türü: {file.content_type}. "
            f"Desteklenen türler: {', '.join(allowed_types)}",
        )

    try:
        # Dosyayı oku
        image_bytes = await read_upload_file(file)

        # Detector'ı al
        detector = get_detector()

        # Confidence ayarla
        detector.confidence_threshold = confidence

        # Tespit yap
        result = await detector.detect_async(image_bytes)

        return result.to_dict()

    except Exception as e:
        logger.error(f"Tespit hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post(
    "/detect-base64",
    response_model=DetectionResultResponse,
    summary="Base64 görsel ile soru tespiti",
    description="Base64 encoded görsel üzerinde soru tespiti yapar.",
)
async def detect_questions_base64(
    image_base64: str = Form(..., description="Base64 encoded görsel"),
    confidence: float = Query(0.25, ge=0.0, le=1.0),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Base64 görsel ile soru tespiti."""

    try:
        # Base64 decode
        # data:image/png;base64, prefix varsa kaldır
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]

        image_bytes = base64.b64decode(image_base64)

        # Detector'ı al ve tespit yap
        detector = get_detector()
        detector.confidence_threshold = confidence
        result = await detector.detect_async(image_bytes)

        return result.to_dict()

    except Exception as e:
        logger.error(f"Base64 tespit hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post(
    "/detect-batch",
    response_model=list[DetectionResultResponse],
    summary="Toplu soru tespiti",
    description="Birden fazla görsel üzerinde toplu tespit yapar.",
)
async def detect_questions_batch(
    files: list[UploadFile] = File(..., description="Sınav sayfası görselleri"),
    confidence: float = Query(0.25, ge=0.0, le=1.0),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Toplu soru tespiti."""

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maksimum 20 dosya yüklenebilir.")

    try:
        detector = get_detector()
        detector.confidence_threshold = confidence

        results = []
        for file in files:
            try:
                image_bytes = await read_upload_file(file)
                result = await detector.detect_async(image_bytes)
                results.append(result.to_dict())
            except Exception as e:
                logger.error(f"Dosya tespiti hatası ({file.filename}): {e}")
                results.append(
                    {
                        "image_path": file.filename,
                        "image_size": {"width": 0, "height": 0},
                        "total_detections": 0,
                        "questions_count": 0,
                        "detections": [],
                        "questions": [],
                        "metadata": {},
                        "processing_time_ms": 0,
                        "error": str(e),
                    }
                )

        return results

    except Exception as e:
        logger.error(f"Toplu tespit hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post(
    "/crop-questions",
    response_model=list[CroppedQuestionResponse],
    summary="Tespit edilen soruları kırp",
    description="Görsel üzerinde tespit edilen soruları kırpıp base64 olarak döndürür.",
)
async def crop_questions(
    file: UploadFile = File(..., description="Sınav sayfası görseli"),
    confidence: float = Query(0.25, ge=0.0, le=1.0),
    padding: int = Query(10, ge=0, le=50, description="Kırpma kenar boşluğu (piksel)"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Soruları kırp ve base64 döndür."""

    from PIL import Image

    try:
        image_bytes = await read_upload_file(file)
        image = Image.open(io.BytesIO(image_bytes))

        detector = get_detector()
        detector.confidence_threshold = confidence

        # Tespit ve kırpma
        cropped_images = detector.crop_questions(image, padding=padding)

        results = []
        for idx, (cropped_img, detection) in enumerate(cropped_images):
            # PIL Image'ı base64'e çevir
            buffer = io.BytesIO()
            cropped_img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            results.append(
                {
                    "question_index": idx,
                    "class_name": detection.class_name,
                    "confidence": detection.confidence,
                    "bbox": detection.bbox.to_dict(),
                    "image_base64": img_base64,
                    "image_width": cropped_img.width,
                    "image_height": cropped_img.height,
                }
            )

        return results

    except Exception as e:
        logger.error(f"Kırpma hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Model bilgileri",
    description="YOLO model bilgilerini döndürür.",
)
async def get_model_info() -> dict[str, Any]:
    """Model bilgilerini getir."""

    try:
        detector = get_detector()
        return detector.get_model_info()
    except Exception as e:
        logger.error(f"Model bilgisi hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/health",
    summary="Servis sağlık kontrolü",
    description="YOLO tespit servisinin durumunu kontrol eder.",
)
async def health_check() -> dict[str, Any]:
    """Sağlık kontrolü."""

    try:
        detector = get_detector()
        info = detector.get_model_info()

        return {
            "status": "healthy",
            "model_loaded": info["model_loaded"],
            "device": info["device"],
            "classes": list(info["classes"].values()),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ==================== Optional: WebSocket for real-time detection ====================

# from fastapi import WebSocket, WebSocketDisconnect
#
# @router.websocket("/ws/detect")
# async def websocket_detect(websocket: WebSocket):
#     """WebSocket üzerinden gerçek zamanlı tespit"""
#     await websocket.accept()
#
#     try:
#         detector = get_detector()
#
#         while True:
#             # Base64 görsel al
#             data = await websocket.receive_text()
#
#             # Tespit yap
#             image_bytes = base64.b64decode(data)
#             result = detector.detect(image_bytes)
#
#             # Sonucu gönder
#             await websocket.send_json(result.to_dict())
#
#     except WebSocketDisconnect:
#         logger.info("WebSocket bağlantısı kapandı")
