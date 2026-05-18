#!/usr/bin/env python3
"""
Beta01 flag pattern systematic DB scanner (Faz 7.3 retrospective + cleanup).

Beta01 18 flag'inde 5 pattern kategorisi tespit edildi (15 gerçek bildirim):
  1. image_bound (9): "görsel eksik" — image olmadan çözülemez
  2. wrong_answer (1): math doğrulanır yanlış
  3. incomplete_text (2): paragraf yarıda, numaralı işaret eksik
  4. broken_text (2): paragraf cut-off
  5. latex_render_bug (1): opsiyonlarda raw \frac

Bu script tüm `auto_judged_high` pool'unda BENZER pattern'leri tarar
ve confirmed olanları toplu reject eder.

PATTERN'LER (beta01 flag'lerinden türetildi):

  IMAGE_BOUND (Bug #11 v2 regex genişletmesi):
    - 'görsel' (genel)
    - 'kavram harita'
    - 'deney düzene'
    - 'şekildeki kap'
    - 'cam boru.*bağlı'
    - 'numaraland.* özelli'
    - 'paralelkenar' + numeric ref (|AK|, |AB|, ABCD)

  BROKEN_TEXT (sonu yarıda Roman):
    - 'III\\s*$' / 'III\\.\\s*$' (Roman III sonra hiçbir şey)
    - 'III\\s*[a-z]' (Roman + lowercase devam — broken)

  INCOMPLETE_TEXT (numaralı işaret eksik metin):
    - Numaralı liste opsiyonlar (A: I, B: II, ...) ama metinde I/II/III/IV/V yok

  LATEX_OPTIONS_RAW (Bug #1 v2):
    - option_a/b/c/d/e içinde \frac, \\sqrt, \\pi, \\sum, \\int, \alpha vb.
    - Frontend MathText wrap eksik (Bug #1 sadece question_text fix etti)

USAGE:
  python backend/scripts/quality/beta_pattern_scanner.py --scan
  python backend/scripts/quality/beta_pattern_scanner.py --sample CATEGORY
  python backend/scripts/quality/beta_pattern_scanner.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")

# Pattern definitions: (category, predicate, reason)
# Predicate: SQL fragment to be ANDed with auto_judged_high filter
PATTERNS = [
    # IMAGE_BOUND patterns
    (
        "image_gorsel",
        "question_text ~* 'görsel'",
        "Soru metni 'görsel' kelimesi içeriyor — image olmadan çözülemez",
    ),
    (
        "image_kavram_harita",
        "question_text ~* 'kavram harita'",
        "Tarih/sosyal — kavram haritası referansı",
    ),
    (
        "image_deney_duzene",
        "question_text ~* 'deney düzene'",
        "Fizik/kimya/biyoloji deney düzeneği şekli",
    ),
    (
        "image_sekildeki_kap",
        "question_text ~* 'şekildeki kap'",
        "Kimya — şekildeki kaplar (deney şekli)",
    ),
    (
        "image_cam_boru",
        "question_text ~* 'cam boru'",
        "Kimya — cam boru ile bağlı deney",
    ),
    (
        "image_numaraland_ozelli",
        "question_text ~* 'numaraland.* özelli'",
        "Numaralandırılmış özellik referansı (numbered list)",
    ),
    (
        "image_paralelkenar",
        "question_text ~* 'paralelkenar' AND question_text ~* '\\|[A-Z]{1,3}\\|'",
        "Geometri paralelkenar + segment notation (|AB|, |AKL|)",
    ),
    (
        "image_dikucgen",
        "question_text ~* '(dik üçgen|eşkenar üçgen|ikizkenar üçgen)' AND question_text ~* '\\|[A-Z]{1,3}\\|'",
        "Geometri üçgen + segment notation",
    ),
    (
        "image_abcd_segment",
        "question_text ~* 'ABCD' AND question_text ~* '\\|[A-Z]{1,3}\\|'",
        "ABCD figür + segment notation",
    ),
    # BROKEN_TEXT patterns
    (
        "broken_ends_III",
        "question_text ~ ' III\\s*$' OR question_text ~ ' II\\s*$' OR question_text ~ ' IV\\s*$'",
        "Roman numaralı liste yarıda kesik (sonu II/III/IV)",
    ),
    (
        "broken_ends_dotdot",
        "question_text ~ '\\.\\s*\\.\\.\\.\\s*$'",
        "Paragraf '...' ile bitiyor (truncation indicator)",
    ),
    # INCOMPLETE_TEXT — options reference I/II/III but no Roman in text
    # NOTE: complex predicate, false positive risk → skip aggressive apply
    (
        "incomplete_roman_options_no_text",
        (
            "(option_a ~* '(yalnız|I, II|I ve|II ve|III ve)' "
            "OR option_b ~* '(yalnız|I, II|I ve|II ve|III ve)') "
            "AND question_text !~ 'I\\.\\s' AND question_text !~ 'II\\.\\s'"
        ),
        "Opsiyonlarda Roman list var ama metinde işaret yok",
    ),
    # LATEX_OPTIONS_RAW — Bug #1 v2 (options için MathText wrap eksik)
    (
        "latex_options_frac",
        (
            "(option_a ~ '\\\\frac' OR option_b ~ '\\\\frac' OR option_c ~ '\\\\frac' "
            "OR option_d ~ '\\\\frac' OR option_e ~ '\\\\frac')"
        ),
        "Opsiyonlarda \\frac raw — Frontend MathText wrap eksik (Bug #1 v2)",
    ),
    (
        "latex_options_sqrt",
        (
            "(option_a ~ '\\\\sqrt' OR option_b ~ '\\\\sqrt' OR option_c ~ '\\\\sqrt' "
            "OR option_d ~ '\\\\sqrt' OR option_e ~ '\\\\sqrt')"
        ),
        "Opsiyonlarda \\sqrt raw — Bug #1 v2",
    ),
    (
        "latex_options_alpha_beta",
        (
            "(option_a ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_b ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_c ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_d ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_e ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)')"
        ),
        "Opsiyonlarda Greek/math symbol raw — Bug #1 v2",
    ),
]

# Reject sınırı: which categories to apply (HIGH confidence)
APPLY_CATEGORIES = {
    "image_gorsel",
    "image_kavram_harita",
    "image_deney_duzene",
    "image_sekildeki_kap",
    "image_cam_boru",
    "image_numaraland_ozelli",
    "image_paralelkenar",
    "image_dikucgen",
    "image_abcd_segment",
    "broken_ends_III",
    "broken_ends_dotdot",
    # incomplete_roman_options_no_text → MEDIUM risk, skip
    # LATEX patterns → frontend fix, soru içeriği OK, REJECT ETME
}


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def scan(eng) -> dict[str, int]:
    """Count auto_judged_high questions matching each pattern."""
    from sqlalchemy import text

    counts = {}
    for cat, pred, _ in PATTERNS:
        sql = (
            f"SELECT COUNT(*) FROM question_bank "
            f"WHERE is_active=true AND quality_review_status='auto_judged_high' "
            f"AND ({pred})"
        )
        with eng.connect() as c:
            counts[cat] = c.execute(text(sql)).scalar() or 0
    return counts


def sample(eng, category: str, n: int = 10) -> list:
    """Return N random samples from category for false-positive check."""
    from sqlalchemy import text

    pred = next((p for c, p, _ in PATTERNS if c == category), None)
    if not pred:
        return []

    sql = (
        f"SELECT id::text, source_book, "
        f"  LEFT(question_text, 250) AS qt, "
        f"  LEFT(option_a, 80) AS a, LEFT(option_b, 80) AS b, "
        f"  LEFT(option_c, 80) AS c, LEFT(option_d, 80) AS d, "
        f"  LEFT(option_e, 80) AS e "
        f"FROM question_bank "
        f"WHERE is_active=true AND quality_review_status='auto_judged_high' "
        f"AND ({pred}) "
        f"ORDER BY md5(id::text) LIMIT {n}"
    )
    with eng.connect() as c:
        return c.execute(text(sql)).fetchall()


def apply_reject(eng, dry_run: bool = True) -> dict:
    """Reject all APPLY_CATEGORIES patterns."""
    from sqlalchemy import text

    audit_obj = {"date": AUDIT_DATE, "source": "beta_pattern_scanner_v1"}
    audit_json = json.dumps(audit_obj)
    counts = {}

    for cat, pred, _ in PATTERNS:
        if cat not in APPLY_CATEGORIES:
            continue

        if dry_run:
            sql = (
                f"SELECT COUNT(*) FROM question_bank "
                f"WHERE is_active=true AND quality_review_status='auto_judged_high' "
                f"AND ({pred})"
            )
            with eng.connect() as c:
                counts[cat] = c.execute(text(sql)).scalar() or 0
        else:
            meta = json.dumps({"category": cat})
            sql = f"""
                UPDATE question_bank
                SET quality_review_status = 'rejected',
                    pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{{}}'::jsonb),
                        '{{beta_pattern_scan_v1}}',
                        CAST(:audit AS jsonb) || CAST(:meta AS jsonb),
                        TRUE
                    )::json,
                    updated_at = NOW()
                WHERE is_active=true
                  AND quality_review_status='auto_judged_high'
                  AND ({pred})
            """
            with eng.begin() as c:
                result = c.execute(text(sql), {"audit": audit_json, "meta": meta})
                counts[cat] = result.rowcount

    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true", help="Count patterns")
    ap.add_argument("--sample", type=str, help="Sample N rows for given category")
    ap.add_argument("--n", type=int, default=10, help="Sample size")
    ap.add_argument("--dry-run", action="store_true", help="Apply dry-run count")
    ap.add_argument("--apply", action="store_true", help="Apply reject")
    args = ap.parse_args()

    if not (args.scan or args.sample or args.dry_run or args.apply):
        print("[error] --scan|--sample|--dry-run|--apply gerekli")
        return 2

    eng = get_engine()
    today = datetime.now().strftime("%Y%m%d")

    if args.scan:
        counts = scan(eng)
        out = PILOTS_DIR / f"{today}_beta_pattern_scan_RESULT.md"
        lines = [
            "# Beta Pattern Scanner — Counts",
            f"\n**Date:** {AUDIT_DATE}\n",
            "| Category | Count | Reason |\n|---|---|---|",
        ]
        for cat, _, reason in PATTERNS:
            n = counts.get(cat, 0)
            marker = "✅ APPLY" if cat in APPLY_CATEGORIES else "⏭ SKIP"
            lines.append(f"| `{cat}` | {n:,} | {marker} {reason} |")
        lines.append("\n**Total auto_judged_high:** ")
        from sqlalchemy import text

        with eng.connect() as c:
            total = c.execute(
                text(
                    "SELECT COUNT(*) FROM question_bank "
                    "WHERE is_active=true AND quality_review_status='auto_judged_high'"
                )
            ).scalar()
        lines.append(f"{total:,}")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n[scan] {total:,} total auto_judged_high")
        for cat, n in counts.items():
            marker = "✅" if cat in APPLY_CATEGORIES else "⏭"
            print(f"  {marker} {cat}: {n:,}")
        print(f"\n[result] {out}")

    elif args.sample:
        rows = sample(eng, args.sample, args.n)
        out = PILOTS_DIR / f"{today}_sample_{args.sample}.md"
        lines = [f"# Sample {args.sample} (N={len(rows)})\n"]
        for row in rows:
            lines.append(f"\n## `{row.id[:8]}` — {row.source_book}\n")
            qt = (row.qt or "").replace("\n", " ")
            lines.append(f"**Text:** {qt}")
            lines.append(f"- A: {row.a}")
            lines.append(f"- B: {row.b}")
            lines.append(f"- C: {row.c}")
            lines.append(f"- D: {row.d}")
            lines.append(f"- E: {row.e}")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[sample] {args.sample}: {len(rows)} satır → {out}")

    elif args.dry_run or args.apply:
        counts = apply_reject(eng, dry_run=args.dry_run)
        total = sum(counts.values())
        mode = "dry-run" if args.dry_run else "apply"
        out = PILOTS_DIR / f"{today}_beta_pattern_{mode}_RESULT.md"

        lines = [
            f"# Beta Pattern Scanner — {mode.upper()} RESULT",
            f"\n**Date:** {AUDIT_DATE}\n",
            "## Per Category\n",
            "| Category | Count |\n|---|---|",
        ]
        for cat, n in counts.items():
            lines.append(f"| `{cat}` | {n:,} |")
        lines.append(f"| **TOTAL** | **{total:,}** |\n")

        from sqlalchemy import text

        with eng.connect() as c:
            post = c.execute(
                text(
                    "SELECT quality_review_status, COUNT(*) FROM question_bank "
                    "WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC"
                )
            ).fetchall()
            view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
        lines.append("## Post State\n")
        lines.append("| Status | Count |\n|---|---|")
        for s, n in post:
            lines.append(f"| {s} | {n:,} |")
        lines.append(f"\n**v_safe_for_beta:** {view:,}")

        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n[{mode}] TOTAL: {total:,}")
        for cat, n in counts.items():
            print(f"  {cat}: {n:,}")
        print(f"\n[v_safe_for_beta] {view:,}")
        print(f"[result] {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
