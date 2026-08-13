"""
KIRO2 - Computer Vision for Exam Analytics System
Görsel Sınav Analitik Sistemi

Bu modül Türk üniversite giriş sınavları için gelişmiş bilgisayarlı görü analitik yetenekleri sağlar.
YKS, TYT, AYT sınavlarında görsel analiz, soru tanıma, cevap analizi ve öğrenci davranış analizi sunar.
"""

import asyncio
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import easyocr
import numpy as np
import torch
from tensorflow import keras


class ExamType(Enum):
    """Sınav türleri"""
    TYT = "tyt"  # Temel Yeterlilik Testi
    AYT = "ayt"  # Alan Yeterlilik Testi
    YKS = "yks"  # Yükseköğretim Kurumları Sınavı
    MOCK = "mock"  # Deneme sınavı

class AnalysisType(Enum):
    """Analiz türleri"""
    QUESTION_RECOGNITION = "question_recognition"
    ANSWER_DETECTION = "answer_detection"
    TEXT_EXTRACTION = "text_extraction"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    PERFORMANCE_TRACKING = "performance_tracking"
    CHEATING_DETECTION = "cheating_detection"
    HANDWRITING_ANALYSIS = "handwriting_analysis"

class QuestionType(Enum):
    """Soru türleri"""
    MULTIPLE_CHOICE = "multiple_choice"
    ESSAY = "essay"
    NUMERICAL = "numerical"
    MATCHING = "matching"
    TRUE_FALSE = "true_false"

@dataclass
class VisionResult:
    """Görsel analiz sonucu"""
    analysis_type: AnalysisType
    exam_type: ExamType
    confidence: float
    result_data: Dict[str, Any]
    processing_time: float
    timestamp: datetime

@dataclass
class QuestionDetection:
    """Soru tanıma sonucu"""
    question_id: str
    question_type: QuestionType
    bounding_box: Tuple[int, int, int, int]
    confidence: float
    text_content: str
    answer_options: List[str]
    correct_answer: Optional[str]

@dataclass
class AnswerDetection:
    """Cevap tanıma sonucu"""
    question_id: str
    selected_answer: str
    confidence: float
    bounding_box: Tuple[int, int, int, int]
    handwriting_quality: float
    erasure_detected: bool

@dataclass
class BehaviorAnalysis:
    """Davranış analizi sonucu"""
    student_id: str
    focus_score: float
    stress_indicators: List[str]
    time_spent_per_section: Dict[str, float]
    suspicious_activities: List[str]
    overall_behavior_score: float

class TurkishExamVisionAnalyzer:
    """Türk sınav sistemi için gelişmiş bilgisayarlı görü analiz motoru"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.ocr_readers = {}
        self.performance_cache = {}
        self.initialize_models()

        # Türkçe karakter desteği
        self.turkish_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZçÇğĞıİöÖşŞüÜ0123456789'

        # YKS/TYT/AYT sınav formatları
        self.exam_formats = {
            ExamType.TYT: {
                'sections': ['Türkçe', 'Matematik', 'Fen', 'Sosyal'],
                'question_counts': [40, 40, 20, 20],
                'time_limits': [75, 75, 45, 45]  # dakika
            },
            ExamType.AYT: {
                'sections': ['Matematik', 'Fen', 'Türk Dili', 'Sosyal', 'Yabancı Dil'],
                'question_counts': [40, 40, 24, 24, 80],
                'time_limits': [75, 75, 45, 45, 120]
            }
        }

    def initialize_models(self):
        """AI modellerini ve OCR sistemlerini başlatır"""
        try:
            # OCR sistemleri
            self.ocr_readers['turkish'] = easyocr.Reader(['tr', 'en'])
            self.ocr_readers['english'] = easyocr.Reader(['en'])

            # Önceden eğitilmiş modeller
            self._load_question_detection_model()
            self._load_answer_detection_model()
            self._load_handwriting_analysis_model()
            self._load_behavior_analysis_model()

            self.logger.info("Tüm AI modelleri başarıyla yüklendi")

        except Exception as e:
            self.logger.error(f"Model yükleme hatası: {str(e)}")
            raise

    def _load_question_detection_model(self):
        """Soru tanıma modelini yükler"""
        # Özel eğitilmiş YOLO modeli
        model_path = "models/question_detection_yolo.pt"
        if Path(model_path).exists():
            self.models['question_detection'] = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        else:
            # Varsayılan model
            self.models['question_detection'] = torch.hub.load('ultralytics/yolov5', 'yolov5s')

    def _load_answer_detection_model(self):
        """Cevap tanıma modelini yükler"""
        model_config = {
            'input_shape': (224, 224, 3),
            'num_classes': 5,  # A, B, C, D, E seçenekleri
            'architecture': 'ResNet50'
        }

        # Keras modeli oluştur
        base_model = keras.applications.ResNet50(
            weights='imagenet',
            include_top=False,
            input_shape=model_config['input_shape']
        )

        model = keras.Sequential([
            base_model,
            keras.layers.GlobalAveragePooling2D(),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(model_config['num_classes'], activation='softmax')
        ])

        self.models['answer_detection'] = model

    def _load_handwriting_analysis_model(self):
        """El yazısı analiz modelini yükler"""
        # CNN-LSTM modeli el yazısı kalitesi için
        model = keras.Sequential([
            keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(128, 32, 1)),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.Flatten(),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')  # Kalite skoru 0-1
        ])

        self.models['handwriting_analysis'] = model

    def _load_behavior_analysis_model(self):
        """Davranış analizi modelini yükler"""
        # Öğrenci davranış analizi için özel model
        self.models['behavior_analysis'] = {
            'face_detector': cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
            'eye_detector': cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml'),
            'pose_estimator': None  # MediaPipe veya benzeri
        }

    async def analyze_exam_document(
        self,
        image_path: str,
        exam_type: ExamType,
        analysis_types: List[AnalysisType]
    ) -> List[VisionResult]:
        """Sınav dokümanını kapsamlı analiz eder"""
        start_time = datetime.now()
        results = []

        try:
            # Görüntüyü yükle
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Görüntü yüklenemedi: {image_path}")

            # Paralel analiz için görevleri hazırla
            tasks = []
            for analysis_type in analysis_types:
                if analysis_type == AnalysisType.QUESTION_RECOGNITION:
                    tasks.append(self._analyze_questions(image, exam_type))
                elif analysis_type == AnalysisType.ANSWER_DETECTION:
                    tasks.append(self._detect_answers(image, exam_type))
                elif analysis_type == AnalysisType.TEXT_EXTRACTION:
                    tasks.append(self._extract_text(image))
                elif analysis_type == AnalysisType.HANDWRITING_ANALYSIS:
                    tasks.append(self._analyze_handwriting(image))

            # Paralel işlem
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Sonuçları birleştir
            for i, task_result in enumerate(task_results):
                if not isinstance(task_result, Exception):
                    analysis_type = analysis_types[i]
                    processing_time = (datetime.now() - start_time).total_seconds()

                    result = VisionResult(
                        analysis_type=analysis_type,
                        exam_type=exam_type,
                        confidence=task_result.get('confidence', 0.0),
                        result_data=task_result,
                        processing_time=processing_time,
                        timestamp=datetime.now()
                    )
                    results.append(result)
                else:
                    self.logger.error(f"Analiz hatası: {str(task_result)}")

            return results

        except Exception as e:
            self.logger.error(f"Doküman analiz hatası: {str(e)}")
            raise

    async def _analyze_questions(self, image: np.ndarray, exam_type: ExamType) -> Dict[str, Any]:
        """Soruları tanır ve analiz eder"""
        try:
            # Görüntü ön işleme
            processed_image = self._preprocess_image(image)

            # YOLO modeli ile soru tespiti
            detections = self.models['question_detection'](processed_image)

            questions = []
            for detection in detections.pandas().xyxy[0].values:
                x1, y1, x2, y2, confidence, class_id = detection

                if confidence > 0.5:  # Güven eşiği
                    # Soru bölgesini kırp
                    question_region = image[int(y1):int(y2), int(x1):int(x2)]

                    # OCR ile metin çıkar
                    text_content = await self._extract_text_from_region(question_region)

                    # Soru türünü belirle
                    question_type = self._classify_question_type(text_content)

                    # Cevap seçeneklerini tespit et
                    answer_options = self._extract_answer_options(text_content, question_type)

                    question = QuestionDetection(
                        question_id=f"q_{len(questions)+1}",
                        question_type=question_type,
                        bounding_box=(int(x1), int(y1), int(x2), int(y2)),
                        confidence=float(confidence),
                        text_content=text_content,
                        answer_options=answer_options,
                        correct_answer=None
                    )
                    questions.append(question)

            return {
                'questions': [q.__dict__ for q in questions],
                'total_questions': len(questions),
                'confidence': np.mean([q.confidence for q in questions]) if questions else 0.0,
                'exam_format_match': self._validate_exam_format(questions, exam_type)
            }

        except Exception as e:
            self.logger.error(f"Soru analiz hatası: {str(e)}")
            return {'error': str(e), 'confidence': 0.0}

    async def _detect_answers(self, image: np.ndarray, exam_type: ExamType) -> Dict[str, Any]:
        """Cevapları tespit eder ve analiz eder"""
        try:
            # Cevap alanlarını tespit et
            answer_regions = self._detect_answer_regions(image)

            answers = []
            for i, region in enumerate(answer_regions):
                x, y, w, h = region
                answer_area = image[y:y+h, x:x+w]

                # Cevap seçimi tespiti
                selected_answer = await self._classify_selected_answer(answer_area)

                # El yazısı kalitesi analizi
                handwriting_quality = await self._assess_handwriting_quality(answer_area)

                # Silinti tespiti
                erasure_detected = self._detect_erasures(answer_area)

                answer = AnswerDetection(
                    question_id=f"q_{i+1}",
                    selected_answer=selected_answer,
                    confidence=0.85,  # Model çıktısından gelecek
                    bounding_box=(x, y, x+w, y+h),
                    handwriting_quality=handwriting_quality,
                    erasure_detected=erasure_detected
                )
                answers.append(answer)

            return {
                'answers': [a.__dict__ for a in answers],
                'total_answers': len(answers),
                'confidence': np.mean([a.confidence for a in answers]) if answers else 0.0,
                'completion_rate': len([a for a in answers if a.selected_answer != 'BOŞŞ']) / len(answers) if answers else 0.0
            }

        except Exception as e:
            self.logger.error(f"Cevap tespit hatası: {str(e)}")
            return {'error': str(e), 'confidence': 0.0}

    async def _extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Görüntüden Türkçe metin çıkarır"""
        try:
            # OCR ile metin çıkarma
            results_turkish = self.ocr_readers['turkish'].readtext(image)
            results_english = self.ocr_readers['english'].readtext(image)

            # Sonuçları birleştir ve temizle
            all_text = []
            turkish_text = []
            english_text = []

            for result in results_turkish:
                bbox, text, confidence = result
                if confidence > 0.6:
                    all_text.append({
                        'text': text,
                        'bbox': bbox,
                        'confidence': confidence,
                        'language': 'turkish'
                    })
                    turkish_text.append(text)

            for result in results_english:
                bbox, text, confidence = result
                if confidence > 0.6:
                    all_text.append({
                        'text': text,
                        'bbox': bbox,
                        'confidence': confidence,
                        'language': 'english'
                    })
                    english_text.append(text)

            # Metin istatistikleri
            total_chars = sum(len(item['text']) for item in all_text)
            turkish_ratio = sum(len(text) for text in turkish_text) / total_chars if total_chars > 0 else 0

            return {
                'extracted_text': all_text,
                'turkish_text': ' '.join(turkish_text),
                'english_text': ' '.join(english_text),
                'total_characters': total_chars,
                'turkish_ratio': turkish_ratio,
                'confidence': np.mean([item['confidence'] for item in all_text]) if all_text else 0.0,
                'text_regions_count': len(all_text)
            }

        except Exception as e:
            self.logger.error(f"Metin çıkarma hatası: {str(e)}")
            return {'error': str(e), 'confidence': 0.0}

    async def _analyze_handwriting(self, image: np.ndarray) -> Dict[str, Any]:
        """El yazısı kalitesini ve özelliklerini analiz eder"""
        try:
            # El yazısı bölgelerini tespit et
            handwriting_regions = self._detect_handwriting_regions(image)

            analyses = []
            for region in handwriting_regions:
                x, y, w, h = region
                hw_area = image[y:y+h, x:x+w]

                # Kalite skoru hesapla
                quality_score = await self._calculate_handwriting_quality(hw_area)

                # El yazısı özellikleri
                features = self._extract_handwriting_features(hw_area)

                analysis = {
                    'region': (x, y, w, h),
                    'quality_score': quality_score,
                    'features': features,
                    'legibility': self._assess_legibility(hw_area),
                    'stress_indicators': self._detect_stress_indicators(hw_area)
                }
                analyses.append(analysis)

            # Genel değerlendirme
            overall_quality = np.mean([a['quality_score'] for a in analyses]) if analyses else 0.0

            return {
                'handwriting_analyses': analyses,
                'overall_quality': overall_quality,
                'total_regions': len(analyses),
                'confidence': 0.8,
                'recommendations': self._generate_handwriting_recommendations(analyses)
            }

        except Exception as e:
            self.logger.error(f"El yazısı analiz hatası: {str(e)}")
            return {'error': str(e), 'confidence': 0.0}

    def analyze_student_behavior(
        self,
        video_path: str,
        exam_duration: int,
        student_id: str
    ) -> BehaviorAnalysis:
        """Öğrenci davranışlarını video analizi ile değerlendirir"""
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = 0

            # Davranış metrikleri
            focus_scores = []
            stress_indicators = []
            suspicious_activities = []
            time_segments = {}

            while cap.read()[0]:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                current_time = frame_count / cap.get(cv2.CAP_PROP_FPS)

                # Yüz tespiti ve odaklanma analizi
                faces = self.models['behavior_analysis']['face_detector'].detectMultiScale(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.3, 5
                )

                if len(faces) > 0:
                    # Tek yüz olmalı (sınav kuralı)
                    if len(faces) > 1:
                        suspicious_activities.append(f"Birden fazla yüz tespit edildi: {current_time:.1f}s")

                    # Odaklanma skoru
                    focus_score = self._calculate_focus_score(frame, faces[0])
                    focus_scores.append(focus_score)

                    # Stres göstergeleri
                    stress_level = self._detect_stress_level(frame, faces[0])
                    if stress_level > 0.7:
                        stress_indicators.append(f"Yüksek stres: {current_time:.1f}s")

                # Her 30 saniyede analiz
                if frame_count % (30 * cap.get(cv2.CAP_PROP_FPS)) == 0:
                    segment = f"{current_time//60:.0f}_{(current_time%60)//30:.0f}"
                    time_segments[segment] = {
                        'avg_focus': np.mean(focus_scores[-900:]) if len(focus_scores) >= 900 else np.mean(focus_scores),
                        'stress_events': len([s for s in stress_indicators if f"{current_time-30:.1f}" <= s.split(':')[1] <= f"{current_time:.1f}"]),
                        'suspicious_events': len([s for s in suspicious_activities if f"{current_time-30:.1f}" <= s.split(':')[1] <= f"{current_time:.1f}"])
                    }

            cap.release()

            # Genel değerlendirme
            overall_focus = np.mean(focus_scores) if focus_scores else 0.0
            overall_behavior_score = self._calculate_behavior_score(
                overall_focus, stress_indicators, suspicious_activities
            )

            return BehaviorAnalysis(
                student_id=student_id,
                focus_score=overall_focus,
                stress_indicators=stress_indicators,
                time_spent_per_section=time_segments,
                suspicious_activities=suspicious_activities,
                overall_behavior_score=overall_behavior_score
            )

        except Exception as e:
            self.logger.error(f"Davranış analizi hatası: {str(e)}")
            raise

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Görüntü ön işleme"""
        # Gri tonlama
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Gürültü azaltma
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # Kontrast iyileştirme
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)

        # Kenar keskinleştirme
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)

        return sharpened

    async def _extract_text_from_region(self, region: np.ndarray) -> str:
        """Belirli bir bölgeden metin çıkarır"""
        try:
            # OCR uygula
            results = self.ocr_readers['turkish'].readtext(region)

            # Metinleri birleştir
            texts = [result[1] for result in results if result[2] > 0.6]
            return ' '.join(texts)

        except Exception as e:
            self.logger.error(f"Bölgesel metin çıkarma hatası: {str(e)}")
            return ""

    def _classify_question_type(self, text: str) -> QuestionType:
        """Metin içeriğine göre soru türünü belirler"""
        text_lower = text.lower()

        # Çoktan seçmeli kontrolleri
        if any(option in text_lower for option in ['a)', 'b)', 'c)', 'd)', 'e)']):
            return QuestionType.MULTIPLE_CHOICE

        # Doğru/Yanlış kontrolleri
        if 'doğru' in text_lower and 'yanlış' in text_lower:
            return QuestionType.TRUE_FALSE

        # Sayısal cevap kontrolleri
        if any(word in text_lower for word in ['hesapla', 'bul', 'kaç', 'kaçtır']):
            return QuestionType.NUMERICAL

        # Eşleştirme kontrolleri
        if 'eşleştir' in text_lower or 'bağla' in text_lower:
            return QuestionType.MATCHING

        # Varsayılan olarak çoktan seçmeli
        return QuestionType.MULTIPLE_CHOICE

    def _extract_answer_options(self, text: str, question_type: QuestionType) -> List[str]:
        """Soru metninden cevap seçeneklerini çıkarır"""
        options = []

        if question_type == QuestionType.MULTIPLE_CHOICE:
            # A), B), C), D), E) seçeneklerini bul
            import re
            pattern = r'[A-E]\)\s*([^A-E\)]+?)(?=[A-E]\)|$)'
            matches = re.findall(pattern, text, re.DOTALL)
            options = [match.strip() for match in matches]

        elif question_type == QuestionType.TRUE_FALSE:
            options = ['Doğru', 'Yanlış']

        return options

    def _validate_exam_format(self, questions: List[QuestionDetection], exam_type: ExamType) -> bool:
        """Tespit edilen soruların sınav formatına uygunluğunu kontrol eder"""
        if exam_type not in self.exam_formats:
            return True

        expected_total = sum(self.exam_formats[exam_type]['question_counts'])
        detected_total = len(questions)

        # %10 tolerans ile kontrol
        return abs(detected_total - expected_total) <= (expected_total * 0.1)

    def _detect_answer_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Cevap alanlarını tespit eder"""
        regions = []

        # Kontur tespiti ile cevap kutularını bul
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 10000:  # Cevap kutusu boyut aralığı
                x, y, w, h = cv2.boundingRect(contour)

                # Dikdörtgen oranı kontrolü (cevap kutusu karakteristiği)
                aspect_ratio = w / h
                if 0.5 < aspect_ratio < 3.0:
                    regions.append((x, y, w, h))

        # Y koordinatına göre sırala (yukarıdan aşağıya)
        regions.sort(key=lambda r: r[1])

        return regions

    async def _classify_selected_answer(self, answer_area: np.ndarray) -> str:
        """Seçilen cevabı sınıflandırır"""
        try:
            # Görüntüyü model için hazırla
            resized = cv2.resize(answer_area, (224, 224))
            normalized = resized.astype(np.float32) / 255.0
            input_data = np.expand_dims(normalized, axis=0)

            # Model ile tahmin
            predictions = self.models['answer_detection'].predict(input_data)
            predicted_class = np.argmax(predictions[0])

            # Sınıf etiketleri
            class_labels = ['A', 'B', 'C', 'D', 'E', 'BOŞ']

            return class_labels[predicted_class] if predicted_class < len(class_labels) else 'BOŞ'

        except Exception as e:
            self.logger.error(f"Cevap sınıflandırma hatası: {str(e)}")
            return 'BOŞ'

    async def _assess_handwriting_quality(self, answer_area: np.ndarray) -> float:
        """El yazısı kalitesini değerlendirir"""
        try:
            # Görüntüyü model için hazırla
            gray = cv2.cvtColor(answer_area, cv2.COLOR_BGR2GRAY) if len(answer_area.shape) == 3 else answer_area
            resized = cv2.resize(gray, (128, 32))
            normalized = resized.astype(np.float32) / 255.0
            input_data = np.expand_dims(np.expand_dims(normalized, axis=0), axis=-1)

            # Kalite skoru tahmini
            quality_score = self.models['handwriting_analysis'].predict(input_data)[0][0]

            return float(quality_score)

        except Exception as e:
            self.logger.error(f"El yazısı kalite değerlendirme hatası: {str(e)}")
            return 0.5

    def _detect_erasures(self, answer_area: np.ndarray) -> bool:
        """Silinti işaretlerini tespit eder"""
        try:
            # Gri tonlama
            gray = cv2.cvtColor(answer_area, cv2.COLOR_BGR2GRAY) if len(answer_area.shape) == 3 else answer_area

            # Gaussian blur uygula
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Kenar tespiti
            edges = cv2.Canny(blurred, 50, 150)

            # Silinti bölgeleri (düzensiz kenarlar) tespit et
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            erasure_indicators = 0
            for contour in contours:
                # Kontur karmaşıklığını hesapla
                perimeter = cv2.arcLength(contour, True)
                area = cv2.contourArea(contour)

                if area > 0:
                    complexity = perimeter / (2 * np.sqrt(np.pi * area))
                    if complexity > 2.0:  # Yüksek karmaşıklık = silinti
                        erasure_indicators += 1

            return erasure_indicators > 2

        except Exception as e:
            self.logger.error(f"Silinti tespit hatası: {str(e)}")
            return False

    def generate_analytics_report(
        self,
        analysis_results: List[VisionResult],
        exam_type: ExamType,
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Kapsamlı analitik rapor oluşturur"""
        try:
            report = {
                'exam_info': {
                    'exam_type': exam_type.value,
                    'student_id': student_id,
                    'analysis_date': datetime.now().isoformat(),
                    'total_analyses': len(analysis_results)
                },
                'performance_summary': {},
                'quality_metrics': {},
                'recommendations': [],
                'detailed_results': []
            }

            # Analiz türlerine göre grupla
            results_by_type = defaultdict(list)
            for result in analysis_results:
                results_by_type[result.analysis_type].append(result)

            # Her analiz türü için özet
            for analysis_type, type_results in results_by_type.items():
                avg_confidence = np.mean([r.confidence for r in type_results])
                avg_processing_time = np.mean([r.processing_time for r in type_results])

                report['performance_summary'][analysis_type.value] = {
                    'average_confidence': float(avg_confidence),
                    'average_processing_time': float(avg_processing_time),
                    'total_analyses': len(type_results)
                }

            # Kalite metrikleri
            all_confidences = [r.confidence for r in analysis_results]
            report['quality_metrics'] = {
                'overall_confidence': float(np.mean(all_confidences)),
                'confidence_std': float(np.std(all_confidences)),
                'min_confidence': float(min(all_confidences)) if all_confidences else 0.0,
                'max_confidence': float(max(all_confidences)) if all_confidences else 0.0
            }

            # Öneriler oluştur
            report['recommendations'] = self._generate_improvement_recommendations(analysis_results)

            # Detaylı sonuçlar
            for result in analysis_results:
                report['detailed_results'].append({
                    'analysis_type': result.analysis_type.value,
                    'confidence': result.confidence,
                    'processing_time': result.processing_time,
                    'timestamp': result.timestamp.isoformat(),
                    'result_summary': self._summarize_result_data(result.result_data)
                })

            return report

        except Exception as e:
            self.logger.error(f"Rapor oluşturma hatası: {str(e)}")
            return {'error': str(e)}

    def _generate_improvement_recommendations(self, results: List[VisionResult]) -> List[str]:
        """Gelişim önerileri oluşturur"""
        recommendations = []

        # Düşük güven skorları kontrolü
        low_confidence_results = [r for r in results if r.confidence < 0.7]
        if low_confidence_results:
            recommendations.append("Bazı analizlerde güven skoru düşük. Görüntü kalitesini artırın.")

        # Yavaş işlem süreleri kontrolü
        slow_results = [r for r in results if r.processing_time > 5.0]
        if slow_results:
            recommendations.append("İşlem süreleri optimize edilebilir. GPU kullanımını artırın.")

        # Analiz türü önerileri
        analysis_types = set(r.analysis_type for r in results)
        if AnalysisType.BEHAVIOR_ANALYSIS not in analysis_types:
            recommendations.append("Davranış analizi eklenerek daha kapsamlı değerlendirme yapılabilir.")

        return recommendations

    def _summarize_result_data(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sonuç verilerini özetler"""
        summary = {}

        # Anahtar metrikleri çıkar
        for key, value in result_data.items():
            if isinstance(value, (int, float)):
                summary[key] = value
            elif isinstance(value, list):
                summary[f"{key}_count"] = len(value)
            elif isinstance(value, dict):
                summary[f"{key}_keys"] = list(value.keys())

        return summary

    # Yardımcı metodlar devam ediyor...
    def _detect_handwriting_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """El yazısı bölgelerini tespit eder"""
        regions = []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Adaptif eşikleme
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)

        # Morfolojik işlemler
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Kontur tespiti
        contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 200:  # Minimum alan
                x, y, w, h = cv2.boundingRect(contour)

                # Aspect ratio kontrolü (el yazısı karakteristiği)
                aspect_ratio = w / h
                if 0.2 < aspect_ratio < 10.0:
                    regions.append((x, y, w, h))

        return regions

    async def _calculate_handwriting_quality(self, hw_area: np.ndarray) -> float:
        """El yazısı kalite skoru hesaplar"""
        try:
            # Çok boyutlu kalite değerlendirmesi

            # 1. Çizgi düzenliliği
            line_regularity = self._assess_line_regularity(hw_area)

            # 2. Karakter aralığı
            char_spacing = self._assess_character_spacing(hw_area)

            # 3. Basınç tutarlılığı
            pressure_consistency = self._assess_pressure_consistency(hw_area)

            # 4. Okunabilirlik
            legibility = self._assess_legibility(hw_area)

            # Ağırlıklı ortalama
            quality_score = (
                line_regularity * 0.25 +
                char_spacing * 0.25 +
                pressure_consistency * 0.25 +
                legibility * 0.25
            )

            return max(0.0, min(1.0, quality_score))

        except Exception as e:
            self.logger.error(f"El yazısı kalite hesaplama hatası: {str(e)}")
            return 0.5

    def _assess_line_regularity(self, hw_area: np.ndarray) -> float:
        """Çizgi düzenliliğini değerlendirir"""
        try:
            gray = cv2.cvtColor(hw_area, cv2.COLOR_BGR2GRAY) if len(hw_area.shape) == 3 else hw_area

            # Yatay projeksyon
            horizontal_projection = np.sum(255 - gray, axis=1)

            # Tepe noktalarını bul (metin satırları)
            peaks = []
            for i in range(1, len(horizontal_projection) - 1):
                if (horizontal_projection[i] > horizontal_projection[i-1] and
                    horizontal_projection[i] > horizontal_projection[i+1] and
                    horizontal_projection[i] > np.mean(horizontal_projection)):
                    peaks.append(i)

            if len(peaks) < 2:
                return 0.5

            # Satır aralıklarının tutarlılığını hesapla
            intervals = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)

            # Düzenlilik skoru (düşük standart sapma = yüksek düzenlilik)
            regularity_score = max(0.0, 1.0 - (std_interval / mean_interval)) if mean_interval > 0 else 0.0

            return regularity_score

        except Exception as e:
            self.logger.error(f"Çizgi düzenlilik değerlendirme hatası: {str(e)}")
            return 0.5

    def _assess_character_spacing(self, hw_area: np.ndarray) -> float:
        """Karakter aralığını değerlendirir"""
        try:
            gray = cv2.cvtColor(hw_area, cv2.COLOR_BGR2GRAY) if len(hw_area.shape) == 3 else hw_area

            # Dikey projeksyon
            vertical_projection = np.sum(255 - gray, axis=0)

            # Boşlukları ve karakterleri tespit et
            in_character = False
            character_widths = []
            space_widths = []
            current_width = 0

            for i, value in enumerate(vertical_projection):
                if value > np.mean(vertical_projection) * 0.3:  # Karakter bölgesi
                    if not in_character:
                        if current_width > 0:
                            space_widths.append(current_width)
                        current_width = 0
                        in_character = True
                    current_width += 1
                else:  # Boşluk bölgesi
                    if in_character:
                        character_widths.append(current_width)
                        current_width = 0
                        in_character = False
                    current_width += 1

            if not character_widths or not space_widths:
                return 0.5

            # Aralık tutarlılığını hesapla
            char_std = np.std(character_widths) / np.mean(character_widths) if np.mean(character_widths) > 0 else 1.0
            space_std = np.std(space_widths) / np.mean(space_widths) if np.mean(space_widths) > 0 else 1.0

            spacing_score = max(0.0, 1.0 - (char_std + space_std) / 2.0)

            return spacing_score

        except Exception as e:
            self.logger.error(f"Karakter aralık değerlendirme hatası: {str(e)}")
            return 0.5

    def _assess_pressure_consistency(self, hw_area: np.ndarray) -> float:
        """Basınç tutarlılığını değerlendirir"""
        try:
            gray = cv2.cvtColor(hw_area, cv2.COLOR_BGR2GRAY) if len(hw_area.shape) == 3 else hw_area

            # Yazı bölgelerini tespit et
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV, 11, 2)

            # İnk yoğunluğu analizi
            writing_pixels = gray[binary == 255]

            if len(writing_pixels) == 0:
                return 0.5

            # Basınç tutarlılığı (pixel yoğunluk dağılımı)
            pressure_std = np.std(writing_pixels.astype(np.float32))
            pressure_mean = np.mean(writing_pixels.astype(np.float32))

            # Normalize edilmiş tutarlılık skoru
            consistency_score = max(0.0, 1.0 - (pressure_std / pressure_mean)) if pressure_mean > 0 else 0.0

            return consistency_score

        except Exception as e:
            self.logger.error(f"Basınç tutarlılık değerlendirme hatası: {str(e)}")
            return 0.5

    def _assess_legibility(self, hw_area: np.ndarray) -> float:
        """Okunabilirlik değerlendirme"""
        try:
            # OCR ile metin tanıma güven skoru
            results = self.ocr_readers['turkish'].readtext(hw_area)

            if not results:
                return 0.3

            # Ortalama güven skoru
            confidences = [result[2] for result in results]
            legibility_score = np.mean(confidences)

            return legibility_score

        except Exception as e:
            self.logger.error(f"Okunabilirlik değerlendirme hatası: {str(e)}")
            return 0.5

    def _extract_handwriting_features(self, hw_area: np.ndarray) -> Dict[str, float]:
        """El yazısı özelliklerini çıkarır"""
        try:
            features = {}

            gray = cv2.cvtColor(hw_area, cv2.COLOR_BGR2GRAY) if len(hw_area.shape) == 3 else hw_area

            # Temel özellikler
            features['area_ratio'] = np.sum(gray < 128) / (gray.shape[0] * gray.shape[1])
            features['mean_intensity'] = np.mean(gray[gray < 128]) / 255.0 if np.any(gray < 128) else 0.0

            # Çizgi özellikleri
            edges = cv2.Canny(gray, 50, 150)
            features['edge_density'] = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])

            # Kontur özellikleri
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                features['contour_area'] = cv2.contourArea(largest_contour) / (gray.shape[0] * gray.shape[1])
                features['contour_perimeter'] = cv2.arcLength(largest_contour, True) / (gray.shape[0] + gray.shape[1])
            else:
                features['contour_area'] = 0.0
                features['contour_perimeter'] = 0.0

            return features

        except Exception as e:
            self.logger.error(f"El yazısı özellik çıkarma hatası: {str(e)}")
            return {}

    def _detect_stress_indicators(self, hw_area: np.ndarray) -> List[str]:
        """Stres göstergelerini tespit eder"""
        indicators = []

        try:
            gray = cv2.cvtColor(hw_area, cv2.COLOR_BGR2GRAY) if len(hw_area.shape) == 3 else hw_area

            # Titrek çizgiler
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Çizgi pürüzlülüğünü hesapla
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) > 10:  # Çok noktalı = titrek çizgi
                    indicators.append("Titrek çizgi yazısı")
                    break

            # Basınç değişimleri
            writing_pixels = gray[gray < 128]
            if len(writing_pixels) > 0:
                pressure_variance = np.var(writing_pixels.astype(np.float32))
                if pressure_variance > 1000:  # Yüksek varyans = düzensiz basınç
                    indicators.append("Düzensiz basınç")

            # Hız göstergeleri
            line_thickness = self._estimate_line_thickness(gray)
            if line_thickness < 2:
                indicators.append("Çok hızlı yazım")
            elif line_thickness > 5:
                indicators.append("Çok yavaş/dikkatli yazım")

        except Exception as e:
            self.logger.error(f"Stres gösterge tespiti hatası: {str(e)}")

        return indicators

    def _estimate_line_thickness(self, gray: np.ndarray) -> float:
        """Çizgi kalınlığını tahmin eder"""
        try:
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV, 11, 2)

            # Mesafe dönüşümü
            dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

            # Ortalama mesafe (kalınlık göstergesi)
            mean_thickness = np.mean(dist_transform[dist_transform > 0]) * 2

            return mean_thickness

        except Exception as e:
            self.logger.error(f"Çizgi kalınlık tahmini hatası: {str(e)}")
            return 3.0

    def _generate_handwriting_recommendations(self, analyses: List[Dict]) -> List[str]:
        """El yazısı geliştirme önerileri"""
        recommendations = []

        if not analyses:
            return ["El yazısı analizi yapılamadı."]

        avg_quality = np.mean([a['quality_score'] for a in analyses])

        if avg_quality < 0.5:
            recommendations.append("El yazısı kalitesini artırmak için daha düzenli yazmaya odaklanın.")

        # Ortak stres göstergeleri
        all_stress = []
        for analysis in analyses:
            all_stress.extend(analysis.get('stress_indicators', []))

        stress_counts = Counter(all_stress)
        for stress_type, count in stress_counts.most_common(3):
            if count > len(analyses) * 0.3:  # %30'dan fazla görünüyorsa
                recommendations.append(f"Sık görülen sorun: {stress_type}")

        # Okunabilirlik önerileri
        avg_legibility = np.mean([a['legibility'] for a in analyses if 'legibility' in a])
        if avg_legibility < 0.6:
            recommendations.append("Harfleri daha net yazmaya özen gösterin.")

        return recommendations

    def _calculate_focus_score(self, frame: np.ndarray, face_rect: Tuple[int, int, int, int]) -> float:
        """Odaklanma skorunu hesaplar"""
        try:
            x, y, w, h = face_rect
            face_region = frame[y:y+h, x:x+w]

            # Göz tespiti
            eyes = self.models['behavior_analysis']['eye_detector'].detectMultiScale(face_region)

            if len(eyes) >= 2:
                # Göz açıklığı analizi
                eye_openness = self._analyze_eye_openness(face_region, eyes)

                # Bakış yönü analizi
                gaze_direction = self._analyze_gaze_direction(face_region, eyes)

                # Odaklanma skoru (0-1 arası)
                focus_score = (eye_openness + gaze_direction) / 2.0

                return max(0.0, min(1.0, focus_score))

            return 0.5  # Göz tespit edilemezse orta değer

        except Exception as e:
            self.logger.error(f"Odaklanma skoru hesaplama hatası: {str(e)}")
            return 0.5

    def _detect_stress_level(self, frame: np.ndarray, face_rect: Tuple[int, int, int, int]) -> float:
        """Stres seviyesini tespit eder"""
        try:
            x, y, w, h = face_rect
            face_region = frame[y:y+h, x:x+w]

            # Yüz ifadesi analizi
            expression_features = self._extract_expression_features(face_region)

            # Stres göstergeleri
            stress_indicators = 0

            # Kaş çatma
            if expression_features.get('eyebrow_tension', 0) > 0.7:
                stress_indicators += 1

            # Ağız gerginliği
            if expression_features.get('mouth_tension', 0) > 0.6:
                stress_indicators += 1

            # Göz kırpma sıklığı (ayrı bir analiz gerekir)

            # Stres seviyesi (0-1 arası)
            stress_level = stress_indicators / 3.0

            return max(0.0, min(1.0, stress_level))

        except Exception as e:
            self.logger.error(f"Stres seviyesi tespiti hatası: {str(e)}")
            return 0.0

    def _analyze_eye_openness(self, face_region: np.ndarray, eyes: List) -> float:
        """Göz açıklığını analiz eder"""
        try:
            if len(eyes) < 2:
                return 0.5

            openness_scores = []

            for eye in eyes:
                ex, ey, ew, eh = eye
                eye_region = face_region[ey:ey+eh, ex:ex+ew]

                # Göz açıklık oranı hesapla
                gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY) if len(eye_region.shape) == 3 else eye_region

                # Yatay ve dikey projeksiyonlar
                h_projection = np.sum(gray_eye, axis=1)
                v_projection = np.sum(gray_eye, axis=0)

                # Göz açıklık göstergesi
                openness = np.std(h_projection) / np.mean(h_projection) if np.mean(h_projection) > 0 else 0
                openness_scores.append(min(1.0, openness))

            return np.mean(openness_scores)

        except Exception as e:
            self.logger.error(f"Göz açıklık analizi hatası: {str(e)}")
            return 0.5

    def _analyze_gaze_direction(self, face_region: np.ndarray, eyes: List) -> float:
        """Bakış yönünü analiz eder"""
        try:
            # Basit bakış yönü analizi
            # Merkeze bakış = yüksek skor
            # Yana bakış = düşük skor

            if len(eyes) < 2:
                return 0.5

            face_center_x = face_region.shape[1] // 2

            gaze_scores = []
            for eye in eyes:
                ex, ey, ew, eh = eye
                eye_center_x = ex + ew // 2

                # Merkeze yakınlık skoru
                distance_from_center = abs(eye_center_x - face_center_x)
                max_distance = face_region.shape[1] // 2

                gaze_score = 1.0 - (distance_from_center / max_distance)
                gaze_scores.append(max(0.0, gaze_score))

            return np.mean(gaze_scores)

        except Exception as e:
            self.logger.error(f"Bakış yönü analizi hatası: {str(e)}")
            return 0.5

    def _extract_expression_features(self, face_region: np.ndarray) -> Dict[str, float]:
        """Yüz ifadesi özelliklerini çıkarır"""
        try:
            features = {}

            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY) if len(face_region.shape) == 3 else face_region

            # Basit özellik çıkarımı
            # Kaş bölgesi (üst %25)
            eyebrow_region = gray_face[:gray_face.shape[0]//4, :]
            features['eyebrow_tension'] = np.std(eyebrow_region) / 255.0

            # Ağız bölgesi (alt %30)
            mouth_region = gray_face[int(gray_face.shape[0]*0.7):, :]
            features['mouth_tension'] = np.std(mouth_region) / 255.0

            # Genel yüz gerginliği
            features['overall_tension'] = np.std(gray_face) / 255.0

            return features

        except Exception as e:
            self.logger.error(f"Yüz ifadesi özellik çıkarma hatası: {str(e)}")
            return {}

    def _calculate_behavior_score(
        self,
        focus_score: float,
        stress_indicators: List[str],
        suspicious_activities: List[str]
    ) -> float:
        """Genel davranış skoru hesaplar"""
        try:
            # Temel skor odaklanma skorundan
            base_score = focus_score

            # Stres penaltısı
            stress_penalty = min(0.3, len(stress_indicators) * 0.05)

            # Şüpheli aktivite penaltısı
            suspicious_penalty = min(0.4, len(suspicious_activities) * 0.1)

            # Toplam skor
            behavior_score = base_score - stress_penalty - suspicious_penalty

            return max(0.0, min(1.0, behavior_score))

        except Exception as e:
            self.logger.error(f"Davranış skoru hesaplama hatası: {str(e)}")
            return 0.5

# Kullanım örneği ve test fonksiyonları
async def main():
    """Ana test fonksiyonu"""
    analyzer = TurkishExamVisionAnalyzer()

    # Örnek görüntü analizi
    try:
        results = await analyzer.analyze_exam_document(
            image_path="sample_exam.jpg",
            exam_type=ExamType.TYT,
            analysis_types=[
                AnalysisType.QUESTION_RECOGNITION,
                AnalysisType.ANSWER_DETECTION,
                AnalysisType.TEXT_EXTRACTION,
                AnalysisType.HANDWRITING_ANALYSIS
            ]
        )

        # Rapor oluştur
        report = analyzer.generate_analytics_report(results, ExamType.TYT, "student_123")

        print("Analiz tamamlandı!")
        print(f"Toplam analiz: {len(results)}")
        print(f"Ortalama güven skoru: {report['quality_metrics']['overall_confidence']:.2f}")

    except Exception as e:
        print(f"Test hatası: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
