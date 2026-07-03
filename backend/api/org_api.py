"""Faz 0 Step 5 — Organizasyon (tenant) yönetim endpoint'leri.

REFERANS WIRING: tenant primitiflerini gerçek endpoint'e bağlar —
get_current_tenant (tenant bağlamı) + require_org_role (kurum-içi yetki) +
tenant-scoped sorgu (cross-tenant izolasyon). Diğer org-scoped endpoint'ler
bu deseni kopyalar.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session as get_db
from core.dependencies import get_current_tenant, require_org_role

router = APIRouter(prefix="/api/v1/org", tags=["Organization"])


class OrgMemberOut(BaseModel):
    user_id: str
    email: str | None = None
    org_role: str


class OrgInfoOut(BaseModel):
    organization_id: str
    name: str
    status: str
    member_count: int


@router.get("/members", response_model=list[OrgMemberOut])
async def list_org_members(
    _membership: dict = Depends(require_org_role("SCHOOL_ADMIN", "TEACHER")),
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[OrgMemberOut]:
    """Kurum üyelerini listeler — YALNIZ çağıranın kendi kurumu (tenant-scoped).

    Cross-tenant izolasyon: organization_id get_current_tenant'tan gelir, istemci
    parametresinden DEĞİL → başka kurumun üyeleri sorgulanamaz.
    """
    rows = (
        await db.execute(
            text(
                "SELECT m.user_id, u.email, m.org_role "
                "FROM org_memberships m JOIN users u ON u.id = m.user_id "
                "WHERE m.organization_id = :org AND m.is_active = true "
                "ORDER BY m.org_role, u.email LIMIT 500"
            ),
            {"org": organization_id},
        )
    ).fetchall()
    return [
        OrgMemberOut(user_id=str(r[0]), email=r[1], org_role=str(r[2])) for r in rows
    ]


@router.get("/info", response_model=OrgInfoOut)
async def org_info(
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> OrgInfoOut:
    """Çağıranın kendi kurum bilgisi (tenant-scoped)."""
    row = (
        await db.execute(
            text(
                "SELECT o.id, o.name, o.status, "
                "(SELECT count(*) FROM org_memberships m "
                " WHERE m.organization_id = o.id AND m.is_active) AS cnt "
                "FROM organizations o WHERE o.id = :org"
            ),
            {"org": organization_id},
        )
    ).first()
    if row is None:
        # get_current_tenant zaten 403 verir; buraya normalde ulaşılmaz
        return OrgInfoOut(
            organization_id=organization_id,
            name="",
            status="unknown",
            member_count=0,
        )
    return OrgInfoOut(
        organization_id=str(row[0]),
        name=str(row[1]),
        status=str(row[2]),
        member_count=int(row[3]),
    )
