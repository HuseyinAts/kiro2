"""
Clustering API Endpoints - KIRO2 YKS Platform
REST API for concept clustering operations.

Spec: REQ-6 Concept Clustering

GET /api/v1/clustering/health — liveness + DB ping (no auth)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from core.database import get_db_session_context
from core.dependencies import (
    get_current_user,  # fixed: was auth_dependencies (no blacklist)
)
from services.concept_clustering_service import (
    HDBSCAN_AVAILABLE,
    SKLEARN_AVAILABLE,
    UMAP_AVAILABLE,
    ClusteringAlgorithm,
    get_clustering_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/clustering", tags=["clustering"])


@router.get("/health", summary="Clustering servis saglik kontrolu")
async def health_check() -> dict[str, Any]:
    """Clustering servisinin temel calisma durumunu raporla."""
    # Lightweight DB liveness ping — sibling /health endpoints all report a
    # `database` flag (GF150 health-probe convention).
    # NEDEN MODUL DUZEYI AD (yerel import DEGIL): fonksiyon icindeki
    # `from core.database import get_db_session_context` her cagrida ADI
    # YENIDEN BAGLIYORDU, bu yuzden `@patch("api.clustering_api.
    # get_db_session_context")` HICBIR ETKI ETMIYORDU -- DB ping'i tasarlanan
    # testler sessizce gercek DB'ye gidiyor, yani bir sey OLCMUYORDU
    # (tests/fast/test_push_clustering_health.py). Modul duzeyindeki ad
    # kullanildiginda yama devreye giriyor ve test deterministik oluyor.
    db_ok = False
    try:
        async with get_db_session_context() as _db:
            await _db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as _dbe:
        logger.debug("clustering health DB ping failed: %s", _dbe)

    try:
        deps = {
            "sklearn_available": SKLEARN_AVAILABLE,
            "hdbscan_available": HDBSCAN_AVAILABLE,
            "umap_available": UMAP_AVAILABLE,
        }
        # K-means temel fonksiyon, digerleri optional degiskenlerdir.
        healthy = deps["sklearn_available"]
        return {
            "status": "healthy" if healthy else "degraded",
            "service": "concept_clustering",
            "database": db_ok,
            "chromadb_available": True,
            "dependencies": deps,
        }
    except Exception as e:
        logger.error(f"Clustering health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "concept_clustering",
            "database": db_ok,
            "error": "Internal error",
            "chromadb_available": False,
        }


# Request/Response Models
class ClusterRequest(BaseModel):
    """Request for clustering operation"""

    embeddings: list[list[float]] = Field(
        ...,
        description="List of embeddings to cluster",
        min_length=2,
    )
    algorithm: ClusteringAlgorithm = Field(
        default=ClusteringAlgorithm.KMEANS,
        description="Clustering algorithm to use",
    )
    k: int | None = Field(
        default=None,
        description="Number of clusters (for K-means, auto-detected if not provided)",
        ge=2,
        le=100,
    )
    min_cluster_size: int = Field(
        default=5,
        description="Minimum cluster size (for HDBSCAN)",
        ge=2,
    )
    document_ids: list[str] | None = Field(
        default=None,
        description="Optional document IDs for tracking",
    )


class ClusterResponse(BaseModel):
    """Response from clustering operation"""

    labels: list[int]
    n_clusters: int
    silhouette_score: float | None
    algorithm: str
    parameters: dict[str, Any]
    noise_points: int = 0


class ElbowRequest(BaseModel):
    """Request for elbow method analysis"""

    embeddings: list[list[float]] = Field(
        ...,
        description="List of embeddings to analyze",
        min_length=3,
    )
    k_min: int = Field(default=2, ge=2)
    k_max: int = Field(default=15, le=50)
    method: str = Field(
        default="silhouette",
        description="Method for optimal k: 'silhouette' or 'elbow'",
    )


class ElbowResponse(BaseModel):
    """Response from elbow analysis"""

    k_values: list[int]
    inertias: list[float]
    silhouette_scores: list[float]
    optimal_k: int
    elbow_point: int | None


class VisualizationRequest(BaseModel):
    """Request for visualization data"""

    embeddings: list[list[float]] = Field(
        ...,
        description="High-dimensional embeddings",
        min_length=2,
    )
    labels: list[int] = Field(
        ...,
        description="Cluster labels",
    )
    document_ids: list[str] | None = None
    n_neighbors: int = Field(default=15, ge=2, le=100)
    min_dist: float = Field(default=0.1, ge=0.0, le=1.0)


class VisualizationResponse(BaseModel):
    """Response with 2D visualization coordinates"""

    x: list[float]
    y: list[float]
    labels: list[int]
    document_ids: list[str] | None = None


# KALDIRILAN IKINCI /health ROTASI (6 Eyl 2026)
#
# Burada `clustering_health()` adiyla IKINCI bir `@router.get("/health")`
# duruyordu. OLCUM: FastAPI ayni yol icin ILK kayitli rotayi servis eder,
# yani bu ikinci rota CALISMIYORDU -- olu koddu. Kaniti uc yerden:
#   * Canli sozlesmeyi olcen iki test ILK rotanin sekline gore yazilmis:
#     tests/e2e/test_golden_flows.py:5597 ("concept_clustering") ve
#     tests/fast/test_chroma_semantic_health.py:52 ("chromadb_available").
#   * `tests/fast/test_push_clustering_health.py` ise BU olu rotanin
#     sekline ("clustering" / "ok") gore yazilmisti ve bu yuzden HICBIR
#     ZAMAN gecemezdi -- yani bir kusuru degil, kendi hayalini olcuyordu.
#   * `backend/openapi.json` ayni yol anahtarini ikinci rotayla EZDIGI icin
#     uretilen sema (ve ondan turetilen frontend/src/types/api.generated.ts)
#     sunucunun ASLA dondurmedigi bir govdeyi belgeliyordu. Frontend'de bu
#     uca yapilan tek bir cagri yok (grep "clustering/health" frontend/src
#     -> yalniz api.generated.ts).
# DB ping'i ve `database` bayragi zaten yukaridaki ILK rotaya tasinmisti
# (GF150 konvansiyonu), yani islevsel kayip yoktur.


@router.post("/concepts", response_model=ClusterResponse)
async def cluster_concepts(
    request: ClusterRequest,
    current_user: dict = Depends(get_current_user),
) -> ClusterResponse:
    """
    Cluster concepts using specified algorithm.

    - **K-means**: Requires k parameter or auto-detects optimal k
    - **HDBSCAN**: Density-based, automatically determines clusters
    """
    service = get_clustering_service()

    try:
        if request.algorithm == ClusteringAlgorithm.KMEANS:
            # Auto-detect k if not provided
            if request.k is None:
                elbow = service.find_optimal_k(request.embeddings)
                k = elbow.optimal_k
            else:
                k = request.k

            result = service.cluster_kmeans(request.embeddings, k)

        elif request.algorithm == ClusteringAlgorithm.HDBSCAN:
            result = service.cluster_hdbscan(
                request.embeddings,
                min_cluster_size=request.min_cluster_size,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown algorithm: {request.algorithm}",
            )

        return ClusterResponse(
            labels=result.labels,
            n_clusters=result.n_clusters,
            silhouette_score=result.silhouette_score,
            algorithm=result.algorithm,
            parameters=result.parameters,
            noise_points=result.noise_points,
        )

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clustering operation failed",
        )


@router.post("/optimal-k", response_model=ElbowResponse)
async def find_optimal_clusters(
    request: ElbowRequest,
    current_user: dict = Depends(get_current_user),
) -> ElbowResponse:
    """
    Find optimal number of clusters using elbow method.

    Returns inertia values, silhouette scores, and recommended k.
    """
    service = get_clustering_service()

    try:
        result = service.find_optimal_k(
            request.embeddings,
            k_range=(request.k_min, request.k_max),
            method=request.method,
        )

        return ElbowResponse(
            k_values=result.k_values,
            inertias=result.inertias,
            silhouette_scores=result.silhouette_scores,
            optimal_k=result.optimal_k,
            elbow_point=result.elbow_point,
        )

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/visualization", response_model=VisualizationResponse)
async def get_visualization_data(
    request: VisualizationRequest,
    current_user: dict = Depends(get_current_user),
) -> VisualizationResponse:
    """
    Get 2D visualization data using UMAP dimensionality reduction.

    Reduces high-dimensional embeddings to 2D for visualization.
    """
    service = get_clustering_service()

    if len(request.embeddings) != len(request.labels):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Embeddings and labels must have same length",
        )

    try:
        result = service.export_visualization(
            request.embeddings,
            request.labels,
            original_ids=request.document_ids,
            n_neighbors=request.n_neighbors,
            min_dist=request.min_dist,
        )

        return VisualizationResponse(
            x=result.x,
            y=result.y,
            labels=result.labels,
            document_ids=result.original_ids,
        )

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/silhouette")
async def calculate_silhouette(
    embeddings: list[list[float]],
    labels: list[int],
    current_user: dict = Depends(get_current_user),
) -> dict[str, float]:
    """
    Calculate silhouette score for a clustering result.

    Score ranges from -1 to 1:
    - 1: Perfect clustering
    - 0: Overlapping clusters
    - -1: Incorrect clustering
    """
    service = get_clustering_service()

    if len(embeddings) != len(labels):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Embeddings and labels must have same length",
        )

    try:
        score = service.calculate_silhouette(embeddings, labels)
        return {"silhouette_score": score}

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/auto")
async def auto_cluster(
    embeddings: list[list[float]],
    prefer_hdbscan: bool = False,
    current_user: dict = Depends(get_current_user),
) -> ClusterResponse:
    """
    Automatically cluster using best available method.

    Automatically selects algorithm and parameters based on data size.
    """
    service = get_clustering_service()

    try:
        result = service.auto_cluster(embeddings, prefer_hdbscan=prefer_hdbscan)

        return ClusterResponse(
            labels=result.labels,
            n_clusters=result.n_clusters,
            silhouette_score=result.silhouette_score,
            algorithm=result.algorithm,
            parameters=result.parameters,
            noise_points=result.noise_points,
        )

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
