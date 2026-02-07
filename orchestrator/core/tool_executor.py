"""
KIRO2 Orchestrator - Tool Executor
==================================
Güvenli tool execution için sandbox.
- Whitelist/Blocklist enforcement
- Timeout handling
- Output capture
- Rollback support
"""

from __future__ import annotations
import asyncio
import subprocess
import tempfile
import shutil
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import json


class ToolCategory(str, Enum):
    """Tool kategorileri"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    SHELL = "shell"
    GIT = "git"
    LINT = "lint"
    TEST = "test"
    BUILD = "build"
    NETWORK = "network"


@dataclass
class ToolResult:
    """Tool execution sonucu"""
    tool_name: str
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    duration_ms: float = 0.0
    files_modified: list[str] = field(default_factory=list)
    rollback_possible: bool = True


@dataclass
class ToolConfig:
    """Tool yapılandırması"""
    name: str
    category: ToolCategory
    timeout: float = 30.0
    requires_confirmation: bool = False
    allowed: bool = True


# Tool whitelist/blocklist
TOOL_ALLOWLIST: dict[str, ToolConfig] = {
    # File operations
    "read_file": ToolConfig("read_file", ToolCategory.FILE_READ),
    "write_file": ToolConfig("write_file", ToolCategory.FILE_WRITE),
    "edit_file": ToolConfig("edit_file", ToolCategory.FILE_WRITE),
    "create_file": ToolConfig("create_file", ToolCategory.FILE_WRITE),
    "list_directory": ToolConfig("list_directory", ToolCategory.FILE_READ),
    "search_files": ToolConfig("search_files", ToolCategory.FILE_READ),
    
    # Git operations
    "git_status": ToolConfig("git_status", ToolCategory.GIT),
    "git_diff": ToolConfig("git_diff", ToolCategory.GIT),
    "git_add": ToolConfig("git_add", ToolCategory.GIT),
    "git_commit": ToolConfig("git_commit", ToolCategory.GIT),
    "git_log": ToolConfig("git_log", ToolCategory.GIT),
    
    # Lint & Test
    "run_lint": ToolConfig("run_lint", ToolCategory.LINT, timeout=60.0),
    "run_tests": ToolConfig("run_tests", ToolCategory.TEST, timeout=120.0),
    "run_typecheck": ToolConfig("run_typecheck", ToolCategory.LINT, timeout=60.0),
    
    # Build
    "run_build": ToolConfig("run_build", ToolCategory.BUILD, timeout=180.0),
}

TOOL_BLOCKLIST: set[str] = {
    "rm_rf",
    "delete_all",
    "format_disk",
    "curl_external",
    "wget",
    "ssh",
    "scp",
    "sudo",
    "chmod_777",
}


class ToolExecutor(ABC):
    """Abstract tool executor"""
    
    @abstractmethod
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        pass


class FileOperations:
    """File system operations"""
    
    def __init__(self, base_path: Path, backup_dir: Optional[Path] = None):
        self.base_path = base_path
        self.backup_dir = backup_dir or base_path / ".kiro_backups"
        self._modified_files: list[tuple[Path, Optional[bytes]]] = []
    
    def _ensure_safe_path(self, path: str) -> Path:
        """Path'in güvenli olduğunu doğrula"""
        full_path = (self.base_path / path).resolve()
        if not str(full_path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Path traversal attempt: {path}")
        return full_path
    
    async def read_file(self, path: str) -> ToolResult:
        """Dosya oku"""
        try:
            full_path = self._ensure_safe_path(path)
            content = full_path.read_text(encoding="utf-8")
            return ToolResult(
                tool_name="read_file",
                success=True,
                output=content,
            )
        except Exception as e:
            return ToolResult(
                tool_name="read_file",
                success=False,
                output="",
                error=str(e),
                exit_code=1,
            )
    
    async def write_file(self, path: str, content: str) -> ToolResult:
        """Dosya yaz (backup ile)"""
        try:
            full_path = self._ensure_safe_path(path)
            
            # Backup mevcut dosyayı
            original_content = None
            if full_path.exists():
                original_content = full_path.read_bytes()
            self._modified_files.append((full_path, original_content))
            
            # Parent directory oluştur
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Yaz
            full_path.write_text(content, encoding="utf-8")
            
            return ToolResult(
                tool_name="write_file",
                success=True,
                output=f"Written {len(content)} bytes to {path}",
                files_modified=[path],
            )
        except Exception as e:
            return ToolResult(
                tool_name="write_file",
                success=False,
                output="",
                error=str(e),
                exit_code=1,
            )
    
    async def edit_file(self, path: str, old_str: str, new_str: str) -> ToolResult:
        """Dosyada string değiştir"""
        try:
            full_path = self._ensure_safe_path(path)
            
            if not full_path.exists():
                return ToolResult(
                    tool_name="edit_file",
                    success=False,
                    output="",
                    error=f"File not found: {path}",
                    exit_code=1,
                )
            
            content = full_path.read_text(encoding="utf-8")
            
            # Backup
            self._modified_files.append((full_path, content.encode()))
            
            # Replace
            if old_str not in content:
                return ToolResult(
                    tool_name="edit_file",
                    success=False,
                    output="",
                    error=f"String not found in file: {old_str[:50]}...",
                    exit_code=1,
                )
            
            new_content = content.replace(old_str, new_str, 1)
            full_path.write_text(new_content, encoding="utf-8")
            
            return ToolResult(
                tool_name="edit_file",
                success=True,
                output=f"Edited {path}",
                files_modified=[path],
            )
        except Exception as e:
            return ToolResult(
                tool_name="edit_file",
                success=False,
                output="",
                error=str(e),
                exit_code=1,
            )
    
    async def list_directory(self, path: str = ".", pattern: str = "*") -> ToolResult:
        """Dizin listele"""
        try:
            full_path = self._ensure_safe_path(path)
            
            if not full_path.exists():
                return ToolResult(
                    tool_name="list_directory",
                    success=False,
                    output="",
                    error=f"Directory not found: {path}",
                    exit_code=1,
                )
            
            items = list(full_path.glob(pattern))
            output = "\n".join([
                f"{'[DIR]' if p.is_dir() else '[FILE]'} {p.relative_to(self.base_path)}"
                for p in sorted(items)[:100]  # Limit output
            ])
            
            return ToolResult(
                tool_name="list_directory",
                success=True,
                output=output,
            )
        except Exception as e:
            return ToolResult(
                tool_name="list_directory",
                success=False,
                output="",
                error=str(e),
                exit_code=1,
            )
    
    def rollback(self):
        """Tüm değişiklikleri geri al"""
        for path, original_content in reversed(self._modified_files):
            try:
                if original_content is None:
                    # Dosya yeni oluşturulmuştu, sil
                    path.unlink(missing_ok=True)
                else:
                    # Orijinal içeriği geri yükle
                    path.write_bytes(original_content)
            except Exception:
                pass  # Best effort rollback
        self._modified_files.clear()
    
    def commit_changes(self):
        """Değişiklikleri onayla, backup'ları temizle"""
        self._modified_files.clear()


class ShellExecutor:
    """Shell command execution"""
    
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
    
    async def run(
        self,
        command: str,
        timeout: float = 30.0,
        env: Optional[dict] = None
    ) -> ToolResult:
        """Shell komutu çalıştır"""
        try:
            # Environment setup
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            start_time = asyncio.get_event_loop().time()
            
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir),
                env=exec_env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(
                    tool_name="shell",
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout}s",
                    exit_code=-1,
                    rollback_possible=False,
                )
            
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return ToolResult(
                tool_name="shell",
                success=proc.returncode == 0,
                output=stdout.decode("utf-8", errors="replace"),
                error=stderr.decode("utf-8", errors="replace") if stderr else None,
                exit_code=proc.returncode or 0,
                duration_ms=duration_ms,
                rollback_possible=False,
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="shell",
                success=False,
                output="",
                error=str(e),
                exit_code=1,
                rollback_possible=False,
            )


class LintRunner:
    """Lint komutları"""
    
    def __init__(self, shell: ShellExecutor, base_path: Path):
        self.shell = shell
        self.base_path = base_path
    
    async def run_ruff(self, paths: list[str], fix: bool = False) -> ToolResult:
        """Ruff lint çalıştır"""
        fix_flag = "--fix" if fix else ""
        cmd = f"ruff check {fix_flag} {' '.join(paths)}"
        result = await self.shell.run(cmd, timeout=60.0)
        result.tool_name = "run_lint"
        return result
    
    async def run_eslint(self, paths: list[str], fix: bool = False) -> ToolResult:
        """ESLint çalıştır"""
        fix_flag = "--fix" if fix else ""
        cmd = f"npx eslint {fix_flag} {' '.join(paths)}"
        result = await self.shell.run(cmd, timeout=60.0)
        result.tool_name = "run_lint"
        return result
    
    async def run_mypy(self, paths: list[str]) -> ToolResult:
        """MyPy type check"""
        cmd = f"mypy {' '.join(paths)}"
        result = await self.shell.run(cmd, timeout=60.0)
        result.tool_name = "run_typecheck"
        return result
    
    async def run_tsc(self) -> ToolResult:
        """TypeScript type check"""
        cmd = "npx tsc --noEmit"
        result = await self.shell.run(cmd, timeout=60.0)
        result.tool_name = "run_typecheck"
        return result


class TestRunner:
    """Test komutları"""
    
    def __init__(self, shell: ShellExecutor):
        self.shell = shell
    
    async def run_pytest(
        self,
        paths: Optional[list[str]] = None,
        coverage: bool = False
    ) -> ToolResult:
        """Pytest çalıştır"""
        path_str = " ".join(paths) if paths else ""
        cov_flag = "--cov --cov-report=term-missing" if coverage else ""
        cmd = f"pytest {cov_flag} {path_str} -v"
        result = await self.shell.run(cmd, timeout=180.0)
        result.tool_name = "run_tests"
        return result
    
    async def run_jest(self, paths: Optional[list[str]] = None) -> ToolResult:
        """Jest çalıştır"""
        path_str = " ".join(paths) if paths else ""
        cmd = f"npx jest {path_str} --passWithNoTests"
        result = await self.shell.run(cmd, timeout=180.0)
        result.tool_name = "run_tests"
        return result


class SandboxToolExecutor(ToolExecutor):
    """
    Güvenli tool execution sandbox
    - Whitelist/blocklist enforcement
    - File operation tracking
    - Rollback support
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.file_ops = FileOperations(project_path)
        self.shell = ShellExecutor(project_path)
        self.lint = LintRunner(self.shell, project_path)
        self.test = TestRunner(self.shell)
        self._execution_log: list[ToolResult] = []
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Tool çalıştır
        """
        # Blocklist kontrolü
        if tool_name in TOOL_BLOCKLIST:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Tool blocked: {tool_name}",
                exit_code=1,
            )
        
        # Whitelist kontrolü
        config = TOOL_ALLOWLIST.get(tool_name)
        if not config:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}",
                exit_code=1,
            )
        
        if not config.allowed:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Tool not allowed: {tool_name}",
                exit_code=1,
            )
        
        # Execute based on category
        try:
            result = await self._dispatch(tool_name, config, **kwargs)
            self._execution_log.append(result)
            return result
        except Exception as e:
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=str(e),
                exit_code=1,
            )
            self._execution_log.append(result)
            return result
    
    async def _dispatch(
        self,
        tool_name: str,
        config: ToolConfig,
        **kwargs
    ) -> ToolResult:
        """Tool'u kategoriye göre çalıştır"""
        
        # File operations
        if tool_name == "read_file":
            return await self.file_ops.read_file(kwargs["path"])
        elif tool_name == "write_file":
            return await self.file_ops.write_file(kwargs["path"], kwargs["content"])
        elif tool_name == "edit_file":
            return await self.file_ops.edit_file(
                kwargs["path"],
                kwargs["old_str"],
                kwargs["new_str"]
            )
        elif tool_name == "list_directory":
            return await self.file_ops.list_directory(
                kwargs.get("path", "."),
                kwargs.get("pattern", "*")
            )
        
        # Lint operations
        elif tool_name == "run_lint":
            lang = kwargs.get("language", "python")
            paths = kwargs.get("paths", ["."])
            fix = kwargs.get("fix", False)
            if lang == "python":
                return await self.lint.run_ruff(paths, fix)
            else:
                return await self.lint.run_eslint(paths, fix)
        
        elif tool_name == "run_typecheck":
            lang = kwargs.get("language", "python")
            paths = kwargs.get("paths", ["."])
            if lang == "python":
                return await self.lint.run_mypy(paths)
            else:
                return await self.lint.run_tsc()
        
        # Test operations
        elif tool_name == "run_tests":
            lang = kwargs.get("language", "python")
            paths = kwargs.get("paths")
            if lang == "python":
                return await self.test.run_pytest(paths, kwargs.get("coverage", False))
            else:
                return await self.test.run_jest(paths)
        
        # Git operations
        elif tool_name.startswith("git_"):
            git_cmd = tool_name.replace("git_", "git ")
            args = kwargs.get("args", "")
            return await self.shell.run(f"{git_cmd} {args}", timeout=30.0)
        
        else:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Tool not implemented: {tool_name}",
                exit_code=1,
            )
    
    def rollback_all(self):
        """Tüm file değişikliklerini geri al"""
        self.file_ops.rollback()
    
    def commit_all(self):
        """Tüm değişiklikleri onayla"""
        self.file_ops.commit_changes()
    
    def get_execution_log(self) -> list[ToolResult]:
        """Execution log'u döndür"""
        return self._execution_log.copy()


# Singleton factory
_executor: Optional[SandboxToolExecutor] = None


def get_tool_executor(project_path: Optional[Path] = None) -> SandboxToolExecutor:
    """Tool executor singleton"""
    global _executor
    if _executor is None:
        if project_path is None:
            project_path = Path.cwd()
        _executor = SandboxToolExecutor(project_path)
    return _executor
