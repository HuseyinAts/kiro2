"""B2B okul onboarding — org üye yönetimi servis mantığı (Faz 1).

`add_member` / `update_member` / `remove_member`: mevcut platform kullanıcısını org'a
ekle, rolünü değiştir, soft-deaktive et. İş-kuralı guard'ları:

- **cross-tenant claim**: kullanıcı başka bir *gerçek* kuruma aitse eklenemez (409).
  Ekleme, kullanıcının `users.organization_id`'sini bu org'a claim eder ki tenant
  çözümü (get_current_tenant) doğru org'a düşsün.
- **koltuk (seat)**: yalnız STUDENT/TEACHER lisans `seat_limit`'ini tüketir; aşarsa 409
  (`billing_service.seat_usage`). Lisans yoksa (limit=None) enforce edilmez.
- **son yönetici (lockout)**: org'un tek aktif SCHOOL_ADMIN'i demote/deaktive edilemez (409).

Tasarım: `org_api.py` (thin endpoint) bu servisi çağırır; `get_current_tenant` org_id
verir (RLS GUC set eder). Servis her sorguda `organization_id` filtreler — defense-in-depth.
Async SQLAlchemy (raw SQL, billing_service deseni).
"""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services import billing_service

# Faz 0 retrofit: tüm eski kullanıcılar bu tek-kiracılı org'a bağlandı (claim edilebilir).
LEGACY_ORG = "org_legacy_default"
VALID_ROLES = {"SCHOOL_ADMIN", "TEACHER", "STUDENT", "PARENT", "OBSERVER"}
_SEAT_ROLES = {"STUDENT", "TEACHER"}


class OrgMemberError(Exception):
    """Üye yönetimi iş-kuralı ihlali. status_code + detail endpoint'te HTTP'ye çevrilir."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _norm_role(role: str | None) -> str:
    r = (role or "").strip().upper()
    if r not in VALID_ROLES:
        raise OrgMemberError(400, f"geçersiz org rolü: {role}")
    return r


async def _seat_guard(db: AsyncSession, org_id: str, role: str) -> None:
    """STUDENT/TEACHER eklerken lisans koltuk limitini aşma → 409."""
    if role not in _SEAT_ROLES:
        return
    su = await billing_service.seat_usage(db, org_id)
    if su["limit"] is not None and su["used"] >= su["limit"]:
        raise OrgMemberError(409, "lisans koltuk limiti dolu")


async def _serialize_org(db: AsyncSession, org_id: str) -> None:
    """Aynı org'un eşzamanlı üye mutasyonlarını serialize et (transaction-scoped
    advisory lock; commit/rollback'te otomatik bırakılır). check-then-act TOCTOU
    yarışlarını kapatır: son-yönetici lockout, koltuk limiti, eşzamanlı çift-ekleme.

    Not: RLS tenant GUC bu (çalışan) session'a set EDİLMEZ — claim akışı LEGACY_ORG
    üyeliğini deaktive eden cross-org bir yazma içerir (GUC set edilseydi RLS bunu
    görünmez kılardı). İzolasyon her sorgudaki açık `organization_id` filtresiyle sağlanır.
    """
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:o))"), {"o": org_id})


async def _active_admin_count(db: AsyncSession, org_id: str) -> int:
    return int(
        (
            await db.execute(
                text(
                    "SELECT count(*) FROM org_memberships WHERE organization_id=:o "
                    "AND is_active=true AND org_role='SCHOOL_ADMIN'"
                ),
                {"o": org_id},
            )
        ).scalar()
        or 0
    )


async def add_member(db: AsyncSession, org_id: str, email: str, org_role: str) -> dict:
    """Mevcut platform kullanıcısını (email ile) org'a ekle/reaktive et.

    404 email-yok, 409 zaten-üye / başka-kuruma-ait / koltuk-dolu, 400 geçersiz-rol.
    """
    role = _norm_role(org_role)
    email = (
        (email or "").strip().lower()
    )  # emailler lowercase saklanır (case-insensitive)
    if not email:
        raise OrgMemberError(400, "e-posta zorunlu")

    await _serialize_org(db, org_id)  # TOCTOU: koltuk/çift-ekleme yarışını serialize et

    urow = (
        await db.execute(
            text("SELECT id, organization_id FROM users WHERE email=:e LIMIT 1"),
            {"e": email},
        )
    ).first()
    if urow is None:
        raise OrgMemberError(404, "bu e-posta ile kayıtlı kullanıcı yok")
    uid, current_org = str(urow[0]), urow[1]

    # cross-tenant claim guard — başka gerçek kuruma aitse çalma
    if current_org and current_org not in (LEGACY_ORG, org_id):
        raise OrgMemberError(409, "kullanıcı başka bir kuruma ait")

    m = (
        await db.execute(
            text(
                "SELECT id, is_active FROM org_memberships "
                "WHERE organization_id=:o AND user_id=:u LIMIT 1"
            ),
            {"o": org_id, "u": uid},
        )
    ).first()
    if m is not None and m[1]:
        raise OrgMemberError(409, "kullanıcı zaten bu kurumun üyesi")

    await _seat_guard(db, org_id, role)

    try:
        if m is not None:  # inaktif üyelik → reaktive et
            await db.execute(
                text(
                    "UPDATE org_memberships SET is_active=true, org_role=:r WHERE id=:i"
                ),
                {"r": role, "i": str(m[0])},
            )
        else:
            await db.execute(
                text(
                    "INSERT INTO org_memberships "
                    "(id,organization_id,user_id,org_role,is_active,created_at) "
                    "VALUES (:i,:o,:u,:r,true,now())"
                ),
                {"i": str(uuid.uuid4()), "o": org_id, "u": uid, "r": role},
            )

        if current_org != org_id:  # tenant claim — üye bu org'a düşsün
            # stale (başka org) aktif üyelikleri kapat → tek-aktif-üyelik = users.org
            # (dual-membership cross-tenant authz açığını kapatır)
            await db.execute(
                text(
                    "UPDATE org_memberships SET is_active=false "
                    "WHERE user_id=:u AND organization_id <> :o AND is_active=true"
                ),
                {"u": uid, "o": org_id},
            )
            await db.execute(
                text("UPDATE users SET organization_id=:o WHERE id=:u"),
                {"o": org_id, "u": uid},
            )
        await db.commit()
    except IntegrityError as exc:  # eşzamanlı çift-ekleme (uq_org_membership)
        await db.rollback()
        raise OrgMemberError(409, "kullanıcı zaten bu kurumun üyesi") from exc
    return {"user_id": uid, "email": email, "org_role": role}


async def update_member(
    db: AsyncSession,
    org_id: str,
    user_id: str,
    org_role: str | None = None,
    is_active: bool | None = None,
) -> dict:
    """Üyenin rolünü ve/veya aktifliğini değiştir. 404 üye-yok, 409 son-admin / koltuk."""
    await _serialize_org(db, org_id)  # TOCTOU: son-admin sayımı yarışını serialize et
    m = (
        await db.execute(
            text(
                "SELECT id, org_role, is_active FROM org_memberships "
                "WHERE organization_id=:o AND user_id=:u LIMIT 1"
            ),
            {"o": org_id, "u": user_id},
        )
    ).first()
    if m is None:
        raise OrgMemberError(404, "üye bulunamadı")
    mid, cur_role, cur_active = str(m[0]), str(m[1]), bool(m[2])

    new_role = _norm_role(org_role) if org_role is not None else cur_role
    new_active = cur_active if is_active is None else bool(is_active)

    # son yönetici lockout — org'u kilitleme (and short-circuit: sayım sadece gerekince)
    if (
        cur_role == "SCHOOL_ADMIN"
        and (new_role != "SCHOOL_ADMIN" or not new_active)
        and await _active_admin_count(db, org_id) <= 1
    ):
        raise OrgMemberError(409, "kurumun son yöneticisi kaldırılamaz")

    # koltuk: yeni durumda tüketiyor & önceden tüketmiyorsa kontrol et
    was_consuming = cur_active and cur_role in _SEAT_ROLES
    will_consume = new_active and new_role in _SEAT_ROLES
    if will_consume and not was_consuming:
        await _seat_guard(db, org_id, new_role)

    await db.execute(
        text("UPDATE org_memberships SET org_role=:r, is_active=:a WHERE id=:i"),
        {"r": new_role, "a": new_active, "i": mid},
    )
    await db.commit()
    return {"user_id": str(user_id), "org_role": new_role, "is_active": new_active}


async def remove_member(db: AsyncSession, org_id: str, user_id: str) -> None:
    """Üyeyi soft-deaktive et (is_active=false). 404 aktif-üye-yok, 409 son-admin."""
    await _serialize_org(db, org_id)  # TOCTOU: son-admin sayımı yarışını serialize et
    m = (
        await db.execute(
            text(
                "SELECT id, org_role FROM org_memberships "
                "WHERE organization_id=:o AND user_id=:u AND is_active=true LIMIT 1"
            ),
            {"o": org_id, "u": user_id},
        )
    ).first()
    if m is None:
        raise OrgMemberError(404, "aktif üye bulunamadı")
    if str(m[1]) == "SCHOOL_ADMIN" and await _active_admin_count(db, org_id) <= 1:
        raise OrgMemberError(409, "kurumun son yöneticisi kaldırılamaz")
    await db.execute(
        text("UPDATE org_memberships SET is_active=false WHERE id=:i"),
        {"i": str(m[0])},
    )
    await db.commit()
