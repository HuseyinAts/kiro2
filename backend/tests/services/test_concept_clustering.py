"""
Tests for Concept Clustering Service
Spec: REQ-6 Concept Clustering
"""

import numpy as np
import pytest


class TestClusteringAlgorithm:
    """Test clustering algorithm enum"""

    def test_algorithm_values(self):
        """Algorithm enum should have expected values"""
        from backend.services.concept_clustering_service import ClusteringAlgorithm

        assert ClusteringAlgorithm.KMEANS.value == "kmeans"
        assert ClusteringAlgorithm.HDBSCAN.value == "hdbscan"


class TestClusterResult:
    """Test ClusterResult dataclass"""

    def test_cluster_result_creation(self):
        """ClusterResult should hold all fields"""
        from backend.services.concept_clustering_service import ClusterResult

        result = ClusterResult(
            labels=[0, 0, 1, 1, 2],
            n_clusters=3,
            silhouette_score=0.75,
            algorithm="kmeans",
        )

        assert len(result.labels) == 5
        assert result.n_clusters == 3
        assert result.silhouette_score == 0.75


class TestConceptClusteringService:
    """Test ConceptClusteringService"""

    @pytest.fixture
    def sample_embeddings(self):
        """Generate sample embeddings for testing"""
        np.random.seed(42)
        # Create 3 clear clusters
        cluster1 = np.random.randn(10, 10) + np.array([5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster2 = np.random.randn(10, 10) + np.array([0, 5, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster3 = np.random.randn(10, 10) + np.array([0, 0, 5, 0, 0, 0, 0, 0, 0, 0])
        return np.vstack([cluster1, cluster2, cluster3])

    @pytest.fixture
    def service(self):
        """Create clustering service instance"""
        from backend.services.concept_clustering_service import ConceptClusteringService

        return ConceptClusteringService(random_state=42)

    def test_kmeans_clustering(self, service, sample_embeddings):
        """K-means should cluster data correctly"""
        result = service.cluster_kmeans(sample_embeddings, k=3)

        assert result.n_clusters == 3
        assert len(result.labels) == 30
        assert result.algorithm == "kmeans"
        assert result.inertia is not None
        # Silhouette should be reasonably high for well-separated clusters
        assert result.silhouette_score is not None
        assert result.silhouette_score > 0.3

    def test_kmeans_invalid_k(self, service, sample_embeddings):
        """K-means should raise error for invalid k"""
        with pytest.raises(ValueError, match="Cannot create"):
            service.cluster_kmeans(sample_embeddings, k=100)

    def test_find_optimal_k(self, service, sample_embeddings):
        """Elbow method should find reasonable k"""
        result = service.find_optimal_k(sample_embeddings, k_range=(2, 6))

        assert result.optimal_k >= 2
        assert result.optimal_k <= 6
        assert len(result.k_values) == 5  # 2,3,4,5,6
        assert len(result.inertias) == 5
        assert len(result.silhouette_scores) == 5

    def test_silhouette_calculation(self, service, sample_embeddings):
        """Silhouette score calculation should work"""
        # First cluster
        result = service.cluster_kmeans(sample_embeddings, k=3)

        # Then calculate silhouette
        score = service.calculate_silhouette(sample_embeddings, result.labels)

        assert -1 <= score <= 1
        # Well-separated clusters should have positive silhouette
        assert score > 0

    def test_auto_cluster(self, service, sample_embeddings):
        """Auto cluster should select appropriate method"""
        result = service.auto_cluster(sample_embeddings)

        assert result.n_clusters >= 2
        assert len(result.labels) == 30
        assert result.algorithm in ["kmeans", "hdbscan"]

    def test_list_input(self, service):
        """Service should accept list input"""
        embeddings = [[1.0, 2.0], [1.1, 2.1], [5.0, 6.0], [5.1, 6.1]]
        result = service.cluster_kmeans(embeddings, k=2)

        assert result.n_clusters == 2
        assert len(result.labels) == 4


class TestElbowResult:
    """Test ElbowResult dataclass"""

    def test_elbow_result_fields(self):
        """ElbowResult should have all required fields"""
        from backend.services.concept_clustering_service import ElbowResult

        result = ElbowResult(
            k_values=[2, 3, 4],
            inertias=[100.0, 50.0, 30.0],
            silhouette_scores=[0.3, 0.5, 0.4],
            optimal_k=3,
            elbow_point=3,
        )

        assert result.optimal_k == 3
        assert len(result.k_values) == 3


class TestVisualizationData:
    """Test VisualizationData dataclass"""

    def test_visualization_data_fields(self):
        """VisualizationData should have coordinates and labels"""
        from backend.services.concept_clustering_service import VisualizationData

        viz = VisualizationData(
            x=[1.0, 2.0, 3.0],
            y=[4.0, 5.0, 6.0],
            labels=[0, 0, 1],
            original_ids=["id1", "id2", "id3"],
        )

        assert len(viz.x) == 3
        assert len(viz.y) == 3
        assert len(viz.labels) == 3


# Skip HDBSCAN tests if not available
try:
    import hdbscan as _hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False


@pytest.mark.skipif(not HDBSCAN_AVAILABLE, reason="hdbscan not installed")
class TestHDBSCANClustering:
    """Test HDBSCAN clustering"""

    @pytest.fixture
    def service(self):
        from backend.services.concept_clustering_service import ConceptClusteringService
        return ConceptClusteringService()

    @pytest.fixture
    def sample_embeddings(self):
        np.random.seed(42)
        cluster1 = np.random.randn(20, 10) + np.array([10, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster2 = np.random.randn(20, 10) + np.array([0, 10, 0, 0, 0, 0, 0, 0, 0, 0])
        return np.vstack([cluster1, cluster2])

    def test_hdbscan_clustering(self, service, sample_embeddings):
        """HDBSCAN should identify clusters"""
        result = service.cluster_hdbscan(sample_embeddings, min_cluster_size=5)

        assert result.algorithm == "hdbscan"
        assert len(result.labels) == 40
        # Should find at least 1 cluster
        assert result.n_clusters >= 1


# Skip UMAP tests if not available
try:
    import umap as _umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False


@pytest.mark.skipif(not UMAP_AVAILABLE, reason="umap-learn not installed")
class TestVisualization:
    """Test UMAP visualization"""

    @pytest.fixture
    def service(self):
        from backend.services.concept_clustering_service import ConceptClusteringService
        return ConceptClusteringService()

    def test_visualization_export(self, service):
        """UMAP visualization should reduce to 2D"""
        np.random.seed(42)
        embeddings = np.random.randn(20, 50)
        labels = [0] * 10 + [1] * 10

        viz = service.export_visualization(embeddings, labels)

        assert len(viz.x) == 20
        assert len(viz.y) == 20
        assert viz.labels == labels
