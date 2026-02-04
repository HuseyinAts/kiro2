"""
Turkish Content Filter Service
Video içeriğinin Türkçe olup olmadığını doğrular ve relevance scoring yapar
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class TurkishValidationResult:
    """Türkçe doğrulama sonucu"""

    is_turkish: bool
    confidence_score: float  # 0.0-1.0
    detected_language: str
    turkish_indicators: List[str]


@dataclass
class FilterResult:
    """Video filtreleme sonucu"""

    video: Any  # VideoResponse veya dict
    language_score: float  # 0-1
    relevance_score: float  # 0-1
    difficulty_match: float  # 0-1
    overall_score: float  # 0-1
    passed: bool
    failure_reasons: List[str] = None

    def __post_init__(self):
        if self.failure_reasons is None:
            self.failure_reasons = []


# Güvenilir Türkçe eğitim kanalları
TRUSTED_TURKISH_CHANNELS = {
    "TonguçAkademi": {
        "weight": 1.0,
        "subjects": ["matematik", "fizik", "kimya", "biyoloji"],
    },
    "Tonguç Akademi": {
        "weight": 1.0,
        "subjects": ["matematik", "fizik", "kimya", "biyoloji"],
    },
    "Khan Academy Türkçe": {"weight": 1.0, "subjects": ["matematik", "fizik"]},
    "KAMP Online": {"weight": 0.95, "subjects": ["matematik", "fizik", "kimya"]},
    "Hocalara Geldik": {"weight": 0.9, "subjects": ["matematik", "fizik"]},
    "MEB Uzaktan Eğitim": {"weight": 0.85, "subjects": "all"},
    "EBA": {"weight": 0.95, "subjects": "all"},
    "BTK Akademi": {"weight": 0.9, "subjects": ["bilgisayar", "teknoloji"]},
    "Evrim Ağacı": {"weight": 0.85, "subjects": ["biyoloji", "fen"]},
    "Matematik Öğretmeni": {"weight": 0.9, "subjects": ["matematik"]},
    "Fizik Öğretmeni": {"weight": 0.92, "subjects": ["fizik"]},
    "Kimya Öğretmeni": {"weight": 0.9, "subjects": ["kimya"]},
    "Biyoloji Öğretmeni": {"weight": 0.9, "subjects": ["biyoloji"]},
    "Türkçe Öğretmeni": {"weight": 0.9, "subjects": ["türkçe", "edebiyat"]},
}

# MEB Müfredatı Konu Taxonomy
SUBJECT_TAXONOMY = {
    "matematik": {
        "keywords": [
            "matematik",
            "geometri",
            "algebra",
            "trigonometri",
            "sayılar",
            "hesaplama",
        ],
        "sub_topics": {
            "geometri": [
                "üçgen",
                "dörtgen",
                "çember",
                "alan",
                "hacim",
                "açı",
                "kenar",
                "çevre",
            ],
            "algebra": [
                "denklem",
                "eşitsizlik",
                "fonksiyon",
                "polinom",
                "köklü sayılar",
            ],
            "sayılar": [
                "doğal sayılar",
                "tam sayılar",
                "rasyonel sayılar",
                "irrasyonel sayılar",
            ],
            "trigonometri": ["sinüs", "kosinüs", "tanjant", "açı ölçüleri"],
        },
    },
    "fizik": {
        "keywords": [
            "fizik",
            "hareket",
            "kuvvet",
            "enerji",
            "elektrik",
            "manyetizma",
            "ışık",
        ],
        "sub_topics": {
            "hareket": [
                "hız",
                "ivme",
                "serbest düşme",
                "atış hareketi",
                "çembersel hareket",
            ],
            "enerji": ["kinetik enerji", "potansiyel enerji", "iş", "güç", "momentum"],
            "elektrik": ["akım", "gerilim", "direnç", "devre", "ohm kanunu"],
            "ışık": ["kırılma", "yansıma", "mercek", "prizma"],
        },
    },
    "kimya": {
        "keywords": [
            "kimya",
            "atom",
            "molekül",
            "element",
            "bileşik",
            "reaksiyon",
            "periyodik",
        ],
        "sub_topics": {
            "atom": ["proton", "nötron", "elektron", "atom numarası", "kütle numarası"],
            "bağlar": ["iyonik bağ", "kovalent bağ", "metalik bağ", "hidrojen bağı"],
            "reaksiyonlar": ["yanma", "asit-baz", "yükseltgenme", "indirgenme"],
            "periyodik": ["periyot", "grup", "metal", "ametal", "yarı metal"],
        },
    },
    "biyoloji": {
        "keywords": [
            "biyoloji",
            "hücre",
            "canlı",
            "organizma",
            "doku",
            "organ",
            "sistem",
        ],
        "sub_topics": {
            "hücre": ["hücre zarı", "sitoplazma", "çekirdek", "mitokondri", "ribozom"],
            "genetik": ["dna", "rna", "gen", "kromozom", "kalıtım"],
            "sistemler": ["sindirim", "dolaşım", "solunum", "boşaltım", "sinir"],
            "ekoloji": ["ekosistem", "besin zinciri", "habitat", "popülasyon"],
        },
    },
    "türkçe": {
        "keywords": [
            "türkçe",
            "dil bilgisi",
            "edebiyat",
            "yazım",
            "noktalama",
            "sözcük",
        ],
        "sub_topics": {
            "dil bilgisi": ["isim", "fiil", "sıfat", "zarf", "edat", "bağlaç"],
            "cümle": ["özne", "yüklem", "nesne", "tümleç", "cümle türleri"],
            "edebiyat": ["şiir", "hikaye", "roman", "makale", "deneme"],
            "yazım": ["büyük harf", "noktalama", "yazım kuralları"],
        },
    },
    "tarih": {
        "keywords": ["tarih", "osmanlı", "türk", "cumhuriyet", "devrim", "savaş"],
        "sub_topics": {
            "osmanlı": ["kuruluş", "yükselme", "duraklama", "gerileme"],
            "cumhuriyet": ["atatürk", "inkılap", "reform", "çağdaşlaşma"],
            "dünya": ["dünya savaşı", "soğuk savaş", "uygarlık"],
        },
    },
    "coğrafya": {
        "keywords": ["coğrafya", "harita", "iklim", "nüfus", "ekonomi", "bölge"],
        "sub_topics": {
            "fiziki": ["dağ", "ova", "akarsu", "göl", "iklim"],
            "beşeri": ["nüfus", "göç", "şehir", "köy", "yerleşme"],
            "ekonomik": ["tarım", "sanayi", "ticaret", "ulaşım"],
        },
    },
}


class TurkishContentFilter:
    """
    Türkçe içerik filtreleme servisi

    Video başlığı, açıklaması ve kanal adını analiz ederek
    içeriğin Türkçe olup olmadığını belirler.
    """

    def __init__(self):
        """TurkishContentFilter'ı başlat"""
        self.turkish_chars = [
            "ç",
            "ğ",
            "ı",
            "ş",
            "ü",
            "ö",
            "Ç",
            "Ğ",
            "İ",
            "Ş",
            "Ü",
            "Ö",
        ]
        self.turkish_edu_words = [
            "konu",
            "ders",
            "anlatım",
            "öğretmen",
            "sınav",
            "türkçe",
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "çözüm",
            "soru",
            "test",
            "örnek",
            "açıklama",
            "tyt",
            "ayt",
            "yks",
            "lgs",
            "kpss",
            "öğrenci",
            "eğitim",
            "kurs",
            "akademi",
            "hazırlık",
            "tekrar",
            "özet",
            "formül",
            "konu anlatımı",
            "soru çözümü",
            "deneme",
        ]

        # İngilizce eğitim kelimeleri (negatif gösterge)
        self.english_edu_words = [
            "tutorial",
            "lesson",
            "lecture",
            "course",
            "learn",
            "study",
            "education",
            "teaching",
            "math",
            "physics",
            "chemistry",
            "biology",
            "english",
            "how to",
            "guide",
            "introduction",
        ]

        # langdetect'i lazy import et
        self._langdetect_available = False
        try:
            import langdetect

            self._langdetect_available = True
            logger.info("langdetect kütüphanesi yüklendi")
        except ImportError:
            logger.warning(
                "langdetect kütüphanesi bulunamadı, temel analiz kullanılacak"
            )

        # Minimum Türkçe skoru - langdetect yoksa daha düşük threshold
        self.min_turkish_score = 0.5 if not self._langdetect_available else 0.7

    async def validate_turkish_content(
        self, video_title: str, video_description: str, channel_name: str
    ) -> TurkishValidationResult:
        """
        Video içeriğinin Türkçe olup olmadığını doğrular

        Args:
            video_title: Video başlığı
            video_description: Video açıklaması
            channel_name: Kanal adı

        Returns:
            TurkishValidationResult: Doğrulama sonucu
        """
        try:
            # Tüm metni birleştir
            full_text = f"{video_title} {video_description}"

            # Türkçe skorunu hesapla
            turkish_score = self.calculate_turkish_score(full_text, channel_name)

            # Dil tespiti yap
            detected_language = self._detect_language(full_text)

            # Türkçe göstergeleri topla
            turkish_indicators = self._find_turkish_indicators(full_text, channel_name)

            # Türkçe olup olmadığını belirle
            is_turkish = turkish_score >= self.min_turkish_score

            result = TurkishValidationResult(
                is_turkish=is_turkish,
                confidence_score=turkish_score,
                detected_language=detected_language,
                turkish_indicators=turkish_indicators,
            )

            logger.info(
                f"Turkish validation: {is_turkish} (score: {turkish_score:.2f}) "
                f"for '{video_title[:50]}...'"
            )

            return result

        except Exception as e:
            logger.error(f"Turkish validation error: {str(e)}")
            # Hata durumunda güvenli tarafta kal
            return TurkishValidationResult(
                is_turkish=False,
                confidence_score=0.0,
                detected_language="unknown",
                turkish_indicators=[],
            )

    def calculate_turkish_score(self, text: str, channel_name: str) -> float:
        """
        Türkçe içerik skoru hesaplar

        Scoring Factors:
        - Türkçe karakterler (ç, ğ, ı, ş, ü, ö): +0.2
        - Türkçe eğitim kelimeleri: +0.3
        - Güvenilir Türkçe kanal: +0.3
        - Dil tespiti (langdetect): +0.2

        Args:
            text: Analiz edilecek metin
            channel_name: Kanal adı

        Returns:
            float: 0.0-1.0 arası skor
        """
        score = 0.0
        text_lower = text.lower()

        # 1. Türkçe karakterler kontrolü (max 0.2)
        turkish_char_count = sum(1 for char in self.turkish_chars if char in text)
        if turkish_char_count > 0:
            # Her 5 Türkçe karakter için 0.05 puan, max 0.2
            char_score = min(turkish_char_count / 5 * 0.05, 0.2)
            score += char_score
            logger.debug(
                f"Turkish chars score: {char_score:.2f} ({turkish_char_count} chars)"
            )

        # 2. Türkçe eğitim kelimeleri (max 0.3)
        turkish_word_count = sum(
            1 for word in self.turkish_edu_words if word in text_lower
        )
        if turkish_word_count > 0:
            # Her kelime için 0.05 puan, max 0.3
            word_score = min(turkish_word_count * 0.05, 0.3)
            score += word_score
            logger.debug(
                f"Turkish words score: {word_score:.2f} ({turkish_word_count} words)"
            )

        # 3. İngilizce kelime cezası (max -0.2)
        english_word_count = sum(
            1 for word in self.english_edu_words if word in text_lower
        )
        if english_word_count > 0:
            english_penalty = min(english_word_count * 0.05, 0.2)
            score -= english_penalty
            logger.debug(
                f"English penalty: -{english_penalty:.2f} ({english_word_count} words)"
            )

        # 4. Güvenilir Türkçe kanal kontrolü (max 0.3)
        if self.is_trusted_turkish_channel(channel_name):
            channel_score = (
                TRUSTED_TURKISH_CHANNELS.get(channel_name, {}).get("weight", 0.85) * 0.3
            )
            score += channel_score
            logger.debug(f"Trusted channel score: {channel_score:.2f}")

        # 5. Dil tespiti (langdetect) (max 0.2)
        if self._langdetect_available and len(text) > 20:
            try:
                import langdetect

                detected_lang = langdetect.detect(text)
                if detected_lang == "tr":
                    score += 0.2
                    logger.debug("Language detection: Turkish (+0.2)")
                else:
                    logger.debug(f"Language detection: {detected_lang} (no bonus)")
            except Exception as e:
                logger.debug(f"Language detection failed: {str(e)}")

        # Skoru 0-1 arasında sınırla
        final_score = max(0.0, min(score, 1.0))

        return final_score

    def is_trusted_turkish_channel(self, channel_name: str) -> bool:
        """
        Güvenilir Türkçe eğitim kanalı kontrolü

        Args:
            channel_name: Kanal adı

        Returns:
            bool: Güvenilir kanal ise True
        """
        if not channel_name:
            return False

        # Tam eşleşme kontrolü
        if channel_name in TRUSTED_TURKISH_CHANNELS:
            return True

        # Case-insensitive eşleşme kontrolü
        channel_lower = channel_name.lower().strip()

        # Önce tam eşleşme dene
        for trusted_channel in TRUSTED_TURKISH_CHANNELS.keys():
            if trusted_channel.lower() == channel_lower:
                return True

        # Kısmi eşleşme kontrolü
        for trusted_channel in TRUSTED_TURKISH_CHANNELS.keys():
            trusted_lower = trusted_channel.lower()
            if trusted_lower in channel_lower or channel_lower in trusted_lower:
                return True

        return False

    def _detect_language(self, text: str) -> str:
        """
        Metin dilini tespit et

        Args:
            text: Analiz edilecek metin

        Returns:
            str: Tespit edilen dil kodu (tr, en, unknown)
        """
        if not text or len(text) < 10:
            return "unknown"

        # langdetect kullan
        if self._langdetect_available:
            try:
                import langdetect

                detected = langdetect.detect(text)
                return detected
            except Exception as e:
                logger.debug(f"Language detection error: {str(e)}")

        # Fallback: Basit Türkçe karakter analizi
        turkish_char_count = sum(1 for char in self.turkish_chars if char in text)
        if turkish_char_count >= 3:
            return "tr"

        return "unknown"

    def _find_turkish_indicators(self, text: str, channel_name: str) -> List[str]:
        """
        Türkçe göstergeleri bul

        Args:
            text: Analiz edilecek metin
            channel_name: Kanal adı

        Returns:
            List[str]: Bulunan Türkçe göstergeler
        """
        indicators = []
        text_lower = text.lower()

        # Türkçe karakterler
        found_chars = [char for char in self.turkish_chars if char in text]
        if found_chars:
            indicators.append(f"turkish_chars: {', '.join(set(found_chars[:5]))}")

        # Türkçe eğitim kelimeleri
        found_words = [word for word in self.turkish_edu_words if word in text_lower]
        if found_words:
            indicators.append(f"turkish_words: {', '.join(found_words[:5])}")

        # Güvenilir kanal
        if self.is_trusted_turkish_channel(channel_name):
            indicators.append(f"trusted_channel: {channel_name}")

        # Dil tespiti
        detected_lang = self._detect_language(text)
        if detected_lang == "tr":
            indicators.append("language_detection: Turkish")

        return indicators

    def get_channel_info(self, channel_name: str) -> Optional[dict]:
        """
        Kanal bilgilerini al

        Args:
            channel_name: Kanal adı

        Returns:
            Optional[dict]: Kanal bilgileri veya None
        """
        return TRUSTED_TURKISH_CHANNELS.get(channel_name)

    def get_all_trusted_channels(self) -> dict:
        """
        Tüm güvenilir kanalları al

        Returns:
            dict: Güvenilir kanallar sözlüğü
        """
        return TRUSTED_TURKISH_CHANNELS.copy()

    async def filter_videos(
        self,
        videos: List[Any],
        min_relevance: float = 0.7,
        target_difficulty: str = "orta",
        language: str = "tr",
        subject: Optional[str] = None,
    ) -> List[Any]:
        """
        Videoları filtrele ve skorla

        Filtering criteria:
        1. Language: Türkçe olmalı (>0.8 confidence)
        2. Relevance: Konu ile alakalı olmalı (>0.7 score)
        3. Difficulty: Seviye uyumlu olmalı (±1 level)

        Args:
            videos: Filtrelenecek video listesi
            min_relevance: Minimum relevance skoru (0-1)
            target_difficulty: Hedef zorluk seviyesi
            language: Hedef dil (default: 'tr')
            subject: Konu (opsiyonel, relevance scoring için)

        Returns:
            List[Any]: Filtrelenmiş ve sıralanmış video listesi
        """
        try:
            filter_results = []

            for video in videos:
                result = await self._evaluate_video(
                    video, min_relevance, target_difficulty, language, subject
                )
                filter_results.append(result)

            # Sadece geçenleri al
            passed_videos = [r.video for r in filter_results if r.passed]

            # Overall score'a göre sırala
            passed_videos.sort(key=lambda v: self._get_video_score(v), reverse=True)

            logger.info(
                f"Filtered {len(videos)} videos -> {len(passed_videos)} passed "
                f"(min_relevance={min_relevance}, target_difficulty={target_difficulty})"
            )

            return passed_videos

        except Exception as e:
            logger.error(f"Video filtering error: {str(e)}")
            # Hata durumunda orijinal listeyi döndür
            return videos

    async def _evaluate_video(
        self,
        video: Any,
        min_relevance: float,
        target_difficulty: str,
        language: str,
        subject: Optional[str],
    ) -> FilterResult:
        """
        Tek bir videoyu değerlendir

        Args:
            video: Video objesi (dict veya VideoResponse)
            min_relevance: Minimum relevance skoru
            target_difficulty: Hedef zorluk seviyesi
            language: Hedef dil
            subject: Konu

        Returns:
            FilterResult: Değerlendirme sonucu
        """
        try:
            # Video bilgilerini al
            title = self._get_video_attr(video, "title", "")
            description = self._get_video_attr(video, "description", "")
            channel = self._get_video_attr(video, "channel", "")
            video_subject = self._get_video_attr(video, "subject", subject or "")
            video_difficulty = self._get_video_attr(video, "difficulty", "orta")

            # 1. Language detection
            language_score = self._detect_language_score(title, description, channel)

            # 2. Relevance scoring
            relevance_score = self._calculate_relevance(
                title, description, video_subject, subject
            )

            # 3. Difficulty matching
            difficulty_match = self._match_difficulty(
                video_difficulty, target_difficulty
            )

            # 4. Overall score (weighted average)
            overall_score = (
                language_score * 0.3 + relevance_score * 0.5 + difficulty_match * 0.2
            )

            # 5. Pass/fail decision
            failure_reasons = []

            # Adjust language threshold based on langdetect availability
            min_language_score = 0.8 if self._langdetect_available else 0.5

            if language_score < min_language_score:
                failure_reasons.append(
                    f"Low language score: {language_score:.2f} < {min_language_score}"
                )

            if relevance_score < min_relevance:
                failure_reasons.append(
                    f"Low relevance: {relevance_score:.2f} < {min_relevance}"
                )

            if difficulty_match < 0.5:
                failure_reasons.append(
                    f"Poor difficulty match: {difficulty_match:.2f} < 0.5"
                )

            passed = (
                language_score >= min_language_score
                and relevance_score >= min_relevance
                and difficulty_match >= 0.5
                and overall_score >= 0.6  # Slightly lower threshold
            )

            return FilterResult(
                video=video,
                language_score=language_score,
                relevance_score=relevance_score,
                difficulty_match=difficulty_match,
                overall_score=overall_score,
                passed=passed,
                failure_reasons=failure_reasons,
            )

        except Exception as e:
            logger.error(f"Video evaluation error: {str(e)}")
            # Hata durumunda videoyu geçir
            return FilterResult(
                video=video,
                language_score=0.0,
                relevance_score=0.0,
                difficulty_match=0.0,
                overall_score=0.0,
                passed=False,
                failure_reasons=[f"Evaluation error: {str(e)}"],
            )

    def _detect_language_score(
        self, title: str, description: str, channel: str
    ) -> float:
        """
        Dil tespiti - multiple signals

        Signals:
        1. Title language detection
        2. Description language detection
        3. Turkish character presence
        4. Channel language (if known)

        Args:
            title: Video başlığı
            description: Video açıklaması
            channel: Kanal adı

        Returns:
            float: Language score (0-1)
        """
        scores = []

        # 1. Title language
        try:
            if self._langdetect_available and title and len(title) > 10:
                import langdetect

                title_lang = langdetect.detect(title)
                scores.append(1.0 if title_lang == "tr" else 0.0)
        except Exception:
            pass

        # 2. Description language
        if description and len(description) > 20:
            try:
                if self._langdetect_available:
                    import langdetect

                    desc_lang = langdetect.detect(description)
                    scores.append(1.0 if desc_lang == "tr" else 0.0)
            except Exception:
                pass

        # 3. Turkish character presence
        turkish_char_ratio = self._calculate_turkish_char_ratio(title)
        scores.append(turkish_char_ratio)

        # 4. Trusted channel bonus
        if self.is_trusted_turkish_channel(channel):
            scores.append(1.0)

        # 5. Turkish education words
        text = f"{title} {description}".lower()
        turkish_word_count = sum(1 for word in self.turkish_edu_words if word in text)
        if turkish_word_count > 0:
            scores.append(min(1.0, turkish_word_count / 3))

        return sum(scores) / len(scores) if scores else 0.5

    def _calculate_turkish_char_ratio(self, text: str) -> float:
        """
        Türkçe karakter oranı hesapla

        Args:
            text: Analiz edilecek metin

        Returns:
            float: Türkçe karakter oranı (0-1)
        """
        if not text:
            return 0.0

        turkish_count = sum(1 for c in text if c in self.turkish_chars)
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return 0.0

        # Türkçe karakterler varsa bonus
        return min(1.0, turkish_count / total_alpha * 5)

    def _calculate_relevance(
        self,
        title: str,
        description: str,
        video_subject: str,
        target_subject: Optional[str],
    ) -> float:
        """
        Konu alakası hesapla

        Factors:
        1. Subject keyword match
        2. Sub-topic keyword match
        3. Title-subject semantic similarity
        4. Description-subject semantic similarity

        Args:
            title: Video başlığı
            description: Video açıklaması
            video_subject: Video konusu
            target_subject: Hedef konu

        Returns:
            float: Relevance score (0-1)
        """
        if not target_subject:
            # Hedef konu belirtilmemişse video konusunu kullan
            target_subject = video_subject

        if not target_subject:
            return 0.5  # Unknown subject

        subject_lower = target_subject.lower()

        # Taxonomy'den konu bilgilerini al
        taxonomy = SUBJECT_TAXONOMY.get(subject_lower, {})

        if not taxonomy:
            # Taxonomy'de yoksa basit keyword matching
            return 1.0 if subject_lower in title.lower() else 0.5

        # 1. Main keyword match
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""

        main_keyword_score = 0.0
        for keyword in taxonomy.get("keywords", []):
            if keyword in title_lower:
                main_keyword_score += 0.3
            if keyword in desc_lower:
                main_keyword_score += 0.1

        main_keyword_score = min(1.0, main_keyword_score)

        # 2. Sub-topic match
        sub_topic_score = 0.0
        for topic, keywords in taxonomy.get("sub_topics", {}).items():
            for keyword in keywords:
                if keyword in title_lower:
                    sub_topic_score += 0.2
                if keyword in desc_lower:
                    sub_topic_score += 0.1

        sub_topic_score = min(1.0, sub_topic_score)

        # 3. Weighted average
        relevance_score = main_keyword_score * 0.6 + sub_topic_score * 0.4

        return relevance_score

    def _match_difficulty(self, video_difficulty: str, target_difficulty: str) -> float:
        """
        Zorluk seviyesi uyumu

        Difficulty levels: başlangıç (1), orta (2), ileri (3)
        Match score: 1.0 (exact), 0.7 (±1), 0.3 (±2)

        Args:
            video_difficulty: Video zorluk seviyesi
            target_difficulty: Hedef zorluk seviyesi

        Returns:
            float: Difficulty match score (0-1)
        """
        difficulty_map = {
            "başlangıç": 1,
            "kolay": 1,
            "temel": 1,
            "orta": 2,
            "normal": 2,
            "zor": 3,
            "ileri": 3,
            "advanced": 3,
        }

        video_level = difficulty_map.get(video_difficulty.lower(), 2)
        target_level = difficulty_map.get(target_difficulty.lower(), 2)

        diff = abs(video_level - target_level)

        if diff == 0:
            return 1.0  # Exact match
        elif diff == 1:
            return 0.7  # Close match (±1 level tolerance)
        else:
            return 0.3  # Poor match

    def _get_video_attr(self, video: Any, attr: str, default: Any = None) -> Any:
        """
        Video attribute'unu al (dict veya object)

        Args:
            video: Video objesi
            attr: Attribute adı
            default: Default değer

        Returns:
            Any: Attribute değeri
        """
        if isinstance(video, dict):
            return video.get(attr, default)
        else:
            return getattr(video, attr, default)

    def _get_video_score(self, video: Any) -> float:
        """
        Video skorunu al

        Args:
            video: Video objesi

        Returns:
            float: Video skoru
        """
        return self._get_video_attr(video, "quality_score", 0.0)

    def get_subject_taxonomy(self, subject: str) -> Optional[Dict[str, Any]]:
        """
        Konu taxonomy'sini al

        Args:
            subject: Konu adı

        Returns:
            Optional[Dict]: Taxonomy bilgileri veya None
        """
        return SUBJECT_TAXONOMY.get(subject.lower())

    def get_all_subjects(self) -> List[str]:
        """
        Tüm desteklenen konuları al

        Returns:
            List[str]: Konu listesi
        """
        return list(SUBJECT_TAXONOMY.keys())


# Global instance
turkish_content_filter = TurkishContentFilter()


async def get_turkish_content_filter() -> TurkishContentFilter:
    """Turkish content filter instance'ını al"""
    return turkish_content_filter
