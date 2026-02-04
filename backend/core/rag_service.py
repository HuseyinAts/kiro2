"""
RAG (Retrieval-Augmented Generation) Service - Performance Optimized
LangChain ve Vector Store entegrasyonu
"""

import hashlib
import json
import logging
import os
import time
import uuid
from functools import lru_cache
from typing import Any

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Performance optimization imports
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available for RAG caching")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGService:
    """RAG pipeline için servis - Performance Optimized"""

    def __init__(self, persist_directory: str = "./vector_db"):
        """
        RAG servisini başlat

        Args:
            persist_directory: Vector store kayıt dizini
        """
        self.persist_directory = persist_directory
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = None

        # Performance optimizations
        self._redis_client = None
        self._search_cache = {}  # In-memory search cache
        self._cache_ttl = int(os.getenv("RAG_CACHE_TTL", "1800"))  # 30 minutes
        self._max_cache_size = int(os.getenv("RAG_MAX_CACHE_SIZE", "500"))

        # Batch processing settings
        self._batch_size = int(os.getenv("RAG_BATCH_SIZE", "50"))

        # Document tracking
        self._document_registry = {}  # Track added documents

        self._initialize()

    def _initialize(self):
        """Servisi başlat"""
        try:
            # Text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )

            # Embeddings (HuggingFace) - use a smaller model that works offline
            try:
                # Try to use HuggingFace embeddings
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # Türkçe desteği
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True},
                )
            except Exception as e:
                logger.warning(f"Could not load HuggingFace embeddings: {e}")
                # Fallback to a simple embedding function for development
                from langchain.embeddings.base import Embeddings

                class SimpleEmbeddings(Embeddings):
                    """Simple embeddings for development without external dependencies"""

                    def embed_documents(self, texts):
                        # Simple hash-based embeddings for development
                        import hashlib

                        embeddings = []
                        for text in texts:
                            # Create a simple 384-dimensional embedding
                            hash_obj = hashlib.sha384(text.encode())
                            hash_bytes = hash_obj.digest()
                            # Convert to float values between -1 and 1
                            embedding = [((b / 255.0) * 2) - 1 for b in hash_bytes]
                            embeddings.append(embedding)
                        return embeddings

                    def embed_query(self, text):
                        return self.embed_documents([text])[0]

                self.embeddings = SimpleEmbeddings()
                logger.info("Using simple embeddings for development")

            # Vector store - use optimized factory with HNSW support
            try:
                from core.vector_store_factory import VectorStoreFactory
                from core.rag_config import get_rag_config

                config = get_rag_config()
                store_type = config.vector_store.store_type

                # Try to load existing store
                try:
                    if store_type == "faiss":
                        self.vector_store = VectorStoreFactory.load_faiss_store(
                            embeddings=self.embeddings,
                            persist_directory=self.persist_directory,
                            index_type="hnsw",
                        )
                        logger.info("Loaded existing FAISS HNSW index")
                    elif store_type == "chroma":
                        self.vector_store = VectorStoreFactory.create_chroma_store(
                            embeddings=self.embeddings,
                            persist_directory=self.persist_directory,
                        )
                        logger.info("Loaded existing Chroma store")
                except (FileNotFoundError, Exception) as e:
                    logger.info(
                        f"No existing store found, will create on first add: {e}"
                    )
                    self.vector_store = None

            except Exception as e:
                logger.error(f"Vector store initialization error: {e}")
                self.vector_store = None

            # Initialize Redis for caching if available
            if REDIS_AVAILABLE:
                try:
                    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                    self._redis_client = redis.from_url(
                        redis_url, decode_responses=True
                    )
                    # Test connection will be done on first use
                    self._redis_tested = False
                except Exception as e:
                    logger.warning(f"Could not initialize Redis for RAG caching: {e}")

            logger.info("RAG Service initialized successfully")

        except Exception as e:
            logger.error(f"RAG Service initialization error: {e!s}")
            raise

    async def _test_redis_connection(self):
        """Test Redis connection"""
        try:
            if self._redis_client:
                await self._redis_client.ping()
                logger.info("Redis connection for RAG caching established")
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}")
            self._redis_client = None

    def _generate_search_cache_key(
        self, query: str, k: int, filter_dict: dict | None = None
    ) -> str:
        """Generate cache key for search queries"""
        cache_data = {"query": query, "k": k, "filter": filter_dict or {}}
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def _get_cached_search_results(
        self, cache_key: str
    ) -> list[dict[str, Any]] | None:
        """Get cached search results"""
        try:
            # Try Redis first
            if self._redis_client:
                cached = await self._redis_client.get(f"rag_search:{cache_key}")
                if cached:
                    logger.debug(f"RAG search cache hit (Redis): {cache_key[:8]}...")
                    return json.loads(cached)

            # Fallback to in-memory cache
            if cache_key in self._search_cache:
                cached_data, timestamp = self._search_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    logger.debug(f"RAG search cache hit (memory): {cache_key[:8]}...")
                    return cached_data
                # Remove expired entry
                del self._search_cache[cache_key]

        except Exception as e:
            logger.error(f"Error getting cached search results: {e}")

        return None

    async def _set_cached_search_results(
        self, cache_key: str, results: list[dict[str, Any]]
    ):
        """Set cached search results"""
        try:
            # Try Redis first
            if self._redis_client:
                await self._redis_client.setex(
                    f"rag_search:{cache_key}", self._cache_ttl, json.dumps(results)
                )
                logger.debug(f"RAG search results cached (Redis): {cache_key[:8]}...")
                return

            # Fallback to in-memory cache
            # Implement LRU eviction if cache is full
            if len(self._search_cache) >= self._max_cache_size:
                # Remove oldest entry
                oldest_key = min(
                    self._search_cache.keys(), key=lambda k: self._search_cache[k][1]
                )
                del self._search_cache[oldest_key]

            self._search_cache[cache_key] = (results, time.time())
            logger.debug(f"RAG search results cached (memory): {cache_key[:8]}...")

        except Exception as e:
            logger.error(f"Error setting cached search results: {e}")

    @lru_cache(maxsize=100)
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better search results - cached"""
        # Basic text preprocessing
        text = text.strip().lower()
        # Remove extra whitespace
        text = " ".join(text.split())
        return text

    def _rerank_results(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int = None,
    ) -> list[dict[str, Any]]:
        """
        Rerank results using cross-encoder for better accuracy

        Args:
            query: Original query
            results: Initial results
            top_k: Number of results to keep after reranking

        Returns:
            Reranked results
        """
        try:
            from core.reranker import get_turkish_reranker

            # Use Turkish-optimized reranker
            reranker = get_turkish_reranker()
            reranked = reranker.rerank(query, results, top_k=top_k)

            # Convert back to dict format
            return [
                {
                    "content": r.content,
                    "text": r.content,
                    "score": r.score,
                    "metadata": r.metadata,
                    "original_score": r.original_score,
                    "rerank_score": r.rerank_score,
                }
                for r in reranked
            ]

        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return results

    async def add_document(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Single document ekle (API uyumlu method)

        Args:
            text: Doküman metni
            metadata: Doküman metadata'sı

        Returns:
            Document ID
        """
        import uuid

        # Check for duplicates
        from core.document_deduplication import get_deduplicator

        dedup = get_deduplicator()
        is_duplicate, original = dedup.is_duplicate(text, method="hash")

        if is_duplicate:
            logger.warning(f"Document is duplicate, skipping: {text[:100]}...")
            raise ValueError("Document is duplicate")

        doc_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["doc_id"] = doc_id

        result = await self.add_documents(
            documents=[{"content": text, "metadata": metadata}]
        )

        if result.get("success"):
            # Track document in registry
            self._document_registry[doc_id] = {
                "text_length": len(text),
                "metadata": metadata,
                "added_at": time.time(),
            }

            # Add to deduplicator
            dedup.add_document(text)

            return doc_id
        raise Exception(result.get("error", "Unknown error"))

    async def add_documents(
        self, documents: list[dict[str, Any]], metadata_fields: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Dokümanlari vector store'a ekle

        Args:
            documents: Doküman listesi [{"content": "...", "metadata": {...}}]
            metadata_fields: Saklanacak metadata alanları

        Returns:
            İşlem sonucu
        """
        try:
            # Dokümanları hazırla
            langchain_docs = []
            for doc in documents:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})

                # Metadata filtrele
                if metadata_fields:
                    metadata = {
                        k: v for k, v in metadata.items() if k in metadata_fields
                    }

                # Metni parçala
                if len(content) > 1000:
                    chunks = self.text_splitter.split_text(content)
                    for i, chunk in enumerate(chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata["chunk_index"] = i
                        langchain_docs.append(
                            Document(page_content=chunk, metadata=chunk_metadata)
                        )
                else:
                    langchain_docs.append(
                        Document(page_content=content, metadata=metadata)
                    )

            # Vector store'a ekle
            if langchain_docs:
                # Handle vector store initialization on first add
                if self.vector_store is None:
                    from core.vector_store_factory import VectorStoreFactory
                    from core.rag_config import get_rag_config

                    config = get_rag_config()

                    # Create optimized store based on config
                    self.vector_store = VectorStoreFactory.create_optimized_store(
                        embeddings=self.embeddings,
                        store_type=config.vector_store.store_type,
                        dimension=384,  # MiniLM dimension
                        expected_size=10000,  # Estimate
                        persist_directory=self.persist_directory,
                    )
                    logger.info(
                        f"Created new {config.vector_store.store_type} vector store"
                    )

                # Add documents
                ids = self.vector_store.add_documents(langchain_docs)

                # Persist
                if hasattr(self.vector_store, "persist"):
                    self.vector_store.persist()
                elif hasattr(self.vector_store, "save_local"):
                    # FAISS
                    from core.vector_store_factory import VectorStoreFactory

                    VectorStoreFactory.save_faiss_store(
                        self.vector_store, self.persist_directory
                    )

                return {
                    "success": True,
                    "message": f"{len(langchain_docs)} doküman eklendi",
                    "document_ids": ids,
                }
            return {"success": False, "message": "Eklenecek doküman bulunamadı"}

        except Exception as e:
            logger.error(f"Add documents error: {e!s}")
            return {"success": False, "error": str(e)}

    async def hybrid_search(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.5,  # 0 = pure keyword, 1 = pure semantic
    ) -> list[dict[str, Any]]:
        """
        Hybrid search combining semantic + keyword (BM25)

        Args:
            query: Arama sorgusu
            k: Sonuç sayısı
            alpha: Semantic/keyword balance (0-1)

        Returns:
            Hybrid search results
        """
        try:
            from langchain.retrievers import EnsembleRetriever
            from langchain_community.retrievers import BM25Retriever

            # Semantic retriever
            semantic_retriever = self.vector_store.as_retriever(search_kwargs={"k": k})

            # Get all documents for BM25 (cache this in production)
            all_docs = []
            if hasattr(self.vector_store, "_collection"):
                # Chroma specific
                try:
                    all_docs_data = self.vector_store._collection.get()
                    all_docs = [
                        Document(page_content=text, metadata=meta)
                        for text, meta in zip(
                            all_docs_data["documents"], all_docs_data["metadatas"]
                        )
                    ]
                except Exception:
                    pass

            if all_docs:
                # Keyword retriever
                keyword_retriever = BM25Retriever.from_documents(all_docs)
                keyword_retriever.k = k

                # Ensemble
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[keyword_retriever, semantic_retriever],
                    weights=[1 - alpha, alpha],
                )

                results = await ensemble_retriever.ainvoke(query)

                return [
                    {
                        "content": doc.page_content,
                        "text": doc.page_content,
                        "metadata": doc.metadata,
                        "score": 1.0,  # Ensemble doesn't provide scores
                    }
                    for doc in results
                ]
            # Fallback to semantic only
            return await self.search(query, k=k)

        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            # Fallback to regular search
            return await self.search(query, k=k)

    async def multi_query_search(
        self,
        query: str,
        k: int = 5,
        num_expansions: int = 2,
    ) -> list[dict[str, Any]]:
        """
        Search using query expansion for better recall

        Args:
            query: Original query
            k: Number of results
            num_expansions: Number of query variations

        Returns:
            Fused search results
        """
        try:
            from core.query_expansion import get_query_expander, MultiQueryRetriever

            # Get expander
            expander = get_query_expander()

            # Create multi-query retriever
            multi_retriever = MultiQueryRetriever(self.vector_store, expander)

            # Retrieve with query expansion
            results = await multi_retriever.retrieve(
                query=query,
                k=k,
                num_expansions=num_expansions,
                aggregation="ranked_fusion",
            )

            return results

        except Exception as e:
            logger.error(f"Multi-query search error: {e}")
            # Fallback to regular search
            return await self.search(query, k=k)

    async def search(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
        score_threshold: float = 0.5,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Vector store'da arama yap - Performance Optimized with Caching

        Args:
            query: Arama sorgusu
            k: Döndürülecek sonuç sayısı
            filter: Metadata filtresi
            score_threshold: Minimum benzerlik skoru
            use_cache: Cache kullanılsın mı

        Returns:
            Arama sonuçları
        """
        try:
            # Preprocess query for better results
            processed_query = self._preprocess_text(query)

            # Check cache first if enabled
            if use_cache:
                cache_key = self._generate_search_cache_key(processed_query, k, filter)
                cached_results = await self._get_cached_search_results(cache_key)
                if cached_results:
                    # Filter by score threshold
                    filtered_results = [
                        r
                        for r in cached_results
                        if r.get("score", 0) >= score_threshold
                    ]
                    return filtered_results

            # Benzerlik araması - handle both with_score and regular methods
            try:
                # Try with score first (preferred)
                results = self.vector_store.similarity_search_with_score(
                    query=processed_query, k=k, filter=filter
                )
                has_scores = True
            except (AttributeError, NotImplementedError):
                # Fallback to regular search
                results = self.vector_store.similarity_search(
                    query=processed_query, k=k, filter=filter
                )
                has_scores = False

            # Sonuçları formatla
            formatted_results = []
            for item in results:
                if has_scores:
                    doc, score = item
                else:
                    doc = item
                    score = 1.0  # Default score if not available

                if score >= score_threshold:
                    formatted_results.append(
                        {
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "score": float(score),
                            "text": doc.page_content,  # API compatibility
                        }
                    )

            # Apply reranking for better accuracy
            if formatted_results:
                formatted_results = self._rerank_results(query, formatted_results, k)

            # Cache the results if caching is enabled
            if use_cache and formatted_results:
                await self._set_cached_search_results(cache_key, formatted_results)

            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {e!s}")
            return []

    async def query_with_context(
        self, query: str, context_size: int = 3, prompt_template: str | None = None
    ) -> dict[str, Any]:
        """
        Kontekst ile birlikte sorgulama (RAG)

        Args:
            query: Kullanıcı sorusu
            context_size: Kullanılacak kontekst sayısı
            prompt_template: Özel prompt şablonu

        Returns:
            Yanıt ve kontekst
        """
        try:
            # Benzer dokümanları bul
            relevant_docs = await self.search(query, k=context_size)

            if not relevant_docs:
                return {
                    "success": False,
                    "message": "İlgili doküman bulunamadı",
                    "query": query,
                }

            # Konteksti oluştur
            context = "\n\n".join([doc["content"] for doc in relevant_docs])

            # Prompt oluştur
            if not prompt_template:
                prompt_template = """Aşağıdaki konteksti kullanarak soruyu cevapla.
Eğer kontekstte cevap yoksa, bilmediğini belirt.

Kontekst:
{context}

Soru: {question}

Cevap:"""

            prompt = prompt_template.format(context=context, question=query)

            return {
                "success": True,
                "prompt": prompt,
                "context": context,
                "relevant_docs": relevant_docs,
                "query": query,
            }

        except Exception as e:
            logger.error(f"Query with context error: {e!s}")
            return {"success": False, "error": str(e)}

    async def add_educational_content(
        self, content_type: str, content: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Eğitim içeriği ekle

        Args:
            content_type: İçerik tipi (lesson, quiz, video_transcript, etc.)
            content: İçerik metni
            metadata: İçerik metadata'sı (subject, grade, topic, etc.)

        Returns:
            İşlem sonucu
        """
        # Metadata'ya içerik tipini ekle
        metadata["content_type"] = content_type

        # LGS/YKS için özel etiketler
        if "exam_type" not in metadata:
            # İçerikten otomatik tespit et
            if any(
                word in content.lower()
                for word in ["lgs", "8. sınıf", "sekizinci sınıf"]
            ):
                metadata["exam_type"] = "LGS"
            elif any(
                word in content.lower() for word in ["yks", "tyt", "ayt", "üniversite"]
            ):
                metadata["exam_type"] = "YKS"

        # Dokümanı ekle
        return await self.add_documents([{"content": content, "metadata": metadata}])

    async def search_educational_content(
        self,
        query: str,
        subject: str | None = None,
        grade: str | None = None,
        exam_type: str | None = None,
        content_type: str | None = None,
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Eğitim içeriği ara

        Args:
            query: Arama sorgusu
            subject: Ders (matematik, fen, etc.)
            grade: Sınıf seviyesi
            exam_type: Sınav tipi (LGS, YKS)
            content_type: İçerik tipi
            k: Sonuç sayısı

        Returns:
            Filtrelenmiş arama sonuçları
        """
        # Filtre oluştur
        filter_dict = {}
        if subject:
            filter_dict["subject"] = subject
        if grade:
            filter_dict["grade"] = grade
        if exam_type:
            filter_dict["exam_type"] = exam_type
        if content_type:
            filter_dict["content_type"] = content_type

        # Arama yap
        return await self.search(
            query=query, k=k, filter=filter_dict if filter_dict else None
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get RAG service statistics"""
        try:
            stats = {
                "total_documents": len(self._document_registry),
                "cache_size": len(self._search_cache),
                "cache_hit_ratio": 0.0,
                "vector_store_type": type(self.vector_store).__name__
                if self.vector_store
                else "None",
                "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
                "persist_directory": self.persist_directory,
            }

            # Try to get vector store count
            if self.vector_store:
                try:
                    if hasattr(self.vector_store, "_collection"):
                        # Chroma
                        count = self.vector_store._collection.count()
                        stats["total_chunks"] = count
                    elif hasattr(self.vector_store, "index"):
                        # FAISS
                        stats["total_chunks"] = self.vector_store.index.ntotal
                except Exception:
                    pass

            return stats
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {"error": str(e)}

    def clear_database(self):
        """Vector store'u temizle"""
        try:
            if hasattr(self.vector_store, "delete_collection"):
                self.vector_store.delete_collection()
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )
            elif hasattr(self.vector_store, "delete"):
                # FAISS - recreate
                self.vector_store = None

            self._document_registry.clear()
            self._search_cache.clear()

            logger.info("Vector database cleared")
            return {"success": True, "message": "Database temizlendi"}
        except Exception as e:
            logger.error(f"Clear database error: {e!s}")
            return {"success": False, "error": str(e)}


# Singleton instance
rag_service = RAGService()
