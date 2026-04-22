#!/usr/bin/env python
"""
Cursor afterFileEdit hook — Python dosyalarını ruff ile otomatik formatlar.

Cursor input formatı (hooks.md docs):
  {
    "file_path": "<absolute path>",
    "edits": [{"old_string": "...", "new_string": "..."}],
    "conversation_id": "...",
    "hook_event_name": "afterFileEdit",
    ...
  }

Claude Code input formatı (legacy, tool_input nested):
  {
    "tool_input": {"file_path": "..."},
    ...
  }

Bu script her iki formatı da destekler.
"""
import json
import os
import subprocess
import sys


# Windows cp1254 encoding fix (KIRO2'nin Windows PowerShell ortamı için)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


PYTHON_DIRS = ["backend", "orchestrator", "ai_ml", "mcp-servers"]
SKIP_DIRS = [".claude", ".cursor", "node_modules", ".git", "__pycache__",
             "venv", ".venv", ".venv_ocr", ".venv-paddle", "wheelhouse"]


def extract_file_path(hook_input: dict) -> str:
    """Cursor top-level veya Claude Code nested format — ikisini de dene."""
    # Cursor format: top-level
    if fp := hook_input.get("file_path"):
        return fp
    # Claude Code format: tool_input.file_path
    if fp := hook_input.get("tool_input", {}).get("file_path"):
        return fp
    return ""


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return 0

    file_path = extract_file_path(hook_input)
    if not file_path.endswith(".py"):
        return 0

    normalized = file_path.replace("\\", "/")

    # Sadece izin verilen dizinlerde
    if not any(f"/{d}/" in normalized or normalized.startswith(f"{d}/")
               for d in PYTHON_DIRS):
        return 0

    # Skip infrastructure
    if any(f"/{d}/" in normalized for d in SKIP_DIRS):
        return 0

    if not os.path.isfile(file_path):
        return 0

    # Ruff: check --fix + format (sessiz, non-blocking)
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
        print(f"[cursor-format] ruff: {os.path.basename(file_path)}",
              file=sys.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print(f"[cursor-format] ruff skip: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] cursor-post-edit-ruff: {e}", file=sys.stderr)
        sys.exit(0)
