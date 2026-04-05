#!/usr/bin/env python3
"""
Audit screenshot dataset quality and print actionable QA report.

Default target:
  veriseti/zkitap/screenshots
"""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


SAYFA_RE = re.compile(r"^sayfa_(\d+)\.(png|json)$", re.IGNORECASE)


@dataclass
class DirMetrics:
    path: Path
    ext_counts: Counter
    png_ids: Set[str]
    json_ids: Set[str]

    @property
    def png_count(self) -> int:
        return len(self.png_ids)

    @property
    def json_count(self) -> int:
        return len(self.json_ids)

    @property
    def missing_json_for_png(self) -> int:
        return len(self.png_ids - self.json_ids)

    @property
    def missing_png_for_json(self) -> int:
        return len(self.json_ids - self.png_ids)


def turkish_normalized_lower(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = value.replace("I", "ı").replace("İ", "i")
    return value.lower()


def canonical_name(value: str) -> str:
    lowered = turkish_normalized_lower(value)
    return "".join(ch for ch in lowered if ch.isalnum())


def analyze_dir(directory: Path) -> DirMetrics:
    ext_counts: Counter = Counter()
    png_ids: Set[str] = set()
    json_ids: Set[str] = set()

    with os.scandir(directory) as entries:
        for entry in entries:
            if not entry.is_file(follow_symlinks=False):
                continue
            child_name = entry.name
            suffix = Path(child_name).suffix
            ext = suffix.lower().lstrip(".")
            ext_counts[ext if ext else "<none>"] += 1
            match = SAYFA_RE.match(child_name)
            if match:
                page_id, page_ext = match.groups()
                if page_ext.lower() == "png":
                    png_ids.add(page_id)
                else:
                    json_ids.add(page_id)
    return DirMetrics(
        path=directory,
        ext_counts=ext_counts,
        png_ids=png_ids,
        json_ids=json_ids,
    )


def audit(root: Path) -> Dict[str, object]:
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Dataset path not found: {root}")

    metrics: List[DirMetrics] = []
    ext_total: Counter = Counter()
    canonical_groups: Dict[str, List[str]] = defaultdict(list)
    typo_like: List[str] = []

    typo_patterns = ("Soeu", "Porble", "Brna", ",k", "Sopru", "Dets", "Sohagi", "Egsersiz", "Lampı")

    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        dir_metrics = analyze_dir(child)
        metrics.append(dir_metrics)
        ext_total.update(dir_metrics.ext_counts)
        canonical_groups[canonical_name(child.name)].append(child.name)
        if any(token in child.name for token in typo_patterns):
            typo_like.append(child.name)

    total_dirs = len(metrics)
    png_dirs = sum(1 for m in metrics if m.ext_counts.get("png", 0) > 0)
    json_dirs = sum(1 for m in metrics if m.ext_counts.get("json", 0) > 0)
    pdf_dirs = sum(1 for m in metrics if m.ext_counts.get("pdf", 0) > 0)
    png_without_json = max(0, png_dirs - json_dirs)

    only_desktop_ini = [
        m.path.name
        for m in metrics
        if sum(m.ext_counts.values()) == 1 and m.ext_counts.get("ini", 0) == 1
    ]
    missing_pdf_dirs = [m.path.name for m in metrics if m.ext_counts.get("pdf", 0) == 0]
    duplicate_groups = [sorted(names) for names in canonical_groups.values() if len(names) > 1]

    json_coverage_rows: List[Tuple[str, int, int, int, int]] = []
    for m in metrics:
        if m.png_count == 0 and m.json_count == 0:
            continue
        json_coverage_rows.append(
            (
                m.path.name,
                m.png_count,
                m.json_count,
                m.missing_json_for_png,
                m.missing_png_for_json,
            )
        )
    json_coverage_rows.sort(key=lambda x: (-x[3], x[0]))

    status = "PASS"
    reasons: List[str] = []
    if png_dirs and (png_without_json / png_dirs) > 0.10:
        status = "FAIL"
        reasons.append("JSON coverage below threshold (>10% PNG dirs missing JSON)")
    if missing_pdf_dirs:
        status = "FAIL"
        reasons.append("Some directories do not contain PDF source")
    if only_desktop_ini:
        status = "FAIL"
        reasons.append("Empty/metadata-only directories detected")

    return {
        "root": str(root),
        "status": status,
        "status_reasons": reasons,
        "summary": {
            "total_dirs": total_dirs,
            "png_dirs": png_dirs,
            "json_dirs": json_dirs,
            "pdf_dirs": pdf_dirs,
            "png_without_json_dirs": png_without_json,
            "ext_total": dict(ext_total),
        },
        "findings": {
            "missing_pdf_dirs": missing_pdf_dirs,
            "only_desktop_ini_dirs": only_desktop_ini,
            "canonical_duplicate_groups": duplicate_groups,
            "typo_like_names": sorted(typo_like),
            "top_missing_json_by_dir": json_coverage_rows[:40],
        },
    }


def print_report(result: Dict[str, object], verbose: bool) -> None:
    summary = result["summary"]  # type: ignore[index]
    findings = result["findings"]  # type: ignore[index]

    print("### Summary")
    print(f"Path: {result['root']}")
    print(f"Status: {result['status']}")
    if result["status_reasons"]:
        print("Reasons:")
        for reason in result["status_reasons"]:
            print(f"- {reason}")
    print()

    print("### Findings")
    print(f"- total_dirs: {summary['total_dirs']}")
    print(f"- png_dirs: {summary['png_dirs']}")
    print(f"- json_dirs: {summary['json_dirs']}")
    print(f"- png_without_json_dirs: {summary['png_without_json_dirs']}")
    print(f"- pdf_missing_dirs: {len(findings['missing_pdf_dirs'])}")
    print(f"- only_desktop_ini_dirs: {len(findings['only_desktop_ini_dirs'])}")
    print(f"- canonical_duplicate_groups: {len(findings['canonical_duplicate_groups'])}")
    print(f"- typo_like_names: {len(findings['typo_like_names'])}")
    print()

    if verbose:
        print("### Missing PDF Dirs")
        for name in findings["missing_pdf_dirs"]:
            print(name)
        print()

        print("### Metadata-Only Dirs")
        for name in findings["only_desktop_ini_dirs"]:
            print(name)
        print()

        print("### Canonical Duplicate Groups")
        for group in findings["canonical_duplicate_groups"]:
            print(" | ".join(group))
        print()

        print("### Typo-Like Names")
        for name in findings["typo_like_names"]:
            print(name)
        print()

        print("### Top Missing JSON by Dir")
        for row in findings["top_missing_json_by_dir"]:
            name, png_count, json_count, missing_json, missing_png = row
            print(
                f"{name} | png={png_count} json={json_count} "
                f"missing_json={missing_json} missing_png={missing_png}"
            )
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit zkitap screenshots dataset quality")
    parser.add_argument(
        "--path",
        default="veriseti/zkitap/screenshots",
        help="Dataset root directory",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional output JSON file path",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed lists",
    )
    args = parser.parse_args()

    result = audit(Path(args.path))
    print_report(result, verbose=args.verbose)

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON report written: {output_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
