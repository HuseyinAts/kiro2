"""
KIRO2 Orchestrator - Quality Gates (Doğru Kodun Omurgası)
=========================================================
"Doğru kod = kanıtlanmış kod"
Başarı YALNIZCA tüm kalite kapıları geçince tanımlanır.

Sıra: Lint → TypeCheck → UnitTest → Integration → Security
Her kapı: PASS → sonraki, FAIL(1) → auto-fix, FAIL(2) → strateji değiştir, FAIL(3) → BLOCKED
"""

from __future__ import annotations
import asyncio
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Awaitable
from pathlib import Path

from .state import RunState, QualityGateState, GateResult, TaskStatus


class GateAction(str, Enum):
    """Kapı sonrası aksiyon"""
    CONTINUE = "continue"      # Sonraki kapıya geç
    RETRY_AUTO_FIX = "retry_auto_fix"  # Auto-fix uygula ve tekrar dene
    RETRY_MINIMAL = "retry_minimal"    # Minimal strateji ile tekrar dene
    BLOCKED = "blocked"        # İnsan müdahalesi gerekli


@dataclass
class GateConfig:
    """Kalite kapısı konfigürasyonu"""
    name: str
    command: list[str]
    auto_fix_command: Optional[list[str]] = None
    max_retries: int = 3
    timeout_seconds: int = 120
    required: bool = True
    coverage_threshold: Optional[int] = None  # % cinsinden


@dataclass 
class GateOutput:
    """Kapı çıktısı"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration_ms: int
    action: GateAction


class QualityGate(ABC):
    """Kalite kapısı temel sınıfı"""
    
    def __init__(self, config: GateConfig, working_dir: Path):
        self.config = config
        self.working_dir = working_dir
    
    @abstractmethod
    async def run(self, state: RunState) -> GateOutput:
        """Kapıyı çalıştır"""
        pass
    
    @abstractmethod
    async def auto_fix(self, state: RunState, error: str) -> bool:
        """Otomatik düzeltme uygula"""
        pass
    
    def _determine_action(self, gate_state: QualityGateState, success: bool) -> GateAction:
        """Sonraki aksiyonu belirle"""
        if success:
            return GateAction.CONTINUE
        
        attempts = gate_state.attempts
        
        if attempts == 1 and self.config.auto_fix_command:
            return GateAction.RETRY_AUTO_FIX
        elif attempts == 2:
            return GateAction.RETRY_MINIMAL
        elif attempts >= self.config.max_retries:
            return GateAction.BLOCKED
        else:
            return GateAction.RETRY_AUTO_FIX if self.config.auto_fix_command else GateAction.RETRY_MINIMAL


class LintGate(QualityGate):
    """Lint kalite kapısı (ruff/eslint)"""
    
    async def run(self, state: RunState) -> GateOutput:
        import time
        start = time.time()
        
        try:
            result = await asyncio.create_subprocess_exec(
                *self.config.command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=self.config.timeout_seconds
            )
            
            success = result.returncode == 0
            duration_ms = int((time.time() - start) * 1000)
            
            gate_state = state.quality_gates.get(self.config.name)
            if not success and gate_state:
                state.record_error(self.config.name, stderr.decode())
            elif success and gate_state:
                gate_state.status = GateResult.PASSED
            
            action = self._determine_action(gate_state, success) if gate_state else GateAction.CONTINUE
            
            return GateOutput(
                success=success,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                return_code=result.returncode,
                duration_ms=duration_ms,
                action=action,
            )
        except asyncio.TimeoutError:
            return GateOutput(
                success=False,
                stdout="",
                stderr="Timeout exceeded",
                return_code=-1,
                duration_ms=self.config.timeout_seconds * 1000,
                action=GateAction.BLOCKED,
            )
    
    async def auto_fix(self, state: RunState, error: str) -> bool:
        """Lint hatalarını otomatik düzelt"""
        if not self.config.auto_fix_command:
            return False
        
        try:
            result = await asyncio.create_subprocess_exec(
                *self.config.auto_fix_command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()
            
            gate_state = state.quality_gates.get(self.config.name)
            if gate_state:
                gate_state.auto_fix_applied = True
            
            return result.returncode == 0
        except Exception:
            return False


class TypeCheckGate(QualityGate):
    """Type check kapısı (mypy/tsc)"""
    
    async def run(self, state: RunState) -> GateOutput:
        import time
        start = time.time()
        
        try:
            result = await asyncio.create_subprocess_exec(
                *self.config.command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=self.config.timeout_seconds
            )
            
            success = result.returncode == 0
            duration_ms = int((time.time() - start) * 1000)
            
            gate_state = state.quality_gates.get(self.config.name)
            if not success and gate_state:
                state.record_error(self.config.name, stderr.decode() or stdout.decode())
            elif success and gate_state:
                gate_state.status = GateResult.PASSED
            
            action = self._determine_action(gate_state, success) if gate_state else GateAction.CONTINUE
            
            return GateOutput(
                success=success,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                return_code=result.returncode,
                duration_ms=duration_ms,
                action=action,
            )
        except asyncio.TimeoutError:
            return GateOutput(
                success=False,
                stdout="",
                stderr="Timeout exceeded",
                return_code=-1,
                duration_ms=self.config.timeout_seconds * 1000,
                action=GateAction.BLOCKED,
            )
    
    async def auto_fix(self, state: RunState, error: str) -> bool:
        """Type hatalarını otomatik düzeltemez"""
        return False  # Type hataları manuel düzeltme gerektirir


class UnitTestGate(QualityGate):
    """Unit test kapısı (pytest/jest)"""
    
    async def run(self, state: RunState) -> GateOutput:
        import time
        start = time.time()
        
        try:
            result = await asyncio.create_subprocess_exec(
                *self.config.command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=self.config.timeout_seconds
            )
            
            stdout_text = stdout.decode()
            stderr_text = stderr.decode()
            
            # Coverage kontrolü
            success = result.returncode == 0
            if success and self.config.coverage_threshold:
                coverage = self._parse_coverage(stdout_text)
                if coverage < self.config.coverage_threshold:
                    success = False
                    stderr_text += f"\nCoverage {coverage}% < threshold {self.config.coverage_threshold}%"
            
            duration_ms = int((time.time() - start) * 1000)
            
            gate_state = state.quality_gates.get(self.config.name)
            if not success and gate_state:
                state.record_error(self.config.name, stderr_text or stdout_text)
            elif success and gate_state:
                gate_state.status = GateResult.PASSED
            
            action = self._determine_action(gate_state, success) if gate_state else GateAction.CONTINUE
            
            return GateOutput(
                success=success,
                stdout=stdout_text,
                stderr=stderr_text,
                return_code=result.returncode,
                duration_ms=duration_ms,
                action=action,
            )
        except asyncio.TimeoutError:
            return GateOutput(
                success=False,
                stdout="",
                stderr="Timeout exceeded",
                return_code=-1,
                duration_ms=self.config.timeout_seconds * 1000,
                action=GateAction.BLOCKED,
            )
    
    def _parse_coverage(self, output: str) -> int:
        """Coverage yüzdesini parse et"""
        import re
        match = re.search(r'(\d+)%', output)
        return int(match.group(1)) if match else 0
    
    async def auto_fix(self, state: RunState, error: str) -> bool:
        """Test hatalarını otomatik düzeltemez"""
        return False


class SecurityGate(QualityGate):
    """Security scan kapısı (bandit/semgrep)"""
    
    async def run(self, state: RunState) -> GateOutput:
        import time
        start = time.time()
        
        try:
            result = await asyncio.create_subprocess_exec(
                *self.config.command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=self.config.timeout_seconds
            )
            
            # Security için severity kontrolü
            stdout_text = stdout.decode()
            success = result.returncode == 0 or not self._has_critical_issues(stdout_text)
            
            duration_ms = int((time.time() - start) * 1000)
            
            gate_state = state.quality_gates.get(self.config.name)
            if not success and gate_state:
                state.record_error(self.config.name, stdout_text)
            elif success and gate_state:
                gate_state.status = GateResult.PASSED
            
            action = self._determine_action(gate_state, success) if gate_state else GateAction.CONTINUE
            
            return GateOutput(
                success=success,
                stdout=stdout_text,
                stderr=stderr.decode(),
                return_code=result.returncode,
                duration_ms=duration_ms,
                action=action,
            )
        except asyncio.TimeoutError:
            return GateOutput(
                success=False,
                stdout="",
                stderr="Timeout exceeded",
                return_code=-1,
                duration_ms=self.config.timeout_seconds * 1000,
                action=GateAction.BLOCKED,
            )
    
    def _has_critical_issues(self, output: str) -> bool:
        """Kritik güvenlik sorunları var mı?"""
        critical_keywords = ["HIGH", "CRITICAL", "severity: high", "severity: critical"]
        return any(kw.lower() in output.lower() for kw in critical_keywords)
    
    async def auto_fix(self, state: RunState, error: str) -> bool:
        """Security sorunlarını otomatik düzeltemez"""
        return False


class QualityGatePipeline:
    """
    Kalite kapıları pipeline'ı.
    
    Sıralı çalıştırma: Lint → TypeCheck → UnitTest → Integration → Security
    Fail-fast: Bir kapı başarısız olursa durur ve aksiyon döndürür.
    """
    
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.gates: list[QualityGate] = []
        self._setup_default_gates()
    
    def _setup_default_gates(self) -> None:
        """Varsayılan kapıları oluştur"""
        # Python backend kapıları
        self.gates = [
            LintGate(
                GateConfig(
                    name="lint",
                    command=["ruff", "check", "."],
                    auto_fix_command=["ruff", "check", "--fix", "."],
                    max_retries=3,
                    timeout_seconds=60,
                ),
                self.working_dir,
            ),
            TypeCheckGate(
                GateConfig(
                    name="typecheck",
                    command=["mypy", "--strict", "."],
                    max_retries=3,
                    timeout_seconds=120,
                ),
                self.working_dir,
            ),
            UnitTestGate(
                GateConfig(
                    name="unit_test",
                    command=["pytest", "-x", "--tb=short"],
                    max_retries=3,
                    timeout_seconds=300,
                    coverage_threshold=80,
                ),
                self.working_dir,
            ),
            SecurityGate(
                GateConfig(
                    name="security",
                    command=["bandit", "-r", ".", "-f", "json"],
                    max_retries=1,
                    timeout_seconds=120,
                    required=False,  # Advisory
                ),
                self.working_dir,
            ),
        ]
    
    async def run_all(self, state: RunState) -> tuple[bool, list[GateOutput]]:
        """
        Tüm kapıları sırayla çalıştır.
        
        Returns:
            (all_passed, outputs)
        """
        outputs: list[GateOutput] = []
        
        for gate in self.gates:
            output = await gate.run(state)
            outputs.append(output)
            
            if not output.success:
                # Aksiyon kontrolü
                if output.action == GateAction.BLOCKED:
                    state.status = TaskStatus.BLOCKED
                    return False, outputs
                
                elif output.action == GateAction.RETRY_AUTO_FIX:
                    fixed = await gate.auto_fix(state, output.stderr)
                    if fixed:
                        # Tekrar dene
                        retry_output = await gate.run(state)
                        outputs.append(retry_output)
                        if not retry_output.success:
                            return False, outputs
                    else:
                        return False, outputs
                
                elif output.action == GateAction.RETRY_MINIMAL:
                    # Minimal strateji gerekli - dışarıya bildir
                    return False, outputs
                
                else:
                    return False, outputs
        
        return True, outputs
    
    async def run_gate(self, gate_name: str, state: RunState) -> Optional[GateOutput]:
        """Tek bir kapıyı çalıştır"""
        for gate in self.gates:
            if gate.config.name == gate_name:
                return await gate.run(state)
        return None


# Factory function - convenience için
_default_pipeline: Optional[QualityGatePipeline] = None


def get_quality_pipeline(working_dir: Optional[Path] = None) -> QualityGatePipeline:
    """
    Kalite pipeline'ı factory fonksiyonu.
    
    Args:
        working_dir: Çalışma dizini (None ise mevcut dizin)
    
    Returns:
        QualityGatePipeline instance
    """
    global _default_pipeline
    
    if working_dir is not None:
        return QualityGatePipeline(working_dir)
    
    if _default_pipeline is None:
        _default_pipeline = QualityGatePipeline(Path.cwd())
    
    return _default_pipeline
