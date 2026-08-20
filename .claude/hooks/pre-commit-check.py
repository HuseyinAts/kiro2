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


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ders_dedektorleri import ters_tirnak_riski, tmp_ad_alani_riski  # noqa: E402


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
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        # SESSIZCE YUTMA (#495): bu kancanin kendisi bir kontrol; sessizce
        # bos donerse "temiz" sanilir. Bloklamiyoruz (kontrol basarisizligi
        # commit'i durdurmamali) ama GORUNUR oluyor.
        print(f"[uyari] kontrol kosulamadi: {type(e).__name__}: {e}", file=sys.stderr)
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


def check_case_duplicates() -> list[str]:
    """Check staged files for case-only duplicates (e.g., App.tsx vs app.tsx).

    Windows NTFS is case-insensitive but Git/Linux are case-sensitive.
    This causes Docker build failures repeatedly (3+ sessions).
    """
    warnings = []
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, timeout=10,
            cwd=os.environ.get("GIT_WORK_TREE", None),
        )
        if result.returncode != 0:
            return []

        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        # Group by lowercase path
        seen: dict[str, list[str]] = {}
        for f in files:
            key = f.lower()
            seen.setdefault(key, []).append(f)

        for key, paths in seen.items():
            if len(paths) > 1:
                warnings.append(
                    f"Case duplicate: {' vs '.join(paths)} — will break Docker/Linux builds"
                )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        # SESSIZCE YUTMA (#495): bu kancanin kendisi bir kontrol; sessizce
        # bos donerse "temiz" sanilir. Bloklamiyoruz (kontrol basarisizligi
        # commit'i durdurmamali) ama GORUNUR oluyor.
        print(f"[uyari] kontrol kosulamadi: {type(e).__name__}: {e}", file=sys.stderr)
    return warnings


def check_model_imports() -> list[str]:
    """Check if backend models import cleanly (SQLAlchemy MetaData conflicts).

    Catches: duplicate table definitions, missing back_populates relationships,
    circular imports. Runs only when backend/models/ files are staged.
    """
    warnings = []
    try:
        # Check if any model files are staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return []

        staged = result.stdout.strip().split("\n")
        model_files = [f for f in staged if f.startswith("backend/models/") and f.endswith(".py")]
        if not model_files:
            return []

        # Try importing all models — catches MetaData conflicts & relationship errors
        check_result = subprocess.run(
            ["python", "-c", "from models import *; print('OK')"],
            capture_output=True, text=True, timeout=15,
            cwd=os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "backend"),
        )
        if check_result.returncode != 0:
            err = check_result.stderr.strip()[-200:] if check_result.stderr else "unknown error"
            warnings.append(f"Model import failed: {err}")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        # SESSIZCE YUTMA (#495): bu kancanin kendisi bir kontrol; sessizce
        # bos donerse "temiz" sanilir. Bloklamiyoruz (kontrol basarisizligi
        # commit'i durdurmamali) ama GORUNUR oluyor.
        print(f"[uyari] kontrol kosulamadi: {type(e).__name__}: {e}", file=sys.stderr)
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

    # --- /tmp ad-alani: UYARIR, BLOKLAMAZ ---------------------------------
    # `is_git_commit_or_add` kapisinin ONUNDE olmali: /tmp her bash komutunda
    # gecerli, yalniz git'te degil. Bloklamiyor cunku mesru kullanimi var
    # (tek komutluk gecici dosya); bloklasaydik surtusme yaratir, kapatilir ve
    # kontrol yine olurdu. Gorunur olmasi yeterli.
    tmp_uyari = tmp_ad_alani_riski(command)
    if tmp_uyari:
        print(f"[uyari] {tmp_uyari}", file=sys.stderr)

    # --- ters tirnak: BLOKLAR ---------------------------------------------
    # Bloklamak orantili: maliyeti sifir (`-F` ile dosyadan ver) ama ihlali
    # SESSIZCE mesaji bozuyor. d03674d9d'de defter kimligi silindi, commit
    # EXIT=0 verdi, push gecti — hicbir kapi otmedi.
    tirnak_uyari = ters_tirnak_riski(command)
    if tirnak_uyari:
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": tirnak_uyari,
                }
            },
            sys.stdout,
        )
        print(f"\nBLOCKED: {tirnak_uyari}", file=sys.stderr)
        return 2

    if not is_git_commit_or_add(command):
        return 0

    errors = []

    # Check files being added
    errors.extend(check_untracked_large_files(command))

    # Check already staged files (for git commit)
    if command.strip().startswith("git commit"):
        errors.extend(check_staged_files())
        errors.extend(check_case_duplicates())
        errors.extend(check_model_imports())

    if errors:
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Pre-commit check failed: {'; '.join(errors)}",
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
