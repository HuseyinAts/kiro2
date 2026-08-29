from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from models.streak_tracking import PerformanceHistory, StreakTracking


@pytest.mark.asyncio
async def test_growth_mindset_api_endpoint(
    async_client: AsyncClient, mock_student_user, db_session: AsyncSession
):
    """
    Test that the /api/v1/student-dashboard/growth-mindset endpoint successfully
    returns a valid Growth Mindset message by evaluating the user's streak and performance.

    NOT (29 Agu 2026, SS10.9 zinciri): Bu test onceden `mock_db_session`
    (conftest.py -- salt bir unittest.mock.AsyncMock()) kullaniyordu. O
    fixture hicbir gercek veritabanina bagli degil; `.add()`/`.commit()`
    cagrilari sessizce hicbir seye yazmiyordu, yani asagidaki seed verisi
    HTTP katmaninin gercekte gordugu (get_db -> db_manager, `async_client`
    ile ayni test_async_engine'e bagli) veritabaninda hic var olmuyordu --
    endpoint gercekten cagrilsaydi bile "improvement" degil "neutral" donerdi.
    Gercek `db_session` fixture'ina (tests/conftest.py) geciyoruz.
    """
    user_id = "test-user-123"

    # 1. Create a streak for the user
    streak = StreakTracking(
        user_id=user_id,
        current_streak=5,
        best_streak=10,
        last_correct_answer=datetime.now(UTC),
    )
    db_session.add(streak)

    # 2. Add some performance history
    now = datetime.now(UTC)
    perf1 = PerformanceHistory(user_id=user_id, score=80.0, recorded_at=now)
    perf2 = PerformanceHistory(
        user_id=user_id, score=60.0, recorded_at=now - timedelta(days=1)
    )
    db_session.add(perf1)
    db_session.add(perf2)

    await db_session.commit()

    # For this test we need to mock the dependency or generate a valid token.
    # We will use the auth_headers fixture from the project or simply override the dependency.
    # Since we can't easily generate a real token here without auth service,
    # Let's override `mevcut_kullanici_getir` dependency on `app`.
    class MockKullanici:
        kullanici_id = user_id

    from api.auth import mevcut_kullanici_getir

    app.dependency_overrides[mevcut_kullanici_getir] = lambda: MockKullanici()

    # 3. Call the endpoint
    response = await async_client.get(
        "/api/v1/student-dashboard/growth-mindset",
        headers={"Authorization": "Bearer dummy"},
    )

    app.dependency_overrides.pop(mevcut_kullanici_getir, None)

    # 4. Verify the response
    assert response.status_code == 200
    data = response.json()

    # It should detect improvement (80 vs 60)
    assert data["type"] == "improvement"
    assert "Gelişim Gözlemlendi" in data["title"]
    assert "arttı" in data["message"]
