#!/usr/bin/env python3
"""
Bug #11 v2 — API-free Claude vision audit pipeline.

Strateji değişikliği (18 May 2026): Gemini API key gerekmez. Claude
(kendi Read tool'u) ile vision audit yapılır, Faz 4.1 pattern'i takip eder.

ADAM:
  1. fetch_samples(N) — random N sample seç (id, image_url, question_text)
  2. resolve_path(id) — image_url → local path
  3. images_to_inspect.tsv yaz: ID + path + truncated text (Claude için)
  4. Claude (insan döngüsünde) image'ları Read ile inceler
  5. claude_vision_verdict.tsv (manuel update veya batch write)
  6. apply_verdict.py — TSV verdict'i DB pipeline_metadata'ya yaz

Sample selection strateji:
  - Mevcut Bug #8 v2 fix sonrası pool: sayısal=46,020 + sözel=13,504
  - Stratified random: 5 random sayısal page-level olmayan (no_tier)
                       5 random sayısal eski tier (control)
                       5 random sözel page-level
                       5 random sözel no_tier
  - 20 sample = manageable batch (1 conversation turn)

USAGE:
  # Audit-bekleyen sample listesi üret (Claude için input)
  python backend/scripts/quality/image_audit_claude_vision.py --prepare 20

  # Verdict TSV'sini DB'ye apply et (Claude doldurduktan sonra)
  python backend/scripts/quality/image_audit_claude_vision.py --apply audit_RESULT.tsv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def resolve_image_path(image_url: str) -> Path | None:
    if not image_url or not image_url.startswith("/static/crops/"):
        return None
    rel = image_url[len("/static/crops/") :]
    return CROPS_BASE / rel


def prepare(n: int) -> int:
    """Stratified random N sample TSV üret (Claude audit için)."""
    from sqlalchemy import text

    eng = get_engine()
    today = datetime.now().strftime("%Y%m%d")
    out_path = PILOTS_DIR / f"{today}_claude_vision_audit_INPUT.tsv"

    # Stratified: sayısal vs sözel; tier var vs no_tier
    strata = {
        "sayısal_no_tier": (
            "subject_area IN ('MATEMATIK','FIZIK','GEOMETRI','KIMYA','BIYOLOJI','COGRAFYA')",
            "(pipeline_metadata::jsonb ->> 'match_tier') IS NULL",
        ),
        "sayısal_tier": (
            "subject_area IN ('MATEMATIK','FIZIK','GEOMETRI','KIMYA','BIYOLOJI','COGRAFYA')",
            "(pipeline_metadata::jsonb ->> 'match_tier') IS NOT NULL",
        ),
        "sözel_no_tier": (
            "subject_area IN ('TURKCE','EDEBIYAT','TARIH','SOSYAL','GENEL','FEN')",
            "(pipeline_metadata::jsonb ->> 'match_tier') IS NULL",
        ),
        "sözel_tier": (
            "subject_area IN ('TURKCE','EDEBIYAT','TARIH','SOSYAL','GENEL','FEN')",
            "(pipeline_metadata::jsonb ->> 'match_tier') IS NOT NULL",
        ),
    }
    per_stratum = max(1, n // len(strata))

    rows = []
    for stratum_name, (subj_where, tier_where) in strata.items():
        sql = f"""
            SELECT id::text AS id, subject_area, source_book, source_page,
                   pipeline_metadata::jsonb ->> 'match_tier' AS match_tier,
                   LEFT(question_text, 300) AS question_text_prefix,
                   question_image_url,
                   LENGTH(question_text) AS text_len,
                   '{stratum_name}' AS stratum
            FROM question_bank
            WHERE is_active = TRUE
              AND quality_review_status IN ('human_verified', 'auto_judged_high')
              AND question_image_url IS NOT NULL AND question_image_url != ''
              AND {subj_where}
              AND {tier_where}
              AND (
                  pipeline_metadata IS NULL
                  OR NOT (pipeline_metadata::jsonb ? 'image_audit_v1')
              )
            ORDER BY md5(id::text)
            LIMIT {per_stratum}
        """
        with eng.connect() as c:
            result = c.execute(text(sql)).fetchall()
            for r in result:
                rows.append(dict(r._mapping))

    # Local image path ekle
    for row in rows:
        p = resolve_image_path(row["question_image_url"])
        row["local_image_path"] = str(p) if p else ""
        row["image_exists"] = str(p.exists()) if p else "False"

    # Empty verdict columns (Claude için)
    audit_cols = [
        "has_options",
        "content_match",
        "image_quality",
        "primary_content",
        "notes",
    ]
    for r in rows:
        for c in audit_cols:
            r[c] = ""

    fieldnames = [
        "id",
        "stratum",
        "subject_area",
        "source_book",
        "source_page",
        "match_tier",
        "text_len",
        "question_text_prefix",
        "question_image_url",
        "local_image_path",
        "image_exists",
    ] + audit_cols

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"[prepared] {len(rows)} sample -> {out_path}")
    print("[stratum breakdown]:")
    from collections import Counter

    for k, v in Counter(r["stratum"] for r in rows).items():
        print(f"  {k}: {v}")
    print()
    print("Sonraki adım: Claude bu TSV'deki image'ları Read ile inceler,")
    print("audit_cols'a verdict yazar. Sonra --apply ile DB'ye yaz.")
    return 0


def apply_verdicts(tsv_path: Path) -> int:
    """TSV'deki Claude verdict'lerini DB pipeline_metadata.image_audit_v1'e yaz."""
    from sqlalchemy import text

    if not tsv_path.exists():
        print(f"HATA: {tsv_path} yok")
        return 2

    eng = get_engine()
    applied = 0
    skipped = 0
    with tsv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            qid = row["id"]
            has_options = row.get("has_options", "").strip().lower()
            content_match = row.get("content_match", "").strip().lower()
            quality = row.get("image_quality", "").strip().lower()
            if not has_options or not content_match:
                skipped += 1
                continue
            has_opts = has_options in ("true", "yes", "1", "t")
            cm = content_match in ("true", "yes", "1", "t")
            verdict = (
                "clean"
                if (not has_opts and cm)
                else ("salvage" if (has_opts and cm) else "reject")
            )
            audit_obj = {
                "audit_date": AUDIT_DATE,
                "auditor": "claude-vision-multi-session",
                "has_options": has_opts,
                "content_match": cm,
                "image_quality": quality or "unknown",
                "primary_content": row.get("primary_content", "").strip().lower()
                or "unknown",
                "notes": (row.get("notes", "") or "")[:200],
                "verdict": verdict,
            }
            audit_json = json.dumps(audit_obj, ensure_ascii=False)
            with eng.begin() as c:
                c.execute(
                    text(
                        """
                        UPDATE question_bank
                        SET pipeline_metadata = jsonb_set(
                                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                '{image_audit_v1}',
                                CAST(:audit AS jsonb),
                                TRUE
                            )::json,
                            updated_at = NOW()
                        WHERE id::text = :qid
                        """
                    ),
                    {"qid": qid, "audit": audit_json},
                )
            applied += 1

    print(f"[done] {applied} verdict DB'ye yazıldı, {skipped} satır boş atlandı")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", type=int, help="N stratified random sample TSV üret")
    ap.add_argument("--apply", type=str, help="TSV verdict'i DB'ye apply et")
    args = ap.parse_args()

    if args.prepare:
        return prepare(args.prepare)
    if args.apply:
        return apply_verdicts(Path(args.apply))

    print("HATA: --prepare N veya --apply TSV gerekli")
    return 2


if __name__ == "__main__":
    sys.exit(main())
