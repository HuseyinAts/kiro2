"""Faz 1 B2B — Kurum (org) lisanslama/DPA/faturalama endpoint'leri.

Tenant-scoped: tüm sorgular get_current_tenant'tan gelen organization_id ile
sınırlanır (istemci org param YOK → cross-tenant izolasyon + RLS defense-in-depth).

- DPA (KVKK veri işleme sözleşmesi): okul imzalamadan aktive edilemez.
- Lisans/koltuk/entitlement: aktif plan + koltuk kullanımı + özellikler.
- Fatura: havale/PO listesi.

Aktivasyon gate: `require_dpa_signed` — DPA imzalı değilse trial başlatılamaz.
B2C `billing_api.py` (users.is_premium/subscription) ile karışmasın diye
prefix `/api/v1/org/billing`.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import (
    get_current_tenant,
    get_db,
    require_dpa_signed,
    require_org_role,
)
from services import billing_service

router = APIRouter(prefix="/api/v1/org/billing", tags=["Organization Billing"])


# ---- Şemalar ----
class DpaStatusOut(BaseModel):
    organization_id: str
    signed: bool


class DpaSignIn(BaseModel):
    signer_name: str | None = Field(default=None, max_length=200)
    signer_email: str | None = Field(default=None, max_length=255)
    version: str = Field(default="v1", max_length=20)


class DpaSignOut(BaseModel):
    dpa_id: str
    signed: bool = True


class ActivationOut(BaseModel):
    organization_id: str
    dpa_signed: bool
    has_active_license: bool
    active: bool  # DPA imzalı + aktif lisans var


class LicenseOut(BaseModel):
    organization_id: str
    license: dict | None
    seat_usage: dict


class TrialStartOut(BaseModel):
    license_id: str
    plan_code: str
    status: str = "trial"


# ---- DPA ----
@router.get("/dpa", response_model=DpaStatusOut)
async def dpa_status(
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> DpaStatusOut:
    """Kurumun DPA imza durumu (herhangi bir üye görebilir)."""
    signed = await billing_service.is_dpa_signed(db, organization_id)
    return DpaStatusOut(organization_id=organization_id, signed=signed)


@router.post("/dpa/sign", response_model=DpaSignOut)
async def dpa_sign(
    payload: DpaSignIn,
    _membership: dict = Depends(require_org_role("SCHOOL_ADMIN")),
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> DpaSignOut:
    """DPA'yı imzalar (yalnız SCHOOL_ADMIN). Aktivasyon ön koşulu."""
    dpa_id = await billing_service.sign_dpa(
        db,
        organization_id,
        payload.signer_name,
        payload.signer_email,
        payload.version,
    )
    return DpaSignOut(dpa_id=dpa_id)


# ---- Aktivasyon özeti ----
@router.get("/activation", response_model=ActivationOut)
async def activation_status(
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> ActivationOut:
    """Aktivasyon özeti — neyin eksik olduğunu gösterir (gate'siz, üye görebilir)."""
    dpa_signed = await billing_service.is_dpa_signed(db, organization_id)
    lic = await billing_service.get_active_license(db, organization_id)
    has_lic = lic is not None
    return ActivationOut(
        organization_id=organization_id,
        dpa_signed=dpa_signed,
        has_active_license=has_lic,
        active=dpa_signed and has_lic,
    )


# ---- Lisans / koltuk / entitlement ----
@router.get("/license", response_model=LicenseOut)
async def license_info(
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> LicenseOut:
    """Aktif lisans + koltuk kullanımı + özellikler (herhangi bir üye)."""
    lic = await billing_service.get_active_license(db, organization_id)
    seats = await billing_service.seat_usage(db, organization_id)
    return LicenseOut(organization_id=organization_id, license=lic, seat_usage=seats)


@router.post("/license/start-trial", response_model=TrialStartOut)
async def start_trial(
    plan_code: str = "free",
    _membership: dict = Depends(require_org_role("SCHOOL_ADMIN")),
    organization_id: str = Depends(require_dpa_signed),
    db: AsyncSession = Depends(get_db),
) -> TrialStartOut:
    """Trial lisansı başlatır — SCHOOL_ADMIN + DPA imzalı ZORUNLU (aktivasyon gate).

    DPA imzalanmamışsa require_dpa_signed 403 verir (aktivasyon bekliyor).
    Zaten aktif lisans varsa veya plan bilinmiyorsa 409.
    """
    lic_id = await billing_service.start_trial(db, organization_id, plan_code)
    if lic_id is None:
        raise HTTPException(
            status_code=409,
            detail="Trial başlatılamadı: zaten aktif lisans var veya plan bilinmiyor.",
        )
    return TrialStartOut(license_id=lic_id, plan_code=plan_code)


# ---- Fatura ----
@router.get("/invoices")
async def list_invoices(
    _membership: dict = Depends(require_org_role("SCHOOL_ADMIN")),
    organization_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Kurumun faturaları (yalnız SCHOOL_ADMIN, tenant-scoped)."""
    return await billing_service.list_invoices(db, organization_id)
