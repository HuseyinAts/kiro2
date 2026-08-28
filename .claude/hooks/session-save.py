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
import re
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

def run_exe(args: list[str], cwd: str | None = None, timeout: int = 15) -> str:
    """Run an executable DIRECTLY — no shell, no bash indirection.

    Neden bash yok (20 Agu 2026'da olculdu): bu makinede SOGUK `bash` spawn
    **7,11 sn**. Eski `_check_bash()` `timeout=3` kullaniyordu, yani her soguk
    kosumda `False` donuyor ve `run_cmd` turevi HER alani sessizce bosaltiyordu
    (branch="", services="DOWN", uncommitted=0). Hook'lar daima soguk kosar.
    Dogrudan `git.exe`: 0,06 sn.
    """
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or str(PROJECT_ROOT),
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()
    except Exception:
        return ""


def run_git(*args: str) -> str:
    """Run a git command directly (git.exe on PATH)."""
    return run_exe(["git", *args])


def http_status(url: str, timeout: float = 3.0) -> str:
    """Return HTTP status code as string, or 'DOWN'. urllib — curl/bash gerekmez."""
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as exc:  # sunucu yanit verdi, 2xx degil
        return str(exc.code)
    except Exception:
        return "DOWN"


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
    """Capture git state.

    `--untracked-files=no` ZORUNLU: bu depoda ~3.400 takipsiz dosya ve
    `d-dataset/output/crops` altinda 528.651 PNG var; takipsiz taramali
    `git status` **60 sn'de bitmiyor** (olculdu), `-uno` ile **0,09 sn**.
    Takipsiz gurultuyu saymak zaten anlamsizdi — S229-B dersi takipli-kirli
    sayisini istiyor.
    """
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    last_commits = run_git("log", "-5", "--oneline")
    uncommitted = run_git("status", "--porcelain", "--untracked-files=no")
    staged = run_git("diff", "--cached", "--stat")
    recent_files = run_git("diff", "--name-only", "HEAD~3")

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
    services["docker"] = run_exe(
        ["docker", "ps", "--format", "{{.Names}}: {{.Status}}"], timeout=10
    ).splitlines()

    # `/health` DOGRU yol; `/api/v1/health` 404 doner (api/health.py'de prefix YOK).
    services["backend"] = http_status("http://localhost:8000/health")
    services["frontend"] = http_status("http://localhost:3000")

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


PSQL_ADAYLARI = (
    r"C:/Program Files/PostgreSQL/18/bin/psql.exe",
    "psql",
)


def _db_sayimi(sorgu: str) -> int | None:
    """Canli DB'den tek sayi oku. Olculemezse None — BAYAT SAYI GOSTERME."""
    for psql in PSQL_ADAYLARI:
        cikti = run_exe(
            [psql, "-U", "postgres", "-p", "5434", "-d", "kiro2", "-t", "-A", "-c", sorgu],
            timeout=8,
        )
        if cikti.strip().isdigit():
            return int(cikti.strip())
    return None


def get_production_state() -> dict:
    """Icerik durumu — KAYNAGI ADIYLA raporla.

    Eski hali `d-dataset/eslesmis_sorucevap.jsonl` satir sayisini (77.336)
    `question_count` diye raporluyor, banner da "Production: 77,336 questions"
    yaziyordu. Bu bir VEKIL olcumdu: canli DB'de `question_bank`=36.967,
    ogrenci kapisi `mv_safe_for_beta`=27.073 (20 Agu 2026). Diskteki dosya ile
    servis edilen havuzun kesisimi olculdu ve SIFIR. Artik ucu de ayri ayri,
    kendi adiyla raporlaniyor; olculemeyen alan `None` kalir.
    """
    jsonl_path = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
    return {
        "jsonl_rows": _fast_line_count(jsonl_path) if jsonl_path.exists() else 0,
        "db_question_bank": _db_sayimi("SELECT count(*) FROM question_bank"),
        "db_safe_pool": _db_sayimi("SELECT count(*) FROM mv_safe_for_beta"),
    }


def get_coverage_state() -> dict:
    """Read last coverage report via tail+regex (no full JSON parse — file is 1.3M+ lines)."""
    path = PROJECT_ROOT / "backend" / "coverage.json"
    if not path.exists():
        return {"available": False}
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            f.seek(max(0, size - 1024))
            tail = f.read().decode("utf-8", errors="replace")
        match = re.search(r'"percent_covered_display":\s*"([^"]+)"', tail)
        if match:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            return {
                "available": True,
                "percent": match.group(1),
                "report_date": mtime.strftime("%Y-%m-%d %H:%M"),
            }
    except Exception:
        pass
    return {"available": False}


KULLANICI_GORUNUR_YOLLAR = (
    "frontend/src",
    "backend/api",
    "backend/services",
    "backend/algorithms",
)


def get_visible_output_state() -> dict:
    """E3: bugun kullanici-gorunur cikti uretildi mi — BEYAN degil OLCUM.

    Neden gerekli (20 Agu 2026 olcumu): son 30 gunde 443 commit atildi;
    tur dagilimi chore 125 + docs 78 + test 34 = **%53 surec isi**.
    `frontend/src`'ye dokunan 69 commit'e karsilik `backend/tests`'e 153.
    Bir kural yalniz yorumda yasarsa silinir; olculup her oturum sonunda
    yuzune bakilirsa yasar (S219: mesaj kaybolur -> yorum silinir -> olcum kalir).
    """
    bugun = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hepsi = run_git("log", f"--since={bugun} 00:00", "--oneline")
    gorunur = run_git(
        "log", f"--since={bugun} 00:00", "--oneline", "--", *KULLANICI_GORUNUR_YOLLAR
    )
    say = lambda s: len([x for x in s.splitlines() if x.strip()])  # noqa: E731
    return {
        "commits_today": say(hepsi),
        "user_visible_today": say(gorunur),
        "paths": list(KULLANICI_GORUNUR_YOLLAR),
    }


def get_migration_state() -> dict:
    """Count alembic migration files (no subprocess — just glob)."""
    versions_dir = PROJECT_ROOT / "backend" / "alembic" / "versions"
    if not versions_dir.exists():
        return {"count": 0, "latest": "N/A"}
    try:
        migrations = sorted(
            [f for f in versions_dir.glob("*.py") if not f.name.startswith("__")],
            key=lambda p: p.name, reverse=True,
        )
        latest = migrations[0].stem if migrations else "N/A"
        return {"count": len(migrations), "latest": latest}
    except Exception:
        return {"count": 0, "latest": "N/A"}


# === Output ===

def _sayi(deger: int | None) -> str:
    """Olculemeyen sayiyi BAYAT bir rakamla degil, acikca 'olculemedi' diye yaz."""
    return f"{deger:,}" if isinstance(deger, int) else "olculemedi"


def build_state_md(git: dict, services: dict, tasks: dict, production: dict,
                   coverage: dict | None = None, migrations: dict | None = None,
                   visible: dict | None = None) -> str:
    """Build SESSION_STATE.md content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Session State (auto-saved: {now})",
        "",
        "## Quick Resume",
        f"- **Branch:** {git['branch']}",
        f"- **Last commit:** {git['last_commits'][0] if git['last_commits'] else 'N/A'}",
        f"- **Uncommitted (takipli):** {git['uncommitted_count']} files ({git['uncommitted_py']} .py)",
        f"- **DB question_bank:** {_sayi(production.get('db_question_bank'))}"
        f" · **ogrenci kapisi (mv_safe_for_beta):** {_sayi(production.get('db_safe_pool'))}",
        f"- **d-dataset JSONL satiri:** {_sayi(production.get('jsonl_rows'))}"
        " _(diskteki dosya — servis edilen havuz DEGIL)_",
        f"- **Coverage:** {coverage['percent']}% ({coverage['report_date']})" if coverage and coverage.get('available') else "- **Coverage:** No report found",
        f"- **Migrations:** {migrations['count']} files, latest: {migrations['latest']}" if migrations else "- **Migrations:** N/A",
        f"- **Backend:** {services['backend']}",
        f"- **Frontend:** {services['frontend']}",
        "",
    ]

    if visible is not None:
        toplam = visible.get("commits_today", 0)
        gorunur = visible.get("user_visible_today", 0)
        if toplam and not gorunur:
            lines.append(
                f"> ⚠ **E3: bugun {toplam} commit atildi, kullanici-gorunur cikti 0.** "
                f"Dokunulmasi beklenen yollar: {', '.join(visible.get('paths', []))}"
            )
        else:
            lines.append(f"- **E3 kullanici-gorunur commit (bugun):** {gorunur}/{toplam}")
        lines.append("")

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

    # Git state snapshot (-uno: takipsiz tarama bu depoda >60 sn)
    git_output = (
        run_git("status", "--porcelain", "--untracked-files=no")
        + "\n"
        + run_git("log", "-3", "--oneline")
    )
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
        coverage = get_coverage_state()
        migrations = get_migration_state()
        visible = get_visible_output_state()

        # Atomic writes
        md_content = build_state_md(
            git, services, tasks, production, coverage, migrations, visible
        )
        atomic_write(STATE_FILE, md_content)

        state_json = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "git": git,
            "services": services,
            "tasks": tasks,
            "production": production,
            "coverage": coverage,
            "migrations": migrations,
            "visible_output": visible,
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
