"""
BERTurk Entegrasyonu ve Duygu Analizi Servisi
Eğitim domain'ine özel duygu analizi ve öğrenci motivasyon tespiti
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)


@dataclass
class SentimentAnalysisResult:
    """Duygu analizi sonucu"""

    text: str
    sentiment: str  # positive, negative, neutral
    confidence: float
    emotion_scores: dict[str, float]  # joy, sadness, anger, fear, surprise, disgust
    educational_context: dict[
        str, float
    ]  # motivation, frustration, engagement, confusion
    timestamp: datetime


@dataclass
class MotivationAssessment:
    """Öğrenci motivasyon değerlendirmesi"""

    student_id: str
    motivation_level: float  # 0.0 - 1.0
    engagement_score: float  # 0.0 - 1.0
    frustration_level: float  # 0.0 - 1.0
    confidence_level: float  # 0.0 - 1.0
    learning_enthusiasm: float  # 0.0 - 1.0
    support_needed: bool
    recommendations: list[str]
    analysis_timestamp: datetime


@dataclass
class IntentDetectionResult:
    """Niyet tespit sonucu"""

    text: str
    intent: str  # question, help_request, complaint, compliment, confusion, etc.
    confidence: float
    entities: list[dict[str, Any]]  # Tespit edilen varlıklar
    context_category: str  # academic, technical, emotional, social
    urgency_level: str  # low, medium, high, critical


@dataclass
class ContextualMeaningResult:
    """Bağlamsal anlam çıkarma sonucu"""

    text: str
    main_topic: str
    subtopics: list[str]
    difficulty_level: float  # 0.0 - 1.0
    academic_domain: str  # math, science, language, social_studies
    key_concepts: list[str]
    semantic_similarity_score: float


class BERTurkService:
    """
    BERTurk model entegrasyonu ile Türkçe duygu analizi ve NLP servisi
    Eğitim domain'ine özel optimizasyonlar içerir
    """

    def __init__(self):
        self.model_name = "dbmdz/bert-base-turkish-cased"
        self.sentiment_model_name = "savasy/bert-base-turkish-sentiment-cased"

        # Model ve tokenizer'lar
        self.tokenizer = None
        self.base_model = None
        self.sentiment_model = None
        self.sentiment_tokenizer = None

        # Cache ve performans
        self.cache_dir = Path("./cache/berturk")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session_cache = {}
        self.max_cache_size = 1000

        # Eğitim domain'ine özel sözlükler
        self.educational_emotions = {
            "motivation": [
                "heyecanlı",
                "istekli",
                "kararlı",
                "azimli",
                "umutlu",
                "coşkulu",
            ],
            "frustration": [
                "sinirli",
                "kızgın",
                "bezgin",
                "yorgun",
                "umutsuz",
                "çaresiz",
            ],
            "engagement": ["ilgili", "meraklı", "odaklanmış", "dikkatli", "aktif"],
            "confusion": [
                "kafası karışık",
                "anlamayan",
                "şaşkın",
                "belirsiz",
                "kararsız",
            ],
            "confidence": ["kendinden emin", "güvenli", "rahat", "sakin", "pozitif"],
            "anxiety": ["endişeli", "gergin", "stresli", "kaygılı", "tedirgin"],
        }

        # Intent sınıfları
        self.intent_categories = {
            "question": ["soru", "nasıl", "neden", "ne", "kim", "nerede", "ne zaman"],
            "help_request": ["yardım", "destek", "açıkla", "göster", "öğret"],
            "complaint": ["şikayet", "sorun", "problem", "hata", "yanlış"],
            "compliment": ["teşekkür", "güzel", "harika", "mükemmel", "başarılı"],
            "confusion": ["anlamadım", "karışık", "belirsiz", "net değil"],
            "technical_issue": ["çalışmıyor", "açılmıyor", "yavaş", "hata veriyor"],
        }

        # Akademik domain sınıfları
        self.academic_domains = {
            "mathematics": [
                "matematik",
                "sayı",
                "hesap",
                "formül",
                "geometri",
                "algebra",
            ],
            "science": ["fen", "fizik", "kimya", "biyoloji", "deney", "atom"],
            "language": ["türkçe", "dil", "gramer", "kelime", "cümle", "metin"],
            "social_studies": ["tarih", "coğrafya", "sosyal", "toplum", "kültür"],
            "general": ["genel", "diğer", "karma", "çeşitli"],
        }

        # Performans metrikleri
        self.performance_stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "model_inference_time": [],
            "error_count": 0,
        }

    async def initialize(self) -> bool:
        """
        BERTurk modellerini yükle ve servisi başlat
        """
        try:
            logger.info("BERTurk servisi başlatılıyor...")

            # Tokenizer'ları yükle
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, cache_dir=str(self.cache_dir)
            )

            self.sentiment_tokenizer = AutoTokenizer.from_pretrained(
                self.sentiment_model_name, cache_dir=str(self.cache_dir)
            )

            # Base model'i yükle
            self.base_model = AutoModel.from_pretrained(
                self.model_name, cache_dir=str(self.cache_dir)
            )

            # Sentiment model'i yükle
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
                self.sentiment_model_name, cache_dir=str(self.cache_dir)
            )

            # Model'leri evaluation moduna al
            self.base_model.eval()
            self.sentiment_model.eval()

            # GPU kullanımı kontrolü
            if torch.cuda.is_available():
                self.base_model = self.base_model.cuda()
                self.sentiment_model = self.sentiment_model.cuda()
                logger.info("BERTurk modelleri GPU'ya yüklendi")
            else:
                logger.info("BERTurk modelleri CPU'da çalışıyor")

            logger.info("BERTurk servisi başarıyla başlatıldı")
            return True

        except Exception as e:
            logger.error(f"BERTurk servisi başlatılırken hata: {e}")
            return False

    async def analyze_sentiment(
        self, text: str, include_emotions: bool = True, educational_context: bool = True
    ) -> SentimentAnalysisResult:
        """
        Metinin duygu analizini yap

        Args:
            text: Analiz edilecek metin
            include_emotions: Detaylı duygu skorları dahil edilsin mi
            educational_context: Eğitim bağlamı analizi yapılsın mı

        Returns:
            SentimentAnalysisResult: Duygu analizi sonucu
        """
        try:
            start_time = datetime.now()

            # Cache kontrolü
            cache_key = (
                f"sentiment_{hash(text)}_{include_emotions}_{educational_context}"
            )
            if cache_key in self.session_cache:
                self.performance_stats["cache_hits"] += 1
                return self.session_cache[cache_key]

            # Metni temizle ve hazırla
            cleaned_text = self._preprocess_text(text)

            if not cleaned_text:
                return self._create_empty_sentiment_result(text)

            # BERTurk ile sentiment analizi
            sentiment_scores = await self._run_sentiment_inference(cleaned_text)

            # Ana sentiment'i belirle
            main_sentiment = self._determine_main_sentiment(sentiment_scores)
            confidence = max(sentiment_scores.values())

            # Detaylı duygu analizi
            emotion_scores = {}
            if include_emotions:
                emotion_scores = await self._analyze_detailed_emotions(cleaned_text)

            # Eğitim bağlamı analizi
            educational_context_scores = {}
            if educational_context:
                educational_context_scores = await self._analyze_educational_context(
                    cleaned_text
                )

            # Sonucu oluştur
            result = SentimentAnalysisResult(
                text=text,
                sentiment=main_sentiment,
                confidence=confidence,
                emotion_scores=emotion_scores,
                educational_context=educational_context_scores,
                timestamp=datetime.now(),
            )

            # Cache'e ekle
            self._add_to_cache(cache_key, result)

            # Performans istatistikleri
            inference_time = (datetime.now() - start_time).total_seconds()
            self.performance_stats["model_inference_time"].append(inference_time)
            self.performance_stats["total_analyses"] += 1

            return result

        except Exception as e:
            logger.error(f"Duygu analizi hatası: {e}")
            self.performance_stats["error_count"] += 1
            return self._create_empty_sentiment_result(text, error=str(e))

    async def _run_sentiment_inference(self, text: str) -> dict[str, float]:
        """BERTurk sentiment model ile inference yap"""
        try:
            # Tokenize et
            inputs = self.sentiment_tokenizer(
                text, return_tensors="pt", truncation=True, padding=True, max_length=512
            )

            # GPU'ya taşı (varsa)
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Model inference
            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

            # Sonuçları parse et
            scores = predictions.cpu().numpy()[0]

            # Label mapping (model'e göre değişebilir)
            labels = ["negative", "neutral", "positive"]

            return {
                label: float(score)
                for label, score in zip(labels, scores, strict=False)
            }

        except Exception as e:
            logger.error(f"Sentiment inference hatası: {e}")
            return {"positive": 0.33, "neutral": 0.34, "negative": 0.33}

    async def _analyze_detailed_emotions(self, text: str) -> dict[str, float]:
        """Detaylı duygu analizi (6 temel duygu)"""
        try:
            # Kelime bazlı duygu analizi
            words = text.lower().split()

            emotion_scores = {
                "joy": 0.0,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "surprise": 0.0,
                "disgust": 0.0,
            }

            # Basit lexicon-based yaklaşım
            joy_words = ["mutlu", "sevinçli", "neşeli", "keyifli", "memnun", "başarılı"]
            sadness_words = ["üzgün", "kederli", "mutsuz", "melankolik", "hüzünlü"]
            anger_words = ["kızgın", "sinirli", "öfkeli", "hiddetli", "asabi"]
            fear_words = ["korkmuş", "endişeli", "tedirgin", "kaygılı", "gergin"]
            surprise_words = ["şaşırmış", "hayret", "inanamıyorum", "vay", "wow"]
            disgust_words = ["iğrenç", "tiksinti", "berbat", "kötü", "rezalet"]

            word_count = len(words)
            if word_count == 0:
                return emotion_scores

            for word in words:
                if word in joy_words:
                    emotion_scores["joy"] += 1.0 / word_count
                elif word in sadness_words:
                    emotion_scores["sadness"] += 1.0 / word_count
                elif word in anger_words:
                    emotion_scores["anger"] += 1.0 / word_count
                elif word in fear_words:
                    emotion_scores["fear"] += 1.0 / word_count
                elif word in surprise_words:
                    emotion_scores["surprise"] += 1.0 / word_count
                elif word in disgust_words:
                    emotion_scores["disgust"] += 1.0 / word_count

            return emotion_scores

        except Exception as e:
            logger.error(f"Detaylı duygu analizi hatası: {e}")
            return {
                "joy": 0.0,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "surprise": 0.0,
                "disgust": 0.0,
            }

    async def _analyze_educational_context(self, text: str) -> dict[str, float]:
        """Eğitim bağlamında duygu analizi"""
        try:
            words = text.lower().split()
            word_count = len(words)

            context_scores = {
                "motivation": 0.0,
                "frustration": 0.0,
                "engagement": 0.0,
                "confusion": 0.0,
                "confidence": 0.0,
                "anxiety": 0.0,
            }

            if word_count == 0:
                return context_scores

            # Her kategori için kelime eşleştirmesi
            for category, keywords in self.educational_emotions.items():
                for word in words:
                    for keyword in keywords:
                        if keyword in word or word in keyword:
                            context_scores[category] += 1.0 / word_count

            return context_scores

        except Exception as e:
            logger.error(f"Eğitim bağlamı analizi hatası: {e}")
            return {
                "motivation": 0.0,
                "frustration": 0.0,
                "engagement": 0.0,
                "confusion": 0.0,
                "confidence": 0.0,
                "anxiety": 0.0,
            }

    async def assess_student_motivation(
        self, student_id: str, recent_texts: list[str], time_window_hours: int = 24
    ) -> MotivationAssessment:
        """
        Öğrenci motivasyon durumunu değerlendir

        Args:
            student_id: Öğrenci ID'si
            recent_texts: Son metinler (sohbet, yorumlar, vs.)
            time_window_hours: Değerlendirme zaman penceresi (saat)

        Returns:
            MotivationAssessment: Motivasyon değerlendirmesi
        """
        try:
            if not recent_texts:
                return self._create_empty_motivation_assessment(student_id)

            # Her metin için duygu analizi yap
            sentiment_results = []
            for text in recent_texts:
                result = await self.analyze_sentiment(
                    text, include_emotions=True, educational_context=True
                )
                sentiment_results.append(result)

            # Genel skorları hesapla
            motivation_scores = []
            engagement_scores = []
            frustration_scores = []
            confidence_scores = []
            enthusiasm_scores = []

            for result in sentiment_results:
                # Motivasyon skoru
                motivation = (
                    result.educational_context.get("motivation", 0.0) * 0.4
                    + result.educational_context.get("engagement", 0.0) * 0.3
                    + (1.0 - result.educational_context.get("frustration", 0.0)) * 0.3
                )
                motivation_scores.append(motivation)

                # Engagement skoru
                engagement = result.educational_context.get("engagement", 0.0)
                engagement_scores.append(engagement)

                # Frustration skoru
                frustration = result.educational_context.get("frustration", 0.0)
                frustration_scores.append(frustration)

                # Confidence skoru
                confidence = result.educational_context.get("confidence", 0.0)
                confidence_scores.append(confidence)

                # Enthusiasm (pozitif duygu + motivasyon)
                enthusiasm = (
                    1.0 if result.sentiment == "positive" else 0.0
                ) * 0.5 + result.educational_context.get("motivation", 0.0) * 0.5
                enthusiasm_scores.append(enthusiasm)

            # Ortalama skorlar
            avg_motivation = sum(motivation_scores) / len(motivation_scores)
            avg_engagement = sum(engagement_scores) / len(engagement_scores)
            avg_frustration = sum(frustration_scores) / len(frustration_scores)
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            avg_enthusiasm = sum(enthusiasm_scores) / len(enthusiasm_scores)

            # Destek gereksinimi
            support_needed = (
                avg_motivation < 0.4 or avg_frustration > 0.6 or avg_confidence < 0.3
            )

            # Öneriler oluştur
            recommendations = self._generate_motivation_recommendations(
                avg_motivation, avg_engagement, avg_frustration, avg_confidence
            )

            return MotivationAssessment(
                student_id=student_id,
                motivation_level=avg_motivation,
                engagement_score=avg_engagement,
                frustration_level=avg_frustration,
                confidence_level=avg_confidence,
                learning_enthusiasm=avg_enthusiasm,
                support_needed=support_needed,
                recommendations=recommendations,
                analysis_timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Motivasyon değerlendirme hatası: {e}")
            return self._create_empty_motivation_assessment(student_id, error=str(e))

    def _generate_motivation_recommendations(
        self,
        motivation: float,
        engagement: float,
        frustration: float,
        confidence: float,
    ) -> list[str]:
        """Motivasyon durumuna göre öneriler oluştur"""
        recommendations = []

        if motivation < 0.4:
            recommendations.append(
                "Öğrencinin motivasyonunu artırmak için başarı hikayelerini paylaşın"
            )
            recommendations.append(
                "Küçük hedefler belirleyerek başarı duygusunu artırın"
            )

        if engagement < 0.4:
            recommendations.append("İnteraktif içerikler ve oyunlaştırma kullanın")
            recommendations.append("Öğrencinin ilgi alanlarına uygun örnekler verin")

        if frustration > 0.6:
            recommendations.append("Zorluk seviyesini düşürün ve adım adım ilerleyin")
            recommendations.append("Öğrenciye mola verme önerisi yapın")
            recommendations.append("Alternatif açıklama yöntemleri deneyin")

        if confidence < 0.3:
            recommendations.append("Pozitif geri bildirim ve teşvik artırın")
            recommendations.append("Öğrencinin güçlü yönlerini vurgulayın")
            recommendations.append(
                "Başarılı olduğu konulardan başlayarak güven oluşturun"
            )

        if not recommendations:
            recommendations.append(
                "Öğrenci genel olarak iyi durumda, mevcut yaklaşımı sürdürün"
            )

        return recommendations

    async def detect_intent(self, text: str) -> IntentDetectionResult:
        """
        Metindeki niyeti tespit et

        Args:
            text: Analiz edilecek metin

        Returns:
            IntentDetectionResult: Niyet tespit sonucu
        """
        try:
            cleaned_text = self._preprocess_text(text)

            if not cleaned_text:
                return self._create_empty_intent_result(text)

            # Kelime bazlı intent tespiti
            words = cleaned_text.lower().split()
            intent_scores = {}

            for intent, keywords in self.intent_categories.items():
                score = 0.0
                for word in words:
                    for keyword in keywords:
                        if keyword in word or word in keyword:
                            score += 1.0

                if len(words) > 0:
                    intent_scores[intent] = score / len(words)
                else:
                    intent_scores[intent] = 0.0

            # En yüksek skorlu intent'i seç
            if intent_scores:
                main_intent = max(intent_scores, key=intent_scores.get)
                confidence = intent_scores[main_intent]
            else:
                main_intent = "general"
                confidence = 0.5

            # Varlık tespiti (basit)
            entities = self._extract_simple_entities(cleaned_text)

            # Bağlam kategorisi
            context_category = self._determine_context_category(cleaned_text)

            # Aciliyet seviyesi
            urgency_level = self._determine_urgency_level(cleaned_text, main_intent)

            return IntentDetectionResult(
                text=text,
                intent=main_intent,
                confidence=confidence,
                entities=entities,
                context_category=context_category,
                urgency_level=urgency_level,
            )

        except Exception as e:
            logger.error(f"Intent tespit hatası: {e}")
            return self._create_empty_intent_result(text, error=str(e))

    def _extract_simple_entities(self, text: str) -> list[dict[str, Any]]:
        """Basit varlık tespiti"""
        entities = []

        # Sayılar
        import re

        numbers = re.findall(r"\d+", text)
        for num in numbers:
            entities.append({"type": "number", "value": num, "confidence": 0.9})

        # Akademik konular
        for domain, keywords in self.academic_domains.items():
            for keyword in keywords:
                if keyword in text.lower():
                    entities.append(
                        {
                            "type": "academic_subject",
                            "value": keyword,
                            "domain": domain,
                            "confidence": 0.8,
                        }
                    )

        return entities

    def _determine_context_category(self, text: str) -> str:
        """Bağlam kategorisini belirle"""
        words = text.lower().split()

        # Akademik kelimeler
        academic_words = ["ders", "ödev", "sınav", "konu", "soru", "cevap", "öğren"]
        # Teknik kelimeler
        technical_words = ["sistem", "program", "uygulama", "hata", "çalışmıyor"]
        # Duygusal kelimeler
        emotional_words = ["üzgün", "mutlu", "kızgın", "endişeli", "heyecanlı"]
        # Sosyal kelimeler
        social_words = ["arkadaş", "öğretmen", "sınıf", "grup", "beraber"]

        academic_score = sum(
            1 for word in words if any(aw in word for aw in academic_words)
        )
        technical_score = sum(
            1 for word in words if any(tw in word for tw in technical_words)
        )
        emotional_score = sum(
            1 for word in words if any(ew in word for ew in emotional_words)
        )
        social_score = sum(
            1 for word in words if any(sw in word for sw in social_words)
        )

        scores = {
            "academic": academic_score,
            "technical": technical_score,
            "emotional": emotional_score,
            "social": social_score,
        }

        return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"

    def _determine_urgency_level(self, text: str, intent: str) -> str:
        """Aciliyet seviyesini belirle"""
        urgent_words = ["acil", "hemen", "çabuk", "acele", "kritik", "önemli"]
        problem_words = ["sorun", "problem", "hata", "çalışmıyor", "yardım"]

        text_lower = text.lower()

        urgent_count = sum(1 for word in urgent_words if word in text_lower)
        problem_count = sum(1 for word in problem_words if word in text_lower)

        if urgent_count > 0 or intent == "complaint":
            return "high"
        if problem_count > 0 or intent == "help_request":
            return "medium"
        return "low"

    async def extract_contextual_meaning(self, text: str) -> ContextualMeaningResult:
        """
        Bağlamsal anlam çıkarma

        Args:
            text: Analiz edilecek metin

        Returns:
            ContextualMeaningResult: Bağlamsal anlam sonucu
        """
        try:
            cleaned_text = self._preprocess_text(text)

            if not cleaned_text:
                return self._create_empty_contextual_result(text)

            # Ana konu tespiti
            main_topic = self._extract_main_topic(cleaned_text)

            # Alt konular
            subtopics = self._extract_subtopics(cleaned_text)

            # Zorluk seviyesi
            difficulty_level = self._assess_text_difficulty(cleaned_text)

            # Akademik domain
            academic_domain = self._classify_academic_domain(cleaned_text)

            # Anahtar kavramlar
            key_concepts = self._extract_key_concepts(cleaned_text)

            # Semantik benzerlik skoru (basit)
            semantic_similarity = 0.5  # Placeholder

            return ContextualMeaningResult(
                text=text,
                main_topic=main_topic,
                subtopics=subtopics,
                difficulty_level=difficulty_level,
                academic_domain=academic_domain,
                key_concepts=key_concepts,
                semantic_similarity_score=semantic_similarity,
            )

        except Exception as e:
            logger.error(f"Bağlamsal anlam çıkarma hatası: {e}")
            return self._create_empty_contextual_result(text, error=str(e))

    def _extract_main_topic(self, text: str) -> str:
        """Ana konuyu çıkar"""
        words = text.lower().split()

        # Frekans analizi
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Kısa kelimeleri filtrele
                word_freq[word] = word_freq.get(word, 0) + 1

        if word_freq:
            return max(word_freq, key=word_freq.get)
        return "genel"

    def _extract_subtopics(self, text: str) -> list[str]:
        """Alt konuları çıkar"""
        words = text.lower().split()

        # Akademik terimler
        academic_terms = []
        for word in words:
            if len(word) > 4 and any(
                domain_words
                for domain_words in self.academic_domains.values()
                if word in domain_words
            ):
                academic_terms.append(word)

        return list(set(academic_terms))[:5]  # İlk 5 benzersiz terim

    def _assess_text_difficulty(self, text: str) -> float:
        """Metin zorluk seviyesini değerlendir"""
        words = text.split()

        if not words:
            return 0.0

        # Ortalama kelime uzunluğu
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Karmaşık kelime oranı (6+ karakter)
        complex_words = sum(1 for word in words if len(word) >= 6)
        complex_ratio = complex_words / len(words)

        # Cümle uzunluğu
        sentence_count = text.count(".") + text.count("!") + text.count("?") + 1
        avg_sentence_length = len(words) / sentence_count

        # Zorluk skoru hesaplama
        difficulty = (
            (avg_word_length / 10) * 0.3
            + complex_ratio * 0.4
            + (avg_sentence_length / 20) * 0.3
        )

        return min(1.0, difficulty)

    def _classify_academic_domain(self, text: str) -> str:
        """Akademik domain sınıflandırması"""
        text_lower = text.lower()

        domain_scores = {}
        for domain, keywords in self.academic_domains.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            domain_scores[domain] = score

        return (
            max(domain_scores, key=domain_scores.get)
            if max(domain_scores.values()) > 0
            else "general"
        )

    def _extract_key_concepts(self, text: str) -> list[str]:
        """Anahtar kavramları çıkar"""
        words = text.lower().split()

        # Önemli kelimeler (uzun ve akademik)
        key_concepts = []
        for word in words:
            if len(word) >= 5:
                # Akademik terim kontrolü
                for domain_keywords in self.academic_domains.values():
                    if word in domain_keywords:
                        key_concepts.append(word)
                        break

        return list(set(key_concepts))[:10]  # İlk 10 benzersiz kavram

    def _preprocess_text(self, text: str) -> str:
        """Metni ön işleme tabi tut"""
        if not text:
            return ""

        # Temel temizlik
        cleaned = text.strip()

        # Çoklu boşlukları tek boşluğa çevir
        import re

        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned

    def _determine_main_sentiment(self, scores: dict[str, float]) -> str:
        """Ana sentiment'i belirle"""
        return max(scores, key=scores.get)

    def _add_to_cache(self, key: str, value: Any):
        """Cache'e değer ekle"""
        if len(self.session_cache) >= self.max_cache_size:
            # En eski girdiyi sil
            oldest_key = next(iter(self.session_cache))
            del self.session_cache[oldest_key]

        self.session_cache[key] = value

    def _create_empty_sentiment_result(
        self, text: str, error: str = None
    ) -> SentimentAnalysisResult:
        """Boş sentiment sonucu oluştur"""
        return SentimentAnalysisResult(
            text=text,
            sentiment="neutral",
            confidence=0.0,
            emotion_scores={},
            educational_context={},
            timestamp=datetime.now(),
        )

    def _create_empty_motivation_assessment(
        self, student_id: str, error: str = None
    ) -> MotivationAssessment:
        """Boş motivasyon değerlendirmesi oluştur"""
        return MotivationAssessment(
            student_id=student_id,
            motivation_level=0.5,
            engagement_score=0.5,
            frustration_level=0.0,
            confidence_level=0.5,
            learning_enthusiasm=0.5,
            support_needed=False,
            recommendations=["Veri yetersiz, daha fazla etkileşim gerekli"],
            analysis_timestamp=datetime.now(),
        )

    def _create_empty_intent_result(
        self, text: str, error: str = None
    ) -> IntentDetectionResult:
        """Boş intent sonucu oluştur"""
        return IntentDetectionResult(
            text=text,
            intent="general",
            confidence=0.0,
            entities=[],
            context_category="general",
            urgency_level="low",
        )

    def _create_empty_contextual_result(
        self, text: str, error: str = None
    ) -> ContextualMeaningResult:
        """Boş bağlamsal sonuç oluştur"""
        return ContextualMeaningResult(
            text=text,
            main_topic="genel",
            subtopics=[],
            difficulty_level=0.5,
            academic_domain="general",
            key_concepts=[],
            semantic_similarity_score=0.0,
        )

    async def get_performance_stats(self) -> dict[str, Any]:
        """Performans istatistiklerini getir"""
        avg_inference_time = 0.0
        if self.performance_stats["model_inference_time"]:
            avg_inference_time = sum(
                self.performance_stats["model_inference_time"]
            ) / len(self.performance_stats["model_inference_time"])

        cache_hit_rate = 0.0
        if self.performance_stats["total_analyses"] > 0:
            cache_hit_rate = (
                self.performance_stats["cache_hits"]
                / self.performance_stats["total_analyses"]
            )

        return {
            "total_analyses": self.performance_stats["total_analyses"],
            "cache_hits": self.performance_stats["cache_hits"],
            "cache_hit_rate": round(cache_hit_rate, 3),
            "average_inference_time_seconds": round(avg_inference_time, 3),
            "error_count": self.performance_stats["error_count"],
            "cache_size": len(self.session_cache),
        }

    async def clear_cache(self):
        """Cache'i temizle"""
        self.session_cache.clear()
        logger.info("BERTurk cache temizlendi")

    async def close(self):
        """Servisi kapat"""
        await self.clear_cache()

        # Model'leri bellekten temizle
        if hasattr(self, "base_model") and self.base_model:
            del self.base_model
        if hasattr(self, "sentiment_model") and self.sentiment_model:
            del self.sentiment_model

        # GPU memory temizle
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("BERTurk servisi kapatıldı")


# Global instance
berturk_service = BERTurkService()
