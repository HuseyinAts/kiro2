"""B2B billing/DPA servis yardımcıları — Faz 1.

DPA-signed gate + entitlement (lisans özellikleri) + koltuk (seat) sayımı.
Tasarım: docs/audits/2026-07-03_b2b_readiness_design.md.
Async SQLAlchemy (raw SQL, hafif).
"""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def is_dpa_signed(db: AsyncSession, org_id: str) -> bool:
    """Okulun geçerli (status='signed') DPA'sı var mı? Aktivasyon ön koşulu."""
    row = (
        await db.execute(
            text(
                "SELECT 1 FROM billing_data_processing_agreements "
                "WHERE organization_id = :org AND status = 'signed' LIMIT 1"
            ),
            {"org": org_id},
        )
    ).first()
    return row is not None


async def get_active_license(db: AsyncSession, org_id: str) -> dict | None:
    """Okulun aktif lisansı (plan + koltuk + özellikler). Yoksa None."""
    row = (
        await db.execute(
            text(
                "SELECT l.id, l.status, l.seat_count, p.code, p.name, p.seat_limit, "
                "       p.features "
                "FROM organization_licenses l JOIN plans p ON p.id = l.plan_id "
                "WHERE l.organization_id = :org "
                "  AND l.status IN ('trial','active') "
                "ORDER BY (l.status='active') DESC, l.created_at DESC LIMIT 1"
            ),
            {"org": org_id},
        )
    ).first()
    if row is None:
        return None
    return {
        "license_id": str(row[0]),
        "status": str(row[1]),
        "seat_count": int(row[2]),
        "plan_code": str(row[3]),
        "plan_name": str(row[4]),
        "seat_limit": row[5],
        "features": row[6] or {},
    }


async def seat_usage(db: AsyncSession, org_id: str) -> dict:
    """Kullanılan koltuk = org'un aktif üye sayısı (org_memberships).

    Ayrı seat-tablosu YOK (YAGNI) — koltuk = aktif STUDENT/TEACHER üye sayımı.
    """
    used = (
        await db.execute(
            text(
                "SELECT count(*) FROM org_memberships "
                "WHERE organization_id = :org AND is_active = true "
                "  AND org_role IN ('STUDENT','TEACHER')"
            ),
            {"org": org_id},
        )
    ).scalar() or 0
    lic = await get_active_license(db, org_id)
    limit = lic["seat_limit"] if lic else None
    return {
        "used": int(used),
        "limit": limit,
        "over_limit": bool(limit is not None and used > limit),
    }


async def has_feature(db: AsyncSession, org_id: str, feature: str) -> bool:
    """Okulun aktif lisansı `feature`'ı içeriyor mu (entitlement kontrolü)."""
    lic = await get_active_license(db, org_id)
    if lic is None:
        return False
    return bool(lic["features"].get(feature))


async def sign_dpa(
    db: AsyncSession,
    org_id: str,
    signer_name: str | None,
    signer_email: str | None,
    version: str = "v1",
) -> str:
    """DPA'yı imzalar (append-only kayıt, audit izi). Yeni signed satır ekler.

    Aktivasyon ön koşulu: bu çağrıdan sonra is_dpa_signed True döner.
    RLS: organization_id GUC ile eşleşmeli (WITH CHECK); org_id get_current_tenant'tan.
    """
    dpa_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO billing_data_processing_agreements "
            "(id, organization_id, version, status, signer_name, signer_email, "
            " signed_at, created_at) VALUES "
            "(:i, :o, :v, 'signed', :sn, :se, now(), now())"
        ),
        {"i": dpa_id, "o": org_id, "v": version, "sn": signer_name, "se": signer_email},
    )
    await db.commit()
    return dpa_id


async def start_trial(
    db: AsyncSession, org_id: str, plan_code: str = "free"
) -> str | None:
    """Okul için trial lisansı başlatır. Zaten aktif/trial lisans varsa None (çakışma).

    plan_code bilinmiyorsa None. Aktivasyon gate'inin (DPA imzalı) arkasında çağrılır.
    """
    existing = await get_active_license(db, org_id)
    if existing is not None:
        return None
    pid = (
        await db.execute(
            text("SELECT id FROM plans WHERE code = :c AND is_active = true"),
            {"c": plan_code},
        )
    ).scalar()
    if pid is None:
        return None
    lic_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO organization_licenses (id, organization_id, plan_id, "
            "seat_count, status, created_at, updated_at) "
            "VALUES (:i, :o, :p, 0, 'trial', now(), now())"
        ),
        {"i": lic_id, "o": org_id, "p": pid},
    )
    await db.commit()
    return lic_id


async def list_invoices(db: AsyncSession, org_id: str) -> list[dict]:
    """Okulun faturaları (yeni→eski). Tenant-scoped."""
    rows = (
        await db.execute(
            text(
                "SELECT id, invoice_no, amount_try, currency, status, method, "
                "       issued_at, paid_at, created_at "
                "FROM invoices WHERE organization_id = :org "
                "ORDER BY created_at DESC LIMIT 200"
            ),
            {"org": org_id},
        )
    ).fetchall()
    return [
        {
            "invoice_id": str(r[0]),
            "invoice_no": str(r[1]),
            "amount_try": float(r[2]),
            "currency": str(r[3]),
            "status": str(r[4]),
            "method": str(r[5]),
            "issued_at": r[6].isoformat() if r[6] else None,
            "paid_at": r[7].isoformat() if r[7] else None,
            "created_at": r[8].isoformat() if r[8] else None,
        }
        for r in rows
    ]
