#!/usr/bin/env python3
"""
Phase 7 via OpenAI Batch API (24h async, 50% discount, bypasses daily RPM cap).

Flow:
  1. build  — Build batch_input.jsonl from pending gold rows.
  2. submit — Upload file + create batch. Saves batch_id to .batch_state.json.
  3. poll   — Check batch status; exit 0 when completed, exit 1 otherwise.
  4. apply  — Download output, parse, INSERT into DB (rationales + math + qb update).
  5. run    — build → submit → poll-loop → apply (single command, auto).

Auto-splits into ≤50K-request chunks (OpenAI batch limit).

Usage:
  python metadata_phase7_batch_openai.py run --limit 68000
  python metadata_phase7_batch_openai.py poll --batch-id batch_xxx
  python metadata_phase7_batch_openai.py apply --batch-id batch_xxx
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Reuse PROMPT_TEMPLATE + taxonomy from existing script
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
from metadata_phase7_llm_generation import (  # noqa: E402
    PROMPT_TEMPLATE,
    derive_taxonomy,
    parse_llm_response,
)

DSN = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE = "https://api.openai.com/v1"

BATCH_LIMIT = 50_000  # OpenAI Batch API max requests per file
MAX_TOKENS = 1500

STATE_DIR = THIS_DIR / "_batch_state"
STATE_DIR.mkdir(exist_ok=True)


def _http(method: str, path: str, body=None, headers=None, timeout=60):
    """Plain urllib HTTP helper. Returns dict or raises."""
    url = f"{OPENAI_BASE}{path}"
    hdrs = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    if headers:
        hdrs.update(headers)
    if isinstance(body, (dict, list)):
        hdrs.setdefault("Content-Type", "application/json")
        body = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {path}: {err_body[:500]}") from e


def fetch_pending_rows(limit: int) -> list:
    """Pull pending Phase 7 gold rows (no rationale yet)."""
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c,
               q.option_d, q.option_e, q.correct_answer, q.subject_area,
               q.exam_type, q.difficulty_level::text, q.bloom_category
        FROM question_bank q
        LEFT JOIN question_option_rationales r
          ON r.question_id = q.id::text AND r.option_letter = 'A'
        WHERE q.is_active = true
          AND q.question_text IS NOT NULL
          AND q.option_a IS NOT NULL
          AND q.correct_answer IN ('A', 'B', 'C', 'D', 'E')
          AND r.question_id IS NULL
          AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
        ORDER BY q.created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def build_prompt_for_row(row) -> str:
    qid, qt, oa, ob, oc, od, oe, ca, subj, exam, diff, bloom = row
    return PROMPT_TEMPLATE.format(
        subject_area=subj or "Genel",
        exam_type=exam or "TYT",
        difficulty_level=diff or "MEDIUM",
        bloom_category=bloom or "kavrama",
        question_text=qt[:1000],
        option_a=oa[:300] if oa else "",
        option_b=ob[:300] if ob else "",
        option_c=oc[:300] if oc else "",
        option_d=(od or "")[:300],
        option_e=(oe or "")[:300],
        correct_answer=ca,
    )


def build_batch_requests(rows) -> Iterator[dict]:
    for row in rows:
        qid = row[0]
        prompt = build_prompt_for_row(row)
        yield {
            "custom_id": qid,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": MAX_TOKENS,
                "response_format": {"type": "json_object"},
            },
        }


def split_into_chunks(rows, chunk_size=BATCH_LIMIT) -> Iterator[tuple[int, list]]:
    """Yield (chunk_index, chunk_rows)."""
    for i in range(0, len(rows), chunk_size):
        yield i // chunk_size, rows[i : i + chunk_size]


def cmd_build(args):
    """Build batch input JSONL(s) and row metadata cache."""
    rows = fetch_pending_rows(args.limit)
    print(f"[build] Fetched {len(rows):,} pending rows from DB")

    if not rows:
        print("[build] No pending rows. Done.")
        return

    input_files = []
    meta_path = STATE_DIR / "rows_meta.json"
    # Save row metadata (for apply step — taxonomy needs full row)
    rows_meta = {
        r[0]: {
            "correct_answer": r[7],
            "subject_area": r[8],
            "difficulty_level": r[10],
            "bloom_category": r[11],
        }
        for r in rows
    }
    meta_path.write_text(json.dumps(rows_meta, ensure_ascii=False), encoding="utf-8")
    print(f"[build] Saved row metadata: {meta_path} ({len(rows_meta):,} rows)")

    for chunk_idx, chunk_rows in split_into_chunks(rows):
        input_path = STATE_DIR / f"batch_input_{chunk_idx:03d}.jsonl"
        with input_path.open("w", encoding="utf-8") as f:
            for req in build_batch_requests(chunk_rows):
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
        size_mb = input_path.stat().st_size / (1024 * 1024)
        print(
            f"[build] chunk {chunk_idx:03d}: {len(chunk_rows):,} rows -> "
            f"{input_path.name} ({size_mb:.1f} MB)"
        )
        input_files.append(input_path.name)

    state = {
        "input_files": input_files,
        "total_rows": len(rows),
        "chunk_size": BATCH_LIMIT,
    }
    (STATE_DIR / "build_state.json").write_text(json.dumps(state, indent=2))
    print(f"[build] Done. {len(input_files)} chunk(s) ready for submit.")


def cmd_submit(args):
    """Upload all built JSONL files + create batches."""
    state_path = STATE_DIR / "build_state.json"
    if not state_path.exists():
        print("[submit] No build_state.json. Run build first.")
        sys.exit(1)
    state = json.loads(state_path.read_text())

    batch_ids = []
    for fname in state["input_files"]:
        path = STATE_DIR / fname
        print(f"[submit] Uploading {fname}...")

        # Upload file via multipart/form-data (manual since urllib has no form helper)
        boundary = "----KIRO2BATCH" + str(int(time.time()))
        body_parts = []
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="purpose"\r\n')
        body_parts.append(b"batch")
        body_parts.append(f"\r\n--{boundary}".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'
            f"Content-Type: application/octet-stream\r\n".encode()
        )
        body_parts.append(path.read_bytes())
        body_parts.append(f"\r\n--{boundary}--\r\n".encode())
        # Join with proper separators
        raw_body = b"\r\n".join(
            [
                f"--{boundary}".encode(),
                b'Content-Disposition: form-data; name="purpose"\r\n',
                b"batch",
                f"--{boundary}".encode(),
                f'Content-Disposition: form-data; name="file"; filename="{fname}"'.encode()
                + b"\r\nContent-Type: application/octet-stream\r\n",
                path.read_bytes(),
                f"--{boundary}--".encode(),
            ]
        )

        req = urllib.request.Request(
            f"{OPENAI_BASE}/files",
            data=raw_body,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                file_obj = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"[submit] Upload failed: HTTP {e.code} {err_body[:300]}")
            sys.exit(1)

        file_id = file_obj["id"]
        print(f"[submit]   uploaded -> file_id={file_id}")

        print(f"[submit] Creating batch for {file_id}...")
        batch = _http(
            "POST",
            "/batches",
            body={
                "input_file_id": file_id,
                "endpoint": "/v1/chat/completions",
                "completion_window": "24h",
            },
        )
        batch_ids.append(batch["id"])
        print(f"[submit]   batch_id={batch['id']} status={batch['status']}")

    submit_state = {"batch_ids": batch_ids, "submitted_at": int(time.time())}
    (STATE_DIR / "submit_state.json").write_text(json.dumps(submit_state, indent=2))
    print(f"\n[submit] All batches submitted: {batch_ids}")


def cmd_poll(args):
    """Poll batch status. Returns 0 if all complete, 1 if pending, 2 if failed."""
    state_path = STATE_DIR / "submit_state.json"
    if not state_path.exists():
        print("[poll] No submit_state.json. Run submit first.")
        sys.exit(1)
    submit_state = json.loads(state_path.read_text())

    batch_ids = args.batch_id.split(",") if args.batch_id else submit_state["batch_ids"]

    statuses = []
    for bid in batch_ids:
        info = _http("GET", f"/batches/{bid}")
        completed = info.get("request_counts", {}).get("completed", 0)
        total = info.get("request_counts", {}).get("total", 0)
        failed = info.get("request_counts", {}).get("failed", 0)
        status = info["status"]
        statuses.append(status)
        print(
            f"[poll] {bid} status={status} completed={completed}/{total} failed={failed}"
        )

    if all(s == "completed" for s in statuses):
        sys.exit(0)
    elif any(s in ("failed", "expired", "cancelled") for s in statuses):
        sys.exit(2)
    sys.exit(1)


def cmd_apply(args):
    """Download outputs + INSERT to DB."""
    state_path = STATE_DIR / "submit_state.json"
    if not state_path.exists():
        print("[apply] No submit_state.json.")
        sys.exit(1)
    submit_state = json.loads(state_path.read_text())
    meta_path = STATE_DIR / "rows_meta.json"
    rows_meta = json.loads(meta_path.read_text(encoding="utf-8"))

    batch_ids = args.batch_id.split(",") if args.batch_id else submit_state["batch_ids"]

    conn = psycopg2.connect(DSN)
    rationale_rows = []
    qb_updates = []
    math_rows = []
    success_n = 0
    fail_n = 0
    parse_fail_samples = []

    for bid in batch_ids:
        info = _http("GET", f"/batches/{bid}")
        output_file_id = info.get("output_file_id")
        if not output_file_id:
            print(f"[apply] {bid}: no output_file_id, skip")
            continue

        print(f"[apply] Downloading {bid} output...")
        req = urllib.request.Request(
            f"{OPENAI_BASE}/files/{output_file_id}/content",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            output_text = resp.read().decode("utf-8", errors="replace")

        for line in output_text.splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            custom_id = entry.get("custom_id")
            response = entry.get("response", {})
            status_code = response.get("status_code", 0)

            if status_code != 200:
                fail_n += 1
                continue

            try:
                body = response.get("body", {})
                content = body["choices"][0]["message"]["content"]
                content = content.replace("\x00", "").replace("\\u0000", "")
                parsed = parse_llm_response(content)
            except Exception as e:
                fail_n += 1
                if len(parse_fail_samples) < 5:
                    parse_fail_samples.append(f"{custom_id}: {e}")
                continue

            if not parsed or not parsed.get("rationales"):
                fail_n += 1
                continue

            rationales = parsed.get("rationales", {}) or {}
            if sum(1 for v in rationales.values() if v) < 5:
                fail_n += 1
                continue

            meta = rows_meta.get(custom_id)
            if not meta:
                fail_n += 1
                continue

            ca = meta["correct_answer"]
            solo, marzano, is_math = derive_taxonomy(
                meta["subject_area"], meta["difficulty_level"], meta["bloom_category"]
            )

            for letter in "ABCDE":
                rtxt = rationales.get(letter)
                if rtxt:
                    rationale_rows.append(
                        (
                            custom_id,
                            letter,
                            str(rtxt)[:1000],
                            letter == ca,
                            OPENAI_MODEL,
                        )
                    )

            miscon = parsed.get("misconception_tags") or []
            solution = parsed.get("solution_steps") or []
            formula = parsed.get("expected_answer_formula")
            qb_updates.append(
                (
                    json.dumps(miscon, ensure_ascii=False) if miscon else None,
                    json.dumps(solution, ensure_ascii=False) if solution else None,
                    solo,
                    marzano,
                    formula,
                    is_math,
                    custom_id,
                )
            )
            if is_math and formula:
                math_rows.append((custom_id, formula))

            success_n += 1

    print(
        f"[apply] Parsed: success={success_n:,} fail={fail_n:,} "
        f"rationale_rows={len(rationale_rows):,} qb_updates={len(qb_updates):,} math={len(math_rows):,}"
    )
    if parse_fail_samples:
        print("[apply] Parse-fail samples (first 5):")
        for s in parse_fail_samples:
            print(f"  {s}")

    if args.dry_run:
        print("[apply] DRY-RUN — no DB writes")
        return

    cur = conn.cursor()
    try:
        if rationale_rows:
            execute_values(
                cur,
                """
                INSERT INTO question_option_rationales
                  (question_id, option_letter, rationale, is_correct, generated_by, generated_at)
                VALUES %s
                ON CONFLICT (question_id, option_letter) DO NOTHING
                """,
                rationale_rows,
                template="(%s, %s, %s, %s, %s, NOW())",
            )

        if qb_updates:
            execute_values(
                cur,
                """
                UPDATE question_bank q SET
                  misconception_tags = v.miscon::jsonb,
                  solution_steps = v.sol::jsonb,
                  solo_level = v.solo,
                  marzano_level = v.marzano,
                  expected_answer_formula = v.formula,
                  is_math_solvable = v.is_math,
                  metadata_filled_at = NOW()
                FROM (VALUES %s) AS v(miscon, sol, solo, marzano, formula, is_math, qid)
                WHERE q.id::text = v.qid
                """,
                qb_updates,
                template="(%s, %s, %s, %s, %s, %s, %s)",
            )

        if math_rows:
            execute_values(
                cur,
                """
                INSERT INTO question_math
                  (question_id, expected_answer_sympy, is_symbolic_verifiable, created_at)
                VALUES %s
                ON CONFLICT (question_id)
                  DO UPDATE SET expected_answer_sympy = EXCLUDED.expected_answer_sympy
                """,
                math_rows,
                template="(%s, %s, TRUE, NOW())",
            )

        conn.commit()
        print("[apply] DB writes committed.")
    except Exception as e:
        conn.rollback()
        print(f"[apply] DB write FAILED, rolled back: {e}")
        sys.exit(3)
    finally:
        conn.close()


def cmd_run(args):
    """build -> submit -> poll-loop -> apply."""
    print("=" * 70)
    print(f"Phase 7 Batch API run — limit {args.limit:,} | model {OPENAI_MODEL}")
    print("=" * 70)
    cmd_build(args)
    cmd_submit(args)

    print("\n[run] Entering poll loop (60s interval, max 24h)...")
    deadline = time.time() + 24 * 3600
    while time.time() < deadline:
        time.sleep(60)
        try:
            cmd_poll(argparse.Namespace(batch_id=None))
        except SystemExit as se:
            if se.code == 0:
                print("[run] All batches completed!")
                break
            if se.code == 2:
                print("[run] Batch failed/expired. Aborting.")
                sys.exit(2)
            # else: still pending, continue
    else:
        print("[run] 24h deadline hit, aborting.")
        sys.exit(1)

    print("\n[run] Applying results to DB...")
    cmd_apply(argparse.Namespace(batch_id=None, dry_run=False))
    print("\n[run] Complete.")


def main():
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY env var not set")
        sys.exit(1)

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build")
    p_build.add_argument("--limit", type=int, default=100_000)

    sub.add_parser("submit")

    p_poll = sub.add_parser("poll")
    p_poll.add_argument("--batch-id", type=str, default=None)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--batch-id", type=str, default=None)
    p_apply.add_argument("--dry-run", action="store_true")

    p_run = sub.add_parser("run")
    p_run.add_argument("--limit", type=int, default=100_000)

    args = ap.parse_args()
    {
        "build": cmd_build,
        "submit": cmd_submit,
        "poll": cmd_poll,
        "apply": cmd_apply,
        "run": cmd_run,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
