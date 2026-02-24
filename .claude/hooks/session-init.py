#!/usr/bin/env python
"""
SessionStart Hook - Claude Code 2026
Oturum başladığında çalışır.

Görevler:
1. Session ID kaydet
2. Environment setup kontrol
3. Son context'i yükle (opsiyonel)
4. Tasks durumunu kontrol et
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows cp1254 emoji crash fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_session_id() -> str:
    """Session ID al veya oluştur."""
    session_id = os.environ.get("CLAUDE_SESSION_ID")
    if not session_id:
        import uuid
        session_id = f"session-{uuid.uuid4().hex[:8]}"
    return session_id


def save_session_info(session_id: str) -> None:
    """Session bilgisini kaydet."""
    sessions_dir = Path.home() / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    session_file = sessions_dir / "current.json"

    session_info = {
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "working_dir": os.getcwd(),
        "task_list_id": os.environ.get("CLAUDE_CODE_TASK_LIST_ID", "kiro2-master"),
    }

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_info, f, indent=2, ensure_ascii=False)

    # History'ye ekle
    history_file = sessions_dir / "history.jsonl"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(session_info, ensure_ascii=False) + "\n")


def check_environment() -> list[str]:
    """Environment ayarlarını kontrol et."""
    warnings = []

    # Kritik environment variable'lar
    required_vars = {
        "CLAUDE_CODE_TASK_LIST_ID": "Task sistemi için gerekli",
    }

    recommended_vars = {
        "ANTHROPIC_API_KEY": "API erişimi için gerekli",
        "GOOGLE_API_KEY": "Gemini MCP için gerekli",
    }

    for var, desc in required_vars.items():
        if not os.environ.get(var):
            warnings.append(f"⚠️ {var} tanımlı değil: {desc}")

    for var, desc in recommended_vars.items():
        if not os.environ.get(var):
            warnings.append(f"ℹ️ {var} tanımlı değil: {desc}")

    return warnings


def check_tasks_status() -> dict:
    """Tasks durumunu kontrol et."""
    task_list_id = os.environ.get("CLAUDE_CODE_TASK_LIST_ID", "kiro2-master")
    tasks_dir = Path.home() / ".claude" / "tasks" / task_list_id

    if not tasks_dir.exists():
        return {"status": "no_tasks", "message": "Task dizini bulunamadı"}

    status_counts = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "blocked": 0,
        "failed": 0,
    }

    for task_file in tasks_dir.glob("task-*.json"):
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task = json.load(f)
            status = task.get("status", "pending")
            if status in status_counts:
                status_counts[status] += 1
        except Exception:
            pass

    total = sum(status_counts.values())

    return {
        "status": "ok",
        "total": total,
        "counts": status_counts,
        "progress": f"{status_counts['completed']}/{total}" if total > 0 else "0/0",
    }


def load_last_context() -> dict | None:
    """Son context'i yükle (varsa)."""
    memory_file = Path.home() / ".claude" / "memory" / "last_context.json"

    if not memory_file.exists():
        return None

    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def print_welcome(session_id: str, warnings: list[str], tasks: dict) -> None:
    """Hoşgeldin mesajı yazdır."""
    separator = "=" * 60
    print(f"\n{separator}")
    print("🚀 KIRO2 Claude Code Session Started")
    print(separator)
    print(f"Session ID: {session_id}")
    print(f"Working Dir: {os.getcwd()}")
    print(f"Task List: {os.environ.get('CLAUDE_CODE_TASK_LIST_ID', 'kiro2-master')}")

    if tasks.get("status") == "ok" and tasks.get("total", 0) > 0:
        print(f"\n📋 Tasks: {tasks['progress']}")
        counts = tasks["counts"]
        if counts["in_progress"] > 0:
            print(f"   🔄 In Progress: {counts['in_progress']}")
        if counts["blocked"] > 0:
            print(f"   🚫 Blocked: {counts['blocked']}")
        if counts["pending"] > 0:
            print(f"   ⏳ Pending: {counts['pending']}")

    if warnings:
        print(f"\n⚠️ Warnings:")
        for w in warnings:
            print(f"   {w}")

    print(separator)
    print()


def main() -> int:
    """Ana fonksiyon."""
    session_id = get_session_id()

    # Session bilgisini kaydet
    save_session_info(session_id)

    # Environment kontrol
    warnings = check_environment()

    # Tasks durumu
    tasks = check_tasks_status()

    # Son context (opsiyonel)
    last_context = load_last_context()
    if last_context:
        print(f"[SessionStart] Last context restored from {last_context.get('saved_at', 'unknown')}")

    # Hoşgeldin mesajı
    print_welcome(session_id, warnings, tasks)

    # Her zaman success dön (non-blocking hook)
    return 0


if __name__ == "__main__":
    sys.exit(main())
