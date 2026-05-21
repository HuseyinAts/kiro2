"""
Curator UI E2E HTTP-only Smoke Test (Session 178 hot-patched canli backend)

Akis:
  1. Admin user dogrula  (DB)
  2. Login -> JWT Bearer token
  3. GET /api/v1/curator/stats           (200, bronze_clean_count)
  4. GET /api/v1/curator/queue?status=bronze_clean&limit=3   (200, items[])
  5. DB snapshot (pre-verdict): quality_review_status = 'bronze_clean'
  6. POST /api/v1/curator/verdict {verify, velocity=10}     (200)
  7. DB snapshot (post-verdict): quality_review_status = 'auto_judged_high'
  8. Audit trail: pipeline_metadata.curator_verdict JSON kontrol
  9. Audit log: audit_logs satiri kontrol
 10. ROLLBACK: state'i bronze_clean'e geri al + audit log sil

Kisitlar:
  - Backend canli (Docker), restart YAPMA
  - DB temizligi ZORUNLU (yalniz test satiri rollback)
  - Production data korunmali
  - Exit 0 = success, 1 = fail
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from typing import Any

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

import httpx
import psycopg2
import psycopg2.extras

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
DSN = "postgresql://postgres:1470@localhost:5434/kiro2"
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@kiro2.com"
ADMIN_PASSWORD = "Kiro2Beta2026@x"

# Test verdict parameters
TEST_VERDICT = "verify"
TEST_VELOCITY = 10
TEST_NOTES = "E2E smoke test - automated rollback"

EXPECTED_NEW_STATUS = "auto_judged_high"  # verify -> auto_judged_high


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
class StepFail(Exception):
    """A test step failed."""


def _print_step(num: int, title: str) -> None:
    print(f"\n[{num}] {title}")
    print("-" * 70)


def _print_pass(msg: str) -> None:
    print(f"  PASS  {msg}")


def _print_fail(msg: str) -> None:
    print(f"  FAIL  {msg}")


def _print_info(msg: str) -> None:
    print(f"  INFO  {msg}")


def _db_connect() -> psycopg2.extensions.connection:
    return psycopg2.connect(DSN)


def _db_fetchone(sql: str, params: tuple | None = None) -> dict[str, Any] | None:
    with (
        _db_connect() as conn,
        conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur,
    ):
        cur.execute(sql, params or ())
        row = cur.fetchone()
        return dict(row) if row else None


def _db_execute(sql: str, params: tuple | None = None) -> int:
    with _db_connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        affected = cur.rowcount
        conn.commit()
        return affected


# -----------------------------------------------------------------------------
# Steps
# -----------------------------------------------------------------------------
def step_check_admin() -> str:
    """Step 1: admin user mevcut mu?"""
    _print_step(1, "Admin user kontrolu")

    row = _db_fetchone(
        "SELECT id, email, role FROM users WHERE email = %s AND role = 'ADMIN' LIMIT 1",
        (ADMIN_EMAIL,),
    )
    if row is None:
        raise StepFail(
            f"Admin user not found (email={ADMIN_EMAIL}). "
            f"Run: python backend/scripts/seed_mvp_data.py"
        )

    admin_id = str(row["id"])
    _print_pass(f"admin found: id={admin_id} email={row['email']}")
    return admin_id


def step_login(client: httpx.Client) -> str:
    """Step 2: login -> Bearer token."""
    _print_step(2, "Login (POST /api/v1/auth/login)")

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise StepFail(f"login failed: {resp.status_code} {resp.text[:300]}")

    body = resp.json()
    token = body.get("access_token") or body.get("token")
    if not token:
        raise StepFail(f"no token in response: keys={list(body.keys())}")

    role = body.get("user", {}).get("rol") or body.get("kullanici", {}).get("rol")
    _print_pass(f"login OK, role={role}, token length={len(token)}")
    return token


def step_stats(client: httpx.Client, token: str) -> dict[str, Any]:
    """Step 3: GET /curator/stats."""
    _print_step(3, "GET /api/v1/curator/stats")

    resp = client.get(
        "/api/v1/curator/stats",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise StepFail(f"stats failed: {resp.status_code} {resp.text[:300]}")

    stats = resp.json()
    _print_pass(
        f"bronze_clean={stats['bronze_clean_count']}, "
        f"pending_status={stats['pending_status_count']}, "
        f"verified={stats['verified_count']}, "
        f"rejected_today={stats['rejected_today']}"
    )
    return stats


def step_queue(client: httpx.Client, token: str) -> dict[str, Any]:
    """Step 4: GET /curator/queue?status=bronze_clean&limit=3."""
    _print_step(4, "GET /api/v1/curator/queue?status=bronze_clean&per_page=3")

    resp = client.get(
        "/api/v1/curator/queue",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "bronze_clean", "per_page": 3},
        timeout=15.0,
    )
    if resp.status_code != 200:
        raise StepFail(f"queue failed: {resp.status_code} {resp.text[:300]}")

    body = resp.json()
    items = body.get("items", [])
    if not items:
        raise StepFail("queue returned 0 items (bronze_clean expected >=1)")

    first = items[0]
    _print_pass(
        f"items count={len(items)}, total={body.get('total')}, "
        f"first_id={first['id'][:8]}..., status={first['quality_review_status']}, "
        f"subject={first['subject_area']}"
    )
    return body


def step_db_snapshot_pre(question_id: str) -> dict[str, Any]:
    """Step 5: DB pre-verdict snapshot."""
    _print_step(5, "DB snapshot (pre-verdict)")

    row = _db_fetchone(
        "SELECT id, quality_review_status, reviewed_by, "
        "pipeline_metadata FROM question_bank WHERE id = %s",
        (question_id,),
    )
    if row is None:
        raise StepFail(f"question {question_id} not found in DB")

    status_val = row["quality_review_status"]
    if status_val != "bronze_clean":
        raise StepFail(f"expected status='bronze_clean', got '{status_val}'")

    has_verdict = bool(
        row.get("pipeline_metadata")
        and isinstance(row["pipeline_metadata"], dict)
        and "curator_verdict" in row["pipeline_metadata"]
    )
    _print_pass(
        f"status=bronze_clean, reviewed_by={row['reviewed_by']}, "
        f"has_existing_curator_verdict={has_verdict}"
    )
    return row


def step_post_verdict(
    client: httpx.Client, token: str, question_id: str
) -> dict[str, Any]:
    """Step 6: POST /curator/verdict."""
    _print_step(6, f"POST /api/v1/curator/verdict (verify, q={question_id[:8]}...)")

    resp = client.post(
        "/api/v1/curator/verdict",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": question_id,
            "verdict": TEST_VERDICT,
            "notes": TEST_NOTES,
            "reviewer_velocity_seconds": TEST_VELOCITY,
        },
        timeout=15.0,
    )
    if resp.status_code != 200:
        raise StepFail(f"verdict failed: {resp.status_code} {resp.text[:400]}")

    body = resp.json()
    if body["new_status"] != EXPECTED_NEW_STATUS:
        raise StepFail(
            f"expected new_status={EXPECTED_NEW_STATUS}, got {body['new_status']}"
        )

    _print_pass(
        f"verdict applied: previous={body['previous_status']} -> "
        f"new={body['new_status']}, reviewed_by={body['reviewed_by'][:8]}..."
    )
    return body


def step_db_snapshot_post(question_id: str, admin_id: str) -> dict[str, Any]:
    """Step 7: DB post-verdict snapshot."""
    _print_step(7, "DB snapshot (post-verdict)")

    row = _db_fetchone(
        "SELECT id, quality_review_status, reviewed_by, "
        "pipeline_metadata FROM question_bank WHERE id = %s",
        (question_id,),
    )
    if row is None:
        raise StepFail(f"question {question_id} not found after verdict")

    status_val = row["quality_review_status"]
    if status_val != EXPECTED_NEW_STATUS:
        raise StepFail(
            f"DB post-verdict status mismatch: expected '{EXPECTED_NEW_STATUS}', "
            f"got '{status_val}'"
        )

    if row["reviewed_by"] != admin_id:
        raise StepFail(
            f"reviewed_by mismatch: expected={admin_id}, got={row['reviewed_by']}"
        )

    _print_pass(
        f"status={status_val} (correct), reviewed_by={row['reviewed_by']} (matches admin)"
    )
    return row


def step_audit_trail(question_id: str, admin_id: str) -> dict[str, Any]:
    """Step 8: pipeline_metadata.curator_verdict trail kontrol."""
    _print_step(8, "Audit trail: pipeline_metadata.curator_verdict")

    row = _db_fetchone(
        "SELECT pipeline_metadata FROM question_bank WHERE id = %s",
        (question_id,),
    )
    if row is None:
        raise StepFail("question not found")

    meta = row["pipeline_metadata"] or {}
    if not isinstance(meta, dict):
        raise StepFail(f"pipeline_metadata is not dict: {type(meta).__name__}")

    cv = meta.get("curator_verdict")
    if cv is None:
        raise StepFail("pipeline_metadata.curator_verdict MISSING")

    # Required fields
    required = {
        "verdict": TEST_VERDICT,
        "previous_status": "bronze_clean",
        "reviewer_id": admin_id,
    }
    for key, expected in required.items():
        if cv.get(key) != expected:
            raise StepFail(
                f"curator_verdict.{key} mismatch: "
                f"expected={expected!r}, got={cv.get(key)!r}"
            )

    if cv.get("velocity_seconds") != TEST_VELOCITY:
        raise StepFail(f"velocity_seconds mismatch: {cv.get('velocity_seconds')}")

    if "reviewed_at" not in cv:
        raise StepFail("curator_verdict.reviewed_at missing")

    _print_pass(
        f"curator_verdict trail OK: verdict={cv['verdict']}, "
        f"velocity={cv['velocity_seconds']}, reviewed_at={cv['reviewed_at'][:19]}"
    )
    _print_info(f"snippet: {json.dumps(cv, ensure_ascii=False, default=str)[:200]}")
    return cv


def step_audit_log(question_id: str, admin_id: str) -> dict[str, Any]:
    """Step 9: audit_logs satiri kontrol."""
    _print_step(9, "audit_logs row check")

    row = _db_fetchone(
        "SELECT id, user_id, action, resource_type, resource_id, "
        "old_values, new_values, created_at "
        "FROM audit_logs "
        "WHERE resource_type = 'question_bank' AND resource_id = %s "
        "ORDER BY created_at DESC LIMIT 1",
        (question_id,),
    )
    if row is None:
        raise StepFail("audit_logs row NOT created for verdict")

    if row["user_id"] != admin_id:
        raise StepFail(
            f"audit user_id mismatch: expected={admin_id}, got={row['user_id']}"
        )

    expected_action = f"curator.verdict.{TEST_VERDICT}"
    if row["action"] != expected_action:
        raise StepFail(
            f"audit action mismatch: expected={expected_action}, got={row['action']}"
        )

    _print_pass(
        f"audit_logs id={row['id'][:8]}..., action={row['action']}, "
        f"created_at={row['created_at']}"
    )
    _print_info(
        f"new_values: {json.dumps(row['new_values'], ensure_ascii=False, default=str)[:200]}"
    )
    return row


def step_rollback(question_id: str, audit_id: str) -> None:
    """Step 10: rollback - DB temizligi."""
    _print_step(10, "ROLLBACK (test cleanup)")

    # 1. quality_review_status -> bronze_clean
    # 2. pipeline_metadata - 'curator_verdict' (jsonb cast required)
    # 3. reviewed_by -> NULL (pre-test default)
    rows_q = _db_execute(
        """
        UPDATE question_bank
        SET quality_review_status = 'bronze_clean',
            pipeline_metadata = CAST(
                (pipeline_metadata::jsonb - 'curator_verdict') AS json
            ),
            reviewed_by = NULL
        WHERE id = %s
        """,
        (question_id,),
    )
    if rows_q != 1:
        raise StepFail(f"rollback: expected 1 question_bank row, got {rows_q}")

    # Audit log delete
    rows_a = _db_execute(
        "DELETE FROM audit_logs WHERE id = %s",
        (audit_id,),
    )
    if rows_a != 1:
        raise StepFail(f"rollback: expected 1 audit_logs row, got {rows_a}")

    # Verify rollback
    row = _db_fetchone(
        "SELECT quality_review_status, pipeline_metadata, reviewed_by "
        "FROM question_bank WHERE id = %s",
        (question_id,),
    )
    if row is None or row["quality_review_status"] != "bronze_clean":
        raise StepFail("rollback verification failed: status not bronze_clean")

    meta = row["pipeline_metadata"] or {}
    if isinstance(meta, dict) and "curator_verdict" in meta:
        raise StepFail("rollback verification failed: curator_verdict still present")

    audit_check = _db_fetchone("SELECT id FROM audit_logs WHERE id = %s", (audit_id,))
    if audit_check is not None:
        raise StepFail("rollback verification failed: audit_logs row still exists")

    _print_pass(
        "rollback verified: status=bronze_clean, curator_verdict removed, "
        "audit_logs row deleted"
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("Curator UI E2E HTTP-only Smoke Test")
    print(f"Backend: {BASE_URL}")
    print(f"DB:      {DSN}")
    print(f"Admin:   {ADMIN_EMAIL}")
    print("=" * 70)

    start = time.time()
    state: dict[str, Any] = {}

    try:
        # Setup
        admin_id = step_check_admin()
        state["admin_id"] = admin_id

        with httpx.Client(base_url=BASE_URL, follow_redirects=True) as client:
            token = step_login(client)
            state["token"] = token

            step_stats(client, token)

            queue = step_queue(client, token)
            test_question_id = queue["items"][0]["id"]
            state["test_question_id"] = test_question_id

            step_db_snapshot_pre(test_question_id)
            step_post_verdict(client, token, test_question_id)
            step_db_snapshot_post(test_question_id, admin_id)
            step_audit_trail(test_question_id, admin_id)
            audit_row = step_audit_log(test_question_id, admin_id)
            state["audit_id"] = audit_row["id"]

        # Cleanup
        step_rollback(test_question_id, audit_row["id"])

        elapsed = time.time() - start
        print("\n" + "=" * 70)
        print(f"ALL STEPS PASSED in {elapsed:.2f}s")
        print(f"  Question tested: {test_question_id}")
        print("  State restored:  bronze_clean (no DB pollution)")
        print("=" * 70)
        return 0

    except StepFail as e:
        elapsed = time.time() - start
        print("\n" + "=" * 70)
        print(f"FAILED after {elapsed:.2f}s")
        print(f"  Reason: {e}")
        print(f"  State: {state}")
        print("=" * 70)
        # Best-effort rollback if we got far enough
        if "test_question_id" in state and "audit_id" in state:
            print("\nAttempting best-effort rollback...")
            try:
                step_rollback(state["test_question_id"], state["audit_id"])
                print("Rollback OK.")
            except Exception as r:
                print(f"Rollback FAILED: {r}")
                print(
                    f"!! MANUAL ROLLBACK REQUIRED: "
                    f"question_id={state.get('test_question_id')} "
                    f"audit_id={state.get('audit_id')}"
                )
        return 1

    except Exception as e:
        elapsed = time.time() - start
        print("\n" + "=" * 70)
        print(f"UNEXPECTED ERROR after {elapsed:.2f}s: {e}")
        print("=" * 70)
        traceback.print_exc()
        if "test_question_id" in state and "audit_id" in state:
            print("\nAttempting best-effort rollback...")
            try:
                step_rollback(state["test_question_id"], state["audit_id"])
                print("Rollback OK.")
            except Exception as r:
                print(f"Rollback FAILED: {r}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
