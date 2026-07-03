"""Faz 0 Step 4 — require_org_role + get_current_membership.

SCHOOL_ADMIN kurum-içi süper-yetkili (her guard geçer); yetkisiz/üyeliksiz 403.
"""

import pytest
from fastapi import HTTPException

from core.dependencies import require_org_role


async def _run_guard(guard, org_role):
    """require_org_role factory'nin ürettiği _guard'ı sahte membership ile çalıştır."""
    membership = {"organization_id": "org_x", "org_role": org_role}
    # _guard'ın tek bağımlılığı membership; doğrudan çağırıyoruz
    return await guard(membership=membership)


@pytest.mark.asyncio
async def test_school_admin_passes_any_guard():
    guard = require_org_role("TEACHER")  # admin değil ama SCHOOL_ADMIN geçmeli
    result = await _run_guard(guard, "SCHOOL_ADMIN")
    assert result["org_role"] == "SCHOOL_ADMIN"


@pytest.mark.asyncio
async def test_exact_role_passes():
    guard = require_org_role("TEACHER")
    result = await _run_guard(guard, "TEACHER")
    assert result["org_role"] == "TEACHER"


@pytest.mark.asyncio
async def test_insufficient_role_403():
    guard = require_org_role("SCHOOL_ADMIN")  # sadece admin
    with pytest.raises(HTTPException) as exc:
        await _run_guard(guard, "STUDENT")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_multiple_allowed_roles():
    guard = require_org_role("TEACHER", "PARENT")
    assert (await _run_guard(guard, "PARENT"))["org_role"] == "PARENT"
    with pytest.raises(HTTPException):
        await _run_guard(guard, "STUDENT")
