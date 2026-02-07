"""
Vector Store Factory
Centralized creation of optimized vector stores with HNSW support
"""

import logging
import os
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Factory for creating optimized vector stores"""

    @staticmethod
    def create_faiss_store(
        embeddings,
        index_type: str = "hnsw",
        dimension: int = 384,
        persist_directory: Optional[str] = None,
        **kwargs,
    ):
        """
        Create FAISS vector store with optimized indexing

        Args:
            embeddings: Embedding function
            index_type: Index type (flat, ivf, hnsw, ivf_hnsw)
            dimension: Embedding dimension
            persist_directory: Directory to save index
            **kwargs: Additional FAISS parameters

        Returns:
            FAISS vector store
        """
        try:
            import faiss
            from langchain_community.vectorstores import FAISS

            # Create index based on type
            if index_type == "flat":
                # Exact search (L2 distance)
                index = faiss.IndexFlatL2(dimension)
                logger.info("Created FAISS FlatL2 index (exact search)")

            elif index_type == "hnsw":
                # HNSW for approximate nearest neighbor
                M = kwargs.get("M", 32)  # Number of connections
                ef_construction = kwargs.get("ef_construction", 200)
                ef_search = kwargs.get("ef_search", 128)

                index = faiss.IndexHNSWFlat(dimension, M)
                index.hnsw.efConstruction = ef_construction
                index.hnsw.efSearch = ef_search

                logger.info(
                    f"Created FAISS HNSW index "
                    f"(M={M}, efConstruction={ef_construction}, efSearch={ef_search})"
                )

            elif index_type == "ivf":
                # IVF (Inverted File Index) for large datasets
                nlist = kwargs.get("nlist", 100)  # Number of clusters
                quantizer = faiss.IndexFlatL2(dimension)
                index = faiss.IndexIVFFlat(quantizer, dimension, nlist)

                logger.info(f"Created FAISS IVF index (nlist={nlist})")

            elif index_type == "ivf_hnsw":
                # Combination of IVF and HNSW (best for very large datasets)
                nlist = kwargs.get("nlist", 100)
                M = kwargs.get("M", 32)

                quantizer = faiss.IndexHNSWFlat(dimension, M)
                index = faiss.IndexIVFFlat(quantizer, dimension, nlist)

                logger.info(f"Created FAISS IVF-HNSW index " f"(nlist={nlist}, M={M})")

            else:
                raise ValueError(f"Unknown index type: {index_type}")

            # Create docstore and index_to_docstore_id for FAISS
            from langchain_community.docstore.in_memory import InMemoryDocstore

            docstore = InMemoryDocstore({})
            index_to_docstore_id = {}

            # Create FAISS vector store
            vector_store = FAISS(
                embedding_function=embeddings,
                index=index,
                docstore=docstore,
                index_to_docstore_id=index_to_docstore_id,
            )

            # Save path if specified
            if persist_directory:
                os.makedirs(persist_directory, exist_ok=True)
                vector_store._persist_directory = persist_directory

            return vector_store

        except ImportError:
            logger.error("FAISS not available. Install with: pip install faiss-cpu")
            raise
        except Exception as e:
            logger.error(f"Error creating FAISS store: {e}")
            raise

    @staticmethod
    def create_chroma_store(
        embeddings,
        persist_directory: str = "./chroma_db",
        collection_name: str = "documents",
        **kwargs,
    ):
        """
        Create Chroma vector store

        Args:
            embeddings: Embedding function
            persist_directory: Persistence directory
            collection_name: Collection name
            **kwargs: Additional parameters

        Returns:
            Chroma vector store
        """
        try:
            from langchain_community.vectorstores import Chroma

            os.makedirs(persist_directory, exist_ok=True)

            vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                collection_name=collection_name,
            )

            logger.info(f"Created Chroma vector store at {persist_directory}")

            return vector_store

        except ImportError:
            logger.error("Chroma not available. Install with: pip install chromadb")
            raise
        except Exception as e:
            logger.error(f"Error creating Chroma store: {e}")
            raise

    @staticmethod
    def create_qdrant_store(
        embeddings,
        collection_name: str = "documents",
        url: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs,
    ):
        """
        Create Qdrant vector store

        Args:
            embeddings: Embedding function
            collection_name: Collection name
            url: Qdrant server URL (for remote)
            path: Local path (for embedded mode)
            **kwargs: Additional parameters

        Returns:
            Qdrant vector store
        """
        try:
            from langchain_community.vectorstores import Qdrant
            from qdrant_client import QdrantClient

            if url:
                # Remote Qdrant server
                client = QdrantClient(url=url)
                logger.info(f"Connecting to Qdrant server at {url}")
            elif path:
                # Embedded mode
                os.makedirs(path, exist_ok=True)
                client = QdrantClient(path=path)
                logger.info(f"Created embedded Qdrant at {path}")
            else:
                # In-memory
                client = QdrantClient(":memory:")
                logger.info("Created in-memory Qdrant")

            vector_store = Qdrant(
                client=client, collection_name=collection_name, embeddings=embeddings
            )

            return vector_store

        except ImportError:
            logger.error(
                "Qdrant not available. " "Install with: pip install qdrant-client"
            )
            raise
        except Exception as e:
            logger.error(f"Error creating Qdrant store: {e}")
            raise

    @staticmethod
    def create_optimized_store(
        embeddings,
        store_type: str = "auto",
        dimension: int = 384,
        expected_size: int = 1000,
        persist_directory: str = "./vector_db",
        **kwargs,
    ):
        """
        Create optimized vector store based on dataset size and requirements

        Args:
            embeddings: Embedding function
            store_type: Store type (auto, faiss, chroma, qdrant)
            dimension: Embedding dimension
            expected_size: Expected number of documents
            persist_directory: Persistence directory
            **kwargs: Additional parameters

        Returns:
            Optimized vector store
        """
        # Auto-select based on size
        if store_type == "auto":
            if expected_size < 1000:
                # Small dataset - use exact search
                store_type = "faiss"
                index_type = "flat"
                logger.info("Auto-selected FAISS Flat (small dataset)")

            elif expected_size < 100000:
                # Medium dataset - use HNSW
                store_type = "faiss"
                index_type = "hnsw"
                logger.info("Auto-selected FAISS HNSW (medium dataset)")

            else:
                # Large dataset - use IVF-HNSW
                store_type = "faiss"
                index_type = "ivf_hnsw"
                kwargs["nlist"] = min(4096, expected_size // 100)
                logger.info("Auto-selected FAISS IVF-HNSW (large dataset)")

        # Create store
        if store_type == "faiss":
            index_type = kwargs.pop("index_type", "hnsw")
            return VectorStoreFactory.create_faiss_store(
                embeddings=embeddings,
                index_type=index_type,
                dimension=dimension,
                persist_directory=persist_directory,
                **kwargs,
            )

        elif store_type == "chroma":
            return VectorStoreFactory.create_chroma_store(
                embeddings=embeddings, persist_directory=persist_directory, **kwargs
            )

        elif store_type == "qdrant":
            return VectorStoreFactory.create_qdrant_store(
                embeddings=embeddings, path=persist_directory, **kwargs
            )

        else:
            raise ValueError(f"Unknown store type: {store_type}")

    @staticmethod
    def load_faiss_store(
        embeddings, persist_directory: str, index_type: str = "hnsw", **kwargs
    ):
        """Load existing FAISS store"""
        try:
            from langchain_community.vectorstores import FAISS

            index_path = Path(persist_directory)
            if not index_path.exists():
                raise FileNotFoundError(f"FAISS index not found at {persist_directory}")

            vector_store = FAISS.load_local(
                persist_directory,
                embeddings,
                allow_dangerous_deserialization=True,  # Required for pickle
            )

            # Update HNSW search parameters if applicable
            if index_type == "hnsw" and hasattr(vector_store.index, "hnsw"):
                ef_search = kwargs.get("ef_search", 128)
                vector_store.index.hnsw.efSearch = ef_search

            logger.info(f"Loaded FAISS store from {persist_directory}")
            return vector_store

        except Exception as e:
            logger.error(f"Error loading FAISS store: {e}")
            raise

    @staticmethod
    def save_faiss_store(vector_store, persist_directory: str):
        """Save FAISS store to disk"""
        try:
            os.makedirs(persist_directory, exist_ok=True)
            vector_store.save_local(persist_directory)
            logger.info(f"Saved FAISS store to {persist_directory}")

        except Exception as e:
            logger.error(f"Error saving FAISS store: {e}")
            raise


# Recommended configurations for different use cases


def get_speed_optimized_config() -> dict:
    """Configuration optimized for search speed"""
    return {
        "store_type": "faiss",
        "index_type": "hnsw",
        "M": 64,  # More connections = faster search
        "ef_construction": 200,
        "ef_search": 200,
    }


def get_accuracy_optimized_config() -> dict:
    """Configuration optimized for search accuracy"""
    return {
        "store_type": "faiss",
        "index_type": "hnsw",
        "M": 32,
        "ef_construction": 400,  # Better graph quality
        "ef_search": 256,  # More thorough search
    }


def get_memory_optimized_config() -> dict:
    """Configuration optimized for memory usage"""
    return {"store_type": "faiss", "index_type": "ivf", "nlist": 100}


def get_balanced_config() -> dict:
    """Balanced configuration"""
    return {
        "store_type": "faiss",
        "index_type": "hnsw",
        "M": 32,
        "ef_construction": 200,
        "ef_search": 128,
    }
