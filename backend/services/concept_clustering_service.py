"""
Concept Clustering Service - KIRO2 YKS Platform
Clusters educational concepts using K-means and HDBSCAN algorithms.

Spec: REQ-6 Concept Clustering
- K-means and HDBSCAN clustering
- Elbow method for optimal k
- Silhouette score for quality
- UMAP visualization export
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Optional imports with graceful degradation
try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available for clustering")

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    logger.warning("hdbscan not available")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logger.warning("umap-learn not available for visualization")


class ClusteringAlgorithm(str, Enum):
    """Supported clustering algorithms"""
    KMEANS = "kmeans"
    HDBSCAN = "hdbscan"


@dataclass
class ClusterResult:
    """Result of a clustering operation"""
    labels: list[int]
    n_clusters: int
    silhouette_score: float | None = None
    inertia: float | None = None  # For K-means
    noise_points: int = 0  # For HDBSCAN
    algorithm: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ElbowResult:
    """Result of elbow method analysis"""
    k_values: list[int]
    inertias: list[float]
    silhouette_scores: list[float]
    optimal_k: int
    elbow_point: int | None = None


@dataclass
class VisualizationData:
    """2D visualization data from UMAP reduction"""
    x: list[float]
    y: list[float]
    labels: list[int]
    original_ids: list[str] | None = None


class ConceptClusteringService:
    """
    Service for clustering educational concepts.

    Features:
    - K-means clustering with configurable k
    - HDBSCAN for density-based clustering
    - Elbow method for optimal k selection
    - Silhouette scoring for quality measurement
    - UMAP/t-SNE visualization data export
    """

    def __init__(
        self,
        random_state: int = 42,
        default_k_range: tuple[int, int] = (2, 15),
    ):
        """
        Initialize clustering service.

        Args:
            random_state: Random seed for reproducibility
            default_k_range: Default range for elbow method (min, max)
        """
        self.random_state = random_state
        self.default_k_range = default_k_range

        # Validate dependencies
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn required for clustering")

    def cluster_kmeans(
        self,
        embeddings: np.ndarray | list[list[float]],
        k: int,
        max_iter: int = 300,
        n_init: int = 10,
    ) -> ClusterResult:
        """
        Cluster embeddings using K-means algorithm.

        Args:
            embeddings: Array of embeddings (n_samples, n_features)
            k: Number of clusters
            max_iter: Maximum iterations
            n_init: Number of initializations

        Returns:
            ClusterResult with labels and metrics
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for K-means clustering")

        # Convert to numpy if needed
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        # Validate input
        if embeddings.shape[0] < k:
            raise ValueError(f"Cannot create {k} clusters with only {embeddings.shape[0]} samples")

        # Perform clustering
        kmeans = KMeans(
            n_clusters=k,
            max_iter=max_iter,
            n_init=n_init,
            random_state=self.random_state,
        )
        labels = kmeans.fit_predict(embeddings)

        # Calculate silhouette score (requires at least 2 clusters with 2+ samples each)
        sil_score = None
        if k > 1 and len(set(labels)) > 1:
            try:
                sil_score = float(silhouette_score(embeddings, labels))
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score: {e}")

        return ClusterResult(
            labels=labels.tolist(),
            n_clusters=k,
            silhouette_score=sil_score,
            inertia=float(kmeans.inertia_),
            algorithm=ClusteringAlgorithm.KMEANS.value,
            parameters={
                "k": k,
                "max_iter": max_iter,
                "n_init": n_init,
            },
        )

    def cluster_hdbscan(
        self,
        embeddings: np.ndarray | list[list[float]],
        min_cluster_size: int = 5,
        min_samples: int | None = None,
        metric: str = "euclidean",
    ) -> ClusterResult:
        """
        Cluster embeddings using HDBSCAN algorithm.

        Args:
            embeddings: Array of embeddings (n_samples, n_features)
            min_cluster_size: Minimum cluster size
            min_samples: Minimum samples for core points
            metric: Distance metric

        Returns:
            ClusterResult with labels and metrics
        """
        if not HDBSCAN_AVAILABLE:
            raise ImportError("hdbscan package required. Run: pip install hdbscan")

        # Convert to numpy if needed
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        # Perform clustering
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
        )
        labels = clusterer.fit_predict(embeddings)

        # Count clusters (excluding noise label -1)
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        noise_points = (labels == -1).sum()

        # Calculate silhouette score (excluding noise points)
        sil_score = None
        non_noise_mask = labels != -1
        if n_clusters > 1 and non_noise_mask.sum() > 1:
            try:
                sil_score = float(silhouette_score(
                    embeddings[non_noise_mask],
                    labels[non_noise_mask],
                ))
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score: {e}")

        return ClusterResult(
            labels=labels.tolist(),
            n_clusters=n_clusters,
            silhouette_score=sil_score,
            noise_points=int(noise_points),
            algorithm=ClusteringAlgorithm.HDBSCAN.value,
            parameters={
                "min_cluster_size": min_cluster_size,
                "min_samples": min_samples,
                "metric": metric,
            },
        )

    def find_optimal_k(
        self,
        embeddings: np.ndarray | list[list[float]],
        k_range: tuple[int, int] | None = None,
        method: str = "silhouette",
    ) -> ElbowResult:
        """
        Find optimal number of clusters using elbow method.

        Args:
            embeddings: Array of embeddings
            k_range: Range of k values to test (min, max)
            method: Method to determine optimal k ("elbow" or "silhouette")

        Returns:
            ElbowResult with k values, scores, and optimal k
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for elbow method")

        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        k_min, k_max = k_range or self.default_k_range
        k_max = min(k_max, embeddings.shape[0] - 1)  # Can't have more clusters than samples

        if k_min >= k_max:
            raise ValueError("Invalid k_range: need at least 2 different k values")

        k_values = list(range(k_min, k_max + 1))
        inertias = []
        silhouette_scores = []

        for k in k_values:
            result = self.cluster_kmeans(embeddings, k)
            inertias.append(result.inertia or 0)
            silhouette_scores.append(result.silhouette_score or 0)

        # Determine optimal k
        if method == "silhouette":
            # Choose k with highest silhouette score
            optimal_k = k_values[np.argmax(silhouette_scores)]
        else:
            # Elbow method: find point of maximum curvature
            optimal_k = self._find_elbow_point(k_values, inertias)

        return ElbowResult(
            k_values=k_values,
            inertias=inertias,
            silhouette_scores=silhouette_scores,
            optimal_k=optimal_k,
            elbow_point=self._find_elbow_point(k_values, inertias),
        )

    def _find_elbow_point(self, k_values: list[int], inertias: list[float]) -> int:
        """
        Find elbow point using the maximum curvature method.

        Uses the perpendicular distance from each point to the line
        connecting the first and last points.
        """
        if len(k_values) < 3:
            return k_values[0]

        # Normalize values
        k_norm = np.array(k_values) / max(k_values)
        inertia_norm = np.array(inertias) / max(inertias) if max(inertias) > 0 else np.array(inertias)

        # Line from first to last point
        p1 = np.array([k_norm[0], inertia_norm[0]])
        p2 = np.array([k_norm[-1], inertia_norm[-1]])

        # Calculate perpendicular distances
        distances = []
        for i in range(len(k_values)):
            p = np.array([k_norm[i], inertia_norm[i]])
            # Distance from point to line
            d = np.abs(np.cross(p2 - p1, p1 - p)) / np.linalg.norm(p2 - p1)
            distances.append(d)

        # Return k with maximum distance (elbow point)
        return k_values[np.argmax(distances)]

    def calculate_silhouette(
        self,
        embeddings: np.ndarray | list[list[float]],
        labels: list[int],
    ) -> float:
        """
        Calculate silhouette score for given clustering.

        Args:
            embeddings: Array of embeddings
            labels: Cluster labels

        Returns:
            Silhouette score (-1 to 1, higher is better)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for silhouette score")

        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        labels_arr = np.array(labels)

        # Filter out noise points (label -1)
        non_noise = labels_arr != -1
        if non_noise.sum() < 2:
            return 0.0

        unique_labels = set(labels_arr[non_noise])
        if len(unique_labels) < 2:
            return 0.0

        return float(silhouette_score(embeddings[non_noise], labels_arr[non_noise]))

    def export_visualization(
        self,
        embeddings: np.ndarray | list[list[float]],
        labels: list[int],
        original_ids: list[str] | None = None,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
    ) -> VisualizationData:
        """
        Export 2D visualization data using UMAP dimensionality reduction.

        Args:
            embeddings: High-dimensional embeddings
            labels: Cluster labels
            original_ids: Optional original document IDs
            n_neighbors: UMAP neighbors parameter
            min_dist: UMAP minimum distance parameter

        Returns:
            VisualizationData with 2D coordinates
        """
        if not UMAP_AVAILABLE:
            raise ImportError("umap-learn required. Run: pip install umap-learn")

        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        # Reduce to 2D
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=min(n_neighbors, embeddings.shape[0] - 1),
            min_dist=min_dist,
            random_state=self.random_state,
        )
        embedding_2d = reducer.fit_transform(embeddings)

        return VisualizationData(
            x=embedding_2d[:, 0].tolist(),
            y=embedding_2d[:, 1].tolist(),
            labels=labels,
            original_ids=original_ids,
        )

    def auto_cluster(
        self,
        embeddings: np.ndarray | list[list[float]],
        prefer_hdbscan: bool = False,
    ) -> ClusterResult:
        """
        Automatically cluster using best method.

        For small datasets (<100), uses K-means with optimal k.
        For larger datasets, optionally uses HDBSCAN.

        Args:
            embeddings: Array of embeddings
            prefer_hdbscan: Use HDBSCAN if available

        Returns:
            ClusterResult from best method
        """
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        n_samples = embeddings.shape[0]

        # Use HDBSCAN for large datasets if preferred and available
        if prefer_hdbscan and HDBSCAN_AVAILABLE and n_samples > 100:
            return self.cluster_hdbscan(embeddings)

        # Use K-means with optimal k
        if n_samples < 10:
            k = max(2, n_samples // 2)
        else:
            elbow = self.find_optimal_k(embeddings, k_range=(2, min(15, n_samples - 1)))
            k = elbow.optimal_k

        return self.cluster_kmeans(embeddings, k)


# Singleton instance
_clustering_service: ConceptClusteringService | None = None


def get_clustering_service() -> ConceptClusteringService:
    """Get or create the global clustering service instance."""
    global _clustering_service
    if _clustering_service is None:
        _clustering_service = ConceptClusteringService()
    return _clustering_service
