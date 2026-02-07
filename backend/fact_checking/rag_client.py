"""
RAG (Retrieval-Augmented Generation) Client

Bu modül, dahili bilgi tabanı (ChromaDB) ile fact-checking yapar.

Features:
- Vector database query
- Semantic similarity hesaplama
- Claim verification

Requirements: REQ-4.1, REQ-4.2
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RAGVerificationResult(BaseModel):
    """RAG doğrulama sonucu"""
    found: bool = Field(description="Bilgi bulundu mu")
    confidence: float = Field(ge=0.0, le=1.0, description="Güven skoru")
    status: str = Field(description="true/false/partially_true/unverified")
    evidence: Optional[str] = Field(default=None, description="Kanıt metni")
    source_documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Kaynak dökümanlar"
    )


class RAGClient:
    """
    RAG sistem client'ı - dahili bilgi tabanı doğrulaması.

    ChromaDB MCP server ile entegre çalışır.
    """

    # Similarity eşik değerleri
    HIGH_SIMILARITY_THRESHOLD = 0.90
    MEDIUM_SIMILARITY_THRESHOLD = 0.70
    LOW_SIMILARITY_THRESHOLD = 0.50

    def __init__(
        self,
        collection_name: str = "kiro2_knowledge_base",
        chromadb_host: Optional[str] = None,
        chromadb_port: int = 8100,
    ):
        """
        Args:
            collection_name: ChromaDB collection ismi
            chromadb_host: ChromaDB host (None=local)
            chromadb_port: ChromaDB port
        """
        self.collection_name = collection_name
        self.chromadb_host = chromadb_host
        self.chromadb_port = chromadb_port
        self._client = None
        self._collection = None
        self._embedding_model = None

    async def initialize(self) -> bool:
        """
        ChromaDB bağlantısını başlat.

        Returns:
            bool: Başarılı mı
        """
        try:
            import chromadb

            if self.chromadb_host:
                self._client = chromadb.HttpClient(
                    host=self.chromadb_host,
                    port=self.chromadb_port,
                )
            else:
                self._client = chromadb.Client()

            # Collection'ı al veya oluştur
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "KIRO2 bilgi tabanı"}
            )

            logger.info(f"ChromaDB initialized: {self.collection_name}")
            return True

        except ImportError:
            logger.warning("chromadb not installed")
            return False
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            return False

    async def verify_claim(self, claim: str) -> RAGVerificationResult:
        """
        Bir iddiayı bilgi tabanında doğrula.

        Args:
            claim: Doğrulanacak iddia

        Returns:
            RAGVerificationResult: Doğrulama sonucu
        """
        if self._collection is None:
            await self.initialize()

        if self._collection is None:
            return RAGVerificationResult(
                found=False,
                confidence=0.0,
                status="unverified",
                evidence=None,
            )

        try:
            # Vector search yap
            results = self._collection.query(
                query_texts=[claim],
                n_results=5,
                include=["documents", "distances", "metadatas"],
            )

            if not results or not results.get("documents", [[]])[0]:
                return RAGVerificationResult(
                    found=False,
                    confidence=0.0,
                    status="unverified",
                    evidence=None,
                )

            # En iyi eşleşmeyi al
            documents = results["documents"][0]
            distances = results["distances"][0] if results.get("distances") else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []

            # Distance'ı similarity'ye çevir (1 - normalized_distance)
            if distances:
                # ChromaDB L2 distance kullanır
                similarity = 1 / (1 + distances[0])
            else:
                similarity = 0.5

            # En iyi döküman
            best_doc = documents[0] if documents else ""
            _ = metadatas[0] if metadatas else {}  # Reserved for future use

            # Verification status belirle
            if similarity > self.HIGH_SIMILARITY_THRESHOLD:
                status = "true"
                confidence = similarity
            elif similarity > self.MEDIUM_SIMILARITY_THRESHOLD:
                status = "partially_true"
                confidence = similarity * 0.8
            elif similarity > self.LOW_SIMILARITY_THRESHOLD:
                status = "unverified"
                confidence = similarity * 0.5
            else:
                status = "unverified"
                confidence = 0.0

            # Kaynak dökümanları hazırla
            source_docs = []
            for i, doc in enumerate(documents[:3]):
                source_docs.append({
                    "text": doc[:500] if doc else "",
                    "similarity": 1 / (1 + distances[i]) if i < len(distances) else 0,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                })

            return RAGVerificationResult(
                found=True,
                confidence=confidence,
                status=status,
                evidence=best_doc[:500] if best_doc else None,
                source_documents=source_docs,
            )

        except Exception as e:
            logger.error(f"RAG verification error: {e}")
            return RAGVerificationResult(
                found=False,
                confidence=0.0,
                status="unverified",
                evidence=None,
            )

    async def add_to_knowledge_base(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Bilgi tabanına döküman ekle.

        Args:
            documents: Döküman listesi
            metadatas: Metadata listesi
            ids: ID listesi

        Returns:
            bool: Başarılı mı
        """
        if self._collection is None:
            await self.initialize()

        if self._collection is None:
            return False

        try:
            # ID oluştur
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]

            self._collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Added {len(documents)} documents to knowledge base")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    async def search_similar(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Benzer dökümanları ara.

        Args:
            query: Arama sorgusu
            n_results: Sonuç sayısı
            filter_metadata: Metadata filtresi

        Returns:
            List[Dict]: Benzer dökümanlar
        """
        if self._collection is None:
            await self.initialize()

        if self._collection is None:
            return []

        try:
            where = filter_metadata if filter_metadata else None

            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "distances", "metadatas"],
            )

            if not results or not results.get("documents", [[]])[0]:
                return []

            documents = results["documents"][0]
            distances = results["distances"][0] if results.get("distances") else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []

            result_list = []
            for i, doc in enumerate(documents):
                result_list.append({
                    "text": doc,
                    "similarity": 1 / (1 + distances[i]) if i < len(distances) else 0,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                })

            return result_list

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_collection_count(self) -> int:
        """
        Collection'daki döküman sayısını al.

        Returns:
            int: Döküman sayısı
        """
        if self._collection is None:
            return 0

        try:
            return self._collection.count()
        except Exception:
            return 0
