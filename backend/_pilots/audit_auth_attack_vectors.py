"""
Auth Attack Vector Reproduce — İleri Düzey Security Audit

Real HTTP attack reproduce: JWT replay, IDOR exploit, CSRF bypass,
session fixation, header injection, rate limit bypass, multi-tab race.

Her vector için:
  - Setup: temiz başlangıç state
  - Attack: gerçek HTTP exploit
  - Verify: DB state + response inspection
  - Conclusion: vulnerable mu?

Usage:
    python backend/_pilots/audit_auth_attack_vectors.py
"""

from __future__ import annotations

import json
import sys
import time

import httpx
import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND = "http://localhost:8000"
DSN = "postgresql://postgres:1470@localhost:5434/kiro2"


def get_admin_creds():
    """admin@kiro2.com sample creds (MVP seed)."""
    return "admin@kiro2.com", "Kiro2Beta2026@x"


def get_student_creds():
    """Find any STUDENT for test."""
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        "SELECT email FROM users WHERE role = 'STUDENT' AND is_active = TRUE LIMIT 2"
    )
    rows = cur.fetchall()
    conn.close()
    if len(rows) < 2:
        return None, None
    return rows[0][0], rows[1][0]


def login(client: httpx.Client, email: str, password: str) -> tuple[str | None, dict]:
    """Login + return (token, response_dict)."""
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        return None, {"status": r.status_code, "body": r.text[:200]}
    body = r.json()
    return body.get("access_token") or body.get("token"), body


# ============================================================
# ATTACK 1: IDOR — soru_bankasi.py:244 anonim erişim (B-P0-1)
# ============================================================
def attack1_idor_anonymous_soru_bankasi():
    """B-P0-1: 3 endpoint auth eksik raporlanmıştı. Anonim olarak erişebilir mi?"""
    print("\n--- ATTACK 1: IDOR /api/v1/soru-bankasi/* anonim erişim ---")
    client = httpx.Client(base_url=BACKEND, timeout=5.0)
    endpoints = [
        ("GET", "/api/v1/soru-bankasi/rastgele?limit=5"),
        ("GET", "/api/v1/soru-bankasi/konular"),
        ("GET", "/api/v1/soru-bankasi/istatistikler"),
    ]
    for method, path in endpoints:
        # NO auth header
        r = client.request(method, path)
        if 200 <= r.status_code < 300:
            print(f"  🔴 VULNERABLE {method} {path} → {r.status_code} (anonim erişim)")
            # Sample response (data leak?)
            try:
                body_preview = (
                    r.json()
                    if r.headers.get("content-type", "").startswith("application/json")
                    else r.text[:200]
                )
                if isinstance(body_preview, list) and body_preview:
                    print(
                        f"     Data leak: {len(body_preview)} items, sample={str(body_preview[0])[:120]}"
                    )
                elif isinstance(body_preview, dict):
                    print(f"     Data leak keys: {list(body_preview.keys())[:8]}")
                else:
                    print(f"     Response: {str(body_preview)[:200]}")
            except Exception:
                print(f"     Response (raw): {r.text[:200]}")
        elif r.status_code in (401, 403):
            print(f"  ✓ Protected {method} {path} → {r.status_code}")
        else:
            print(f"  ? {method} {path} → {r.status_code}")
    client.close()


# ============================================================
# ATTACK 2: JWT replay after logout
# ============================================================
def attack2_jwt_replay_after_logout():
    """JWT logout sonrası replay edilebilir mi? Blacklist çalışıyor mu?"""
    print("\n--- ATTACK 2: JWT replay after logout ---")
    email, _ = get_student_creds()
    if not email:
        print("  No student user — skip")
        return
    client = httpx.Client(base_url=BACKEND, timeout=5.0)
    token, _ = login(client, email, "Kiro2Beta2026@x")
    if not token:
        print(f"  Login failed for {email}")
        client.close()
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Validate /me works
    r1 = client.get("/api/v1/auth/me", headers=headers)
    print(f"  Before logout /me: {r1.status_code}")

    # 2. Logout (blacklist token)
    r2 = client.post("/api/v1/auth/logout", headers=headers)
    print(f"  Logout: {r2.status_code}")

    # 3. Replay token — should be rejected (401)
    r3 = client.get("/api/v1/auth/me", headers=headers)
    if r3.status_code == 401:
        print(f"  ✓ Token blacklisted /me: {r3.status_code} (replay blocked)")
    elif r3.status_code == 200:
        print(f"  🔴 VULNERABLE: Token still valid after logout: {r3.status_code}")
    else:
        print(f"  ? Unexpected: {r3.status_code}")
    client.close()


# ============================================================
# ATTACK 3: IDOR via user_id query param (Session 84 regression check)
# ============================================================
def attack3_idor_user_id_query():
    """Gamification endpoint'lerinde user_id query param hala kabul ediyor mu?"""
    print("\n--- ATTACK 3: IDOR via ?user_id= query (Session 84 regression) ---")
    email, victim_email = get_student_creds()
    if not email or not victim_email:
        print("  Need 2 students — skip")
        return
    client = httpx.Client(base_url=BACKEND, timeout=5.0)
    token, body = login(client, email, "Kiro2Beta2026@x")
    if not token:
        print("  Login failed")
        client.close()
        return
    headers = {"Authorization": f"Bearer {token}"}
    attacker_id = body.get("user_id") or body.get("user", {}).get("id")

    # Victim user ID — DB'den bul
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (victim_email,))
    victim_id = cur.fetchone()
    conn.close()
    if not victim_id:
        print("  Victim user_id not found")
        return
    victim_id = victim_id[0]
    print(f"  Attacker login: {email[:30]} → attacker_id={str(attacker_id)[:8]}")
    print(f"  Target victim:  {victim_email[:30]} → victim_id={str(victim_id)[:8]}")

    # Try gamification endpoints with ?user_id=<victim>
    endpoints = [
        f"/api/v1/gamification/points?user_id={victim_id}",
        f"/api/v1/gamification/achievements?user_id={victim_id}",
        f"/api/v1/gamification/badges/earned?user_id={victim_id}",
    ]
    for path in endpoints:
        r = client.get(path, headers=headers)
        if 200 <= r.status_code < 300:
            # Check if victim data leaked (vs attacker's)
            print(f"  ? {path[:60]} → {r.status_code}")
            try:
                body = r.json()
                # Eğer response içinde victim_id varsa = IDOR vulnerable
                body_str = (
                    json.dumps(body) if isinstance(body, (dict, list)) else str(body)
                )
                if str(victim_id) in body_str:
                    print("     🔴 VULNERABLE: victim_id leaked in response")
                else:
                    print("     ✓ Server ignored user_id, returned attacker's own data")
            except Exception:
                pass
        elif r.status_code in (401, 403):
            print(f"  ✓ Protected {path[:60]} → {r.status_code}")
        else:
            print(f"  ? {path[:60]} → {r.status_code}")
    client.close()


# ============================================================
# ATTACK 4: CSRF bypass via Bearer token (GF99 verify)
# ============================================================
def attack4_csrf_bypass_check():
    """Bearer client'lar CSRF middleware'i early-return ediyor mu?"""
    print("\n--- ATTACK 4: CSRF middleware behavior for Bearer clients ---")
    email, _ = get_student_creds()
    if not email:
        return
    client = httpx.Client(base_url=BACKEND, timeout=5.0)
    token, _ = login(client, email, "Kiro2Beta2026@x")
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}"}

    # POST without CSRF token (Bearer header should bypass CSRF)
    r = client.post("/api/v1/auth/logout", headers=headers)
    if r.status_code == 403 and "csrf" in r.text.lower():
        print(f"  🔴 BUG: Bearer client blocked by CSRF: {r.status_code} {r.text[:80]}")
    elif r.status_code in (200, 204):
        print(f"  ✓ Bearer client bypass CSRF: {r.status_code} (correct)")
    else:
        print(f"  ? Unexpected: {r.status_code} {r.text[:80]}")

    # POST with cookie auth but no CSRF token (should 403)
    cookie_client = httpx.Client(base_url=BACKEND, timeout=5.0)
    r2 = cookie_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Kiro2Beta2026@x"}
    )
    if r2.status_code == 200:
        # Now have cookies, try state-changing POST without CSRF header
        r3 = cookie_client.post("/api/v1/auth/logout")
        if r3.status_code == 403 and "csrf" in r3.text.lower():
            print(f"  ✓ Cookie client requires CSRF: {r3.status_code} (correct)")
        else:
            print(f"  ? Cookie POST without CSRF: {r3.status_code}")
    cookie_client.close()
    client.close()


# ============================================================
# ATTACK 5: Header injection / X-User-ID spoofing (Session 178 finding)
# ============================================================
def attack5_x_user_id_spoofing():
    """B-P1-3: api_optimizer.py X-User-ID header trust → rate limit bypass."""
    print("\n--- ATTACK 5: X-User-ID header spoofing for rate limit bypass ---")
    client = httpx.Client(base_url=BACKEND, timeout=5.0)

    # Try 5 rapid logins with DIFFERENT X-User-ID values
    # If rate limiter uses X-User-ID, each unique value gets fresh bucket
    fake_ids = ["spoofed-1", "spoofed-2", "spoofed-3", "spoofed-4", "spoofed-5"]
    results = []
    for fake_id in fake_ids:
        headers = {"X-User-ID": fake_id}
        r = client.post(
            "/api/v1/auth/login",
            headers=headers,
            json={"email": "nonexistent@test.com", "password": "wrong"},
        )
        results.append((fake_id, r.status_code))
    counts = {}
    for _, s in results:
        counts[s] = counts.get(s, 0) + 1
    if counts.get(429, 0) > 0:
        print(f"  ✓ Rate limiter triggered (X-User-ID ignored): {counts}")
    elif counts.get(401, 0) == 5:
        print(f"  🔴 VULNERABLE: Rate limit bypassed via X-User-ID spoofing: {counts}")
    else:
        print(f"  ? Result: {counts}")
    client.close()


# ============================================================
# ATTACK 6: Negative/oversized integer in path param (overflow check)
# ============================================================
def attack6_integer_overflow_paths():
    """Path parametre olarak negatif/aşırı büyük int gönder."""
    print("\n--- ATTACK 6: Integer overflow / negative in path params ---")
    email, _ = get_student_creds()
    client = httpx.Client(base_url=BACKEND, timeout=5.0)
    token, _ = login(client, email, "Kiro2Beta2026@x")
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}"}

    payloads = [
        ("user_id", -1, "/api/v1/users/-1"),
        ("user_id_oflow", 99999999999999999, "/api/v1/users/99999999999999999"),
        ("question_id_neg", -42, "/api/v1/questions/-42"),
        ("topic_id_oflow", 2**63, f"/api/v1/topics/{2**63}"),
    ]
    for name, val, path in payloads:
        r = client.get(path, headers=headers)
        if r.status_code == 500:
            print(f"  🔴 CRASH on {name}={val}: 500 {r.text[:80]}")
        elif r.status_code == 422:
            print(f"  ✓ Validation 422 on {name}={val} (Pydantic guard)")
        elif r.status_code in (404, 400):
            print(f"  ✓ Rejected {name}={val}: {r.status_code}")
        elif r.status_code in (401, 403):
            print(f"  ? Auth gate first: {r.status_code}")
        else:
            print(f"  ? {name}={val}: {r.status_code}")
    client.close()


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("KIRO2 AUTH ATTACK VECTOR AUDIT — Real HTTP exploits")
    print("=" * 70)
    print()
    print(
        "⚠️  All attacks targeted at LOCAL http://localhost:8000 (production hot-patched)"
    )
    print("⚠️  No production secrets exposed. Test users from seed.")

    # Wait for rate limit cooldown from earlier workload test
    print("\n  [waiting 65s for rate limit cooldown...]", end="", flush=True)
    time.sleep(65)
    print(" done")

    attack1_idor_anonymous_soru_bankasi()
    time.sleep(2)
    attack2_jwt_replay_after_logout()
    time.sleep(2)
    attack3_idor_user_id_query()
    time.sleep(2)
    attack4_csrf_bypass_check()
    time.sleep(2)
    attack5_x_user_id_spoofing()
    time.sleep(2)
    attack6_integer_overflow_paths()

    print()
    print("=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
