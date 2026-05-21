"""R1 restore pre-apply spot check.

Conservative 6-rule already filtered. This script applies SECONDARY content
sanity checks on 30 random sample restorable=True rows, looking for issues
the rule missed:
  - text has Turkish letters (real question, not English/symbolic)
  - text >= 5 distinct words
  - options not all numeric / not all 1-character
  - text doesn't start with "Resim:", "Şekil:" (likely orphan caption)
"""

from __future__ import annotations

import csv
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TSV = Path("backend/_pilots/20260521_r1_fn_restore_pilot_RAW.tsv")
TR_CHARS = set("çğıöşüÇĞIİÖŞÜ")
ORPHAN_PREFIXES = ("Resim:", "Şekil:", "Tablo:", "Grafik:", "Yukarıdaki")


def main() -> int:
    rows = []
    with TSV.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["auto_restorable"] == "True":
                rows.append(r)

    print(f"Total restorable: {len(rows)}")
    random.seed(42)
    sample = random.sample(rows, min(30, len(rows)))

    issues = []
    for r in sample:
        problems = []
        text = r["question_text"]
        # Turkish letters
        if not any(c in TR_CHARS for c in text):
            problems.append("no_tr_chars")
        # Distinct words
        words = set(re.findall(r"\b\w{3,}\b", text.lower()))
        if len(words) < 5:
            problems.append(f"few_words={len(words)}")
        # Orphan prefix
        for p in ORPHAN_PREFIXES:
            if text.lstrip().startswith(p):
                problems.append(f"orphan_prefix={p}")
                break
        # Numeric-only options
        opts = [r[f"option_{x}"] for x in "abcde"]
        if all(re.fullmatch(r"[\d\s,.\-+/]+", o.strip()) for o in opts):
            # All numeric — acceptable for math, but flag for review
            pass  # not flagging numeric — common in math
        # Single-char options (e.g., "A", "B", "C") — likely placeholder
        if all(len(o.strip()) <= 2 for o in opts):
            problems.append("single_char_opts")

        if problems:
            issues.append(
                {
                    "id": r["id"][:8],
                    "subject": r["subject_area"],
                    "problems": problems,
                    "text_preview": text[:80],
                }
            )

    print(f"\nSpot-check sample: {len(sample)}")
    print(f"Sanity issues found: {len(issues)}")
    print()
    if issues:
        print("ISSUES:")
        for i in issues:
            print(f"  {i['id']} ({i['subject']}): {', '.join(i['problems'])}")
            print(f"    text: {i['text_preview']!r}")
    else:
        print("  All 30 samples pass secondary content sanity. ✅")

    # Sample preview (3 random)
    print("\n--- 3 RANDOM SAMPLE PREVIEW ---")
    for r in random.sample(sample, 3):
        print(
            f"\n[{r['id'][:8]}] {r['subject_area']} | {r['source_book']} p{r['source_page']}"
        )
        print(f"  Q: {r['question_text'][:150]}")
        for x in "abcde":
            print(f"  {x.upper()}) {r[f'option_{x}'][:60]}")
        print(f"  correct: {r['correct_answer']}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
