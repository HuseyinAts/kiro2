#!/usr/bin/env python
"""
PreToolUse Hook — Large File Blocker (Bash matcher)

Blocks git add/commit when staged files exceed 50MB.
Prevents the recurring issue of >100MB files hitting GitHub's limit.

EXIT CODE 2: BLOCKS the command
EXIT CODE 0: ALLOW
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# Windows cp1254 crash fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# LFS tracked extensions (already in .gitattributes or should be)
LFS_EXTENSIONS = {".jsonl", ".bin", ".pt", ".db", ".pkl", ".h5", ".onnx", ".safetensors"}


def is_git_commit_or_add(command: str) -> bool:
    """Check if the bash command is git add or git commit."""
    cmd = command.strip()
    return cmd.startswith("git add") or cmd.startswith("git commit")


def check_staged_files() -> list[str]:
    """Check staged files for size violations. Returns list of warnings."""
    warnings = []
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []

        for filepath in result.stdout.strip().split("\n"):
            if not filepath:
                continue
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                if size > MAX_FILE_SIZE_BYTES:
                    ext = os.path.splitext(filepath)[1].lower()
                    size_mb = size / (1024 * 1024)
                    msg = f"{filepath} is {size_mb:.1f}MB (limit: {MAX_FILE_SIZE_MB}MB)"
                    if ext in LFS_EXTENSIONS:
                        msg += " — use git-lfs or add to .gitignore"
                    warnings.append(msg)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return warnings


def check_untracked_large_files(command: str) -> list[str]:
    """Check if 'git add' targets large files directly."""
    warnings = []
    if not command.strip().startswith("git add"):
        return []

    # Extract file paths from git add command
    parts = command.strip().split()
    if len(parts) < 3:
        return []

    for part in parts[2:]:
        if part.startswith("-"):
            continue
        # Check if it's a file path (not a flag)
        if os.path.isfile(part):
            size = os.path.getsize(part)
            if size > MAX_FILE_SIZE_BYTES:
                size_mb = size / (1024 * 1024)
                warnings.append(f"{part} is {size_mb:.1f}MB (limit: {MAX_FILE_SIZE_MB}MB)")

    return warnings


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return 0

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    command = hook_input.get("tool_input", {}).get("command", "")
    if not is_git_commit_or_add(command):
        return 0

    errors = []

    # Check files being added
    errors.extend(check_untracked_large_files(command))

    # Check already staged files (for git commit)
    if command.strip().startswith("git commit"):
        errors.extend(check_staged_files())

    if errors:
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Large file(s) detected: {'; '.join(errors)}",
            }
        }
        json.dump(result, sys.stdout)
        print(f"\nBLOCKED: {'; '.join(errors)}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] pre-commit-check hook exception: {e}", file=sys.stderr)
        sys.exit(0)
