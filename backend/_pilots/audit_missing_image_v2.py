"""
audit_missing_image_v2.py — OPTIMIZED.

Cache-based: her kitap dir'inin filename set'ini bir kere okur.
49K satir x 1 set lookup = O(N), iterdir 430 kere (kitap basina 1).

Cikti:
- backend/_pilots/20260515_missing_image_v2_RESULT.md
- TSV reuse: backend/_pilots/_tmp_missing_image_rows.tsv (v1'den)
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

CROPS_ROOT = Path("C:/Users/husey/kiro2/d-dataset/output/crops")
INPUT_TSV = Path("C:/Users/husey/kiro2/backend/_pilots/_tmp_missing_image_rows.tsv")
RESULT_MD = Path(
    "C:/Users/husey/kiro2/backend/_pilots/20260515_missing_image_v2_RESULT.md"
)


def normalize_book(name: str) -> list[str]:
    if not name:
        return []
    base = name.replace(" ", "_")
    return list(dict.fromkeys([base, base.lower()]))


def main() -> None:
    if not INPUT_TSV.exists():
        print(f"ERROR: {INPUT_TSV} yok. Once v1 scriptini calistir.")
        return

    print("[1/3] Disk index ve dosya cache'i kuruluyor...")
    print("      (430 kitap dir x ~3000 dosya = ~30s)")

    dir_index: dict[str, Path] = {}
    file_cache: dict[Path, set[str]] = {}

    for p in CROPS_ROOT.iterdir():
        if not p.is_dir():
            continue
        dir_index[p.name] = p
        dir_index[p.name.lower()] = p
        try:
            file_cache[p] = {f.name for f in p.iterdir() if f.is_file()}
        except (PermissionError, OSError):
            file_cache[p] = set()

    n_books = len(set(dir_index.values()))
    n_files = sum(len(s) for s in file_cache.values())
    print(f"      OK: {n_books} kitap, {n_files:,} dosya cache'lendi")

    print("[2/3] 49K satir taranyor...")

    status_counts: Counter = Counter()
    book_dir_misses: Counter = Counter()
    mq_breakdown: dict[str, Counter] = defaultdict(Counter)
    sample: dict[str, list[dict]] = defaultdict(list)

    n_total = 0
    with INPUT_TSV.open("r", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        idx = {col: i for i, col in enumerate(header)}

        for line in f:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < len(header):
                continue
            n_total += 1
            qid = cols[idx["id"]]
            book = cols[idx["source_book"]]
            try:
                page = int(cols[idx["source_page"]])
            except (ValueError, TypeError):
                status_counts["invalid_page"] += 1
                continue
            q_no_raw = cols[idx["q_no"]]
            mq = cols[idx["match_quality"]] or "null"

            # Book dir lookup
            book_dir = None
            for cand in normalize_book(book):
                if cand in dir_index:
                    book_dir = dir_index[cand]
                    break
                if cand.lower() in dir_index:
                    book_dir = dir_index[cand.lower()]
                    break

            if book_dir is None:
                status_counts["no_book_dir"] += 1
                book_dir_misses[book] += 1
                mq_breakdown[mq]["no_book_dir"] += 1
                continue

            try:
                q_no_int = int(q_no_raw)
            except (ValueError, TypeError):
                status_counts["invalid_q_no"] += 1
                mq_breakdown[mq]["invalid_q_no"] += 1
                continue

            files = file_cache[book_dir]
            page_prefix = f"p{page:04d}"
            expected_suffix = f"_{page_prefix}_q{q_no_int:02d}.png"

            # Exact match (any file ending with expected suffix)
            exact_matches = [f for f in files if f.endswith(expected_suffix)]
            if exact_matches:
                status_counts["exact_match"] += 1
                mq_breakdown[mq]["exact_match"] += 1
                if len(sample["exact_match"]) < 3:
                    sample["exact_match"].append(
                        {
                            "id": qid,
                            "book": book,
                            "page": page,
                            "q": q_no_raw,
                            "mq": mq,
                            "files": exact_matches[:2],
                        }
                    )
                continue

            # Page var mi?
            page_files = [f for f in files if page_prefix in f]
            if page_files:
                q_files = [f for f in page_files if "_q" in f and f.endswith(".png")]
                if q_files:
                    status_counts["page_match_other_q"] += 1
                    mq_breakdown[mq]["page_match_other_q"] += 1
                    if len(sample["page_match_other_q"]) < 3:
                        sample["page_match_other_q"].append(
                            {
                                "id": qid,
                                "book": book,
                                "page": page,
                                "q": q_no_raw,
                                "mq": mq,
                                "files": q_files[:5],
                            }
                        )
                    continue
                status_counts["page_no_q_files"] += 1
                mq_breakdown[mq]["page_no_q_files"] += 1
                if len(sample["page_no_q_files"]) < 3:
                    sample["page_no_q_files"].append(
                        {
                            "id": qid,
                            "book": book,
                            "page": page,
                            "q": q_no_raw,
                            "mq": mq,
                            "files": page_files[:3],
                        }
                    )
                continue

            status_counts["no_page_files"] += 1
            mq_breakdown[mq]["no_page_files"] += 1
            if len(sample["no_page_files"]) < 3:
                sample["no_page_files"].append(
                    {
                        "id": qid,
                        "book": book,
                        "page": page,
                        "q": q_no_raw,
                        "mq": mq,
                        "files": [],
                    }
                )

            if n_total % 10000 == 0:
                print(f"      ... {n_total:,} / 49,313")

    print(f"      OK: {n_total:,} satir tarandi")

    print("[3/3] Rapor yaziliyor...")
    write_report(n_total, status_counts, book_dir_misses, mq_breakdown, sample)
    print(f"\n[OK] Rapor: {RESULT_MD}\n")
    print("OZET:")
    for st, n in status_counts.most_common():
        pct = 100.0 * n / n_total
        print(f"  {st:25s} {n:>7,} ({pct:5.1f}%)")


def write_report(
    n_total: int,
    status_counts: Counter,
    book_dir_misses: Counter,
    mq_breakdown: dict[str, Counter],
    sample: dict[str, list[dict]],
) -> None:
    lines: list[str] = []
    lines.append("# Missing-Image Repair Potential — Audit RESULT v2")
    lines.append("")
    lines.append("**Tarih:** 14 May 2026 (Session 156 deeper analysis)")
    lines.append("**Input:** 49,313 satir (unverified + has_diagram=true + image=null)")
    lines.append("**Method:** Read-only DB+disk audit. Disk dosya cache'li.")
    lines.append("")

    repairable = status_counts.get("exact_match", 0)
    pct_repair = 100.0 * repairable / n_total if n_total else 0
    other_q = status_counts.get("page_match_other_q", 0)
    pct_other_q = 100.0 * other_q / n_total if n_total else 0

    lines.append("## TL;DR")
    lines.append("")
    lines.append(
        f"- **Pipeline-fix DOGRUDAN (exact_match):** {repairable:,} ({pct_repair:.1f}%)"
    )
    lines.append(
        f"- **Pipeline-fix MUMKUN ama q_no fix gerekli:** {other_q:,} ({pct_other_q:.1f}%)"
    )
    lines.append(
        f"- **TOPLAM pipeline-fix potansiyeli:** {repairable + other_q:,} ({pct_repair + pct_other_q:.1f}%)"
    )
    lines.append("")

    lines.append("## Status dagilimi")
    lines.append("")
    lines.append("| Status | n | % | Anlam |")
    lines.append("|---|---|---|---|")

    meaning = {
        "exact_match": "Disk'te tam dosya var, populate edilebilir",
        "page_match_other_q": "Page'in baska crop'lari var, q_no parsing gerekli",
        "page_no_q_files": "Sadece meta.json var, q*.png yok (crop atlanmis)",
        "no_page_files": "Page hic yok kitap dir'inde",
        "no_book_dir": "Kitap dir disk'te yok (kitap adi mismatch)",
        "invalid_q_no": "q_no parse edilemiyor",
        "invalid_page": "source_page integer degil",
    }
    for st, n in status_counts.most_common():
        pct = 100.0 * n / n_total
        lines.append(f"| `{st}` | {n:,} | {pct:.1f}% | {meaning.get(st, '?')} |")

    lines.append("")
    lines.append("## match_quality x status crosstab")
    lines.append("")
    lines.append(
        "| match_quality | exact | page_other_q | page_no_q | no_page | no_dir | other |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for mq in ["exact", "fuzzy", "fallback", "null"]:
        row = mq_breakdown.get(mq, Counter())
        em = row.get("exact_match", 0)
        po = row.get("page_match_other_q", 0)
        pn = row.get("page_no_q_files", 0)
        nf = row.get("no_page_files", 0)
        nd = row.get("no_book_dir", 0)
        total = sum(row.values())
        other = total - em - po - pn - nf - nd
        if total == 0:
            continue
        lines.append(
            f"| {mq} | {em:,} | {po:,} | {pn:,} | {nf:,} | {nd:,} | {other:,} |"
        )

    lines.append("")
    lines.append("## En cok eksik kitaplar (no_book_dir top 20)")
    lines.append("")
    lines.append("| Book | Eksik satir |")
    lines.append("|---|---|")
    for book, n in book_dir_misses.most_common(20):
        book_short = book[:60].replace("|", "/")
        lines.append(f"| `{book_short}` | {n} |")

    lines.append("")
    lines.append("## Sample finding'ler")
    lines.append("")
    for st, items in sample.items():
        if not items:
            continue
        lines.append(f"### `{st}`")
        for item in items:
            files_str = ", ".join(item["files"][:3]) if item["files"] else "—"
            book_short = item["book"][:50].replace("|", "/")
            lines.append(
                f"- id=`{item['id'][:8]}...` book=`{book_short}` "
                f"page={item['page']} q_no={item['q']!r} mq={item['mq']} "
                f"files=[{files_str}]"
            )
        lines.append("")

    lines.append("## Karar matrisi")
    lines.append("")
    total_fix_possible = pct_repair + pct_other_q
    if total_fix_possible >= 60:
        lines.append(
            f"**ONERI: YOL A.1 (Tier C image matcher) UYGULA.** "
            f"%{total_fix_possible:.0f} pipeline-fix ile cozulebilir. "
            f"%{pct_repair:.0f} dogrudan, %{pct_other_q:.0f} q_no parse fix ile."
        )
    elif total_fix_possible >= 30:
        lines.append(
            f"**ONERI: YOL A.1 KISMEN UYGULA.** "
            f"%{total_fix_possible:.0f} pipeline-fix mumkun ama kalan %{100 - total_fix_possible:.0f} "
            f"icin curator/judge gerekecek."
        )
    else:
        lines.append(
            f"**ONERI: PIPELINE-FIX MARJINAL.** Sadece %{total_fix_possible:.0f} repair edilebilir. "
            f"Crop generation aşaması basarisiz, OCR rerun (E4) duşunulmeli."
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `audit_missing_image_v2.py` — read-only.*")

    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
