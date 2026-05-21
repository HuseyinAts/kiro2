"""
Subject Relevance Scorer Service
Video içeriğinin ders ve konu ile uygunluğunu skorlar
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from core.turkish_nlp_utils import normalize_tr

logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """Konu uygunluk skoru"""

    overall_score: float  # 0.0-1.0
    subject_match: float  # Ders eşleşme skoru
    topic_match: float  # Konu eşleşme skoru
    semantic_similarity: float  # Semantik benzerlik skoru
    keyword_overlap: float  # Anahtar kelime örtüşme skoru


# Konu anahtar kelime mapping'leri
SUBJECT_KEYWORDS = {
    "matematik": {
        "core": [
            "matematik",
            "sayı",
            "fonksiyon",
            "türev",
            "integral",
            "limit",
            "geometri",
            "cebir",
        ],
        "topics": {
            "türev": [
                "türev",
                "diferansiyel",
                "eğim",
                "teğet",
                "türev alma",
                "türev kuralları",
            ],
            "integral": [
                "integral",
                "alan",
                "hacim",
                "belirsiz",
                "belirli integral",
                "integrasyon",
            ],
            "limit": ["limit", "süreklilik", "yakınsama", "limit hesabı", "sonsuz"],
            "fonksiyon": ["fonksiyon", "grafik", "denklem", "eşitlik", "bağıntı"],
            "geometri": [
                "geometri",
                "üçgen",
                "dörtgen",
                "çember",
                "alan",
                "çevre",
                "açı",
            ],
            "cebir": ["cebir", "denklem", "eşitsizlik", "polinom", "köklü sayılar"],
            "trigonometri": [
                "trigonometri",
                "sinüs",
                "kosinüs",
                "tanjant",
                "açı",
                "birim çember",
            ],
            "olasılık": [
                "olasılık",
                "permütasyon",
                "kombinasyon",
                "istatistik",
                "veri",
            ],
            "logaritma": ["logaritma", "üstel", "log", "ln", "e sayısı"],
        },
    },
    "fizik": {
        "core": [
            "fizik",
            "kuvvet",
            "hareket",
            "enerji",
            "elektrik",
            "manyetizma",
            "ışık",
        ],
        "topics": {
            "hareket": [
                "hız",
                "ivme",
                "yol",
                "zaman",
                "kinematik",
                "düzgün hareket",
                "serbest düşme",
            ],
            "kuvvet": [
                "newton",
                "kütle",
                "ağırlık",
                "sürtünme",
                "dinamik",
                "kuvvet yasaları",
            ],
            "enerji": [
                "iş",
                "güç",
                "potansiyel",
                "kinetik",
                "enerji korunumu",
                "mekanik enerji",
            ],
            "elektrik": ["akım", "voltaj", "direnç", "ohm", "devre", "elektrik yükü"],
            "manyetizma": [
                "mıknatıs",
                "manyetik alan",
                "indüksiyon",
                "elektromanyetik",
            ],
            "ışık": ["ışık", "kırılma", "yansıma", "mercek", "prizma", "optik"],
            "dalga": ["dalga", "frekans", "periyot", "ses", "titreşim", "dalga boyu"],
            "basınç": ["basınç", "sıvı", "gaz", "pascal", "hidrostatik", "atmosfer"],
        },
    },
    "kimya": {
        "core": [
            "kimya",
            "atom",
            "molekül",
            "reaksiyon",
            "element",
            "bileşik",
            "madde",
        ],
        "topics": {
            "atom": [
                "proton",
                "nötron",
                "elektron",
                "periyodik",
                "atom yapısı",
                "çekirdek",
            ],
            "reaksiyon": [
                "asit",
                "baz",
                "oksidasyon",
                "indirgenme",
                "kimyasal reaksiyon",
                "denge",
            ],
            "bileşik": [
                "molekül",
                "bağ",
                "iyonik",
                "kovalent",
                "kimyasal bağ",
                "formül",
            ],
            "çözelti": [
                "çözelti",
                "çözücü",
                "çözünen",
                "derişim",
                "molarite",
                "seyreltme",
            ],
            "gazlar": ["gaz", "basınç", "hacim", "sıcaklık", "ideal gaz", "mol"],
            "organik": ["organik", "karbon", "hidrokarbon", "alkan", "alken", "alkin"],
            "asit-baz": ["asit", "baz", "ph", "nötrleşme", "tuz", "indikatör"],
            "elektrokimya": [
                "elektrokimya",
                "pil",
                "elektroliz",
                "anot",
                "katot",
                "redoks",
            ],
        },
    },
    "biyoloji": {
        "core": ["biyoloji", "hücre", "canlı", "doku", "organ", "sistem", "genetik"],
        "topics": {
            "hücre": [
                "hücre",
                "organelle",
                "mitokondri",
                "çekirdek",
                "zar",
                "sitoplazma",
            ],
            "genetik": [
                "genetik",
                "dna",
                "rna",
                "gen",
                "kromozom",
                "kalıtım",
                "mutasyon",
            ],
            "ekosistem": [
                "ekosistem",
                "besin zinciri",
                "habitat",
                "popülasyon",
                "çevre",
            ],
            "solunum": [
                "solunum",
                "akciğer",
                "oksijen",
                "karbondioksit",
                "gaz alışverişi",
            ],
            "dolaşım": ["dolaşım", "kalp", "kan", "damar", "arter", "ven"],
            "sindirim": ["sindirim", "mide", "bağırsak", "enzim", "besin", "emilim"],
            "fotosentez": [
                "fotosentez",
                "klorofil",
                "güneş",
                "ışık",
                "bitki",
                "oksijen",
            ],
        },
    },
    "türkçe": {
        "core": ["türkçe", "dil", "gramer", "edebiyat", "metin", "yazım", "sözcük"],
        "topics": {
            "gramer": ["gramer", "fiil", "isim", "sıfat", "zarf", "edat", "bağlaç"],
            "edebiyat": ["edebiyat", "şiir", "roman", "hikaye", "edebi tür", "yazar"],
            "yazım": ["yazım", "noktalama", "imla", "büyük harf", "küçük harf"],
            "anlam": ["anlam", "eş anlamlı", "zıt anlamlı", "mecaz", "gerçek anlam"],
            "cümle": ["cümle", "özne", "yüklem", "nesne", "tümleç", "cümle öğeleri"],
        },
    },
    "tarih": {
        "core": ["tarih", "osmanlı", "türk", "devlet", "savaş", "dönem", "medeniyet"],
        "topics": {
            "osmanlı": [
                "osmanlı",
                "padişah",
                "devşirme",
                "tımar",
                "yeniçeri",
                "tanzimat",
            ],
            "cumhuriyet": [
                "cumhuriyet",
                "atatürk",
                "inkılap",
                "reform",
                "kurtuluş savaşı",
            ],
            "ilkçağ": ["ilkçağ", "sümer", "mısır", "yunan", "roma", "medeniyet"],
            "ortaçağ": ["ortaçağ", "selçuklu", "haçlı", "moğol", "feodal"],
        },
    },
    "coğrafya": {
        "core": ["coğrafya", "harita", "iklim", "nüfus", "ekonomi", "bölge", "doğa"],
        "topics": {
            "fiziki": ["dağ", "ova", "akarsu", "göl", "deniz", "iklim", "bitki örtüsü"],
            "beşeri": ["nüfus", "göç", "şehir", "köy", "yerleşme", "kültür"],
            "ekonomik": ["tarım", "sanayi", "ticaret", "ulaşım", "enerji", "maden"],
        },
    },
}


class SubjectRelevanceScorer:
    """
    Konu uygunluk skorlama servisi

    Video başlığı, açıklaması ve etiketlerini analiz ederek
    hedef ders ve konu ile uygunluğunu skorlar.
    """

    def __init__(self):
        """SubjectRelevanceScorer'ı başlat"""
        self.subject_keywords = SUBJECT_KEYWORDS

        # Sentence transformers'ı lazy import et
        self._sentence_transformers_available = False
        self._model = None
        if os.environ.get("TESTING") == "true":
            logger.info("Skipping SentenceTransformer init in test mode")
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            self._sentence_transformers_available = True
            logger.info("Sentence transformers modeli yüklendi")
        except ImportError:
            logger.warning(
                "sentence-transformers kütüphanesi bulunamadı, semantik analiz devre dışı"
            )
        except Exception as e:
            logger.warning(f"Sentence transformers yüklenemedi: {e!s}")

    async def calculate_relevance_score(
        self,
        video_title: str,
        video_description: str,
        video_tags: list[str],
        target_subject: str,
        target_topic: str | None = None,
    ) -> RelevanceScore:
        """
        Video'nun konu ile uygunluk skorunu hesaplar

        Args:
            video_title: Video başlığı
            video_description: Video açıklaması
            video_tags: Video etiketleri
            target_subject: Hedef ders (matematik, fizik, kimya, vb.)
            target_topic: Hedef konu (türev, hareket, atom, vb.) - opsiyonel

        Returns:
            RelevanceScore: Uygunluk skoru detayları
        """
        try:
            # Tüm metni birleştir
            video_text = f"{video_title} {video_description} {' '.join(video_tags)}"
            # FIX: Türkçe normalizasyonu kullan
            video_text_lower = normalize_tr(video_text)

            # Ders normalizasyonu - FIX: Türkçe normalizasyonu kullan
            target_subject = normalize_tr(target_subject).strip()
            target_topic = normalize_tr(target_topic).strip() if target_topic else None

            # 1. Anahtar kelime örtüşme skoru (40%)
            keyword_score = self._calculate_keyword_overlap(
                video_text_lower, target_subject, target_topic
            )

            # 2. Ders eşleşme skoru (25%)
            subject_score = self._calculate_subject_match(
                video_text_lower, target_subject
            )

            # 3. Konu eşleşme skoru (20%)
            topic_score = self._calculate_topic_match(
                video_text_lower, target_subject, target_topic
            )

            # 4. Semantik benzerlik skoru (15%)
            semantic_score = await self._calculate_semantic_similarity(
                video_text, target_subject, target_topic
            )

            # Toplam skor hesapla
            overall_score = (
                keyword_score * 0.40
                + subject_score * 0.25
                + topic_score * 0.20
                + semantic_score * 0.15
            )

            result = RelevanceScore(
                overall_score=overall_score,
                subject_match=subject_score,
                topic_match=topic_score,
                semantic_similarity=semantic_score,
                keyword_overlap=keyword_score,
            )

            logger.info(
                f"Relevance score: {overall_score:.2f} "
                f"(subject: {subject_score:.2f}, topic: {topic_score:.2f}, "
                f"keyword: {keyword_score:.2f}, semantic: {semantic_score:.2f}) "
                f"for '{video_title[:50]}...'"
            )

            return result

        except Exception as e:
            logger.error(f"Relevance scoring error: {e!s}", exc_info=True)
            # Hata durumunda düşük skor döndür
            return RelevanceScore(
                overall_score=0.0,
                subject_match=0.0,
                topic_match=0.0,
                semantic_similarity=0.0,
                keyword_overlap=0.0,
            )

    def _calculate_keyword_overlap(
        self, video_text: str, subject: str, topic: str | None
    ) -> float:
        """
        Anahtar kelime örtüşme oranını hesaplar

        Args:
            video_text: Video metni (lowercase)
            subject: Hedef ders
            topic: Hedef konu (opsiyonel)

        Returns:
            float: 0.0-1.0 arası örtüşme skoru
        """
        score = 0.0

        # Ders anahtar kelimeleri
        subject_data = self.subject_keywords.get(subject, {})
        core_keywords = subject_data.get("core", [])

        if core_keywords:
            # Core keywords eşleşme
            core_matches = sum(1 for kw in core_keywords if kw in video_text)
            core_score = core_matches / len(core_keywords)
            score += core_score * 0.5  # %50 ağırlık
            logger.debug(
                f"Core keywords: {core_matches}/{len(core_keywords)} = {core_score:.2f}"
            )

        # Konu anahtar kelimeleri
        if topic:
            topic_keywords = subject_data.get("topics", {}).get(topic, [])
            if topic_keywords:
                topic_matches = sum(1 for kw in topic_keywords if kw in video_text)
                topic_score = topic_matches / len(topic_keywords)
                score += topic_score * 0.5  # %50 ağırlık
                logger.debug(
                    f"Topic keywords: {topic_matches}/{len(topic_keywords)} = {topic_score:.2f}"
                )
            else:
                # Konu belirtilmiş ama anahtar kelime yok
                score += 0.25  # Kısmi puan
        else:
            # Konu belirtilmemiş
            score += 0.25  # Kısmi puan

        return min(score, 1.0)

    def _calculate_subject_match(self, video_text: str, subject: str) -> float:
        """
        Ders eşleşme skorunu hesaplar

        Args:
            video_text: Video metni (lowercase)
            subject: Hedef ders

        Returns:
            float: 0.0-1.0 arası ders eşleşme skoru
        """
        score = 0.0

        # Ders adı direkt geçiyor mu?
        if subject in video_text:
            score += 0.5
            logger.debug(f"Subject name found: {subject}")

        # Core keywords kontrolü
        subject_data = self.subject_keywords.get(subject, {})
        core_keywords = subject_data.get("core", [])

        if core_keywords:
            # En az 2 core keyword geçmeli
            core_matches = sum(1 for kw in core_keywords if kw in video_text)
            if core_matches >= 2:
                score += 0.3
                logger.debug(f"Multiple core keywords found: {core_matches}")
            elif core_matches == 1:
                score += 0.15
                logger.debug("Single core keyword found")

        # Ders ile ilgili yaygın kelimeler
        subject_related = {
            "matematik": ["mat", "sayısal", "hesap", "problem"],
            "fizik": ["fiz", "sayısal", "deney", "kanun"],
            "kimya": ["kim", "sayısal", "deney", "laboratuvar"],
            "biyoloji": ["bio", "canlı", "yaşam", "doğa"],
            "türkçe": ["dil", "sözel", "metin", "okuma"],
            "tarih": ["sözel", "dönem", "olay", "kronoloji"],
            "coğrafya": ["sözel", "harita", "dünya", "yer"],
        }

        related_words = subject_related.get(subject, [])
        if related_words:
            related_matches = sum(1 for word in related_words if word in video_text)
            if related_matches > 0:
                score += 0.2
                logger.debug(f"Related words found: {related_matches}")

        return min(score, 1.0)

    def _calculate_topic_match(
        self, video_text: str, subject: str, topic: str | None
    ) -> float:
        """
        Konu eşleşme skorunu hesaplar

        Args:
            video_text: Video metni (lowercase)
            subject: Hedef ders
            topic: Hedef konu (opsiyonel)

        Returns:
            float: 0.0-1.0 arası konu eşleşme skoru
        """
        if not topic:
            # Konu belirtilmemiş, nötr skor
            return 0.5

        score = 0.0

        # Konu adı direkt geçiyor mu?
        if topic in video_text:
            score += 0.6
            logger.debug(f"Topic name found: {topic}")

        # Konu anahtar kelimeleri
        subject_data = self.subject_keywords.get(subject, {})
        topic_keywords = subject_data.get("topics", {}).get(topic, [])

        if topic_keywords:
            # En az 1 topic keyword geçmeli
            topic_matches = sum(1 for kw in topic_keywords if kw in video_text)
            if topic_matches >= 3:
                score += 0.4
                logger.debug(f"Multiple topic keywords found: {topic_matches}")
            elif topic_matches >= 1:
                score += 0.2
                logger.debug(f"Some topic keywords found: {topic_matches}")

        return min(score, 1.0)

    async def _calculate_semantic_similarity(
        self, video_text: str, subject: str, topic: str | None
    ) -> float:
        """
        Embedding tabanlı semantik benzerlik hesaplar

        Args:
            video_text: Video metni
            subject: Hedef ders
            topic: Hedef konu (opsiyonel)

        Returns:
            float: 0.0-1.0 arası semantik benzerlik skoru
        """
        if not self._sentence_transformers_available or not self._model:
            # Sentence transformers yok, fallback skor
            logger.debug("Semantic similarity unavailable, using fallback")
            return 0.5

        try:
            # Hedef metni oluştur
            if topic:
                target_text = f"{subject} {topic}"
            else:
                target_text = subject

            # Embeddings hesapla
            video_embedding = self._model.encode(video_text[:500])  # İlk 500 karakter
            target_embedding = self._model.encode(target_text)

            # Cosine similarity hesapla
            import numpy as np

            similarity = np.dot(video_embedding, target_embedding) / (
                np.linalg.norm(video_embedding) * np.linalg.norm(target_embedding)
            )

            # -1 ile 1 arası değeri 0-1 arasına normalize et
            normalized_similarity = (similarity + 1) / 2

            logger.debug(f"Semantic similarity: {normalized_similarity:.2f}")

            return float(normalized_similarity)

        except Exception as e:
            logger.error(f"Semantic similarity calculation error: {e!s}", exc_info=True)
            return 0.5

    def get_subject_keywords(self, subject: str) -> dict[str, Any]:
        """
        Ders için anahtar kelimeleri al

        Args:
            subject: Ders adı

        Returns:
            Dict: Ders anahtar kelimeleri
        """
        return self.subject_keywords.get(normalize_tr(subject), {})

    def get_topic_keywords(self, subject: str, topic: str) -> list[str]:
        """
        Konu için anahtar kelimeleri al

        Args:
            subject: Ders adı
            topic: Konu adı

        Returns:
            List[str]: Konu anahtar kelimeleri
        """
        subject_data = self.subject_keywords.get(normalize_tr(subject), {})
        return subject_data.get("topics", {}).get(normalize_tr(topic), [])

    def get_all_subjects(self) -> list[str]:
        """
        Tüm desteklenen dersleri al

        Returns:
            List[str]: Ders listesi
        """
        return list(self.subject_keywords.keys())

    def get_topics_for_subject(self, subject: str) -> list[str]:
        """
        Ders için tüm konuları al

        Args:
            subject: Ders adı

        Returns:
            List[str]: Konu listesi
        """
        subject_data = self.subject_keywords.get(normalize_tr(subject), {})
        return list(subject_data.get("topics", {}).keys())


# Global instance
subject_relevance_scorer = SubjectRelevanceScorer()


async def get_subject_relevance_scorer() -> SubjectRelevanceScorer:
    """Subject relevance scorer instance'ını al"""
    return subject_relevance_scorer
