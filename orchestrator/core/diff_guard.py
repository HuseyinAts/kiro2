"""
KIRO2 Diff Guard - Yüksek Riskli Değişiklik Koruma Sistemi

7 yüksek riskli kategori için otomatik koruma ve 3 seviyeli sınıflandırma.
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Yüksek risk kategorileri"""
    AUTH = "authentication"  # Kimlik doğrulama
    PAYMENT = "payment"  # Ödeme işlemleri
    DATABASE = "database"  # Veritabanı işlemleri
    INFRASTRUCTURE = "infrastructure"  # Altyapı
    CONFIG = "configuration"  # Yapılandırma
    SECURITY = "security"  # Güvenlik
    CORE = "core"  # Çekirdek iş mantığı


class RiskLevel(Enum):
    """Risk seviyeleri"""
    LOW = 1  # Düşük risk - otomatik onay
    MEDIUM = 2  # Orta risk - dikkatli inceleme
    HIGH = 3  # Yüksek risk - zorunlu inceleme
    CRITICAL = 4  # Kritik - manuel onay gerekli


# Diff sınırları yapılandırması
DIFF_LIMITS = {
    "max_files_per_pr": 10,
    "max_lines_added": 500,
    "max_lines_removed": 200,
    "max_total_changes": 600,
    "require_review_threshold": 100,
    "require_approval_threshold": 300,
    "auto_reject_threshold": 1000,
}


@dataclass
class DiffAnalysis:
    """Diff analiz sonucu"""
    files_changed: list[str]
    lines_added: int
    lines_removed: int
    risk_level: RiskLevel
    risk_categories: list[RiskCategory]
    requires_review: bool
    requires_approval: bool
    warnings: list[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DiffLimits:
    """Risk seviyesine göre diff limitleri"""
    max_files: int
    max_lines_added: int
    max_lines_removed: int
    max_total_changes: int


class DiffGuard:
    """
    Diff Guard - Değişiklik Koruma Sistemi
    
    Özellikleri:
    - 7 yüksek riskli kategori tanıma
    - 3 seviyeli risk sınıflandırma
    - Otomatik diff boyut limitleri
    - Pattern-based tehdit algılama
    """
    
    # Kategori bazlı dosya pattern'leri
    RISK_PATTERNS: dict[RiskCategory, list[str]] = {
        RiskCategory.AUTH: [
            r".*auth.*\.py$",
            r".*login.*\.py$",
            r".*session.*\.py$",
            r".*jwt.*\.py$",
            r".*oauth.*\.py$",
            r".*password.*\.py$",
            r".*token.*\.py$",
            r".*/security/.*",
            r".*useAuth.*\.(ts|tsx)$",
            r".*authStore.*\.(ts|tsx)$",
        ],
        RiskCategory.PAYMENT: [
            r".*payment.*\.py$",
            r".*billing.*\.py$",
            r".*subscription.*\.py$",
            r".*invoice.*\.py$",
            r".*stripe.*\.py$",
            r".*checkout.*\.py$",
        ],
        RiskCategory.DATABASE: [
            r".*migration.*\.py$",
            r".*alembic.*",
            r".*models.*\.py$",
            r".*database.*\.py$",
            r".*schema.*\.py$",
            r".*\.sql$",
            r".*connection.*\.py$",
        ],
        RiskCategory.INFRASTRUCTURE: [
            r".*docker.*",
            r".*kubernetes.*",
            r".*terraform.*",
            r".*ansible.*",
            r".*\.ya?ml$",
            r".*nginx.*",
            r".*gunicorn.*",
            r".*uwsgi.*",
        ],
        RiskCategory.CONFIG: [
            r".*\.env.*",
            r".*config.*\.py$",
            r".*settings.*\.py$",
            r".*\.json$",
            r".*\.toml$",
            r".*requirements.*\.txt$",
            r".*package.*\.json$",
        ],
        RiskCategory.SECURITY: [
            r".*security.*\.py$",
            r".*crypto.*\.py$",
            r".*encrypt.*\.py$",
            r".*cors.*\.py$",
            r".*csrf.*\.py$",
            r".*permissions.*\.py$",
            r".*rbac.*\.py$",
        ],
        RiskCategory.CORE: [
            r".*main\.py$",
            r".*app\.py$",
            r".*core/.*\.py$",
            r".*/api/.*\.py$",
            r".*routers/.*\.py$",
            r".*services/.*\.py$",
        ],
    }
    
    # Risk seviyesine göre diff limitleri
    DIFF_LIMITS: dict[RiskLevel, DiffLimits] = {
        RiskLevel.LOW: DiffLimits(max_files=20, max_lines_added=500, max_lines_removed=300, max_total_changes=800),
        RiskLevel.MEDIUM: DiffLimits(max_files=10, max_lines_added=200, max_lines_removed=150, max_total_changes=350),
        RiskLevel.HIGH: DiffLimits(max_files=5, max_lines_added=50, max_lines_removed=30, max_total_changes=80),
        RiskLevel.CRITICAL: DiffLimits(max_files=2, max_lines_added=20, max_lines_removed=10, max_total_changes=30),
    }
    
    # Tehlikeli pattern'ler (içerik kontrolü)
    DANGEROUS_PATTERNS = [
        (r"DROP\s+TABLE", "SQL DROP TABLE detected"),
        (r"DELETE\s+FROM\s+\w+\s*;", "SQL DELETE without WHERE detected"),
        (r"TRUNCATE\s+TABLE", "SQL TRUNCATE detected"),
        (r"rm\s+-rf\s+/", "Dangerous rm -rf command detected"),
        (r"eval\s*\(", "eval() usage detected"),
        (r"exec\s*\(", "exec() usage detected"),
        (r"os\.system\s*\(", "os.system() usage detected"),
        (r"subprocess\.call.*shell\s*=\s*True", "Shell injection risk detected"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
        (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
        (r"secret[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"),
    ]
    
    def __init__(self):
        self._compiled_patterns: dict[RiskCategory, list[re.Pattern]] = {}
        self._compile_patterns()
        logger.info("DiffGuard initialized")
    
    def _compile_patterns(self):
        """Pattern'leri derle"""
        for category, patterns in self.RISK_PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def analyze_diff(
        self,
        files_changed: list[str],
        lines_added: int = 0,
        lines_removed: int = 0,
        diff_content: Optional[str] = None
    ) -> DiffAnalysis:
        """
        Diff analizi yap
        
        Args:
            files_changed: Değişen dosya listesi
            lines_added: Eklenen satır sayısı
            lines_removed: Silinen satır sayısı
            diff_content: Diff içeriği (opsiyonel, tehlike kontrolü için)
        
        Returns:
            DiffAnalysis sonucu
        """
        warnings = []
        risk_categories = []
        
        # 1. Dosya bazlı risk kategorisi tespiti
        for file_path in files_changed:
            for category, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    if pattern.match(file_path):
                        if category not in risk_categories:
                            risk_categories.append(category)
                        break
        
        # 2. Risk seviyesi belirleme
        risk_level = self._calculate_risk_level(risk_categories, lines_added, lines_removed)
        
        # 3. Tehlikeli pattern kontrolü
        blocked = False
        block_reason = None
        
        if diff_content:
            for pattern_str, warning_msg in self.DANGEROUS_PATTERNS:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                if pattern.search(diff_content):
                    warnings.append(warning_msg)
                    if "Hardcoded" in warning_msg or "DROP" in warning_msg or "rm -rf" in warning_msg:
                        blocked = True
                        block_reason = warning_msg
        
        # 4. Diff limitleri kontrolü
        limits = self.DIFF_LIMITS[risk_level]
        total_changes = lines_added + lines_removed
        
        if len(files_changed) > limits.max_files:
            warnings.append(f"Too many files changed: {len(files_changed)} > {limits.max_files}")
        
        if lines_added > limits.max_lines_added:
            warnings.append(f"Too many lines added: {lines_added} > {limits.max_lines_added}")
        
        if lines_removed > limits.max_lines_removed:
            warnings.append(f"Too many lines removed: {lines_removed} > {limits.max_lines_removed}")
        
        if total_changes > limits.max_total_changes:
            warnings.append(f"Total changes exceed limit: {total_changes} > {limits.max_total_changes}")
        
        # 5. İnceleme/onay gerekliliği
        requires_review = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) or len(warnings) > 0
        requires_approval = risk_level == RiskLevel.CRITICAL or blocked
        
        return DiffAnalysis(
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            risk_level=risk_level,
            risk_categories=risk_categories,
            requires_review=requires_review,
            requires_approval=requires_approval,
            warnings=warnings,
            blocked=blocked,
            block_reason=block_reason
        )
    
    def _calculate_risk_level(
        self,
        categories: list[RiskCategory],
        lines_added: int,
        lines_removed: int
    ) -> RiskLevel:
        """Risk seviyesi hesapla"""
        
        # Kritik kategoriler
        critical_categories = {RiskCategory.AUTH, RiskCategory.PAYMENT, RiskCategory.SECURITY}
        high_categories = {RiskCategory.DATABASE, RiskCategory.INFRASTRUCTURE}
        
        # Kategori bazlı risk
        category_risk = RiskLevel.LOW
        for cat in categories:
            if cat in critical_categories:
                category_risk = RiskLevel.CRITICAL
                break
            elif cat in high_categories:
                if category_risk.value < RiskLevel.HIGH.value:
                    category_risk = RiskLevel.HIGH
            elif category_risk.value < RiskLevel.MEDIUM.value:
                category_risk = RiskLevel.MEDIUM
        
        # Boyut bazlı risk
        total_changes = lines_added + lines_removed
        if total_changes > 500:
            size_risk = RiskLevel.HIGH
        elif total_changes > 200:
            size_risk = RiskLevel.MEDIUM
        else:
            size_risk = RiskLevel.LOW
        
        # En yüksek riski döndür
        return RiskLevel(max(category_risk.value, size_risk.value))
    
    def get_category_for_file(self, file_path: str) -> Optional[RiskCategory]:
        """Dosya için risk kategorisi döndür"""
        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(file_path):
                    return category
        return None
    
    def check_file_allowed(self, file_path: str, operation: str = "modify") -> tuple[bool, Optional[str]]:
        """
        Dosya işlemine izin verilip verilmediğini kontrol et
        
        Args:
            file_path: Dosya yolu
            operation: İşlem türü (modify, delete, create)
        
        Returns:
            (allowed, reason) - İzin durumu ve sebep
        """
        category = self.get_category_for_file(file_path)
        
        if category in (RiskCategory.AUTH, RiskCategory.PAYMENT):
            if operation == "delete":
                return False, f"Cannot delete {category.value} files without approval"
            return True, f"Caution: {category.value} file modification"
        
        if category == RiskCategory.DATABASE and operation == "delete":
            return False, "Cannot delete database files without approval"
        
        return True, None
    
    def suggest_decomposition(self, analysis: DiffAnalysis) -> list[dict]:
        """
        Büyük değişiklikleri parçalama önerisi
        
        Args:
            analysis: Diff analiz sonucu
        
        Returns:
            Parçalama önerileri listesi
        """
        suggestions = []
        
        if not analysis.requires_review:
            return suggestions
        
        # Kategori bazlı grupla
        category_files: dict[RiskCategory, list[str]] = {}
        for file_path in analysis.files_changed:
            cat = self.get_category_for_file(file_path)
            if cat:
                if cat not in category_files:
                    category_files[cat] = []
                category_files[cat].append(file_path)
        
        # Her kategori için ayrı PR öner
        for category, files in category_files.items():
            if len(files) > 0:
                suggestions.append({
                    "category": category.value,
                    "files": files,
                    "suggested_pr_title": f"[{category.value.upper()}] Update {len(files)} files",
                    "priority": "high" if category in (RiskCategory.AUTH, RiskCategory.PAYMENT) else "normal"
                })
        
        # Kategorisiz dosyalar
        uncategorized = [f for f in analysis.files_changed 
                        if not self.get_category_for_file(f)]
        if uncategorized:
            suggestions.append({
                "category": "general",
                "files": uncategorized,
                "suggested_pr_title": f"[GENERAL] Update {len(uncategorized)} files",
                "priority": "low"
            })
        
        return suggestions


# Singleton instance
_diff_guard: Optional[DiffGuard] = None


def get_diff_guard() -> DiffGuard:
    """Singleton DiffGuard erişimi"""
    global _diff_guard
    if _diff_guard is None:
        _diff_guard = DiffGuard()
    return _diff_guard


if __name__ == "__main__":
    # Test
    guard = get_diff_guard()
    
    # Test analizi
    test_files = [
        "backend/app/api/auth/login.py",
        "backend/app/models/user.py",
        "frontend/src/hooks/useAuth.ts",
        "backend/alembic/versions/001_initial.py"
    ]
    
    analysis = guard.analyze_diff(
        files_changed=test_files,
        lines_added=150,
        lines_removed=30
    )
    
    print(f"Risk Level: {analysis.risk_level.name}")
    print(f"Risk Categories: {[c.value for c in analysis.risk_categories]}")
    print(f"Requires Review: {analysis.requires_review}")
    print(f"Requires Approval: {analysis.requires_approval}")
    print(f"Warnings: {analysis.warnings}")
    
    # Decomposition önerileri
    suggestions = guard.suggest_decomposition(analysis)
    print(f"\nDecomposition Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"  - {s['suggested_pr_title']}: {len(s['files'])} files")
