#!/usr/bin/env python3
"""
Phase 7 via Google Gemini Batch API (24h async, 50% discount, no daily RPM cap).

Sub-commands:
  build  — Build JSONL files from pending gold rows (auto-split if > 50K).
  submit — Upload each JSONL to Files API + create batch jobs.
  poll   — Check batch status; exit 0 if all SUCCEEDED.
  apply  — Download outputs, parse, INSERT into DB.
  run    — build → submit → poll-loop → apply (single command).

JSONL line format:
  {"key": "<qid>", "request": {"contents": [...], "generationConfig": {...}}}

Workaround: upload as mime="text/plain" (see python-genai issue #1590).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
from metadata_phase7_llm_generation import (  # noqa
    PROMPT_TEMPLATE,
    derive_taxonomy,
    parse_llm_response,
)

DSN = os.environ.get("DATABASE_URL") or (
    __import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)")
)
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

GEN_BASE = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_BASE = "https://generativelanguage.googleapis.com/upload/v1beta"

BATCH_LIMIT = 30_000  # split files; under file-size 2GB easily
MAX_OUTPUT_TOKENS = 16000  # increased from 4000 — fixes truncation parse_fail

STATE_DIR = THIS_DIR / "_batch_state_gemini"
STATE_DIR.mkdir(exist_ok=True)


# ── HTTP helpers ──────────────────────────────────────────────────────────


def _http(method, url, body=None, headers=None, timeout=120):
    hdrs = headers or {}
    if isinstance(body, (dict, list)):
        hdrs.setdefault("Content-Type", "application/json")
        body = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {err[:500]}") from e


# ── DB fetch + prompt build ───────────────────────────────────────────────


def fetch_pending_rows(limit: int):
    """Return rows missing Phase 7 rationale, ordered by curator priority.

    S180 fix (2026-05-22 audit): pre-fix filter `beta_filter_v1.rule =
    'R4_rule_based_gold'` excluded the 15,321 R1-restored gold questions
    (audit_judged_high status). Result: gold pool rationale coverage was
    0% — beta launch blocked. New filter targets `auto_judged_high` +
    `bronze_clean` status directly (the two beta-eligible pools), with
    an env override to scope back to R4 for old-style batches.

    Env override:
      PHASE7_TARGET_RULE=R4_rule_based_gold  # legacy mode
      (unset)                                 # new mode: all gold/bronze
    """
    target_rule = os.getenv("PHASE7_TARGET_RULE", "").strip()
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    if target_rule:
        # Legacy: scope by beta_filter_v1.rule.
        cur.execute(
            """
            SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c,
                   q.option_d, q.option_e, q.correct_answer, q.subject_area,
                   q.exam_type, q.difficulty_level::text, q.bloom_category
            FROM question_bank q
            LEFT JOIN question_option_rationales r
              ON r.question_id = q.id::text AND r.option_letter = 'A'
            WHERE q.is_active AND q.question_text IS NOT NULL
              AND q.option_a IS NOT NULL
              AND q.correct_answer IN ('A','B','C','D','E')
              AND r.question_id IS NULL
              AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = %s
            ORDER BY q.created_at DESC
            LIMIT %s
            """,
            (target_rule, limit),
        )
    else:
        # Default: target beta-eligible pools by curator status.
        cur.execute(
            """
            SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c,
                   q.option_d, q.option_e, q.correct_answer, q.subject_area,
                   q.exam_type, q.difficulty_level::text, q.bloom_category
            FROM question_bank q
            LEFT JOIN question_option_rationales r
              ON r.question_id = q.id::text AND r.option_letter = 'A'
            WHERE q.is_active AND q.question_text IS NOT NULL
              AND q.option_a IS NOT NULL
              AND q.correct_answer IN ('A','B','C','D','E')
              AND r.question_id IS NULL
              AND q.quality_review_status IN ('auto_judged_high', 'bronze_clean')
            ORDER BY
              CASE q.quality_review_status
                WHEN 'auto_judged_high' THEN 0
                WHEN 'bronze_clean' THEN 1
                ELSE 2
              END,
              q.created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def build_prompt(row):
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


def build_request_line(row):
    qid = row[0]
    prompt = build_prompt(row)
    return {
        "key": qid,
        "request": {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
                "responseMimeType": "application/json",
            },
        },
    }


# ── CLI commands ──────────────────────────────────────────────────────────


def cmd_build(args):
    rows = fetch_pending_rows(args.limit)
    print(f"[build] Fetched {len(rows):,} pending rows")
    if not rows:
        print("[build] Done (nothing to do)")
        return

    # Save row metadata
    meta = {
        r[0]: {
            "correct_answer": r[7],
            "subject_area": r[8],
            "difficulty_level": r[10],
            "bloom_category": r[11],
        }
        for r in rows
    }
    (STATE_DIR / "rows_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[build] Saved metadata: {len(meta):,} rows")

    # Chunked JSONL files
    input_files = []
    for i in range(0, len(rows), BATCH_LIMIT):
        idx = i // BATCH_LIMIT
        chunk = rows[i : i + BATCH_LIMIT]
        path = STATE_DIR / f"batch_input_{idx:03d}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for row in chunk:
                f.write(json.dumps(build_request_line(row), ensure_ascii=False) + "\n")
        size_mb = path.stat().st_size / (1024 * 1024)
        print(
            f"[build] chunk {idx:03d}: {len(chunk):,} rows → {path.name} ({size_mb:.1f} MB)"
        )
        input_files.append(path.name)

    (STATE_DIR / "build_state.json").write_text(
        json.dumps({"input_files": input_files, "total_rows": len(rows)}, indent=2)
    )
    print(f"[build] Done. {len(input_files)} chunk(s).")


def upload_file_via_resumable(path: Path):
    """Resumable upload (large files). Returns file name (e.g. 'files/abc')."""
    size = path.stat().st_size
    # Step 1: start resumable session
    headers = {
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(size),
        "X-Goog-Upload-Header-Content-Type": "text/plain",
        "Content-Type": "application/json",
    }
    init_body = json.dumps({"file": {"display_name": path.stem}}).encode("utf-8")
    init_url = f"{UPLOAD_BASE}/files?key={GEMINI_KEY}"
    req = urllib.request.Request(
        init_url, data=init_body, headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        upload_url = resp.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise RuntimeError("Resumable upload: no X-Goog-Upload-URL")

    # Step 2: upload bytes
    headers2 = {
        "Content-Length": str(size),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize",
    }
    with path.open("rb") as f:
        data = f.read()
    req2 = urllib.request.Request(
        upload_url, data=data, headers=headers2, method="POST"
    )
    with urllib.request.urlopen(req2, timeout=600) as resp2:
        result = json.loads(resp2.read())
    return result["file"]["name"]  # "files/abc123"


def cmd_submit(args):
    state_path = STATE_DIR / "build_state.json"
    if not state_path.exists():
        print("[submit] No build_state.json")
        sys.exit(1)
    state = json.loads(state_path.read_text())

    batch_names = []
    for fname in state["input_files"]:
        path = STATE_DIR / fname
        print(
            f"[submit] Uploading {fname} ({path.stat().st_size / (1024 * 1024):.1f} MB)..."
        )
        try:
            file_name = upload_file_via_resumable(path)
        except Exception as e:
            print(f"[submit] Upload failed: {e}")
            sys.exit(2)
        print(f"[submit]   uploaded → {file_name}")

        print(f"[submit] Creating batch for {file_name}...")
        batch_body = {
            "batch": {
                "displayName": f"phase7_{path.stem}",
                "inputConfig": {"fileName": file_name},
            }
        }
        batch_resp = _http(
            "POST",
            f"{GEN_BASE}/models/{GEMINI_MODEL}:batchGenerateContent?key={GEMINI_KEY}",
            body=batch_body,
        )
        batch_name = batch_resp.get("name") or batch_resp.get("metadata", {}).get(
            "name"
        )
        if not batch_name:
            print(f"[submit] Unknown response: {json.dumps(batch_resp)[:500]}")
            sys.exit(3)
        print(f"[submit]   batch_name={batch_name}")
        batch_names.append(batch_name)

    (STATE_DIR / "submit_state.json").write_text(
        json.dumps(
            {"batch_names": batch_names, "submitted_at": int(time.time())}, indent=2
        )
    )
    print(f"\n[submit] All batches submitted: {batch_names}")


def cmd_poll(args):
    state_path = STATE_DIR / "submit_state.json"
    if not state_path.exists():
        print("[poll] No submit_state.json")
        sys.exit(1)
    state = json.loads(state_path.read_text())
    batch_names = state["batch_names"]

    all_done = True
    any_failed = False
    for bname in batch_names:
        info = _http("GET", f"{GEN_BASE}/{bname}?key={GEMINI_KEY}")
        meta = info.get("metadata", {})
        # Gemini status: BATCH_STATE_UNSPECIFIED, PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED, EXPIRED
        # Also: JOB_STATE_PENDING/RUNNING/SUCCEEDED etc.
        state_str = info.get("state") or meta.get("state") or "?"
        done = info.get("done", False)
        req_counts = meta.get("requestCounts", {}) or info.get("metadata", {}).get(
            "requestCounts", {}
        )
        completed = req_counts.get("succeededRequestCount", 0) or req_counts.get(
            "completed", 0
        )
        total = req_counts.get("totalRequestCount", 0) or req_counts.get("total", 0)
        failed = req_counts.get("failedRequestCount", 0) or req_counts.get("failed", 0)
        print(
            f"[poll] {bname} state={state_str} done={done} "
            f"completed={completed}/{total} failed={failed}"
        )
        if state_str not in ("JOB_STATE_SUCCEEDED", "BATCH_STATE_SUCCEEDED"):
            all_done = False
        if state_str in (
            "JOB_STATE_FAILED",
            "BATCH_STATE_FAILED",
            "JOB_STATE_CANCELLED",
            "JOB_STATE_EXPIRED",
        ):
            any_failed = True

    if all_done:
        sys.exit(0)
    if any_failed:
        sys.exit(2)
    sys.exit(1)


def download_file(file_name: str) -> bytes:
    """Download file content via Files API download endpoint."""
    url = f"https://generativelanguage.googleapis.com/download/v1beta/{file_name}:download?alt=media&key={GEMINI_KEY}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=600) as resp:
        return resp.read()


def cmd_apply(args):
    state_path = STATE_DIR / "submit_state.json"
    if not state_path.exists():
        print("[apply] No submit_state.json")
        sys.exit(1)
    state = json.loads(state_path.read_text())
    meta_path = STATE_DIR / "rows_meta.json"
    rows_meta = json.loads(meta_path.read_text(encoding="utf-8"))

    conn = psycopg2.connect(DSN)
    rationale_rows = []
    qb_updates = []
    math_rows = []
    success_n = 0
    fail_n = 0

    for bname in state["batch_names"]:
        info = _http("GET", f"{GEN_BASE}/{bname}?key={GEMINI_KEY}")
        dest = info.get("response", {}).get("responsesFile") or info.get(
            "metadata", {}
        ).get("outputFile")
        # Fallback: GET batch returns response.responsesFile when state SUCCEEDED
        if not dest:
            print(f"[apply] {bname} has no output file (state={info.get('state')})")
            continue
        print(f"[apply] Downloading {dest}...")
        raw = download_file(dest).decode("utf-8", errors="replace")

        for line in raw.splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            key = entry.get("key")
            response = entry.get("response")
            error = entry.get("error")

            if error or not response:
                fail_n += 1
                continue

            cands = response.get("candidates") or []
            if not cands:
                fail_n += 1
                continue

            parts = cands[0].get("content", {}).get("parts") or []
            content = "".join(p.get("text", "") for p in parts)
            content = content.replace("\x00", "").replace("\\u0000", "")
            parsed = parse_llm_response(content)
            if not parsed or not parsed.get("rationales"):
                fail_n += 1
                continue

            rationales = parsed.get("rationales", {}) or {}
            if sum(1 for v in rationales.values() if v) < 5:
                fail_n += 1
                continue

            m = rows_meta.get(key)
            if not m:
                fail_n += 1
                continue

            ca = m["correct_answer"]
            solo, marzano, is_math = derive_taxonomy(
                m["subject_area"], m["difficulty_level"], m["bloom_category"]
            )

            for letter in "ABCDE":
                rtxt = rationales.get(letter)
                if rtxt:
                    rationale_rows.append(
                        (key, letter, str(rtxt)[:1000], letter == ca, GEMINI_MODEL)
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
                    key,
                )
            )
            if is_math and formula:
                math_rows.append((key, formula))
            success_n += 1

    print(
        f"[apply] success={success_n:,} fail={fail_n:,} "
        f"rationale_rows={len(rationale_rows):,} qb_updates={len(qb_updates):,}"
    )

    if args.dry_run:
        print("[apply] DRY-RUN")
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
        print(f"[apply] DB FAILED: {e}")
        sys.exit(3)
    finally:
        conn.close()


def main():
    if not GEMINI_KEY:
        print("FATAL: GEMINI_API_KEY missing")
        sys.exit(1)

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("--limit", type=int, default=100_000)
    sub.add_parser("submit")
    sub.add_parser("poll")
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()
    {"build": cmd_build, "submit": cmd_submit, "poll": cmd_poll, "apply": cmd_apply}[
        args.cmd
    ](args)


if __name__ == "__main__":
    main()
