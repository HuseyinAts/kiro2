"""
audit_missing_image_repair_potential.py

READ-ONLY audit. DB veya disk DEGISTIRMEZ.

Amac: 49,313 sat`r `cin (has_diagram=true + image_url=null + unverified)
disk'te crop dosyas` var m`? Pipeline-fix m`mk`n m` kanitla.

Cikti: backend/_pilots/20260515_missing_image_repair_potential_RESULT.md

Kullanim: python audit_missing_image_repair_potential.py
"""

from __future__ import annotations

import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

CROPS_ROOT = Path("C:/Users/husey/kiro2/d-dataset/output/crops")
PSQL = "C:/Program Files/PostgreSQL/18/bin/psql.exe"
PG_PORT = "5434"
PG_USER = "postgres"
PG_DB = "kiro2"
PG_PASS = "1470"

OUTPUT_TSV = Path("C:/Users/husey/kiro2/backend/_pilots/_tmp_missing_image_rows.tsv")
RESULT_MD = Path(
    "C:/Users/husey/kiro2/backend/_pilots/20260515_missing_image_repair_potential_RESULT.md"
)

# 49,313 sat`r `cin SQL — id, source_book, source_page, q_no
EXPORT_SQL = r"""
SET client_encoding = 'UTF8';
\copy (SELECT id::text, source_book, source_page, pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' AS q_no, pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' AS match_quality FROM question_bank WHERE is_active = TRUE AND quality_review_status = 'unverified' AND question_image_url IS NULL AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram')::boolean = TRUE) TO 'C:/Users/husey/kiro2/backend/_pilots/_tmp_missing_image_rows.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true);
"""


def export_rows() -> int:
    """Export 49K rows to TSV. Returns row count."""
    sql_file = Path("C:/Users/husey/kiro2/backend/_pilots/_tmp_export_missing.sql")
    sql_file.write_text(EXPORT_SQL, encoding="utf-8")
    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASS
    result = subprocess.run(
        [PSQL, "-p", PG_PORT, "-U", PG_USER, "-d", PG_DB, "-f", str(sql_file)],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"psql export failed: {result.stderr}")
    sql_file.unlink()
    return sum(1 for _ in OUTPUT_TSV.open("r", encoding="utf-8")) - 1


def normalize_book(name: str) -> list[str]:
    """Disk'te dir adi varyantlari uret. Birden fazla deneme stratejisi."""
    if not name:
        return []
    candidates = []
    # Strategy 1: bosluk -> underscore
    candidates.append(name.replace(" ", "_"))
    # Strategy 2: bosluk -> underscore + Turkce karakter normalize (i -> i)
    s2 = name.replace(" ", "_")
    candidates.append(s2)
    # Strategy 3: lowercase
    candidates.append(name.replace(" ", "_").lower())
    return list(dict.fromkeys(candidates))  # dedup, preserve order


def find_book_dir(book_name: str, dir_index: dict[str, str]) -> str | None:
    """Disk dir index'ten case-insensitive match dene."""
    for cand in normalize_book(book_name):
        if cand in dir_index:
            return dir_index[cand]
        # Case-insensitive
        cand_lower = cand.lower()
        if cand_lower in dir_index:
            return dir_index[cand_lower]
    return None


def check_file_existence(
    book_dir: Path, page: int, q_no_raw: str
) -> tuple[str, list[str]]:
    """
    Returns (status, matching_files):
      - 'exact_match': p<page:04d>_q<qno:02d>.png var
      - 'page_match_other_q': page klasoru var ama q_no farkli
      - 'page_no_files': page meta var ama q* PNG yok
      - 'no_page_meta': p<page:04d>_meta.json bile yok
      - 'invalid_q_no': q_no parse edilemiyor
    """
    if not book_dir.exists():
        return "no_book_dir", []

    # q_no normalize
    try:
        q_no_int = int(q_no_raw)
    except (ValueError, TypeError):
        return "invalid_q_no", []

    page_prefix = f"p{page:04d}"
    expected_file = f"_{page_prefix}_q{q_no_int:02d}.png"

    # Tum dosyalari listele (cache disinda yavas olabilir)
    try:
        all_files = list(book_dir.iterdir())
    except (PermissionError, OSError):
        return "io_error", []

    page_files = [f.name for f in all_files if page_prefix in f.name]
    if not page_files:
        return "no_page_files", []

    # Exact match var mi?
    exact = [f for f in page_files if f.endswith(expected_file)]
    if exact:
        return "exact_match", exact

    # Page var ama q_no farkli mi?
    q_files = [f for f in page_files if "_q" in f and f.endswith(".png")]
    if q_files:
        return "page_match_other_q", q_files[:5]

    # Sadece meta json var
    return "page_no_q_files", page_files[:5]


def main() -> None:
    print("[1/4] DB'den 49K satir export ediliyor...")
    n_rows = export_rows()
    print(f"      -> {n_rows:,} satir TSV'ye yazildi")

    print("[2/4] Disk'teki kitap dir index'i kuruluyor...")
    dir_index: dict[str, str] = {}
    for p in CROPS_ROOT.iterdir():
        if p.is_dir():
            name = p.name
            dir_index[name] = str(p)
            dir_index[name.lower()] = str(p)
    print(f"      -> {len(set(dir_index.values())):,} kitap klasoru indekslendi")

    print("[3/4] Her satir icin disk check...")
    status_counts: Counter = Counter()
    book_dir_misses: Counter = Counter()
    match_quality_breakdown: dict[str, Counter] = defaultdict(Counter)
    sample_findings: dict[str, list[dict]] = defaultdict(list)

    with OUTPUT_TSV.open("r", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        col_idx = {col: i for i, col in enumerate(header)}

        for line_num, line in enumerate(f, 1):
            cols = line.rstrip("\n").split("\t")
            if len(cols) < len(header):
                continue
            qid = cols[col_idx["id"]]
            book = cols[col_idx["source_book"]]
            try:
                page = int(cols[col_idx["source_page"]])
            except (ValueError, TypeError):
                status_counts["invalid_page"] += 1
                continue
            q_no = cols[col_idx["q_no"]]
            mq = cols[col_idx["match_quality"]] or "null"

            book_dir_str = find_book_dir(book, dir_index)
            if book_dir_str is None:
                status_counts["no_book_dir"] += 1
                book_dir_misses[book] += 1
                match_quality_breakdown[mq]["no_book_dir"] += 1
                continue

            book_dir = Path(book_dir_str)
            status, files = check_file_existence(book_dir, page, q_no)
            status_counts[status] += 1
            match_quality_breakdown[mq][status] += 1

            if len(sample_findings[status]) < 3:
                sample_findings[status].append(
                    {
                        "id": qid,
                        "book": book,
                        "page": page,
                        "q_no": q_no,
                        "match_quality": mq,
                        "files_seen": files,
                    }
                )

            if line_num % 5000 == 0:
                print(f"      ... {line_num:,} satir islendi")

    print("[4/4] Rapor yaziliyor...")
    write_report(
        n_rows, status_counts, book_dir_misses, match_quality_breakdown, sample_findings
    )
    print(f"\n[OK] Rapor: {RESULT_MD}")
    print("\nOzet:")
    for status, n in status_counts.most_common():
        pct = 100.0 * n / n_rows
        print(f"  {status:30s} {n:>7,} ({pct:5.1f}%)")


def write_report(
    n_total: int,
    status_counts: Counter,
    book_dir_misses: Counter,
    mq_breakdown: dict[str, Counter],
    samples: dict[str, list[dict]],
) -> None:
    lines: list[str] = []
    lines.append("# Missing-Image Repair Potential — Audit RESULT")
    lines.append("")
    lines.append("**Tarih:** 15 May 2026 (Session 156 deeper analysis)")
    lines.append(
        "**Method:** Read-only DB+disk audit. 49,313 unverified+has_diagram=true+image=null satiri."
    )
    lines.append("**Cikti:** `pipeline-fix mumkun mu?` sorusunun veri-tabanli cevabi.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Ozet")
    lines.append("")
    lines.append(f"- **Toplam audit edilen:** {n_total:,} satir")
    lines.append("- **Disk'te toplam crop dir:** ~430 kitap, ~499K PNG")
    lines.append("")

    repairable = status_counts.get("exact_match", 0)
    pct_repair = 100.0 * repairable / n_total if n_total else 0
    lines.append(
        f"- **Pipeline-fix (exact match):** **{repairable:,} ({pct_repair:.1f}%)**"
    )
    lines.append("")
    lines.append("## Status dagilimi")
    lines.append("")
    lines.append("| Status | n | % | Anlam |")
    lines.append("|---|---|---|---|")

    status_meaning = {
        "exact_match": "✅ Disk'te tam dosya var, populate edilebilir",
        "page_match_other_q": "⚠️ Page var ama q_no eslesmiyor (q_no parsing problemi)",
        "page_no_q_files": "⚠️ Page meta var ama q*.png yok (crop atlanmis)",
        "no_page_files": "❌ Page hic yok (kitap dir'inde sayfa bulunamadi)",
        "no_book_dir": "❌ Kitap dir disk'te yok (Tier C eslestirmesi de gerekebilir)",
        "invalid_q_no": "❌ q_no parse edilemiyor (NULL veya garip karakter)",
        "invalid_page": "❌ source_page integer degil",
    }
    for status, n in status_counts.most_common():
        pct = 100.0 * n / n_total
        meaning = status_meaning.get(status, "?")
        lines.append(f"| `{status}` | {n:,} | {pct:.1f}% | {meaning} |")

    lines.append("")
    lines.append("## match_quality x status crosstab")
    lines.append("")
    lines.append(
        "| match_quality | exact_match | page_other_q | no_page_files | no_book_dir | other |"
    )
    lines.append("|---|---|---|---|---|---|")
    for mq in ["exact", "fuzzy", "fallback", "null"]:
        row = mq_breakdown.get(mq, Counter())
        em = row.get("exact_match", 0)
        po = row.get("page_match_other_q", 0)
        nf = row.get("no_page_files", 0)
        nd = row.get("no_book_dir", 0)
        other = sum(row.values()) - em - po - nf - nd
        total = sum(row.values())
        if total == 0:
            continue
        lines.append(f"| {mq} | {em:,} | {po:,} | {nf:,} | {nd:,} | {other:,} |")

    lines.append("")
    lines.append("## En cok eksik kitaplar (no_book_dir top 20)")
    lines.append("")
    lines.append("| Book | Eksik satir |")
    lines.append("|---|---|")
    for book, n in book_dir_misses.most_common(20):
        lines.append(f"| `{book[:60]}` | {n} |")

    lines.append("")
    lines.append("## Sample finding'ler (her status'tan 3 adet)")
    lines.append("")
    for status, items in samples.items():
        if not items:
            continue
        lines.append(f"### `{status}`")
        for item in items:
            files_preview = (
                ", ".join(item["files_seen"][:3]) if item["files_seen"] else "—"
            )
            lines.append(
                f"- id=`{item['id'][:8]}...` book=`{item['book'][:40]}` "
                f"page={item['page']} q_no={item['q_no']!r} mq={item['match_quality']} "
                f"files=[{files_preview}]"
            )
        lines.append("")

    lines.append("## Karar matrisi")
    lines.append("")
    if pct_repair >= 50:
        lines.append(
            f"✅ **Pipeline-fix YOL A.1 uygulanmali.** {repairable:,} satir ({pct_repair:.0f}%) "
        )
        lines.append(
            "dogrudan disk'ten populate edilebilir. Tier C scripti yazimi onerilir."
        )
    elif pct_repair >= 20:
        lines.append(
            f"⚠️ **Pipeline-fix kismen mumkun.** {repairable:,} satir ({pct_repair:.0f}%) yeterli"
        )
        lines.append(
            f"kazanim ama kalan %{100 - pct_repair:.0f} icin curator/judge gerekecek."
        )
    else:
        lines.append(
            f"❌ **Pipeline-fix marjinal.** Sadece {repairable:,} satir ({pct_repair:.0f}%)"
        )
        lines.append(
            "dogrudan repair edilebilir. Asil sorun crop generation'da, OCR rerun gerekebilir (E4)."
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "*Generated by `audit_missing_image_repair_potential.py` — read-only.*"
    )

    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
