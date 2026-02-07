#!/usr/bin/env python3
"""
KIRO2 Task Manager - Claude Code 2026 Tasks API Implementation

Dependency-aware task management with wave-based parallelism.
Boris Cherny standards compliant.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import uuid


class TaskStatus(str, Enum):
    """Task status enum."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enum."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TaskMetadata:
    """Task metadata."""
    estimatedHours: Optional[float] = None
    actualHours: Optional[float] = None
    commits: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Task:
    """Task data class."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    blockedBy: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: list[str] = field(default_factory=list)
    createdAt: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    metadata: TaskMetadata = field(default_factory=TaskMetadata)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        d = asdict(self)
        d["status"] = self.status.value
        d["priority"] = self.priority.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Create from dictionary."""
        data["status"] = TaskStatus(data.get("status", "pending"))
        data["priority"] = TaskPriority(data.get("priority", "medium"))
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"] = TaskMetadata(**data["metadata"])
        return cls(**data)


class TaskManager:
    """Task manager for KIRO2 project."""

    def __init__(self, task_list_id: str = "kiro2-master"):
        """Initialize task manager."""
        self.task_list_id = task_list_id
        self.base_dir = Path.home() / ".claude" / "tasks" / task_list_id
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_task_path(self, task_id: str) -> Path:
        """Get path for task file."""
        return self.base_dir / f"{task_id}.json"

    def _generate_id(self) -> str:
        """Generate unique task ID."""
        existing = self.list_tasks()
        max_num = 0
        for task in existing:
            try:
                num = int(task.id.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                pass
        return f"task-{max_num + 1:03d}"

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        tags: list[str] | None = None,
        blocked_by: list[str] | None = None,
    ) -> Task:
        """Create a new task."""
        task_id = self._generate_id()
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=TaskPriority(priority),
            tags=tags or [],
            blockedBy=blocked_by or [],
        )

        # Check if blocked
        if task.blockedBy:
            incomplete = []
            for dep_id in task.blockedBy:
                dep_task = self.get_task(dep_id)
                if dep_task and dep_task.status != TaskStatus.COMPLETED:
                    incomplete.append(dep_id)
            if incomplete:
                task.status = TaskStatus.BLOCKED

        # Update blocks list of dependencies
        for dep_id in task.blockedBy:
            dep_task = self.get_task(dep_id)
            if dep_task and task_id not in dep_task.blocks:
                dep_task.blocks.append(task_id)
                self._save_task(dep_task)

        self._save_task(task)
        print(f"Created task: {task_id} - {title}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        path = self._get_task_path(task_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Task.from_dict(data)

    def _save_task(self, task: Task) -> None:
        """Save task to file."""
        path = self._get_task_path(task.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(task.to_dict(), f, indent=2, ensure_ascii=False)

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        owner: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> Optional[Task]:
        """Update an existing task."""
        task = self.get_task(task_id)
        if not task:
            print(f"Task not found: {task_id}")
            return None

        if title:
            task.title = title
        if description:
            task.description = description
        if owner:
            task.owner = owner
        if priority:
            task.priority = TaskPriority(priority)
        if tags:
            task.tags = tags
        if notes:
            task.metadata.notes = notes

        if status:
            new_status = TaskStatus(status)
            old_status = task.status

            # Handle status transitions
            if new_status == TaskStatus.IN_PROGRESS and not task.startedAt:
                task.startedAt = datetime.utcnow().isoformat() + "Z"

            if new_status == TaskStatus.COMPLETED:
                task.completedAt = datetime.utcnow().isoformat() + "Z"
                # Unblock dependent tasks
                self._unblock_dependents(task_id)

            task.status = new_status

        self._save_task(task)
        print(f"Updated task: {task_id}")
        return task

    def _unblock_dependents(self, completed_task_id: str) -> None:
        """Unblock tasks that were waiting on completed task."""
        all_tasks = self.list_tasks()
        for task in all_tasks:
            if completed_task_id in task.blockedBy and task.status == TaskStatus.BLOCKED:
                # Check if all dependencies are now complete
                all_complete = True
                for dep_id in task.blockedBy:
                    dep_task = self.get_task(dep_id)
                    if dep_task and dep_task.status != TaskStatus.COMPLETED:
                        all_complete = False
                        break

                if all_complete:
                    task.status = TaskStatus.PENDING
                    self._save_task(task)
                    print(f"  Unblocked: {task.id} - {task.title}")

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[Task]:
        """List all tasks with optional filters."""
        tasks = []
        for path in self.base_dir.glob("task-*.json"):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            task = Task.from_dict(data)

            # Apply filters
            if status and task.status.value != status:
                continue
            if priority and task.priority.value != priority:
                continue
            if tags and not any(t in task.tags for t in tags):
                continue

            tasks.append(task)

        # Sort by priority and creation time
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.priority.value, 1), t.createdAt))
        return tasks

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        path = self._get_task_path(task_id)
        if path.exists():
            path.unlink()
            print(f"Deleted task: {task_id}")
            return True
        print(f"Task not found: {task_id}")
        return False

    def get_waves(self) -> list[list[Task]]:
        """Calculate wave-based execution order."""
        all_tasks = self.list_tasks()
        completed_ids = {t.id for t in all_tasks if t.status == TaskStatus.COMPLETED}
        remaining = [t for t in all_tasks if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)]

        waves = []
        while remaining:
            # Find tasks with all dependencies satisfied
            wave = []
            for task in remaining:
                deps_satisfied = all(dep_id in completed_ids for dep_id in task.blockedBy)
                if deps_satisfied:
                    wave.append(task)

            if not wave:
                # Circular dependency or stuck tasks
                print("Warning: Some tasks have unresolvable dependencies")
                break

            waves.append(wave)
            for task in wave:
                completed_ids.add(task.id)
            remaining = [t for t in remaining if t.id not in completed_ids]

        return waves

    def print_status(self) -> None:
        """Print current task status."""
        all_tasks = self.list_tasks()

        print(f"\n{'='*60}")
        print(f"KIRO2 Task Status - {self.task_list_id}")
        print(f"{'='*60}\n")

        # Group by status
        by_status: dict[str, list[Task]] = {}
        for task in all_tasks:
            status = task.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)

        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "blocked": "🚫",
            "failed": "❌",
            "cancelled": "⛔",
        }

        for status in ["in_progress", "pending", "blocked", "completed", "failed", "cancelled"]:
            tasks = by_status.get(status, [])
            if tasks:
                emoji = status_emoji.get(status, "")
                print(f"{emoji} {status.upper()} ({len(tasks)})")
                for task in tasks:
                    priority_mark = "!" if task.priority == TaskPriority.HIGH else ""
                    blocked_info = f" [blocked by: {', '.join(task.blockedBy)}]" if task.blockedBy else ""
                    print(f"   {task.id}: {task.title}{priority_mark}{blocked_info}")
                print()

        # Summary
        total = len(all_tasks)
        completed = len(by_status.get("completed", []))
        print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%)" if total > 0 else "No tasks")

    def print_waves(self) -> None:
        """Print wave-based execution plan."""
        waves = self.get_waves()

        print(f"\n{'='*60}")
        print("Wave-Based Execution Plan")
        print(f"{'='*60}\n")

        for i, wave in enumerate(waves, 1):
            print(f"Wave {i} (Parallel):")
            for task in wave:
                deps = f" <- [{', '.join(task.blockedBy)}]" if task.blockedBy else ""
                print(f"  {task.id}: {task.title}{deps}")
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="KIRO2 Task Manager")
    parser.add_argument(
        "--task-list",
        default=os.environ.get("CLAUDE_CODE_TASK_LIST_ID", "kiro2-master"),
        help="Task list ID",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("--title", "-t", required=True, help="Task title")
    create_parser.add_argument("--description", "-d", default="", help="Task description")
    create_parser.add_argument("--priority", "-p", default="medium", choices=["high", "medium", "low"])
    create_parser.add_argument("--tags", nargs="*", default=[], help="Task tags")
    create_parser.add_argument("--blocked-by", nargs="*", default=[], help="Blocking task IDs")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("task_id", help="Task ID")
    update_parser.add_argument("--status", "-s", choices=["pending", "in_progress", "completed", "blocked", "failed", "cancelled"])
    update_parser.add_argument("--title", "-t", help="New title")
    update_parser.add_argument("--description", "-d", help="New description")
    update_parser.add_argument("--owner", "-o", help="Owner session ID")
    update_parser.add_argument("--priority", "-p", choices=["high", "medium", "low"])
    update_parser.add_argument("--tags", nargs="*", help="New tags")
    update_parser.add_argument("--notes", "-n", help="Add notes")

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status", "-s", choices=["pending", "in_progress", "completed", "blocked", "failed", "cancelled"])
    list_parser.add_argument("--priority", "-p", choices=["high", "medium", "low"])
    list_parser.add_argument("--tags", nargs="*", help="Filter by tags")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", help="Task ID to delete")

    # Status command
    subparsers.add_parser("status", help="Show task status")

    # Waves command
    subparsers.add_parser("waves", help="Show wave-based execution plan")

    args = parser.parse_args()
    manager = TaskManager(args.task_list)

    if args.command == "create":
        manager.create_task(
            title=args.title,
            description=args.description,
            priority=args.priority,
            tags=args.tags,
            blocked_by=args.blocked_by,
        )
    elif args.command == "update":
        manager.update_task(
            task_id=args.task_id,
            status=args.status,
            title=args.title,
            description=args.description,
            owner=args.owner,
            priority=args.priority,
            tags=args.tags,
            notes=args.notes,
        )
    elif args.command == "list":
        tasks = manager.list_tasks(status=args.status, priority=args.priority, tags=args.tags)
        for task in tasks:
            print(f"{task.id}: [{task.status.value}] {task.title}")
    elif args.command == "delete":
        manager.delete_task(args.task_id)
    elif args.command == "status":
        manager.print_status()
    elif args.command == "waves":
        manager.print_waves()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
