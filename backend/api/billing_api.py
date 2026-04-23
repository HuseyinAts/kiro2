"""
Billing MVP — abonelik özeti + geliştirici webhook.

Gerçek ödeme sağlayıcısı (iyzico/PayTR vb.) entegrasyonu: bu modülü
webhook imzalama ve idempotency ile genişletin. Şimdilik:
- `billing_subscriptions` satırı
- `users.is_premium` bayrağı (mevcut rate limit / ürün guard'ları ile uyumlu)
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import AuthenticatedUser, get_current_user, get_db

router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])


class BillingMeResponse(BaseModel):
    user_id: str
    is_premium: bool
    plan_code: str
    subscription_status: str
    provider: str | None = None
    current_period_end: str | None = None


class BillingWebhookPayload(BaseModel):
    """İç webhook (sandbox); üretimde sağlayıcı şeması ile değiştirin."""

    user_id: str = Field(..., min_length=1)
    plan_code: str = Field(default="pro", min_length=1)
    status: str = Field(
        default="active",
        description="active | inactive | canceled",
    )


@router.get("/me", response_model=BillingMeResponse)
async def billing_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BillingMeResponse:
    uid = str(current_user.id)

    urow = (
        await db.execute(
            text("SELECT is_premium FROM users WHERE id = :uid"),
            {"uid": uid},
        )
    ).first()
    prem = bool(urow[0]) if urow is not None else False

    row = (
        await db.execute(
            text(
                """
                SELECT plan_code, status, provider, current_period_end
                FROM billing_subscriptions
                WHERE user_id = :uid
                """
            ),
            {"uid": uid},
        )
    ).mappings().first()

    if not row:
        return BillingMeResponse(
            user_id=uid,
            is_premium=prem,
            plan_code="free",
            subscription_status="inactive",
        )

    pe = row["current_period_end"]
    return BillingMeResponse(
        user_id=uid,
        is_premium=prem,
        plan_code=str(row["plan_code"] or "free"),
        subscription_status=str(row["status"] or "inactive"),
        provider=row["provider"],
        current_period_end=pe.isoformat() if pe is not None else None,
    )


@router.post("/webhook")
async def billing_webhook(
    payload: BillingWebhookPayload,
    db: AsyncSession = Depends(get_db),
    x_kiro2_billing_secret: str | None = Header(default=None, alias="X-Kiro2-Billing-Secret"),
) -> dict[str, Any]:
    """
    Paylaşımlı sır ile korunan iç webhook. Üretimde sağlayıcı imzası kullanın.
    """
    expected = os.getenv("BILLING_WEBHOOK_SECRET", "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing webhook not configured (BILLING_WEBHOOK_SECRET)",
        )
    if not x_kiro2_billing_secret or x_kiro2_billing_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid billing webhook secret",
        )

    uid = payload.user_id.strip()
    active = payload.status.lower() == "active"
    sub_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kiro2.billing.{uid}"))

    await db.execute(
        text(
            """
            INSERT INTO billing_subscriptions (
                id, user_id, plan_code, status, provider, updated_at
            ) VALUES (
                :id, :uid, :plan,
                CASE WHEN :active THEN 'active' ELSE 'inactive' END,
                'internal', now()
            )
            ON CONFLICT (user_id) DO UPDATE SET
                plan_code = EXCLUDED.plan_code,
                status = EXCLUDED.status,
                provider = EXCLUDED.provider,
                updated_at = now()
            """
        ),
        {
            "id": sub_id,
            "uid": uid,
            "plan": payload.plan_code if active else "free",
            "active": active,
        },
    )
    await db.execute(
        text("UPDATE users SET is_premium = :p WHERE id = :uid"),
        {"p": active, "uid": uid},
    )
    await db.commit()

    return {"success": True, "user_id": uid, "is_premium": active}
