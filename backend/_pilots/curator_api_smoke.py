"""
Curator API Smoke Test — Faz 3.1

Production DB'ye (kiro2 @ port 5434) bağlanır ve curator endpoint'lerinin
gerçek veriyle çalıştığını doğrular. Read-only — verdict POST etmez,
çünkü o gerçek satır mutate eder.

Çalıştırma:
    cd backend && python _pilots/curator_api_smoke.py

Çıktı:
    - GET /queue?status=bronze_clean → total + 3 örnek soru
    - GET /stats → bronze_clean_count, verified_count vb.
    - GET /queue?status=invalid_xxx → 400 doğrulama
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from types import SimpleNamespace  # noqa: E402

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from api.curator import router as curator_router  # noqa: E402
from core.dependencies import get_current_admin_user, get_db  # noqa: E402


def _override_admin():
    return SimpleNamespace(
        id="smoke-admin",
        username="smoke-admin",
        role="admin",
        email="smoke@test.com",
        permissions=[],
        exp=None,
    )


async def _real_db():
    """Production DB'ye bağlan (kiro2 @ 5434)."""
    from core.database import get_async_session

    async for session in get_async_session():
        yield session


async def main() -> int:
    app = FastAPI()
    app.include_router(curator_router)
    app.dependency_overrides[get_current_admin_user] = _override_admin
    app.dependency_overrides[get_db] = _real_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        print("=" * 60)
        print("Curator API smoke test (production DB read-only)")
        print("=" * 60)

        # 1. /queue?status=bronze_clean
        print("\n[1] GET /api/v1/curator/queue?status=bronze_clean&per_page=3")
        r = await client.get(
            "/api/v1/curator/queue",
            params={"status": "bronze_clean", "per_page": 3},
        )
        print(f"  status_code: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"  total: {d['total']}")
            print(f"  returned: {len(d['items'])}")
            for it in d["items"]:
                print(
                    f"    {it['id'][:8]}... "
                    f"[{it['subject_area']}/{it['difficulty_level']}] "
                    f"correct={it['correct_answer']} "
                    f"img={'YES' if it['image_url'] else 'NO'}"
                )
        else:
            print(f"  ERROR: {r.text[:300]}")
            return 1

        # 2. /stats
        print("\n[2] GET /api/v1/curator/stats")
        r = await client.get("/api/v1/curator/stats")
        print(f"  status_code: {r.status_code}")
        if r.status_code == 200:
            print(f"  body: {json.dumps(r.json(), indent=2)}")
        else:
            print(f"  ERROR: {r.text[:300]}")
            return 1

        # 3. Invalid status → 400
        print("\n[3] GET /api/v1/curator/queue?status=invalid_xxx (expect 400)")
        r = await client.get("/api/v1/curator/queue", params={"status": "invalid_xxx"})
        print(f"  status_code: {r.status_code} (expected 400)")
        assert r.status_code == 400, r.text

        # 4. has_diagram filter
        print(
            "\n[4] GET /api/v1/curator/queue"
            "?status=bronze_clean&has_diagram=true&per_page=2"
        )
        r = await client.get(
            "/api/v1/curator/queue",
            params={
                "status": "bronze_clean",
                "has_diagram": "true",
                "per_page": 2,
            },
        )
        print(f"  status_code: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"  total: {d['total']}")
            assert all(it["image_url"] for it in d["items"]), (
                "has_diagram=true should only return items with image_url"
            )

        print("\n" + "=" * 60)
        print("SMOKE TEST PASSED")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
