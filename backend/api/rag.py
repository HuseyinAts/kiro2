"""
RAG (Retrieval-Augmented Generation) API Endpoints
Production-ready vector search and document retrieval

Features:
- Document indexing (PDF, TXT, MD)
- Semantic search
- Context retrieval for LLM
- Turkish language support
- Caching and optimization
"""

# Defer annotation evaluation: ``RAGService`` may be ``None`` at import time
# (optional dependency fallback), and without PEP 563 the module-level
# annotation ``_rag_service: RAGService | None`` would evaluate ``None | None``
# and crash the whole router.
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from core.dependencies import (
    get_current_user,  # fixed: was auth_dependencies (no blacklist)
)

try:
    from core.rag_service import RAGService
except (ImportError, TypeError):
    RAGService = None

from core.structured_logger import get_logger
from models.database import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["RAG - Retrieval Augmented Generation"])

# Global RAG service instance
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Get or create RAG service instance.

    Raises a 503 "Service Unavailable" if the optional RAG dependencies
    (e.g. chromadb, embeddings) could not be imported. Without this guard
    handlers would call ``RAGService()`` against the ``None`` sentinel set
    at import time and the whole request would crash with
    ``TypeError: 'NoneType' object is not callable`` (caught by the bare
    ``except Exception`` block and surfaced as a generic 500 — a silent
    regression). Matches the ``_require_berturk_service()`` pattern
    introduced for GF22.
    """
    global _rag_service
    if RAGService is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "RAG service unavailable: optional dependencies "
                "(chromadb / nomic-embed-text) are not installed."
            ),
        )
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


# ==================== REQUEST/RESPONSE MODELS ====================


class DocumentIndexRequest(BaseModel):
    """Document indexing request"""

    content: str = Field(
        ..., min_length=10, max_length=100000, description="Document content"
    )
    metadata: dict = Field(
        default_factory=dict, description="Document metadata (title, subject, etc.)"
    )
    source: str = Field(default="manual", description="Document source")


class DocumentIndexResponse(BaseModel):
    """Document indexing response"""

    success: bool
    document_id: str
    chunks_created: int
    message: str


class SearchRequest(BaseModel):
    """Semantic search request"""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    k: int = Field(default=4, ge=1, le=20, description="Number of results")
    filter_metadata: dict | None = Field(None, description="Metadata filters")


class SearchResult(BaseModel):
    """Search result item"""

    content: str
    score: float
    metadata: dict
    source: str


class SearchResponse(BaseModel):
    """Search response"""

    success: bool
    results: list[SearchResult]
    total_results: int
    query: str


class ContextRequest(BaseModel):
    """Context retrieval for LLM"""

    query: str = Field(..., min_length=1, max_length=1000)
    k: int = Field(default=3, ge=1, le=10)
    include_metadata: bool = Field(default=True)


class ContextResponse(BaseModel):
    """Context response for LLM"""

    success: bool
    context: str
    sources: list[dict]
    token_count: int


class DocumentListResponse(BaseModel):
    """Document list response"""

    success: bool
    documents: list[dict]
    total_count: int


class StatsResponse(BaseModel):
    """RAG service statistics"""

    success: bool
    stats: dict


# ==================== ENDPOINTS ====================


@router.post("/index/text", response_model=DocumentIndexResponse)
async def index_text_document(
    request: DocumentIndexRequest, current_user: User = Depends(get_current_user)
):
    """
    Index a text document for semantic search

    - Split into chunks
    - Create embeddings
    - Store in vector database
    """
    try:
        rag_service = get_rag_service()

        # Add document with metadata
        doc_metadata = {
            **request.metadata,
            "user_id": current_user.id,
            "source": request.source,
            "indexed_at": str(time.time()),
        }

        doc_id = await rag_service.add_document(
            text=request.content, metadata=doc_metadata
        )

        # Calculate chunks created
        chunks = len(request.content) // 1000 + 1

        logger.info(
            "document_indexed", doc_id=doc_id, chunks=chunks, user_id=current_user.id
        )

        return DocumentIndexResponse(
            success=True,
            document_id=doc_id,
            chunks_created=chunks,
            message="Document indexed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document indexing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/index/file", response_model=DocumentIndexResponse)
async def index_file_document(
    file: UploadFile = File(...),
    metadata: str = "{}",  # JSON string
    current_user: User = Depends(get_current_user),
):
    """
    Index a file document (PDF, TXT, MD)

    - Extract text from file
    - Index content
    """
    try:
        import json

        # Parse metadata
        file_metadata = json.loads(metadata) if metadata else {}

        # Read file content
        content = await file.read()

        # Detect file type and extract text
        filename = file.filename or "unknown"
        file_ext = filename.split(".")[-1].lower()

        if file_ext in ["txt", "md"]:
            text = content.decode("utf-8")
        elif file_ext == "pdf":
            # PDF extraction (requires pypdf)
            try:
                from io import BytesIO

                from pypdf import PdfReader

                pdf = PdfReader(BytesIO(content))
                text = "\n\n".join([page.extract_text() for page in pdf.pages])
            except ImportError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF support requires pypdf package",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}",
            )

        # Index document
        rag_service = get_rag_service()

        doc_metadata = {
            **file_metadata,
            "filename": filename,
            "file_type": file_ext,
            "user_id": current_user.id,
            "indexed_at": str(time.time()),
        }

        doc_id = await rag_service.add_document(text=text, metadata=doc_metadata)

        chunks = len(text) // 1000 + 1

        logger.info(
            "file_indexed",
            filename=filename,
            doc_id=doc_id,
            chunks=chunks,
            user_id=current_user.id,
        )

        return DocumentIndexResponse(
            success=True,
            document_id=doc_id,
            chunks_created=chunks,
            message=f"File '{filename}' indexed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File indexing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest, current_user: User = Depends(get_current_user)
):
    """
    Semantic search across indexed documents

    - Vector similarity search
    - Ranked results
    - Metadata filtering
    """
    try:
        rag_service = get_rag_service()

        is_admin = getattr(current_user, "role", "") in ("ADMIN", "admin")
        
        # Enforce IDOR protection: Users can only search their own documents
        user_filter = {} if is_admin else {"user_id": current_user.id}
        filter_dict = {**(request.filter_metadata or {}), **user_filter}

        # Perform search
        results = await rag_service.search(
            query=request.query, k=request.k, filter_dict=filter_dict
        )

        # Format results
        search_results = [
            SearchResult(
                content=result["text"],
                score=result.get("score", 0.0),
                metadata=result.get("metadata", {}),
                source=result.get("metadata", {}).get("source", "unknown"),
            )
            for result in results
        ]

        logger.info(
            "semantic_search_completed",
            query=request.query,
            results_count=len(search_results),
            user_id=current_user.id,
        )

        return SearchResponse(
            success=True,
            results=search_results,
            total_results=len(search_results),
            query=request.query,
        )

    except HTTPException:
        # 503 from get_rag_service() must propagate unchanged — see GF56.
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/context", response_model=ContextResponse)
async def get_llm_context(
    request: ContextRequest, current_user: User = Depends(get_current_user)
):
    """
    Get relevant context for LLM prompt

    - Retrieve relevant documents
    - Format as context string
    - Ready for LLM consumption
    """
    try:
        rag_service = get_rag_service()

        is_admin = getattr(current_user, "role", "") in ("ADMIN", "admin")
        
        # Enforce IDOR protection: Users can only retrieve context from their own documents
        user_filter = None if is_admin else {"user_id": current_user.id}

        # Search for relevant documents
        results = await rag_service.search(query=request.query, k=request.k, filter_dict=user_filter)

        # Build context string
        context_parts = []
        sources = []

        for idx, result in enumerate(results, 1):
            text = result["text"]
            metadata = result.get("metadata", {})

            context_parts.append(f"[{idx}] {text}")

            if request.include_metadata:
                sources.append(
                    {
                        "index": idx,
                        "source": metadata.get("source", "unknown"),
                        "metadata": metadata,
                    }
                )

        context = "\n\n".join(context_parts)

        # Estimate token count (rough: 1 token ≈ 4 characters)
        token_count = len(context) // 4

        logger.info(
            "llm_context_retrieved",
            query=request.query,
            sources_count=len(sources),
            token_count=token_count,
            user_id=current_user.id,
        )

        return ContextResponse(
            success=True, context=context, sources=sources, token_count=token_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    limit: int = 50, offset: int = 0, current_user: User = Depends(get_current_user)
):
    """
    List indexed documents

    - Pagination support
    - User filtering
    """
    try:
        rag_service = get_rag_service()

        # Alias offset to skip for consistency with code below
        skip = offset

        # Get documents from vector store
        documents = []
        total_count = 0
        is_admin = getattr(current_user, "role", "") in ("ADMIN", "admin")

        try:
            # Get document registry from RAG service
            if hasattr(rag_service, "_document_registry"):
                registry = rag_service._document_registry
                
                filtered_registry = {}
                for doc_id, doc_info in registry.items():
                    owner_id = doc_info.get("user_id") or doc_info.get("metadata", {}).get("user_id")
                    if is_admin or owner_id == current_user.id:
                        filtered_registry[doc_id] = doc_info
                        
                total_count = len(filtered_registry)

                # Convert registry to document list
                for doc_id, doc_info in filtered_registry.items():
                    documents.append(
                        {
                            "id": doc_id,
                            "title": doc_info.get("title", "Untitled"),
                            "source": doc_info.get("source", "unknown"),
                            "indexed_at": doc_info.get("indexed_at", ""),
                            "chunk_count": doc_info.get("chunk_count", 0),
                            "metadata": doc_info.get("metadata", {}),
                        }
                    )

                # Sort by indexed_at descending
                documents.sort(key=lambda x: str(x.get("indexed_at", "")), reverse=True)

                # Apply pagination
                start_idx = skip
                end_idx = skip + limit
                documents = documents[start_idx:end_idx]

            # If no registry, try to get from vector store directly
            elif hasattr(rag_service, "vector_store") and rag_service.vector_store:
                try:
                    # Try to get collection info from Chroma
                    collection = rag_service.vector_store._collection
                    if collection:
                        where_clause = None if is_admin else {"user_id": current_user.id}
                        
                        try:
                            results = collection.get(
                                where=where_clause,
                                limit=limit, offset=skip
                            )

                            if results and results.get("ids"):
                                for i, (doc_id, metadata) in enumerate(
                                    zip(
                                        results.get("ids", []), results.get("metadatas", [])
                                    )
                                ):
                                    documents.append(
                                        {
                                            "id": doc_id,
                                            "title": metadata.get(
                                                "title", f"Document {i + 1}"
                                            ),
                                            "source": metadata.get("source", "unknown"),
                                            "indexed_at": metadata.get("indexed_at", ""),
                                            "chunk_count": 1,
                                            "metadata": metadata,
                                        }
                                    )
                                total_count = len(documents) # Note: page size count
                        except Exception as e:
                            logger.warning(f"Error filtering chroma results: {e}")
                except Exception as e:
                    logger.warning(f"Could not get documents from vector store: {e}")

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")

        return DocumentListResponse(
            success=True, documents=documents, total_count=total_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str, current_user: User = Depends(get_current_user)
):
    """
    Delete indexed document

    - Remove from vector store
    - Clear embeddings
    """
    try:
        rag_service = get_rag_service()

        is_admin = getattr(current_user, "role", "") in ("ADMIN", "admin")

        # Delete from document registry
        deleted = False
        if hasattr(rag_service, "_document_registry"):
            if document_id in rag_service._document_registry:
                doc_info = rag_service._document_registry[document_id]
                
                # Check ownership
                owner_id = doc_info.get("user_id") or doc_info.get("metadata", {}).get("user_id")
                if not is_admin and owner_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to delete this document",
                    )
                
                del rag_service._document_registry[document_id]
                deleted = True

        # Delete from vector store
        if hasattr(rag_service, "vector_store") and rag_service.vector_store:
            try:
                # Get collection
                collection = rag_service.vector_store._collection
                if collection:
                    # Check ownership in vector store if not already checked in registry
                    if not deleted and not is_admin:
                        results = collection.get(where={"document_id": document_id})
                        if results and results.get("metadatas") and len(results["metadatas"]) > 0:
                            doc_meta = results["metadatas"][0]
                            if doc_meta.get("user_id") != current_user.id:
                                raise HTTPException(
                                    status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Not authorized to delete this document",
                                )
                    
                    # Delete documents with matching IDs
                    # Chroma uses filter-based deletion
                    collection.delete(where={"document_id": document_id})
                    deleted = True
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Could not delete from vector store: {e}")

        # Clear related cache entries
        if hasattr(rag_service, "_search_cache"):
            # Clear cache entries related to this document
            keys_to_remove = [
                key
                for key in rag_service._search_cache.keys()
                if document_id in str(key)
            ]
            for key in keys_to_remove:
                del rag_service._search_cache[key]

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        logger.info("document_deleted", doc_id=document_id, user_id=current_user.id)

        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/stats", response_model=StatsResponse)
async def get_rag_stats(current_user: User = Depends(get_current_user)):
    """
    RAG service statistics

    - Total documents
    - Total chunks
    - Cache statistics
    """
    try:
        rag_service = get_rag_service()

        stats = rag_service.get_statistics()
        stats["status"] = "operational"

        return StatsResponse(success=True, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/health")
async def health_check():
    """
    RAG service health check
    """
    try:
        rag_service = get_rag_service()

        return {
            "status": "healthy",
            "service": "RAG",
            "embeddings_loaded": rag_service.embeddings is not None,
            "vector_store_loaded": rag_service.vector_store is not None,
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
