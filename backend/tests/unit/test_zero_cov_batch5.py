"""
Zero-coverage batch 5: Unit tests for 5 low-coverage backend files.

Files covered:
1. services/khan_academy_client.py   (28%)
2. services/content_recommendation_service.py  (28%)
3. core/passwordless_auth.py  (40%)
4. core/embedding_cache.py    (37%)
5. services/video_solution_service.py  (26%)
"""

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Ensure backend root is on sys.path
# ---------------------------------------------------------------------------
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ---------------------------------------------------------------------------
# Stubs for heavy / unavailable optional dependencies
# (install before importing target modules)
# ---------------------------------------------------------------------------

# chromadb stub
_chromadb_stub = MagicMock()
_chromadb_settings_stub = MagicMock()
sys.modules.setdefault("chromadb", _chromadb_stub)
sys.modules.setdefault("chromadb.config", _chromadb_settings_stub)

# sentence_transformers stub
_st_stub = MagicMock()
sys.modules.setdefault("sentence_transformers", _st_stub)

# aiofiles stub
_aiofiles_stub = MagicMock()
sys.modules.setdefault("aiofiles", _aiofiles_stub)

# ---------------------------------------------------------------------------
# Now import the modules under test
# ---------------------------------------------------------------------------
from core.embedding_cache import (  # noqa: E402
    EmbeddingCache,
    EmbeddingCacheConfig,
    EmbeddingEntry,
    EmbeddingIndex,
    LRUCache,
    QuantizedEmbedding,
    SearchResult,
    calculate_quantization_error,
    dequantize_batch,
    dequantize_embedding,
    get_embedding_cache,
    get_quantization_stats,
    quantize_batch,
    quantize_embedding,
)
from core.passwordless_auth import (  # noqa: E402
    InMemoryTokenStorage,
    MagicLinkToken,
    PasswordlessAuthEvent,
    PasswordlessAuthService,
    RateLimitEntry,
    WebAuthnService,
    get_passwordless_auth_service,
    get_webauthn_service,
)
from services.content_recommendation_service import (  # noqa: E402
    INTERACTION_WEIGHTS,
    ContentRecommendationService,
    InteractionType,
    RecommendationResult,
    UserInteraction,
    get_recommendation_service,
)
from services.khan_academy_client import (  # noqa: E402
    KhanAcademyClient,
    KhanCertificate,
    KhanContentMetadata,
    KhanContentType,
    KhanSubject,
    KhanUserProgress,
    MockKhanAcademyClient,
    get_khan_client,
)
from services.video_solution_service import (  # noqa: E402
    VideoConfig,
    VideoProcessor,
    VideoValidator,
)

# ===========================================================================
# 1. KhanAcademyClient Tests
# ===========================================================================


class TestKhanContentType:
    def test_enum_values(self):
        assert KhanContentType.VIDEO == "video"
        assert KhanContentType.EXERCISE == "exercise"
        assert KhanContentType.ARTICLE == "article"
        assert KhanContentType.PROJECT == "project"


class TestKhanSubject:
    def test_enum_values(self):
        assert KhanSubject.MATH == "math"
        assert KhanSubject.SCIENCE == "science"
        assert KhanSubject.COMPUTING == "computing"


class TestKhanContentMetadata:
    def test_defaults(self):
        meta = KhanContentMetadata(
            content_id="c1",
            title="Test",
            content_type=KhanContentType.VIDEO,
            subject=KhanSubject.MATH,
        )
        assert meta.language == "tr"
        assert meta.has_turkish is True
        assert meta.description is None

    def test_full_video_metadata(self):
        meta = KhanContentMetadata(
            content_id="vid1",
            title="Video Title",
            content_type=KhanContentType.VIDEO,
            subject=KhanSubject.MATH,
            video_url="https://cdn.khanacademy.org/video.mp4",
            duration_seconds=300,
            thumbnail_url="https://cdn.khanacademy.org/thumb.jpg",
            difficulty_level="intermediate",
        )
        assert meta.video_url is not None
        assert meta.duration_seconds == 300
        assert meta.difficulty_level == "intermediate"


class TestKhanAcademyClientInit:
    def test_init_stores_credentials(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        assert client.client_id == "cid"
        assert client.client_secret == "csec"
        assert client.access_token is None
        assert client.token_expires_at is None

    def test_get_headers_without_token(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        headers = client._get_headers()
        assert "Accept" in headers
        assert headers["User-Agent"] == "Kiro-Platform/1.0"
        assert "Authorization" not in headers

    def test_get_headers_with_token(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        client.access_token = "my_token"
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer my_token"

    def test_get_authorization_url_generates_state(self):
        client = KhanAcademyClient(client_id="my_client_id", client_secret="secret")
        url = client.get_authorization_url(redirect_uri="https://app/callback")
        assert "my_client_id" in url
        assert "state=" in url
        assert "response_type=code" in url

    def test_get_authorization_url_uses_provided_state(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        url = client.get_authorization_url(
            redirect_uri="https://app/callback", state="my_state_123"
        )
        assert "my_state_123" in url


class TestKhanAcademyClientAsync:
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "access_token": "at_abc",
            "refresh_token": "rt_xyz",
            "expires_in": 3600,
        }

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.exchange_code_for_token(
                "auth_code", "https://app/callback"
            )

        assert result["access_token"] == "at_abc"
        assert result["refresh_token"] == "rt_xyz"
        assert "expires_at" in result
        assert client.access_token == "at_abc"

    @pytest.mark.asyncio
    async def test_refresh_access_token_no_refresh_token_raises(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        with pytest.raises(Exception, match="No refresh token"):
            await client.refresh_access_token()

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        client.refresh_token = "old_rt"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_at",
            "refresh_token": "new_rt",
            "expires_in": 3600,
        }

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.refresh_access_token()

        assert result["access_token"] == "new_at"
        assert client.access_token == "new_at"
        assert client.refresh_token == "new_rt"

    @pytest.mark.asyncio
    async def test_ensure_valid_token_raises_when_no_token(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        with pytest.raises(Exception, match="Not authenticated"):
            await client._ensure_valid_token()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_refreshes_when_expiring(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        client.access_token = "old_at"
        client.refresh_token = "rt"
        # Token expires in 1 minute — within the 5-min buffer
        client.token_expires_at = datetime.now() + timedelta(minutes=1)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "access_token": "refreshed_at",
            "expires_in": 3600,
        }

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            await client._ensure_valid_token()

        assert client.access_token == "refreshed_at"

    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_refresh_needed(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        client.access_token = "valid_at"
        # Token expires in 1 hour — no refresh needed
        client.token_expires_at = datetime.now() + timedelta(hours=1)
        # Should complete without error or refresh
        await client._ensure_valid_token()

    @pytest.mark.asyncio
    async def test_get_turkish_content_success(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        client.access_token = "tok"
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "children": [
                {
                    "id": "v1",
                    "kind": "video",
                    "translated_languages": ["tr"],
                    "title": "Math Video",
                    "subject": "math",
                },
                {
                    "id": "v2",
                    "kind": "exercise",
                    "translated_languages": ["tr"],
                    "title": "Math Exercise",
                    "subject": "math",
                },
                # item with no Turkish — should be skipped
                {
                    "id": "v3",
                    "kind": "video",
                    "translated_languages": ["en"],
                    "title": "English Only",
                    "subject": "math",
                },
            ]
        }

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await client.get_turkish_content()

        assert len(results) == 2
        assert all(r.has_turkish for r in results)

    @pytest.mark.asyncio
    async def test_update_user_progress_success(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        client.access_token = "tok"
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.update_user_progress(
                "user1", "content1", {"done": True}
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_progress_failure_returns_false(self):
        import httpx

        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        client.access_token = "tok"
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        mock_request = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "forbidden"

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "403", request=mock_request, response=mock_resp
            )
            result = await client.update_user_progress("user1", "c1", {})

        assert result is False

    @pytest.mark.asyncio
    async def test_close_calls_aclose(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        with patch.object(
            client.client, "aclose", new_callable=AsyncMock
        ) as mock_aclose:
            await client.close()
            mock_aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        with patch.object(client.client, "aclose", new_callable=AsyncMock):
            async with client as c:
                assert c is client


class TestKhanAcademyClientParsing:
    def test_parse_content_item_video(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        item = {
            "id": "vid1",
            "kind": "video",
            "translated_languages": ["tr"],
            "title": "Math Video",
            "subject": "math",
            "duration": 600,
            "image_url": "https://thumb.jpg",
        }
        result = client._parse_content_item(item)
        assert result is not None
        assert result.content_type == KhanContentType.VIDEO
        assert result.duration_seconds == 600
        assert result.has_turkish is True

    def test_parse_content_item_exercise(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        item = {
            "id": "ex1",
            "kind": "exercise",
            "translated_languages": ["tr"],
            "title": "Algebra Exercise",
            "subject": "math",
            "total_problems": 10,
        }
        result = client._parse_content_item(item)
        assert result is not None
        assert result.content_type == KhanContentType.EXERCISE
        assert result.problem_count == 10

    def test_parse_content_item_unknown_kind_returns_none(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        item = {"id": "x", "kind": "quiz", "translated_languages": ["tr"]}
        result = client._parse_content_item(item)
        assert result is None

    def test_parse_content_item_no_turkish_returns_none(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        item = {
            "id": "vid2",
            "kind": "video",
            "translated_languages": ["en"],
            "title": "English Video",
            "subject": "math",
        }
        result = client._parse_content_item(item)
        assert result is None

    def test_parse_content_item_with_date(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        item = {
            "id": "vid3",
            "kind": "article",
            "translated_languages": ["tr"],
            "title": "Article",
            "subject": "math",
            "date_added": "2024-01-15T10:00:00",
        }
        result = client._parse_content_item(item)
        assert result is not None
        assert result.created_at is not None

    def test_parse_progress_item(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        item = {
            "id": "content1",
            "kind": "video",
            "seconds_watched": 120,
            "completed": False,
            "total_done": 5,
            "total_correct": 3,
            "points_earned": 50,
            "badges": ["badge_a"],
        }
        prog = client._parse_progress_item("user1", item)
        assert prog.user_id == "user1"
        assert prog.content_id == "content1"
        assert prog.video_seconds_watched == 120
        assert prog.energy_points == 50

    def test_parse_badge(self):
        client = KhanAcademyClient(client_id="cid", client_secret="csec")
        badge = {
            "badge_name": "math-master",
            "name": "Math Master",
            "badge_category": "mastery",
            "description": "Great at math",
            "icon_src": "https://icon.png",
            "date_earned": "2024-03-01T12:00:00",
        }
        cert = client._parse_badge("user42", badge)
        assert cert.user_id == "user42"
        assert cert.badge_name == "Math Master"
        assert cert.badge_category == "mastery"
        assert cert.verification_url is not None


class TestMockKhanAcademyClient:
    @pytest.mark.asyncio
    async def test_get_turkish_content_returns_mock_items(self):
        mock_client = MockKhanAcademyClient()
        results = await mock_client.get_turkish_content()
        assert len(results) == 10
        assert all(isinstance(r, KhanContentMetadata) for r in results)
        assert all(r.has_turkish for r in results)

    @pytest.mark.asyncio
    async def test_get_turkish_content_respects_limit(self):
        mock_client = MockKhanAcademyClient()
        results = await mock_client.get_turkish_content(limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_user_progress_returns_5_items(self):
        mock_client = MockKhanAcademyClient()
        progress = await mock_client.get_user_progress("user1")
        assert len(progress) == 5
        assert all(isinstance(p, KhanUserProgress) for p in progress)

    @pytest.mark.asyncio
    async def test_get_user_badges_returns_3_items(self):
        mock_client = MockKhanAcademyClient()
        badges = await mock_client.get_user_badges("user1")
        assert len(badges) == 3
        assert all(isinstance(b, KhanCertificate) for b in badges)


class TestGetKhanClient:
    def test_get_khan_client_mock_mode(self):
        client = get_khan_client(use_mock=True)
        assert isinstance(client, MockKhanAcademyClient)

    def test_get_khan_client_no_credentials_returns_mock(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("KHAN_ACADEMY_CLIENT_ID", None)
            os.environ.pop("KHAN_ACADEMY_CLIENT_SECRET", None)
            client = get_khan_client(use_mock=False)
        assert isinstance(client, MockKhanAcademyClient)

    def test_get_khan_client_with_credentials(self):
        with patch.dict(
            os.environ,
            {
                "KHAN_ACADEMY_CLIENT_ID": "cid123",
                "KHAN_ACADEMY_CLIENT_SECRET": "csec456",
            },
        ):
            client = get_khan_client(use_mock=False)
        assert isinstance(client, KhanAcademyClient)
        assert client.client_id == "cid123"


# ===========================================================================
# 2. ContentRecommendationService Tests
# ===========================================================================


class TestInteractionWeights:
    def test_weights_defined_for_all_types(self):
        for itype in InteractionType:
            assert itype in INTERACTION_WEIGHTS

    def test_positive_weights_for_positive_interactions(self):
        assert INTERACTION_WEIGHTS[InteractionType.LIKE] > 0
        assert INTERACTION_WEIGHTS[InteractionType.COMPLETE] > 0
        assert INTERACTION_WEIGHTS[InteractionType.BOOKMARK] > 0

    def test_negative_weights_for_negative_interactions(self):
        assert INTERACTION_WEIGHTS[InteractionType.SKIP] < 0
        assert INTERACTION_WEIGHTS[InteractionType.DISLIKE] < 0


class TestUserInteraction:
    def test_create_interaction(self):
        interaction = UserInteraction(
            user_id="u1",
            content_id="c1",
            interaction_type=InteractionType.LIKE,
        )
        assert interaction.user_id == "u1"
        assert interaction.content_id == "c1"
        assert interaction.duration_seconds == 0
        assert isinstance(interaction.timestamp, datetime)


class TestContentRecommendationServiceInit:
    def test_init_defaults(self):
        svc = ContentRecommendationService()
        assert svc._initialized is False
        assert svc._user_profiles == {}
        assert svc._interactions == []
        assert svc._click_tracking == {}

    def test_cold_start_threshold_is_5(self):
        svc = ContentRecommendationService()
        assert svc.COLD_START_THRESHOLD == 5

    def test_weights_sum_to_one(self):
        svc = ContentRecommendationService()
        total = svc.CONTENT_WEIGHT + svc.COLLABORATIVE_WEIGHT + svc.POPULARITY_WEIGHT
        assert abs(total - 1.0) < 1e-9


class TestCtrTracking:
    def test_view_increments_impressions(self):
        svc = ContentRecommendationService()
        interaction = UserInteraction(
            user_id="u1",
            content_id="c1",
            interaction_type=InteractionType.VIEW,
        )
        svc._update_ctr_tracking(interaction)
        assert svc._click_tracking["c1"]["impressions"] == 1
        assert svc._click_tracking["c1"]["clicks"] == 0

    def test_like_increments_clicks(self):
        svc = ContentRecommendationService()
        interaction = UserInteraction(
            user_id="u1",
            content_id="c1",
            interaction_type=InteractionType.LIKE,
        )
        svc._update_ctr_tracking(interaction)
        assert svc._click_tracking["c1"]["clicks"] == 1

    def test_complete_increments_clicks(self):
        svc = ContentRecommendationService()
        interaction = UserInteraction(
            user_id="u1",
            content_id="c1",
            interaction_type=InteractionType.COMPLETE,
        )
        svc._update_ctr_tracking(interaction)
        assert svc._click_tracking["c1"]["clicks"] == 1

    def test_skip_does_not_increment_clicks_or_impressions(self):
        svc = ContentRecommendationService()
        interaction = UserInteraction(
            user_id="u1",
            content_id="c1",
            interaction_type=InteractionType.SKIP,
        )
        svc._update_ctr_tracking(interaction)
        assert svc._click_tracking["c1"]["clicks"] == 0
        assert svc._click_tracking["c1"]["impressions"] == 0


class TestCollaborativeScore:
    def test_no_interactions_returns_zero(self):
        svc = ContentRecommendationService()
        score = svc._get_collaborative_score("c1", "u1")
        assert score == 0.0

    def test_other_user_like_contributes_score(self):
        svc = ContentRecommendationService()
        svc._interactions.append(
            UserInteraction(
                user_id="u2", content_id="c1", interaction_type=InteractionType.LIKE
            )
        )
        score = svc._get_collaborative_score("c1", "u1")
        assert score > 0.0

    def test_self_interaction_ignored(self):
        svc = ContentRecommendationService()
        svc._interactions.append(
            UserInteraction(
                user_id="u1", content_id="c1", interaction_type=InteractionType.LIKE
            )
        )
        score = svc._get_collaborative_score("c1", "u1")
        assert score == 0.0

    def test_capped_at_one(self):
        svc = ContentRecommendationService()
        for i in range(20):
            svc._interactions.append(
                UserInteraction(
                    user_id=f"u{i + 2}",
                    content_id="c1",
                    interaction_type=InteractionType.COMPLETE,
                )
            )
        score = svc._get_collaborative_score("c1", "u1")
        assert score == 1.0


class TestPopularityScore:
    def test_no_tracking_returns_zero(self):
        svc = ContentRecommendationService()
        score = svc._get_popularity_score("unknown_content")
        assert score == 0.0

    def test_clicks_increase_score(self):
        svc = ContentRecommendationService()
        svc._click_tracking["c1"] = {"clicks": 5, "impressions": 10}
        score = svc._get_popularity_score("c1")
        assert score == 0.5

    def test_ctr_capped_at_one(self):
        svc = ContentRecommendationService()
        svc._click_tracking["c1"] = {"clicks": 100, "impressions": 10}
        score = svc._get_popularity_score("c1")
        assert score == 1.0


class TestEnsureDiversity:
    def _make_rec(self, content_id, subject, score=0.5):
        return RecommendationResult(
            content_id=content_id,
            content_preview="preview",
            score=score,
            metadata={"subject": subject},
            recommendation_type="hybrid",
        )

    def test_returns_all_when_under_limit(self):
        svc = ContentRecommendationService()
        recs = [self._make_rec(f"c{i}", "math") for i in range(3)]
        result = svc._ensure_diversity(recs, limit=5)
        assert len(result) == 3

    def test_round_robin_across_subjects(self):
        svc = ContentRecommendationService()
        recs = [
            self._make_rec("c1", "math"),
            self._make_rec("c2", "math"),
            self._make_rec("c3", "physics"),
            self._make_rec("c4", "chemistry"),
        ]
        result = svc._ensure_diversity(recs, limit=3)
        subjects = {r.metadata["subject"] for r in result}
        assert len(subjects) >= 2

    def test_does_not_exceed_limit(self):
        svc = ContentRecommendationService()
        recs = [self._make_rec(f"c{i}", f"subject_{i % 4}") for i in range(20)]
        result = svc._ensure_diversity(recs, limit=5)
        assert len(result) == 5


class TestCalculateDiversityScore:
    def _make_rec(self, subject):
        return RecommendationResult(
            content_id="c1",
            content_preview="p",
            score=1.0,
            metadata={"subject": subject},
            recommendation_type="hybrid",
        )

    def test_empty_returns_zero(self):
        svc = ContentRecommendationService()
        assert svc._calculate_diversity_score([]) == 0.0

    def test_single_subject_low_diversity(self):
        svc = ContentRecommendationService()
        recs = [self._make_rec("math")] * 5
        score = svc._calculate_diversity_score(recs)
        assert score == round(1 / 5, 4)

    def test_all_different_subjects_high_diversity(self):
        svc = ContentRecommendationService()
        subjects = ["math", "physics", "chemistry", "biology"]
        recs = [self._make_rec(s) for s in subjects]
        score = svc._calculate_diversity_score(recs)
        assert score >= 0.9  # bonus applied (>= DIVERSITY_MIN_TOPICS)

    def test_bonus_applied_when_min_topics_met(self):
        svc = ContentRecommendationService()
        recs = [self._make_rec(f"s{i}") for i in range(svc.DIVERSITY_MIN_TOPICS)]
        score = svc._calculate_diversity_score(recs)
        assert score == 1.0  # 1.0 * 1.2 capped at 1.0


class TestCtrReport:
    @pytest.mark.asyncio
    async def test_empty_report(self):
        svc = ContentRecommendationService()
        report = await svc.get_ctr_report()
        assert report["total_content"] == 0
        assert report["average_ctr"] == 0.0

    @pytest.mark.asyncio
    async def test_report_with_data(self):
        svc = ContentRecommendationService()
        svc._click_tracking["c1"] = {"clicks": 10, "impressions": 100}
        svc._click_tracking["c2"] = {"clicks": 5, "impressions": 50}
        report = await svc.get_ctr_report()
        assert report["total_content"] == 2
        assert report["average_ctr"] > 0
        assert len(report["top_performing"]) <= 5


class TestGetRecommendationService:
    def test_returns_singleton(self):
        import services.content_recommendation_service as mod

        mod._recommendation_service = None
        svc1 = get_recommendation_service()
        svc2 = get_recommendation_service()
        assert svc1 is svc2
        mod._recommendation_service = None  # cleanup


class TestRecordInteraction:
    @pytest.mark.asyncio
    async def test_record_interaction_stores_in_list(self):
        svc = ContentRecommendationService()
        # Prevent real initialization
        svc._initialized = False

        async def _fake_init():
            return False

        svc.initialize = _fake_init

        interaction = UserInteraction(
            user_id="u1",
            content_id="c1",
            interaction_type=InteractionType.VIEW,
        )
        result = await svc.record_interaction(interaction)
        assert result is True
        assert len(svc._interactions) == 1

    @pytest.mark.asyncio
    async def test_record_interaction_updates_ctr(self):
        svc = ContentRecommendationService()
        svc._initialized = False

        async def _fake_init():
            return False

        svc.initialize = _fake_init

        interaction = UserInteraction(
            user_id="u1",
            content_id="c2",
            interaction_type=InteractionType.VIEW,
        )
        await svc.record_interaction(interaction)
        assert "c2" in svc._click_tracking
        assert svc._click_tracking["c2"]["impressions"] == 1


# ===========================================================================
# 3. PasswordlessAuthService Tests
# ===========================================================================


class TestInMemoryTokenStorage:
    @pytest.mark.asyncio
    async def test_store_and_get(self):
        storage = InMemoryTokenStorage()
        await storage.store("key1", {"value": 42}, expires_in=3600)
        result = await storage.get("key1")
        assert result == {"value": 42}

    @pytest.mark.asyncio
    async def test_get_nonexistent_key_returns_none(self):
        storage = InMemoryTokenStorage()
        result = await storage.get("no_such_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_expired_key_returns_none(self):
        storage = InMemoryTokenStorage()
        await storage.store("exp_key", "some_value", expires_in=0)
        import time

        time.sleep(0.01)  # ensure expiry
        # Manually expire it
        storage._expiry["exp_key"] = datetime.now(UTC) - timedelta(seconds=1)
        result = await storage.get("exp_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_key(self):
        storage = InMemoryTokenStorage()
        await storage.store("del_key", "v", expires_in=3600)
        await storage.delete("del_key")
        result = await storage.get("del_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists_true(self):
        storage = InMemoryTokenStorage()
        await storage.store("ex_key", "v", expires_in=3600)
        assert await storage.exists("ex_key") is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        storage = InMemoryTokenStorage()
        assert await storage.exists("missing") is False

    def test_cleanup_expired_removes_stale(self):
        storage = InMemoryTokenStorage()
        storage._storage["stale"] = "data"
        storage._expiry["stale"] = datetime.now(UTC) - timedelta(seconds=1)
        storage._storage["fresh"] = "data2"
        storage._expiry["fresh"] = datetime.now(UTC) + timedelta(hours=1)

        count = storage.cleanup_expired()
        assert count == 1
        assert "stale" not in storage._storage
        assert "fresh" in storage._storage


class TestMagicLinkToken:
    def test_fields(self):
        now = datetime.now(UTC)
        token = MagicLinkToken(
            token="tok123",
            email="user@example.com",
            created_at=now,
            expires_at=now + timedelta(minutes=15),
        )
        assert token.is_used is False
        assert token.ip_address is None


class TestPasswordlessAuthServiceBasics:
    def test_init_defaults(self):
        svc = PasswordlessAuthService()
        assert svc.MAGIC_LINK_EXPIRE_MINUTES == 15
        assert svc.MAX_MAGIC_LINK_ATTEMPTS == 5
        assert svc._audit_logs == []
        assert svc._rate_limits == {}

    def test_supports_fallback_to_password_always_true(self):
        svc = PasswordlessAuthService()
        assert svc.supports_fallback_to_password() is True

    @pytest.mark.asyncio
    async def test_generate_magic_link_invalid_email(self):
        svc = PasswordlessAuthService()
        result = await svc.generate_magic_link_token("not-an-email")
        assert result.success is False
        assert result.error_code == "INVALID_EMAIL"

    @pytest.mark.asyncio
    async def test_generate_magic_link_empty_email(self):
        svc = PasswordlessAuthService()
        result = await svc.generate_magic_link_token("")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_generate_magic_link_success(self):
        svc = PasswordlessAuthService()
        result = await svc.generate_magic_link_token(
            "user@example.com", ip_address="127.0.0.1"
        )
        assert result.success is True
        assert result.token is not None
        assert result.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_generate_magic_link_normalizes_email(self):
        svc = PasswordlessAuthService()
        result = await svc.generate_magic_link_token("User@EXAMPLE.COM")
        assert result.email == "user@example.com"


class TestPasswordlessVerification:
    @pytest.mark.asyncio
    async def test_verify_empty_token_fails(self):
        svc = PasswordlessAuthService()
        result = await svc.verify_magic_link_token("")
        assert result.valid is False
        assert result.error_code == "EMPTY_TOKEN"

    @pytest.mark.asyncio
    async def test_verify_nonexistent_token_fails(self):
        svc = PasswordlessAuthService()
        result = await svc.verify_magic_link_token("nonexistent_token_abc")
        assert result.valid is False
        assert result.error_code == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_verify_valid_token_succeeds(self):
        svc = PasswordlessAuthService()
        gen_result = await svc.generate_magic_link_token("user@example.com")
        assert gen_result.success is True

        verify_result = await svc.verify_magic_link_token(gen_result.token)
        assert verify_result.valid is True
        assert verify_result.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_verify_token_only_once(self):
        svc = PasswordlessAuthService()
        gen_result = await svc.generate_magic_link_token("once@example.com")
        token = gen_result.token

        # First verification succeeds
        first = await svc.verify_magic_link_token(token)
        assert first.valid is True

        # Second verification fails (token deleted)
        second = await svc.verify_magic_link_token(token)
        assert second.valid is False

    @pytest.mark.asyncio
    async def test_verify_expired_token(self):
        svc = PasswordlessAuthService()
        gen_result = await svc.generate_magic_link_token("exp@example.com")
        token = gen_result.token

        # Manually expire the token
        token_key = f"magic_link:token:{token}"
        token_data = await svc._storage.get(token_key)
        token_data.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        # Re-store with the expired time
        await svc._storage.store(token_key, token_data, expires_in=3600)

        result = await svc.verify_magic_link_token(token)
        assert result.valid is False
        assert result.error_code == "TOKEN_EXPIRED"


class TestRateLimiting:
    def test_first_attempt_allowed(self):
        svc = PasswordlessAuthService()
        allowed, retry = svc._check_rate_limit("test@example.com")
        assert allowed is True
        assert retry is None

    def test_exceeding_max_attempts_blocks(self):
        svc = PasswordlessAuthService()
        email = "spam@example.com"
        # Exhaust attempts
        for _ in range(svc.MAX_MAGIC_LINK_ATTEMPTS + 1):
            svc._check_rate_limit(email)

        allowed, retry = svc._check_rate_limit(email)
        assert allowed is False
        assert retry is not None
        assert retry > 0

    def test_reset_rate_limit(self):
        svc = PasswordlessAuthService()
        email = "reset@example.com"
        for _ in range(svc.MAX_MAGIC_LINK_ATTEMPTS + 2):
            svc._check_rate_limit(email)

        svc._reset_rate_limit(email)
        allowed, _ = svc._check_rate_limit(email)
        assert allowed is True

    def test_window_expiry_resets_counter(self):
        svc = PasswordlessAuthService()
        email = "window@example.com"
        svc._rate_limits[email] = RateLimitEntry(
            email=email,
            attempts=10,
            first_attempt=datetime.now(UTC) - timedelta(hours=2),
        )
        allowed, _ = svc._check_rate_limit(email)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limited_magic_link_returns_error(self):
        svc = PasswordlessAuthService()
        email = "ratelimited@example.com"
        # Force rate limit
        svc._rate_limits[email] = RateLimitEntry(
            email=email,
            attempts=100,
            blocked_until=datetime.now(UTC) + timedelta(minutes=30),
        )

        result = await svc.generate_magic_link_token(email)
        assert result.success is False
        assert result.error_code == "RATE_LIMITED"


class TestAuditLogs:
    def test_log_event_creates_entry(self):
        svc = PasswordlessAuthService()
        entry = svc._log_audit_event(
            event=PasswordlessAuthEvent.MAGIC_LINK_GENERATED,
            email="user@example.com",
            ip_address="1.2.3.4",
            user_agent="Mozilla/5.0",
            success=True,
        )
        assert entry.event == PasswordlessAuthEvent.MAGIC_LINK_GENERATED
        assert entry.success is True
        assert len(svc._audit_logs) == 1

    def test_audit_logs_capped_at_10000(self):
        svc = PasswordlessAuthService()
        for _ in range(10005):
            svc._log_audit_event(
                event=PasswordlessAuthEvent.MAGIC_LINK_GENERATED,
                email="u@e.com",
                ip_address=None,
                user_agent=None,
                success=True,
            )
        assert len(svc._audit_logs) <= 10000

    def test_get_recent_audit_logs_filter_by_email(self):
        svc = PasswordlessAuthService()
        svc._log_audit_event(
            PasswordlessAuthEvent.MAGIC_LINK_GENERATED, "a@b.com", None, None, True
        )
        svc._log_audit_event(
            PasswordlessAuthEvent.MAGIC_LINK_GENERATED, "c@d.com", None, None, True
        )
        logs = svc.get_recent_audit_logs(email="a@b.com")
        assert all(log.email == "a@b.com" for log in logs)

    def test_get_recent_audit_logs_filter_by_event(self):
        svc = PasswordlessAuthService()
        svc._log_audit_event(
            PasswordlessAuthEvent.MAGIC_LINK_GENERATED, "u@e.com", None, None, True
        )
        svc._log_audit_event(
            PasswordlessAuthEvent.MAGIC_LINK_VERIFIED, "u@e.com", None, None, True
        )
        logs = svc.get_recent_audit_logs(
            event_type=PasswordlessAuthEvent.MAGIC_LINK_VERIFIED
        )
        assert all(
            log.event == PasswordlessAuthEvent.MAGIC_LINK_VERIFIED for log in logs
        )

    def test_get_stats_returns_expected_keys(self):
        svc = PasswordlessAuthService()
        stats = svc.get_stats()
        assert "total_audit_logs" in stats
        assert "events_last_hour" in stats
        assert "magic_links_generated_last_hour" in stats
        assert "magic_links_verified_last_hour" in stats

    @pytest.mark.asyncio
    async def test_send_magic_link_email_returns_true(self):
        svc = PasswordlessAuthService()
        result = await svc.send_magic_link_email("user@example.com", "tok123")
        assert result is True

    @pytest.mark.asyncio
    async def test_log_fallback_to_password(self):
        svc = PasswordlessAuthService()
        await svc.log_fallback_to_password(
            email="user@example.com",
            ip_address="1.2.3.4",
            reason="preferred_password",
        )
        logs = svc.get_recent_audit_logs(
            event_type=PasswordlessAuthEvent.FALLBACK_TO_PASSWORD
        )
        assert len(logs) == 1


class TestWebAuthnService:
    @pytest.mark.asyncio
    async def test_generate_registration_options(self):
        svc = WebAuthnService()
        result = await svc.generate_registration_options(
            user_id=1, user_name="testuser"
        )
        assert result.success is True
        assert result.data is not None
        assert result.data.challenge in svc._challenges

    @pytest.mark.asyncio
    async def test_generate_authentication_options(self):
        svc = WebAuthnService()
        result = await svc.generate_authentication_options(user_id=1)
        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_verify_registration_invalid_challenge(self):
        svc = WebAuthnService()
        result = await svc.verify_registration_response(
            credential_id="cred1",
            client_data_json="eyJjaGFsbGVuZ2UiOiAiYmFkX2NoYWxsZW5nZSJ9",
            attestation_object="att",
            expected_challenge="nonexistent_challenge",
        )
        assert result.success is False
        assert result.error_code == "invalid_challenge"

    @pytest.mark.asyncio
    async def test_full_registration_and_authentication_flow(self):
        import base64
        import json

        svc = WebAuthnService()

        # Step 1: Generate registration challenge
        reg_result = await svc.generate_registration_options(
            user_id=42, user_name="alice"
        )
        assert reg_result.success is True
        challenge = reg_result.data.challenge

        # Step 2: Build a valid client_data_json (base64-encoded JSON with matching challenge)
        client_data = json.dumps({"type": "webauthn.create", "challenge": challenge})
        client_data_b64 = (
            base64.urlsafe_b64encode(client_data.encode()).decode().rstrip("=")
        )

        # Step 3: Verify registration
        verify_result = await svc.verify_registration_response(
            credential_id="cred_alice",
            client_data_json=client_data_b64,
            attestation_object="att_object",
            expected_challenge=challenge,
            device_name="Alice's Device",
        )
        assert verify_result.success is True
        assert "cred_alice" in svc._credentials

    @pytest.mark.asyncio
    async def test_get_user_credentials(self):
        svc = WebAuthnService()
        from core.passwordless_auth import WebAuthnCredential

        svc._credentials["cred1"] = WebAuthnCredential(
            id="cred1", user_id=1, public_key="pk", is_active=True
        )
        svc._credentials["cred2"] = WebAuthnCredential(
            id="cred2", user_id=2, public_key="pk2", is_active=True
        )
        creds = await svc.get_user_credentials(user_id=1)
        assert len(creds) == 1
        assert creds[0].id == "cred1"

    @pytest.mark.asyncio
    async def test_revoke_credential_unauthorized(self):
        from core.passwordless_auth import WebAuthnCredential

        svc = WebAuthnService()
        svc._credentials["cred1"] = WebAuthnCredential(
            id="cred1", user_id=1, public_key="pk"
        )
        result = await svc.revoke_credential("cred1", user_id=99)
        assert result.success is False
        assert result.error_code == "unauthorized"

    @pytest.mark.asyncio
    async def test_revoke_credential_success(self):
        from core.passwordless_auth import WebAuthnCredential

        svc = WebAuthnService()
        svc._credentials["cred1"] = WebAuthnCredential(
            id="cred1", user_id=5, public_key="pk"
        )
        result = await svc.revoke_credential("cred1", user_id=5)
        assert result.success is True
        assert svc._credentials["cred1"].is_active is False


class TestGlobalPasswordlessInstances:
    def test_get_passwordless_auth_service_singleton(self):
        import core.passwordless_auth as mod

        mod._passwordless_service = None
        svc1 = get_passwordless_auth_service()
        svc2 = get_passwordless_auth_service()
        assert svc1 is svc2
        mod._passwordless_service = None

    def test_get_webauthn_service_singleton(self):
        import core.passwordless_auth as mod

        mod._webauthn_service = None
        s1 = get_webauthn_service()
        s2 = get_webauthn_service()
        assert s1 is s2
        mod._webauthn_service = None


# ===========================================================================
# 4. EmbeddingCache Tests
# ===========================================================================


class TestEmbeddingEntry:
    def test_to_dict_and_from_dict(self):
        emb = np.array([0.1, 0.2, 0.3])
        entry = EmbeddingEntry(text="hello", embedding=emb, model="test_model")
        d = entry.to_dict()
        assert d["text"] == "hello"
        assert d["model"] == "test_model"

        restored = EmbeddingEntry.from_dict(d)
        assert restored.text == "hello"
        np.testing.assert_allclose(restored.embedding, emb)

    def test_metadata_default_empty(self):
        emb = np.zeros(10)
        entry = EmbeddingEntry(text="test", embedding=emb)
        assert entry.metadata == {}


class TestSearchResult:
    def test_to_dict(self):
        emb = np.zeros(4)
        sr = SearchResult(text="hello", embedding=emb, similarity=0.9)
        d = sr.to_dict()
        assert d["text"] == "hello"
        assert d["similarity"] == 0.9


class TestEmbeddingIndex:
    def test_add_and_search(self):
        idx = EmbeddingIndex(dimension=4)
        emb1 = np.array([1.0, 0.0, 0.0, 0.0])
        emb2 = np.array([0.0, 1.0, 0.0, 0.0])
        idx.add("text1", emb1)
        idx.add("text2", emb2)

        query = np.array([1.0, 0.0, 0.0, 0.0])
        results = idx.search(query, top_k=1)
        assert len(results) == 1
        assert results[0].text == "text1"
        assert results[0].similarity > 0.99

    def test_search_empty_index_returns_empty(self):
        idx = EmbeddingIndex(dimension=4)
        query = np.array([1.0, 0.0, 0.0, 0.0])
        results = idx.search(query, top_k=5)
        assert results == []

    def test_threshold_filters_low_similarity(self):
        idx = EmbeddingIndex(dimension=4)
        idx.add("text1", np.array([1.0, 0.0, 0.0, 0.0]))
        idx.add("text2", np.array([0.0, 1.0, 0.0, 0.0]))
        query = np.array([1.0, 0.0, 0.0, 0.0])
        # Orthogonal vector has similarity ~0; require 0.9
        results = idx.search(query, top_k=10, threshold=0.9)
        assert len(results) == 1
        assert results[0].text == "text1"

    def test_dimension_mismatch_skipped(self):
        idx = EmbeddingIndex(dimension=4)
        idx.add("misfit", np.array([1.0, 2.0, 3.0]))  # wrong dimension
        assert idx.size() == 0

    def test_size_and_clear(self):
        idx = EmbeddingIndex(dimension=3)
        idx.add("a", np.array([1.0, 0.0, 0.0]))
        idx.add("b", np.array([0.0, 1.0, 0.0]))
        assert idx.size() == 2
        idx.clear()
        assert idx.size() == 0


class TestLRUCache:
    def test_put_and_get(self):
        cache = LRUCache(capacity=3)
        emb = np.zeros(4)
        entry = EmbeddingEntry(text="hello", embedding=emb)
        cache.put("k1", entry)
        assert cache.get("k1") is entry

    def test_capacity_evicts_lru(self):
        cache = LRUCache(capacity=2)
        e1 = EmbeddingEntry(text="a", embedding=np.zeros(4))
        e2 = EmbeddingEntry(text="b", embedding=np.zeros(4))
        e3 = EmbeddingEntry(text="c", embedding=np.zeros(4))
        cache.put("k1", e1)
        cache.put("k2", e2)
        cache.put("k3", e3)  # k1 should be evicted

        assert cache.get("k1") is None
        assert cache.get("k2") is not None

    def test_get_moves_to_end(self):
        cache = LRUCache(capacity=2)
        e1 = EmbeddingEntry(text="a", embedding=np.zeros(4))
        e2 = EmbeddingEntry(text="b", embedding=np.zeros(4))
        e3 = EmbeddingEntry(text="c", embedding=np.zeros(4))
        cache.put("k1", e1)
        cache.put("k2", e2)
        cache.get("k1")  # k1 is now most recently used
        cache.put("k3", e3)  # k2 should be evicted

        assert cache.get("k2") is None
        assert cache.get("k1") is not None

    def test_clear(self):
        cache = LRUCache(capacity=10)
        cache.put("k1", EmbeddingEntry(text="a", embedding=np.zeros(4)))
        cache.clear()
        assert cache.size() == 0


class TestEmbeddingCacheCore:
    @pytest.mark.asyncio
    async def test_initialize_redis_unavailable(self):
        cache = EmbeddingCache()
        with patch(
            "core.embedding_cache.redis.from_url", new_callable=AsyncMock
        ) as mock_redis:
            mock_redis.side_effect = Exception("connection refused")
            result = await cache.initialize()
        assert result is False
        assert cache._redis_available is False

    @pytest.mark.asyncio
    async def test_generate_key_deterministic(self):
        cache = EmbeddingCache()
        k1 = cache._generate_key("Hello World", "model_a")
        k2 = cache._generate_key("hello world", "model_a")  # normalized
        assert k1 == k2

    @pytest.mark.asyncio
    async def test_set_and_get_memory_only(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        emb = np.array([0.1, 0.2, 0.3, 0.4])
        await cache.set("test text", emb, model="m1")

        result = await cache.get("test text", model="m1")
        assert result is not None
        np.testing.assert_allclose(result, emb)

    @pytest.mark.asyncio
    async def test_get_miss_increments_miss_stat(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        await cache.get("no such text", model="default")
        assert cache.stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_set_list_converts_to_numpy(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        emb_list = [0.1, 0.2, 0.3]
        await cache.set("list text", emb_list, model="m2")

        result = await cache.get("list text", model="m2")
        assert result is not None
        assert isinstance(result, np.ndarray)

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        # Use dimension=4 so the EmbeddingIndex accepts 4-d vectors
        cfg = EmbeddingCacheConfig()
        cache = EmbeddingCache(config=cfg)
        cache._redis_available = False
        cache.index = EmbeddingIndex(dimension=4)

        emb1 = np.array([1.0, 0.0, 0.0, 0.0])
        emb2 = np.array([0.0, 1.0, 0.0, 0.0])
        await cache.set("vec1", emb1)
        await cache.set("vec2", emb2)

        query = np.array([1.0, 0.0, 0.0, 0.0])
        results = await cache.search(query, top_k=1, threshold=0.9)
        assert len(results) == 1
        assert results[0].text == "vec1"

    @pytest.mark.asyncio
    async def test_batch_get_returns_dict(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        await cache.set("t1", np.array([1.0, 0.0]))
        await cache.set("t2", np.array([0.0, 1.0]))

        results = await cache.batch_get(["t1", "t2", "t3"])
        assert results["t1"] is not None
        assert results["t2"] is not None
        assert results["t3"] is None

    @pytest.mark.asyncio
    async def test_batch_set_memory_only(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        entries = [("text_a", np.array([1.0, 0.0])), ("text_b", np.array([0.0, 1.0]))]
        count = await cache.batch_set(entries, model="m3")
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_stats_structure(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        stats = await cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_ratio" in stats
        assert "redis_available" in stats
        assert stats["redis_available"] is False

    @pytest.mark.asyncio
    async def test_hit_ratio_calculation(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        await cache.set("x", np.array([1.0]))
        await cache.get("x")  # hit
        await cache.get("x")  # hit
        await cache.get("missing")  # miss

        stats = await cache.get_stats()
        assert abs(stats["hit_ratio"] - 2 / 3) < 0.01

    @pytest.mark.asyncio
    async def test_clear_empties_memory_cache(self):
        cache = EmbeddingCache()
        cache._redis_available = False

        await cache.set("clr", np.array([1.0]))
        await cache.clear()

        result = await cache.get("clr")
        assert result is None


class TestGetEmbeddingCache:
    @pytest.mark.asyncio
    async def test_returns_instance(self):
        import core.embedding_cache as mod

        mod._global_embedding_cache = None
        with patch.object(
            EmbeddingCache, "initialize", new_callable=AsyncMock
        ) as mock_init:
            mock_init.return_value = False
            cache = await get_embedding_cache()
        assert isinstance(cache, EmbeddingCache)
        mod._global_embedding_cache = None


# ===========================================================================
# 5. Quantization Functions Tests
# ===========================================================================


class TestQuantizeEmbedding:
    def test_basic_quantization(self):
        emb = np.array([0.1, 0.5, -0.3, 0.8], dtype=np.float32)
        q = quantize_embedding(emb)
        assert isinstance(q, QuantizedEmbedding)
        assert q.data.dtype == np.int8
        assert q.min_val == pytest.approx(float(emb.min()), rel=1e-5)
        assert q.max_val == pytest.approx(float(emb.max()), rel=1e-5)

    def test_quantize_list_input(self):
        emb_list = [0.1, 0.2, 0.3, 0.4]
        q = quantize_embedding(emb_list)
        assert isinstance(q, QuantizedEmbedding)
        assert q.data.dtype == np.int8

    def test_constant_embedding_no_division_by_zero(self):
        emb = np.ones(10, dtype=np.float32) * 0.5
        q = quantize_embedding(emb)
        assert q is not None
        assert not np.any(np.isnan(q.data.astype(float)))

    def test_memory_reduction_roughly_75_percent(self):
        emb = np.random.randn(768).astype(np.float32)
        q = quantize_embedding(emb)
        assert q.memory_size() < emb.nbytes  # quantized is smaller

    def test_to_dict_and_from_dict(self):
        emb = np.array([0.1, -0.5, 0.3], dtype=np.float32)
        q = quantize_embedding(emb)
        d = q.to_dict()
        restored_q = QuantizedEmbedding.from_dict(d)
        assert restored_q.min_val == q.min_val
        assert restored_q.max_val == q.max_val
        np.testing.assert_array_equal(restored_q.data, q.data)


class TestDequantizeEmbedding:
    def test_round_trip_accuracy(self):
        emb = np.array([0.1, 0.5, -0.3, 0.8], dtype=np.float32)
        q = quantize_embedding(emb)
        restored = dequantize_embedding(q)
        max_error = np.abs(emb - restored).max()
        assert max_error < 0.02  # <2% quantization error

    def test_high_dimension_round_trip(self):
        np.random.seed(42)
        emb = np.random.randn(768).astype(np.float32)
        q = quantize_embedding(emb)
        restored = dequantize_embedding(q)
        # Cosine similarity should be very high
        cos_sim = np.dot(emb, restored) / (
            np.linalg.norm(emb) * np.linalg.norm(restored)
        )
        assert cos_sim > 0.99


class TestQuantizeBatch:
    def test_1d_array_wraps_in_list(self):
        emb = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        result = quantize_batch(emb)
        assert len(result) == 1
        assert isinstance(result[0], QuantizedEmbedding)

    def test_2d_batch(self):
        batch = np.random.randn(5, 4).astype(np.float32)
        result = quantize_batch(batch)
        assert len(result) == 5

    def test_dequantize_batch_round_trip(self):
        batch = np.random.randn(4, 8).astype(np.float32)
        q_list = quantize_batch(batch)
        restored = dequantize_batch(q_list)
        assert restored.shape == batch.shape
        max_err = np.abs(batch - restored).max()
        assert max_err < 0.05

    def test_dequantize_empty_batch(self):
        result = dequantize_batch([])
        assert len(result) == 0


class TestCalculateQuantizationError:
    def test_returns_expected_keys(self):
        emb = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        q = quantize_embedding(emb)
        metrics = calculate_quantization_error(emb, q)

        expected_keys = {
            "max_absolute_error",
            "mean_absolute_error",
            "max_relative_error",
            "mean_relative_error",
            "cosine_similarity",
            "memory_reduction_percent",
            "original_size_bytes",
            "quantized_size_bytes",
        }
        assert expected_keys.issubset(set(metrics.keys()))

    def test_cosine_similarity_close_to_one(self):
        np.random.seed(7)
        emb = np.random.randn(128).astype(np.float32)
        q = quantize_embedding(emb)
        metrics = calculate_quantization_error(emb, q)
        assert metrics["cosine_similarity"] > 0.99

    def test_memory_reduction_is_75_percent(self):
        emb = np.zeros(100, dtype=np.float32)
        q = quantize_embedding(emb)
        metrics = calculate_quantization_error(emb, q)
        assert metrics["memory_reduction_percent"] == 75.0


class TestGetQuantizationStats:
    def test_1d_input_treated_as_single_embedding(self):
        emb = np.random.randn(64).astype(np.float32)
        stats = get_quantization_stats(emb)
        assert stats["sample_count"] == 1

    def test_batch_stats(self):
        batch = np.random.randn(10, 64).astype(np.float32)
        stats = get_quantization_stats(batch)
        assert stats["sample_count"] == 10
        assert 0.0 <= stats["avg_cosine_similarity"] <= 1.0
        assert stats["min_cosine_similarity"] <= stats["avg_cosine_similarity"]


# ===========================================================================
# 6. VideoSolutionService Tests
# ===========================================================================


class TestVideoConfig:
    def test_max_file_size(self):
        assert VideoConfig.MAX_FILE_SIZE_BYTES == 500 * 1024 * 1024

    def test_supported_formats_includes_mp4(self):
        from models.video_solution import VideoFormat

        assert VideoFormat.MP4 in VideoConfig.SUPPORTED_FORMATS

    def test_ensure_directories_creates_dirs(self, tmp_path):
        original_upload = VideoConfig.UPLOAD_DIR
        original_processed = VideoConfig.PROCESSED_DIR
        original_thumb = VideoConfig.THUMBNAIL_DIR

        VideoConfig.UPLOAD_DIR = tmp_path / "uploads" / "videos"
        VideoConfig.PROCESSED_DIR = tmp_path / "uploads" / "videos" / "processed"
        VideoConfig.THUMBNAIL_DIR = tmp_path / "uploads" / "thumbnails"

        VideoConfig.ensure_directories()

        assert VideoConfig.UPLOAD_DIR.exists()
        assert VideoConfig.PROCESSED_DIR.exists()
        assert VideoConfig.THUMBNAIL_DIR.exists()

        VideoConfig.UPLOAD_DIR = original_upload
        VideoConfig.PROCESSED_DIR = original_processed
        VideoConfig.THUMBNAIL_DIR = original_thumb


class TestVideoValidatorUpload:
    def _make_mock_file(self, filename: str, size: int = 1024):
        mock_file = MagicMock()
        mock_file.filename = filename
        mock_file.file = MagicMock()
        mock_file.file.seek = MagicMock()
        mock_file.file.tell.return_value = size
        return mock_file

    @pytest.mark.asyncio
    async def test_no_filename_fails(self):
        mock_file = MagicMock()
        mock_file.filename = None

        mock_db = AsyncMock()
        is_valid, err, _ = await VideoValidator.validate_upload(
            mock_file, "q1", mock_db
        )
        assert is_valid is False
        assert "Dosya adı" in err

    @pytest.mark.asyncio
    async def test_unsupported_format_fails(self):
        mock_file = self._make_mock_file("video.xyz")
        mock_db = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute = AsyncMock(return_value=result_mock)

        is_valid, err, metadata = await VideoValidator.validate_upload(
            mock_file, "q1", mock_db
        )
        assert is_valid is False
        assert "Desteklenmeyen" in err

    @pytest.mark.asyncio
    async def test_empty_file_fails(self):
        mock_file = self._make_mock_file("video.mp4", size=0)
        mock_db = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute = AsyncMock(return_value=result_mock)

        is_valid, err, metadata = await VideoValidator.validate_upload(
            mock_file, "q1", mock_db
        )
        assert is_valid is False
        assert "boş" in err

    @pytest.mark.asyncio
    async def test_file_too_large_fails(self):
        oversized = VideoConfig.MAX_FILE_SIZE_BYTES + 1024
        mock_file = self._make_mock_file("video.mp4", size=oversized)
        mock_db = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute = AsyncMock(return_value=result_mock)

        is_valid, err, metadata = await VideoValidator.validate_upload(
            mock_file, "q1", mock_db
        )
        assert is_valid is False
        assert "büyük" in err

    @pytest.mark.asyncio
    async def test_question_not_found_fails(self):
        mock_file = self._make_mock_file("video.mp4", size=1024)
        mock_db = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        is_valid, err, metadata = await VideoValidator.validate_upload(
            mock_file, "nonexistent_q", mock_db
        )
        assert is_valid is False
        assert "Soru bulunamadı" in err

    @pytest.mark.asyncio
    async def test_valid_file_passes(self):
        mock_file = self._make_mock_file("video.mp4", size=10 * 1024 * 1024)
        mock_db = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = MagicMock()  # question exists
        mock_db.execute = AsyncMock(return_value=result_mock)

        is_valid, err, metadata = await VideoValidator.validate_upload(
            mock_file, "valid_q", mock_db
        )
        assert is_valid is True
        assert err is None
        assert metadata["file_size_bytes"] == 10 * 1024 * 1024


class TestVideoValidateProperties:
    @pytest.mark.asyncio
    async def test_ffprobe_failure_returns_false(self):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"ffprobe not found"))

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            is_valid, err, props = await VideoValidator.validate_video_properties(
                Path("nonexistent.mp4")
            )

        assert is_valid is False
        assert "ffprobe" in err

    @pytest.mark.asyncio
    async def test_no_video_stream_returns_false(self):
        probe_data = json.dumps({"streams": [], "format": {"duration": "60"}})
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(probe_data.encode(), b""))

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            is_valid, err, props = await VideoValidator.validate_video_properties(
                Path("test.mp4")
            )

        assert is_valid is False
        assert "Video stream" in err

    @pytest.mark.asyncio
    async def test_valid_video_properties(self):
        probe_data = json.dumps(
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 1280,
                        "height": 720,
                        "codec_name": "h264",
                        "r_frame_rate": "30/1",
                    }
                ],
                "format": {"duration": "120", "bit_rate": "2000000"},
            }
        )
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(probe_data.encode(), b""))

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            is_valid, err, props = await VideoValidator.validate_video_properties(
                Path("good_video.mp4")
            )

        assert is_valid is True
        assert err is None
        assert props["width"] == 1280
        assert props["codec"] == "h264"

    @pytest.mark.asyncio
    async def test_video_too_short_fails(self):
        probe_data = json.dumps(
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 1280,
                        "height": 720,
                        "codec_name": "h264",
                        "r_frame_rate": "30/1",
                    }
                ],
                "format": {"duration": "5", "bit_rate": "2000000"},  # < 10s minimum
            }
        )
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(probe_data.encode(), b""))

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            is_valid, err, props = await VideoValidator.validate_video_properties(
                Path("short.mp4")
            )

        assert is_valid is False
        assert "kısa" in err

    @pytest.mark.asyncio
    async def test_low_resolution_fails(self):
        probe_data = json.dumps(
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 320,
                        "height": 240,
                        "codec_name": "h264",
                        "r_frame_rate": "30/1",
                    }
                ],
                "format": {"duration": "60", "bit_rate": "500000"},
            }
        )
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(probe_data.encode(), b""))

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            is_valid, err, props = await VideoValidator.validate_video_properties(
                Path("lowres.mp4")
            )

        assert is_valid is False
        assert "Çözünürlük" in err


class TestVideoProcessor:
    @pytest.mark.asyncio
    async def test_compress_video_ffmpeg_error(self):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"error output"))

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            success, err, stats = await VideoProcessor.compress_video(
                Path("input.mp4"), Path("output.mp4")
            )

        assert success is False
        assert "Sıkıştırma hatası" in err
        assert stats is None

    @pytest.mark.asyncio
    async def test_generate_thumbnail_ffmpeg_error(self):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"thumb error"))

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            success, err = await VideoProcessor.generate_thumbnail(
                Path("video.mp4"), Path("thumb.jpg")
            )

        assert success is False
        assert err is not None

    @pytest.mark.asyncio
    async def test_generate_thumbnail_success(self, tmp_path):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        # Create a dummy output file
        thumb_path = tmp_path / "thumb.jpg"

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = mock_process
            success, err = await VideoProcessor.generate_thumbnail(
                Path("video.mp4"), thumb_path
            )

        assert success is True
        assert err is None
