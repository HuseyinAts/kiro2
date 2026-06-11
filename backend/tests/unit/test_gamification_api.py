"""
Unit tests for api/gamification_api.py

Covers:
- Helper functions: calculate_level, xp_for_level, get_badge_definitions
- GET  /points              (get_points_summary)
- GET  /points/history      (get_point_history)
- POST /points/award        (award_points)
- GET  /level               (get_level_info)
- GET  /level/progress      (get_level_progress)
- GET  /badges              (get_all_badges)
- GET  /badges/earned       (get_earned_badges)
- GET  /badges/categories   (get_badge_categories)
- GET  /leaderboard         (get_leaderboard)
- GET  /achievements        (get_user_achievements)
- GET  /achievements/completed (get_completed_achievements)
- GET  /leaderboard/nearby  (get_nearby_users_in_leaderboard)
- GET  /leaderboard/rank    (get_user_leaderboard_rank)
- GET  /leaderboard/stats   (get_leaderboard_statistics)
"""

import sys

sys.path.insert(0, "C:/Users/husey/kiro2/backend")

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cache_miss():
    """Return a RedisCache mock that always misses."""
    cache = MagicMock()
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    return cache


def _make_cache_hit(data: dict):
    """Return a RedisCache mock that always returns cached data."""
    cache = MagicMock()
    cache.get.return_value = data
    return cache


def _make_async_db(fetchall=None, scalars_all=None):
    """Return an AsyncMock DB session for async endpoints."""
    db = AsyncMock()
    result_mock = MagicMock()
    if fetchall is not None:
        result_mock.fetchall.return_value = fetchall
        result_mock.all.return_value = fetchall
    if scalars_all is not None:
        result_mock.scalars.return_value.all.return_value = scalars_all
    db.execute.return_value = result_mock
    return db


def _make_leaderboard_manager(nearby=None, rank_info=None, stats=None):
    """Return a mock LeaderboardManager."""
    mgr = MagicMock()
    mgr.get_nearby_users.return_value = nearby or {"users": []}
    mgr.get_user_rank.return_value = rank_info
    mgr.get_leaderboard_stats.return_value = stats or {"total_users": 0}
    return mgr


def _make_test_user(user_id="user-001"):
    """Return a mock AuthenticatedUser for endpoint tests."""
    from core.dependencies import AuthenticatedUser, UserRole

    return AuthenticatedUser(
        id=user_id,
        username="test_user",
        role=UserRole("student"),
        email="test@test.com",
    )


_MOCK_SUMMARY_ZERO = {"total_points": 0, "daily_points": 0, "weekly_points": 0}


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------


class TestCalculateLevel:
    """Tests for the calculate_level helper function."""

    def setup_method(self):
        from api.gamification_api import calculate_level

        self.calculate_level = calculate_level

    def test_zero_xp_returns_level_one(self):
        assert self.calculate_level(0) == 1

    def test_small_xp_stays_level_one(self):
        assert self.calculate_level(50) == 1

    def test_exact_threshold_advances_level(self):
        from api.gamification_api import xp_for_level

        threshold = xp_for_level(2)
        assert self.calculate_level(threshold) == 2

    def test_below_threshold_stays_previous_level(self):
        from api.gamification_api import xp_for_level

        threshold = xp_for_level(2)
        assert self.calculate_level(threshold - 1) == 1

    def test_very_high_xp_gives_high_level(self):
        result = self.calculate_level(1_000_000)
        assert result >= 10


class TestXpForLevel:
    """Tests for the xp_for_level helper function."""

    def setup_method(self):
        from api.gamification_api import xp_for_level

        self.xp_for_level = xp_for_level

    def test_level_one_requires_zero_xp(self):
        assert self.xp_for_level(1) == 0

    def test_level_two_requires_positive_xp(self):
        assert self.xp_for_level(2) > 0

    def test_xp_is_monotonically_increasing(self):
        for lvl in range(1, 10):
            assert self.xp_for_level(lvl + 1) > self.xp_for_level(lvl)


class TestGetBadgeDefinitions:
    """Tests for the get_badge_definitions helper function."""

    def setup_method(self):
        from api.gamification_api import get_badge_definitions

        self.get_badge_definitions = get_badge_definitions

    def test_returns_list(self):
        result = self.get_badge_definitions()
        assert isinstance(result, list)

    def test_each_badge_has_required_keys(self):
        required = {"id", "name", "description", "category", "rarity", "icon"}
        for badge in self.get_badge_definitions():
            assert required <= badge.keys(), f"Badge {badge.get('id')} missing keys"

    def test_categories_are_valid(self):
        valid_cats = {"study", "exam", "social", "special", "milestone"}
        for badge in self.get_badge_definitions():
            assert badge["category"] in valid_cats

    def test_rarities_are_valid(self):
        valid_rarities = {"common", "rare", "legendary"}
        for badge in self.get_badge_definitions():
            assert badge["rarity"] in valid_rarities


# ---------------------------------------------------------------------------
# Endpoint tests — mock GamificationDBService for DB-backed endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetPointsSummary:
    """Tests for GET /points endpoint."""

    async def test_cache_hit_returns_cached_data(self):
        from api.gamification_api import get_points_summary

        cached_data = {"success": True, "data": {"total_points": 42}}
        db = AsyncMock()

        with patch(
            "api.gamification_api.get_cache", return_value=_make_cache_hit(cached_data)
        ):
            result = await get_points_summary(
                current_user=_make_test_user("user-001"), db=db
            )

        assert result == cached_data

    async def test_cache_miss_computes_summary(self):
        from api.gamification_api import get_points_summary

        mock_summary = {"total_points": 200, "daily_points": 50, "weekly_points": 100}
        db = AsyncMock()

        with (
            patch("api.gamification_api.get_cache", return_value=_make_cache_miss()),
            patch(
                "api.gamification_api.GamificationDBService.get_points_summary",
                new=AsyncMock(return_value=mock_summary),
            ),
        ):
            result = await get_points_summary(
                current_user=_make_test_user("user-compute"), db=db
            )

        assert result["success"] is True
        assert result["data"]["total_points"] == 200

    async def test_new_user_has_zero_points(self):
        from api.gamification_api import get_points_summary

        db = AsyncMock()

        with (
            patch("api.gamification_api.get_cache", return_value=_make_cache_miss()),
            patch(
                "api.gamification_api.GamificationDBService.get_points_summary",
                new=AsyncMock(return_value=_MOCK_SUMMARY_ZERO),
            ),
        ):
            result = await get_points_summary(
                current_user=_make_test_user("brand-new-user"), db=db
            )

        assert result["data"]["total_points"] == 0
        assert result["data"]["daily_points"] == 0
        assert result["data"]["weekly_points"] == 0

    async def test_response_structure_has_message(self):
        from api.gamification_api import get_points_summary

        db = AsyncMock()

        with (
            patch("api.gamification_api.get_cache", return_value=_make_cache_miss()),
            patch(
                "api.gamification_api.GamificationDBService.get_points_summary",
                new=AsyncMock(return_value=_MOCK_SUMMARY_ZERO),
            ),
        ):
            result = await get_points_summary(
                current_user=_make_test_user("some-user"), db=db
            )

        assert "message" in result
        assert "data" in result


@pytest.mark.asyncio
class TestGetPointHistory:
    """Tests for GET /points/history endpoint."""

    async def test_returns_empty_for_new_user(self):
        from api.gamification_api import get_point_history

        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_point_history",
            new=AsyncMock(return_value=[]),
        ):
            result = await get_point_history(
                current_user=_make_test_user("no-history"), db=db, days=30, limit=None
            )

        assert result["success"] is True
        assert result["data"]["total_count"] == 0
        assert result["data"]["transactions"] == []

    async def test_period_days_reflected_in_response(self):
        from api.gamification_api import get_point_history

        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_point_history",
            new=AsyncMock(return_value=[]),
        ):
            result = await get_point_history(
                current_user=_make_test_user("any"), db=db, days=7, limit=None
            )

        assert result["data"]["period_days"] == 7

    async def test_returns_transactions(self):
        from api.gamification_api import get_point_history

        txns = [
            {"points": 10, "timestamp": "2024-01-01"},
            {"points": 20, "timestamp": "2024-01-02"},
        ]
        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_point_history",
            new=AsyncMock(return_value=txns),
        ):
            result = await get_point_history(
                current_user=_make_test_user("txn-user"), db=db, days=365, limit=None
            )

        assert result["data"]["total_count"] == 2


@pytest.mark.asyncio
class TestAwardPoints:
    """Tests for POST /points/award endpoint."""

    async def test_award_returns_new_total(self):
        from api.gamification_api import AwardPointsRequest, award_points

        db = AsyncMock()

        with (
            patch(
                "api.gamification_api.GamificationDBService.award_xp",
                new=AsyncMock(return_value=50),
            ),
            patch(
                "api.gamification_api.GamificationDBService.update_leaderboard",
                new=AsyncMock(),
            ),
            patch("api.gamification_api.get_cache", return_value=_make_cache_miss()),
        ):
            result = await award_points(
                current_user=_make_test_user("award-user"),
                db=db,
                body=AwardPointsRequest(
                    points=50, reason="quiz_completion"
                ),
            )

        assert result["success"] is True
        assert result["data"]["new_total"] == 50

    async def test_cumulative_awards_accumulate(self):
        from api.gamification_api import AwardPointsRequest, award_points

        db = AsyncMock()

        with (
            patch(
                "api.gamification_api.GamificationDBService.award_xp",
                new=AsyncMock(return_value=125),
            ),
            patch(
                "api.gamification_api.GamificationDBService.update_leaderboard",
                new=AsyncMock(),
            ),
            patch("api.gamification_api.get_cache", return_value=_make_cache_miss()),
        ):
            result = await award_points(
                current_user=_make_test_user("cumul-user"),
                db=db,
                body=AwardPointsRequest(
                    points=25, reason="streak_milestone"
                ),
            )

        assert result["data"]["new_total"] == 125

    async def test_transaction_has_required_fields(self):
        from api.gamification_api import AwardPointsRequest, award_points

        db = AsyncMock()

        with (
            patch(
                "api.gamification_api.GamificationDBService.award_xp",
                new=AsyncMock(return_value=5),
            ),
            patch(
                "api.gamification_api.GamificationDBService.update_leaderboard",
                new=AsyncMock(),
            ),
            patch("api.gamification_api.get_cache", return_value=_make_cache_miss()),
        ):
            result = await award_points(
                current_user=_make_test_user("field-test"),
                db=db,
                body=AwardPointsRequest(
                    points=5, reason="streak_milestone"
                ),
            )

        txn = result["data"]["transaction"]
        for field in ("user_id", "points", "reason", "timestamp"):
            assert field in txn


@pytest.mark.asyncio
class TestGetLevelInfo:
    """Tests for GET /level endpoint."""

    async def test_new_user_at_level_one(self):
        from api.gamification_api import get_level_info

        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_points_summary",
            new=AsyncMock(return_value=_MOCK_SUMMARY_ZERO),
        ):
            result = await get_level_info(
                current_user=_make_test_user("fresh-user"), db=db
            )

        assert result["success"] is True
        assert result["data"]["current_level"] == 1
        assert result["data"]["total_xp"] == 0

    async def test_progress_percentage_between_zero_and_hundred(self):
        from api.gamification_api import get_level_info

        mock_summary = {"total_points": 75, "daily_points": 0, "weekly_points": 0}
        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_points_summary",
            new=AsyncMock(return_value=mock_summary),
        ):
            result = await get_level_info(
                current_user=_make_test_user("progress-user"), db=db
            )

        pct = result["data"]["progress_percentage"]
        assert 0.0 <= pct <= 100.0

    async def test_xp_for_next_level_is_positive(self):
        from api.gamification_api import get_level_info

        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_points_summary",
            new=AsyncMock(return_value=_MOCK_SUMMARY_ZERO),
        ):
            result = await get_level_info(
                current_user=_make_test_user("any-level"), db=db
            )

        assert result["data"]["xp_for_next_level"] > 0

    async def test_response_has_all_level_fields(self):
        from api.gamification_api import get_level_info

        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_points_summary",
            new=AsyncMock(return_value=_MOCK_SUMMARY_ZERO),
        ):
            result = await get_level_info(
                current_user=_make_test_user("fields-check"), db=db
            )

        for key in (
            "current_level",
            "total_xp",
            "xp_for_next_level",
            "progress_percentage",
        ):
            assert key in result["data"]


@pytest.mark.asyncio
class TestGetLevelProgress:
    """Tests for GET /level/progress endpoint."""

    async def test_new_user_progress_response(self):
        from api.gamification_api import get_level_progress

        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_points_summary",
            new=AsyncMock(return_value=_MOCK_SUMMARY_ZERO),
        ):
            result = await get_level_progress(
                current_user=_make_test_user("new-progress"), db=db
            )

        assert result["success"] is True
        data = result["data"]
        assert data["current_level"] == 1
        assert data["total_xp"] == 0
        assert data["xp_in_current_level"] == 0

    async def test_xp_in_current_level_is_non_negative(self):
        from api.gamification_api import get_level_progress

        mock_summary = {"total_points": 300, "daily_points": 0, "weekly_points": 0}
        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_points_summary",
            new=AsyncMock(return_value=mock_summary),
        ):
            result = await get_level_progress(
                current_user=_make_test_user("progress-level"), db=db
            )

        assert result["data"]["xp_in_current_level"] >= 0

    async def test_progress_percentage_non_negative(self):
        from api.gamification_api import get_level_progress

        db = AsyncMock()

        with patch(
            "api.gamification_api.GamificationDBService.get_points_summary",
            new=AsyncMock(return_value=_MOCK_SUMMARY_ZERO),
        ):
            result = await get_level_progress(
                current_user=_make_test_user("any-progress"), db=db
            )

        assert result["data"]["progress_percentage"] >= 0


# ---------------------------------------------------------------------------
# Badge endpoint tests — mock DB queries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetAllBadges:
    """Tests for GET /badges endpoint."""

    async def test_returns_all_badges_without_filter(self):
        from api.gamification_api import get_all_badges, get_badge_definitions

        db = _make_async_db(fetchall=[])
        result = await get_all_badges(
            current_user=_make_test_user("badge-user"), db=db, category=None
        )

        assert result["success"] is True
        assert result["data"]["total_count"] == len(get_badge_definitions())

    async def test_category_filter_reduces_count(self):
        from api.gamification_api import get_all_badges

        db1 = _make_async_db(fetchall=[])
        result_all = await get_all_badges(
            current_user=_make_test_user("filter-user"), db=db1, category=None
        )

        db2 = _make_async_db(fetchall=[])
        result_study = await get_all_badges(
            current_user=_make_test_user("filter-user"), db=db2, category="study"
        )

        assert result_study["data"]["total_count"] < result_all["data"]["total_count"]

    async def test_category_filter_only_returns_matching(self):
        from api.gamification_api import get_all_badges

        db = _make_async_db(fetchall=[])
        result = await get_all_badges(
            current_user=_make_test_user("cat-check"), db=db, category="exam"
        )

        for badge in result["data"]["badges"]:
            assert badge["category"] == "exam"

    async def test_new_user_has_zero_earned_badges(self):
        from api.gamification_api import get_all_badges

        db = _make_async_db(fetchall=[])
        result = await get_all_badges(
            current_user=_make_test_user("zero-earned"), db=db, category=None
        )

        assert result["data"]["earned_count"] == 0
        for badge in result["data"]["badges"]:
            assert badge["earned"] is False

    async def test_badge_info_has_required_fields(self):
        from api.gamification_api import get_all_badges

        db = _make_async_db(fetchall=[])
        result = await get_all_badges(
            current_user=_make_test_user("fields-user"), db=db, category=None
        )

        for badge in result["data"]["badges"]:
            for key in (
                "badge_id",
                "name",
                "description",
                "category",
                "rarity",
                "icon",
                "earned",
            ):
                assert key in badge


@pytest.mark.asyncio
class TestGetEarnedBadges:
    """Tests for GET /badges/earned endpoint."""

    async def test_new_user_returns_empty_earned_list(self):
        from api.gamification_api import get_earned_badges

        db = _make_async_db(scalars_all=[])
        result = await get_earned_badges(
            current_user=_make_test_user("no-earned"), db=db
        )

        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert result["data"]["badges"] == []

    async def test_user_with_badges_returns_them(self):
        from api.gamification_api import get_earned_badges

        earned_row = MagicMock()
        earned_row.badge_id = "consistent_7"
        earned_row.earned_at = None

        db = _make_async_db(fetchall=[(earned_row, "consistent_7")])
        result = await get_earned_badges(
            current_user=_make_test_user("has-badges"), db=db
        )

        assert result["data"]["count"] == 1
        assert result["data"]["badges"][0]["badge_id"] == "consistent_7"
        assert result["data"]["badges"][0]["earned"] is True


@pytest.mark.asyncio
class TestGetBadgeCategories:
    """Tests for GET /badges/categories endpoint."""

    async def test_returns_all_expected_categories(self):
        from api.gamification_api import get_badge_categories

        db = _make_async_db(fetchall=[])
        result = await get_badge_categories(
            current_user=_make_test_user("cat-user"), db=db
        )

        assert result["success"] is True
        cats = result["data"]["categories"]
        for expected_cat in ("study", "exam", "social", "special", "milestone"):
            assert expected_cat in cats

    async def test_completion_percentage_between_zero_and_hundred(self):
        from api.gamification_api import get_badge_categories

        db = _make_async_db(fetchall=[])
        result = await get_badge_categories(
            current_user=_make_test_user("pct-user"), db=db
        )

        for cat, stats in result["data"]["categories"].items():
            pct = stats["completion_percentage"]
            assert 0.0 <= pct <= 100.0

    async def test_earned_never_exceeds_total(self):
        from api.gamification_api import get_badge_categories

        db = _make_async_db(fetchall=[])
        result = await get_badge_categories(
            current_user=_make_test_user("earned-vs-total"), db=db
        )

        for cat, stats in result["data"]["categories"].items():
            assert stats["earned"] <= stats["total"]


# ---------------------------------------------------------------------------
# Leaderboard endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetLeaderboard:
    """Tests for GET /leaderboard endpoint."""

    async def test_cache_hit_returns_cached(self):
        from api.gamification_api import get_leaderboard

        cached = {"success": True, "data": {"period": "weekly", "entries": []}}
        db = AsyncMock()

        with patch(
            "api.gamification_api.get_cache", return_value=_make_cache_hit(cached)
        ):
            result = await get_leaderboard(
                current_user=_make_test_user("cache-user"),
                db=db,
                period="weekly",
                limit=10,
            )

        assert result == cached

    async def test_empty_user_pool_returns_empty_entries(self):
        from api.gamification_api import get_leaderboard

        db = _make_async_db(fetchall=[])

        with patch("api.gamification_api.get_cache", return_value=_make_cache_miss()):
            result = await get_leaderboard(
                current_user=_make_test_user("empty-pool"),
                db=db,
                period="alltime",
                limit=100,
            )

        assert result["success"] is True
        assert result["data"]["entries"] == []

    async def test_period_reflected_in_response(self):
        from api.gamification_api import get_leaderboard

        db = _make_async_db(fetchall=[])

        with patch("api.gamification_api.get_cache", return_value=_make_cache_miss()):
            result = await get_leaderboard(
                current_user=_make_test_user("period-user"),
                db=db,
                period="monthly",
                limit=5,
            )

        assert result["data"]["period"] == "monthly"

    async def test_user_rank_populated_when_in_pool(self):
        from api.gamification_api import get_leaderboard

        uid = "rank-check-user"
        rows = [(uid, "test@test.com", 999)]
        db = _make_async_db(fetchall=rows)

        with patch("api.gamification_api.get_cache", return_value=_make_cache_miss()):
            result = await get_leaderboard(
                current_user=_make_test_user(uid),
                db=db,
                period="alltime",
                limit=100,
            )

        assert result["data"]["user_rank"] is not None

    async def test_unknown_user_has_no_rank(self):
        from api.gamification_api import get_leaderboard

        rows = [("other-user", "other@test.com", 500)]
        db = _make_async_db(fetchall=rows)

        with patch("api.gamification_api.get_cache", return_value=_make_cache_miss()):
            result = await get_leaderboard(
                current_user=_make_test_user("totally-unknown-user"),
                db=db,
                period="alltime",
                limit=100,
            )

        assert result["data"]["user_rank"] is None


# ---------------------------------------------------------------------------
# P2.2: Achievement & Leaderboard Manager tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetUserAchievements:
    """Tests for GET /achievements endpoint (P2.2, uses DB)."""

    async def test_empty_achievements_for_new_user(self):
        from api.gamification_api import get_user_achievements

        db = _make_async_db(scalars_all=[])
        result = await get_user_achievements(
            current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
            db=db,
        )

        assert result["success"] is True
        assert result["data"]["total_count"] == 0
        assert result["data"]["completed_count"] == 0
        assert result["data"]["in_progress_count"] == 0

    async def test_counts_completed_vs_in_progress(self):
        from api.gamification_api import get_user_achievements

        def _ach(completed: bool):
            a = MagicMock()
            a.is_completed = completed
            a.to_dict.return_value = {"is_completed": completed}
            return a

        achievements = [_ach(True), _ach(True), _ach(False)]
        db = _make_async_db(scalars_all=achievements)

        result = await get_user_achievements(
            current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
            db=db,
        )

        assert result["data"]["completed_count"] == 2
        assert result["data"]["in_progress_count"] == 1
        assert result["data"]["total_count"] == 3

    async def test_response_contains_achievements_list(self):
        from api.gamification_api import get_user_achievements

        db = _make_async_db(scalars_all=[])
        result = await get_user_achievements(
            current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
            db=db,
        )

        assert "achievements" in result["data"]


@pytest.mark.asyncio
class TestGetCompletedAchievements:
    """Tests for GET /achievements/completed endpoint (P2.2)."""

    async def test_returns_only_completed(self):
        from api.gamification_api import get_completed_achievements

        def _ach():
            a = MagicMock()
            a.is_completed = True
            a.to_dict.return_value = {"is_completed": True}
            return a

        db = _make_async_db(scalars_all=[_ach(), _ach()])
        result = await get_completed_achievements(
            current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
            db=db,
        )

        assert result["success"] is True
        assert result["data"]["count"] == 2

    async def test_empty_when_no_completions(self):
        from api.gamification_api import get_completed_achievements

        db = _make_async_db(scalars_all=[])
        result = await get_completed_achievements(
            current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
            db=db,
        )

        assert result["data"]["count"] == 0
        assert result["data"]["achievements"] == []


@pytest.mark.asyncio
class TestGetNearbyUsers:
    """Tests for GET /leaderboard/nearby endpoint (P2.2)."""

    async def test_returns_nearby_users_from_manager(self):
        from api.gamification_api import get_nearby_users_in_leaderboard

        nearby_data = {"users": [{"user_id": "abc", "rank": 2}]}
        mgr = _make_leaderboard_manager(nearby=nearby_data)

        db = MagicMock()
        redis = MagicMock()

        with patch("api.gamification_api.get_leaderboard_manager", return_value=mgr):
            result = get_nearby_users_in_leaderboard(
                current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                leaderboard_type="global",
                range_size=5,
                db=db,
                redis=redis,
            )

        assert result["success"] is True
        assert result["data"] == nearby_data

    async def test_manager_called_with_correct_args(self):
        from uuid import UUID

        from api.gamification_api import get_nearby_users_in_leaderboard

        mgr = _make_leaderboard_manager()
        db = MagicMock()
        redis = MagicMock()
        uid = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

        with patch("api.gamification_api.get_leaderboard_manager", return_value=mgr):
            get_nearby_users_in_leaderboard(
                current_user=_make_test_user(uid),
                leaderboard_type="weekly",
                range_size=3,
                db=db,
                redis=redis,
            )

        mgr.get_nearby_users.assert_called_once_with(
            user_id=uid,
            leaderboard_type="weekly",
            range_size=3,
        )


@pytest.mark.asyncio
class TestGetUserLeaderboardRank:
    """Tests for GET /leaderboard/rank endpoint (P2.2)."""

    async def test_returns_rank_info_when_found(self):
        from api.gamification_api import get_user_leaderboard_rank

        rank_data = {
            "rank": 5,
            "score": 1200,
            "total_users": 100,
            "percentile": 95.0,
        }
        mgr = _make_leaderboard_manager(rank_info=rank_data)

        db = MagicMock()
        redis = MagicMock()

        with patch("api.gamification_api.get_leaderboard_manager", return_value=mgr):
            result = get_user_leaderboard_rank(
                current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                leaderboard_type="global",
                db=db,
                redis=redis,
            )

        assert result["success"] is True
        assert result["data"] == rank_data

    async def test_returns_not_found_when_rank_is_none(self):
        from api.gamification_api import get_user_leaderboard_rank

        mgr = _make_leaderboard_manager(rank_info=None)
        db = MagicMock()
        redis = MagicMock()

        with patch("api.gamification_api.get_leaderboard_manager", return_value=mgr):
            result = get_user_leaderboard_rank(
                current_user=_make_test_user("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                leaderboard_type="global",
                db=db,
                redis=redis,
            )

        assert result["success"] is False
        assert result["data"] is None


@pytest.mark.asyncio
class TestGetLeaderboardStatistics:
    """Tests for GET /leaderboard/stats endpoint (P2.2)."""

    async def test_returns_stats_from_manager(self):
        from api.gamification_api import get_leaderboard_statistics

        stats_data = {"total_users": 500, "top_score": 9999, "avg_score": 450}
        mgr = _make_leaderboard_manager(stats=stats_data)

        db = MagicMock()
        redis = MagicMock()

        with patch("api.gamification_api.get_leaderboard_manager", return_value=mgr):
            result = get_leaderboard_statistics(
                current_user=_make_test_user("stats-user"),
                leaderboard_type="global",
                db=db,
                redis=redis,
            )

        assert result["success"] is True
        assert result["data"] == stats_data

    async def test_manager_receives_correct_leaderboard_type(self):
        from api.gamification_api import get_leaderboard_statistics

        mgr = _make_leaderboard_manager()
        db = MagicMock()
        redis = MagicMock()

        with patch("api.gamification_api.get_leaderboard_manager", return_value=mgr):
            get_leaderboard_statistics(
                current_user=_make_test_user("stats-user"),
                leaderboard_type="weekly",
                db=db,
                redis=redis,
            )

        mgr.get_leaderboard_stats.assert_called_once_with("weekly")
