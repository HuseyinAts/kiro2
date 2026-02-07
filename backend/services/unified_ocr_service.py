"""
KIRO2 Unified OCR Service
========================

YOLO detection sonuçlarını OCR ile işleyen birleşik servis.

Desteklenen OCR motorları:
- EasyOCR (varsayılan, Türkçe + İngilizce + matematik)
- PaddleOCR (hızlı, Türkçe destekli)
- Tesseract (fallback)
- Claude Vision (premium, en yüksek kalite)

Kullanım:
    from services.unified_ocr_service import UnifiedOCRService, get_ocr_service

    # Singleton instance
    ocr = get_ocr_service()
    
    # YOLO detection sonuçlarından OCR
    results = await ocr.process_yolo_detections(detection_results)
    
    # Tek görsel OCR
    text = await ocr.extract_text(image_path)
"""

import asyncio
import base64
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ============================================================
# Data Classes
# ============================================================

class OCREngine(Enum):
    """Kullanılabilir OCR motorları"""
    EASYOCR = "easyocr"
    PADDLEOCR = "paddleocr"
    TESSERACT = "tesseract"
    CLAUDE_VISION = "claude_vision"
    SURYA = "surya"


@dataclass
class OCRBox:
    """OCR tarafından tespit edilen metin kutusu"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    
    @property
    def area(self) -> int:
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)


@dataclass
class OCRResult:
    """OCR işlem sonucu"""
    text: str
    raw_text: str  # Temizlenmemiş metin
    confidence: float
    boxes: List[OCRBox]
    engine: str
    language: str
    processing_time_ms: float
    has_math: bool = False
    latex: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestionOCRResult:
    """Soru için OCR sonucu"""
    question_number: Optional[int]
    question_text: str
    options: Dict[str, str]  # A, B, C, D, E
    has_image: bool
    has_equation: bool
    latex_content: Optional[str]
    confidence: float
    raw_ocr: OCRResult
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# OCR Engine Implementations
# ============================================================

class EasyOCREngine:
    """EasyOCR implementation - Türkçe ve matematik için optimize"""
    
    def __init__(self, languages: List[str] = None, gpu: bool = True):
        self.languages = languages or ['tr', 'en']
        self.gpu = gpu
        self._reader = None
        
    @property
    def reader(self):
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=self.gpu,
                    verbose=False
                )
                logger.info(f"EasyOCR initialized with languages: {self.languages}")
            except ImportError:
                logger.error("EasyOCR not installed. Run: pip install easyocr")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                raise
        return self._reader
    
    def extract(self, image: np.ndarray) -> List[OCRBox]:
        """Görüntüden metin çıkar"""
        results = self.reader.readtext(image)
        
        boxes = []
        for bbox, text, conf in results:
            # bbox: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            x1 = int(min(p[0] for p in bbox))
            y1 = int(min(p[1] for p in bbox))
            x2 = int(max(p[0] for p in bbox))
            y2 = int(max(p[1] for p in bbox))
            
            boxes.append(OCRBox(
                text=text,
                confidence=conf,
                bbox=(x1, y1, x2, y2)
            ))
        
        return boxes


class PaddleOCREngine:
    """PaddleOCR implementation - Hızlı ve doğru"""
    
    def __init__(self, lang: str = 'tr', use_gpu: bool = True):
        self.lang = lang
        self.use_gpu = use_gpu
        self._ocr = None
        
    @property
    def ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(
                    lang=self.lang,
                    use_angle_cls=True,
                    use_gpu=self.use_gpu,
                    show_log=False
                )
                logger.info(f"PaddleOCR initialized with lang: {self.lang}")
            except ImportError:
                logger.error("PaddleOCR not installed. Run: pip install paddlepaddle paddleocr")
                raise
        return self._ocr
    
    def extract(self, image: np.ndarray) -> List[OCRBox]:
        """Görüntüden metin çıkar"""
        result = self.ocr.ocr(image, cls=True)
        
        boxes = []
        if result and result[0]:
            for line in result[0]:
                bbox_points, (text, conf) = line
                # bbox_points: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                x1 = int(min(p[0] for p in bbox_points))
                y1 = int(min(p[1] for p in bbox_points))
                x2 = int(max(p[0] for p in bbox_points))
                y2 = int(max(p[1] for p in bbox_points))
                
                boxes.append(OCRBox(
                    text=text,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2)
                ))
        
        return boxes


class TesseractEngine:
    """Tesseract OCR fallback"""
    
    def __init__(self, lang: str = 'tur+eng'):
        self.lang = lang
        
    def extract(self, image: np.ndarray) -> List[OCRBox]:
        """Görüntüden metin çıkar"""
        try:
            import pytesseract
            
            # Tesseract data
            data = pytesseract.image_to_data(
                image,
                lang=self.lang,
                output_type=pytesseract.Output.DICT
            )
            
            boxes = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i]) / 100.0
                
                if text and conf > 0:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    boxes.append(OCRBox(
                        text=text,
                        confidence=conf,
                        bbox=(x, y, x + w, y + h)
                    ))
            
            return boxes
            
        except ImportError:
            logger.error("pytesseract not installed")
            return []


class ClaudeVisionEngine:
    """Claude Vision API for premium OCR"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self._client = None
        
    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude Vision initialized")
            except ImportError:
                logger.error("anthropic not installed")
        return self._client
    
    async def extract_async(self, image: np.ndarray) -> Tuple[str, float]:
        """Claude Vision ile OCR"""
        if not self.client:
            return "", 0.0
        
        # Image to base64
        _, buffer = cv2.imencode('.png', image)
        b64_image = base64.b64encode(buffer).decode('utf-8')
        
        prompt = """Bu görüntüdeki tüm metni oku ve aynen döndür.

Kurallar:
1. Matematiksel ifadeleri LaTeX formatında yaz ($ $ içinde)
2. Soru numaralarını koru
3. Şık harflerini (A, B, C, D, E) koru
4. Satır yapısını koru
5. Türkçe karakterleri doğru yaz

Sadece görüntüdeki metni döndür, başka açıklama yapma."""
        
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            text = response.content[0].text
            return text, 0.95  # Claude genellikle yüksek kalite
            
        except Exception as e:
            logger.error(f"Claude Vision error: {e}")
            return "", 0.0


# ============================================================
# Text Processing Utilities
# ============================================================

class TextProcessor:
    """OCR sonuçlarını işleyen yardımcı sınıf"""
    
    # Matematiksel ifade kalıpları
    MATH_PATTERNS = [
        r'\d+[+\-×÷*/^=]\d+',  # Temel işlemler
        r'[xyz]\s*[+\-=]\s*\d+',  # Değişkenli ifadeler
        r'\d+\s*[²³⁴⁵]',  # Üsler
        r'√\d+',  # Karekök
        r'\d+/\d+',  # Kesirler
        r'∫|∑|∏|lim|sin|cos|tan|log|ln',  # Matematik sembolleri
        r'[αβγδεζηθικλμνξπρστυφχψω]',  # Yunan harfleri
    ]
    
    # Soru numarası kalıpları
    QUESTION_NUMBER_PATTERNS = [
        r'^(\d+)[\.\)]\s*',  # "1." veya "1)"
        r'^Soru\s*(\d+)',  # "Soru 1"
        r'^S\.?\s*(\d+)',  # "S.1" veya "S 1"
    ]
    
    # Şık kalıpları
    OPTION_PATTERNS = [
        r'^([A-E])[\.\)]\s*(.+)$',  # "A." veya "A)"
        r'^([A-E])\s+(.+)$',  # "A metin"
    ]
    
    @classmethod
    def clean_text(cls, text: str) -> str:
        """OCR metnini temizle"""
        if not text:
            return ""
        
        # Çoklu boşlukları teke indir
        text = re.sub(r'\s+', ' ', text)
        
        # Satır başı/sonu boşlukları temizle
        text = '\n'.join(line.strip() for line in text.split('\n'))
        
        # Boş satırları teke indir
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @classmethod
    def detect_math(cls, text: str) -> bool:
        """Metinde matematik var mı?"""
        for pattern in cls.MATH_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def extract_question_number(cls, text: str) -> Optional[int]:
        """Soru numarasını çıkar"""
        for pattern in cls.QUESTION_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    pass
        return None
    
    @classmethod
    def extract_options(cls, text: str) -> Dict[str, str]:
        """Şıkları çıkar (A, B, C, D, E)"""
        options = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            for pattern in cls.OPTION_PATTERNS:
                match = re.match(pattern, line)
                if match:
                    letter = match.group(1).upper()
                    content = match.group(2).strip()
                    options[letter] = content
                    break
        
        return options
    
    @classmethod
    def convert_to_latex(cls, text: str) -> str:
        """Basit matematik ifadelerini LaTeX'e çevir"""
        # Üst simgeler
        text = re.sub(r'(\d+)²', r'$\1^2$', text)
        text = re.sub(r'(\d+)³', r'$\1^3$', text)
        
        # Karekök
        text = re.sub(r'√(\d+)', r'$\\sqrt{\1}$', text)
        
        # Kesirler (basit)
        text = re.sub(r'(\d+)/(\d+)', r'$\\frac{\1}{\2}$', text)
        
        # Çarpı işareti
        text = text.replace('×', r'$\times$')
        text = text.replace('÷', r'$\div$')
        
        return text
    
    @classmethod
    def merge_boxes_to_text(cls, boxes: List[OCRBox], image_height: int = None) -> str:
        """OCR kutularını satır sırasına göre birleştir"""
        if not boxes:
            return ""
        
        # Y koordinatına göre grupla (satır tespiti)
        # Yakın y değerlerini aynı satır say
        threshold = 15  # piksel
        
        sorted_boxes = sorted(boxes, key=lambda b: (b.bbox[1], b.bbox[0]))
        
        lines = []
        current_line = []
        current_y = sorted_boxes[0].bbox[1] if sorted_boxes else 0
        
        for box in sorted_boxes:
            if abs(box.bbox[1] - current_y) > threshold:
                # Yeni satır
                if current_line:
                    # X'e göre sırala
                    current_line.sort(key=lambda b: b.bbox[0])
                    line_text = ' '.join(b.text for b in current_line)
                    lines.append(line_text)
                current_line = [box]
                current_y = box.bbox[1]
            else:
                current_line.append(box)
        
        # Son satır
        if current_line:
            current_line.sort(key=lambda b: b.bbox[0])
            line_text = ' '.join(b.text for b in current_line)
            lines.append(line_text)
        
        return '\n'.join(lines)


# ============================================================
# Unified OCR Service
# ============================================================

class UnifiedOCRService:
    """
    Birleşik OCR servisi - YOLO detection ile entegre
    
    Özellikler:
    - Çoklu OCR motoru desteği
    - Otomatik motor seçimi
    - YOLO detection sonuçlarını işleme
    - Batch processing
    - Async support
    """
    
    def __init__(
        self,
        primary_engine: OCREngine = OCREngine.EASYOCR,
        fallback_engine: OCREngine = OCREngine.TESSERACT,
        use_gpu: bool = True,
        languages: List[str] = None
    ):
        self.primary_engine = primary_engine
        self.fallback_engine = fallback_engine
        self.use_gpu = use_gpu
        self.languages = languages or ['tr', 'en']
        
        self._engines: Dict[OCREngine, Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(f"UnifiedOCRService initialized: primary={primary_engine.value}, fallback={fallback_engine.value}")
    
    def _get_engine(self, engine_type: OCREngine):
        """OCR motorunu lazy load et"""
        if engine_type not in self._engines:
            if engine_type == OCREngine.EASYOCR:
                self._engines[engine_type] = EasyOCREngine(
                    languages=self.languages,
                    gpu=self.use_gpu
                )
            elif engine_type == OCREngine.PADDLEOCR:
                self._engines[engine_type] = PaddleOCREngine(
                    lang='tr',
                    use_gpu=self.use_gpu
                )
            elif engine_type == OCREngine.TESSERACT:
                self._engines[engine_type] = TesseractEngine(lang='tur+eng')
            elif engine_type == OCREngine.CLAUDE_VISION:
                self._engines[engine_type] = ClaudeVisionEngine()
            else:
                raise ValueError(f"Unknown engine: {engine_type}")
        
        return self._engines[engine_type]
    
    def _load_image(self, image_input: Union[str, Path, bytes, np.ndarray, Image.Image]) -> np.ndarray:
        """Farklı input tiplerini numpy array'e çevir"""
        if isinstance(image_input, np.ndarray):
            return image_input
        
        if isinstance(image_input, Image.Image):
            return cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        
        if isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if isinstance(image_input, (str, Path)):
            path = str(image_input)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Image not found: {path}")
            return cv2.imread(path)
        
        raise TypeError(f"Unsupported image type: {type(image_input)}")
    
    def extract_text(
        self,
        image: Union[str, Path, bytes, np.ndarray, Image.Image],
        engine: OCREngine = None
    ) -> OCRResult:
        """
        Görüntüden metin çıkar (senkron)
        
        Args:
            image: Görüntü (path, bytes, numpy array, PIL Image)
            engine: Kullanılacak OCR motoru (None = primary)
            
        Returns:
            OCRResult
        """
        import time
        start_time = time.time()
        
        # Görüntüyü yükle
        img_array = self._load_image(image)
        
        # Motor seç
        engine_type = engine or self.primary_engine
        ocr_engine = self._get_engine(engine_type)
        
        try:
            # OCR çalıştır
            boxes = ocr_engine.extract(img_array)
            
            # Metni birleştir
            raw_text = TextProcessor.merge_boxes_to_text(boxes, img_array.shape[0])
            clean_text = TextProcessor.clean_text(raw_text)
            
            # Ortalama güven skoru
            avg_confidence = sum(b.confidence for b in boxes) / len(boxes) if boxes else 0.0
            
            # Matematik tespiti
            has_math = TextProcessor.detect_math(clean_text)
            latex = TextProcessor.convert_to_latex(clean_text) if has_math else None
            
            processing_time = (time.time() - start_time) * 1000
            
            return OCRResult(
                text=clean_text,
                raw_text=raw_text,
                confidence=avg_confidence,
                boxes=boxes,
                engine=engine_type.value,
                language=','.join(self.languages),
                processing_time_ms=processing_time,
                has_math=has_math,
                latex=latex
            )
            
        except Exception as e:
            logger.error(f"OCR error with {engine_type.value}: {e}")
            
            # Fallback dene
            if engine_type != self.fallback_engine:
                logger.info(f"Trying fallback engine: {self.fallback_engine.value}")
                return self.extract_text(image, self.fallback_engine)
            
            # Hata döndür
            return OCRResult(
                text="",
                raw_text="",
                confidence=0.0,
                boxes=[],
                engine=engine_type.value,
                language=','.join(self.languages),
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)}
            )
    
    async def extract_text_async(
        self,
        image: Union[str, Path, bytes, np.ndarray, Image.Image],
        engine: OCREngine = None
    ) -> OCRResult:
        """Async metin çıkarma"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.extract_text(image, engine)
        )
    
    def process_question(
        self,
        image: Union[str, Path, bytes, np.ndarray, Image.Image],
        engine: OCREngine = None
    ) -> QuestionOCRResult:
        """
        Soru görüntüsünü işle ve yapılandırılmış sonuç döndür
        
        Args:
            image: Soru görüntüsü
            engine: OCR motoru
            
        Returns:
            QuestionOCRResult
        """
        # OCR çalıştır
        ocr_result = self.extract_text(image, engine)
        
        # Soru bilgilerini çıkar
        question_number = TextProcessor.extract_question_number(ocr_result.text)
        options = TextProcessor.extract_options(ocr_result.text)
        
        # Soru metnini temizle (şıkları çıkar)
        question_text = ocr_result.text
        for letter, content in options.items():
            question_text = question_text.replace(f"{letter})", "").replace(f"{letter}.", "")
            question_text = question_text.replace(content, "")
        question_text = TextProcessor.clean_text(question_text)
        
        # Görsel/denklem tespiti
        has_image = any(kw in ocr_result.text.lower() for kw in ['şekil', 'grafik', 'tablo', 'diyagram'])
        
        return QuestionOCRResult(
            question_number=question_number,
            question_text=question_text,
            options=options,
            has_image=has_image,
            has_equation=ocr_result.has_math,
            latex_content=ocr_result.latex,
            confidence=ocr_result.confidence,
            raw_ocr=ocr_result
        )
    
    async def process_question_async(
        self,
        image: Union[str, Path, bytes, np.ndarray, Image.Image],
        engine: OCREngine = None
    ) -> QuestionOCRResult:
        """Async soru işleme"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.process_question(image, engine)
        )
    
    async def process_yolo_detections(
        self,
        detection_result: Dict[str, Any],
        image_path: Optional[str] = None,
        crop_padding: int = 10
    ) -> Dict[str, Any]:
        """
        YOLO detection sonuçlarını OCR ile işle
        
        Args:
            detection_result: YOLO detector'dan gelen sonuç
            image_path: Orijinal görüntü yolu (kırpma için)
            crop_padding: Kırpma için padding (piksel)
            
        Returns:
            OCR sonuçları ile zenginleştirilmiş detection
        """
        from services.yolo_question_detector import get_question_detector
        
        # Orijinal görüntüyü yükle
        if image_path:
            original_image = self._load_image(image_path)
        elif 'image_path' in detection_result:
            original_image = self._load_image(detection_result['image_path'])
        else:
            raise ValueError("Image path required for YOLO detection processing")
        
        # YOLO detector'dan kırpılmış soruları al
        detector = get_question_detector()
        
        results = {
            'questions': [],
            'metadata': {},
            'processing_time_ms': 0
        }
        
        import time
        start_time = time.time()
        
        # Her detection için OCR çalıştır
        detections = detection_result.get('detections', [])
        
        tasks = []
        for det in detections:
            class_name = det.get('class_name', '')
            bbox = det.get('bbox', {})
            
            # Bounding box'tan kırp
            x1 = max(0, int(bbox.get('x1', 0)) - crop_padding)
            y1 = max(0, int(bbox.get('y1', 0)) - crop_padding)
            x2 = min(original_image.shape[1], int(bbox.get('x2', 0)) + crop_padding)
            y2 = min(original_image.shape[0], int(bbox.get('y2', 0)) + crop_padding)
            
            cropped = original_image[y1:y2, x1:x2]
            
            if class_name == 'soru':
                # Soru için tam OCR
                tasks.append(('question', cropped, det))
            elif class_name in ['konu', 'kitap', 'test_no', 'sayfa']:
                # Metadata için basit OCR
                tasks.append(('metadata', cropped, det))
        
        # Paralel OCR
        for task_type, cropped, det in tasks:
            try:
                if task_type == 'question':
                    ocr_result = await self.process_question_async(cropped)
                    results['questions'].append({
                        'detection': det,
                        'ocr': asdict(ocr_result) if ocr_result else None
                    })
                else:
                    # Metadata için basit text extraction
                    ocr_result = await self.extract_text_async(cropped)
                    class_name = det.get('class_name', 'unknown')
                    results['metadata'][class_name] = ocr_result.text
                    
            except Exception as e:
                logger.error(f"OCR error for detection: {e}")
        
        results['processing_time_ms'] = (time.time() - start_time) * 1000
        
        return results
    
    async def batch_process(
        self,
        images: List[Union[str, Path, bytes, np.ndarray]],
        max_concurrent: int = 5
    ) -> List[OCRResult]:
        """
        Batch görüntü işleme
        
        Args:
            images: Görüntü listesi
            max_concurrent: Maksimum eşzamanlı işlem
            
        Returns:
            OCRResult listesi
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(img):
            async with semaphore:
                return await self.extract_text_async(img)
        
        tasks = [process_with_semaphore(img) for img in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Exception'ları handle et
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch OCR error for image {i}: {result}")
                processed.append(OCRResult(
                    text="",
                    raw_text="",
                    confidence=0.0,
                    boxes=[],
                    engine=self.primary_engine.value,
                    language=','.join(self.languages),
                    processing_time_ms=0,
                    metadata={"error": str(result)}
                ))
            else:
                processed.append(result)
        
        return processed
    
    def get_info(self) -> Dict[str, Any]:
        """Servis bilgilerini döndür"""
        return {
            "primary_engine": self.primary_engine.value,
            "fallback_engine": self.fallback_engine.value,
            "use_gpu": self.use_gpu,
            "languages": self.languages,
            "loaded_engines": [e.value for e in self._engines.keys()],
            "supported_engines": [e.value for e in OCREngine]
        }


# ============================================================
# Singleton Instance
# ============================================================

_ocr_service_instance: Optional[UnifiedOCRService] = None


def get_ocr_service(
    primary_engine: OCREngine = OCREngine.EASYOCR,
    **kwargs
) -> UnifiedOCRService:
    """
    Singleton OCR service instance
    
    Args:
        primary_engine: Primary OCR engine
        **kwargs: Additional arguments for UnifiedOCRService
        
    Returns:
        UnifiedOCRService instance
    """
    global _ocr_service_instance
    
    if _ocr_service_instance is None:
        _ocr_service_instance = UnifiedOCRService(
            primary_engine=primary_engine,
            **kwargs
        )
    
    return _ocr_service_instance


# ============================================================
# Convenience Functions
# ============================================================

def extract_text(
    image: Union[str, Path, bytes, np.ndarray],
    engine: OCREngine = None
) -> OCRResult:
    """Convenience function for text extraction"""
    return get_ocr_service().extract_text(image, engine)


async def extract_text_async(
    image: Union[str, Path, bytes, np.ndarray],
    engine: OCREngine = None
) -> OCRResult:
    """Convenience function for async text extraction"""
    return await get_ocr_service().extract_text_async(image, engine)


def process_question(
    image: Union[str, Path, bytes, np.ndarray],
    engine: OCREngine = None
) -> QuestionOCRResult:
    """Convenience function for question processing"""
    return get_ocr_service().process_question(image, engine)


async def process_question_async(
    image: Union[str, Path, bytes, np.ndarray],
    engine: OCREngine = None
) -> QuestionOCRResult:
    """Convenience function for async question processing"""
    return await get_ocr_service().process_question_async(image, engine)
