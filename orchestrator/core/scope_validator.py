"""
KIRO2 Scope Validator - Değişiklik Kapsamı Doğrulama
====================================================
"Doğru Kod" prensiplerine uygun değişiklik kapsamı kontrolü.

Kontrol Edilen Limitler:
- Dosya sayısı (max 5)
- Satır ekleme (max 50)
- Satır silme (max 30)
- Tek commit'e sığabilirlik
- Risk kategorisi değerlendirmesi
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ScopeViolationType(Enum):
    """Kapsam ihlali tipleri"""
    TOO_MANY_FILES = "too_many_files"
    TOO_MANY_LINES_ADDED = "too_many_lines_added"
    TOO_MANY_LINES_REMOVED = "too_many_lines_removed"
    HIGH_RISK_FILE = "high_risk_file"
    CROSS_BOUNDARY = "cross_boundary"  # Backend + Frontend aynı anda
    BREAKING_CHANGE = "breaking_change"
    NO_TESTS = "no_tests"
    CONFIG_CHANGE = "config_change"
    MIGRATION_REQUIRED = "migration_required"


class RiskCategory(Enum):
    """Risk kategorileri"""
    LOW = "low"           # Dokümantasyon, yorum
    MEDIUM = "medium"     # Normal kod değişikliği
    HIGH = "high"         # Auth, payment, database
    CRITICAL = "critical" # Security, core infrastructure


@dataclass
class ScopeLimits:
    """Kapsam limitleri - Doğru Kod prensibi"""
    max_files: int = 5
    max_lines_added: int = 50
    max_lines_removed: int = 30
    max_total_changes: int = 80
    allow_cross_boundary: bool = False
    require_tests: bool = True
    allow_config_changes: bool = True
    allow_migrations: bool = False  # Migrations ayrı PR olmalı


@dataclass
class FileChange:
    """Tek dosya değişikliği"""
    path: str
    lines_added: int = 0
    lines_removed: int = 0
    is_new: bool = False
    is_deleted: bool = False
    
    @property
    def total_changes(self) -> int:
        return self.lines_added + self.lines_removed
    
    @property
    def boundary(self) -> str:
        """Dosyanın hangi boundary'de olduğunu belirle"""
        path_lower = self.path.lower()
        if any(x in path_lower for x in ['frontend', 'src/components', 'src/pages', '.tsx', '.jsx', '.css']):
            return 'frontend'
        elif any(x in path_lower for x in ['backend', 'api', 'routers', 'services', 'models']):
            return 'backend'
        elif any(x in path_lower for x in ['test', 'spec', 'pytest', 'jest']):
            return 'test'
        elif any(x in path_lower for x in ['docker', 'ci', '.yml', '.yaml', 'config']):
            return 'infra'
        elif any(x in path_lower for x in ['docs', 'readme', '.md']):
            return 'docs'
        elif any(x in path_lower for x in ['migration', 'alembic']):
            return 'migration'
        return 'other'


@dataclass
class ScopeViolation:
    """Kapsam ihlali"""
    violation_type: ScopeViolationType
    severity: RiskCategory
    message: str
    details: dict = field(default_factory=dict)
    remediation: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "type": self.violation_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "remediation": self.remediation,
        }


@dataclass
class ScopeValidationResult:
    """Kapsam doğrulama sonucu"""
    valid: bool
    violations: list[ScopeViolation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_category: RiskCategory = RiskCategory.LOW
    can_auto_merge: bool = True
    requires_review: bool = False
    requires_approval: bool = False
    summary: str = ""
    
    # İstatistikler
    total_files: int = 0
    total_lines_added: int = 0
    total_lines_removed: int = 0
    boundaries_affected: set = field(default_factory=set)
    
    def add_violation(self, violation: ScopeViolation) -> None:
        self.violations.append(violation)
        self.valid = False
        # Risk kategorisini yükselt
        if violation.severity.value > self.risk_category.value:
            self.risk_category = violation.severity
    
    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


class ScopeValidator:
    """
    Değişiklik Kapsamı Doğrulayıcı
    
    "Doğru Kod" prensiplerine göre:
    - Küçük, odaklı değişiklikler
    - Tek bir amaca hizmet
    - Test edilebilir boyutta
    """
    
    # Yüksek riskli dosya patternleri
    HIGH_RISK_PATTERNS = [
        r'.*auth.*\.py$',
        r'.*security.*\.py$',
        r'.*payment.*\.py$',
        r'.*billing.*\.py$',
        r'.*password.*\.py$',
        r'.*token.*\.py$',
        r'.*credential.*\.py$',
        r'.*database.*\.py$',
        r'.*migration.*\.py$',
        r'.*\.env.*',
        r'.*secret.*',
        r'.*config/prod.*',
    ]
    
    # Kritik dosyalar (değişiklik onay gerektirir)
    CRITICAL_FILES = [
        'main.py',
        'settings.py',
        'config.py',
        'database.py',
        '__init__.py',  # Core modüllerde
        'requirements.txt',
        'package.json',
        'pyproject.toml',
    ]
    
    def __init__(self, limits: Optional[ScopeLimits] = None):
        self.limits = limits or ScopeLimits()
        self.validation_history: list[ScopeValidationResult] = []
        logger.info("ScopeValidator initialized")
    
    def validate(self, changes: list[FileChange]) -> ScopeValidationResult:
        """
        Değişiklikleri doğrula
        
        Args:
            changes: Dosya değişiklikleri listesi
            
        Returns:
            Doğrulama sonucu
        """
        result = ScopeValidationResult(valid=True)
        
        # İstatistikleri hesapla
        result.total_files = len(changes)
        result.total_lines_added = sum(c.lines_added for c in changes)
        result.total_lines_removed = sum(c.lines_removed for c in changes)
        result.boundaries_affected = set(c.boundary for c in changes)
        
        # Kontrolleri uygula
        self._check_file_count(changes, result)
        self._check_line_counts(changes, result)
        self._check_high_risk_files(changes, result)
        self._check_cross_boundary(changes, result)
        self._check_test_coverage(changes, result)
        self._check_config_changes(changes, result)
        self._check_migrations(changes, result)
        self._check_critical_files(changes, result)
        
        # Sonuç özetini oluştur
        result.summary = self._generate_summary(result)
        
        # Onay gereksinimlerini belirle
        self._determine_approval_requirements(result)
        
        # Geçmişe ekle
        self.validation_history.append(result)
        
        logger.info(f"Scope validation: valid={result.valid}, risk={result.risk_category.value}")
        return result
    
    def validate_diff(self, diff_text: str) -> ScopeValidationResult:
        """
        Git diff metninden değişiklikleri parse edip doğrula
        
        Args:
            diff_text: Git diff çıktısı
            
        Returns:
            Doğrulama sonucu
        """
        changes = self._parse_diff(diff_text)
        return self.validate(changes)
    
    def _check_file_count(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Dosya sayısı kontrolü"""
        if len(changes) > self.limits.max_files:
            result.add_violation(ScopeViolation(
                violation_type=ScopeViolationType.TOO_MANY_FILES,
                severity=RiskCategory.MEDIUM,
                message=f"Çok fazla dosya değişikliği: {len(changes)} > {self.limits.max_files}",
                details={"count": len(changes), "limit": self.limits.max_files},
                remediation="Değişiklikleri daha küçük commit'lere bölün"
            ))
    
    def _check_line_counts(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Satır sayısı kontrolü"""
        total_added = sum(c.lines_added for c in changes)
        total_removed = sum(c.lines_removed for c in changes)
        total_changes = total_added + total_removed
        
        if total_added > self.limits.max_lines_added:
            result.add_violation(ScopeViolation(
                violation_type=ScopeViolationType.TOO_MANY_LINES_ADDED,
                severity=RiskCategory.MEDIUM,
                message=f"Çok fazla satır eklendi: {total_added} > {self.limits.max_lines_added}",
                details={"count": total_added, "limit": self.limits.max_lines_added},
                remediation="Eklenen satırları azaltın veya commit'leri bölün"
            ))
        
        if total_removed > self.limits.max_lines_removed:
            result.add_violation(ScopeViolation(
                violation_type=ScopeViolationType.TOO_MANY_LINES_REMOVED,
                severity=RiskCategory.MEDIUM,
                message=f"Çok fazla satır silindi: {total_removed} > {self.limits.max_lines_removed}",
                details={"count": total_removed, "limit": self.limits.max_lines_removed},
                remediation="Silme işlemlerini ayrı bir refactoring PR'ında yapın"
            ))
        
        if total_changes > self.limits.max_total_changes:
            result.add_warning(
                f"Toplam değişiklik yüksek: {total_changes} satır (önerilen: {self.limits.max_total_changes})"
            )
    
    def _check_high_risk_files(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Yüksek riskli dosya kontrolü"""
        high_risk_files = []
        
        for change in changes:
            for pattern in self.HIGH_RISK_PATTERNS:
                if re.match(pattern, change.path, re.IGNORECASE):
                    high_risk_files.append(change.path)
                    break
        
        if high_risk_files:
            result.add_violation(ScopeViolation(
                violation_type=ScopeViolationType.HIGH_RISK_FILE,
                severity=RiskCategory.HIGH,
                message=f"Yüksek riskli dosyalar değiştirildi: {', '.join(high_risk_files)}",
                details={"files": high_risk_files},
                remediation="Bu dosyalar için senior review gerekli"
            ))
            result.requires_review = True
    
    def _check_cross_boundary(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Cross-boundary kontrolü (frontend + backend aynı anda)"""
        if not self.limits.allow_cross_boundary:
            boundaries = set(c.boundary for c in changes)
            
            if 'frontend' in boundaries and 'backend' in boundaries:
                result.add_violation(ScopeViolation(
                    violation_type=ScopeViolationType.CROSS_BOUNDARY,
                    severity=RiskCategory.MEDIUM,
                    message="Frontend ve backend değişiklikleri ayrı commit'lerde olmalı",
                    details={"boundaries": list(boundaries)},
                    remediation="Frontend ve backend değişikliklerini ayrı PR'lara bölün"
                ))
    
    def _check_test_coverage(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Test dosyası kontrolü"""
        if not self.limits.require_tests:
            return
        
        code_files = [c for c in changes if c.boundary in ('frontend', 'backend')]
        test_files = [c for c in changes if c.boundary == 'test']
        
        if code_files and not test_files:
            result.add_warning("Kod değişikliği var ama test yok. Test eklemeyi düşünün.")
    
    def _check_config_changes(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Config dosyası kontrolü"""
        config_files = [c for c in changes if c.boundary == 'infra']
        
        if config_files and not self.limits.allow_config_changes:
            result.add_violation(ScopeViolation(
                violation_type=ScopeViolationType.CONFIG_CHANGE,
                severity=RiskCategory.MEDIUM,
                message=f"Config değişiklikleri ayrı PR gerektirir: {[c.path for c in config_files]}",
                details={"files": [c.path for c in config_files]},
                remediation="Config değişikliklerini ayrı bir PR'a taşıyın"
            ))
    
    def _check_migrations(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Migration kontrolü"""
        migration_files = [c for c in changes if c.boundary == 'migration']
        
        if migration_files and not self.limits.allow_migrations:
            result.add_violation(ScopeViolation(
                violation_type=ScopeViolationType.MIGRATION_REQUIRED,
                severity=RiskCategory.HIGH,
                message="Migration değişiklikleri ayrı PR gerektirir",
                details={"files": [c.path for c in migration_files]},
                remediation="Migration'ları ayrı bir PR'da yapın ve staging'de test edin"
            ))
            result.requires_approval = True
    
    def _check_critical_files(self, changes: list[FileChange], result: ScopeValidationResult) -> None:
        """Kritik dosya kontrolü"""
        critical_changed = []
        
        for change in changes:
            filename = Path(change.path).name
            if filename in self.CRITICAL_FILES:
                critical_changed.append(change.path)
        
        if critical_changed:
            result.add_warning(f"Kritik dosyalar değişti: {', '.join(critical_changed)}")
            result.requires_review = True
    
    def _determine_approval_requirements(self, result: ScopeValidationResult) -> None:
        """Onay gereksinimlerini belirle"""
        if result.risk_category == RiskCategory.CRITICAL:
            result.requires_approval = True
            result.can_auto_merge = False
            result.requires_review = True
        elif result.risk_category == RiskCategory.HIGH:
            result.requires_review = True
            result.can_auto_merge = False
        elif result.violations:
            result.can_auto_merge = False
    
    def _generate_summary(self, result: ScopeValidationResult) -> str:
        """Özet oluştur"""
        status = "✅ GEÇER" if result.valid else "❌ BAŞARISIZ"
        
        lines = [
            f"Kapsam Doğrulama: {status}",
            f"Risk: {result.risk_category.value.upper()}",
            f"Dosya: {result.total_files}",
            f"Satır: +{result.total_lines_added} -{result.total_lines_removed}",
            f"Alanlar: {', '.join(result.boundaries_affected)}",
        ]
        
        if result.violations:
            lines.append(f"İhlal: {len(result.violations)}")
        if result.warnings:
            lines.append(f"Uyarı: {len(result.warnings)}")
        
        return " | ".join(lines)
    
    def _parse_diff(self, diff_text: str) -> list[FileChange]:
        """Git diff metnini parse et"""
        changes = []
        current_file = None
        lines_added = 0
        lines_removed = 0
        
        for line in diff_text.split('\n'):
            # Yeni dosya başlangıcı
            if line.startswith('diff --git'):
                # Önceki dosyayı kaydet
                if current_file:
                    changes.append(FileChange(
                        path=current_file,
                        lines_added=lines_added,
                        lines_removed=lines_removed
                    ))
                
                # Yeni dosyayı parse et
                match = re.search(r'diff --git a/(.*) b/(.*)', line)
                if match:
                    current_file = match.group(2)
                    lines_added = 0
                    lines_removed = 0
            
            elif line.startswith('+') and not line.startswith('+++'):
                lines_added += 1
            elif line.startswith('-') and not line.startswith('---'):
                lines_removed += 1
        
        # Son dosyayı kaydet
        if current_file:
            changes.append(FileChange(
                path=current_file,
                lines_added=lines_added,
                lines_removed=lines_removed
            ))
        
        return changes
    
    def get_stats(self) -> dict:
        """Doğrulama istatistikleri"""
        if not self.validation_history:
            return {"total": 0, "passed": 0, "failed": 0}
        
        total = len(self.validation_history)
        passed = sum(1 for r in self.validation_history if r.valid)
        
        violation_counts = {}
        for result in self.validation_history:
            for v in result.violations:
                vtype = v.violation_type.value
                violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "violation_breakdown": violation_counts,
        }


# Singleton instance
_scope_validator: Optional[ScopeValidator] = None


def get_scope_validator(limits: Optional[ScopeLimits] = None) -> ScopeValidator:
    """Singleton ScopeValidator instance"""
    global _scope_validator
    if _scope_validator is None:
        _scope_validator = ScopeValidator(limits)
    return _scope_validator
