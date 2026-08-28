"""GF1x regression: a token validated within the 60s positive-cache window must
still be rejected immediately after logout blacklists it.

Root cause (2026-06-23): JWTManager.is_blacklisted_async checked the `valid_tokens`
positive cache BEFORE `blacklisted_tokens`, and blacklist_token_async never evicted
the token from `valid_tokens`. So GET /me (caches valid) → logout (blacklists) →
GET /me returned 200 instead of 401 for up to 60s.
"""

import pytest

from core.jwt_auth import JWTManager, UserRole


def _make_token(mgr: JWTManager) -> str:
    return mgr.create_access_token(
        user_id="test-user-1",
        email="test@kiro2.com",
        role=UserRole.STUDENT,
    )


@pytest.mark.asyncio
async def test_blacklist_wins_over_valid_cache_after_validation():
    """validate (populates valid_tokens) → blacklist → must be blacklisted NOW."""
    mgr = JWTManager()  # no Redis: in-memory only path

    token = _make_token(mgr)

    # 1) First check populates the valid_tokens positive cache and returns False.
    assert await mgr.is_blacklisted_async(token) is False

    # 2) Logout blacklists the token.
    await mgr.blacklist_token_async(token)

    # 3) The very next check must report blacklisted despite the fresh valid cache.
    assert await mgr.is_blacklisted_async(token) is True


@pytest.mark.asyncio
async def test_blacklist_without_prior_validation_still_blocks():
    """Sanity: blacklisting a never-validated token is detected."""
    mgr = JWTManager()
    token = _make_token(mgr)
    await mgr.blacklist_token_async(token)
    assert await mgr.is_blacklisted_async(token) is True
