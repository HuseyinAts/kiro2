"""
Semantic YouTube Video Search
Embedding benzerliği ile ders-konu-zorluk eşleştirmesi
"""

import logging
import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import aiohttp
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class SemanticVideoMatch:
    """Semantic benzerlik ile video eşleştirmesi"""

    video_id: str
    title: str
    channel: str
    channel_id: str
    description: str
    thumbnail: str
    duration: str
    view_count: int
    upload_date: str
    url: str

    # Semantic scores
    semantic_similarity: float  # Query ile semantik benzerlik
    subject_relevance: float  # Konu relevansı
    difficulty_match: float  # Zorluk seviyesi uyumu
    quality_score: float  # Genel kalite skoru
    language_score: float  # Türkçe dil skoru

    # Combined score
    combined_score: float  # Tüm skorların ağırlıklı ortalaması


class SemanticYouTubeSearch:
    """Embedding tabanlı semantic YouTube video arama"""

    def __init__(self):
        self.model = None
        self.embeddings_cache = {}
        self.cache_file = Path("semantic_cache.pkl")

        # Türkçe destekli embedding modeli - Alternatives
        self.model_names = [
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "sentence-transformers/distiluse-base-multilingual-cased",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            "all-MiniLM-L6-v2",  # English fallback but works well
        ]
        self.model_name = self.model_names[0]

        # Konu-zorluk semantic vektörleri (önceden hesaplanmış)
        self.subject_embeddings = {}
        self.difficulty_embeddings = {}

        # YouTube API setup
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session: aiohttp.ClientSession | None = None

        # Türkçe eğitim kanalları — from canonical source
        from core.youtube_channels import TRUSTED_TURKISH_CHANNELS

        self.trusted_channels = {
            name: {"weight": data["weight"], "subjects": data.get("subjects") or "all"}
            for name, data in TRUSTED_TURKISH_CHANNELS.items()
        }

    async def initialize_model(self):
        """Embedding modelini başlat - multiple fallbacks"""
        if self.model is None:
            for model_name in self.model_names:
                try:
                    logger.info(f"Semantic model yükleniyor: {model_name}")

                    # HuggingFace Hub auth bypass

                    # Direct model loading without auth
                    self.model = SentenceTransformer(model_name, token=False)
                    self.model_name = model_name

                    # Test encoding (validates model works, result not needed)
                    self.model.encode(["test sentence"])

                    # Konu embeddings'lerini hesapla
                    await self._precompute_subject_embeddings()

                    # Cache'i yükle
                    await self._load_cache()

                    logger.info(f"Semantic model hazır: {model_name}")
                    return  # Success - exit loop

                except Exception as e:
                    logger.warning(f"Model {model_name} yüklenemedi: {e!s}")
                    self.model = None
                    continue

            # All models failed
            logger.error("Tüm embedding modelleri başarısız - fallback moda geçiliyor")
            await self._initialize_fallback_embeddings()

    async def _precompute_subject_embeddings(self):
        """Konu ve zorluk seviyelerinin embeddings'lerini önceden hesapla"""
        if not self.model:
            return

        # Konu tanımları (Türkçe)
        subject_definitions = {
            "matematik": "matematik temel kavramlar sayılar fonksiyonlar türev integral limit geometri",
            "fizik": "fizik hareket kuvvet enerji elektrik manyetizma dalga ışık mekanik",
            "kimya": "kimya atom molekül periyodik sistem reaksiyon asit baz organik",
            "turkce": "türkçe dil bilgisi anlam sözcük metin okuma yazma edebiyat",
            "biyoloji": "biyoloji hücre genetik evrim ekoloji anatomi fizyoloji",
            "tarih": "tarih osmanlı cumhuriyet savaş devrim reform medeniyet",
            "geometri": "geometri açı üçgen dörtgen çember daire alan hacim",
            "cografya": "coğrafya harita iklim nüfus yerleşme bölge deprem",
            "edebiyat": "edebiyat şiir roman hikaye divan halk tanzimat",
        }

        # Zorluk seviyesi tanımları
        difficulty_definitions = {
            "baslangic": "temel kolay başlangıç giriş basit anlaşılır",
            "orta": "orta seviye normal standart tipik",
            "ileri": "ileri zor karmaşık detaylı derin analiz",
            "sinava_ozel": "sınav tyt ayt ydt örnek soru test çözüm",
        }

        # Embeddings hesapla
        for subject, definition in subject_definitions.items():
            self.subject_embeddings[subject] = self.model.encode([definition])[0]

        for difficulty, definition in difficulty_definitions.items():
            self.difficulty_embeddings[difficulty] = self.model.encode([definition])[0]

        logger.info(
            f"Embeddings hesaplandı: {len(self.subject_embeddings)} konu, {len(self.difficulty_embeddings)} zorluk"
        )

    async def _load_cache(self):
        """Embedding cache'ini yükle"""
        try:
            if self.cache_file.exists():
                with self.cache_file.open("rb") as f:
                    self.embeddings_cache = pickle.load(f)
                logger.info(
                    f"Embedding cache yüklendi: {len(self.embeddings_cache)} item"
                )
        except Exception as e:
            logger.warning(f"Cache yüklenemedi: {e!s}")
            self.embeddings_cache = {}

    async def _save_cache(self):
        """Embedding cache'ini kaydet"""
        try:
            with self.cache_file.open("wb") as f:
                pickle.dump(self.embeddings_cache, f)
        except Exception as e:
            logger.warning(f"Cache kaydedilemedi: {e!s}")

    async def _initialize_fallback_embeddings(self):
        """Fallback embedding sistemi - offline TF-IDF based"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Türkçe stopwords
            turkish_stopwords = [
                "bir",
                "bu",
                "ve",
                "ile",
                "için",
                "olan",
                "olarak",
                "da",
                "de",
                "en",
                "çok",
                "daha",
                "gibi",
                "kadar",
                "sonra",
                "böyle",
                "şu",
            ]

            # TF-IDF vectorizer for Turkish
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words=turkish_stopwords,
                max_features=1000,
                ngram_range=(1, 2),
                lowercase=True,
            )

            # Sample Turkish education corpus
            education_corpus = [
                "matematik temel kavramlar sayılar fonksiyonlar",
                "fizik hareket kuvvet enerji elektrik manyetizma",
                "kimya atom molekül periyodik sistem reaksiyon",
                "türkçe dil bilgisi anlam sözcük metin okuma",
                "tyt ayt sınav hazırlık test örnek sorular",
                "başlangıç temel kolay anlaşılır basit",
                "orta seviye normal tipik standart",
                "ileri zor karmaşık detaylı derin analiz",
                "konu anlatımı ders öğretmen eğitim",
            ]

            # Fit vectorizer
            self.tfidf_vectorizer.fit(education_corpus)

            # Precompute subject/difficulty vectors
            await self._precompute_subject_embeddings()

            logger.info("Fallback TF-IDF embedding sistemi hazır")

        except Exception as e:
            logger.error(f"Fallback embedding hatası: {e!s}", exc_info=True)

    def _get_text_embedding(self, text: str) -> np.ndarray:
        """Text'in embedding'ini hesapla (cache + fallback)"""
        # Cache kontrolü
        cache_key = hash(text.lower().strip())
        if cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]

        try:
            if self.model:
                # SentenceTransformer embedding
                embedding = self.model.encode([text])[0]
            elif hasattr(self, "tfidf_vectorizer"):
                # TF-IDF fallback
                tfidf_vector = self.tfidf_vectorizer.transform([text]).toarray()[0]
                embedding = tfidf_vector
            else:
                # Simple hash fallback
                words = text.lower().split()[:20]
                embedding = np.array(
                    [hash(word) % 1000 for word in words] + [0] * (20 - len(words))
                )

            # Cache'e kaydet
            self.embeddings_cache[cache_key] = embedding
            return embedding

        except Exception as e:
            logger.warning(f"Embedding hesaplama hatası: {e!s}")
            # Final fallback
            words = text.lower().split()[:10]
            return np.array(
                [hash(word) % 100 for word in words] + [0] * (10 - len(words))
            )

    def _calculate_semantic_similarity(
        self, query_embedding: np.ndarray, video_text: str
    ) -> float:
        """Query ile video metni arasındaki semantic benzerlik"""
        video_embedding = self._get_text_embedding(video_text)

        try:
            # Ensure same dimensionality
            if len(query_embedding) != len(video_embedding):
                # Pad or truncate to match
                min_len = min(len(query_embedding), len(video_embedding))
                query_embedding = query_embedding[:min_len]
                video_embedding = video_embedding[:min_len]

            if self.model or hasattr(self, "tfidf_vectorizer"):
                # Cosine similarity for real embeddings
                similarity = cosine_similarity([query_embedding], [video_embedding])[0][
                    0
                ]
                # Normalize to 0-1 range
                similarity = (similarity + 1) / 2  # From [-1,1] to [0,1]
            else:
                # Simple overlap similarity for hash-based
                query_set = set(query_embedding)
                video_set = set(video_embedding)
                intersection = len(query_set & video_set)
                union = len(query_set | video_set)
                similarity = intersection / max(union, 1)

            return float(max(0.0, min(similarity, 1.0)))

        except Exception as e:
            logger.warning(f"Similarity hesaplama hatası: {e!s}")
            return 0.3  # Default moderate similarity

    def _calculate_subject_relevance(self, video_text: str, subject: str) -> float:
        """Video'nun konuya semantic relevansi"""
        if subject not in self.subject_embeddings:
            return 0.5

        video_embedding = self._get_text_embedding(video_text)
        subject_embedding = self.subject_embeddings[subject]

        if self.model:
            relevance = cosine_similarity([video_embedding], [subject_embedding])[0][0]
        else:
            # Fallback: Keyword overlap
            subject_words = subject.split()
            video_words = video_text.lower().split()
            overlap = len(set(subject_words) & set(video_words)) / len(subject_words)
            relevance = overlap

        return float(max(0.0, relevance))

    def _calculate_difficulty_match(self, video_text: str, difficulty: str) -> float:
        """Video'nun zorluk seviyesi uyumu"""
        if difficulty not in self.difficulty_embeddings:
            return 0.5

        video_embedding = self._get_text_embedding(video_text)
        difficulty_embedding = self.difficulty_embeddings[difficulty]

        if self.model:
            match = cosine_similarity([video_embedding], [difficulty_embedding])[0][0]
        else:
            # Fallback: Simple matching
            difficulty_words = {
                "baslangic": ["temel", "kolay", "başlangıç", "basit"],
                "orta": ["orta", "normal", "tipik"],
                "ileri": ["ileri", "zor", "karmaşık", "detaylı"],
                "sinava_ozel": ["sınav", "test", "örnek"],
            }
            words = difficulty_words.get(difficulty, [])
            video_words = video_text.lower()
            match = sum(1 for word in words if word in video_words) / max(len(words), 1)

        return float(max(0.0, match))

    async def semantic_search_videos(
        self,
        subject: str,
        exam_type: str = "TYT",
        difficulty: str = "orta",
        max_results: int = 10,
        query_text: str | None = None,
    ) -> list[SemanticVideoMatch]:
        """Semantic similarity ile video arama"""

        # Model başlatma
        await self.initialize_model()

        # Turkish normalization (defense-in-depth)
        import unicodedata

        subject = unicodedata.normalize("NFC", subject)
        subject = subject.replace("İ", "i").replace("I", "ı").lower()

        # Query oluştur
        if not query_text:
            query_text = f"{exam_type} {subject} {difficulty} konu anlatımı ders"

        query_embedding = self._get_text_embedding(query_text)

        logger.info(f"Semantic arama: '{query_text}'")

        try:
            # YouTube API'den videolar al
            raw_videos = await self._fetch_youtube_videos(
                subject, exam_type, max_results * 2
            )

            if not raw_videos:
                logger.warning("YouTube API'den video alınamadı")
                return []

            # Semantic scoring
            semantic_matches = []

            for video_data in raw_videos:
                try:
                    # Video text (title + description)
                    video_text = f"{video_data.get('title', '')} {video_data.get('description', '')}"

                    # Müzik filtresi
                    if self._is_music_content(
                        video_text, video_data.get("channel", "")
                    ):
                        continue

                    # Semantic skorlar hesapla
                    semantic_similarity = self._calculate_semantic_similarity(
                        query_embedding, video_text
                    )
                    subject_relevance = self._calculate_subject_relevance(
                        video_text, subject
                    )
                    difficulty_match = self._calculate_difficulty_match(
                        video_text, difficulty
                    )

                    # Diğer skorlar
                    quality_score = self._calculate_quality_score(video_data)
                    language_score = self._calculate_turkish_score(video_text)

                    # Kanal güvenilirlik bonusu
                    channel_bonus = self._get_channel_bonus(
                        video_data.get("channel", "")
                    )

                    # Combined score (ağırlıklı)
                    combined_score = (
                        semantic_similarity * 0.3
                        + subject_relevance * 0.25
                        + difficulty_match * 0.2
                        + quality_score * 0.1
                        + language_score * 0.1
                        + channel_bonus * 0.05
                    )

                    # Minimum threshold
                    if combined_score < 0.4:
                        continue

                    # SemanticVideoMatch oluştur
                    match = SemanticVideoMatch(
                        video_id=video_data.get("video_id", ""),
                        title=video_data.get("title", ""),
                        channel=video_data.get("channel", ""),
                        channel_id=video_data.get("channel_id", ""),
                        description=video_data.get("description", "")[:200] + "...",
                        thumbnail=video_data.get("thumbnail", ""),
                        duration=video_data.get("duration", "00:00"),
                        view_count=video_data.get("view_count", 0),
                        upload_date=video_data.get("upload_date", ""),
                        url=f"https://www.youtube.com/embed/{video_data.get('video_id', '')}",
                        semantic_similarity=semantic_similarity,
                        subject_relevance=subject_relevance,
                        difficulty_match=difficulty_match,
                        quality_score=quality_score,
                        language_score=language_score,
                        combined_score=combined_score,
                    )

                    semantic_matches.append(match)

                except Exception as e:
                    logger.error(f"Video scoring hatası: {e!s}", exc_info=True)
                    continue

            # Combined score'a göre sırala
            semantic_matches.sort(key=lambda x: x.combined_score, reverse=True)

            # Cache'i kaydet
            await self._save_cache()

            logger.info(
                f"Semantic arama tamamlandı: {len(semantic_matches[:max_results])} video"
            )

            return semantic_matches[:max_results]

        except Exception as e:
            logger.error(f"Semantic arama hatası: {e!s}", exc_info=True)
            return []

    async def _fetch_youtube_videos(
        self, subject: str, exam_type: str, max_results: int
    ) -> list[dict]:
        """YouTube API'den video verilerini al"""
        # Bu kısım mevcut real_youtube_api'den adaptasyonu olacak
        # Şimdilik mock data dönüyoruz

        return [
            {
                "video_id": "VuwKz2TVVKA",
                "title": f"{exam_type} {subject.title()} - Temel Kavramlar ve Uygulamalar",
                "channel": "TonguçAkademi",
                "channel_id": "UCQaEgq0uA7wHQlUkE3o8L4w",
                "description": f"{subject} dersi temel kavramlar {exam_type} sınavına hazırlanma konu anlatımı",
                "thumbnail": "https://img.youtube.com/vi/VuwKz2TVVKA/maxresdefault.jpg",
                "duration": "18:43",
                "view_count": 125000,
                "upload_date": "2024-09-15",
            },
            {
                "video_id": "L_42C1qoQTE",
                "title": f"{exam_type} {subject.title()} - İleri Seviye Problemler",
                "channel": "KAMP Online",
                "channel_id": "UCkamp_online",
                "description": f"{subject} ileri seviye sorular detaylı çözümler {exam_type} sınav hazırlık",
                "thumbnail": "https://img.youtube.com/vi/L_42C1qoQTE/maxresdefault.jpg",
                "duration": "32:15",
                "view_count": 89000,
                "upload_date": "2024-09-10",
            },
        ]

    def _is_music_content(self, text: str, channel: str) -> bool:
        """Müzik içeriği kontrolü"""
        music_terms = ["müzik", "music", "şarkı", "song", "cover", "remix"]
        text_lower = f"{text} {channel}".lower()
        return any(term in text_lower for term in music_terms)

    def _calculate_quality_score(self, video_data: dict) -> float:
        """Video kalite skoru"""
        view_count = video_data.get("view_count", 0)

        score = 0.5
        if 10000 <= view_count <= 500000:
            score += 0.3
        elif view_count > 500000:
            score += 0.2

        return min(score, 1.0)

    def _calculate_turkish_score(self, text: str) -> float:
        """Türkçe dil skoru"""
        turkish_chars = ["ç", "ğ", "ı", "ş", "ü", "ö"]
        turkish_words = ["konu", "ders", "anlatım", "öğretmen", "sınav", "türkçe"]

        text_lower = text.lower()

        char_score = sum(1 for char in turkish_chars if char in text_lower) * 0.1
        word_score = sum(1 for word in turkish_words if word in text_lower) * 0.1

        return min(char_score + word_score + 0.5, 1.0)

    def _get_channel_bonus(self, channel: str) -> float:
        """Güvenilir kanal bonusu"""
        channel_lower = channel.lower()
        for trusted_channel, data in self.trusted_channels.items():
            if trusted_channel.lower() in channel_lower:
                return data["weight"] - 1.0  # 0.0-0.2 bonus
        return 0.0

    async def close(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
        await self._save_cache()

    # FIX Resource Cleanup: Context manager implementation
    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session cleanup"""
        await self.close()


# Global instance
semantic_youtube_search = SemanticYouTubeSearch()


async def get_semantic_youtube_search() -> SemanticYouTubeSearch:
    """Semantic YouTube search instance'ını al"""
    return semantic_youtube_search
