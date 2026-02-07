#!/usr/bin/env python3
"""
SubagentStop Hook - Claude Code 2026
Sub-agent tamamlandığında çalışır.

Görevler:
1. Sub-agent sonuçlarını logla
2. Task sistemini güncelle
3. Metrics topla
4. Bildirim gönder (opsiyonel)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_env_json(key: str, default: dict | None = None) -> dict:
    """Environment variable'dan JSON parse et."""
    value = os.environ.get(key, "")
    if not value:
        return default or {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default or {}


def log_subagent_result(agent_id: str, result: dict) -> None:
    """Sub-agent sonucunu logla."""
    log_dir = Path.home() / ".claude" / "logs" / "subagents"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.jsonl"

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_id": agent_id,
        "status": result.get("status", "unknown"),
        "duration_ms": result.get("duration_ms"),
        "tokens_used": result.get("tokens_used"),
        "model": result.get("model"),
        "task_id": result.get("task_id"),
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def update_task_status(task_id: str, status: str, result: dict) -> None:
    """Task durumunu güncelle."""
    if not task_id:
        return

    task_list_id = os.environ.get("CLAUDE_CODE_TASK_LIST_ID", "kiro2-master")
    task_file = Path.home() / ".claude" / "tasks" / task_list_id / f"{task_id}.json"

    if not task_file.exists():
        return

    with open(task_file, "r", encoding="utf-8") as f:
        task = json.load(f)

    # Durumu güncelle
    if status == "success":
        task["status"] = "completed"
        task["completedAt"] = datetime.utcnow().isoformat() + "Z"
    elif status == "error":
        task["status"] = "failed"

    # Metadata ekle
    if "metadata" not in task:
        task["metadata"] = {}
    task["metadata"]["lastAgentResult"] = {
        "status": status,
        "completedAt": datetime.utcnow().isoformat() + "Z",
    }

    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task, f, indent=2, ensure_ascii=False)

    print(f"[SubagentStop] Task {task_id} updated: {status}")


def collect_metrics(result: dict) -> None:
    """Metrics topla."""
    metrics_dir = Path.home() / ".claude" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    metrics_file = metrics_dir / "subagent_metrics.json"

    # Mevcut metrikleri oku
    if metrics_file.exists():
        with open(metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    else:
        metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_tokens": 0,
            "total_duration_ms": 0,
            "by_model": {},
        }

    # Güncelle
    metrics["total_runs"] += 1
    if result.get("status") == "success":
        metrics["successful_runs"] += 1
    else:
        metrics["failed_runs"] += 1

    if result.get("tokens_used"):
        metrics["total_tokens"] += result["tokens_used"]

    if result.get("duration_ms"):
        metrics["total_duration_ms"] += result["duration_ms"]

    model = result.get("model", "unknown")
    if model not in metrics["by_model"]:
        metrics["by_model"][model] = {"runs": 0, "tokens": 0}
    metrics["by_model"][model]["runs"] += 1
    if result.get("tokens_used"):
        metrics["by_model"][model]["tokens"] += result["tokens_used"]

    metrics["last_updated"] = datetime.utcnow().isoformat() + "Z"

    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def main() -> int:
    """Ana fonksiyon."""
    # Environment'dan bilgileri al
    agent_id = os.environ.get("SUBAGENT_ID", "unknown")
    result = get_env_json("SUBAGENT_RESULT", {})
    task_id = os.environ.get("TASK_ID") or result.get("task_id")

    status = result.get("status", "unknown")

    print(f"[SubagentStop] Agent {agent_id} completed with status: {status}")

    # Log
    log_subagent_result(agent_id, result)

    # Task güncelle
    if task_id:
        update_task_status(task_id, status, result)

    # Metrics topla
    collect_metrics(result)

    # Her zaman success dön (non-blocking hook)
    return 0


if __name__ == "__main__":
    sys.exit(main())
