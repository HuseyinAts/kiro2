"""B2B billing/DPA servis yardımcıları — Faz 1.

DPA-signed gate + entitlement (lisans özellikleri) + koltuk (seat) sayımı.
Tasarım: docs/audits/2026-07-03_b2b_readiness_design.md.
Async SQLAlchemy (raw SQL, hafif).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def is_dpa_signed(db: AsyncSession, org_id: str) -> bool:
    """Okulun geçerli (status='signed') DPA'sı var mı? Aktivasyon ön koşulu."""
    row = (
        await db.execute(
            text(
                "SELECT 1 FROM data_processing_agreements "
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
