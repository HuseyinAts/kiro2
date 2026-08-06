"""
Content Recommendation Service - KIRO2 Eğitim Platformu

Spec REQ-4: Kişiselleştirilmiş içerik öneri sistemi.

Bu servis:
- REQ-4.1: User profile embedding oluşturma
- REQ-4.2: Geçmiş etkileşimleri aggregate etme
- REQ-4.3: Hybrid filtering (collaborative + content-based)
- REQ-4.4: Cold-start fallback (popularity-based)
- REQ-4.5: Recommendation diversity
- REQ-4.6: Click-through rate tracking

Author: KIRO2 Team
Date: 2026-01-15
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from core.chroma_client import create_chromadb_client
from core.config import EmbeddingConfig

logger = logging.getLogger(__name__)


class InteractionType(str, Enum):
    """Kullanıcı etkileşim tipleri."""

    VIEW = "view"
    LIKE = "like"
    COMPLETE = "complete"
    BOOKMARK = "bookmark"
    SHARE = "share"
    SKIP = "skip"
    DISLIKE = "dislike"


# Etkileşim ağırlıkları
INTERACTION_WEIGHTS: dict[InteractionType, float] = {
    InteractionType.VIEW: 0.3,
    InteractionType.LIKE: 1.0,
    InteractionType.COMPLETE: 1.5,
    InteractionType.BOOKMARK: 1.2,
    InteractionType.SHARE: 1.3,
    InteractionType.SKIP: -0.2,
    InteractionType.DISLIKE: -1.0,
}


@dataclass
class UserInteraction:
    """Kullanıcı etkileşim kaydı."""

    user_id: str
    content_id: str
    interaction_type: InteractionType
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class UserProfile:
    """Kullanıcı profil embedding'i."""

    user_id: str
    embedding: list[float]
    interaction_count: int
    last_updated: datetime
    preferred_subjects: list[str] = field(default_factory=list)
    preferred_difficulty: float = 0.0
    is_cold_start: bool = True


@dataclass
class RecommendationResult:
    """Öneri sonucu."""

    content_id: str
    content_preview: str
    score: float
    metadata: dict
    recommendation_type: (
        str  # "content_based", "collaborative", "popularity", "diversity"
    )


@dataclass
class RecommendationResponse:
    """Öneri response'u."""

    user_id: str
    recommendations: list[RecommendationResult]
    is_cold_start: bool
    strategy_used: str
    diversity_score: float
    generated_at: datetime = field(default_factory=datetime.now)


class ContentRecommendationService:
    """
    Kişiselleştirilmiş içerik öneri servisi.

    Spec REQ-4 implementasyonu.

    Hybrid filtering approach:
    - Content-based: İçerik benzerliği (embedding)
    - Collaborative: Kullanıcı benzerliği
    - Popularity: Trend içerikler
    """

    # Konfigürasyon
    COLD_START_THRESHOLD = 5  # Bu kadar etkileşimden az = cold start
    CONTENT_WEIGHT = 0.6  # Hybrid: content-based ağırlığı
    COLLABORATIVE_WEIGHT = 0.3  # Hybrid: collaborative ağırlığı
    POPULARITY_WEIGHT = 0.1  # Popularity ağırlığı
    DIVERSITY_MIN_TOPICS = 3  # Minimum farklı konu

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "kiro2_content",
    ):
        """
        ContentRecommendationService başlat.

        Args:
            persist_directory: ChromaDB persist dizini (env: CHROMADB_PERSIST_DIR)
            collection_name: Content collection adı
        """
        import os

        self.persist_directory = persist_directory or os.getenv(
            "CHROMADB_PERSIST_DIR", "./vector_db"
        )
        self.collection_name = collection_name
        self._client: chromadb.Client | None = None
        self._collection = None
        self._embedding_model = None
        self._initialized = False

        # In-memory caches
        self._user_profiles: dict[str, UserProfile] = {}
        self._interactions: list[UserInteraction] = []
        self._click_tracking: dict[
            str, dict
        ] = {}  # content_id -> {clicks, impressions}

    async def initialize(self) -> bool:
        """Servisi başlat."""
        if self._initialized:
            return True

        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available")
            return False

        try:
            self._client = create_chromadb_client(
                persist_directory=self.persist_directory,
            )

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )

            if EMBEDDINGS_AVAILABLE:
                model_name = EmbeddingConfig.get_model_name()
                self._embedding_model = SentenceTransformer(model_name)
                logger.info(f"Embedding model loaded: {model_name}")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def _embed_text(self, text: str) -> list[float]:
        """Metin için embedding oluştur."""
        # 2026 Ultra Expert NLP Lens Fix: Normalize Turkish text before embedding
        from core.turkish_nlp_utils import normalize_tr

        text = normalize_tr(text)

        if self._embedding_model is None:
            import hashlib

            hash_bytes = hashlib.sha256(text.encode()).digest()
            return [float(b) / 255.0 for b in hash_bytes[:128]]

        embedding = self._embedding_model.encode(text)
        return embedding.tolist()

    async def record_interaction(self, interaction: UserInteraction) -> bool:
        """
        Kullanıcı etkileşimini kaydet.

        Args:
            interaction: Etkileşim bilgisi

        Returns:
            Başarı durumu
        """
        try:
            self._interactions.append(interaction)

            # User profile güncelle
            await self._update_user_profile(interaction.user_id)

            # CTR tracking güncelle (REQ-4.6)
            self._update_ctr_tracking(interaction)

            logger.debug(
                f"Interaction recorded: {interaction.user_id} - "
                f"{interaction.interaction_type.value} - {interaction.content_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to record interaction: {e}", exc_info=True)
            return False

    def _update_ctr_tracking(self, interaction: UserInteraction) -> None:
        """CTR tracking güncelle (REQ-4.6)."""
        content_id = interaction.content_id

        if content_id not in self._click_tracking:
            self._click_tracking[content_id] = {"clicks": 0, "impressions": 0}

        if interaction.interaction_type == InteractionType.VIEW:
            self._click_tracking[content_id]["impressions"] += 1
        elif interaction.interaction_type in [
            InteractionType.LIKE,
            InteractionType.COMPLETE,
        ]:
            self._click_tracking[content_id]["clicks"] += 1

    async def _update_user_profile(self, user_id: str) -> UserProfile:
        """
        Kullanıcı profil embedding'ini güncelle.

        Spec REQ-4.1, REQ-4.2: User profile embedding ve interaction aggregation.

        Args:
            user_id: Kullanıcı ID'si

        Returns:
            Güncellenmiş UserProfile
        """
        if not await self.initialize():
            return UserProfile(
                user_id=user_id,
                embedding=[0.0] * 768,
                interaction_count=0,
                last_updated=datetime.now(),
                is_cold_start=True,
            )

        # Kullanıcının etkileşimlerini al
        user_interactions = [i for i in self._interactions if i.user_id == user_id]

        interaction_count = len(user_interactions)
        is_cold_start = interaction_count < self.COLD_START_THRESHOLD

        if interaction_count == 0:
            profile = UserProfile(
                user_id=user_id,
                embedding=[0.0] * EmbeddingConfig.get_model_dimension(),
                interaction_count=0,
                last_updated=datetime.now(),
                is_cold_start=True,
            )
            self._user_profiles[user_id] = profile
            return profile

        # İçerik embedding'lerini weighted average ile aggregate et (REQ-4.2)
        weighted_embeddings = []
        weights = []
        subjects = []

        for interaction in user_interactions:
            try:
                # İçerik embedding'ini al
                content = self._collection.get(
                    ids=[interaction.content_id], include=["embeddings", "metadatas"]
                )

                if content and content.get("embeddings"):
                    embedding = content["embeddings"][0]
                    weight = INTERACTION_WEIGHTS.get(interaction.interaction_type, 0.5)

                    # Recency bonus: son 7 gündeki etkileşimler daha önemli
                    days_ago = (datetime.now() - interaction.timestamp).days
                    recency_bonus = max(0.5, 1.0 - (days_ago / 30))
                    weight *= recency_bonus

                    weighted_embeddings.append(embedding)
                    weights.append(weight)

                    # Subject tracking
                    if content.get("metadatas"):
                        subject = content["metadatas"][0].get("subject")
                        if subject:
                            subjects.append(subject)

            except Exception as e:
                logger.warning(f"Could not get content {interaction.content_id}: {e}")

        # Weighted average embedding
        if weighted_embeddings and NUMPY_AVAILABLE:
            embeddings_array = np.array(weighted_embeddings)
            weights_array = np.array(weights)
            weights_array = weights_array / weights_array.sum()  # Normalize

            profile_embedding = np.average(
                embeddings_array, axis=0, weights=weights_array
            )
            profile_embedding = profile_embedding.tolist()
        elif weighted_embeddings:
            # Fallback: simple average
            dim = len(weighted_embeddings[0])
            profile_embedding = [
                sum(emb[i] for emb in weighted_embeddings) / len(weighted_embeddings)
                for i in range(dim)
            ]
        else:
            profile_embedding = [0.0] * EmbeddingConfig.get_model_dimension()

        # Preferred subjects
        from collections import Counter

        subject_counts = Counter(subjects)
        preferred_subjects = [s for s, _ in subject_counts.most_common(5)]

        profile = UserProfile(
            user_id=user_id,
            embedding=profile_embedding,
            interaction_count=interaction_count,
            last_updated=datetime.now(),
            preferred_subjects=preferred_subjects,
            is_cold_start=is_cold_start,
        )

        self._user_profiles[user_id] = profile
        return profile

    async def get_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        subject_filter: str | None = None,
        ensure_diversity: bool = True,
    ) -> RecommendationResponse:
        """
        Kullanıcı için içerik önerileri getir.

        Spec REQ-4.3, REQ-4.4, REQ-4.5

        Args:
            user_id: Kullanıcı ID'si
            limit: Maksimum öneri sayısı
            subject_filter: Opsiyonel konu filtresi
            ensure_diversity: Çeşitlilik sağla (REQ-4.5)

        Returns:
            RecommendationResponse
        """
        if not await self.initialize():
            return RecommendationResponse(
                user_id=user_id,
                recommendations=[],
                is_cold_start=True,
                strategy_used="error",
                diversity_score=0.0,
            )

        # User profile al veya oluştur
        profile = await self._update_user_profile(user_id)

        # Cold start kontrolü (REQ-4.4)
        if profile.is_cold_start:
            return await self._get_cold_start_recommendations(
                user_id, limit, subject_filter
            )

        # Hybrid recommendations (REQ-4.3)
        recommendations = await self._get_hybrid_recommendations(
            profile,
            limit * 2,
            subject_filter,  # Diversity için fazla al
        )

        # Diversity sağla (REQ-4.5)
        if ensure_diversity:
            recommendations = self._ensure_diversity(recommendations, limit)
        else:
            recommendations = recommendations[:limit]

        # Diversity score hesapla
        diversity_score = self._calculate_diversity_score(recommendations)

        return RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations,
            is_cold_start=False,
            strategy_used="hybrid",
            diversity_score=diversity_score,
        )

    async def _get_cold_start_recommendations(
        self, user_id: str, limit: int, subject_filter: str | None
    ) -> RecommendationResponse:
        """
        Cold start kullanıcılar için popularity-based öneriler.

        Spec REQ-4.4: Cold-start fallback

        Args:
            user_id: Kullanıcı ID'si
            limit: Maksimum öneri sayısı
            subject_filter: Opsiyonel konu filtresi

        Returns:
            RecommendationResponse
        """
        try:
            # En popüler içerikleri al
            where_clause = {"subject": subject_filter} if subject_filter else None

            results = self._collection.get(
                where=where_clause, include=["documents", "metadatas"], limit=limit * 3
            )

            if not results or not results.get("ids"):
                return RecommendationResponse(
                    user_id=user_id,
                    recommendations=[],
                    is_cold_start=True,
                    strategy_used="cold_start_empty",
                    diversity_score=0.0,
                )

            # Popularity'ye göre sırala
            recommendations = []
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                doc = results["documents"][i] if results.get("documents") else ""

                # Popularity score: view_count + like_count * 2
                view_count = metadata.get("view_count", 0)
                like_count = metadata.get("like_count", 0)
                popularity = view_count + like_count * 2

                recommendations.append(
                    RecommendationResult(
                        content_id=doc_id,
                        content_preview=doc[:150] + "..." if len(doc) > 150 else doc,
                        score=popularity,
                        metadata=metadata,
                        recommendation_type="popularity",
                    )
                )

            # Popularity'ye göre sırala ve limit uygula
            recommendations.sort(key=lambda x: x.score, reverse=True)
            recommendations = recommendations[:limit]

            # Diversity sağla
            recommendations = self._ensure_diversity(recommendations, limit)

            return RecommendationResponse(
                user_id=user_id,
                recommendations=recommendations,
                is_cold_start=True,
                strategy_used="cold_start_popularity",
                diversity_score=self._calculate_diversity_score(recommendations),
            )

        except Exception as e:
            logger.error(f"Cold start recommendations failed: {e}", exc_info=True)
            return RecommendationResponse(
                user_id=user_id,
                recommendations=[],
                is_cold_start=True,
                strategy_used="error",
                diversity_score=0.0,
            )

    async def _get_hybrid_recommendations(
        self, profile: UserProfile, limit: int, subject_filter: str | None
    ) -> list[RecommendationResult]:
        """
        Hybrid filtering ile öneriler.

        Spec REQ-4.3: Collaborative + Content-based hybrid

        Args:
            profile: Kullanıcı profili
            limit: Maksimum öneri sayısı
            subject_filter: Opsiyonel konu filtresi

        Returns:
            Öneri listesi
        """
        try:
            # Content-based: profile embedding ile benzer içerikler
            where_clause = {"subject": subject_filter} if subject_filter else None

            results = self._collection.query(
                query_embeddings=[profile.embedding],
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            recommendations = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    # Zaten etkileşimde bulunulan içerikleri atla
                    user_content_ids = {
                        inter.content_id
                        for inter in self._interactions
                        if inter.user_id == profile.user_id
                    }
                    if doc_id in user_content_ids:
                        continue

                    metadata = (
                        results["metadatas"][0][i] if results.get("metadatas") else {}
                    )
                    doc = results["documents"][0][i] if results.get("documents") else ""
                    distance = (
                        results["distances"][0][i] if results.get("distances") else 1.0
                    )

                    # Content-based score
                    content_score = 1 - distance

                    # Collaborative score (simplified: similar users)
                    collab_score = self._get_collaborative_score(
                        doc_id, profile.user_id
                    )

                    # Popularity score
                    popularity_score = self._get_popularity_score(doc_id)

                    # Hybrid score
                    hybrid_score = (
                        self.CONTENT_WEIGHT * content_score
                        + self.COLLABORATIVE_WEIGHT * collab_score
                        + self.POPULARITY_WEIGHT * popularity_score
                    )

                    recommendations.append(
                        RecommendationResult(
                            content_id=doc_id,
                            content_preview=doc[:150] + "..."
                            if len(doc) > 150
                            else doc,
                            score=round(hybrid_score, 4),
                            metadata=metadata,
                            recommendation_type="hybrid",
                        )
                    )

            # Score'a göre sırala
            recommendations.sort(key=lambda x: x.score, reverse=True)
            return recommendations

        except Exception as e:
            logger.error(f"Hybrid recommendations failed: {e}", exc_info=True)
            return []

    def _get_collaborative_score(self, content_id: str, user_id: str) -> float:
        """
        Collaborative filtering score.

        Basitleştirilmiş: benzer etkileşimlerde bulunan kullanıcı sayısı.
        """
        # Bu içerikle etkileşimde bulunan diğer kullanıcılar
        other_users = set()
        for inter in self._interactions:
            if inter.content_id == content_id and inter.user_id != user_id:
                if inter.interaction_type in [
                    InteractionType.LIKE,
                    InteractionType.COMPLETE,
                ]:
                    other_users.add(inter.user_id)

        # Normalize (0-1)
        max_users = 10  # Varsayılan max
        return min(len(other_users) / max_users, 1.0)

    def _get_popularity_score(self, content_id: str) -> float:
        """Popularity score (CTR-based)."""
        tracking = self._click_tracking.get(content_id, {"clicks": 0, "impressions": 1})

        impressions = max(tracking["impressions"], 1)
        clicks = tracking["clicks"]

        ctr = clicks / impressions
        return min(ctr, 1.0)

    def _ensure_diversity(
        self, recommendations: list[RecommendationResult], limit: int
    ) -> list[RecommendationResult]:
        """
        Öneri çeşitliliğini sağla.

        Spec REQ-4.5: Different topics'ten seç.

        Args:
            recommendations: Ham öneri listesi
            limit: Hedef öneri sayısı

        Returns:
            Çeşitlendirilmiş öneri listesi
        """
        if len(recommendations) <= limit:
            return recommendations

        # Konulara göre grupla
        by_subject: dict[str, list[RecommendationResult]] = {}
        for rec in recommendations:
            subject = rec.metadata.get("subject", "other")
            if subject not in by_subject:
                by_subject[subject] = []
            by_subject[subject].append(rec)

        # Round-robin ile farklı konulardan seç
        diverse_recs: list[RecommendationResult] = []
        subjects = list(by_subject.keys())

        # Minimum farklı konu garantisi
        while len(diverse_recs) < limit and subjects:
            for subject in subjects[:]:
                if len(diverse_recs) >= limit:
                    break

                if by_subject[subject]:
                    # En yüksek skorlu olanı al
                    rec = by_subject[subject].pop(0)
                    diverse_recs.append(rec)

                    if not by_subject[subject]:
                        subjects.remove(subject)

        return diverse_recs

    def _calculate_diversity_score(
        self, recommendations: list[RecommendationResult]
    ) -> float:
        """Çeşitlilik skorunu hesapla."""
        if not recommendations:
            return 0.0

        subjects = set()
        for rec in recommendations:
            subject = rec.metadata.get("subject", "other")
            subjects.add(subject)

        # Diversity: unique subjects / total recommendations
        diversity = len(subjects) / len(recommendations)

        # Bonus: minimum topic requirement met
        if len(subjects) >= self.DIVERSITY_MIN_TOPICS:
            diversity = min(diversity * 1.2, 1.0)

        return round(diversity, 4)

    async def get_ctr_report(self) -> dict:
        """
        CTR raporu getir.

        Spec REQ-4.6: Click-through rate tracking.

        Returns:
            CTR istatistikleri
        """
        if not self._click_tracking:
            return {
                "total_content": 0,
                "average_ctr": 0.0,
                "top_performing": [],
                "bottom_performing": [],
            }

        ctr_data = []
        for content_id, data in self._click_tracking.items():
            impressions = max(data["impressions"], 1)
            clicks = data["clicks"]
            ctr = clicks / impressions

            ctr_data.append(
                {
                    "content_id": content_id,
                    "impressions": impressions,
                    "clicks": clicks,
                    "ctr": round(ctr * 100, 2),  # Percentage
                }
            )

        # Sort by CTR
        ctr_data.sort(key=lambda x: x["ctr"], reverse=True)

        avg_ctr = sum(d["ctr"] for d in ctr_data) / len(ctr_data) if ctr_data else 0.0

        return {
            "total_content": len(ctr_data),
            "average_ctr": round(avg_ctr, 2),
            "top_performing": ctr_data[:5],
            "bottom_performing": ctr_data[-5:] if len(ctr_data) > 5 else [],
        }


# Singleton instance
_recommendation_service: ContentRecommendationService | None = None


def get_recommendation_service(
    persist_directory: str = "./vector_db", collection_name: str = "kiro2_content"
) -> ContentRecommendationService:
    """
    Singleton ContentRecommendationService instance döndür.

    Args:
        persist_directory: ChromaDB persist dizini
        collection_name: Collection adı

    Returns:
        ContentRecommendationService instance
    """
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = ContentRecommendationService(
            persist_directory=persist_directory, collection_name=collection_name
        )
    return _recommendation_service
