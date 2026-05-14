"""
_prepare_scoring_files.py — read-only.

C1, C2, C3 RAW TSV dosyalarına verdict + error_type + notes
kolonlarini ekleyip _SCORING.tsv olarak yazar.

Kullanim: python _prepare_scoring_files.py
"""

from __future__ import annotations

import csv
from pathlib import Path

PILOTS = Path("C:/Users/husey/kiro2/backend/_pilots")

SOURCES = [
    ("20260515_audit_C1_RAW.tsv", "20260515_audit_C1_SCORING.tsv"),
    ("20260515_audit_C2_RAW.tsv", "20260515_audit_C2_SCORING.tsv"),
    ("20260515_audit_C3_RAW.tsv", "20260515_audit_C3_SCORING.tsv"),
]

EXTRA_COLS = ["verdict", "error_type", "notes"]


def main() -> None:
    for src_name, dst_name in SOURCES:
        src = PILOTS / src_name
        dst = PILOTS / dst_name

        if not src.exists():
            print(f"[SKIP] {src_name} yok")
            continue

        with src.open("r", encoding="utf-8", newline="") as f_in:
            reader = csv.reader(f_in, delimiter="\t", quotechar='"')
            rows = list(reader)

        if not rows:
            print(f"[SKIP] {src_name} bos")
            continue

        header = rows[0] + EXTRA_COLS
        new_rows = [header]
        for r in rows[1:]:
            # Pad row if shorter than header
            r = r + [""] * (len(header) - len(r))
            # Add empty extras
            new_rows.append(r[: len(rows[0])] + ["", "", ""])

        with dst.open("w", encoding="utf-8", newline="") as f_out:
            writer = csv.writer(
                f_out, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            writer.writerows(new_rows)

        print(f"[OK] {dst_name}: {len(new_rows) - 1} satir + 3 yeni kolon")


if __name__ == "__main__":
    main()
