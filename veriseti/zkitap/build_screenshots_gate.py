#!/usr/bin/env python3
"""
Build gating artifacts for zkitap screenshots dataset.

Outputs:
- screenshots_allowlist.txt
- screenshots_exclude_dirs.txt
- screenshots_merge_plan.csv
- screenshots_quality_status.json
- screenshots_pdf_missing_dirs.txt
- screenshots_no_json_priority.tsv
- screenshots_only_metadata_dirs.txt
- screenshots_no_png_dirs.txt
"""

from __future__ import annotations

import json
import os
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class DirInfo:
    name: str
    total_files: int
    png_count: int
    json_count: int
    pdf_count: int
    ini_count: int
    lnk_count: int

    @property
    def only_metadata(self) -> bool:
        return self.total_files > 0 and (self.ini_count + self.lnk_count) == self.total_files

    @property
    def json_per_png_ratio(self) -> float:
        if self.png_count == 0:
            return 0.0
        return self.json_count / self.png_count


def turkish_lower_nfc(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = value.replace("İ", "i").replace("I", "ı")
    return value.lower()


def canonical_name(value: str) -> str:
    lowered = turkish_lower_nfc(value)
    return "".join(ch for ch in lowered if ch.isalnum())


def scan_dirs(root: Path) -> List[DirInfo]:
    rows: List[DirInfo] = []
    dir_names = []
    with os.scandir(root) as root_entries:
        for entry in root_entries:
            if entry.is_dir(follow_symlinks=False):
                dir_names.append(entry.name)

    for dir_name in sorted(dir_names):
        d = root / dir_name
        counts = Counter()
        total_files = 0
        with os.scandir(d) as dir_entries:
            for entry in dir_entries:
                if entry.is_file(follow_symlinks=False):
                    total_files += 1
                    ext = Path(entry.name).suffix.lower()
                    counts[ext] += 1
        rows.append(
            DirInfo(
                name=dir_name,
                total_files=total_files,
                png_count=counts[".png"],
                json_count=counts[".json"],
                pdf_count=counts[".pdf"],
                ini_count=counts[".ini"],
                lnk_count=counts[".lnk"],
            )
        )
    return rows


def main() -> int:
    root = Path("veriseti/zkitap/screenshots")
    out_dir = Path("veriseti/zkitap")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = scan_dirs(root)
    groups = defaultdict(list)
    for r in rows:
        groups[canonical_name(r.name)].append(r.name)

    merge_plan = []
    primary_by_group = {}
    for key, names in groups.items():
        sorted_names = sorted(names)
        primary = sorted_names[0]
        primary_by_group[key] = primary
        for dup in sorted_names[1:]:
            merge_plan.append(
                {
                    "canonical": key,
                    "primary": primary,
                    "duplicate": dup,
                    "reason": "canonical_duplicate",
                }
            )

    allowlist: List[str] = []
    exclude = []
    missing_pdf_dirs: List[str] = []
    no_json_priority_rows: List[str] = []
    reason_counts = Counter()
    only_metadata_dirs: List[str] = []
    no_png_dirs: List[str] = []
    total_png = 0
    total_json = 0
    total_pdf = 0
    with_png = 0
    with_json = 0
    with_pdf = 0
    empty_dirs = 0

    for r in rows:
        total_png += r.png_count
        total_json += r.json_count
        total_pdf += r.pdf_count
        if r.total_files == 0:
            empty_dirs += 1
        if r.png_count > 0:
            with_png += 1
        if r.json_count > 0:
            with_json += 1
        if r.pdf_count > 0:
            with_pdf += 1
        reason = []
        if r.png_count == 0:
            reason.append("no_png")
        if r.json_count == 0:
            reason.append("no_json")
        if r.pdf_count == 0:
            reason.append("no_pdf")
        if r.only_metadata:
            reason.append("only_metadata")
        if primary_by_group[canonical_name(r.name)] != r.name:
            reason.append("duplicate_secondary")

        if reason:
            exclude.append({"dir": r.name, "reasons": reason})
            reason_counts.update(reason)
            if "no_pdf" in reason:
                missing_pdf_dirs.append(r.name)
            if "no_json" in reason:
                no_json_priority_rows.append(
                    f"{r.name}\t{r.png_count}\t{r.pdf_count}\t{r.total_files}\t{r.json_per_png_ratio:.6f}"
                )
            if "only_metadata" in reason:
                only_metadata_dirs.append(r.name)
            if "no_png" in reason:
                no_png_dirs.append(r.name)
        else:
            allowlist.append(r.name)

    allowlist.sort()
    exclude.sort(key=lambda x: x["dir"])

    (out_dir / "screenshots_allowlist.txt").write_text(
        "\n".join(allowlist) + ("\n" if allowlist else ""),
        encoding="utf-8",
    )

    (out_dir / "screenshots_exclude_dirs.txt").write_text(
        "\n".join(f"{x['dir']}\t{','.join(x['reasons'])}" for x in exclude) + ("\n" if exclude else ""),
        encoding="utf-8",
    )
    (out_dir / "screenshots_pdf_missing_dirs.txt").write_text(
        "\n".join(sorted(missing_pdf_dirs)) + ("\n" if missing_pdf_dirs else ""),
        encoding="utf-8",
    )
    (out_dir / "screenshots_only_metadata_dirs.txt").write_text(
        "\n".join(sorted(only_metadata_dirs)) + ("\n" if only_metadata_dirs else ""),
        encoding="utf-8",
    )
    (out_dir / "screenshots_no_png_dirs.txt").write_text(
        "\n".join(sorted(no_png_dirs)) + ("\n" if no_png_dirs else ""),
        encoding="utf-8",
    )
    # Columns: dir_name, png_count, pdf_count, total_files, json_per_png_ratio
    (out_dir / "screenshots_no_json_priority.tsv").write_text(
        "\n".join(
            [
                "dir_name\tpng_count\tpdf_count\ttotal_files\tjson_per_png_ratio",
                *sorted(
                    no_json_priority_rows,
                    key=lambda row: int(row.split("\t")[1]),
                    reverse=True,
                ),
            ]
        )
        + ("\n" if no_json_priority_rows else ""),
        encoding="utf-8",
    )

    merge_csv = ["canonical,primary,duplicate,reason"]
    for row in merge_plan:
        merge_csv.append(f"{row['canonical']},{row['primary']},{row['duplicate']},{row['reason']}")
    (out_dir / "screenshots_merge_plan.csv").write_text("\n".join(merge_csv) + "\n", encoding="utf-8")

    payload = {
        "root": str(root),
        "total_dirs": len(rows),
        "allowlist_dirs": len(allowlist),
        "exclude_dirs": len(exclude),
        "with_png_dirs": with_png,
        "with_json_dirs": with_json,
        "with_pdf_dirs": with_pdf,
        "without_png_dirs": len(rows) - with_png,
        "without_json_dirs": len(rows) - with_json,
        "without_pdf_dirs": len(rows) - with_pdf,
        "empty_dirs": empty_dirs,
        "total_png_files": total_png,
        "total_json_files": total_json,
        "total_pdf_files": total_pdf,
        "json_per_png_ratio": round((total_json / total_png), 6) if total_png else 0.0,
        "dir_json_coverage_ratio": round((with_json / len(rows)), 6) if rows else 0.0,
        "reason_counts": dict(reason_counts),
        "canonical_duplicate_groups": sum(1 for names in groups.values() if len(names) > 1),
        "merge_plan_rows": len(merge_plan),
    }
    (out_dir / "screenshots_quality_status.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
