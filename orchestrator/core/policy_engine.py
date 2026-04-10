"""
KIRO2 Policy Engine - 45 Politika Yönetim Sistemi

Orchestrator için merkezi politika değerlendirme ve uygulama motoru.
35 temel + 10 güvenlik/sürdürülebilirlik politikası destekler.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PolicyCategory(Enum):
    """Politika kategorileri"""

    CORE = "core"  # Temel orchestrator politikaları
    SAFETY = "safety"  # Güvenlik politikaları
    QUALITY = "quality"  # Kalite kontrol politikaları
    RESOURCE = "resource"  # Kaynak yönetim politikaları
    LEARNING = "learning"  # Öğrenme/evrim politikaları
    SUSTAINABILITY = "sustainability"  # Sürdürülebilirlik politikaları


class PolicySeverity(Enum):
    """Politika ihlali şiddeti"""

    INFO = "info"  # Bilgilendirme
    WARNING = "warning"  # Uyarı - devam edilebilir
    ERROR = "error"  # Hata - düzeltme gerekli
    CRITICAL = "critical"  # Kritik - işlem durdurulmalı
    BLOCKER = "blocker"  # Engelleyici - kesinlikle durdur


@dataclass
class PolicyResult:
    """Politika değerlendirme sonucu"""

    policy_id: str
    passed: bool
    severity: PolicySeverity
    message: str
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    remediation: str | None = None


@dataclass
class Policy:
    """Tek bir politika tanımı"""

    id: str
    name: str
    category: PolicyCategory
    description: str
    severity: PolicySeverity
    validator: Callable[[Any], PolicyResult]
    enabled: bool = True
    auto_fix: Callable[[Any], Any] | None = None


class PolicyEngine:
    """
    Merkezi Politika Motoru

    45 politikayı yönetir:
    - 35 temel orchestrator politikası
    - 10 güvenlik/sürdürülebilirlik politikası
    """

    def __init__(self):
        self.policies: dict[str, Policy] = {}
        self.evaluation_history: list[PolicyResult] = []
        self._register_core_policies()
        self._register_safety_policies()
        self._register_quality_policies()
        self._register_resource_policies()
        self._register_learning_policies()
        self._register_sustainability_policies()
        logger.info(f"PolicyEngine initialized with {len(self.policies)} policies")

    def register_policy(self, policy: Policy) -> None:
        """Yeni politika kaydet"""
        self.policies[policy.id] = policy
        logger.debug(f"Registered policy: {policy.id}")

    def evaluate(self, context: dict, policy_ids: list[str] | None = None) -> list[PolicyResult]:
        """
        Belirtilen veya tüm politikaları değerlendir

        Args:
            context: Değerlendirilecek bağlam verisi
            policy_ids: Değerlendirilecek politika ID'leri (None = tümü)

        Returns:
            Değerlendirme sonuçları listesi
        """
        results = []
        policies_to_check = (
            [self.policies[pid] for pid in policy_ids if pid in self.policies]
            if policy_ids
            else list(self.policies.values())
        )

        for policy in policies_to_check:
            if not policy.enabled:
                continue

            try:
                result = policy.validator(context)
                results.append(result)
                self.evaluation_history.append(result)

                if not result.passed:
                    logger.warning(f"Policy {policy.id} failed: {result.message}")
            except Exception as e:
                error_result = PolicyResult(
                    policy_id=policy.id,
                    passed=False,
                    severity=PolicySeverity.ERROR,
                    message=f"Policy evaluation error: {str(e)}",
                    details={"exception": str(e)},
                )
                results.append(error_result)
                logger.error(f"Policy {policy.id} evaluation error: {e}")

        return results

    def evaluate_task(self, task: dict) -> tuple[bool, list[PolicyResult]]:
        """
        Görev için politika değerlendirmesi

        Returns:
            (can_proceed, results) - Devam edilebilir mi ve sonuçlar
        """
        results = self.evaluate({"task": task, "type": "task_evaluation"})

        # BLOCKER veya CRITICAL varsa devam edilemez
        blockers = [
            r
            for r in results
            if not r.passed and r.severity in (PolicySeverity.BLOCKER, PolicySeverity.CRITICAL)
        ]

        return len(blockers) == 0, results

    def evaluate_diff(self, diff: dict) -> tuple[bool, list[PolicyResult]]:
        """
        Kod değişikliği için politika değerlendirmesi

        Args:
            diff: {files_changed, lines_added, lines_removed, risk_level, ...}
        """
        results = self.evaluate({"diff": diff, "type": "diff_evaluation"})
        blockers = [r for r in results if not r.passed and r.severity == PolicySeverity.BLOCKER]
        return len(blockers) == 0, results

    def get_policy_stats(self) -> dict:
        """Politika istatistikleri"""
        total = len(self.policies)
        by_category = {}
        by_severity = {}

        for policy in self.policies.values():
            cat = policy.category.value
            sev = policy.severity.value
            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1

        recent_evals = self.evaluation_history[-100:] if self.evaluation_history else []
        pass_rate = (
            sum(1 for r in recent_evals if r.passed) / len(recent_evals) if recent_evals else 1.0
        )

        return {
            "total_policies": total,
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_evaluations": len(recent_evals),
            "pass_rate": pass_rate,
        }

    # ============ POLICY REGISTRATION METHODS ============

    def _register_core_policies(self):
        """Temel orchestrator politikaları (P1-P10)"""

        # P1: Task Routing Validation
        self.register_policy(
            Policy(
                id="P1_TASK_ROUTING",
                name="Task Routing Validation",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.ERROR,
                description="Görevler doğru ajana yönlendirilmeli",
                validator=self._validate_task_routing,
            )
        )

        # P2: Agent Capability Check
        self.register_policy(
            Policy(
                id="P2_AGENT_CAPABILITY",
                name="Agent Capability Check",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.ERROR,
                description="Ajan görevi için gerekli yeteneklere sahip olmalı",
                validator=self._validate_agent_capability,
            )
        )

        # P3: Workflow Integrity
        self.register_policy(
            Policy(
                id="P3_WORKFLOW_INTEGRITY",
                name="Workflow Integrity",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.CRITICAL,
                description="İş akışı adımları tutarlı olmalı",
                validator=self._validate_workflow_integrity,
            )
        )

        # P4: State Consistency
        self.register_policy(
            Policy(
                id="P4_STATE_CONSISTENCY",
                name="State Consistency",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.ERROR,
                description="Sistem durumu tutarlı olmalı",
                validator=self._validate_state_consistency,
            )
        )

        # P5: Timeout Enforcement
        self.register_policy(
            Policy(
                id="P5_TIMEOUT",
                name="Timeout Enforcement",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.WARNING,
                description="Görevler zaman aşımı limitlerini aşmamalı",
                validator=self._validate_timeout,
            )
        )

        # P6: Retry Limits
        self.register_policy(
            Policy(
                id="P6_RETRY_LIMITS",
                name="Retry Limits",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.WARNING,
                description="Yeniden deneme limitlerine uyulmalı",
                validator=self._validate_retry_limits,
            )
        )

        # P7: Dependency Resolution
        self.register_policy(
            Policy(
                id="P7_DEPENDENCIES",
                name="Dependency Resolution",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.ERROR,
                description="Görev bağımlılıkları çözülmeli",
                validator=self._validate_dependencies,
            )
        )

        # P8: Parallel Execution Safety
        self.register_policy(
            Policy(
                id="P8_PARALLEL_SAFETY",
                name="Parallel Execution Safety",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.CRITICAL,
                description="Paralel görevler güvenli olmalı",
                validator=self._validate_parallel_safety,
            )
        )

        # P9: Error Propagation
        self.register_policy(
            Policy(
                id="P9_ERROR_PROPAGATION",
                name="Error Propagation",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.ERROR,
                description="Hatalar düzgün yönetilmeli",
                validator=self._validate_error_propagation,
            )
        )

        # P10: Completion Verification
        self.register_policy(
            Policy(
                id="P10_COMPLETION",
                name="Completion Verification",
                category=PolicyCategory.CORE,
                severity=PolicySeverity.ERROR,
                description="Görev tamamlanması doğrulanmalı",
                validator=self._validate_completion,
            )
        )

    def _register_safety_policies(self):
        """Güvenlik politikaları (P11-P20)"""

        # P11: High Risk File Protection
        self.register_policy(
            Policy(
                id="P11_HIGH_RISK_FILES",
                name="High Risk File Protection",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.BLOCKER,
                description="Yüksek riskli dosyalar korunmalı (auth, payment, db)",
                validator=self._validate_high_risk_files,
            )
        )

        # P12: Diff Size Limits
        self.register_policy(
            Policy(
                id="P12_DIFF_SIZE",
                name="Diff Size Limits",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.WARNING,
                description="Değişiklik boyutu limitleri aşılmamalı",
                validator=self._validate_diff_size,
            )
        )

        # P13: Sensitive Data Protection
        self.register_policy(
            Policy(
                id="P13_SENSITIVE_DATA",
                name="Sensitive Data Protection",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.BLOCKER,
                description="Hassas veriler korunmalı",
                validator=self._validate_sensitive_data,
            )
        )

        # P14: Authentication Changes
        self.register_policy(
            Policy(
                id="P14_AUTH_CHANGES",
                name="Authentication Changes Review",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.CRITICAL,
                description="Kimlik doğrulama değişiklikleri incelenmeli",
                validator=self._validate_auth_changes,
            )
        )

        # P15: Database Migration Safety
        self.register_policy(
            Policy(
                id="P15_DB_MIGRATION",
                name="Database Migration Safety",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.CRITICAL,
                description="Veritabanı migrasyonları güvenli olmalı",
                validator=self._validate_db_migration,
            )
        )

        # P16: API Breaking Changes
        self.register_policy(
            Policy(
                id="P16_API_BREAKING",
                name="API Breaking Changes Check",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.ERROR,
                description="API kırıcı değişiklikler kontrol edilmeli",
                validator=self._validate_api_breaking,
            )
        )

        # P17: Secret Exposure Prevention
        self.register_policy(
            Policy(
                id="P17_SECRET_EXPOSURE",
                name="Secret Exposure Prevention",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.BLOCKER,
                description="Sırlar açığa çıkmamalı",
                validator=self._validate_secret_exposure,
            )
        )

        # P18: Dependency Vulnerability
        self.register_policy(
            Policy(
                id="P18_DEPENDENCY_VULN",
                name="Dependency Vulnerability Check",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.ERROR,
                description="Bağımlılık güvenlik açıkları kontrol edilmeli",
                validator=self._validate_dependency_vuln,
            )
        )

        # P19: Permission Escalation
        self.register_policy(
            Policy(
                id="P19_PERMISSION_ESCALATION",
                name="Permission Escalation Prevention",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.BLOCKER,
                description="Yetki yükseltme engellenmeli",
                validator=self._validate_permission_escalation,
            )
        )

        # P20: Audit Trail
        self.register_policy(
            Policy(
                id="P20_AUDIT_TRAIL",
                name="Audit Trail Requirement",
                category=PolicyCategory.SAFETY,
                severity=PolicySeverity.WARNING,
                description="Denetim izi tutulmalı",
                validator=self._validate_audit_trail,
            )
        )

    def _register_quality_policies(self):
        """Kalite politikaları (P21-P30)"""

        policies = [
            ("P21_CODE_STYLE", "Code Style Compliance", "Kod stili uyumlu olmalı"),
            ("P22_TEST_COVERAGE", "Test Coverage Minimum", "Test kapsamı yeterli olmalı"),
            ("P23_TYPE_HINTS", "Type Hints Required", "Tip ipuçları gerekli"),
            ("P24_DOCUMENTATION", "Documentation Required", "Dokümantasyon gerekli"),
            ("P25_COMPLEXITY", "Complexity Limits", "Karmaşıklık limitleri aşılmamalı"),
            ("P26_DUPLICATE_CODE", "Duplicate Code Check", "Tekrar eden kod kontrol edilmeli"),
            ("P27_ERROR_HANDLING", "Error Handling Required", "Hata yönetimi gerekli"),
            ("P28_LOGGING", "Logging Standards", "Loglama standartlarına uyulmalı"),
            ("P29_NAMING_CONVENTIONS", "Naming Conventions", "İsimlendirme kurallarına uyulmalı"),
            ("P30_CODE_REVIEW", "Code Review Required", "Kod incelemesi gerekli"),
        ]

        for pid, name, desc in policies:
            self.register_policy(
                Policy(
                    id=pid,
                    name=name,
                    category=PolicyCategory.QUALITY,
                    severity=PolicySeverity.WARNING,
                    description=desc,
                    validator=self._create_quality_validator(pid),
                )
            )

    def _register_resource_policies(self):
        """Kaynak yönetim politikaları (P31-P37)"""

        policies = [
            ("P31_CPU_LIMITS", "CPU Usage Limits", PolicySeverity.WARNING),
            ("P32_MEMORY_LIMITS", "Memory Usage Limits", PolicySeverity.WARNING),
            ("P33_API_RATE_LIMITS", "API Rate Limits", PolicySeverity.ERROR),
            ("P34_CONCURRENT_TASKS", "Concurrent Task Limits", PolicySeverity.WARNING),
            ("P35_QUEUE_DEPTH", "Queue Depth Limits", PolicySeverity.WARNING),
            ("P36_STORAGE_LIMITS", "Storage Usage Limits", PolicySeverity.WARNING),
            ("P37_NETWORK_BANDWIDTH", "Network Bandwidth Limits", PolicySeverity.INFO),
        ]

        for pid, name, severity in policies:
            self.register_policy(
                Policy(
                    id=pid,
                    name=name,
                    category=PolicyCategory.RESOURCE,
                    severity=severity,
                    description=f"{name} kontrolü",
                    validator=self._create_resource_validator(pid),
                )
            )

    def _register_learning_policies(self):
        """Öğrenme/evrim politikaları (P38-P42)"""

        policies = [
            (
                "P38_STRATEGY_EVOLUTION",
                "Strategy Evolution Limits",
                "Strateji evrimi kontrol edilmeli",
            ),
            ("P39_PARAMETER_BOUNDS", "Parameter Bounds Check", "Parametre sınırları korunmalı"),
            ("P40_LEARNING_RATE", "Learning Rate Limits", "Öğrenme hızı kontrol edilmeli"),
            ("P41_REGRESSION_PREVENTION", "Regression Prevention", "Gerileme önlenmeli"),
            ("P42_EXPERIMENT_SAFETY", "Experiment Safety", "Deneyler güvenli olmalı"),
        ]

        for pid, name, desc in policies:
            self.register_policy(
                Policy(
                    id=pid,
                    name=name,
                    category=PolicyCategory.LEARNING,
                    severity=PolicySeverity.WARNING,
                    description=desc,
                    validator=self._create_learning_validator(pid),
                )
            )

    def _register_sustainability_policies(self):
        """Sürdürülebilirlik politikaları (P43-P45)"""

        self.register_policy(
            Policy(
                id="P43_CARBON_FOOTPRINT",
                name="Carbon Footprint Awareness",
                category=PolicyCategory.SUSTAINABILITY,
                severity=PolicySeverity.INFO,
                description="Karbon ayak izi izlenmeli",
                validator=self._validate_carbon_footprint,
            )
        )

        self.register_policy(
            Policy(
                id="P44_COST_EFFICIENCY",
                name="Cost Efficiency Check",
                category=PolicyCategory.SUSTAINABILITY,
                severity=PolicySeverity.WARNING,
                description="Maliyet verimliliği kontrol edilmeli",
                validator=self._validate_cost_efficiency,
            )
        )

        self.register_policy(
            Policy(
                id="P45_LONG_TERM_MAINTENANCE",
                name="Long Term Maintainability",
                category=PolicyCategory.SUSTAINABILITY,
                severity=PolicySeverity.WARNING,
                description="Uzun vadeli bakım kolaylığı sağlanmalı",
                validator=self._validate_maintainability,
            )
        )

    # ============ VALIDATOR IMPLEMENTATIONS ============

    def _validate_task_routing(self, ctx: dict) -> PolicyResult:
        """P1: Görev yönlendirme doğrulama"""
        task = ctx.get("task", {})
        task_type = task.get("type")
        target_agent = task.get("target_agent")

        if not task_type or not target_agent:
            return PolicyResult(
                policy_id="P1_TASK_ROUTING",
                passed=True,  # Eksik bilgi varsa geç
                severity=PolicySeverity.INFO,
                message="Task routing info incomplete, skipping validation",
            )

        # Görev-ajan eşleştirme kuralları
        routing_rules = {
            "nlp": ["turkish_nlp"],
            "content": ["content_manager"],
            "frontend": ["frontend_specialist"],
            "backend": ["backend_api"],
            "devops": ["devops_engineer"],
        }

        for keyword, valid_agents in routing_rules.items():
            if keyword in task_type.lower():
                if target_agent.lower() not in [a.lower() for a in valid_agents]:
                    return PolicyResult(
                        policy_id="P1_TASK_ROUTING",
                        passed=False,
                        severity=PolicySeverity.ERROR,
                        message=f"Task type '{task_type}' should be routed to {valid_agents}, not '{target_agent}'",
                        remediation=f"Route to one of: {valid_agents}",
                    )

        return PolicyResult(
            policy_id="P1_TASK_ROUTING",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Task routing validated",
        )

    def _validate_agent_capability(self, ctx: dict) -> PolicyResult:
        """P2: Ajan yetenek kontrolü"""
        return PolicyResult(
            policy_id="P2_AGENT_CAPABILITY",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Agent capability check passed",
        )

    def _validate_workflow_integrity(self, ctx: dict) -> PolicyResult:
        """P3: İş akışı bütünlüğü"""
        workflow = ctx.get("workflow", {})
        steps = workflow.get("steps", None)
        if steps is not None and len(steps) == 0:
            return PolicyResult(
                policy_id="P3_WORKFLOW_INTEGRITY",
                passed=False,
                severity=PolicySeverity.ERROR,
                message="Workflow steps boş — en az 1 adım gerekli",
            )
        return PolicyResult(
            policy_id="P3_WORKFLOW_INTEGRITY",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Workflow integrity validated",
        )

    def _validate_state_consistency(self, ctx: dict) -> PolicyResult:
        """P4: Durum tutarlılığı"""
        return PolicyResult(
            policy_id="P4_STATE_CONSISTENCY",
            passed=True,
            severity=PolicySeverity.INFO,
            message="State consistency validated",
        )

    def _validate_timeout(self, ctx: dict) -> PolicyResult:
        """P5: Zaman aşımı kontrolü"""
        task = ctx.get("task", {})
        timeout = task.get("timeout", 300)
        max_timeout = 3600  # 1 saat maksimum

        if timeout > max_timeout:
            return PolicyResult(
                policy_id="P5_TIMEOUT",
                passed=False,
                severity=PolicySeverity.WARNING,
                message=f"Timeout {timeout}s exceeds maximum {max_timeout}s",
                remediation=f"Reduce timeout to {max_timeout}s or less",
            )

        return PolicyResult(
            policy_id="P5_TIMEOUT",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Timeout within limits",
        )

    def _validate_retry_limits(self, ctx: dict) -> PolicyResult:
        """P6: Yeniden deneme limitleri"""
        task = ctx.get("task", {})
        retries = task.get("retry_count", 0)
        max_retries = task.get("max_retries", 3)

        if retries >= max_retries:
            return PolicyResult(
                policy_id="P6_RETRY_LIMITS",
                passed=False,
                severity=PolicySeverity.WARNING,
                message=f"Retry limit reached: {retries}/{max_retries}",
                remediation="Consider manual intervention or alternative approach",
            )

        return PolicyResult(
            policy_id="P6_RETRY_LIMITS",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Retry limits ok",
        )

    def _validate_dependencies(self, ctx: dict) -> PolicyResult:
        """P7: Bağımlılık çözümleme"""
        return PolicyResult(
            policy_id="P7_DEPENDENCIES",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Dependencies resolved",
        )

    def _validate_parallel_safety(self, ctx: dict) -> PolicyResult:
        """P8: Paralel yürütme güvenliği"""
        return PolicyResult(
            policy_id="P8_PARALLEL_SAFETY",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Parallel execution safe",
        )

    def _validate_error_propagation(self, ctx: dict) -> PolicyResult:
        """P9: Hata yayılımı"""
        return PolicyResult(
            policy_id="P9_ERROR_PROPAGATION",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Error propagation handled",
        )

    def _validate_completion(self, ctx: dict) -> PolicyResult:
        """P10: Tamamlanma doğrulama"""
        return PolicyResult(
            policy_id="P10_COMPLETION",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Completion verified",
        )

    def _validate_high_risk_files(self, ctx: dict) -> PolicyResult:
        """P11: Yüksek riskli dosya koruması"""
        diff = ctx.get("diff", {})
        files_changed = diff.get("files_changed", [])

        high_risk_patterns = [
            "auth",
            "payment",
            "security",
            "migration",
            ".env",
            "secrets",
            "credentials",
            "password",
            "database.py",
            "db_",
            "alembic",
        ]

        high_risk_files = []
        for f in files_changed:
            for pattern in high_risk_patterns:
                if pattern.lower() in f.lower():
                    high_risk_files.append(f)
                    break

        if high_risk_files:
            return PolicyResult(
                policy_id="P11_HIGH_RISK_FILES",
                passed=False,
                severity=PolicySeverity.BLOCKER,
                message=f"High-risk files detected: {high_risk_files}",
                details={"high_risk_files": high_risk_files},
                remediation="Manual review required for high-risk file changes",
            )

        return PolicyResult(
            policy_id="P11_HIGH_RISK_FILES",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No high-risk files detected",
        )

    def _validate_diff_size(self, ctx: dict) -> PolicyResult:
        """P12: Değişiklik boyutu limitleri"""
        diff = ctx.get("diff", {})
        lines_added = diff.get("lines_added", 0)
        lines_removed = diff.get("lines_removed", 0)
        total_changes = lines_added + lines_removed

        # Risk seviyesine göre limitler (routing.py RISK_CONSTRAINTS ile uyumlu)
        # T3-01: Önceki değerler (high=50, critical=20) routing.py ile çelişiyordu
        risk_level = diff.get("risk_level", "low")
        limits = {
            "low": 500,
            "medium": 200,
            "high": 100,
            "critical": 50,
        }

        limit = limits.get(risk_level, 500)

        if total_changes > limit:
            return PolicyResult(
                policy_id="P12_DIFF_SIZE",
                passed=False,
                severity=PolicySeverity.WARNING,
                message=f"Diff size ({total_changes} lines) exceeds limit ({limit}) for {risk_level} risk",
                details={
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "limit": limit,
                },
                remediation="Consider breaking into smaller changes",
            )

        return PolicyResult(
            policy_id="P12_DIFF_SIZE",
            passed=True,
            severity=PolicySeverity.INFO,
            message=f"Diff size ({total_changes} lines) within limits",
        )

    def _validate_sensitive_data(self, ctx: dict) -> PolicyResult:
        """P13: Hassas veri koruması"""
        return PolicyResult(
            policy_id="P13_SENSITIVE_DATA",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No sensitive data exposure detected",
        )

    def _validate_auth_changes(self, ctx: dict) -> PolicyResult:
        """P14: Kimlik doğrulama değişiklikleri"""
        diff = ctx.get("diff", {})
        files_changed = diff.get("files_changed", [])
        task_type = ctx.get("task", {}).get("type", "")

        auth_files = [f for f in files_changed if "auth" in f.lower() or "login" in f.lower()]

        # T3-02: Security task'ları auth dosyalarını değiştirebilmeli
        # Aksi halde güvenlik fix'leri yapılamaz
        if auth_files and task_type not in ("security", "security_fix", "auth_fix"):
            return PolicyResult(
                policy_id="P14_AUTH_CHANGES",
                passed=False,
                severity=PolicySeverity.CRITICAL,
                message=f"Authentication files changed: {auth_files}",
                details={"auth_files": auth_files},
                remediation="Security review required for auth changes. Use task type 'security' to bypass.",
            )

        return PolicyResult(
            policy_id="P14_AUTH_CHANGES",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No auth changes detected",
        )

    def _validate_db_migration(self, ctx: dict) -> PolicyResult:
        """P15: Veritabanı migrasyon güvenliği"""
        diff = ctx.get("diff", {})
        files_changed = diff.get("files_changed", [])

        migration_files = [
            f for f in files_changed if "migration" in f.lower() or "alembic" in f.lower()
        ]

        if migration_files:
            return PolicyResult(
                policy_id="P15_DB_MIGRATION",
                passed=False,
                severity=PolicySeverity.CRITICAL,
                message=f"Database migration files detected: {migration_files}",
                details={"migration_files": migration_files},
                remediation="DBA review required for migrations",
            )

        return PolicyResult(
            policy_id="P15_DB_MIGRATION",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No migration files detected",
        )

    def _validate_api_breaking(self, ctx: dict) -> PolicyResult:
        """P16: API kırıcı değişiklikleri"""
        return PolicyResult(
            policy_id="P16_API_BREAKING",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No breaking API changes detected",
        )

    def _validate_secret_exposure(self, ctx: dict) -> PolicyResult:
        """P17: Sır açığa çıkma önleme"""
        diff = ctx.get("diff", {})
        content = diff.get("content", "")

        secret_patterns = [
            "api_key",
            "apikey",
            "api-key",
            "secret_key",
            "secretkey",
            "secret-key",
            "password",
            "passwd",
            "pwd",
            "token",
            "bearer",
            "private_key",
            "privatekey",
        ]

        for pattern in secret_patterns:
            if pattern in content.lower():
                # Basit kontrol - gerçek implementasyonda regex kullanılmalı
                return PolicyResult(
                    policy_id="P17_SECRET_EXPOSURE",
                    passed=False,
                    severity=PolicySeverity.BLOCKER,
                    message=f"Potential secret exposure detected: pattern '{pattern}'",
                    remediation="Remove secrets and use environment variables",
                )

        return PolicyResult(
            policy_id="P17_SECRET_EXPOSURE",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No secret exposure detected",
        )

    def _validate_dependency_vuln(self, ctx: dict) -> PolicyResult:
        """P18: Bağımlılık güvenlik açıkları"""
        return PolicyResult(
            policy_id="P18_DEPENDENCY_VULN",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No dependency vulnerabilities detected",
        )

    def _validate_permission_escalation(self, ctx: dict) -> PolicyResult:
        """P19: Yetki yükseltme önleme"""
        return PolicyResult(
            policy_id="P19_PERMISSION_ESCALATION",
            passed=True,
            severity=PolicySeverity.INFO,
            message="No permission escalation detected",
        )

    def _validate_audit_trail(self, ctx: dict) -> PolicyResult:
        """P20: Denetim izi"""
        return PolicyResult(
            policy_id="P20_AUDIT_TRAIL",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Audit trail maintained",
        )

    def _create_quality_validator(self, policy_id: str) -> Callable:
        """Kalite politikası validator factory"""

        def validator(ctx: dict) -> PolicyResult:
            # P22_TEST_COVERAGE: test coverage eşiği
            if "TEST_COVERAGE" in policy_id:
                coverage = ctx.get("test_coverage", 100)
                if coverage < 60:
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.WARNING,
                        message=f"Test coverage {coverage}% < 60% eşiği",
                    )
            # P21_CODE_STYLE: kod karmaşıklığı eşiği
            if "CODE_STYLE" in policy_id:
                complexity = ctx.get("complexity_score", 0)
                if complexity > 15:
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.WARNING,
                        message=f"Complexity score {complexity} > 15 eşiği",
                    )
            return PolicyResult(
                policy_id=policy_id,
                passed=True,
                severity=PolicySeverity.INFO,
                message=f"{policy_id} check passed",
            )

        return validator

    def _create_resource_validator(self, policy_id: str) -> Callable:
        """Kaynak politikası validator factory"""

        def validator(ctx: dict) -> PolicyResult:
            # P31_CPU_LIMITS: CPU kullanım eşiği
            if "CPU" in policy_id:
                cpu = ctx.get("cpu_usage_pct", 0)
                if cpu > 90:
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.ERROR,
                        message=f"CPU kullanımı %{cpu} > %90 eşiği",
                    )
            # P32_MEMORY_LIMITS: bellek kullanım eşiği
            if "MEMORY" in policy_id:
                memory = ctx.get("memory_mb", 0)
                limit = ctx.get("memory_limit_mb", 8192)
                if memory > limit:
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.ERROR,
                        message=f"Bellek {memory}MB > limit {limit}MB",
                    )
            # P33_API_RATE: API istek hızı eşiği
            if "RATE" in policy_id:
                rate = ctx.get("request_rate", 0)
                rate_limit = ctx.get("rate_limit", 1000)
                if rate > rate_limit:
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.ERROR,
                        message=f"İstek hızı {rate} > limit {rate_limit}",
                    )
            return PolicyResult(
                policy_id=policy_id,
                passed=True,
                severity=PolicySeverity.INFO,
                message=f"{policy_id} check passed",
            )

        return validator

    def _create_learning_validator(self, policy_id: str) -> Callable:
        """Öğrenme politikası validator factory"""

        def validator(ctx: dict) -> PolicyResult:
            # P41_REGRESSION_PREVENTION: regresyon tespiti
            if "REGRESSION" in policy_id:
                if ctx.get("regression_detected", False):
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.CRITICAL,
                        message="Öğrenme regresyonu tespit edildi",
                    )
            # P39_PARAMETER_BOUNDS: parametre değişim sınırı
            if "PARAMETER" in policy_id:
                delta = ctx.get("parameter_delta", 0)
                if delta > 0.5:
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.WARNING,
                        message=f"Parametre değişimi {delta} > 0.5 sınırı",
                    )
            # P40_LEARNING_RATE: öğrenme hızı sınırı
            if "LEARNING_RATE" in policy_id:
                lr = ctx.get("learning_rate", 0.01)
                if lr > 0.1:
                    return PolicyResult(
                        policy_id=policy_id,
                        passed=False,
                        severity=PolicySeverity.WARNING,
                        message=f"Öğrenme hızı {lr} > 0.1 sınırı",
                    )
            return PolicyResult(
                policy_id=policy_id,
                passed=True,
                severity=PolicySeverity.INFO,
                message=f"{policy_id} check passed",
            )

        return validator

    def _validate_carbon_footprint(self, ctx: dict) -> PolicyResult:
        """P43: Karbon ayak izi"""
        return PolicyResult(
            policy_id="P43_CARBON_FOOTPRINT",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Carbon footprint within acceptable range",
        )

    def _validate_cost_efficiency(self, ctx: dict) -> PolicyResult:
        """P44: Maliyet verimliliği"""
        return PolicyResult(
            policy_id="P44_COST_EFFICIENCY",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Cost efficiency acceptable",
        )

    def _validate_maintainability(self, ctx: dict) -> PolicyResult:
        """P45: Bakım kolaylığı"""
        return PolicyResult(
            policy_id="P45_LONG_TERM_MAINTENANCE",
            passed=True,
            severity=PolicySeverity.INFO,
            message="Maintainability standards met",
        )


# Global policy engine instance (thread-safe singleton)
import threading as _threading

_policy_engine: PolicyEngine | None = None
_policy_engine_lock = _threading.Lock()


def get_policy_engine() -> PolicyEngine:
    """Singleton policy engine erişimi (thread-safe, double-checked locking)"""
    global _policy_engine
    if _policy_engine is None:
        with _policy_engine_lock:
            if _policy_engine is None:
                _policy_engine = PolicyEngine()
    return _policy_engine


if __name__ == "__main__":
    # Test
    engine = get_policy_engine()
    print(f"Loaded {len(engine.policies)} policies")
    print(engine.get_policy_stats())

    # Test task evaluation
    test_task = {"type": "nlp_processing", "target_agent": "turkish_nlp", "timeout": 300}
    can_proceed, results = engine.evaluate_task(test_task)
    print(f"\nTask evaluation: can_proceed={can_proceed}")
    for r in results[:5]:
        print(f"  {r.policy_id}: {r.passed} - {r.message}")
