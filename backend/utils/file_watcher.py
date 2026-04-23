"""
File watcher for detecting changed files using git.

Used by quality hooks to check only modified files.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class FileWatcher:
    """Detects changed files using git diff."""

    def __init__(self, repo_root: Path | None = None):
        """
        Initialize file watcher.

        Args:
            repo_root: Git repository root directory
        """
        self.repo_root = repo_root or self._find_repo_root()

    def _find_repo_root(self) -> Path:
        """Find git repository root."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return Path.cwd()

    def get_changed_files(
        self,
        staged_only: bool = False,
        include_untracked: bool = True
    ) -> list[str]:
        """
        Get list of changed files.

        Args:
            staged_only: Only return staged files
            include_untracked: Include untracked files

        Returns:
            List of changed file paths
        """
        changed: set[str] = set()

        if staged_only:
            # Get staged files
            changed.update(self._get_staged_files())
        else:
            # Get modified files (staged + unstaged)
            changed.update(self._get_modified_files())

            if include_untracked:
                changed.update(self._get_untracked_files())

        return sorted(changed)

    def get_changed_python_files(
        self,
        staged_only: bool = False,
        include_untracked: bool = True
    ) -> list[str]:
        """
        Get list of changed Python files.

        Args:
            staged_only: Only return staged files
            include_untracked: Include untracked files

        Returns:
            List of changed Python file paths
        """
        all_changed = self.get_changed_files(staged_only, include_untracked)
        return [f for f in all_changed if f.endswith(".py")]

    def _get_staged_files(self) -> list[str]:
        """Get staged files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                return [
                    str(self.repo_root / f.strip())
                    for f in result.stdout.strip().split("\n")
                    if f.strip()
                ]
        except Exception:
            pass
        return []

    def _get_modified_files(self) -> list[str]:
        """Get modified files (staged + unstaged)."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                return [
                    str(self.repo_root / f.strip())
                    for f in result.stdout.strip().split("\n")
                    if f.strip()
                ]
        except Exception:
            pass
        return []

    def _get_untracked_files(self) -> list[str]:
        """Get untracked files."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                return [
                    str(self.repo_root / f.strip())
                    for f in result.stdout.strip().split("\n")
                    if f.strip()
                ]
        except Exception:
            pass
        return []

    def is_file_changed(self, file_path: str) -> bool:
        """
        Check if a specific file has changed.

        Args:
            file_path: Path to file

        Returns:
            True if file has changes
        """
        changed_files = self.get_changed_files()
        abs_path = str(Path(file_path).resolve())
        return abs_path in changed_files or file_path in changed_files


def get_changed_python_files(repo_root: Path | None = None) -> list[str]:
    """
    Convenience function to get changed Python files.

    Args:
        repo_root: Git repository root

    Returns:
        List of changed Python file paths
    """
    watcher = FileWatcher(repo_root)
    return watcher.get_changed_python_files()
