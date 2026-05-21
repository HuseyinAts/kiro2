"""
KIRO2 YOLO Question Detector Service
=====================================
YOLO11 tabanlı soru tespit servisi.
Sınav sayfalarından soruları, cevapları ve metadata'yı otomatik tespit eder.

Sınıflar:
- soru: Soru blokları
- cevaplar: Cevap anahtarı
- zorluk_seviyesi: Zorluk göstergesi
- kitap: Kaynak kitap
- test_no: Test numarası
- sayfa: Sayfa numarası

Model: YOLO11m (mAP@50: 97.5%)
"""

import asyncio
import io
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# PIL for image processing
from PIL import Image

logger = logging.getLogger(__name__)


class DetectionClass(Enum):
    """Tespit edilebilen sınıflar (YOLO11x trained model)"""
    SORU = 0
    KONU = 1
    CEVAPLAR = 2
    TEST_NO = 3
    SAYFA = 4
    COZUM = 5
    KITAP = 6


@dataclass
class BoundingBox:
    """Tespit edilen nesne için bounding box"""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @property
    def area(self) -> int:
        return self.width * self.height

    def to_dict(self) -> dict[str, int]:
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "width": self.width,
            "height": self.height
        }


@dataclass
class Detection:
    """Tek bir tespit sonucu"""
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox.to_dict()
        }


@dataclass
class PageDetectionResult:
    """Sayfa tespit sonucu"""
    image_path: str | None
    image_width: int
    image_height: int
    detections: list[Detection]
    questions: list[Detection]
    metadata: dict[str, Any]
    processing_time_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_path": self.image_path,
            "image_size": {
                "width": self.image_width,
                "height": self.image_height
            },
            "total_detections": len(self.detections),
            "questions_count": len(self.questions),
            "detections": [d.to_dict() for d in self.detections],
            "questions": [q.to_dict() for q in self.questions],
            "metadata": self.metadata,
            "processing_time_ms": round(self.processing_time_ms, 2)
        }


class YOLOQuestionDetector:
    """
    YOLO11 tabanlı soru tespit servisi.
    
    Kullanım:
        detector = YOLOQuestionDetector()
        result = detector.detect("sayfa.png")
        
        # Async kullanım
        result = await detector.detect_async("sayfa.png")
    """

    CLASS_NAMES = {
        0: "soru",
        1: "konu",
        2: "cevaplar",
        3: "test_no",
        4: "sayfa",
        5: "cozum",
        6: "kitap"
    }

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "auto"
    ):
        """
        Args:
            model_path: YOLO model dosyası yolu (varsayılan: models/yolo11_best.pt)
            confidence_threshold: Minimum güven eşiği (0-1)
            iou_threshold: NMS için IoU eşiği
            device: "cpu", "cuda", "mps" veya "auto"
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None
        self._executor = ThreadPoolExecutor(max_workers=2)

        # Model yolu
        if model_path is None:
            # Proje kök dizinini bul
            backend_dir = Path(__file__).parent.parent
            project_root = backend_dir.parent
            model_path = project_root / "models" / "yolo11_best.pt"

        self.model_path = Path(model_path)

        # Model'i lazy load et
        self._model_loaded = False

    def _load_model(self) -> None:
        """YOLO modelini yükle (lazy loading)"""
        if self._model_loaded:
            return

        try:
            from ultralytics import YOLO

            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"YOLO model bulunamadı: {self.model_path}\n"
                    "Lütfen modeli 'models/yolo11_best.pt' konumuna kopyalayın."
                )

            logger.info(f"YOLO model yükleniyor: {self.model_path}")
            self.model = YOLO(str(self.model_path))

            # Device ayarı
            if self.device == "auto":
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"

            logger.info(f"YOLO model yüklendi. Device: {self.device}")
            self._model_loaded = True

        except ImportError:
            raise ImportError(
                "Ultralytics kütüphanesi bulunamadı. "
                "Lütfen 'pip install ultralytics' komutunu çalıştırın."
            )

    def detect(
        self,
        image_source: str | Path | Image.Image | bytes,
        save_result: bool = False,
        output_dir: str | None = None
    ) -> PageDetectionResult:
        """
        Görsel üzerinde soru tespiti yap.
        
        Args:
            image_source: Görsel dosya yolu, PIL Image veya bytes
            save_result: Sonucu görsel olarak kaydet
            output_dir: Kayıt dizini
            
        Returns:
            PageDetectionResult: Tespit sonuçları
        """
        import time
        start_time = time.time()

        # Model yükle
        self._load_model()

        # Görsel yükle
        image_path = None
        if isinstance(image_source, (str, Path)):
            image_path = str(image_source)
            image = Image.open(image_source)
        elif isinstance(image_source, bytes):
            image = Image.open(io.BytesIO(image_source))
        elif isinstance(image_source, Image.Image):
            image = image_source
        else:
            raise ValueError(f"Desteklenmeyen görsel türü: {type(image_source)}")

        img_width, img_height = image.size

        # YOLO inference
        results = self.model.predict(
            source=image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False,
            save=save_result,
            project=output_dir if save_result else None
        )

        # Sonuçları parse et
        detections = []
        questions = []
        metadata = {
            "kitap": None,
            "test_no": None,
            "sayfa": None,
            "konu": None,
            "cevaplar": None,
            "cozum": None
        }

        if results and len(results) > 0:
            result = results[0]

            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    class_name = self.CLASS_NAMES.get(class_id, f"unknown_{class_id}")

                    detection = Detection(
                        class_id=class_id,
                        class_name=class_name,
                        confidence=confidence,
                        bbox=BoundingBox(x1, y1, x2, y2)
                    )
                    detections.append(detection)

                    # Sınıflara göre ayır
                    if class_id == DetectionClass.SORU.value:
                        questions.append(detection)
                    elif class_id == DetectionClass.KONU.value:
                        metadata["konu"] = detection.to_dict()
                    elif class_id == DetectionClass.CEVAPLAR.value:
                        metadata["cevaplar"] = detection.to_dict()
                    elif class_id == DetectionClass.TEST_NO.value:
                        metadata["test_no"] = detection.to_dict()
                    elif class_id == DetectionClass.SAYFA.value:
                        metadata["sayfa"] = detection.to_dict()
                    elif class_id == DetectionClass.COZUM.value:
                        metadata["cozum"] = detection.to_dict()
                    elif class_id == DetectionClass.KITAP.value:
                        metadata["kitap"] = detection.to_dict()

        # Soruları y koordinatına göre sırala (yukarıdan aşağıya)
        questions.sort(key=lambda q: q.bbox.y1)

        processing_time = (time.time() - start_time) * 1000

        return PageDetectionResult(
            image_path=image_path,
            image_width=img_width,
            image_height=img_height,
            detections=detections,
            questions=questions,
            metadata=metadata,
            processing_time_ms=processing_time
        )

    async def detect_async(
        self,
        image_source: str | Path | Image.Image | bytes,
        save_result: bool = False,
        output_dir: str | None = None
    ) -> PageDetectionResult:
        """
        Async soru tespiti.
        
        Args:
            image_source: Görsel dosya yolu, PIL Image veya bytes
            save_result: Sonucu görsel olarak kaydet
            output_dir: Kayıt dizini
            
        Returns:
            PageDetectionResult: Tespit sonuçları
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.detect(image_source, save_result, output_dir)
        )

    def detect_batch(
        self,
        image_sources: list[str | Path],
        save_results: bool = False,
        output_dir: str | None = None
    ) -> list[PageDetectionResult]:
        """
        Birden fazla görsel için toplu tespit.
        
        Args:
            image_sources: Görsel dosya yolları listesi
            save_results: Sonuçları kaydet
            output_dir: Kayıt dizini
            
        Returns:
            List[PageDetectionResult]: Tespit sonuçları listesi
        """
        results = []
        for source in image_sources:
            try:
                result = self.detect(source, save_results, output_dir)
                results.append(result)
            except Exception as e:
                logger.error(f"Tespit hatası ({source}): {e}", exc_info=True)
                # Hatalı görsel için boş sonuç
                results.append(PageDetectionResult(
                    image_path=str(source),
                    image_width=0,
                    image_height=0,
                    detections=[],
                    questions=[],
                    metadata={},
                    processing_time_ms=0
                ))

        return results

    async def detect_batch_async(
        self,
        image_sources: list[str | Path],
        save_results: bool = False,
        output_dir: str | None = None
    ) -> list[PageDetectionResult]:
        """
        Async toplu tespit.
        """
        tasks = [
            self.detect_async(source, save_results, output_dir)
            for source in image_sources
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def crop_questions(
        self,
        image_source: str | Path | Image.Image,
        result: PageDetectionResult | None = None,
        padding: int = 10
    ) -> list[tuple[Image.Image, Detection]]:
        """
        Tespit edilen soruları kırp.
        
        Args:
            image_source: Kaynak görsel
            result: Önceden yapılmış tespit sonucu (yoksa yeniden tespit edilir)
            padding: Kenar boşluğu (piksel)
            
        Returns:
            List[Tuple[Image, Detection]]: Kırpılmış görsel ve tespit bilgisi
        """
        # Görseli yükle
        if isinstance(image_source, (str, Path)):
            image = Image.open(image_source)
        else:
            image = image_source

        # Tespit yap
        if result is None:
            result = self.detect(image)

        cropped = []
        for question in result.questions:
            bbox = question.bbox

            # Padding ekle
            x1 = max(0, bbox.x1 - padding)
            y1 = max(0, bbox.y1 - padding)
            x2 = min(image.width, bbox.x2 + padding)
            y2 = min(image.height, bbox.y2 + padding)

            cropped_img = image.crop((x1, y1, x2, y2))
            cropped.append((cropped_img, question))

        return cropped

    def get_model_info(self) -> dict[str, Any]:
        """Model bilgilerini döndür"""
        self._load_model()

        return {
            "model_path": str(self.model_path),
            "model_loaded": self._model_loaded,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "classes": self.CLASS_NAMES,
            "num_classes": len(self.CLASS_NAMES)
        }


# Singleton instance
_detector_instance: YOLOQuestionDetector | None = None


def get_question_detector(
    model_path: str | None = None,
    confidence_threshold: float = 0.25,
    **kwargs
) -> YOLOQuestionDetector:
    """
    Singleton YOLO detector instance döndür.
    
    Args:
        model_path: Model dosya yolu
        confidence_threshold: Güven eşiği
        
    Returns:
        YOLOQuestionDetector: Detector instance
    """
    global _detector_instance

    if _detector_instance is None:
        _detector_instance = YOLOQuestionDetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            **kwargs
        )

    return _detector_instance


# Convenience functions
def detect_questions(
    image_source: str | Path | Image.Image | bytes,
    confidence: float = 0.25
) -> PageDetectionResult:
    """
    Kısa yol fonksiyonu - görsel üzerinde soru tespiti.
    
    Args:
        image_source: Görsel kaynağı
        confidence: Güven eşiği
        
    Returns:
        PageDetectionResult: Tespit sonuçları
    """
    detector = get_question_detector(confidence_threshold=confidence)
    return detector.detect(image_source)


async def detect_questions_async(
    image_source: str | Path | Image.Image | bytes,
    confidence: float = 0.25
) -> PageDetectionResult:
    """
    Async kısa yol fonksiyonu.
    """
    detector = get_question_detector(confidence_threshold=confidence)
    return await detector.detect_async(image_source)
