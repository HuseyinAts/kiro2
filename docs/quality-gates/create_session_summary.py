#!/usr/bin/env python3
"""
Create a dated session summary markdown file from template.

Usage:
  python3 docs/quality-gates/create_session_summary.py --slug screenshots-gate
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a session summary file")
    parser.add_argument("--slug", required=True, help="Short session name, e.g. screenshots-gate")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date in YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="Overwrite if file exists")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    template_path = base_dir / "session-summary-template.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    out_name = f"{args.slug}-session-summary-{args.date}.md"
    out_path = base_dir / out_name
    if out_path.exists() and not args.force:
        raise FileExistsError(
            f"Summary already exists: {out_path}. Use --force to overwrite."
        )

    template = template_path.read_text(encoding="utf-8")
    content = (
        template.replace("{{TITLE}}", args.slug.replace("-", " ").title())
        .replace("{{DATE}}", args.date)
        .replace("{{TARGET}}", "TODO")
        .replace("{{GOAL}}", "TODO")
        .replace("{{STEP_1}}", "TODO")
        .replace("{{STEP_2}}", "TODO")
        .replace("{{STEP_3}}", "TODO")
        .replace("{{RESULT_1}}", "TODO")
        .replace("{{RESULT_2}}", "TODO")
        .replace("{{VERIFY_1}}", "TODO")
        .replace("{{VERIFY_2}}", "TODO")
        .replace("{{NOTE}}", "TODO")
    )
    out_path.write_text(content, encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

