"""
ChromaDB MCP Server - KIRO2 YKS Soru Bankası Semantic Search

Bu MCP server, YKS soru bankasında semantic search sağlar.
Boris Cherny'nin önerdiği verification feedback loops için
soru kalitesi ve benzerlik analizi yapabilir.

Tools:
- search_questions: Semantik soru arama
- find_similar: Benzer sorular bulma
- embed_content: İçerik embedding oluşturma
- verify_question_quality: Soru kalite doğrulama

Spec: REQ-8 MCP Server Integration
- Rate limiting: 100 requests/minute
- Prometheus metrics export

Author: KIRO2 Team
Date: 2026-01-14
"""

import os
import sys
import json
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import Optional, Callable, Any
from pathlib import Path

# Prometheus metrics support
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.environ.get("MCP_RATE_LIMIT", "100"))  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds


class RateLimiter:
    """
    Simple in-memory rate limiter for MCP tools.

    Spec: REQ-8 - 100 requests per minute
    """

    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str = "global") -> tuple[bool, int]:
        """
        Check if request is allowed.

        Returns:
            (is_allowed, remaining_requests)
        """
        now = time.time()
        cutoff = now - self.window

        # Clean old requests
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= self.max_requests:
            return False, 0

        self._requests[key].append(now)
        remaining = self.max_requests - len(self._requests[key])
        return True, remaining

    def get_reset_time(self, key: str = "global") -> float:
        """Get time until rate limit resets."""
        if not self._requests[key]:
            return 0

        oldest = min(self._requests[key])
        return max(0, oldest + self.window - time.time())


# Global rate limiter instance
_rate_limiter = RateLimiter()


class MCPMetrics:
    """
    Prometheus metrics for ChromaDB MCP server.

    Spec: REQ-8 - Prometheus metrics export
    """

    def __init__(self):
        if PROMETHEUS_AVAILABLE:
            # Request counters
            self.requests_total = Counter(
                "chromadb_mcp_requests_total",
                "Total number of MCP requests",
                ["tool", "status"]
            )

            # Latency histogram
            self.request_latency = Histogram(
                "chromadb_mcp_request_latency_seconds",
                "Request latency in seconds",
                ["tool"],
                buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
            )

            # Rate limit counter
            self.rate_limited_total = Counter(
                "chromadb_mcp_rate_limited_total",
                "Number of rate-limited requests"
            )

            # Active requests gauge
            self.active_requests = Gauge(
                "chromadb_mcp_active_requests",
                "Number of currently active requests"
            )

            # Collection size gauge
            self.collection_size = Gauge(
                "chromadb_mcp_collection_size",
                "Number of documents in collection"
            )

    def record_request(self, tool: str, status: str, duration: float):
        """Record a request metric."""
        if PROMETHEUS_AVAILABLE:
            self.requests_total.labels(tool=tool, status=status).inc()
            self.request_latency.labels(tool=tool).observe(duration)

    def record_rate_limit(self):
        """Record a rate-limited request."""
        if PROMETHEUS_AVAILABLE:
            self.rate_limited_total.inc()

    def set_collection_size(self, size: int):
        """Update collection size gauge."""
        if PROMETHEUS_AVAILABLE:
            self.collection_size.set(size)

    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in exposition format."""
        if PROMETHEUS_AVAILABLE:
            return generate_latest()
        return b"# Prometheus not available"


# Global metrics instance
_metrics = MCPMetrics()


def rate_limited_tool(func: Callable) -> Callable:
    """
    Decorator for rate limiting MCP tools.

    Returns error JSON if rate limit exceeded.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        tool_name = func.__name__

        # Check rate limit
        is_allowed, remaining = _rate_limiter.is_allowed()

        if not is_allowed:
            _metrics.record_rate_limit()
            reset_time = _rate_limiter.get_reset_time()
            return json.dumps({
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {RATE_LIMIT_REQUESTS}/minute",
                "retry_after_seconds": round(reset_time, 1),
                "tool": tool_name
            })

        # Execute with metrics
        start_time = time.time()
        status = "success"

        try:
            if PROMETHEUS_AVAILABLE:
                _metrics.active_requests.inc()

            result = await func(*args, **kwargs)

            # Check if result indicates error
            if isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    if "error" in parsed:
                        status = "error"
                except json.JSONDecodeError:
                    pass

            return result

        except Exception:
            status = "error"
            raise

        finally:
            duration = time.time() - start_time
            _metrics.record_request(tool_name, status, duration)

            if PROMETHEUS_AVAILABLE:
                _metrics.active_requests.dec()

    return wrapper

# FastMCP import
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from fastmcp import FastMCP

# ChromaDB import
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

# Sentence transformers for Turkish embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None


# Import embedding config
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.config import EmbeddingConfig
    EMBEDDING_MODEL = EmbeddingConfig.get_model_name()
except ImportError:
    # Fallback to default
    EMBEDDING_MODEL = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"

# NumPy for MMR and Hybrid Ranking
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# Initialize MCP server
mcp = FastMCP("chromadb-mcp")

# Configuration
PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./vector_db")
COLLECTION_NAME = "kiro2_questions"


class ChromaDBService:
    """ChromaDB service for KIRO2 question bank."""

    def __init__(self):
        self.client: Optional[chromadb.Client] = None
        self.collection = None
        self.embedding_model = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize ChromaDB and embedding model."""
        if self._initialized:
            return True

        if not CHROMADB_AVAILABLE:
            return False

        try:
            # Initialize ChromaDB client
            self.client = chromadb.Client(Settings(
                persist_directory=PERSIST_DIR,
                anonymized_telemetry=False
            ))

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )

            # Initialize embedding model if available
            if EMBEDDINGS_AVAILABLE:
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

            self._initialized = True
            return True

        except Exception as e:
            print(f"ChromaDB initialization error: {e}", file=sys.stderr)
            return False

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text."""
        if self.embedding_model is None:
            # Fallback: return simple hash-based embedding
            import hashlib
            hash_bytes = hashlib.sha256(text.encode()).digest()
            return [float(b) / 255.0 for b in hash_bytes[:128]]

        embedding = self.embedding_model.encode(text)
        return embedding.tolist()


# Global service instance
_service = ChromaDBService()


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    İki vektör arasındaki cosine similarity hesaplar.

    Args:
        vec1: Birinci vektör
        vec2: İkinci vektör

    Returns:
        Cosine similarity değeri (0.0 - 1.0 arası)
    """
    if not NUMPY_AVAILABLE:
        # Fallback: basit dot product / norms
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    a = np.array(vec1)
    b = np.array(vec2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def mmr_rerank(
    query_embedding: list[float],
    results: list[dict],
    lambda_param: float = 0.5,
    top_k: int = 10
) -> list[dict]:
    """
    MMR (Maximal Marginal Relevance) ile sonuçları yeniden sıralar.

    Spec REQ-3.5: Diversity sağlamak için MMR algoritması.
    MMR = λ * Sim(d, q) - (1-λ) * max(Sim(d, d_selected))

    Args:
        query_embedding: Sorgu vektörü
        results: Sonuç listesi (her biri 'embedding' ve 'similarity' içermeli)
        lambda_param: Relevance vs diversity dengesi (0.0-1.0)
        top_k: Döndürülecek sonuç sayısı

    Returns:
        MMR ile sıralanmış sonuç listesi
    """
    if not results:
        return []

    if len(results) <= top_k:
        return results

    selected: list[dict] = []
    remaining = list(results)

    while len(selected) < top_k and remaining:
        mmr_scores = []

        for doc in remaining:
            # Relevance: query ile benzerlik
            doc_embedding = doc.get("embedding", [])
            if not doc_embedding:
                # Embedding yoksa mevcut similarity kullan
                relevance = doc.get("similarity", 0.0)
            else:
                relevance = cosine_similarity(query_embedding, doc_embedding)

            # Diversity: seçilen belgelerle maksimum benzerlik
            if selected and doc_embedding:
                max_sim_to_selected = max(
                    cosine_similarity(doc_embedding, s.get("embedding", []))
                    for s in selected
                    if s.get("embedding")
                )
            else:
                max_sim_to_selected = 0.0

            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            mmr_scores.append((doc, mmr_score))

        # En yüksek MMR skorlu belgeyi seç
        best_doc, _ = max(mmr_scores, key=lambda x: x[1])
        selected.append(best_doc)
        remaining.remove(best_doc)

    return selected


def hybrid_rank(
    results: list[dict],
    weights: dict[str, float] | None = None
) -> list[dict]:
    """
    Hybrid ranking ile sonuçları skorlar.

    Spec REQ-3.6: similarity + recency + popularity kombine skorlama.
    Score = w1*similarity + w2*recency_score + w3*popularity_score

    Args:
        results: Sonuç listesi
        weights: Ağırlıklar (varsayılan: similarity=0.6, recency=0.2, popularity=0.2)

    Returns:
        Hybrid score ile sıralanmış sonuç listesi
    """
    if weights is None:
        weights = {"similarity": 0.6, "recency": 0.2, "popularity": 0.2}

    if not results:
        return []

    # Max değerleri bul (normalizasyon için)
    max_views = max((r.get("metadata", {}).get("view_count", 1) for r in results), default=1)
    now = datetime.now()

    for result in results:
        metadata = result.get("metadata", {})

        # 1. Similarity score (zaten normalize 0-1)
        similarity = result.get("similarity", 0.0)

        # 2. Recency score (son 30 günde = 1.0, 365+ gün = 0.0)
        created_at_str = metadata.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                days_old = (now - created_at.replace(tzinfo=None)).days
                recency = max(0.0, 1.0 - (days_old / 365))
            except (ValueError, TypeError):
                recency = 0.5  # Varsayılan
        else:
            recency = 0.5

        # 3. Popularity score (normalize edilmiş view count)
        view_count = metadata.get("view_count", 0)
        popularity = view_count / max_views if max_views > 0 else 0.0

        # Hybrid score hesapla
        hybrid_score = (
            weights["similarity"] * similarity +
            weights["recency"] * recency +
            weights["popularity"] * popularity
        )

        result["hybrid_score"] = round(hybrid_score, 4)
        result["score_breakdown"] = {
            "similarity": round(similarity, 4),
            "recency": round(recency, 4),
            "popularity": round(popularity, 4)
        }

    # Hybrid score'a göre sırala
    return sorted(results, key=lambda x: x.get("hybrid_score", 0), reverse=True)


@mcp.tool()
@rate_limited_tool
async def search_questions(
    query: str,
    subject: str = "",
    exam_type: str = "",
    difficulty_min: float = -4.0,
    difficulty_max: float = 4.0,
    limit: int = 10,
    use_mmr: bool = False,
    mmr_lambda: float = 0.5,
    use_hybrid_ranking: bool = False
) -> str:
    """
    YKS soru bankasında semantik arama yapar.

    Args:
        query: Arama sorgusu (Türkçe)
        subject: Ders filtresi (matematik, fizik, kimya, vb.)
        exam_type: Sınav tipi filtresi (TYT, AYT-SAY, AYT-EA, AYT-SOZ, YDT)
        difficulty_min: Minimum zorluk (-4.0 ile 4.0 arası)
        difficulty_max: Maksimum zorluk (-4.0 ile 4.0 arası)
        limit: Maksimum sonuç sayısı
        use_mmr: MMR (Maximal Marginal Relevance) ile çeşitlilik sağla (Spec REQ-3.5)
        mmr_lambda: MMR lambda parametresi (0.0=diversity, 1.0=relevance)
        use_hybrid_ranking: Hybrid ranking kullan (similarity+recency+popularity) (Spec REQ-3.6)

    Returns:
        JSON formatında benzer sorular
    """
    if not await _service.initialize():
        return json.dumps({
            "error": "ChromaDB initialization failed",
            "available": CHROMADB_AVAILABLE,
            "embeddings": EMBEDDINGS_AVAILABLE
        })

    try:
        # Generate query embedding
        query_embedding = _service.embed_text(query)

        # Build where clause
        where_clause = {}
        if subject:
            where_clause["subject"] = subject
        if exam_type:
            where_clause["exam_type"] = exam_type

        # Query ChromaDB - daha fazla sonuç al (MMR/hybrid için)
        fetch_limit = limit * 3 if (use_mmr or use_hybrid_ranking) else limit

        results = _service.collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_limit,
            where=where_clause if where_clause else None,
            include=["documents", "metadatas", "distances", "embeddings"]
        )

        # Filter by difficulty and build result list
        filtered_results = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                difficulty = metadata.get("difficulty", 0.0)

                if difficulty_min <= difficulty <= difficulty_max:
                    result_item = {
                        "content": doc,
                        "metadata": metadata,
                        "similarity": 1 - results["distances"][0][i] if results.get("distances") else 0
                    }

                    # Embedding'i MMR için sakla (varsa)
                    if results.get("embeddings") and results["embeddings"][0]:
                        result_item["embedding"] = results["embeddings"][0][i]

                    filtered_results.append(result_item)

        # Apply MMR if requested (Spec REQ-3.5)
        if use_mmr and len(filtered_results) > limit:
            filtered_results = mmr_rerank(
                query_embedding=query_embedding,
                results=filtered_results,
                lambda_param=mmr_lambda,
                top_k=limit
            )

        # Apply Hybrid Ranking if requested (Spec REQ-3.6)
        if use_hybrid_ranking:
            filtered_results = hybrid_rank(filtered_results)

        # Limit sonuçları
        filtered_results = filtered_results[:limit]

        # Embedding'leri response'dan kaldır (çok büyük)
        for r in filtered_results:
            r.pop("embedding", None)

        return json.dumps({
            "query": query,
            "results": filtered_results,
            "count": len(filtered_results),
            "filters": {
                "subject": subject,
                "exam_type": exam_type,
                "difficulty_range": [difficulty_min, difficulty_max]
            },
            "ranking": {
                "mmr_enabled": use_mmr,
                "mmr_lambda": mmr_lambda if use_mmr else None,
                "hybrid_ranking_enabled": use_hybrid_ranking
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rate_limited_tool
async def find_similar(
    question_id: str,
    limit: int = 5,
    exclude_same_subject: bool = False
) -> str:
    """
    Belirli bir soruya benzer soruları bulur.

    Args:
        question_id: Kaynak soru ID'si
        limit: Maksimum sonuç sayısı
        exclude_same_subject: Aynı dersteki soruları hariç tut

    Returns:
        JSON formatında benzer sorular
    """
    if not await _service.initialize():
        return json.dumps({"error": "ChromaDB not available"})

    try:
        # Get the source question
        source = _service.collection.get(
            ids=[question_id],
            include=["documents", "metadatas", "embeddings"]
        )

        if not source or not source.get("documents"):
            return json.dumps({"error": f"Question {question_id} not found"})

        source_doc = source["documents"][0]
        source_meta = source["metadatas"][0] if source.get("metadatas") else {}
        source_embedding = source["embeddings"][0] if source.get("embeddings") else None

        # Generate embedding if not stored
        if source_embedding is None:
            source_embedding = _service.embed_text(source_doc)

        # Build where clause
        where_clause = {}
        if exclude_same_subject and source_meta.get("subject"):
            where_clause["subject"] = {"$ne": source_meta["subject"]}

        # Query for similar
        results = _service.collection.query(
            query_embeddings=[source_embedding],
            n_results=limit + 1,  # +1 because source might be included
            where=where_clause if where_clause else None,
            include=["documents", "metadatas", "distances"]
        )

        # Filter out source question
        similar = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                doc_id = results["ids"][0][i] if results.get("ids") else None
                if doc_id != question_id:
                    similar.append({
                        "id": doc_id,
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "similarity": 1 - results["distances"][0][i] if results.get("distances") else 0
                    })

        return json.dumps({
            "source_id": question_id,
            "source_content": source_doc[:200] + "..." if len(source_doc) > 200 else source_doc,
            "similar_questions": similar[:limit],
            "count": len(similar[:limit])
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rate_limited_tool
async def embed_content(
    content: str,
    metadata: dict = None,
    question_id: str = None
) -> str:
    """
    İçeriği embedding'e dönüştürür ve veritabanına kaydeder.

    Args:
        content: Kaydedilecek soru içeriği
        metadata: Soru metadata'sı (subject, exam_type, difficulty, vb.)
        question_id: Opsiyonel soru ID'si (otomatik üretilir)

    Returns:
        JSON formatında kayıt sonucu
    """
    if not await _service.initialize():
        return json.dumps({"error": "ChromaDB not available"})

    try:
        # Generate ID if not provided
        if question_id is None:
            import uuid
            question_id = str(uuid.uuid4())

        # Generate embedding
        embedding = _service.embed_text(content)

        # Prepare metadata
        meta = metadata or {}
        meta["content_length"] = len(content)
        meta["embedding_model"] = EMBEDDING_MODEL

        # Add to collection
        _service.collection.add(
            ids=[question_id],
            documents=[content],
            metadatas=[meta],
            embeddings=[embedding]
        )

        return json.dumps({
            "success": True,
            "question_id": question_id,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "metadata": meta,
            "embedding_dimensions": len(embedding)
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rate_limited_tool
async def verify_question_quality(
    content: str,
    expected_subject: str = "",
    check_duplicates: bool = True,
    similarity_threshold: float = 0.9
) -> str:
    """
    Soru kalitesini doğrular (Boris Cherny verification loop).

    Kontroller:
    - Duplicate detection (benzer sorular)
    - Subject consistency (ders uyumu)
    - Content quality (içerik kalitesi)
    - Turkish character validation

    Args:
        content: Doğrulanacak soru içeriği
        expected_subject: Beklenen ders
        check_duplicates: Duplicate kontrolü yap
        similarity_threshold: Duplicate eşik değeri (0.0-1.0)

    Returns:
        JSON formatında doğrulama sonucu
    """
    if not await _service.initialize():
        return json.dumps({"error": "ChromaDB not available"})

    issues = []
    warnings = []

    try:
        # 1. Content length check
        if len(content) < 50:
            issues.append("Soru içeriği çok kısa (minimum 50 karakter)")
        elif len(content) < 100:
            warnings.append("Soru içeriği kısa, detay eklenebilir")

        # 2. Turkish character check
        turkish_chars = set("çÇğĞıİöÖşŞüÜ")
        has_turkish = any(c in content for c in turkish_chars)
        if not has_turkish:
            warnings.append("Türkçe özel karakter bulunamadı")

        # 3. Option check (A-E)
        has_options = all(f"{opt})" in content or f"{opt}." in content for opt in "ABCDE")
        if not has_options:
            issues.append("YKS formatında 5 şık (A-E) bulunamadı")

        # 4. Duplicate check
        duplicates = []
        if check_duplicates:
            query_embedding = _service.embed_text(content)
            results = _service.collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )

            if results and results.get("distances"):
                for i, dist in enumerate(results["distances"][0]):
                    similarity = 1 - dist
                    if similarity >= similarity_threshold:
                        duplicates.append({
                            "similarity": round(similarity, 3),
                            "content_preview": results["documents"][0][i][:100] + "..."
                        })

            if duplicates:
                issues.append(f"Potansiyel duplicate tespit edildi ({len(duplicates)} adet)")

        # 5. Subject consistency (if we can detect)
        subject_keywords = {
            "matematik": ["denklem", "fonksiyon", "türev", "integral", "geometri"],
            "fizik": ["hız", "ivme", "kuvvet", "enerji", "dalga"],
            "kimya": ["mol", "atom", "element", "tepkime", "asit"],
            "biyoloji": ["hücre", "DNA", "protein", "metabolizma", "gen"],
            "türkçe": ["paragraf", "anlam", "sözcük", "cümle", "yazım"]
        }

        detected_subjects = []
        content_lower = content.lower()
        for subject, keywords in subject_keywords.items():
            if any(kw in content_lower for kw in keywords):
                detected_subjects.append(subject)

        if expected_subject and detected_subjects:
            if expected_subject.lower() not in detected_subjects:
                warnings.append(f"Ders uyumsuzluğu: beklenen={expected_subject}, tespit={detected_subjects}")

        # Final verdict
        is_valid = len(issues) == 0
        quality_score = 100 - (len(issues) * 25) - (len(warnings) * 10)
        quality_score = max(0, min(100, quality_score))

        return json.dumps({
            "valid": is_valid,
            "quality_score": quality_score,
            "issues": issues,
            "warnings": warnings,
            "duplicates": duplicates if check_duplicates else [],
            "detected_subjects": detected_subjects,
            "content_length": len(content),
            "has_turkish_chars": has_turkish,
            "has_yks_options": has_options
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rate_limited_tool
async def health_check_tool() -> str:
    """
    ChromaDB MCP server sağlık kontrolü.

    Spec REQ-8.5: Health check implementasyonu.

    Returns:
        JSON formatında sağlık durumu:
        - status: healthy/unhealthy
        - chromadb_available: ChromaDB paketi mevcut mu
        - embeddings_available: Embedding modeli mevcut mu
        - document_count: Collection'daki döküman sayısı
        - rate_limit_remaining: Kalan rate limit
    """
    initialized = await _service.initialize()

    collection_count = 0
    if initialized and _service.collection:
        try:
            collection_count = _service.collection.count()
        except Exception:
            pass

    # Rate limit durumu
    is_allowed, remaining = _rate_limiter.is_allowed()
    if is_allowed:
        _rate_limiter._requests["global"].pop()  # Bu çağrıyı sayma

    return json.dumps({
        "status": "healthy" if initialized else "unhealthy",
        "chromadb_available": CHROMADB_AVAILABLE,
        "embeddings_available": EMBEDDINGS_AVAILABLE,
        "embedding_model": EMBEDDING_MODEL if EMBEDDINGS_AVAILABLE else None,
        "persist_directory": PERSIST_DIR,
        "collection_name": COLLECTION_NAME,
        "document_count": collection_count,
        "rate_limit_remaining": remaining + (1 if is_allowed else 0),
        "prometheus_available": PROMETHEUS_AVAILABLE
    }, ensure_ascii=False, indent=2)


@mcp.resource("chromadb://health")
async def health_check() -> str:
    """ChromaDB MCP server health check."""
    initialized = await _service.initialize()

    collection_count = 0
    if initialized and _service.collection:
        try:
            collection_count = _service.collection.count()
        except Exception:
            pass

    return json.dumps({
        "status": "healthy" if initialized else "unhealthy",
        "chromadb_available": CHROMADB_AVAILABLE,
        "embeddings_available": EMBEDDINGS_AVAILABLE,
        "embedding_model": EMBEDDING_MODEL if EMBEDDINGS_AVAILABLE else None,
        "persist_directory": PERSIST_DIR,
        "collection_name": COLLECTION_NAME,
        "document_count": collection_count
    }, indent=2)


@mcp.resource("chromadb://stats")
async def collection_stats() -> str:
    """Get collection statistics."""
    if not await _service.initialize():
        return json.dumps({"error": "ChromaDB not available"})

    try:
        count = _service.collection.count()

        # Get sample for subject distribution
        sample = _service.collection.peek(limit=100)
        subjects = {}
        exam_types = {}

        if sample and sample.get("metadatas"):
            for meta in sample["metadatas"]:
                subj = meta.get("subject", "unknown")
                exam = meta.get("exam_type", "unknown")
                subjects[subj] = subjects.get(subj, 0) + 1
                exam_types[exam] = exam_types.get(exam, 0) + 1

        return json.dumps({
            "total_documents": count,
            "subject_distribution": subjects,
            "exam_type_distribution": exam_types,
            "collection_name": COLLECTION_NAME
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("chromadb://metrics")
async def prometheus_metrics() -> str:
    """
    Export Prometheus metrics.

    Spec: REQ-8 - Prometheus metrics export
    """
    # Update collection size metric
    if await _service.initialize() and _service.collection:
        try:
            count = _service.collection.count()
            _metrics.set_collection_size(count)
        except Exception:
            pass

    metrics_data = _metrics.get_metrics()
    return metrics_data.decode("utf-8") if isinstance(metrics_data, bytes) else str(metrics_data)


@mcp.resource("chromadb://rate-limit-status")
async def rate_limit_status() -> str:
    """Get current rate limit status."""
    is_allowed, remaining = _rate_limiter.is_allowed()
    reset_time = _rate_limiter.get_reset_time()

    # Don't consume a request slot for this check
    if is_allowed:
        _rate_limiter._requests["global"].pop()

    return json.dumps({
        "limit": RATE_LIMIT_REQUESTS,
        "window_seconds": RATE_LIMIT_WINDOW,
        "remaining": remaining + (1 if is_allowed else 0),
        "reset_in_seconds": round(reset_time, 1),
        "prometheus_available": PROMETHEUS_AVAILABLE
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
