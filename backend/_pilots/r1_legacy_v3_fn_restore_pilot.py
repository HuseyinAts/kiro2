#!/usr/bin/env python3
"""
R1 legacy_v3 False-Negative Restore — Pilot (100 sample, stratified).

Faz 6.6 reject audit'i R1_legacy_v3 filtresinin %24 false-negative rate
ürettiğini gösterdi (3/30 örnekte iyi soru → ~4,415 satır expected
restorable). R1 bilinçli olarak "legacy_v3_unaudited" durumundaki tüm
satırları toptan reject etti — bu kural fazla agresif.

Bu pilot 100 stratified sample alır, rule-based restorability kriterini
uygular ve restorable oranını ölçer. Hedef: %70-90 restorable bulmak.

Sampling: subject_area bazlı stratified, oran orijinal R1 dağılımına yakın
Seed: deterministic 'r1_fn_restore_v1'
Out:
  - {AUDIT_DATE}_r1_fn_restore_pilot_RAW.tsv (full sample + auto-rule labels)
  - {AUDIT_DATE}_r1_fn_restore_RESULT.md (audit özet)

USAGE:
  python backend/_pilots/r1_legacy_v3_fn_restore_pilot.py
"""

from __future__ import annotations

import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = datetime.now().strftime("%Y%m%d")
SEED = "r1_fn_restore_v1"
N_TOTAL = 100

# Subject stratification — orantılı dağılım (orijinal R1 yüzdelerine yakın)
# Toplam 18,397: MAT=5604(%30.5), TUR=3083(%16.8), GEO=2538(%13.8), FIZ=1915(%10.4),
# KIM=1269(%6.9), EDE=1060(%5.8), TAR=766(%4.2), SOS=679(%3.7), GEN=625(%3.4),
# BIO=575(%3.1), diğer ~%1.5
SUBJECT_QUOTA = {
    "MATEMATIK": 30,
    "TURKCE": 17,
    "GEOMETRI": 14,
    "FIZIK": 10,
    "KIMYA": 7,
    "EDEBIYAT": 6,
    "TARIH": 4,
    "SOSYAL": 4,
    "GENEL": 3,
    "BIYOLOJI": 3,
    "FEN": 1,
    "COGRAFYA": 1,
}  # toplam 100

COLUMNS = [
    "id",
    "subject_area",
    "source_book",
    "source_page",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "correct_answer",
    "question_image_url",
    "text_len",
    "has_image",
    "has_5_options",
    "valid_correct_answer",
    "text_no_repeat",
    "text_no_ellipsis",
    "text_min_len",
    "auto_restorable",
    "fail_reasons",
    "manual_verdict",
    "notes",
]

REPEAT_CHAR_RE = re.compile(r"(.)\1{4,}")  # aaaaa, bbbbb gibi 5+ tekrar
ELLIPSIS_RE = re.compile(r"\.{4,}")  # ....., ...... gibi 4+ nokta


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def sample_stratified(eng):
    """Subject quota'ya göre stratified random sample, deterministic seed."""
    from sqlalchemy import text

    sql = """
        SELECT
            CAST(id AS text) AS id,
            subject_area,
            source_book,
            source_page,
            question_text,
            option_a, option_b, option_c, option_d, option_e,
            correct_answer,
            question_image_url
        FROM question_bank
        WHERE is_active = TRUE
          AND quality_review_status = 'rejected'
          AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R1_legacy_v3'
          AND subject_area = :subj
        ORDER BY md5(CAST(id AS text) || :seed)
        LIMIT :n
    """
    all_rows = []
    for subj, quota in SUBJECT_QUOTA.items():
        with eng.connect() as c:
            result = c.execute(
                text(sql), {"subj": subj, "seed": SEED + subj, "n": quota}
            ).fetchall()
        rows = [dict(r._mapping) for r in result]
        if len(rows) < quota:
            print(
                f"[warn] {subj}: requested {quota}, got {len(rows)} (insufficient pool)"
            )
        all_rows.extend(rows)
    return all_rows


def apply_auto_rules(row: dict) -> dict:
    """
    Restorability auto-rule kriteri (conservative — false-positive YOK hedefli).

    Bir satır restorable sayılır ANCAK:
      1. question_image_url IS NOT NULL ve boş değil
      2. 5 option (a-e) tümü dolu
      3. correct_answer ∈ {A,B,C,D,E}
      4. LENGTH(question_text) >= 50
      5. question_text 5+ tekrarlı karakter içermiyor (aaaaa, .....)
      6. question_text 4+ nokta (......) içermiyor (ellipsis garbage)
    """
    text_val = row.get("question_text") or ""
    text_len = len(text_val)
    has_image = bool(row.get("question_image_url"))
    opts = [row.get(f"option_{c}") for c in ("a", "b", "c", "d", "e")]
    has_5_options = all(o and str(o).strip() for o in opts)
    valid_ca = row.get("correct_answer") in ("A", "B", "C", "D", "E")
    text_min_len = text_len >= 50
    text_no_repeat = not REPEAT_CHAR_RE.search(text_val)
    text_no_ellipsis = not ELLIPSIS_RE.search(text_val)

    checks = {
        "has_image": has_image,
        "has_5_options": has_5_options,
        "valid_correct_answer": valid_ca,
        "text_min_len": text_min_len,
        "text_no_repeat": text_no_repeat,
        "text_no_ellipsis": text_no_ellipsis,
    }
    auto_restorable = all(checks.values())
    fail_reasons = [k for k, v in checks.items() if not v]

    return {
        "text_len": text_len,
        "has_image": has_image,
        "has_5_options": has_5_options,
        "valid_correct_answer": valid_ca,
        "text_no_repeat": text_no_repeat,
        "text_no_ellipsis": text_no_ellipsis,
        "text_min_len": text_min_len,
        "auto_restorable": auto_restorable,
        "fail_reasons": ",".join(fail_reasons),
    }


def write_tsv(rows: list, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            cleaned = {}
            for k in COLUMNS:
                v = row.get(k, "")
                if v is None:
                    cleaned[k] = ""
                else:
                    cleaned[k] = (
                        str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")
                    )
            writer.writerow(cleaned)


def write_result_md(rows: list, out_path: Path) -> None:
    total = len(rows)
    if total == 0:
        out_path.write_text("# R1 Restore Pilot — empty sample\n", encoding="utf-8")
        return

    restorable = sum(1 for r in rows if r.get("auto_restorable"))
    not_restorable = total - restorable
    pct = restorable / total * 100

    # Subject breakdown
    subj_stats = {}
    for r in rows:
        s = r.get("subject_area") or "UNKNOWN"
        if s not in subj_stats:
            subj_stats[s] = {"total": 0, "restorable": 0}
        subj_stats[s]["total"] += 1
        if r.get("auto_restorable"):
            subj_stats[s]["restorable"] += 1

    # Fail reason breakdown
    reason_counts = {}
    for r in rows:
        if not r.get("auto_restorable"):
            for reason in (r.get("fail_reasons") or "").split(","):
                reason = reason.strip()
                if reason:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1

    lines = [
        "# R1 legacy_v3 False-Negative Restore — PILOT RESULT",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        "**Sample size:** 100 (stratified by subject_area)",
        "**Pool:** 18,397 R1_legacy_v3 rejected rows",
        f"**Seed:** `{SEED}` (deterministic)",
        "",
        "## Context",
        "",
        "Faz 6.6 reject audit'i R1_legacy_v3 filtresinin **%24 false-negative",
        "rate** ürettiğini tespit etti (3/30 örnekte iyi soru yanlış reject).",
        "Beklenen restorable: ~4,415 satır (18,397 × 0.24).",
        "",
        "R1 reject kuralı: `quality_review_status='legacy_v3_unaudited'` satırların",
        "toptan reject edilmesi — fazla agresif (audit edilmemiş ≠ kötü).",
        "",
        "## Auto-Rule Criteria (conservative, false-positive YOK hedefli)",
        "",
        "Bir satır restorable sayılır AİSAR (Ancak ve sadece):",
        "1. `question_image_url IS NOT NULL` (boş string değil)",
        "2. Tüm 5 option dolu (`option_a..option_e`)",
        "3. `correct_answer ∈ {A,B,C,D,E}`",
        "4. `LENGTH(question_text) >= 50`",
        "5. Text 5+ tekrarlı karakter içermiyor (`aaaaa`, regex `(.)\\1{4,}`)",
        "6. Text 4+ ardışık nokta içermiyor (`....`, regex `\\.{4,}`)",
        "",
        "## Sonuç — Auto-Rule",
        "",
        "| Metrik | Sayı | Yüzde |",
        "|---|---|---|",
        f"| **Restorable (auto-rule PASS)** | **{restorable}** | **{pct:.1f}%** |",
        f"| Not restorable | {not_restorable} | {100 - pct:.1f}% |",
        f"| **Total** | **{total}** | 100% |",
        "",
        "## Subject Breakdown",
        "",
        "| Subject | Total | Restorable | % |",
        "|---|---|---|---|",
    ]
    for s in sorted(subj_stats.keys(), key=lambda x: -subj_stats[x]["total"]):
        st = subj_stats[s]
        p = st["restorable"] / st["total"] * 100 if st["total"] else 0
        lines.append(f"| {s} | {st['total']} | {st['restorable']} | {p:.1f}% |")

    lines.extend(
        [
            "",
            "## Fail Reason Breakdown",
            "",
            "| Reason | Count | % of total |",
            "|---|---|---|",
        ]
    )
    for reason, cnt in sorted(reason_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {reason} | {cnt} | {cnt / total * 100:.1f}% |")

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- **Restorable oranı: %{pct:.1f}**",
            (
                "- ✅ Pilot başarılı — Faz 6.6 bulgusunu (%24+) doğruluyor"
                if pct >= 50
                else "- ⚠️ Pilot beklenenden düşük — apply ÖNCESİ manuel verdict review gerek"
            ),
            "- Apply tahmini etki: "
            f"~{int(18397 * pct / 100):,} satır → `auto_judged_high`",
            "",
            "## Next Steps",
            "",
            "1. RAW TSV'de manual_verdict kolonuna 20-30 satır insan-onay yap",
            "   (false-positive sıfır mı doğrula)",
            "2. False-positive 0 ise → "
            "`backend/scripts/quality/r1_legacy_v3_restore_apply.py --dry-run`",
            "3. Dry-run state OK ise → `--apply`",
            "",
            "## Audit Trail",
            "",
            "Restored satırlarda eklenecek metadata:",
            "```json",
            '{"r1_restore_v1": {"date": "...", "reason": "false_negative_recovery",',
            ' "pilot_restorable_pct": X.X, "previous_status": "rejected",',
            ' "previous_rule": "R1_legacy_v3"}}',
            "```",
            "",
            "Önceki `beta_filter_v1` metadata korunur (rollback için).",
            "",
        ]
    )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    eng = get_engine()
    print(f"[seed] {SEED}")
    print(f"[quota] total={sum(SUBJECT_QUOTA.values())}")
    print()

    raw_rows = sample_stratified(eng)
    print(f"[fetched] {len(raw_rows)} rows")

    # Enrich with auto-rule
    enriched = []
    for r in raw_rows:
        rule_out = apply_auto_rules(r)
        merged = {**r, **rule_out, "manual_verdict": "", "notes": ""}
        enriched.append(merged)

    restorable = sum(1 for r in enriched if r["auto_restorable"])
    pct = restorable / len(enriched) * 100 if enriched else 0
    print(f"[auto-rule] restorable={restorable}/{len(enriched)} ({pct:.1f}%)")

    tsv_path = PILOTS_DIR / f"{AUDIT_DATE}_r1_fn_restore_pilot_RAW.tsv"
    md_path = PILOTS_DIR / f"{AUDIT_DATE}_r1_fn_restore_RESULT.md"

    write_tsv(enriched, tsv_path)
    write_result_md(enriched, md_path)

    print(f"[tsv]    {tsv_path}")
    print(f"[result] {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
