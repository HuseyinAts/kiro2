"""Fix codemod artifact: orphan `, exc_info=True)` after trailing-comma logger.error.

Broken pattern (causes SyntaxError):
    logger.error(
        "msg",
        var1,
        var2,         # trailing comma
    , exc_info=True)  # leading comma -> double comma == SyntaxError

Fix: rewrite to logger.exception(...) and drop exc_info kwarg + drop orphan comma.
"""

from __future__ import annotations

import py_compile
import re
import sys
from pathlib import Path

BROKEN_FILES = [
    "services/exam_answer_tracking_service.py",
    "services/exam_performance_service.py",
    "services/league_service.py",
    "services/study_planner_service.py",
    "services/youtube_rate_limiter.py",
]

# Match the broken block ending in:
#     <expr>,\n
#         <whitespace>, exc_info=True)
# Replace with:
#     <expr>,\n
#         <whitespace>)
# Plus retroactively turn the preceding `logger.error(` into `logger.exception(`.
ORPHAN_RE = re.compile(
    r"logger\.error\((?P<body>(?:[^()]|\([^()]*\))*?,)\n(?P<lead>[ \t]+), exc_info=True\)",
    re.MULTILINE,
)


def fix_file(path: Path) -> int:
    src = path.read_text(encoding="utf-8")
    new_src, n = ORPHAN_RE.subn(
        lambda m: f"logger.exception({m.group('body')}\n{m.group('lead')})",
        src,
    )
    if n:
        path.write_text(new_src, encoding="utf-8")
    return n


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    total = 0
    for rel in BROKEN_FILES:
        p = root / rel
        if not p.exists():
            print(f"SKIP missing: {rel}")
            continue
        n = fix_file(p)
        print(f"  {rel}: {n} site(s) rewritten")
        total += n
        # verify syntax
        try:
            py_compile.compile(str(p), doraise=True)
            print("    syntax OK")
        except py_compile.PyCompileError as e:
            print(f"    STILL BROKEN: {e}")
            return 1
    print(f"--- {total} total sites rewritten across {len(BROKEN_FILES)} files ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
