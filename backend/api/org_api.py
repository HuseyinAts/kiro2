"""Faz 0 Step 5 — Organizasyon (tenant) yönetim endpoint'leri.

REFERANS WIRING: tenant primitiflerini gerçek endpoint'e bağlar —
get_current_tenant (tenant bağlamı) + require_org_role (kurum-içi yetki) +
tenant-scoped sorgu (cross-tenant izolasyon). Diğer org-scoped endpoint'ler
bu deseni kopyalar.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session as get_db
from core.dependencies import get_current_tenant, require_org_role
from services import org_service

router = APIRouter(prefix="/api/v1/org", tags=["Organization"])


class OrgMemberOut(BaseModel):
    user_id: str
    email: str | None = None
    org_role: str


class OrgMemberCreate(BaseModel):
    email: str
    org_role: str


class OrgMemberUpdate(BaseModel):
    org_role: str | None = None
    is_active: bool | None = None


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


@router.post("/members", response_model=OrgMemberOut, status_code=201)
async def add_org_member(
    body: OrgMemberCreate,
    _membership: dict = Depends(require_org_role("SCHOOL_ADMIN")),
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> OrgMemberOut:
    """Mevcut platform kullanıcısını (email ile) kuruma ekler — YALNIZ SCHOOL_ADMIN.

    404 email-yok, 409 zaten-üye / başka-kuruma-ait / koltuk-dolu, 400 geçersiz-rol.
    """
    try:
        m = await org_service.add_member(db, organization_id, body.email, body.org_role)
    except org_service.OrgMemberError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    return OrgMemberOut(user_id=m["user_id"], email=m["email"], org_role=m["org_role"])


@router.patch("/members/{user_id}", response_model=OrgMemberOut)
async def update_org_member(
    user_id: str,
    body: OrgMemberUpdate,
    _membership: dict = Depends(require_org_role("SCHOOL_ADMIN")),
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> OrgMemberOut:
    """Üye rolünü/aktifliğini değiştirir — YALNIZ SCHOOL_ADMIN.

    404 üye-yok, 409 son-yönetici / koltuk-dolu.
    """
    try:
        m = await org_service.update_member(
            db,
            organization_id,
            user_id,
            org_role=body.org_role,
            is_active=body.is_active,
        )
    except org_service.OrgMemberError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    return OrgMemberOut(user_id=m["user_id"], email=None, org_role=m["org_role"])


@router.delete("/members/{user_id}", status_code=204)
async def remove_org_member(
    user_id: str,
    _membership: dict = Depends(require_org_role("SCHOOL_ADMIN")),
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Üyeyi soft-deaktive eder (is_active=false) — YALNIZ SCHOOL_ADMIN.

    404 aktif-üye-yok, 409 son-yönetici.
    """
    try:
        await org_service.remove_member(db, organization_id, user_id)
    except org_service.OrgMemberError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
