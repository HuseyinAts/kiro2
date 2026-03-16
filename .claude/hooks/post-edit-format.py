#!/usr/bin/env python
"""PostToolUse: Auto-format Python files with ruff after Edit/Write."""
import json
import os
import subprocess
import sys

# Windows cp1254 fix (REQUIRED)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Python directories to auto-format
PYTHON_DIRS = ["backend", "orchestrator"]


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return 0

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only .py files
    if not file_path.endswith(".py"):
        return 0

    # Only backend/ and orchestrator/ directories
    normalized = file_path.replace("\\", "/")
    if not any(d in normalized for d in PYTHON_DIRS):
        return 0

    # Skip infrastructure directories
    skip_dirs = [".claude", "node_modules", ".git", "__pycache__", "venv", ".venv"]
    if any(f"/{d}/" in normalized for d in skip_dirs):
        return 0

    # Check file exists
    if not os.path.isfile(file_path):
        return 0

    # Run ruff check --fix + ruff format (silent, non-blocking)
    try:
        subprocess.run(
            ["ruff", "check", "--fix", "--quiet", file_path],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["ruff", "format", "--quiet", file_path],
            capture_output=True,
            timeout=10,
        )
        print(f"[format] ruff: {os.path.basename(file_path)}", file=sys.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print(f"[format] ruff skip: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] post-edit-format: {e}", file=sys.stderr)
        sys.exit(0)
