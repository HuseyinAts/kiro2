import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """Tespit edilen nesne için sonuç sınıfı"""
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    cropped_image: np.ndarray | None = None

class YKSQuestionDetector:
    """
    Tezdeki yaklaşımı takip eden YOLO tabanlı soru tespit sistemi
    Etiketler: question, topic, subject, test_identifier, page_number, answer_sheet
    """

    LABELS = {
        0: 'question',
        1: 'topic',
        2: 'subject',
        3: 'test_identifier',
        4: 'page_number',
        5: 'answer_sheet'
    }

    def __init__(self, model_path: str = None):
        """
        Args:
            model_path: Eğitilmiş YOLO model dosyası yolu
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # Model yolu verilmediyse yeni model başlat (eğitim için)
        if model_path and Path(model_path).exists():
            self.model = YOLO(model_path)
        else:
            # YOLOv8 kullanıyoruz (tezde v12 var ama v8 daha stabil)
            try:
                self.model = YOLO('yolov8x.pt')  # Pretrained model
            except (FileNotFoundError, OSError, RuntimeError) as e:
                logger.warning(f"YOLOv8x model yüklenemedi ({e}), küçük model indiriliyor...")
                self.model = YOLO('yolov8n.pt')  # Daha küçük model

        logger.info(f"YOLO model loaded on {self.device}")

    def prepare_image(self, image_path: str, target_size: int = 640) -> np.ndarray:
        """
        Tezdeki yaklaşım: 640x640 resize + 3x3 tiling

        Args:
            image_path: Görüntü dosyası yolu
            target_size: Hedef boyut (tezde 640x640)

        Returns:
            İşlenmiş görüntü
        """
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Image not found: {image_path}")

        # Orijinal boyutları kaydet
        self.original_height, self.original_width = image.shape[:2]

        # 640x640'a yeniden boyutlandır
        resized = cv2.resize(image, (target_size, target_size))

        return resized

    def apply_tiling(self, image: np.ndarray, tile_size: int = 3) -> tuple:
        """
        3x3 tiling uygula (küçük nesneler için)

        Args:
            image: Giriş görüntüsü
            tile_size: Tile boyutu (3x3)

        Returns:
            Tile'lar listesi ve pozisyonları
        """
        h, w = image.shape[:2]
        tile_h = h // tile_size
        tile_w = w // tile_size

        tiles = []
        positions = []

        for i in range(tile_size):
            for j in range(tile_size):
                y1 = i * tile_h
                y2 = (i + 1) * tile_h if i < tile_size - 1 else h
                x1 = j * tile_w
                x2 = (j + 1) * tile_w if j < tile_size - 1 else w

                tile = image[y1:y2, x1:x2]
                tiles.append(tile)
                positions.append((x1, y1))

        return tiles, positions

    def detect_objects(self, image_path: str, use_tiling: bool = True) -> list[DetectionResult]:
        """
        Görüntüde nesneleri tespit et

        Args:
            image_path: Görüntü dosyası yolu
            use_tiling: 3x3 tiling kullanılsın mı

        Returns:
            Tespit edilen nesneler listesi
        """
        image = self.prepare_image(image_path)
        all_detections = []

        if use_tiling:
            # Tiling uygula
            tiles, positions = self.apply_tiling(image)

            for tile, (offset_x, offset_y) in zip(tiles, positions):
                results = self.model(tile, conf=0.25)

                for r in results:
                    if r.boxes is not None:
                        for box in r.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                            # Tile offset'lerini ekle
                            x1 += offset_x
                            y1 += offset_y
                            x2 += offset_x
                            y2 += offset_y

                            # Orijinal boyutlara geri dönüştür
                            scale_x = self.original_width / 640
                            scale_y = self.original_height / 640

                            x1 = int(x1 * scale_x)
                            y1 = int(y1 * scale_y)
                            x2 = int(x2 * scale_x)
                            y2 = int(y2 * scale_y)

                            label_id = int(box.cls[0])
                            label = self.LABELS.get(label_id, 'unknown')
                            confidence = float(box.conf[0])

                            detection = DetectionResult(
                                label=label,
                                confidence=confidence,
                                bbox=(x1, y1, x2, y2)
                            )
                            all_detections.append(detection)
        else:
            # Direkt tespit
            results = self.model(image, conf=0.25)

            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                        # Orijinal boyutlara dönüştür
                        scale_x = self.original_width / 640
                        scale_y = self.original_height / 640

                        x1 = int(x1 * scale_x)
                        y1 = int(y1 * scale_y)
                        x2 = int(x2 * scale_x)
                        y2 = int(y2 * scale_y)

                        label_id = int(box.cls[0])
                        label = self.LABELS.get(label_id, 'unknown')
                        confidence = float(box.conf[0])

                        detection = DetectionResult(
                            label=label,
                            confidence=confidence,
                            bbox=(x1, y1, x2, y2)
                        )
                        all_detections.append(detection)

        # NMS (Non-Maximum Suppression) uygula
        all_detections = self.apply_nms(all_detections)

        return all_detections

    def apply_nms(self, detections: list[DetectionResult], iou_threshold: float = 0.5) -> list[DetectionResult]:
        """
        Non-Maximum Suppression uygula
        """
        if not detections:
            return []

        # Label'lara göre grupla
        grouped = {}
        for det in detections:
            if det.label not in grouped:
                grouped[det.label] = []
            grouped[det.label].append(det)

        final_detections = []

        for label, dets in grouped.items():
            # Confidence'a göre sırala
            dets.sort(key=lambda x: x.confidence, reverse=True)

            kept = []
            for det in dets:
                keep = True
                for kept_det in kept:
                    if self.calculate_iou(det.bbox, kept_det.bbox) > iou_threshold:
                        keep = False
                        break
                if keep:
                    kept.append(det)

            final_detections.extend(kept)

        return final_detections

    def calculate_iou(self, box1: tuple, box2: tuple) -> float:
        """IoU hesapla"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        # Kesişim alanı
        x_inter_min = max(x1_min, x2_min)
        y_inter_min = max(y1_min, y2_min)
        x_inter_max = min(x1_max, x2_max)
        y_inter_max = min(y1_max, y2_max)

        if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
            return 0.0

        inter_area = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)

        # Birleşim alanı
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def crop_detections(self, image_path: str, detections: list[DetectionResult]) -> list[DetectionResult]:
        """
        Tespit edilen bölgeleri kırp
        """
        image = cv2.imread(str(image_path))

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            det.cropped_image = image[y1:y2, x1:x2]

        return detections
