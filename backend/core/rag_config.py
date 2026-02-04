"""
RAG System Configuration
Centralized settings for all RAG components
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""

    # Model selection
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    model_type: str = "huggingface"  # huggingface, openai, cohere
    device: str = "cpu"  # cpu, cuda

    # OpenAI settings (if used)
    openai_api_key: Optional[str] = None
    openai_model: str = "text-embedding-ada-002"

    # Cohere settings (if used)
    cohere_api_key: Optional[str] = None
    cohere_model: str = "embed-multilingual-v3.0"

    # Performance
    batch_size: int = 32
    normalize: bool = True


@dataclass
class VectorStoreConfig:
    """Vector store configuration"""

    # Store type
    store_type: str = "chroma"  # chroma, faiss, qdrant
    persist_directory: str = "./vector_db"
    collection_name: str = "kiro2_documents"

    # Chroma specific
    chroma_host: Optional[str] = None
    chroma_port: Optional[int] = None

    # FAISS specific
    faiss_index_type: str = "FlatL2"  # FlatL2, IVFFlat, HNSW

    # Search settings
    similarity_metric: str = "cosine"  # cosine, l2, ip
    search_k: int = 4
    fetch_k: int = 20  # For MMR


@dataclass
class TextSplitterConfig:
    """Text chunking configuration"""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: list = None

    def __post_init__(self):
        if self.separators is None:
            self.separators = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class CacheConfig:
    """Cache configuration"""

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = True
    redis_ttl: int = 1800  # 30 minutes
    redis_max_connections: int = 10

    # In-memory
    memory_cache_size: int = 500
    memory_ttl: int = 3600  # 1 hour

    # Performance
    enable_search_cache: bool = True
    cache_key_prefix: str = "kiro2:rag"


@dataclass
class SearchConfig:
    """Search and retrieval configuration"""

    # Search modes
    default_k: int = 5
    max_k: int = 20
    score_threshold: float = 0.5

    # Hybrid search
    enable_hybrid: bool = True
    hybrid_alpha: float = 0.5  # 0=keyword, 1=semantic

    # Reranking
    enable_reranking: bool = True
    rerank_weight: float = 0.3

    # MMR (diversity)
    enable_mmr: bool = False
    mmr_lambda: float = 0.5


@dataclass
class RAGConfig:
    """Complete RAG system configuration"""

    embedding: EmbeddingConfig = None
    vector_store: VectorStoreConfig = None
    text_splitter: TextSplitterConfig = None
    cache: CacheConfig = None
    search: SearchConfig = None

    # Educational features
    turkish_optimization: bool = True
    subject_filtering: bool = True
    exam_type_tagging: bool = True

    # Performance
    async_mode: bool = True
    max_concurrent_requests: int = 10

    def __post_init__(self):
        # Initialize sub-configs if not provided
        if self.embedding is None:
            self.embedding = EmbeddingConfig()
        if self.vector_store is None:
            self.vector_store = VectorStoreConfig()
        if self.text_splitter is None:
            self.text_splitter = TextSplitterConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.search is None:
            self.search = SearchConfig()

        # Load from environment variables
        self._load_from_env()

    def _load_from_env(self):
        """Load configuration from environment variables"""

        # Embedding
        if os.getenv("EMBEDDING_MODEL"):
            self.embedding.model_name = os.getenv("EMBEDDING_MODEL")
        if os.getenv("OPENAI_API_KEY"):
            self.embedding.openai_api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("COHERE_API_KEY"):
            self.embedding.cohere_api_key = os.getenv("COHERE_API_KEY")

        # Vector store
        if os.getenv("VECTOR_STORE_TYPE"):
            self.vector_store.store_type = os.getenv("VECTOR_STORE_TYPE")
        if os.getenv("VECTOR_DB_PATH"):
            self.vector_store.persist_directory = os.getenv("VECTOR_DB_PATH")

        # Cache
        if os.getenv("REDIS_URL"):
            self.cache.redis_url = os.getenv("REDIS_URL")
        if os.getenv("RAG_CACHE_TTL"):
            self.cache.redis_ttl = int(os.getenv("RAG_CACHE_TTL"))

        # Search
        if os.getenv("RAG_DEFAULT_K"):
            self.search.default_k = int(os.getenv("RAG_DEFAULT_K"))


# Global configuration instance
_config: Optional[RAGConfig] = None


def get_rag_config() -> RAGConfig:
    """Get or create global RAG configuration"""
    global _config
    if _config is None:
        _config = RAGConfig()
    return _config


def set_rag_config(config: RAGConfig):
    """Set global RAG configuration"""
    global _config
    _config = config


# Preset configurations for different use cases


def get_development_config() -> RAGConfig:
    """Configuration for development environment"""
    config = RAGConfig()
    config.vector_store.store_type = "faiss"  # In-memory
    config.cache.redis_enabled = False
    config.search.enable_hybrid = False
    return config


def get_production_config() -> RAGConfig:
    """Configuration for production environment"""
    config = RAGConfig()
    config.vector_store.store_type = "chroma"
    config.cache.redis_enabled = True
    config.search.enable_hybrid = True
    config.search.enable_reranking = True
    return config


def get_high_performance_config() -> RAGConfig:
    """Configuration optimized for high performance"""
    config = RAGConfig()
    config.vector_store.store_type = "faiss"
    config.vector_store.faiss_index_type = "IVFFlat"
    config.cache.redis_enabled = True
    config.cache.memory_cache_size = 1000
    config.search.enable_hybrid = True
    config.search.enable_reranking = True
    config.embedding.batch_size = 64
    config.max_concurrent_requests = 20
    return config


def get_turkish_optimized_config() -> RAGConfig:
    """Configuration optimized for Turkish educational content"""
    config = RAGConfig()
    config.embedding.model_name = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    config.text_splitter.chunk_size = 800  # Shorter for Turkish
    config.text_splitter.chunk_overlap = 150
    config.turkish_optimization = True
    config.subject_filtering = True
    config.exam_type_tagging = True
    config.search.enable_hybrid = True
    config.search.hybrid_alpha = 0.6  # More semantic weight for Turkish
    return config
