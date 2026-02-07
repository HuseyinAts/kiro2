#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 Soru Çıkarma Pipeline
===========================
YOLO tespit + Surya OCR + Soru-Cevap Eşleştirme

Kullanım:
    python extract_questions.py --input kitap.pdf --output sorular.json

Gereksinimler:
    pip install ultralytics surya-ocr pillow pdf2image
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# VERİ YAPILARI
# ============================================================================

@dataclass
class BoundingBox:
    """Tespit edilen bölge"""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str

@dataclass
class Question:
    """Çıkarılan soru"""
    number: int
    text: str
    options: List[str]
    correct_answer: Optional[str]
    topic: Optional[str]
    difficulty: Optional[str]
    page: int
    bbox: Dict
    raw_ocr: str

@dataclass
class PageResult:
    """Sayfa işleme sonucu"""
    page_number: int
    test_number: Optional[str]
    topic: Optional[str]
    questions: List[Question]
    answer_key: Dict[int, str]
    raw_detections: List[BoundingBox]

# ============================================================================
# YOLO TESPİT MODÜLÜ
# ============================================================================

class YOLODetector:
    """YOLO tabanlı nesne tespiti"""
    
    CLASS_NAMES = {
        0: 'soru',
        1: 'konu',
        2: 'cevaplar',
        3: 'test_no',
        4: 'sayfa',
        5: 'cozum',
        6: 'kitap'
    }
    
    def __init__(self, model_path: str):
        """
        Args:
            model_path: Eğitilmiş YOLO model dosyası (.pt)
        """
        from ultralytics import YOLO
        self.model = YOLO(model_path)
        logger.info(f"YOLO model yüklendi: {model_path}")
    
    def detect(self, image: Image.Image, conf_threshold: float = 0.5) -> List[BoundingBox]:
        """
        Görüntüde nesne tespiti yap
        
        Args:
            image: PIL Image
            conf_threshold: Minimum güven eşiği
            
        Returns:
            Tespit edilen bounding box listesi
        """
        results = self.model(image, conf=conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                
                detections.append(BoundingBox(
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    confidence=conf,
                    class_id=class_id,
                    class_name=self.CLASS_NAMES.get(class_id, f'unknown_{class_id}')
                ))
        
        # Y pozisyonuna göre sırala (yukarıdan aşağıya)
        detections.sort(key=lambda d: (d.y1, d.x1))
        
        logger.info(f"Tespit edilen bölge sayısı: {len(detections)}")
        return detections

# ============================================================================
# OCR MODÜLÜ
# ============================================================================

class SuryaOCR:
    """Surya OCR entegrasyonu"""
    
    def __init__(self, langs: List[str] = ["tr", "en"]):
        """
        Args:
            langs: OCR dilleri
        """
        from surya.ocr import run_ocr
        from surya.model.detection.model import load_model as load_det_model
        from surya.model.detection.processor import load_processor as load_det_processor
        from surya.model.recognition.model import load_model as load_rec_model
        from surya.model.recognition.processor import load_processor as load_rec_processor
        
        logger.info("Surya modelleri yükleniyor...")
        
        self.det_model = load_det_model()
        self.det_processor = load_det_processor()
        self.rec_model = load_rec_model()
        self.rec_processor = load_rec_processor()
        self.langs = langs
        self.run_ocr = run_ocr
        
        logger.info("Surya OCR hazır")
    
    def extract_text(self, image: Image.Image) -> str:
        """
        Görüntüden metin çıkar
        
        Args:
            image: PIL Image
            
        Returns:
            Çıkarılan metin
        """
        results = self.run_ocr(
            [image],
            [self.langs],
            self.det_model,
            self.det_processor,
            self.rec_model,
            self.rec_processor
        )
        
        if not results or not results[0].text_lines:
            return ""
        
        # Satırları birleştir
        lines = [line.text for line in results[0].text_lines]
        return "\n".join(lines)
    
    def extract_from_region(self, image: Image.Image, bbox: BoundingBox) -> str:
        """
        Belirli bir bölgeden metin çıkar
        
        Args:
            image: Tam sayfa görüntüsü
            bbox: Kırpılacak bölge
            
        Returns:
            Bölgeden çıkarılan metin
        """
        # Bölgeyi kırp
        cropped = image.crop((int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)))
        return self.extract_text(cropped)

# ============================================================================
# SORU PARSER MODÜLÜ
# ============================================================================

class QuestionParser:
    """Soru metni ayrıştırıcı"""
    
    # Soru numarası desenleri
    QUESTION_NUM_PATTERNS = [
        r'^(\d+)\s*[.)\-]\s*',           # 1. veya 1) veya 1-
        r'^Soru\s*(\d+)\s*[.:\-]?\s*',   # Soru 1:
        r'^\((\d+)\)\s*',                 # (1)
    ]
    
    # Seçenek desenleri
    OPTION_PATTERNS = [
        r'^([A-E])\s*[.)\-]\s*(.+)$',    # A) veya A. veya A-
        r'^\(([A-E])\)\s*(.+)$',          # (A)
    ]
    
    # Cevap anahtarı desenleri
    ANSWER_KEY_PATTERNS = [
        r'(\d+)\s*[.:\-]\s*([A-E])',     # 1.A veya 1:A veya 1-A
        r'(\d+)\s*=\s*([A-E])',           # 1=A
        r'(\d+)\s+([A-E])(?:\s|$)',       # 1 A
    ]
    
    def parse_question_text(self, raw_text: str) -> Tuple[Optional[int], str, List[str]]:
        """
        Ham OCR metninden soru numarası, metin ve seçenekleri çıkar
        
        Returns:
            (soru_no, soru_metni, seçenekler)
        """
        lines = raw_text.strip().split('\n')
        if not lines:
            return None, "", []
        
        # Soru numarasını bul
        question_num = None
        first_line = lines[0].strip()
        
        for pattern in self.QUESTION_NUM_PATTERNS:
            match = re.match(pattern, first_line, re.IGNORECASE)
            if match:
                question_num = int(match.group(1))
                first_line = re.sub(pattern, '', first_line, flags=re.IGNORECASE).strip()
                break
        
        # Seçenekleri ayır
        question_lines = []
        options = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Seçenek mi kontrol et
            is_option = False
            for pattern in self.OPTION_PATTERNS:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    option_letter = match.group(1)
                    option_text = match.group(2).strip()
                    options.append(f"{option_letter}) {option_text}")
                    is_option = True
                    break
            
            if not is_option and not any(line.startswith(p) for p in ['A)', 'B)', 'C)', 'D)', 'E)']):
                question_lines.append(line)
        
        question_text = ' '.join(question_lines)
        
        # Soru numarasını temizle
        if question_num is None and question_text:
            for pattern in self.QUESTION_NUM_PATTERNS:
                match = re.match(pattern, question_text)
                if match:
                    question_num = int(match.group(1))
                    question_text = re.sub(pattern, '', question_text).strip()
                    break
        
        return question_num, question_text, options
    
    def parse_answer_key(self, raw_text: str) -> Dict[int, str]:
        """
        Cevap anahtarı metninden soru-cevap eşleşmelerini çıkar
        
        Returns:
            {soru_no: cevap} sözlüğü
        """
        answers = {}
        
        for pattern in self.ANSWER_KEY_PATTERNS:
            matches = re.findall(pattern, raw_text)
            for match in matches:
                q_num = int(match[0])
                answer = match[1].upper()
                if answer in 'ABCDE':
                    answers[q_num] = answer
        
        return answers

# ============================================================================
# ANA PIPELINE
# ============================================================================

class KIRO2Extractor:
    """KIRO2 Soru Çıkarma Ana Pipeline"""
    
    def __init__(self, yolo_model_path: str, use_surya: bool = True):
        """
        Args:
            yolo_model_path: YOLO model dosya yolu
            use_surya: Surya OCR kullan (False ise sadece tespit)
        """
        self.detector = YOLODetector(yolo_model_path)
        self.ocr = SuryaOCR() if use_surya else None
        self.parser = QuestionParser()
        
        logger.info("KIRO2 Extractor başlatıldı")
    
    def process_image(self, image: Image.Image, page_number: int = 1) -> PageResult:
        """
        Tek bir sayfa görüntüsünü işle
        
        Args:
            image: Sayfa görüntüsü
            page_number: Sayfa numarası
            
        Returns:
            PageResult
        """
        # 1. YOLO ile bölgeleri tespit et
        detections = self.detector.detect(image)
        
        # 2. Bölgeleri sınıflandır
        questions = []
        answer_key = {}
        topic = None
        test_number = None
        
        for det in detections:
            if self.ocr is None:
                continue
                
            # Bölgeden metin çıkar
            text = self.ocr.extract_from_region(image, det)
            
            if det.class_name == 'soru':
                q_num, q_text, options = self.parser.parse_question_text(text)
                
                if q_num is not None:
                    questions.append(Question(
                        number=q_num,
                        text=q_text,
                        options=options,
                        correct_answer=None,
                        topic=topic,
                        difficulty=None,
                        page=page_number,
                        bbox=asdict(det),
                        raw_ocr=text
                    ))
            
            elif det.class_name == 'cevaplar':
                page_answers = self.parser.parse_answer_key(text)
                answer_key.update(page_answers)
            
            elif det.class_name == 'konu':
                topic = text.strip()
            
            elif det.class_name == 'test_no':
                test_number = text.strip()
        
        # 3. Cevapları sorularla eşleştir
        for q in questions:
            if q.number in answer_key:
                q.correct_answer = answer_key[q.number]
            if topic and not q.topic:
                q.topic = topic
        
        return PageResult(
            page_number=page_number,
            test_number=test_number,
            topic=topic,
            questions=questions,
            answer_key=answer_key,
            raw_detections=detections
        )
    
    def process_pdf(self, pdf_path: str, output_path: Optional[str] = None) -> List[PageResult]:
        """
        PDF dosyasını işle
        
        Args:
            pdf_path: PDF dosya yolu
            output_path: JSON çıktı yolu (opsiyonel)
            
        Returns:
            Tüm sayfaların sonuçları
        """
        from pdf2image import convert_from_path
        
        logger.info(f"PDF işleniyor: {pdf_path}")
        
        # PDF'i görüntülere çevir
        images = convert_from_path(pdf_path, dpi=200)
        logger.info(f"Toplam sayfa: {len(images)}")
        
        results = []
        all_questions = []
        global_answer_key = {}
        
        for i, image in enumerate(images):
            page_num = i + 1
            logger.info(f"Sayfa {page_num}/{len(images)} işleniyor...")
            
            result = self.process_image(image, page_num)
            results.append(result)
            
            # Global istatistikler
            all_questions.extend(result.questions)
            global_answer_key.update(result.answer_key)
        
        # Tüm cevapları sorualarla eşleştir (kitap sonu cevap anahtarı için)
        for q in all_questions:
            if q.correct_answer is None and q.number in global_answer_key:
                q.correct_answer = global_answer_key[q.number]
        
        # Sonuçları kaydet
        if output_path:
            self._save_results(results, output_path)
        
        # İstatistikler
        matched = sum(1 for q in all_questions if q.correct_answer)
        logger.info(f"\n📊 İşlem Özeti:")
        logger.info(f"  Toplam sayfa: {len(results)}")
        logger.info(f"  Toplam soru: {len(all_questions)}")
        logger.info(f"  Eşleşen soru-cevap: {matched} (%{100*matched/len(all_questions) if all_questions else 0:.1f})")
        
        return results
    
    def process_folder(self, folder_path: str, output_path: str) -> List[PageResult]:
        """
        Klasördeki tüm görüntüleri işle
        
        Args:
            folder_path: Görüntü klasörü
            output_path: JSON çıktı yolu
            
        Returns:
            Tüm sayfaların sonuçları
        """
        folder = Path(folder_path)
        image_files = sorted(
            list(folder.glob('*.png')) + 
            list(folder.glob('*.jpg')) + 
            list(folder.glob('*.jpeg'))
        )
        
        logger.info(f"Klasör işleniyor: {folder_path}")
        logger.info(f"Toplam görüntü: {len(image_files)}")
        
        results = []
        
        for i, img_path in enumerate(image_files):
            page_num = i + 1
            logger.info(f"Görüntü {page_num}/{len(image_files)}: {img_path.name}")
            
            image = Image.open(img_path)
            result = self.process_image(image, page_num)
            results.append(result)
        
        self._save_results(results, output_path)
        return results
    
    def _save_results(self, results: List[PageResult], output_path: str):
        """Sonuçları JSON olarak kaydet"""
        output = {
            'total_pages': len(results),
            'total_questions': sum(len(r.questions) for r in results),
            'pages': []
        }
        
        for result in results:
            page_data = {
                'page_number': result.page_number,
                'test_number': result.test_number,
                'topic': result.topic,
                'question_count': len(result.questions),
                'questions': [asdict(q) for q in result.questions]
            }
            output['pages'].append(page_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Sonuçlar kaydedildi: {output_path}")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='KIRO2 Soru Çıkarma Pipeline')
    
    parser.add_argument('--model', type=str, required=True,
                       help='YOLO model dosyası (.pt)')
    parser.add_argument('--input', type=str, required=True,
                       help='Giriş dosyası (PDF) veya klasör')
    parser.add_argument('--output', type=str, required=True,
                       help='Çıktı JSON dosyası')
    parser.add_argument('--no-ocr', action='store_true',
                       help='OCR kullanma (sadece tespit)')
    
    args = parser.parse_args()
    
    # Pipeline oluştur
    extractor = KIRO2Extractor(
        yolo_model_path=args.model,
        use_surya=not args.no_ocr
    )
    
    # Giriş türünü belirle ve işle
    input_path = Path(args.input)
    
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        extractor.process_pdf(str(input_path), args.output)
    elif input_path.is_dir():
        extractor.process_folder(str(input_path), args.output)
    else:
        # Tek görüntü
        image = Image.open(input_path)
        result = extractor.process_image(image, 1)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
