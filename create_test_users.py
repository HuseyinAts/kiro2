#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create test student accounts for Phase 1 testing
"""
import sys
import os
import asyncio
from pathlib import Path
import uuid
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

def log(msg):
    print(msg, flush=True)

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def create_test_users():
    """Create test student accounts"""
    log("="*80)
    log("CREATE TEST USERS - Phase 1")
    log("="*80)
    log("")

    try:
        from core.database import db_manager
        from sqlalchemy import text
        import bcrypt

        await db_manager.initialize()
        log("[✓] Database connection established")
        log("")

        # Test users to create
        test_users = [
            {
                "ad": "Zeynep",
                "soyad": "Kaya",
                "email": "zeynep@test.com",
                "telefon": "5551234567",
                "rol": "OGRENCI",
                "sinif": 12,
                "okul": "Atatürk Anadolu Lisesi",
                "alan": "SAY",  # Sayısal
                "hedef_universite": "ODTÜ",
                "hedef_bolum": "Bilgisayar Mühendisliği"
            },
            {
                "ad": "Can",
                "soyad": "Özkan",
                "email": "can@test.com",
                "telefon": "5557654321",
                "rol": "OGRENCI",
                "sinif": 12,
                "okul": "Fen Lisesi",
                "alan": "SAY",  # Sayısal
                "hedef_universite": "İTÜ",
                "hedef_bolum": "Makine Mühendisliği"
            }
        ]

        # Simple password: "test123" hashed with bcrypt
        password = "test123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        created = 0
        skipped = 0
        errors = []

        async with db_manager.get_session() as session:
            for user_data in test_users:
                try:
                    log(f"[→] Creating user: {user_data['ad']} {user_data['soyad']} ({user_data['email']})")

                    # Check if user exists
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM kullanicilar WHERE email = :email"),
                        {"email": user_data['email']}
                    )
                    exists = result.scalar() > 0

                    if exists:
                        log(f"  [SKIP] User already exists")
                        skipped += 1
                        continue

                    # Create user
                    user_id = str(uuid.uuid4())
                    await session.execute(
                        text("""
                            INSERT INTO kullanicilar (
                                id, ad, soyad, email, telefon, rol, parola_hash,
                                aktif, sinif, okul, alan, hedef_universite, hedef_bolum,
                                kayit_tarihi, guncelleme_tarihi
                            ) VALUES (
                                CAST(:id AS uuid), :ad, :soyad, :email, :telefon, :rol, :parola_hash,
                                true, :sinif, :okul, :alan, :hedef_universite, :hedef_bolum,
                                NOW(), NOW()
                            )
                        """),
                        {
                            "id": user_id,
                            "ad": user_data['ad'],
                            "soyad": user_data['soyad'],
                            "email": user_data['email'],
                            "telefon": user_data['telefon'],
                            "rol": user_data['rol'],
                            "parola_hash": password_hash,
                            "sinif": user_data['sinif'],
                            "okul": user_data['okul'],
                            "alan": user_data['alan'],
                            "hedef_universite": user_data['hedef_universite'],
                            "hedef_bolum": user_data['hedef_bolum']
                        }
                    )

                    await session.commit()
                    created += 1
                    log(f"  [✓] User created (ID: {user_id[:8]}...)")
                    log(f"      Email: {user_data['email']} | Password: {password}")

                except Exception as e:
                    error_msg = f"User {user_data['email']} failed: {str(e)[:100]}"
                    log(f"  [ERROR] {error_msg}")
                    errors.append(error_msg)
                    await session.rollback()

        log("")
        log("="*80)
        log("SUMMARY")
        log("="*80)
        log(f"\nTotal Users to Create: {len(test_users)}")
        log(f"Created:               {created}")
        log(f"Skipped (exists):      {skipped}")
        log(f"Errors:                {len(errors)}")
        log("")

        if created > 0:
            log(f"[✓✓✓] {created} new test users created!")
            log("")
            log("Login Credentials:")
            log("  Email: zeynep@test.com | Password: test123")
            log("  Email: can@test.com    | Password: test123")
            log("")

        # Verify total user count
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM kullanicilar WHERE rol = 'OGRENCI'")
            )
            student_count = result.scalar()

            result = await session.execute(
                text("SELECT COUNT(*) FROM kullanicilar")
            )
            total_count = result.scalar()

            log(f"[INFO] Total students in database: {student_count}")
            log(f"[INFO] Total users in database:    {total_count}")

        log("="*80)

        await db_manager.close()

    except Exception as e:
        log(f"[ERROR] Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_users())
