"""KVKK Md.7 — Silme (unutulma) hakkı: kullanıcı PII anonimleştirme.

Hard-delete DEĞİL, **anonim hale getirme** (KVKK m.28: anonimleştirilmiş veri
kişisel veri sayılmaz; FK-güvenli; istatistiksel/eğitim verisi yasal olarak
kalabilir). Anonimleştirmeden ÖNCE orijinal PII `kvkk_erasure_backup`'a yazılır
(geri-alınabilir + silme-işlemi kanıtı).

Yalnız APPROVED (admin onaylı) talep için executor'dan çağrılır — insan-döngüsü.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# users tablosu anonimleştirilecek PII kolonları (id/role/org/istatistik KORUNUR).
_USERS_PII_COLS = [
    "email",
    "username",
    "password_hash",
    "secret_2fa",
    "backup_codes_hashed",
    "first_name",
    "last_name",
    "phone",
    "birth_date",
    "is_active",
    "is_verified",
]

# Profil tabloları → NULL'lanacak PII kolonları.
_PROFILE_PII: dict[str, list[str]] = {
    "student_profiles": ["veli_email", "school_name"],
    "teacher_profiles": ["school_name"],
    "parent_profiles": ["children_ids"],
}


async def _backup(
    db: AsyncSession, request_id: str, user_id: str, table_name: str, values: dict
) -> None:
    """Anonimleştirme öncesi orijinal PII'ı sakla (reversible + kanıt)."""
    await db.execute(
        text(
            "INSERT INTO kvkk_erasure_backup "
            "(id, request_id, user_id, table_name, original_values, created_at) "
            "VALUES (:i, :r, :u, :t, :v, now())"
        ),
        {
            "i": str(uuid.uuid4()),
            "r": request_id,
            "u": user_id,
            "t": table_name,
            "v": json.dumps(values, default=str, ensure_ascii=False),
        },
    )


async def anonymize_user(db: AsyncSession, user_id: str, request_id: str) -> dict:
    """Kullanıcının PII'ını anonimleştir (backup'lı). Değiştirilen tablo sayısını döner.

    users: kimlik alanları anonim + is_active/is_verified=false. Profiller: PII NULL.
    email/username çakışmasın diye deterministik hash-suffix ('erased_<h8>').
    """
    h = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    touched: dict[str, int] = {}

    # 1) users
    row = (
        (
            await db.execute(
                text(f"SELECT {', '.join(_USERS_PII_COLS)} FROM users WHERE id = :u"),
                {"u": user_id},
            )
        )
        .mappings()
        .first()
    )
    if row:
        await _backup(db, request_id, user_id, "users", dict(row))
        await db.execute(
            text(
                "UPDATE users SET "
                "email = :email, username = :username, password_hash = 'ERASED', "
                "secret_2fa = NULL, backup_codes_hashed = NULL, "
                "first_name = 'Silinmiş', last_name = 'Kullanıcı', "
                "phone = NULL, birth_date = NULL, "
                "is_active = false, is_verified = false, updated_at = now() "
                "WHERE id = :u"
            ),
            {
                "email": f"erased_{h}@anonymized.invalid",
                "username": f"erased_{h}",
                "u": user_id,
            },
        )
        touched["users"] = 1

    # 2) profiller (varsa)
    for tbl, cols in _PROFILE_PII.items():
        r = (
            (
                await db.execute(
                    text(f"SELECT {', '.join(cols)} FROM {tbl} WHERE user_id = :u"),
                    {"u": user_id},
                )
            )
            .mappings()
            .first()
        )
        if r:
            await _backup(db, request_id, user_id, tbl, dict(r))
            set_clause = ", ".join(f"{c} = NULL" for c in cols)
            await db.execute(
                text(
                    f"UPDATE {tbl} SET {set_clause}, updated_at = now() "
                    f"WHERE user_id = :u"
                ),
                {"u": user_id},
            )
            touched[tbl] = 1

    await db.commit()
    return touched
