"""
BERTurk Embedding Service
Türkçe pre-trained BERT modeli ile sentence embedding ve semantic similarity.

Requirements: REQ-48.21-48.24
"""

import logging
from dataclasses import dataclass

import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Embedding sonucu"""

    text: str
    embedding: np.ndarray
    dimension: int
    model_name: str


class BERTurkEmbeddingService:
    """
    BERTurk Embedding Service

    Türkçe pre-trained BERT modeli kullanarak sentence embedding ve
    semantic similarity hesaplama servisi.

    Requirements:
    - REQ-48.21: BERTurk model loading
    - REQ-48.22: Sentence embedding generation (768 boyutlu)
    - REQ-48.23: Semantic similarity calculation (cosine similarity)
    - REQ-48.24: Similarity score (0-1 arası)
    """

    def __init__(
        self,
        model_name: str = "dbmdz/bert-base-turkish-cased",
        device: str | None = None,
        cache_dir: str | None = None,
    ):
        """
        Initialize BERTurk Embedding Service

        REQ-48.21: BERTurk model loading

        Args:
            model_name: Hugging Face model adı
            device: Device ('cuda', 'cpu', veya None - otomatik)
            cache_dir: Model cache dizini
        """
        self.model_name = model_name

        # Device seç
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Loading BERTurk model: {model_name} on {self.device}")

        # Tokenizer ve model yükle
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)

        self.model = AutoModel.from_pretrained(model_name, cache_dir=cache_dir)

        self.model.to(self.device)
        self.model.eval()  # Evaluation mode

        # Embedding cache - LRU Cache to prevent OOM
        from collections import OrderedDict

        self.embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self.max_cache_size = 10000

        logger.info(f"BERTurk model loaded successfully: {model_name}")

    def generate_embedding(
        self, text: str, use_cache: bool = True, pooling_strategy: str = "mean"
    ) -> EmbeddingResult:
        """
        Sentence embedding oluştur

        REQ-48.22: Sentence embedding generation (768 boyutlu vektör)

        Args:
            text: Input text
            use_cache: Cache kullan
            pooling_strategy: Pooling stratejisi ('mean', 'cls', 'max')

        Returns:
            EmbeddingResult: Embedding sonucu
        """
        # Cache kontrolü
        cache_key = f"{text}_{pooling_strategy}"
        if use_cache and cache_key in self.embedding_cache:
            embedding = self.embedding_cache.pop(cache_key)
            self.embedding_cache[cache_key] = embedding  # Move to end (LRU)
            return EmbeddingResult(
                text=text,
                embedding=embedding,
                dimension=len(embedding),
                model_name=self.model_name,
            )

        # Tokenize
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=512
        )

        # Device'a taşı
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Forward pass
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Pooling stratejisi uygula
        if pooling_strategy == "mean":
            # Mean pooling
            attention_mask = inputs["attention_mask"]
            token_embeddings = outputs.last_hidden_state

            # Mask uygula
            input_mask_expanded = (
                attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            )
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embedding = (sum_embeddings / sum_mask).squeeze()

        elif pooling_strategy == "cls":
            # CLS token embedding
            embedding = outputs.last_hidden_state[:, 0, :].squeeze()

        elif pooling_strategy == "max":
            # Max pooling
            token_embeddings = outputs.last_hidden_state
            embedding = torch.max(token_embeddings, dim=1)[0].squeeze()

        else:
            raise ValueError(f"Unknown pooling strategy: {pooling_strategy}")

        # NumPy array'e çevir
        embedding_np = embedding.cpu().numpy()

        # Cache'e ekle
        if use_cache:
            if len(self.embedding_cache) >= self.max_cache_size:
                self.embedding_cache.popitem(last=False)
            self.embedding_cache[cache_key] = embedding_np

        result = EmbeddingResult(
            text=text,
            embedding=embedding_np,
            dimension=len(embedding_np),
            model_name=self.model_name,
        )

        # Dimension kontrolü (768 olmalı)
        assert (
            result.dimension == 768
        ), f"Expected 768 dimensions, got {result.dimension}"

        return result

    def generate_batch_embeddings(
        self, texts: list[str], batch_size: int = 32, pooling_strategy: str = "mean"
    ) -> list[EmbeddingResult]:
        """
        Batch embedding oluştur

        Args:
            texts: Text listesi
            batch_size: Batch boyutu
            pooling_strategy: Pooling stratejisi

        Returns:
            List[EmbeddingResult]: Embedding sonuçları
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            # Tokenize
            inputs = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )

            # Device'a taşı
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Pooling
            if pooling_strategy == "mean":
                attention_mask = inputs["attention_mask"]
                token_embeddings = outputs.last_hidden_state

                input_mask_expanded = (
                    attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                )
                sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                embeddings = sum_embeddings / sum_mask

            elif pooling_strategy == "cls":
                embeddings = outputs.last_hidden_state[:, 0, :]

            elif pooling_strategy == "max":
                embeddings = torch.max(outputs.last_hidden_state, dim=1)[0]

            # NumPy'ye çevir
            embeddings_np = embeddings.cpu().numpy()

            # Results oluştur
            for text, embedding in zip(batch_texts, embeddings_np, strict=False):
                results.append(
                    EmbeddingResult(
                        text=text,
                        embedding=embedding,
                        dimension=len(embedding),
                        model_name=self.model_name,
                    )
                )

        logger.info(f"Generated {len(results)} embeddings")
        return results

    def calculate_similarity(
        self, text1: str, text2: str, use_cache: bool = True
    ) -> float:
        """
        İki text arasında semantic similarity hesapla

        REQ-48.23: Semantic similarity calculation (cosine similarity)
        REQ-48.24: Similarity score (0-1 arası)

        Args:
            text1: İlk text
            text2: İkinci text
            use_cache: Cache kullan

        Returns:
            float: Similarity score (0-1 arası)
        """
        # Embeddings oluştur
        emb1 = self.generate_embedding(text1, use_cache=use_cache)
        emb2 = self.generate_embedding(text2, use_cache=use_cache)

        # Cosine similarity hesapla
        similarity = cosine_similarity(
            emb1.embedding.reshape(1, -1), emb2.embedding.reshape(1, -1)
        )[0][0]

        # 0-1 aralığında olduğundan emin ol
        similarity = float(np.clip(similarity, 0.0, 1.0))

        return similarity

    def calculate_batch_similarities(
        self, query_text: str, candidate_texts: list[str], top_k: int | None = None
    ) -> list[tuple[str, float]]:
        """
        Bir query text ile birden fazla candidate text arasında similarity hesapla

        Args:
            query_text: Query text
            candidate_texts: Candidate text listesi
            top_k: En yüksek k sonucu döndür (None = hepsi)

        Returns:
            List[Tuple[str, float]]: (text, similarity) listesi (sıralı)
        """
        # Query embedding
        query_emb = self.generate_embedding(query_text)

        # Candidate embeddings
        candidate_embs = self.generate_batch_embeddings(candidate_texts)

        # Similarity hesapla
        similarities = []
        for candidate_emb in candidate_embs:
            similarity = cosine_similarity(
                query_emb.embedding.reshape(1, -1),
                candidate_emb.embedding.reshape(1, -1),
            )[0][0]

            similarity = float(np.clip(similarity, 0.0, 1.0))
            similarities.append((candidate_emb.text, similarity))

        # Sırala (yüksekten düşüğe)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Top-k filtrele
        if top_k is not None:
            similarities = similarities[:top_k]

        return similarities

    def find_most_similar(
        self, query_text: str, candidate_texts: list[str], threshold: float = 0.7
    ) -> list[tuple[str, float]]:
        """
        Threshold üzerinde similarity olan textleri bul

        Args:
            query_text: Query text
            candidate_texts: Candidate text listesi
            threshold: Minimum similarity threshold

        Returns:
            List[Tuple[str, float]]: Threshold üzerindeki (text, similarity) listesi
        """
        similarities = self.calculate_batch_similarities(query_text, candidate_texts)

        # Threshold filtrele
        filtered = [(text, score) for text, score in similarities if score >= threshold]

        return filtered

    def cluster_texts(
        self, texts: list[str], n_clusters: int = 5
    ) -> dict[int, list[str]]:
        """
        Textleri semantic similarity'ye göre cluster'la

        Args:
            texts: Text listesi
            n_clusters: Cluster sayısı

        Returns:
            Dict[int, List[str]]: Cluster ID -> text listesi
        """
        from sklearn.cluster import KMeans

        # Embeddings oluştur
        embeddings = self.generate_batch_embeddings(texts)
        embedding_matrix = np.array([emb.embedding for emb in embeddings])

        # K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embedding_matrix)

        # Cluster'ları organize et
        clusters: dict[int, list[str]] = {i: [] for i in range(n_clusters)}
        for text, label in zip(texts, cluster_labels, strict=False):
            clusters[int(label)].append(text)

        logger.info(f"Clustered {len(texts)} texts into {n_clusters} clusters")
        return clusters

    def get_cache_size(self) -> int:
        """
        Cache boyutunu getir

        Returns:
            int: Cache'deki embedding sayısı
        """
        return len(self.embedding_cache)

    def clear_cache(self) -> None:
        """Cache'i temizle"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")

    def save_embeddings(
        self, embeddings: list[EmbeddingResult], output_file: str
    ) -> None:
        """
        Embeddings'leri dosyaya kaydet

        Args:
            embeddings: Embedding listesi
            output_file: Çıktı dosyası
        """
        data = {
            "model_name": self.model_name,
            "embeddings": [
                {
                    "text": emb.text,
                    "embedding": emb.embedding.tolist(),
                    "dimension": emb.dimension,
                }
                for emb in embeddings
            ],
        }

        import json

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(embeddings)} embeddings to {output_file}")

    def load_embeddings(self, input_file: str) -> list[EmbeddingResult]:
        """
        Embeddings'leri dosyadan yükle

        Args:
            input_file: Input dosyası

        Returns:
            List[EmbeddingResult]: Embedding listesi
        """
        import json

        with open(input_file, encoding="utf-8") as f:
            data = json.load(f)

        embeddings = []
        for item in data["embeddings"]:
            embeddings.append(
                EmbeddingResult(
                    text=item["text"],
                    embedding=np.array(item["embedding"]),
                    dimension=item["dimension"],
                    model_name=data["model_name"],
                )
            )

        logger.info(f"Loaded {len(embeddings)} embeddings from {input_file}")
        return embeddings
