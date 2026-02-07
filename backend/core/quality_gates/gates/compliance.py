"""
Compliance Gate
===============

Checks:
- GDPR compliance
- KVKK (Turkish GDPR) compliance
- SOC2 requirements
- PII handling (encryption, anonymization)
- Audit log completeness
- Data retention policy
- Consent management

Critical for educational platform with student data.
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

from ..models import (
    GateConfig,
    GateIssue,
    GateMetrics,
    GateResult,
    GateSeverity,
    GateStatus,
)
from .base import BaseGate, GateContext


logger = logging.getLogger(__name__)


# PII patterns to detect
PII_PATTERNS = [
    (r"tc_?kimlik|tckn|identity_number", "Turkish ID Number"),
    (r"email|e_?mail", "Email Address"),
    (r"phone|telefon|mobile|cep", "Phone Number"),
    (r"address|adres|sokak|cadde", "Physical Address"),
    (r"birth_?date|dogum_?tarihi|dob", "Birth Date"),
    (r"password|sifre|parola", "Password"),
    (r"credit_?card|kredi_?kart", "Credit Card"),
    (r"ip_?address|ip_?addr", "IP Address"),
    (r"student_?name|ogrenci_?adi", "Student Name"),
    (r"parent_?name|veli_?adi", "Parent Name"),
]


class ComplianceGate(BaseGate):
    """GDPR/KVKK compliance gate."""

    def get_name(self) -> str:
        return "compliance"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="compliance",
            enabled=True,
            blocking=True,
            threshold=7.0,
            warning_threshold=9.0,
            timeout_seconds=120,
            max_retries=1,
            depends_on=["security", "architecture"],
            tool_config={
                "gdpr_enabled": True,
                "kvkk_enabled": True,
                "soc2_enabled": False,
                "pii_encryption_required": True,
                "audit_logging_required": True,
                "consent_tracking_required": True,
                "data_retention_days": 365 * 3,  # 3 years for education
                "sensitive_fields": [
                    "tc_kimlik", "email", "phone", "password",
                    "student_name", "parent_name", "address",
                ],
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Execute compliance checks."""
        start_time = time.time()
        issues: list[GateIssue] = []
        scores: dict[str, float] = {}

        config = self.config.tool_config

        # 1. Check PII handling
        pii_result = await self._check_pii_handling(
            context.working_dir,
            config.get("pii_encryption_required", True),
        )
        scores["pii"] = pii_result.get("score", 5)
        issues.extend(pii_result.get("issues", []))

        # 2. Check audit logging
        if config.get("audit_logging_required", True):
            audit_result = await self._check_audit_logging(context.working_dir)
            scores["audit"] = audit_result.get("score", 5)
            issues.extend(audit_result.get("issues", []))

        # 3. Check consent management
        if config.get("consent_tracking_required", True):
            consent_result = await self._check_consent_management(context.working_dir)
            scores["consent"] = consent_result.get("score", 5)
            issues.extend(consent_result.get("issues", []))

        # 4. Check data retention
        retention_result = await self._check_data_retention(
            context.working_dir,
            config.get("data_retention_days", 365 * 3),
        )
        scores["retention"] = retention_result.get("score", 10)
        issues.extend(retention_result.get("issues", []))

        # 5. GDPR-specific checks
        if config.get("gdpr_enabled", True):
            gdpr_result = await self._check_gdpr_compliance(context.working_dir)
            scores["gdpr"] = gdpr_result.get("score", 5)
            issues.extend(gdpr_result.get("issues", []))

        # 6. KVKK-specific checks
        if config.get("kvkk_enabled", True):
            kvkk_result = await self._check_kvkk_compliance(context.working_dir)
            scores["kvkk"] = kvkk_result.get("score", 5)
            issues.extend(kvkk_result.get("issues", []))

        # Calculate final score
        if scores:
            final_score = sum(scores.values()) / len(scores)
        else:
            final_score = 5.0

        # Build metrics
        metrics = GateMetrics(
            gdpr_compliant=scores.get("gdpr", 0) >= 7,
            kvkk_compliant=scores.get("kvkk", 0) >= 7,
            audit_logs_complete=scores.get("audit", 0) >= 8,
            pii_encrypted=pii_result.get("encrypted", False),
        )

        status = self.determine_status(final_score)

        # Critical failures
        if any(i.severity == GateSeverity.CRITICAL for i in issues):
            status = GateStatus.FAIL

        execution_time_ms = (time.time() - start_time) * 1000
        message = self._build_message(scores, pii_result)

        return GateResult(
            gate_name=self.get_name(),
            status=status,
            score=round(final_score, 2),
            threshold=self.config.threshold,
            message=message,
            issues=issues,
            metrics=metrics,
            execution_time_ms=execution_time_ms,
            blocking=self.config.blocking,
        )

    async def _check_pii_handling(
        self,
        working_dir: Path,
        encryption_required: bool,
    ) -> dict:
        """Check PII handling practices."""
        issues: list[GateIssue] = []
        pii_fields_found: list[str] = []
        encrypted_count = 0
        unencrypted_count = 0

        # Scan models for PII fields
        model_dirs = ["models", "schemas", "database"]

        for model_dir in model_dirs:
            model_path = working_dir / model_dir
            if not model_path.exists():
                continue

            py_files = list(model_path.rglob("*.py"))

            for py_file in py_files[:30]:
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")

                    for pattern, pii_type in PII_PATTERNS:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            pii_fields_found.extend(matches)

                            # Check if field is encrypted/hashed
                            for match in matches[:5]:
                                # Look for encryption indicators
                                encrypted_patterns = [
                                    f"{match}.*encrypt",
                                    f"{match}.*hash",
                                    f"{match}.*cipher",
                                    f"encrypt.*{match}",
                                    f"Encrypted.*{match}",
                                ]
                                is_encrypted = any(
                                    re.search(p, content, re.IGNORECASE)
                                    for p in encrypted_patterns
                                )

                                if is_encrypted:
                                    encrypted_count += 1
                                else:
                                    unencrypted_count += 1
                                    if encryption_required:
                                        issues.append(
                                            self.create_issue(
                                                file=str(py_file.relative_to(working_dir)),
                                                rule="PII_UNENCRYPTED",
                                                message=f"PII field '{match}' ({pii_type}) may not be encrypted",
                                                severity=GateSeverity.HIGH,
                                                suggestion="Use encryption for sensitive data storage",
                                            )
                                        )
                except Exception:
                    continue

        total_pii = encrypted_count + unencrypted_count
        if total_pii > 0:
            encryption_rate = encrypted_count / total_pii
            score = encryption_rate * 10
        else:
            score = 10.0  # No PII found

        return {
            "score": round(score, 2),
            "issues": issues[:10],
            "pii_count": total_pii,
            "encrypted": encryption_rate >= 0.8 if total_pii > 0 else True,
        }

    async def _check_audit_logging(self, working_dir: Path) -> dict:
        """Check audit logging implementation."""
        issues: list[GateIssue] = []
        score = 10.0

        # Look for audit log models/handlers
        audit_patterns = [
            "audit_log",
            "auditlog",
            "activity_log",
            "user_activity",
        ]

        found_audit = False
        py_files = list(working_dir.rglob("*.py"))

        for py_file in py_files[:50]:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                if any(p in content for p in audit_patterns):
                    found_audit = True
                    break
            except Exception:
                continue

        if not found_audit:
            score -= 5
            issues.append(
                self.create_issue(
                    file=".",
                    rule="NO_AUDIT_LOG",
                    message="No audit logging implementation found",
                    severity=GateSeverity.HIGH,
                    suggestion="Implement audit logging for data access tracking",
                )
            )

        # Check for required audit fields
        required_fields = ["user_id", "action", "timestamp", "resource"]
        if found_audit:
            # Simple check - look for these fields in audit-related files
            audit_files = [f for f in py_files if "audit" in f.name.lower()]
            for audit_file in audit_files:
                try:
                    content = audit_file.read_text(encoding="utf-8", errors="ignore").lower()
                    missing = [f for f in required_fields if f not in content]
                    if missing:
                        score -= len(missing) * 0.5
                        issues.append(
                            self.create_issue(
                                file=str(audit_file.relative_to(working_dir)),
                                rule="INCOMPLETE_AUDIT",
                                message=f"Audit log missing fields: {', '.join(missing)}",
                                severity=GateSeverity.MEDIUM,
                            )
                        )
                except Exception:
                    continue

        return {
            "score": max(0, round(score, 2)),
            "issues": issues,
        }

    async def _check_consent_management(self, working_dir: Path) -> dict:
        """Check consent management implementation."""
        issues: list[GateIssue] = []
        score = 10.0

        consent_patterns = [
            "consent",
            "gdpr_consent",
            "kvkk_onay",
            "user_consent",
            "privacy_consent",
        ]

        found_consent = False
        py_files = list(working_dir.rglob("*.py"))

        for py_file in py_files[:50]:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                if any(p in content for p in consent_patterns):
                    found_consent = True
                    break
            except Exception:
                continue

        if not found_consent:
            score -= 4
            issues.append(
                self.create_issue(
                    file=".",
                    rule="NO_CONSENT_MANAGEMENT",
                    message="No consent management implementation found",
                    severity=GateSeverity.MEDIUM,
                    suggestion="Implement user consent tracking for GDPR/KVKK compliance",
                )
            )

        return {
            "score": max(0, round(score, 2)),
            "issues": issues,
        }

    async def _check_data_retention(
        self,
        working_dir: Path,
        max_retention_days: int,
    ) -> dict:
        """Check data retention policy implementation."""
        issues: list[GateIssue] = []
        score = 10.0

        retention_patterns = [
            "retention",
            "data_cleanup",
            "purge_old",
            "delete_expired",
            "data_deletion",
        ]

        found_retention = False
        py_files = list(working_dir.rglob("*.py"))

        for py_file in py_files[:50]:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                if any(p in content for p in retention_patterns):
                    found_retention = True
                    break
            except Exception:
                continue

        if not found_retention:
            score -= 3
            issues.append(
                self.create_issue(
                    file=".",
                    rule="NO_RETENTION_POLICY",
                    message="No data retention policy implementation found",
                    severity=GateSeverity.LOW,
                    suggestion=f"Implement data retention policy (max: {max_retention_days} days)",
                )
            )

        return {
            "score": max(0, round(score, 2)),
            "issues": issues,
        }

    async def _check_gdpr_compliance(self, working_dir: Path) -> dict:
        """Check GDPR-specific compliance."""
        issues: list[GateIssue] = []
        score = 10.0

        # GDPR rights that should be implemented
        gdpr_rights = {
            "right_to_access": ["data_export", "get_user_data", "export_data"],
            "right_to_erasure": ["delete_user", "anonymize", "forget_me", "data_deletion"],
            "right_to_portability": ["export", "download_data", "data_portability"],
        }

        py_files = list(working_dir.rglob("*.py"))
        all_content = ""

        for py_file in py_files[:100]:
            try:
                all_content += py_file.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                continue

        for right, patterns in gdpr_rights.items():
            found = any(p in all_content for p in patterns)
            if not found:
                score -= 2
                issues.append(
                    self.create_issue(
                        file=".",
                        rule=f"GDPR_{right.upper()}",
                        message=f"GDPR {right.replace('_', ' ')} not implemented",
                        severity=GateSeverity.MEDIUM,
                        suggestion=f"Implement {right.replace('_', ' ')} functionality",
                    )
                )

        return {
            "score": max(0, round(score, 2)),
            "issues": issues,
        }

    async def _check_kvkk_compliance(self, working_dir: Path) -> dict:
        """Check KVKK (Turkish GDPR) compliance."""
        issues: list[GateIssue] = []
        score = 10.0

        # KVKK-specific requirements
        kvkk_requirements = {
            "aydinlatma_metni": ["aydinlatma", "bilgilendirme", "privacy_notice"],
            "acik_riza": ["acik_riza", "explicit_consent", "kvkk_onay"],
            "veri_sorumlusu": ["veri_sorumlusu", "data_controller", "sicil"],
        }

        py_files = list(working_dir.rglob("*.py"))
        all_content = ""

        for py_file in py_files[:100]:
            try:
                all_content += py_file.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                continue

        for req, patterns in kvkk_requirements.items():
            found = any(p in all_content for p in patterns)
            if not found:
                score -= 1.5
                issues.append(
                    self.create_issue(
                        file=".",
                        rule=f"KVKK_{req.upper()}",
                        message=f"KVKK requirement '{req}' not found",
                        severity=GateSeverity.MEDIUM,
                        suggestion=f"Implement KVKK {req} requirement",
                    )
                )

        return {
            "score": max(0, round(score, 2)),
            "issues": issues,
        }

    def _build_message(self, scores: dict, pii_result: dict) -> str:
        """Build result message."""
        parts = []

        if "gdpr" in scores:
            status = "compliant" if scores["gdpr"] >= 7 else "non-compliant"
            parts.append(f"GDPR: {status}")

        if "kvkk" in scores:
            status = "compliant" if scores["kvkk"] >= 7 else "non-compliant"
            parts.append(f"KVKK: {status}")

        if "pii" in scores:
            encrypted = "yes" if pii_result.get("encrypted") else "no"
            parts.append(f"PII encrypted: {encrypted}")

        if "audit" in scores:
            status = "complete" if scores["audit"] >= 8 else "incomplete"
            parts.append(f"Audit: {status}")

        return " | ".join(parts) if parts else "Compliance checks completed"
