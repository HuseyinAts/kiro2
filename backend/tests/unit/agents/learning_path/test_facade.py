"""
Tests for LearningPathFacade

KIRO2 - YKS Hazırlık Platformu
Unit tests for the facade layer that coordinates learning path services.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.learning_path.facade import (
    FacadeConfig,
    LearningPathFacade,
    get_learning_path_facade,
)
from agents.learning_path.models import (
    KnowledgeLevel,
    LearningPath,
    LearningPhase,
    LearningResource,
    LearningStyle,
    PathNode,
    StudentProfile,
)
from agents.learning_path.services.path_adaptation import (
    AdaptationAction,
    AdaptationResult,
    AdaptationType,
    PerformanceMetrics,
)
from agents.learning_path.services.path_generation import (
    PathGenerationResult,
)
from agents.learning_path.services.resource_discovery import (
    DiscoveryResult,
)


@pytest.fixture
def mock_student_profile():
    """Create a mock student profile with correct fields."""
    return StudentProfile(
        student_id="test-student-123",
        name="Test Öğrenci",
        grade="11",
        exam_target="YKS",
        learning_goal="YKS hazırlık",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=["matematik", "fizik"],
        available_time=120,
    )


@pytest.fixture
def mock_learning_resource():
    """Create a mock learning resource with correct fields."""
    return LearningResource(
        resource_id="res-1",
        title="Türev Video Dersi",
        source="YouTube",
        url="https://youtube.com/watch?v=abc",
        resource_type="video",
        difficulty_level=KnowledgeLevel.INTERMEDIATE,
        estimated_time=30,
        language="tr",
        description="Türev konusunda temel kavramlar ve çözüm teknikleri",
        tags=["matematik", "türev", "YKS"],
    )


@pytest.fixture
def mock_learning_path(mock_learning_resource):
    """Create a mock learning path with correct fields."""
    return LearningPath(
        path_id="path-123",
        student_id="test-student-123",
        goal="Türev konusunu öğren",
        resources=[mock_learning_resource],
        phases=[
            LearningPhase(
                phase_id="phase-1",
                name="Temel Türev",
                description="Türev temelleri",
                order=1,
                resources=[mock_learning_resource],
                learning_objectives=["Türev kavramını anla"],
            )
        ],
        created_at=datetime.now(),
        reasoning="Öğrenci seviyesine uygun yol oluşturuldu",
    )


@pytest.fixture
def mock_path_node(mock_learning_resource):
    """Create a mock path node with correct fields."""
    return PathNode(
        node_id="node-1",
        topic="Temel Türev",
        order=1,
        resources=[mock_learning_resource],
        estimated_time=60,
    )


@pytest.fixture
def mock_resources(mock_learning_resource):
    """Create mock learning resources list."""
    return [
        mock_learning_resource,
        LearningResource(
            resource_id="res-2",
            title="Türev Alıştırmaları",
            source="Khan Academy",
            url="https://khanacademy.org/turev",
            resource_type="practice",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=45,
            language="tr",
            description="Türev alıştırma soruları",
            tags=["matematik", "türev", "alıştırma"],
        ),
    ]


@pytest.fixture
def facade_config():
    """Create facade configuration."""
    return FacadeConfig(
        enable_caching=True,
        cache_ttl_seconds=300,
        max_resources_per_search=20,
    )


class TestLearningPathFacadeInit:
    """Tests for facade initialization."""

    def test_facade_init_default(self):
        """Test facade initializes with default config."""
        facade = LearningPathFacade()
        assert facade.config is not None
        assert facade.config.enable_caching is True
        assert facade._path_generation is None  # Lazy init

    def test_facade_init_with_config(self, facade_config):
        """Test facade initializes with custom config."""
        facade = LearningPathFacade(config=facade_config)
        assert facade.config.enable_caching is True
        assert facade.config.max_resources_per_search == 20

    def test_facade_lazy_service_init(self):
        """Test services are lazy initialized."""
        facade = LearningPathFacade()

        # Services should be None initially
        assert facade._path_generation is None
        assert facade._resource_discovery is None
        assert facade._path_adaptation is None


class TestLearningPathFacadeServices:
    """Tests for facade service properties."""

    def test_path_generation_property(self):
        """Test path_generation property lazy initializes."""
        facade = LearningPathFacade()

        # Access the property
        service = facade.path_generation

        # Should be initialized now
        assert service is not None
        assert facade._path_generation is not None

    def test_resource_discovery_property(self):
        """Test resource_discovery property lazy initializes."""
        facade = LearningPathFacade()

        service = facade.resource_discovery

        assert service is not None
        assert facade._resource_discovery is not None

    def test_path_adaptation_property(self):
        """Test path_adaptation property lazy initializes."""
        facade = LearningPathFacade()

        service = facade.path_adaptation

        assert service is not None
        assert facade._path_adaptation is not None


class TestCreatePathForStudent:
    """Tests for create_path_for_student method."""

    @pytest.mark.asyncio
    async def test_create_path_success(
        self, mock_student_profile, mock_learning_path, mock_path_node
    ):
        """Test successful path creation."""
        # Create mock services
        mock_path_gen = MagicMock()
        mock_path_gen.generate_path = AsyncMock(
            return_value=PathGenerationResult(
                success=True,
                path=mock_learning_path,
                nodes=[mock_path_node],
                total_duration_minutes=150,
            )
        )

        facade = LearningPathFacade(path_generation=mock_path_gen)
        facade._profiles_cache["test-student-123"] = mock_student_profile

        result = await facade.create_path_for_student(
            student_id="test-student-123",
            subject="matematik",
            target_level=KnowledgeLevel.INTERMEDIATE,
        )

        assert result.success is True
        mock_path_gen.generate_path.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_path_caches_result(
        self, mock_student_profile, mock_learning_path, mock_path_node
    ):
        """Test path is cached after creation."""
        mock_path_gen = MagicMock()
        mock_path_gen.generate_path = AsyncMock(
            return_value=PathGenerationResult(
                success=True,
                path=mock_learning_path,
                nodes=[mock_path_node],
                total_duration_minutes=150,
            )
        )

        facade = LearningPathFacade(path_generation=mock_path_gen)
        facade._profiles_cache["test-student-123"] = mock_student_profile

        await facade.create_path_for_student(
            student_id="test-student-123",
            subject="matematik",
        )

        # Path should be cached
        assert "test-student-123" in facade._paths_cache


class TestSearchResources:
    """Tests for search_resources method."""

    @pytest.mark.asyncio
    async def test_search_resources_success(self, mock_resources):
        """Test successful resource search."""
        mock_discovery = MagicMock()
        mock_discovery.discover = AsyncMock(
            return_value=DiscoveryResult(
                resources=mock_resources,
                total_found=2,
                sources_searched=["YouTube", "Khan Academy"],
                errors={},
            )
        )

        facade = LearningPathFacade(resource_discovery=mock_discovery)

        resources = await facade.search_resources(
            query="türev",
            subject="matematik",
            limit=10,
        )

        assert len(resources) == 2
        assert resources[0].resource_id == "res-1"
        mock_discovery.discover.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_resources_empty(self):
        """Test search returns empty when no results."""
        mock_discovery = MagicMock()
        mock_discovery.discover = AsyncMock(
            return_value=DiscoveryResult(
                resources=[],
                total_found=0,
                sources_searched=["YouTube"],
                errors={},
            )
        )

        facade = LearningPathFacade(resource_discovery=mock_discovery)

        resources = await facade.search_resources(
            query="nonexistent topic",
            limit=10,
        )

        assert len(resources) == 0


class TestAdaptStudentPath:
    """Tests for adapt_student_path method."""

    @pytest.mark.asyncio
    async def test_adapt_path_success(self, mock_learning_path):
        """Test successful path adaptation."""
        mock_adaptation = MagicMock()
        mock_adaptation.adapt_path = AsyncMock(
            return_value=AdaptationResult(
                success=True,
                actions_taken=[
                    AdaptationAction(
                        type=AdaptationType.DIFFICULTY_ADJUSTMENT,
                        description="Zorluk seviyesi ayarlandı",
                    )
                ],
                message="Yol başarıyla uyarlandı",
            )
        )

        facade = LearningPathFacade(path_adaptation=mock_adaptation)
        facade._paths_cache["test-student-123"] = mock_learning_path

        performance = [
            PerformanceMetrics(
                topic="türev",
                quiz_score=90,
                completion_time_minutes=30,
                attempts=1,
            )
        ]

        result = await facade.adapt_student_path(
            student_id="test-student-123",
            performance=performance,
        )

        assert result.success is True
        assert len(result.actions_taken) == 1
        mock_adaptation.adapt_path.assert_called_once()


class TestGetStudentPath:
    """Tests for get_student_path method."""

    @pytest.mark.asyncio
    async def test_get_path_from_cache(self, mock_learning_path):
        """Test getting path from cache."""
        facade = LearningPathFacade()
        facade._paths_cache["test-student-123"] = mock_learning_path

        path = await facade.get_student_path("test-student-123")

        assert path is not None
        assert path.path_id == "path-123"

    @pytest.mark.asyncio
    async def test_get_path_not_found(self):
        """Test getting path when not in cache."""
        facade = LearningPathFacade()

        path = await facade.get_student_path("nonexistent-student")

        assert path is None


class TestFacadeFactory:
    """Tests for facade factory function."""

    def test_get_learning_path_facade_singleton(self):
        """Test facade factory returns consistent instance."""
        # Clear any cached instance
        import agents.learning_path.facade as facade_module
        if hasattr(facade_module, '_facade_instance'):
            facade_module._facade_instance = None

        facade1 = get_learning_path_facade()
        facade2 = get_learning_path_facade()

        # Should be the same instance (singleton pattern)
        assert facade1 is facade2
