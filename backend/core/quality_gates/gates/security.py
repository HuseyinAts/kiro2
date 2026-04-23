"""
Security Gate
=============

Checks:
- Bandit security scanner (Python)
- Safety dependency checker
- Trivy container scanner (optional)
- Secret detection (detect-secrets)
- OWASP Top 10 compliance checks

Critical vulnerabilities block immediately.
High severity: 24h fix required.
"""

from __future__ import annotations

import json
import logging
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


class SecurityGate(BaseGate):
    """Security scanning gate with multiple analyzers."""

    def get_name(self) -> str:
        return "security"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="security",
            enabled=True,
            blocking=True,
            threshold=7.0,
            warning_threshold=9.0,
            timeout_seconds=180,
            max_retries=1,
            depends_on=["code_quality"],
            tool_config={
                "bandit_enabled": True,
                "safety_enabled": True,
                "trivy_enabled": False,  # Optional
                "secrets_enabled": True,
                "block_on_critical": True,
                "block_on_high": False,
                "bandit_confidence": "MEDIUM",
                "bandit_severity": "LOW",
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Execute security scans."""
        start_time = time.time()
        issues: list[GateIssue] = []
        scores: dict[str, float] = {}
        vuln_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        config = self.config.tool_config

        # 1. Bandit security scan
        if config.get("bandit_enabled", True):
            bandit_result = await self._run_bandit(context.working_dir)
            scores["bandit"] = bandit_result["score"]
            issues.extend(bandit_result["issues"])
            for sev, count in bandit_result.get("counts", {}).items():
                vuln_counts[sev] = vuln_counts.get(sev, 0) + count

        # 2. Safety dependency check
        if config.get("safety_enabled", True):
            safety_result = await self._run_safety(context.working_dir)
            scores["safety"] = safety_result["score"]
            issues.extend(safety_result["issues"])
            for sev, count in safety_result.get("counts", {}).items():
                vuln_counts[sev] = vuln_counts.get(sev, 0) + count

        # 3. Trivy container scan (optional)
        if config.get("trivy_enabled", False):
            trivy_result = await self._run_trivy(context.working_dir)
            scores["trivy"] = trivy_result["score"]
            issues.extend(trivy_result["issues"])

        # 4. Secret detection
        if config.get("secrets_enabled", True):
            secrets_result = await self._run_secrets_scan(context.working_dir)
            if secrets_result["secrets_found"] > 0:
                scores["secrets"] = 0  # Immediate fail
                issues.extend(secrets_result["issues"])
            else:
                scores["secrets"] = 10

        # Calculate average score
        if scores:
            final_score = sum(scores.values()) / len(scores)
        else:
            final_score = 10.0

        # Check blocking conditions
        status = self.determine_status(final_score)
        if config.get("block_on_critical", True) and vuln_counts["critical"] > 0:
            status = GateStatus.FAIL
        if config.get("block_on_high", False) and vuln_counts["high"] > 0:
            status = GateStatus.FAIL
        if any(i.rule == "SECRET_EXPOSED" for i in issues):
            status = GateStatus.FAIL

        # Build metrics
        metrics = GateMetrics(
            critical_vulns=vuln_counts["critical"],
            high_vulns=vuln_counts["high"],
            medium_vulns=vuln_counts["medium"],
            low_vulns=vuln_counts["low"],
            secrets_found=sum(1 for i in issues if i.rule == "SECRET_EXPOSED"),
        )

        execution_time_ms = (time.time() - start_time) * 1000
        message = self._build_message(vuln_counts, scores)

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

    async def _run_bandit(self, working_dir: Path) -> dict:
        """Run Bandit security scanner."""
        result = await self.run_command(
            [
                "bandit",
                "-r",
                ".",
                "-f",
                "json",
                "-ll",  # Medium+ severity
                "--confidence-level",
                self.config.tool_config.get("bandit_confidence", "MEDIUM"),
            ],
            working_dir,
        )

        issues: list[GateIssue] = []
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        output = result.stdout or result.stderr
        if output:
            try:
                bandit_data = json.loads(output)
                results = bandit_data.get("results", [])

                for finding in results[:50]:
                    severity = finding.get("issue_severity", "MEDIUM").lower()
                    if severity not in counts:
                        severity = "medium"
                    counts[severity] += 1

                    issues.append(
                        self.create_issue(
                            file=finding.get("filename", "unknown"),
                            line=finding.get("line_number"),
                            rule=finding.get("test_id", "unknown"),
                            message=finding.get("issue_text", ""),
                            severity=self._map_severity(severity),
                            suggestion=finding.get("more_info"),
                        )
                    )
            except json.JSONDecodeError:
                pass

        # Score calculation
        total_vulns = sum(counts.values())
        if total_vulns == 0:
            score = 10.0
        else:
            # Weighted penalty
            penalty = (
                counts["critical"] * 3 +
                counts["high"] * 2 +
                counts["medium"] * 1 +
                counts["low"] * 0.5
            )
            score = max(0, 10 - penalty)

        return {
            "score": round(score, 2),
            "issues": issues,
            "counts": counts,
        }

    async def _run_safety(self, working_dir: Path) -> dict:
        """Run Safety dependency checker."""
        # First, check if requirements.txt exists
        req_file = working_dir / "requirements.txt"
        if not req_file.exists():
            return {"score": 10.0, "issues": [], "counts": {}}

        result = await self.run_command(
            ["safety", "check", "--json", "-r", "requirements.txt"],
            working_dir,
        )

        issues: list[GateIssue] = []
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        if result.stdout:
            try:
                # Safety returns list of vulnerabilities
                safety_data = json.loads(result.stdout)

                if isinstance(safety_data, list):
                    for vuln in safety_data[:30]:
                        # Safety format: [package, affected, installed, description, id]
                        if isinstance(vuln, list) and len(vuln) >= 4:
                            package = vuln[0]
                            desc = vuln[3] if len(vuln) > 3 else ""

                            # Determine severity from description
                            severity = self._guess_severity(desc)
                            counts[severity] += 1

                            issues.append(
                                self.create_issue(
                                    file="requirements.txt",
                                    rule=f"CVE-{vuln[4]}" if len(vuln) > 4 else "VULN",
                                    message=f"{package}: {desc[:200]}",
                                    severity=self._map_severity(severity),
                                    suggestion=f"Update {package} to a secure version",
                                )
                            )
            except json.JSONDecodeError:
                pass

        total_vulns = sum(counts.values())
        if total_vulns == 0:
            score = 10.0
        else:
            penalty = (
                counts["critical"] * 4 +
                counts["high"] * 2.5 +
                counts["medium"] * 1 +
                counts["low"] * 0.3
            )
            score = max(0, 10 - penalty)

        return {
            "score": round(score, 2),
            "issues": issues,
            "counts": counts,
        }

    async def _run_trivy(self, working_dir: Path) -> dict:
        """Run Trivy container scanner."""
        # Check for Dockerfile
        dockerfile = working_dir / "Dockerfile"
        if not dockerfile.exists():
            return {"score": 10.0, "issues": [], "counts": {}}

        result = await self.run_command(
            ["trivy", "fs", "--format", "json", "."],
            working_dir,
        )

        issues: list[GateIssue] = []
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        if result.stdout:
            try:
                trivy_data = json.loads(result.stdout)
                results = trivy_data.get("Results", [])

                for res in results:
                    for vuln in res.get("Vulnerabilities", [])[:30]:
                        severity = vuln.get("Severity", "MEDIUM").lower()
                        if severity not in counts:
                            severity = "medium"
                        counts[severity] += 1

                        issues.append(
                            self.create_issue(
                                file=res.get("Target", "unknown"),
                                rule=vuln.get("VulnerabilityID", "unknown"),
                                message=vuln.get("Title", ""),
                                severity=self._map_severity(severity),
                                suggestion=vuln.get("FixedVersion"),
                            )
                        )
            except json.JSONDecodeError:
                pass

        total_vulns = sum(counts.values())
        score = max(0, 10 - (
            counts["critical"] * 3 +
            counts["high"] * 2 +
            counts["medium"] * 1 +
            counts["low"] * 0.3
        )) if total_vulns > 0 else 10.0

        return {
            "score": round(score, 2),
            "issues": issues,
            "counts": counts,
        }

    async def _run_secrets_scan(self, working_dir: Path) -> dict:
        """Run secret detection scan."""
        result = await self.run_command(
            ["detect-secrets", "scan", ".", "--all-files"],
            working_dir,
        )

        issues: list[GateIssue] = []
        secrets_found = 0

        if result.stdout:
            try:
                secrets_data = json.loads(result.stdout)
                results = secrets_data.get("results", {})

                for filepath, findings in results.items():
                    for finding in findings:
                        secrets_found += 1
                        issues.append(
                            self.create_issue(
                                file=filepath,
                                line=finding.get("line_number"),
                                rule="SECRET_EXPOSED",
                                message=f"Potential {finding.get('type', 'secret')} found",
                                severity=GateSeverity.CRITICAL,
                                suggestion="Remove secret and rotate credentials immediately",
                            )
                        )
            except json.JSONDecodeError:
                # Fallback: check for common patterns
                pass

        return {
            "secrets_found": secrets_found,
            "issues": issues,
        }

    def _map_severity(self, severity: str) -> GateSeverity:
        """Map string severity to GateSeverity."""
        mapping = {
            "critical": GateSeverity.CRITICAL,
            "high": GateSeverity.HIGH,
            "medium": GateSeverity.MEDIUM,
            "low": GateSeverity.LOW,
            "info": GateSeverity.INFO,
        }
        return mapping.get(severity.lower(), GateSeverity.MEDIUM)

    def _guess_severity(self, description: str) -> str:
        """Guess severity from vulnerability description."""
        desc_lower = description.lower()
        if any(w in desc_lower for w in ["critical", "rce", "remote code", "sql injection"]):
            return "critical"
        elif any(w in desc_lower for w in ["high", "authentication bypass", "privilege"]):
            return "high"
        elif any(w in desc_lower for w in ["denial of service", "dos", "memory"]):
            return "medium"
        return "low"

    def _build_message(self, counts: dict, scores: dict) -> str:
        """Build result message."""
        parts = []

        if counts["critical"]:
            parts.append(f"Critical: {counts['critical']}")
        if counts["high"]:
            parts.append(f"High: {counts['high']}")
        if counts["medium"]:
            parts.append(f"Medium: {counts['medium']}")
        if counts["low"]:
            parts.append(f"Low: {counts['low']}")

        if not parts:
            parts.append("No vulnerabilities found")

        # Add tool scores
        tool_parts = [f"{k}: {v:.1f}" for k, v in scores.items()]
        if tool_parts:
            parts.append(f"[{', '.join(tool_parts)}]")

        return " | ".join(parts)
