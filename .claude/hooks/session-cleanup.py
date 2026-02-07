#!/usr/bin/env python3
"""
SessionEnd Hook - Claude Code 2026
Oturum bittiğinde çalışır.

Görevler:
1. Context'i kaydet
2. Açık task'ları işaretle
3. Metrics finalize
4. Cleanup
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_session_id() -> str:
    """Mevcut session ID'yi al."""
    sessions_dir = Path.home() / ".claude" / "sessions"
    current_file = sessions_dir / "current.json"

    if current_file.exists():
        try:
            with open(current_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("session_id", "unknown")
        except Exception:
            pass

    return os.environ.get("CLAUDE_SESSION_ID", "unknown")


def save_context_summary() -> None:
    """Context özetini kaydet."""
    memory_dir = Path.home() / ".claude" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    context_file = memory_dir / "last_context.json"

    # Basit context özeti
    context = {
        "session_id": get_session_id(),
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "working_dir": os.getcwd(),
        "task_list_id": os.environ.get("CLAUDE_CODE_TASK_LIST_ID", "kiro2-master"),
    }

    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)

    print("[SessionEnd] Context saved")


def release_task_ownership() -> int:
    """Sahip olunan task'ları release et."""
    session_id = get_session_id()
    task_list_id = os.environ.get("CLAUDE_CODE_TASK_LIST_ID", "kiro2-master")
    tasks_dir = Path.home() / ".claude" / "tasks" / task_list_id

    if not tasks_dir.exists():
        return 0

    released_count = 0

    for task_file in tasks_dir.glob("task-*.json"):
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task = json.load(f)

            # Bu session'a ait ve in_progress olanları release et
            if task.get("owner") == session_id and task.get("status") == "in_progress":
                task["owner"] = None
                task["status"] = "pending"  # veya "blocked" olarak bırak

                if "metadata" not in task:
                    task["metadata"] = {}
                task["metadata"]["releasedAt"] = datetime.utcnow().isoformat() + "Z"
                task["metadata"]["releasedBy"] = session_id

                with open(task_file, "w", encoding="utf-8") as f:
                    json.dump(task, f, indent=2, ensure_ascii=False)

                released_count += 1
                print(f"[SessionEnd] Released task: {task['id']}")
        except Exception as e:
            print(f"[SessionEnd] Error releasing task {task_file.name}: {e}")

    return released_count


def update_session_history() -> None:
    """Session history'yi güncelle."""
    sessions_dir = Path.home() / ".claude" / "sessions"
    current_file = sessions_dir / "current.json"

    if not current_file.exists():
        return

    try:
        with open(current_file, "r", encoding="utf-8") as f:
            session_info = json.load(f)

        session_info["ended_at"] = datetime.utcnow().isoformat() + "Z"

        # Duration hesapla
        if "started_at" in session_info:
            try:
                start = datetime.fromisoformat(session_info["started_at"].replace("Z", "+00:00"))
                end = datetime.utcnow()
                duration = (end - start.replace(tzinfo=None)).total_seconds()
                session_info["duration_seconds"] = int(duration)
            except Exception:
                pass

        # Archive'a taşı
        archive_dir = sessions_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        session_id = session_info.get("session_id", "unknown")
        archive_file = archive_dir / f"{session_id}.json"

        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)

        # current.json'ı sil
        current_file.unlink()

        print(f"[SessionEnd] Session archived: {session_id}")
    except Exception as e:
        print(f"[SessionEnd] Error archiving session: {e}")


def finalize_metrics() -> None:
    """Metrics'i finalize et."""
    metrics_dir = Path.home() / ".claude" / "metrics"

    if not metrics_dir.exists():
        return

    daily_file = metrics_dir / f"{datetime.now().strftime('%Y%m%d')}_summary.json"

    # Bugünkü session'ı ekle
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "session_id": get_session_id(),
        "ended_at": datetime.utcnow().isoformat() + "Z",
    }

    # Mevcut metrikleri ekle
    metrics_file = metrics_dir / "subagent_metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                metrics = json.load(f)
            summary["subagent_metrics"] = metrics
        except Exception:
            pass

    with open(daily_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def print_summary(released_count: int) -> None:
    """Oturum özeti yazdır."""
    separator = "=" * 60
    print(f"\n{separator}")
    print("👋 KIRO2 Claude Code Session Ended")
    print(separator)
    print(f"Session ID: {get_session_id()}")
    print(f"Released Tasks: {released_count}")
    print(f"Context saved: ~/.claude/memory/last_context.json")
    print(separator)
    print()


def main() -> int:
    """Ana fonksiyon."""
    # Context kaydet
    save_context_summary()

    # Task ownership release
    released_count = release_task_ownership()

    # Session history güncelle
    update_session_history()

    # Metrics finalize
    finalize_metrics()

    # Özet
    print_summary(released_count)

    # Her zaman success dön (non-blocking hook)
    return 0


if __name__ == "__main__":
    sys.exit(main())
