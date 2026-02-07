import asyncio
from pathlib import Path
from typing import List, Dict
import json
import logging
from datetime import datetime

from .yolo_detector import YKSQuestionDetector
from .gemini_ocr import GeminiOCRService

logger = logging.getLogger(__name__)

class YKSQuestionPipeline:
    """
    Tezdeki pipeline'ı takip eden ana işlem hattı:
    1. YOLO ile nesne tespiti
    2. Gemini ile OCR
    3. Veri birleştirme ve kayıt
    """

    def __init__(self, yolo_model_path: str = None, gemini_api_key: str = None):
        """
        Pipeline'ı başlat
        """
        self.detector = YKSQuestionDetector(yolo_model_path)
        self.ocr = GeminiOCRService(gemini_api_key)

        # Çıktı dizini
        self.output_dir = Path("backend/services/question_parser/outputs")
        self.output_dir.mkdir(exist_ok=True, parents=True)

        logger.info("YKS Question Pipeline initialized")

    async def process_test_page(self, image_path: str) -> Dict:
        """
        Tek bir test sayfasını işle

        Args:
            image_path: Test sayfası görüntüsü

        Returns:
            İşlenmiş veri
        """
        image_path = Path(image_path)

        # 1. YOLO ile nesneleri tespit et
        logger.info(f"Processing: {image_path}")
        detections = self.detector.detect_objects(str(image_path), use_tiling=True)

        # 2. Tespit edilen bölgeleri kırp
        detections = self.detector.crop_detections(str(image_path), detections)

        # 3. Tespitleri kategorize et
        questions = []
        metadata = {}

        for det in detections:
            if det.label == 'question':
                questions.append(det)
            else:
                metadata[det.label] = det

        # 4. OCR uygula
        results = {
            'file': str(image_path),
            'processed_at': datetime.now().isoformat(),
            'questions': [],
            'metadata': {}
        }

        # Metadata OCR
        for label, det in metadata.items():
            if det.cropped_image is not None:
                text = await self.ocr.extract_metadata(det.cropped_image, label)
                results['metadata'][label] = text

        # Soru OCR
        for i, q_det in enumerate(questions):
            if q_det.cropped_image is not None:
                q_data = await self.ocr.extract_question(q_det.cropped_image)
                if q_data:
                    # Metadata ekle
                    q_data['subject'] = results['metadata'].get('subject', '')
                    q_data['topic'] = results['metadata'].get('topic', '')
                    q_data['test_id'] = results['metadata'].get('test_identifier', '')
                    q_data['page_number'] = int(results['metadata'].get('page_number', 0)) if results['metadata'].get('page_number', '').isdigit() else 0
                    q_data['bbox'] = q_det.bbox
                    q_data['confidence'] = q_det.confidence

                    results['questions'].append(q_data)

        # 5. Sonuçları kaydet
        output_file = self.output_dir / f"{image_path.stem}_processed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"Processed {len(results['questions'])} questions from {image_path.name}")

        return results

    async def process_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Birden fazla test sayfasını işle

        Args:
            image_paths: Test sayfası görüntüleri listesi

        Returns:
            İşlenmiş veriler
        """
        tasks = []
        for path in image_paths:
            task = self.process_test_page(path)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Tüm sonuçları birleştir
        all_questions = []
        for result in results:
            all_questions.extend(result['questions'])

        # Ana çıktı dosyası
        output_file = self.output_dir / f"batch_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_questions': len(all_questions),
                'processed_files': len(results),
                'questions': all_questions,
                'results': results
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"Batch processing complete: {len(all_questions)} total questions")

        return results

    def extract_answer_sheet(self, image_path: str) -> Dict[str, str]:
        """
        Cevap anahtarını çıkar (manuel kontrol gerekebilir)

        Args:
            image_path: Cevap anahtarı görüntüsü

        Returns:
            Soru numarası -> cevap eşleşmesi
        """
        # Bu kısım tezde belirtildiği gibi manuel yapılabilir
        # veya özel bir OCR modeli eğitilebilir

        logger.warning("Cevap anahtarı çıkarma henüz otomatik değil, manuel kontrol gerekli")
        return {}
