#!/usr/bin/env python
"""
PostToolUse Hook — Auto-Checkpoint After Git Commit

Matcher: Bash (set in settings.json)
Triggers when Bash output contains a git commit hash pattern.
Updates SESSION_STATE.md with latest commit info.

Advisory only (exit 0) — never blocks.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Windows cp1254 crash fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = PROJECT_ROOT / ".claude" / "sessions" / "latest.md"

# Patterns that indicate a git commit just happened
COMMIT_PATTERNS = [
    # "create mode", "[branch hash] message" — standard git commit output
    re.compile(r"\[[\w/.-]+\s+([a-f0-9]{7,12})\]"),
    # Short hash at start of line (git log --oneline style after commit)
    re.compile(r"^([a-f0-9]{7,12})\s+", re.MULTILINE),
]


def extract_commit_hash(output: str) -> str | None:
    """Extract commit hash from Bash output."""
    for pattern in COMMIT_PATTERNS:
        match = pattern.search(output)
        if match:
            return match.group(1)
    return None


def run_cmd(cmd: str) -> str:
    """Run shell command, return stdout."""
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True, timeout=5,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8", errors="replace",
        )
        return result.stdout.strip()
    except Exception:
        return ""


def atomic_write(path: Path, content: str) -> None:
    """Write file atomically: tempfile + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def update_state(commit_hash: str) -> None:
    """Update SESSION_STATE.md with checkpoint info."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    branch = run_cmd("git branch --show-current")
    last_5 = run_cmd("git log -5 --oneline")
    uncommitted = run_cmd("git status --short")
    uncommitted_count = len([l for l in uncommitted.splitlines() if l.strip()])

    # Read existing state to preserve "Bu Session'da Yapilanlar" section
    existing_tasks = ""
    if STATE_FILE.exists():
        try:
            old = STATE_FILE.read_text(encoding="utf-8")
            # Extract existing tasks section
            match = re.search(
                r"## Bu Session'da Yapilanlar\n(.*?)(?=\n## |\Z)",
                old, re.DOTALL,
            )
            if match:
                existing_tasks = match.group(1).strip()
        except Exception:
            pass

    lines = [
        f"# Session State (checkpoint: {now})",
        "",
        "## Quick Resume",
        f"- **Branch:** {branch}",
        f"- **Last commit:** {commit_hash}",
        f"- **Uncommitted:** {uncommitted_count} files",
        f"- **Production:** 77,336 questions",
        "",
    ]

    if existing_tasks:
        lines.extend([
            "## Bu Session'da Yapilanlar",
            existing_tasks,
            "",
        ])

    if last_5:
        lines.append("## Recent Commits")
        for c in last_5.splitlines()[:5]:
            lines.append(f"- {c}")
        lines.append("")

    if uncommitted.strip():
        lines.append("## Uncommitted Changes")
        for item in uncommitted.splitlines()[:10]:
            lines.append(f"- {item}")
        lines.append("")

    atomic_write(STATE_FILE, "\n".join(lines) + "\n")


def main() -> int:
    """Main entry point."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return 0

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    # Check tool output for commit hash
    tool_result = hook_input.get("tool_result", {})
    stdout = tool_result.get("stdout", "")
    stderr = tool_result.get("stderr", "")
    output = f"{stdout}\n{stderr}"

    # Also check the command itself — was it a git commit?
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")
    if "git commit" not in command:
        return 0

    commit_hash = extract_commit_hash(output)
    if not commit_hash:
        return 0

    try:
        update_state(commit_hash)
        print(f"[Checkpoint] Session state saved after commit {commit_hash}", file=sys.stderr)
    except Exception as e:
        print(f"[Checkpoint] Warning: state save failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] post-commit-checkpoint hook exception: {e}", file=sys.stderr)
        sys.exit(0)
