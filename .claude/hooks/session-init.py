#!/usr/bin/env python
"""
SessionStart Hook — Context Restore + Welcome Banner

Reads stdin JSON from Claude Code:
  { "session_id": "...", "source": "startup|resume|clear|compact", "model": "..." }

Outputs structured JSON on stdout — Claude Code adds this directly to context.
Also prints welcome banner to stderr (shown to user in verbose mode).

State continuity: reads session_state.json saved by Stop hook (session-save.py).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows cp1254 crash fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_JSON = PROJECT_ROOT / ".claude" / "session_state.json"
SESSIONS_DIR = Path.home() / ".claude" / "sessions"


def read_hook_input() -> dict:
    """Read stdin JSON from Claude Code."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return {}


def load_previous_state() -> dict | None:
    """Load previous session state from JSON file."""
    if STATE_JSON.exists():
        try:
            return json.loads(STATE_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def format_time_ago(saved_at: str) -> str:
    """Human-readable time since save."""
    try:
        saved = datetime.fromisoformat(saved_at.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - saved
        hours = delta.total_seconds() / 3600
        if hours < 1:
            return f"{int(delta.total_seconds() / 60)}m ago"
        elif hours < 24:
            return f"{int(hours)}h ago"
        return f"{int(hours / 24)}d ago"
    except Exception:
        return "unknown"


def save_session_info(session_id: str) -> None:
    """Save session info to disk + history."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    session_info = {
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "working_dir": str(PROJECT_ROOT),
    }

    # Current session
    (SESSIONS_DIR / "current.json").write_text(
        json.dumps(session_info, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # History (with rotation: max 500 → keep last 200)
    history_file = SESSIONS_DIR / "history.jsonl"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(session_info, ensure_ascii=False) + "\n")
    try:
        lines = history_file.read_text(encoding="utf-8").splitlines()
        if len(lines) > 500:
            history_file.write_text("\n".join(lines[-200:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def check_environment() -> list[str]:
    """Check environment variables AND infrastructure health."""
    warnings = []

    # API keys
    for var, desc in {
        "ANTHROPIC_API_KEY": "API erisimi icin gerekli",
        "GOOGLE_API_KEY": "Gemini MCP icin gerekli",
    }.items():
        if not os.environ.get(var):
            warnings.append(f"{var} tanimli degil: {desc}")

    # Infrastructure checks (fast, max 3s total)
    # PostgreSQL (port 5434) — 1s timeout
    try:
        result = subprocess.run(
            ["pg_isready", "-p", "5434", "-t", "1"],
            capture_output=True, timeout=2
        )
        if result.returncode != 0:
            warnings.append("PostgreSQL (5434) erisilemez")
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass  # pg_isready not installed or timeout

    # Backend health — 1s timeout
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:8000/api/v1/health", method="GET")
        with urllib.request.urlopen(req, timeout=1) as resp:
            if resp.status != 200:
                warnings.append(f"Backend health: HTTP {resp.status}")
    except Exception:
        warnings.append("Backend (8000) erisilemez")

    return warnings


def build_context(prev_state: dict | None) -> str:
    """Build context string for Claude from previous session state."""
    if not prev_state:
        return ""

    git = prev_state.get("git", {})
    services = prev_state.get("services", {})
    production = prev_state.get("production", {})
    tasks = prev_state.get("tasks", {})
    time_ago = format_time_ago(prev_state.get("saved_at", ""))

    parts = [f"Previous session ({time_ago}):"]
    parts.append(f"Branch: {git.get('branch', '?')}")

    commits = git.get("last_commits", [])
    if commits:
        parts.append(f"Last commit: {commits[0]}")

    uncommitted = git.get("uncommitted_count", 0)
    if uncommitted > 0:
        parts.append(f"Uncommitted: {uncommitted} files ({git.get('uncommitted_py', 0)} .py)")

    q_count = production.get("question_count", 0)
    if q_count > 0:
        parts.append(f"Production: {q_count:,} questions")

    parts.append(f"Services: Backend={services.get('backend', '?')} Frontend={services.get('frontend', '?')}")

    active = tasks.get("active", [])
    if active:
        parts.append("Active tasks: " + ", ".join(f"[{t['id']}] {t['subject']}" for t in active[:3]))

    return "\n".join(parts)


def print_banner(session_id: str, source: str, warnings: list[str], prev_state: dict | None) -> None:
    """Print welcome banner to stderr (user-visible)."""
    sep = "=" * 60
    lines = [
        f"\n{sep}",
        "KIRO2 Claude Code Session Started",
        sep,
        f"Session ID: {session_id}",
        f"Working Dir: {PROJECT_ROOT}",
        f"Task List: {os.environ.get('CLAUDE_CODE_TASK_LIST_ID', 'kiro2-master')}",
    ]

    if prev_state:
        time_ago = format_time_ago(prev_state.get("saved_at", ""))
        git = prev_state.get("git", {})
        services = prev_state.get("services", {})
        production = prev_state.get("production", {})

        lines.append(f"\n--- Previous Session ({time_ago}) ---")
        lines.append(f"Branch: {git.get('branch', '?')}")
        commits = git.get("last_commits", [])
        if commits:
            lines.append(f"Last commit: {commits[0]}")
        uncommitted = git.get("uncommitted_count", 0)
        if uncommitted > 0:
            lines.append(f"Uncommitted: {uncommitted} files ({git.get('uncommitted_py', 0)} .py)")
        q_count = production.get("question_count", 0)
        if q_count > 0:
            lines.append(f"Production: {q_count:,} questions")
        lines.append(f"Services: Backend={services.get('backend', '?')} Frontend={services.get('frontend', '?')}")
        lines.append("--- End Previous State ---")

    source_labels = {
        "startup": "New Session",
        "resume": "Resumed Session",
        "clear": "After /clear",
        "compact": "After Compaction",
    }
    lines.append(f"Source: {source_labels.get(source, source)}")

    if warnings:
        lines.append("\nWarnings:")
        for w in warnings:
            lines.append(f"   {w}")

    lines.append(sep)
    print("\n".join(lines), file=sys.stderr)


def main() -> int:
    """Main entry point."""
    # Read Claude Code's stdin JSON
    hook_input = read_hook_input()
    session_id = hook_input.get("session_id", f"unknown-{datetime.now().strftime('%H%M%S')}")
    source = hook_input.get("source", "startup")

    # Save session info
    save_session_info(session_id)

    # Load previous state
    prev_state = load_previous_state()

    # Environment check
    warnings = check_environment()

    # Print banner to stderr (user-visible)
    print_banner(session_id, source, warnings, prev_state)

    # Output structured JSON to stdout — Claude Code adds this to context
    context = build_context(prev_state)
    if context:
        result = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
        json.dump(result, sys.stdout)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Warning: session-init failed: {e}", file=sys.stderr)
        sys.exit(0)
