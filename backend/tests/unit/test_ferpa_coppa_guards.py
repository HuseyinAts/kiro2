"""F4: FERPA/COPPA — temel yetki kapıları."""

from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.ferpa_coppa_compliance_api import (
    COPPAConsentRequest,
    request_coppa_parental_consent,
)
from core.dependencies import AuthenticatedUser, UserRole


@pytest.mark.asyncio
async def test_coppa_create_rejects_non_parent_non_admin() -> None:
    req = COPPAConsentRequest(
        child_id="child-1",
        parent_id="parent-1",
        child_date_of_birth=date.today() - timedelta(days=365 * 10),
        verification_method="email",
        allow_data_collection=False,
        allow_marketing_communication=False,
        allow_third_party_sharing=False,
    )
    user = AuthenticatedUser(
        id=99, username="stu", role=UserRole.STUDENT, email=None
    )
    db = AsyncMock()
    with pytest.raises(HTTPException) as ei:
        await request_coppa_parental_consent(req, db, user)
    assert ei.value.status_code == 403
    db.execute.assert_not_called()
