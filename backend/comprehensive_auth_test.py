#!/usr/bin/env python3
"""
Comprehensive authentication test
Tests both database password verification and API login
"""
import asyncio
import os
import sys

import httpx

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select

from api.auth import pwd_context
from core.database import db_manager
from models.database import User


async def test_comprehensive():
    """Comprehensive authentication test"""
    print("="*60)
    print("COMPREHENSIVE AUTHENTICATION TEST")
    print("="*60)

    # Test 1: Database user check
    print("\n[TEST 1] Database User Verification")
    print("-"*60)
    await db_manager.initialize()

    async with db_manager.get_session() as db:
        result = await db.execute(select(User).where(User.email == 'test@kiro2.com'))
        user = result.scalar_one_or_none()

        if not user:
            print("FAILED: User not found in database!")
            return

        print(f"  Email: {user.email}")
        print(f"  Role: {user.role.value}")
        print(f"  Active: {user.is_active}")
        print(f"  Hash format: {user.password_hash[:10]}...")

        # Test password verification
        test_password = "Test123!"
        is_valid = pwd_context.verify(test_password, user.password_hash)
        print(f"\n  Password verification with '{test_password}': {'PASS' if is_valid else 'FAIL'}")

        if not is_valid:
            print("  FAILED: Password verification failed!")
            return

    await db_manager.close()

    # Test 2: API Login
    print("\n[TEST 2] API Login Test")
    print("-"*60)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"email": "test@kiro2.com", "sifre": "Test123!"},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                print(f"  Status: {response.status_code} OK")
                print(f"  Access Token: {data['access_token'][:20]}...")
                print(f"  Token Type: {data['token_type']}")
                print(f"  Expires In: {data['expires_in']}s")
                print(f"  User ID: {data['kullanici']['kullanici_id']}")
                print(f"  User Role: {data['kullanici']['rol']}")
                print("\n  API Login: PASS")
            else:
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text}")
                print("\n  API Login: FAIL")
                return

        except Exception as e:
            print(f"  Error: {e!s}")
            print("\n  API Login: FAIL")
            return

    # Final Summary
    print("\n" + "="*60)
    print("SUMMARY: ALL TESTS PASSED")
    print("="*60)
    print("\nAuthentication System Status:")
    print("  Database User: EXISTS")
    print("  Password Hash: VALID (bcrypt)")
    print("  Password Verification: WORKING")
    print("  API Login: WORKING")
    print("  JWT Token Generation: WORKING")
    print("\nTest user credentials:")
    print("  Email: test@kiro2.com")
    print("  Password: Test123!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_comprehensive())
