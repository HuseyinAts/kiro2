#!/usr/bin/env python
"""
Stop + PreCompact Hook — Session State Auto-Save + Backup

Used for both Stop (session exit) and PreCompact (before context compaction).
Saves git state, services, production count, tasks to SESSION_STATE.md + JSON.
Backs up critical files with rotation (max 20 per type).

Atomic writes: uses tempfile + os.replace to prevent half-written state on crash.
Bash detection: warns if bash is missing instead of silently producing empty state.
"""

from __future__ import annotations

import json
import os
import shutil
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
STATE_FILE = PROJECT_ROOT / ".claude" / "SESSION_STATE.md"
STATE_JSON = PROJECT_ROOT / ".claude" / "session_state.json"
BACKUP_DIR = Path.home() / ".claude" / "session-backups"
MAX_BACKUPS_PER_TYPE = 20

# Detect bash availability once at module load
_BASH_AVAILABLE: bool | None = None


def _check_bash() -> bool:
    """Check if bash is available in PATH."""
    global _BASH_AVAILABLE
    if _BASH_AVAILABLE is None:
        try:
            subprocess.run(["bash", "--version"], capture_output=True, timeout=3)
            _BASH_AVAILABLE = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            _BASH_AVAILABLE = False
            print("[WARN] bash not found in PATH — git/curl commands will fail", file=sys.stderr)
    return _BASH_AVAILABLE


def run_cmd(cmd: str, cwd: str | None = None) -> str:
    """Run a shell command via bash. Returns '' if bash missing or command fails."""
    if not _check_bash():
        return ""
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd or str(PROJECT_ROOT),
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()
    except Exception:
        return ""


def atomic_write(path: Path, content: str) -> None:
    """Write file atomically: tempfile + os.replace (safe on crash)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        # Cleanup temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _fast_line_count(path: Path) -> int:
    """Count lines via raw byte reading (~60ms for 112MB)."""
    try:
        count = 0
        with open(path, "rb") as fh:
            while chunk := fh.read(1 << 20):
                count += chunk.count(b"\n")
        return count
    except Exception:
        return 0


# === Data collection ===

def get_git_state() -> dict:
    """Capture git state."""
    branch = run_cmd("git branch --show-current")
    last_commits = run_cmd("git log -5 --oneline")
    uncommitted = run_cmd("git status --short")
    staged = run_cmd("git diff --cached --stat")
    recent_files = run_cmd("git diff --name-only HEAD~3 2>/dev/null")

    py_changes = len([line for line in uncommitted.splitlines() if line.strip().endswith(".py")])

    return {
        "branch": branch,
        "last_commits": last_commits.splitlines()[:5],
        "uncommitted_count": len([line for line in uncommitted.splitlines() if line.strip()]),
        "uncommitted_py": py_changes,
        "staged": staged,
        "uncommitted_files": uncommitted.splitlines()[:15],
        "recent_files": recent_files.splitlines()[:10],
    }


def get_services_state() -> dict:
    """Check running services (with connect timeout)."""
    services = {}
    services["docker"] = (run_cmd("docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null").splitlines() or [])

    backend = run_cmd('curl -s --connect-timeout 2 --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8000/health')
    services["backend"] = backend if backend else "DOWN"

    frontend = run_cmd('curl -s --connect-timeout 2 --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:3000')
    services["frontend"] = frontend if frontend else "DOWN"

    return services


def get_tasks_state() -> dict:
    """Get active task list state."""
    task_list_id = os.environ.get("CLAUDE_CODE_TASK_LIST_ID", "kiro2-master")
    tasks_dir = Path.home() / ".claude" / "tasks" / task_list_id

    if not tasks_dir.exists():
        return {"active": [], "pending": [], "total": 0}

    active, pending, completed_count = [], [], 0
    for task_file in sorted(tasks_dir.glob("task-*.json")):
        try:
            task = json.loads(task_file.read_text(encoding="utf-8"))
            status = task.get("status", "pending")
            entry = {"id": task.get("id", task_file.stem), "subject": task.get("subject", "Unknown")}
            if status == "in_progress":
                active.append(entry)
            elif status == "pending":
                pending.append(entry)
            elif status == "completed":
                completed_count += 1
        except Exception:
            pass

    return {"active": active[:5], "pending": pending[:5], "completed": completed_count,
            "total": len(active) + len(pending) + completed_count}


def get_production_state() -> dict:
    """Get production data state."""
    jsonl_path = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
    return {"question_count": _fast_line_count(jsonl_path) if jsonl_path.exists() else 0}


# === Output ===

def build_state_md(git: dict, services: dict, tasks: dict, production: dict) -> str:
    """Build SESSION_STATE.md content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Session State (auto-saved: {now})",
        "",
        "## Quick Resume",
        f"- **Branch:** {git['branch']}",
        f"- **Last commit:** {git['last_commits'][0] if git['last_commits'] else 'N/A'}",
        f"- **Uncommitted:** {git['uncommitted_count']} files ({git['uncommitted_py']} .py)",
        f"- **Production:** {production['question_count']:,} questions",
        f"- **Backend:** {services['backend']}",
        f"- **Frontend:** {services['frontend']}",
        "",
    ]

    if tasks["active"]:
        lines.append("## Active Tasks (in_progress)")
        for t in tasks["active"]:
            lines.append(f"- [{t['id']}] {t['subject']}")
        lines.append("")

    if tasks["pending"]:
        lines.append("## Pending Tasks")
        for t in tasks["pending"]:
            lines.append(f"- [{t['id']}] {t['subject']}")
        lines.append("")

    if git["last_commits"]:
        lines.append("## Recent Commits")
        for c in git["last_commits"]:
            lines.append(f"- {c}")
        lines.append("")

    if git["uncommitted_files"]:
        lines.append("## Uncommitted Changes")
        for item in git["uncommitted_files"][:10]:
            lines.append(f"- {item}")
        if git["uncommitted_count"] > 10:
            lines.append(f"- ... and {git['uncommitted_count'] - 10} more")
        lines.append("")

    if services["docker"]:
        lines.append("## Running Containers")
        for container in services["docker"]:
            lines.append(f"- {container}")
        lines.append("")

    if git["recent_files"]:
        lines.append("## Recently Modified Files")
        for item in git["recent_files"]:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


# === Backup (absorbed from pre-compact.py) ===

def run_backup() -> None:
    """Backup critical files + cleanup old backups."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Backup files
    for src, prefix in [
        (PROJECT_ROOT / "progress.md", "progress"),
        (PROJECT_ROOT / "CLAUDE.local.md", "CLAUDE.local"),
        (STATE_FILE, "SESSION_STATE"),
    ]:
        if src.exists():
            shutil.copy2(src, BACKUP_DIR / f"{prefix}-{ts}{src.suffix}")

    # Git state snapshot
    git_output = run_cmd("git status --short") + "\n" + run_cmd("git log -3 --oneline")
    if git_output.strip():
        (BACKUP_DIR / f"git-{ts}.txt").write_text(git_output, encoding="utf-8")

    # Cleanup: keep max 20 per prefix
    groups: dict[str, list[Path]] = {}
    for f in BACKUP_DIR.iterdir():
        if f.is_file() and "-" in f.stem:
            # Key = everything before the timestamp (e.g. "progress", "CLAUDE.local", "git")
            key = f.stem.rsplit("-", 1)[0]
            groups.setdefault(key, []).append(f)

    for _key, files in groups.items():
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for old_file in files[MAX_BACKUPS_PER_TYPE:]:
            try:
                old_file.unlink()
            except Exception:
                pass


# === Main ===

def main() -> int:
    """Main entry point. Used by both Stop and PreCompact hooks."""
    try:
        git = get_git_state()
        services = get_services_state()
        tasks = get_tasks_state()
        production = get_production_state()

        # Atomic writes
        md_content = build_state_md(git, services, tasks, production)
        atomic_write(STATE_FILE, md_content)

        state_json = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "git": git,
            "services": services,
            "tasks": tasks,
            "production": production,
        }
        atomic_write(STATE_JSON, json.dumps(state_json, indent=2, ensure_ascii=False))

        # Backup
        run_backup()

        print(f"Session state saved to {STATE_FILE}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: session-save failed: {e}", file=sys.stderr)

    # Never block session exit or compaction
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] session-save hook exception: {e}", file=sys.stderr)
        sys.exit(0)
