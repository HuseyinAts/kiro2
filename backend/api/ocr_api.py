"""
KIRO2 OCR API Endpoints
======================

YOLO detection ile entegre OCR API'si.

Endpoints:
- POST /api/ocr/extract - Tek görsel OCR
- POST /api/ocr/extract-batch - Batch OCR
- POST /api/ocr/question - Soru OCR (yapılandırılmış)
- POST /api/ocr/yolo-detect-ocr - YOLO detection + OCR pipeline
- GET /api/ocr/engines - Kullanılabilir OCR motorları
- GET /api/ocr/health - Sağlık kontrolü
"""

import base64
import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    logger.warning("cv2/numpy not available, OCR API will be degraded")
    CV2_AVAILABLE = False
    cv2 = None
    np = None

try:
    from services.unified_ocr_service import (
        OCREngine,
        OCRResult,
        get_ocr_service,
    )
    from services.yolo_question_detector import get_question_detector
    OCR_SERVICE_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"OCR services not available: {e}")
    OCR_SERVICE_AVAILABLE = False
    OCREngine = None
    OCRResult = None
    get_ocr_service = None
    get_question_detector = None

router = APIRouter(prefix="/api/v1/ocr", tags=["OCR"])


# ============================================================
# Pydantic Models
# ============================================================

class OCRBoxResponse(BaseModel):
    """OCR kutusu yanıtı"""
    text: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]


class OCRResultResponse(BaseModel):
    """OCR sonuç yanıtı"""
    text: str
    raw_text: str
    confidence: float
    boxes: List[OCRBoxResponse]
    engine: str
    language: str
    processing_time_ms: float
    has_math: bool
    latex: Optional[str]
    metadata: dict = {}


class QuestionOCRResponse(BaseModel):
    """Soru OCR yanıtı"""
    question_number: Optional[int]
    question_text: str
    options: dict  # {A: "", B: "", C: "", D: "", E: ""}
    has_image: bool
    has_equation: bool
    latex_content: Optional[str]
    confidence: float
    raw_ocr: OCRResultResponse


class Base64ImageRequest(BaseModel):
    """Base64 görsel isteği"""
    image: str = Field(..., description="Base64 encoded image")
    engine: Optional[str] = Field(None, description="OCR engine: easyocr, paddleocr, tesseract, claude_vision")


class BatchOCRRequest(BaseModel):
    """Batch OCR isteği"""
    images: List[str] = Field(..., description="List of base64 encoded images")
    engine: Optional[str] = None
    max_concurrent: int = Field(5, ge=1, le=20)


class YOLOOCRRequest(BaseModel):
    """YOLO + OCR isteği"""
    image: str = Field(..., description="Base64 encoded image")
    confidence_threshold: float = Field(0.25, ge=0.0, le=1.0)
    crop_padding: int = Field(10, ge=0, le=50)
    ocr_engine: Optional[str] = None


class OCREngineInfo(BaseModel):
    """OCR motoru bilgisi"""
    name: str
    available: bool
    description: str


class HealthResponse(BaseModel):
    """Sağlık kontrolü yanıtı"""
    status: str
    primary_engine: str
    fallback_engine: str
    loaded_engines: List[str]


# ============================================================
# Helper Functions
# ============================================================

def decode_base64_image(b64_string: str):
    """Base64 string'i numpy array'e çevir"""
    if not CV2_AVAILABLE:
        raise HTTPException(503, "cv2/numpy not available")

    # Data URL prefix'i varsa kaldır
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]

    img_bytes = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image")

    return img


def get_engine_from_string(engine_str: Optional[str]) -> Optional[OCREngine]:
    """String'den OCREngine enum'a çevir"""
    if not engine_str:
        return None

    engine_map = {
        'easyocr': OCREngine.EASYOCR,
        'paddleocr': OCREngine.PADDLEOCR,
        'tesseract': OCREngine.TESSERACT,
        'claude_vision': OCREngine.CLAUDE_VISION,
        'surya': OCREngine.SURYA,
    }

    return engine_map.get(engine_str.lower())


def ocr_result_to_response(result: OCRResult) -> OCRResultResponse:
    """OCRResult'ı response modeline çevir"""
    return OCRResultResponse(
        text=result.text,
        raw_text=result.raw_text,
        confidence=result.confidence,
        boxes=[
            OCRBoxResponse(
                text=box.text,
                confidence=box.confidence,
                bbox=list(box.bbox)
            )
            for box in result.boxes
        ],
        engine=result.engine,
        language=result.language,
        processing_time_ms=result.processing_time_ms,
        has_math=result.has_math,
        latex=result.latex,
        metadata=result.metadata
    )


# ============================================================
# Endpoints
# ============================================================

@router.post("/extract", response_model=OCRResultResponse)
async def extract_text(
    file: UploadFile = File(...),
    engine: Optional[str] = Form(None)
):
    """
    Tek görselten metin çıkar

    - **file**: Görsel dosyası (PNG, JPEG, WebP)
    - **engine**: OCR motoru (easyocr, paddleocr, tesseract, claude_vision)
    """
    if not OCR_SERVICE_AVAILABLE:
        raise HTTPException(503, "OCR service not available")

    # Dosya türü kontrolü
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Invalid file type. Allowed: {allowed_types}")

    try:
        # Dosyayı oku
        contents = await file.read()

        # OCR çalıştır
        ocr_service = get_ocr_service()
        ocr_engine = get_engine_from_string(engine)
        result = await ocr_service.extract_text_async(contents, ocr_engine)

        return ocr_result_to_response(result)

    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(500, f"OCR failed: {str(e)}")


@router.post("/extract-base64", response_model=OCRResultResponse)
async def extract_text_base64(request: Base64ImageRequest):
    """
    Base64 görselten metin çıkar
    
    - **image**: Base64 encoded görsel
    - **engine**: OCR motoru
    """
    try:
        # Görseli decode et
        img = decode_base64_image(request.image)

        # OCR çalıştır
        ocr_service = get_ocr_service()
        ocr_engine = get_engine_from_string(request.engine)
        result = await ocr_service.extract_text_async(img, ocr_engine)

        return ocr_result_to_response(result)

    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(500, f"OCR failed: {str(e)}")


@router.post("/extract-batch", response_model=List[OCRResultResponse])
async def extract_text_batch(request: BatchOCRRequest):
    """
    Batch görsel OCR
    
    - **images**: Base64 encoded görsel listesi (max 20)
    - **engine**: OCR motoru
    - **max_concurrent**: Maksimum eşzamanlı işlem
    """
    if len(request.images) > 20:
        raise HTTPException(400, "Maximum 20 images allowed per batch")

    try:
        # Görselleri decode et
        images = [decode_base64_image(b64) for b64 in request.images]

        # Batch OCR çalıştır
        ocr_service = get_ocr_service()
        results = await ocr_service.batch_process(images, request.max_concurrent)

        return [ocr_result_to_response(r) for r in results]

    except Exception as e:
        logger.error(f"Batch OCR error: {e}")
        raise HTTPException(500, f"Batch OCR failed: {str(e)}")


@router.post("/question", response_model=QuestionOCRResponse)
async def process_question(
    file: UploadFile = File(...),
    engine: Optional[str] = Form(None)
):
    """
    Soru görselini işle ve yapılandırılmış sonuç döndür
    
    - **file**: Soru görseli
    - **engine**: OCR motoru
    """
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Invalid file type. Allowed: {allowed_types}")

    try:
        contents = await file.read()

        ocr_service = get_ocr_service()
        ocr_engine = get_engine_from_string(engine)
        result = await ocr_service.process_question_async(contents, ocr_engine)

        return QuestionOCRResponse(
            question_number=result.question_number,
            question_text=result.question_text,
            options=result.options,
            has_image=result.has_image,
            has_equation=result.has_equation,
            latex_content=result.latex_content,
            confidence=result.confidence,
            raw_ocr=ocr_result_to_response(result.raw_ocr)
        )

    except Exception as e:
        logger.error(f"Question OCR error: {e}")
        raise HTTPException(500, f"Question OCR failed: {str(e)}")


@router.post("/question-base64", response_model=QuestionOCRResponse)
async def process_question_base64(request: Base64ImageRequest):
    """
    Base64 soru görselini işle
    
    - **image**: Base64 encoded soru görseli
    - **engine**: OCR motoru
    """
    try:
        img = decode_base64_image(request.image)

        ocr_service = get_ocr_service()
        ocr_engine = get_engine_from_string(request.engine)
        result = await ocr_service.process_question_async(img, ocr_engine)

        return QuestionOCRResponse(
            question_number=result.question_number,
            question_text=result.question_text,
            options=result.options,
            has_image=result.has_image,
            has_equation=result.has_equation,
            latex_content=result.latex_content,
            confidence=result.confidence,
            raw_ocr=ocr_result_to_response(result.raw_ocr)
        )

    except Exception as e:
        logger.error(f"Question OCR error: {e}")
        raise HTTPException(500, f"Question OCR failed: {str(e)}")


@router.post("/yolo-detect-ocr")
async def yolo_detect_and_ocr(request: YOLOOCRRequest):
    """
    YOLO detection + OCR pipeline
    
    Önce YOLO ile soruları tespit eder, sonra her soru için OCR çalıştırır.
    
    - **image**: Base64 encoded görsel
    - **confidence_threshold**: YOLO confidence threshold
    - **crop_padding**: Kırpma için padding
    - **ocr_engine**: OCR motoru
    """
    try:
        # Görseli decode et
        img = decode_base64_image(request.image)

        # YOLO detection
        detector = get_question_detector()
        detection_result = detector.detect(img, confidence_threshold=request.confidence_threshold)

        # Detection sonucunu dict'e çevir
        detection_dict = {
            'image_path': None,
            'detections': [
                {
                    'class_id': d.class_id,
                    'class_name': d.class_name,
                    'confidence': d.confidence,
                    'bbox': {
                        'x1': d.bbox.x1,
                        'y1': d.bbox.y1,
                        'x2': d.bbox.x2,
                        'y2': d.bbox.y2
                    }
                }
                for d in detection_result.detections
            ]
        }

        # OCR işle
        ocr_service = get_ocr_service()

        # Her detection için OCR
        questions = []
        metadata = {}

        for det in detection_dict['detections']:
            bbox = det['bbox']
            class_name = det['class_name']

            # Kırp
            x1 = max(0, int(bbox['x1']) - request.crop_padding)
            y1 = max(0, int(bbox['y1']) - request.crop_padding)
            x2 = min(img.shape[1], int(bbox['x2']) + request.crop_padding)
            y2 = min(img.shape[0], int(bbox['y2']) + request.crop_padding)

            cropped = img[y1:y2, x1:x2]

            if class_name == 'soru':
                # Soru için tam OCR
                ocr_engine = get_engine_from_string(request.ocr_engine)
                result = await ocr_service.process_question_async(cropped, ocr_engine)

                questions.append({
                    'detection': det,
                    'ocr': {
                        'question_number': result.question_number,
                        'question_text': result.question_text,
                        'options': result.options,
                        'has_image': result.has_image,
                        'has_equation': result.has_equation,
                        'latex_content': result.latex_content,
                        'confidence': result.confidence
                    }
                })
            else:
                # Metadata için basit OCR
                ocr_engine = get_engine_from_string(request.ocr_engine)
                result = await ocr_service.extract_text_async(cropped, ocr_engine)
                metadata[class_name] = result.text

        return {
            'success': True,
            'detection_count': len(detection_dict['detections']),
            'question_count': len(questions),
            'questions': questions,
            'metadata': metadata,
            'yolo_detections': detection_dict['detections']
        }

    except Exception as e:
        logger.error(f"YOLO+OCR error: {e}")
        raise HTTPException(500, f"YOLO+OCR failed: {str(e)}")


@router.get("/engines", response_model=List[OCREngineInfo])
async def list_engines():
    """Kullanılabilir OCR motorlarını listele"""
    engines = [
        OCREngineInfo(
            name="easyocr",
            available=True,
            description="EasyOCR - Türkçe ve matematik için optimize, GPU destekli"
        ),
        OCREngineInfo(
            name="paddleocr",
            available=True,
            description="PaddleOCR - Hızlı ve doğru, Türkçe destekli"
        ),
        OCREngineInfo(
            name="tesseract",
            available=True,
            description="Tesseract - Yaygın kullanılan açık kaynak OCR"
        ),
        OCREngineInfo(
            name="claude_vision",
            available=True,
            description="Claude Vision - Premium kalite, API key gerekli"
        ),
    ]

    return engines


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """OCR servisi sağlık kontrolü"""
    try:
        ocr_service = get_ocr_service()
        info = ocr_service.get_info()

        return HealthResponse(
            status="healthy",
            primary_engine=info['primary_engine'],
            fallback_engine=info['fallback_engine'],
            loaded_engines=info['loaded_engines']
        )

    except Exception as e:
        return HealthResponse(
            status=f"unhealthy: {str(e)}",
            primary_engine="unknown",
            fallback_engine="unknown",
            loaded_engines=[]
        )


@router.get("/info")
async def get_service_info():
    """OCR servisi detaylı bilgisi"""
    try:
        ocr_service = get_ocr_service()
        return ocr_service.get_info()
    except Exception as e:
        raise HTTPException(500, f"Failed to get service info: {str(e)}")
