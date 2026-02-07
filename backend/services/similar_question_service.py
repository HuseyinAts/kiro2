"""
Benzer Soru Önerisi Servisi
Question embedding'leri ve semantik benzerlik ile benzer soru önerisi.

Task 75: Benzer Soru Önerisi
- 75.1: Soru embedding'leri (Question vectorization, Semantic embeddings, Similarity matrix)
- 75.2: Semantik benzerlik (Cosine similarity, Nearest neighbor search, Threshold tuning)
- 75.3: Konu bazlı filtreleme (Topic constraints, Hierarchical filtering, Cross-topic suggestions)
- 75.4: Zorluk bazlı filtreleme (Difficulty range matching, Progressive difficulty, Adaptive suggestions)

Requirements: REQ-13.7
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pickle
from pathlib import Path

try:
    from services.nlp_training.berturk_embedding import (
        BERTurkEmbeddingService,
        EmbeddingResult,
    )
except ImportError:
    from nlp_training.berturk_embedding import BERTurkEmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class QuestionEmbedding:
    """Soru embedding'i"""

    question_id: str
    text: str
    embedding: np.ndarray
    subject: str
    topic: str
    difficulty: float
    exam_type: str
    created_at: datetime


@dataclass
class SimilarQuestionResult:
    """Benzer soru sonucu"""

    question_id: str
    text: str
    similarity_score: float
    subject: str
    topic: str
    difficulty: float
    exam_type: str
    match_reason: str  # Neden benzer olduğunu açıkla


class SimilarQuestionService:
    """
    Benzer Soru Önerisi Servisi

    Task 75 implementasyonu:
    - Soru embedding'leri (BERTurk)
    - Semantik benzerlik (Cosine similarity)
    - Konu bazlı filtreleme
    - Zorluk bazlı filtreleme
    """

    def __init__(
        self,
        berturk_service: Optional[BERTurkEmbeddingService] = None,
        cache_dir: str = "data/question_embeddings",
    ):
        """
        Initialize Similar Question Service

        Args:
            berturk_service: BERTurk embedding servisi
            cache_dir: Embedding cache dizini
        """
        # BERTurk servisi
        if berturk_service is None:
            logger.info("Initializing BERTurk service for question embeddings")
            self.berturk_service = BERTurkEmbeddingService()
        else:
            self.berturk_service = berturk_service

        # Cache dizini
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory embedding cache
        self.question_embeddings: Dict[str, QuestionEmbedding] = {}

        # Similarity matrix cache
        self.similarity_matrix: Optional[np.ndarray] = None
        self.question_id_index: Dict[str, int] = {}

        logger.info(f"SimilarQuestionService initialized with cache dir: {cache_dir}")

    # ========== Task 75.1: Soru Embedding'leri ==========

    def generate_question_embedding(
        self,
        question_id: str,
        text: str,
        subject: str,
        topic: str,
        difficulty: float,
        exam_type: str,
    ) -> QuestionEmbedding:
        """
        Tek bir soru için embedding oluştur

        Task 75.1: Question vectorization

        Args:
            question_id: Soru ID
            text: Soru metni
            subject: Ders (Matematik, Türkçe, vb.)
            topic: Konu
            difficulty: Zorluk seviyesi (0-10)
            exam_type: Sınav türü (TYT, AYT, YDT)

        Returns:
            QuestionEmbedding: Soru embedding'i
        """
        # BERTurk ile embedding oluştur
        emb_result = self.berturk_service.generate_embedding(
            text=text, use_cache=True, pooling_strategy="mean"
        )

        # QuestionEmbedding oluştur
        question_emb = QuestionEmbedding(
            question_id=question_id,
            text=text,
            embedding=emb_result.embedding,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            exam_type=exam_type,
            created_at=datetime.now(),
        )

        # Cache'e ekle
        self.question_embeddings[question_id] = question_emb

        logger.debug(f"Generated embedding for question {question_id}")
        return question_emb

    def generate_batch_embeddings(
        self, questions: List[Dict[str, Any]]
    ) -> List[QuestionEmbedding]:
        """
        Toplu soru embedding'leri oluştur

        Task 75.1: Semantic embeddings (batch processing)

        Args:
            questions: Soru listesi (dict formatında)
                - question_id: str
                - text: str
                - subject: str
                - topic: str
                - difficulty: float
                - exam_type: str

        Returns:
            List[QuestionEmbedding]: Embedding listesi
        """
        logger.info(f"Generating embeddings for {len(questions)} questions")

        # Batch embedding oluştur
        texts = [q["text"] for q in questions]
        emb_results = self.berturk_service.generate_batch_embeddings(
            texts=texts, batch_size=32, pooling_strategy="mean"
        )

        # QuestionEmbedding'lere çevir
        question_embeddings = []
        for question, emb_result in zip(questions, emb_results):
            question_emb = QuestionEmbedding(
                question_id=question["question_id"],
                text=question["text"],
                embedding=emb_result.embedding,
                subject=question["subject"],
                topic=question["topic"],
                difficulty=question["difficulty"],
                exam_type=question["exam_type"],
                created_at=datetime.now(),
            )

            # Cache'e ekle
            self.question_embeddings[question["question_id"]] = question_emb
            question_embeddings.append(question_emb)

        logger.info(f"Generated {len(question_embeddings)} question embeddings")
        return question_embeddings

    def build_similarity_matrix(self) -> np.ndarray:
        """
        Tüm sorular için similarity matrix oluştur

        Task 75.1: Similarity matrix

        Returns:
            np.ndarray: Similarity matrix (N x N)
        """
        if len(self.question_embeddings) == 0:
            logger.warning("No question embeddings available")
            return np.array([])

        logger.info(
            f"Building similarity matrix for {len(self.question_embeddings)} questions"
        )

        # Embedding matrix oluştur
        question_ids = list(self.question_embeddings.keys())
        embeddings = np.array(
            [self.question_embeddings[qid].embedding for qid in question_ids]
        )

        # Cosine similarity matrix hesapla
        from sklearn.metrics.pairwise import cosine_similarity

        similarity_matrix = cosine_similarity(embeddings)

        # Index mapping oluştur
        self.question_id_index = {qid: idx for idx, qid in enumerate(question_ids)}
        self.similarity_matrix = similarity_matrix

        logger.info(f"Similarity matrix built: {similarity_matrix.shape}")
        return similarity_matrix

    # ========== Task 75.2: Semantik Benzerlik ==========

    def calculate_similarity(self, question_id_1: str, question_id_2: str) -> float:
        """
        İki soru arasında cosine similarity hesapla

        Task 75.2: Cosine similarity calculation

        Args:
            question_id_1: İlk soru ID
            question_id_2: İkinci soru ID

        Returns:
            float: Similarity score (0-1 arası)
        """
        # Embeddings al
        if question_id_1 not in self.question_embeddings:
            raise ValueError(f"Question {question_id_1} not found in embeddings")
        if question_id_2 not in self.question_embeddings:
            raise ValueError(f"Question {question_id_2} not found in embeddings")

        emb1 = self.question_embeddings[question_id_1].embedding
        emb2 = self.question_embeddings[question_id_2].embedding

        # Cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity

        similarity = cosine_similarity(emb1.reshape(1, -1), emb2.reshape(1, -1))[0][0]

        return float(np.clip(similarity, 0.0, 1.0))

    def find_nearest_neighbors(
        self, question_id: str, k: int = 10, similarity_threshold: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Nearest neighbor search ile en benzer soruları bul

        Task 75.2: Nearest neighbor search

        Args:
            question_id: Query soru ID
            k: En yakın k soru
            similarity_threshold: Minimum benzerlik eşiği

        Returns:
            List[Tuple[str, float]]: (question_id, similarity) listesi
        """
        if question_id not in self.question_embeddings:
            raise ValueError(f"Question {question_id} not found in embeddings")

        # Similarity matrix kullan (varsa)
        if self.similarity_matrix is not None and question_id in self.question_id_index:
            query_idx = self.question_id_index[question_id]
            similarities = self.similarity_matrix[query_idx]

            # Sırala (kendisi hariç)
            sorted_indices = np.argsort(similarities)[::-1]

            results = []
            for idx in sorted_indices:
                if idx == query_idx:
                    continue  # Kendisini atla

                sim_score = similarities[idx]
                if sim_score < similarity_threshold:
                    break

                # Question ID bul
                candidate_id = list(self.question_id_index.keys())[
                    list(self.question_id_index.values()).index(idx)
                ]
                results.append((candidate_id, float(sim_score)))

                if len(results) >= k:
                    break

            return results

        # Fallback: Manuel hesaplama
        else:
            query_emb = self.question_embeddings[question_id].embedding

            similarities = []
            for candidate_id, candidate_emb_obj in self.question_embeddings.items():
                if candidate_id == question_id:
                    continue

                # Cosine similarity
                from sklearn.metrics.pairwise import cosine_similarity

                sim_score = cosine_similarity(
                    query_emb.reshape(1, -1), candidate_emb_obj.embedding.reshape(1, -1)
                )[0][0]

                if sim_score >= similarity_threshold:
                    similarities.append((candidate_id, float(sim_score)))

            # Sırala ve top-k al
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:k]

    def tune_similarity_threshold(
        self,
        validation_pairs: List[Tuple[str, str, bool]],
        threshold_range: Tuple[float, float] = (0.3, 0.9),
        step: float = 0.05,
    ) -> float:
        """
        Similarity threshold'u optimize et

        Task 75.2: Similarity threshold tuning

        Args:
            validation_pairs: (question_id_1, question_id_2, is_similar) listesi
            threshold_range: Threshold aralığı
            step: Adım boyutu

        Returns:
            float: Optimal threshold
        """
        logger.info(
            f"Tuning similarity threshold with {len(validation_pairs)} validation pairs"
        )

        best_threshold = 0.5
        best_f1_score = 0.0

        # Threshold'ları dene
        thresholds = np.arange(threshold_range[0], threshold_range[1], step)

        for threshold in thresholds:
            true_positives = 0
            false_positives = 0
            false_negatives = 0

            for q1, q2, is_similar in validation_pairs:
                try:
                    similarity = self.calculate_similarity(q1, q2)
                    predicted_similar = similarity >= threshold

                    if predicted_similar and is_similar:
                        true_positives += 1
                    elif predicted_similar and not is_similar:
                        false_positives += 1
                    elif not predicted_similar and is_similar:
                        false_negatives += 1

                except ValueError:
                    continue

            # F1 score hesapla
            if true_positives + false_positives > 0:
                precision = true_positives / (true_positives + false_positives)
            else:
                precision = 0.0

            if true_positives + false_negatives > 0:
                recall = true_positives / (true_positives + false_negatives)
            else:
                recall = 0.0

            if precision + recall > 0:
                f1_score = 2 * (precision * recall) / (precision + recall)
            else:
                f1_score = 0.0

            if f1_score > best_f1_score:
                best_f1_score = f1_score
                best_threshold = threshold

        logger.info(
            f"Optimal threshold: {best_threshold:.3f} (F1: {best_f1_score:.3f})"
        )
        return best_threshold

    # ========== Task 75.3: Konu Bazlı Filtreleme ==========

    def filter_by_topic(
        self,
        candidates: List[Tuple[str, float]],
        target_topic: str,
        allow_cross_topic: bool = False,
        topic_hierarchy: Optional[Dict[str, List[str]]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Konu bazlı filtreleme uygula

        Task 75.3: Topic constraint application

        Args:
            candidates: (question_id, similarity) listesi
            target_topic: Hedef konu
            allow_cross_topic: Çapraz konu önerilerine izin ver
            topic_hierarchy: Konu hiyerarşisi (parent -> children)

        Returns:
            List[Tuple[str, float]]: Filtrelenmiş liste
        """
        filtered = []

        for question_id, similarity in candidates:
            if question_id not in self.question_embeddings:
                continue

            candidate_topic = self.question_embeddings[question_id].topic

            # Aynı konu
            if candidate_topic == target_topic:
                filtered.append((question_id, similarity))

            # Çapraz konu izinli ve hiyerarşi varsa
            elif allow_cross_topic and topic_hierarchy:
                # Hierarchical filtering (Task 75.3)
                if self._is_related_topic(
                    target_topic, candidate_topic, topic_hierarchy
                ):
                    # Çapraz konu için similarity'yi biraz düşür
                    adjusted_similarity = similarity * 0.9
                    filtered.append((question_id, adjusted_similarity))

        return filtered

    def _is_related_topic(
        self, topic1: str, topic2: str, topic_hierarchy: Dict[str, List[str]]
    ) -> bool:
        """
        İki konunun ilişkili olup olmadığını kontrol et

        Task 75.3: Hierarchical filtering

        Args:
            topic1: İlk konu
            topic2: İkinci konu
            topic_hierarchy: Konu hiyerarşisi

        Returns:
            bool: İlişkili mi?
        """
        # Aynı parent'a sahipler mi?
        for parent, children in topic_hierarchy.items():
            if topic1 in children and topic2 in children:
                return True

        # Biri diğerinin parent'ı mı?
        if topic1 in topic_hierarchy and topic2 in topic_hierarchy[topic1]:
            return True
        if topic2 in topic_hierarchy and topic1 in topic_hierarchy[topic2]:
            return True

        return False

    def get_cross_topic_suggestions(
        self, question_id: str, k: int = 5, similarity_threshold: float = 0.6
    ) -> List[SimilarQuestionResult]:
        """
        Çapraz konu önerileri getir

        Task 75.3: Cross-topic suggestions

        Args:
            question_id: Query soru ID
            k: Öneri sayısı
            similarity_threshold: Minimum benzerlik

        Returns:
            List[SimilarQuestionResult]: Çapraz konu önerileri
        """
        if question_id not in self.question_embeddings:
            raise ValueError(f"Question {question_id} not found")

        query_topic = self.question_embeddings[question_id].topic

        # Nearest neighbors bul
        neighbors = self.find_nearest_neighbors(
            question_id=question_id,
            k=k * 3,  # Daha fazla al, sonra filtrele
            similarity_threshold=similarity_threshold,
        )

        # Farklı konulardan olanları filtrele
        cross_topic_results = []
        for candidate_id, similarity in neighbors:
            candidate = self.question_embeddings[candidate_id]

            if candidate.topic != query_topic:
                result = SimilarQuestionResult(
                    question_id=candidate_id,
                    text=candidate.text,
                    similarity_score=similarity,
                    subject=candidate.subject,
                    topic=candidate.topic,
                    difficulty=candidate.difficulty,
                    exam_type=candidate.exam_type,
                    match_reason=f"Farklı konu ({candidate.topic}) ama semantik olarak benzer",
                )
                cross_topic_results.append(result)

                if len(cross_topic_results) >= k:
                    break

        return cross_topic_results

    # ========== Task 75.4: Zorluk Bazlı Filtreleme ==========

    def filter_by_difficulty(
        self,
        candidates: List[Tuple[str, float]],
        target_difficulty: float,
        difficulty_range: float = 1.0,
        progressive: bool = False,
    ) -> List[Tuple[str, float]]:
        """
        Zorluk bazlı filtreleme uygula

        Task 75.4: Difficulty range matching

        Args:
            candidates: (question_id, similarity) listesi
            target_difficulty: Hedef zorluk seviyesi (0-10)
            difficulty_range: Zorluk aralığı (±)
            progressive: Progressive difficulty (giderek zorlaşan)

        Returns:
            List[Tuple[str, float]]: Filtrelenmiş liste
        """
        filtered = []

        for question_id, similarity in candidates:
            if question_id not in self.question_embeddings:
                continue

            candidate_difficulty = self.question_embeddings[question_id].difficulty

            # Difficulty range matching
            if progressive:
                # Progressive difficulty: Hedeften biraz daha zor sorular öner
                if (
                    target_difficulty
                    <= candidate_difficulty
                    <= target_difficulty + difficulty_range * 1.5
                ):
                    filtered.append((question_id, similarity))
            else:
                # Normal range matching
                if abs(candidate_difficulty - target_difficulty) <= difficulty_range:
                    filtered.append((question_id, similarity))

        return filtered

    def get_progressive_difficulty_suggestions(
        self, question_id: str, k: int = 5, difficulty_increment: float = 0.5
    ) -> List[SimilarQuestionResult]:
        """
        Giderek zorlaşan soru önerileri

        Task 75.4: Progressive difficulty

        Args:
            question_id: Query soru ID
            k: Öneri sayısı
            difficulty_increment: Zorluk artış miktarı

        Returns:
            List[SimilarQuestionResult]: Progressive difficulty önerileri
        """
        if question_id not in self.question_embeddings:
            raise ValueError(f"Question {question_id} not found")

        query_question = self.question_embeddings[question_id]
        target_difficulty = query_question.difficulty + difficulty_increment

        # Nearest neighbors bul
        neighbors = self.find_nearest_neighbors(
            question_id=question_id, k=k * 2, similarity_threshold=0.5
        )

        # Zorluk filtrele (daha zor olanlar)
        filtered = self.filter_by_difficulty(
            candidates=neighbors,
            target_difficulty=target_difficulty,
            difficulty_range=1.0,
            progressive=True,
        )

        # SimilarQuestionResult'a çevir
        results = []
        for candidate_id, similarity in filtered[:k]:
            candidate = self.question_embeddings[candidate_id]

            result = SimilarQuestionResult(
                question_id=candidate_id,
                text=candidate.text,
                similarity_score=similarity,
                subject=candidate.subject,
                topic=candidate.topic,
                difficulty=candidate.difficulty,
                exam_type=candidate.exam_type,
                match_reason=f"Benzer ama daha zor (zorluk: {candidate.difficulty:.1f})",
            )
            results.append(result)

        return results

    def get_adaptive_suggestions(
        self, question_id: str, student_performance: float, k: int = 5
    ) -> List[SimilarQuestionResult]:
        """
        Öğrenci performansına göre adaptif öneriler

        Task 75.4: Adaptive suggestions

        Args:
            question_id: Query soru ID
            student_performance: Öğrenci başarı oranı (0-1)
            k: Öneri sayısı

        Returns:
            List[SimilarQuestionResult]: Adaptif öneriler
        """
        if question_id not in self.question_embeddings:
            raise ValueError(f"Question {question_id} not found")

        query_question = self.question_embeddings[question_id]

        # Performansa göre zorluk ayarla
        if student_performance >= 0.8:
            # Yüksek performans: Daha zor sorular
            target_difficulty = min(query_question.difficulty + 1.0, 10.0)
            difficulty_range = 1.5
        elif student_performance >= 0.6:
            # Orta performans: Benzer zorluk
            target_difficulty = query_question.difficulty
            difficulty_range = 1.0
        else:
            # Düşük performans: Daha kolay sorular
            target_difficulty = max(query_question.difficulty - 1.0, 0.0)
            difficulty_range = 1.0

        # Nearest neighbors bul
        neighbors = self.find_nearest_neighbors(
            question_id=question_id, k=k * 2, similarity_threshold=0.5
        )

        # Zorluk filtrele
        filtered = self.filter_by_difficulty(
            candidates=neighbors,
            target_difficulty=target_difficulty,
            difficulty_range=difficulty_range,
            progressive=False,
        )

        # SimilarQuestionResult'a çevir
        results = []
        for candidate_id, similarity in filtered[:k]:
            candidate = self.question_embeddings[candidate_id]

            # Match reason oluştur
            if student_performance >= 0.8:
                reason = f"Yüksek performans - daha zor soru (zorluk: {candidate.difficulty:.1f})"
            elif student_performance >= 0.6:
                reason = f"Orta performans - benzer zorluk (zorluk: {candidate.difficulty:.1f})"
            else:
                reason = f"Düşük performans - daha kolay soru (zorluk: {candidate.difficulty:.1f})"

            result = SimilarQuestionResult(
                question_id=candidate_id,
                text=candidate.text,
                similarity_score=similarity,
                subject=candidate.subject,
                topic=candidate.topic,
                difficulty=candidate.difficulty,
                exam_type=candidate.exam_type,
                match_reason=reason,
            )
            results.append(result)

        return results

    # ========== Ana Öneri Fonksiyonu ==========

    def get_similar_questions(
        self,
        question_id: str,
        k: int = 10,
        similarity_threshold: float = 0.6,
        same_topic_only: bool = True,
        difficulty_range: Optional[float] = None,
        student_performance: Optional[float] = None,
    ) -> List[SimilarQuestionResult]:
        """
        Benzer soru önerileri getir (tüm filtreler ile)

        Combines all tasks: 75.1, 75.2, 75.3, 75.4

        Args:
            question_id: Query soru ID
            k: Öneri sayısı
            similarity_threshold: Minimum benzerlik eşiği
            same_topic_only: Sadece aynı konudan öner
            difficulty_range: Zorluk aralığı (None = filtreleme yok)
            student_performance: Öğrenci performansı (0-1, None = adaptif yok)

        Returns:
            List[SimilarQuestionResult]: Benzer soru önerileri
        """
        if question_id not in self.question_embeddings:
            raise ValueError(f"Question {question_id} not found in embeddings")

        query_question = self.question_embeddings[question_id]

        # 1. Nearest neighbor search (Task 75.2)
        neighbors = self.find_nearest_neighbors(
            question_id=question_id,
            k=k * 3,  # Daha fazla al, sonra filtrele
            similarity_threshold=similarity_threshold,
        )

        # 2. Konu filtresi (Task 75.3)
        if same_topic_only:
            neighbors = self.filter_by_topic(
                candidates=neighbors,
                target_topic=query_question.topic,
                allow_cross_topic=False,
            )

        # 3. Zorluk filtresi (Task 75.4)
        if difficulty_range is not None:
            neighbors = self.filter_by_difficulty(
                candidates=neighbors,
                target_difficulty=query_question.difficulty,
                difficulty_range=difficulty_range,
                progressive=False,
            )

        # 4. Adaptif filtreleme (Task 75.4)
        if student_performance is not None:
            # Performansa göre zorluk ayarla
            if student_performance >= 0.8:
                target_difficulty = min(query_question.difficulty + 1.0, 10.0)
            elif student_performance >= 0.6:
                target_difficulty = query_question.difficulty
            else:
                target_difficulty = max(query_question.difficulty - 1.0, 0.0)

            neighbors = self.filter_by_difficulty(
                candidates=neighbors,
                target_difficulty=target_difficulty,
                difficulty_range=1.5,
                progressive=False,
            )

        # 5. SimilarQuestionResult'a çevir
        results = []
        for candidate_id, similarity in neighbors[:k]:
            candidate = self.question_embeddings[candidate_id]

            # Match reason oluştur
            reasons = []
            reasons.append(f"Semantik benzerlik: {similarity:.2f}")

            if same_topic_only:
                reasons.append(f"Aynı konu: {candidate.topic}")

            if difficulty_range is not None:
                diff_delta = abs(candidate.difficulty - query_question.difficulty)
                reasons.append(f"Benzer zorluk (Δ{diff_delta:.1f})")

            if student_performance is not None:
                if student_performance >= 0.8:
                    reasons.append("Yüksek performans - zorlaştırıldı")
                elif student_performance < 0.6:
                    reasons.append("Düşük performans - kolaylaştırıldı")

            result = SimilarQuestionResult(
                question_id=candidate_id,
                text=candidate.text,
                similarity_score=similarity,
                subject=candidate.subject,
                topic=candidate.topic,
                difficulty=candidate.difficulty,
                exam_type=candidate.exam_type,
                match_reason=" | ".join(reasons),
            )
            results.append(result)

        logger.info(f"Found {len(results)} similar questions for {question_id}")
        return results

    # ========== Cache Yönetimi ==========

    def save_embeddings_to_disk(
        self, filename: str = "question_embeddings.pkl"
    ) -> None:
        """
        Embedding'leri diske kaydet

        Args:
            filename: Dosya adı
        """
        filepath = self.cache_dir / filename

        data = {
            "question_embeddings": self.question_embeddings,
            "similarity_matrix": self.similarity_matrix,
            "question_id_index": self.question_id_index,
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Saved {len(self.question_embeddings)} embeddings to {filepath}")

    def load_embeddings_from_disk(
        self, filename: str = "question_embeddings.pkl"
    ) -> bool:
        """
        Embedding'leri diskten yükle

        Args:
            filename: Dosya adı

        Returns:
            bool: Başarılı mı?
        """
        filepath = self.cache_dir / filename

        if not filepath.exists():
            logger.warning(f"Embedding file not found: {filepath}")
            return False

        try:
            with open(filepath, "rb") as f:
                data = pickle.load(f)

            self.question_embeddings = data["question_embeddings"]
            self.similarity_matrix = data.get("similarity_matrix")
            self.question_id_index = data.get("question_id_index", {})

            logger.info(
                f"Loaded {len(self.question_embeddings)} embeddings from {filepath}"
            )
            return True

        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Servis istatistiklerini getir

        Returns:
            Dict[str, Any]: İstatistikler
        """
        stats = {
            "total_embeddings": len(self.question_embeddings),
            "has_similarity_matrix": self.similarity_matrix is not None,
            "cache_dir": str(self.cache_dir),
            "berturk_cache_size": self.berturk_service.get_cache_size(),
        }

        if self.similarity_matrix is not None:
            stats["similarity_matrix_shape"] = self.similarity_matrix.shape

        # Konu dağılımı
        topics = {}
        for emb in self.question_embeddings.values():
            topics[emb.topic] = topics.get(emb.topic, 0) + 1
        stats["topics"] = topics

        # Zorluk dağılımı
        difficulties = [emb.difficulty for emb in self.question_embeddings.values()]
        if difficulties:
            stats["difficulty_stats"] = {
                "min": float(np.min(difficulties)),
                "max": float(np.max(difficulties)),
                "mean": float(np.mean(difficulties)),
                "std": float(np.std(difficulties)),
            }

        return stats


# Global service instance
_similar_question_service: Optional[SimilarQuestionService] = None


def get_similar_question_service() -> SimilarQuestionService:
    """
    Global SimilarQuestionService instance'ı getir

    Returns:
        SimilarQuestionService: Service instance
    """
    global _similar_question_service

    if _similar_question_service is None:
        _similar_question_service = SimilarQuestionService()

    return _similar_question_service
