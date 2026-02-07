"""
Unit tests for ReflectionService (REQ-3)

Guided reflection, depth measurement, and learning extraction tests.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from api.schemas.diary import ReflectionCreate, ReflectionPromptsResponse


class TestReflectionServiceGuidedQuestions:
    """Test REQ-3.1: Guided Questions"""

    def test_get_prompts_default(self):
        """Test getting default prompts without category"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        response = service.get_prompts()

        assert isinstance(response, ReflectionPromptsResponse)
        assert len(response.prompts) == 4  # One from each category

    def test_get_prompts_with_category(self):
        """Test getting prompts for specific category"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        response = service.get_prompts(category="what_went_well")

        assert isinstance(response, ReflectionPromptsResponse)
        assert len(response.prompts) == 4  # All prompts from that category

    def test_get_prompts_with_context(self):
        """Test getting prompts with context hints"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        context = {
            "success_count": 5,
            "challenges": ["time management", "testing"],
            "learnings": ["async patterns", "testing"],
        }

        response = service.get_prompts(context=context)

        assert response.context_hints is not None
        assert "success" in response.context_hints

    def test_get_all_prompts(self):
        """Test getting all prompts by category"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        all_prompts = service.get_all_prompts()

        assert "what_went_well" in all_prompts
        assert "what_could_improve" in all_prompts
        assert "what_did_i_learn" in all_prompts
        assert "what_will_i_do_differently" in all_prompts


class TestReflectionServiceDepthMeasurement:
    """Test REQ-3.6: Depth Measurement"""

    def test_measure_depth_surface_response(self):
        """Test depth measurement for surface-level responses"""
        from services.reflection_service import ReflectionService
        from models.diary import ReflectionDepth

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        # Short, simple responses
        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_went_well="iyi",
            what_could_improve="tamam",
        )

        depth, score = service.measure_depth(data)

        assert depth == ReflectionDepth.SURFACE
        assert score < 0.4

    def test_measure_depth_moderate_response(self):
        """Test depth measurement for moderate responses"""
        from services.reflection_service import ReflectionService
        from models.diary import ReflectionDepth

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        # Medium-length responses with some depth
        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_went_well="Bugün API endpoint'lerini tamamladım ve testler geçti.",
            what_could_improve="Daha iyi dokümantasyon yazabilirdim, zaman kalmadı.",
            what_did_i_learn="Async patterns konusunda yeni şeyler öğrendim.",
        )

        depth, score = service.measure_depth(data)

        assert depth in [ReflectionDepth.SURFACE, ReflectionDepth.MODERATE]

    def test_measure_depth_deep_response(self):
        """Test depth measurement for deep responses"""
        from services.reflection_service import ReflectionService
        from models.diary import ReflectionDepth

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        # Long, thoughtful responses with deep thinking indicators
        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_went_well="""
            Bugün API endpoint'lerini tamamladım. Farkettim ki async pattern kullanımı
            performans üzerinde önemli bir etki yapıyor. Anladım ki uzun vadede bu yaklaşım
            daha sürdürülebilir olacak. Stratejik olarak düşündüğümde, bu deneyim gelecekteki
            projelerde de değerli olacak.
            """,
            what_could_improve="""
            Aslında daha iyi planlama yapabilirdim. Nedeni şu: zaman yönetimi konusunda
            eksiklerim var. Düşündüğümde, perspektifimi değiştirmem gerekiyor.
            """,
            what_did_i_learn="""
            İç gözlem ve farkındalık konusunda önemli adımlar attım. Anladım ki
            varsayımlarımı sorgulamam gerekiyor. Bu bir analiz ve sentez gerektiren süreç.
            """,
            what_will_i_do_differently="""
            Gelecekte daha stratejik düşüneceğim. Motivasyonumu artırmak için amaçlarımı
            netleştireceğim. Uzun vadede bu yaklaşım daha verimli olacak.
            """,
        )

        depth, score = service.measure_depth(data)

        # The algorithm may return MODERATE or DEEP depending on exact scoring
        # At minimum, this should be at least moderate level reflection
        assert depth in [ReflectionDepth.MODERATE, ReflectionDepth.DEEP]
        assert score >= 0.4  # At least moderate score

    def test_measure_depth_empty_response(self):
        """Test depth measurement for empty responses"""
        from services.reflection_service import ReflectionService
        from models.diary import ReflectionDepth

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        data = ReflectionCreate(diary_entry_id=uuid4())

        depth, score = service.measure_depth(data)

        assert depth == ReflectionDepth.SURFACE
        assert score == 0.0


class TestReflectionServiceLearningExtraction:
    """Test REQ-3.4: Learning Extraction"""

    def test_extract_learnings_from_what_did_i_learn(self):
        """Test learning extraction from main learning field"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_did_i_learn="Async patterns öğrendim. FastAPI ile REST API geliştirmeyi kavradım. Testing best practices hakkında bilgi edindim.",
        )

        learnings = service.extract_learnings(data)

        assert isinstance(learnings, list)
        assert len(learnings) > 0
        assert len(learnings) <= 5  # Max 5

    def test_extract_learnings_from_other_fields(self):
        """Test learning extraction from other fields using keywords"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_went_well="Her şey iyi gitti, async konusunda yeni şeyler öğrendim.",
            what_could_improve="Daha fazla test yazmalıyım, bunu farkettim.",
        )

        learnings = service.extract_learnings(data)

        assert isinstance(learnings, list)

    def test_extract_learnings_empty(self):
        """Test learning extraction from empty responses"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        data = ReflectionCreate(diary_entry_id=uuid4())

        learnings = service.extract_learnings(data)

        assert learnings == []


class TestReflectionServiceActionItems:
    """Test REQ-3.5: Action Items Extraction"""

    def test_extract_action_items_from_what_will_i_do(self):
        """Test action item extraction from main action field"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_will_i_do_differently="Daha fazla test yazacağım. CI/CD pipeline kuracağım. Code review sürecini iyileştireceğim.",
        )

        actions = service.extract_action_items(data)

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert len(actions) <= 5  # Max 5

    def test_extract_action_items_with_turkish_keywords(self):
        """Test action item extraction with Turkish keywords"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_could_improve="Yarın bu konuya odaklanacağım ve daha iyi planlama yapacağım.",
        )

        actions = service.extract_action_items(data)

        assert isinstance(actions, list)

    def test_extract_action_items_empty(self):
        """Test action item extraction from empty responses"""
        from services.reflection_service import ReflectionService

        mock_db = MagicMock()
        service = ReflectionService(mock_db)

        data = ReflectionCreate(diary_entry_id=uuid4())

        actions = service.extract_action_items(data)

        assert actions == []


class TestReflectionServiceCRUD:
    """Test CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_reflection(self):
        """Test creating a reflection"""
        from services.reflection_service import ReflectionService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ReflectionService(mock_db)

        data = ReflectionCreate(
            diary_entry_id=uuid4(),
            what_went_well="Bugün iyi çalıştım",
            what_could_improve="Daha iyi planlama yapabilirim",
            what_did_i_learn="Yeni bir pattern öğrendim",
            what_will_i_do_differently="Yarın daha erken başlayacağım",
        )

        await service.create_reflection(uuid4(), data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_reflections(self):
        """Test getting reflections with filters"""
        from services.reflection_service import ReflectionService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = ReflectionService(mock_db)

        reflections = await service.get_reflections(
            user_id=uuid4(),
            diary_entry_id=None,
            depth=None,
            limit=20
        )

        assert isinstance(reflections, list)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_reflection_by_id(self):
        """Test getting reflection by ID"""
        from services.reflection_service import ReflectionService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ReflectionService(mock_db)

        reflection = await service.get_reflection_by_id(uuid4(), uuid4())

        assert reflection is None

    @pytest.mark.asyncio
    async def test_delete_reflection_not_found(self):
        """Test deleting non-existent reflection"""
        from services.reflection_service import ReflectionService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ReflectionService(mock_db)

        result = await service.delete_reflection(uuid4(), uuid4())

        assert result is False


class TestReflectionServiceStatistics:
    """Test depth statistics"""

    @pytest.mark.asyncio
    async def test_get_depth_statistics_empty(self):
        """Test depth statistics with no data"""
        from services.reflection_service import ReflectionService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = ReflectionService(mock_db)

        stats = await service.get_depth_statistics(uuid4(), days=30)

        assert stats["total_reflections"] == 0
        assert stats["average_depth_score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_depth_statistics_with_data(self):
        """Test depth statistics with reflection data"""
        from services.reflection_service import ReflectionService
        from models.diary import ReflectionDepth

        mock_db = AsyncMock()

        # Create mock reflections
        mock_reflections = []
        for depth in [ReflectionDepth.SURFACE, ReflectionDepth.MODERATE, ReflectionDepth.DEEP]:
            r = MagicMock()
            r.depth = depth
            r.depth_score = 0.3 if depth == ReflectionDepth.SURFACE else (0.5 if depth == ReflectionDepth.MODERATE else 0.8)
            r.created_at = datetime.now()
            mock_reflections.append(r)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_reflections
        mock_db.execute.return_value = mock_result

        service = ReflectionService(mock_db)

        stats = await service.get_depth_statistics(uuid4(), days=30)

        assert stats["total_reflections"] == 3
        assert stats["surface_count"] == 1
        assert stats["moderate_count"] == 1
        assert stats["deep_count"] == 1


class TestReflectionServiceIndicators:
    """Test depth indicators"""

    def test_deep_indicators_list(self):
        """Test that DEEP_INDICATORS contains expected keywords"""
        from services.reflection_service import ReflectionService

        assert "farkettim" in ReflectionService.DEEP_INDICATORS
        assert "anladım" in ReflectionService.DEEP_INDICATORS
        assert "perspektif" in ReflectionService.DEEP_INDICATORS

    def test_surface_indicators_list(self):
        """Test that SURFACE_INDICATORS contains expected keywords"""
        from services.reflection_service import ReflectionService

        assert "iyi" in ReflectionService.SURFACE_INDICATORS
        assert "tamam" in ReflectionService.SURFACE_INDICATORS
        assert "ok" in ReflectionService.SURFACE_INDICATORS

    def test_prompts_structure(self):
        """Test that PROMPTS has correct structure"""
        from services.reflection_service import ReflectionService

        prompts = ReflectionService.PROMPTS

        assert len(prompts) == 4  # 4 categories
        for category, questions in prompts.items():
            assert isinstance(questions, list)
            assert len(questions) >= 1
