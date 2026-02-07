"""
Check that models/ files use relative imports (not absolute).

Mixing absolute (from models.base import Base) and relative (from .base import Base)
imports within the models/ package causes SQLAlchemy to create duplicate MetaData
objects, leading to 'Table already defined' errors.

Usage:
    python scripts/check_model_imports.py

Exit codes:
    0 - All imports are correct
    1 - Found absolute self-imports that should be relative
"""

import re
import sys
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "models"
# Pattern: "from models.xxx import" at the start of a line (absolute self-import)
ABSOLUTE_IMPORT_RE = re.compile(r"^from models\.(\w+) import", re.MULTILINE)


def check_file(filepath: Path) -> list[str]:
    """Check a single file for absolute self-imports."""
    violations = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return violations

    for match in ABSOLUTE_IMPORT_RE.finditer(content):
        line_num = content[: match.start()].count("\n") + 1
        violations.append(
            f"  {filepath.relative_to(MODELS_DIR.parent)}:{line_num}: "
            f"{match.group(0)}  ->  from .{match.group(1)} import ..."
        )
    return violations


def main() -> int:
    if not MODELS_DIR.exists():
        print(f"models/ directory not found at {MODELS_DIR}")
        return 1

    all_violations: list[str] = []
    for py_file in sorted(MODELS_DIR.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        all_violations.extend(check_file(py_file))

    if all_violations:
        print(
            "ERROR: Found absolute self-imports in models/ "
            "(should use relative imports):"
        )
        print()
        for v in all_violations:
            print(v)
        print()
        print(
            f"Found {len(all_violations)} violation(s). "
            "Use relative imports: from .module import Name"
        )
        return 1

    print("OK: All models/ imports use relative paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
