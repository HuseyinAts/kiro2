#!/usr/bin/env python3
"""
OWASP Top 10 Security Vulnerability Scanner
KIRO2 Platform Security Audit - Task 143.1

Bu script OWASP Top 10 2021 guvenlik aciklarini test eder:
A01:2021 - Broken Access Control
A02:2021 - Cryptographic Failures
A03:2021 - Injection
A04:2021 - Insecure Design
A05:2021 - Security Misconfiguration
A06:2021 - Vulnerable and Outdated Components
A07:2021 - Identification and Authentication Failures
A08:2021 - Software and Data Integrity Failures
A09:2021 - Security Logging and Monitoring Failures
A10:2021 - Server-Side Request Forgery (SSRF)
"""

import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class VulnerabilityStatus(Enum):
    VULNERABLE = "VULNERABLE"
    SECURE = "SECURE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NOT_APPLICABLE = "N/A"


@dataclass
class Finding:
    """Security finding representation"""
    vulnerability_id: str
    title: str
    severity: Severity
    status: VulnerabilityStatus
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str = ""
    evidence: str = ""


@dataclass
class AuditReport:
    """Complete security audit report"""
    scan_date: str = field(default_factory=lambda: datetime.now().isoformat())
    scanner_version: str = "1.0.0"
    target: str = "KIRO2 Backend"
    findings: list[Finding] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    def generate_summary(self) -> dict:
        self.summary = {
            "total_findings": len(self.findings),
            "critical": len([f for f in self.findings if f.severity == Severity.CRITICAL]),
            "high": len([f for f in self.findings if f.severity == Severity.HIGH]),
            "medium": len([f for f in self.findings if f.severity == Severity.MEDIUM]),
            "low": len([f for f in self.findings if f.severity == Severity.LOW]),
            "info": len([f for f in self.findings if f.severity == Severity.INFO]),
            "vulnerable": len([f for f in self.findings if f.status == VulnerabilityStatus.VULNERABLE]),
            "secure": len([f for f in self.findings if f.status == VulnerabilityStatus.SECURE]),
            "needs_review": len([f for f in self.findings if f.status == VulnerabilityStatus.NEEDS_REVIEW]),
        }
        return self.summary


class OWASPTop10Scanner:
    """OWASP Top 10 2021 Security Scanner"""

    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.report = AuditReport()

    async def run_full_scan(self) -> AuditReport:
        """Run complete OWASP Top 10 scan"""
        print("[SECURITY] KIRO2 OWASP Top 10 Security Audit Started")
        print("=" * 60)

        await self.scan_a01_broken_access_control()
        await self.scan_a02_cryptographic_failures()
        await self.scan_a03_injection()
        await self.scan_a04_insecure_design()
        await self.scan_a05_security_misconfiguration()
        await self.scan_a06_vulnerable_components()
        await self.scan_a07_authentication_failures()
        await self.scan_a08_data_integrity_failures()
        await self.scan_a09_logging_failures()
        await self.scan_a10_ssrf()

        self.report.generate_summary()
        return self.report

    async def scan_a01_broken_access_control(self) -> None:
        """A01:2021 - Broken Access Control"""
        print("\n[A01] Broken Access Control Scan...")

        api_files = list(self.backend_path.glob("api/*.py"))
        missing_auth_endpoints = []

        auth_patterns = [
            r"Depends\(.*get_current_user",
            r"Depends\(.*require_auth",
            r"Depends\(.*get_admin",
            r"@require_auth",
            r"@admin_required",
        ]

        for api_file in api_files:
            content = api_file.read_text(encoding="utf-8", errors="ignore")
            routes = re.findall(
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                content,
            )

            for method, path in routes:
                if any(skip in path for skip in ["/health", "/status", "/docs", "/openapi", "/test"]):
                    continue
                has_auth = any(re.search(pattern, content) for pattern in auth_patterns)
                if not has_auth and "public" not in path.lower():
                    missing_auth_endpoints.append(f"{api_file.name}: {method.upper()} {path}")

        if missing_auth_endpoints:
            self.report.add_finding(Finding(
                vulnerability_id="A01-001",
                title="Endpoints Without Authentication Check",
                severity=Severity.HIGH,
                status=VulnerabilityStatus.NEEDS_REVIEW,
                description=f"Found {len(missing_auth_endpoints)} endpoints that may lack authentication",
                recommendation="Review and add appropriate authentication to all sensitive endpoints",
                evidence="\n".join(missing_auth_endpoints[:10]),
            ))
        else:
            self.report.add_finding(Finding(
                vulnerability_id="A01-001",
                title="Authentication Check Coverage",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description="All API endpoints appear to have authentication checks",
                recommendation="Continue monitoring for new endpoints",
            ))

        rbac_file = self.backend_path / "core" / "rbac_system.py"
        if rbac_file.exists():
            content = rbac_file.read_text(encoding="utf-8", errors="ignore")
            if "check_permission" in content and "Role" in content:
                self.report.add_finding(Finding(
                    vulnerability_id="A01-002",
                    title="RBAC System Implementation",
                    severity=Severity.INFO,
                    status=VulnerabilityStatus.SECURE,
                    description="RBAC system is implemented with role-based permissions",
                    file_path=str(rbac_file),
                ))
            else:
                self.report.add_finding(Finding(
                    vulnerability_id="A01-002",
                    title="RBAC System Incomplete",
                    severity=Severity.MEDIUM,
                    status=VulnerabilityStatus.NEEDS_REVIEW,
                    description="RBAC system may be incomplete",
                    file_path=str(rbac_file),
                    recommendation="Ensure complete RBAC implementation with proper permission checks",
                ))

        print("  [OK] A01 scan complete")

    async def scan_a02_cryptographic_failures(self) -> None:
        """A02:2021 - Cryptographic Failures"""
        print("\n[A02] Cryptographic Failures Scan...")

        weak_hash_patterns = [
            (r"md5\s*\(", "MD5 hash usage detected", Severity.HIGH),
            (r"sha1\s*\(", "SHA1 hash usage detected", Severity.MEDIUM),
            (r"hashlib\.md5", "MD5 hashlib usage", Severity.HIGH),
            (r"hashlib\.sha1", "SHA1 hashlib usage", Severity.MEDIUM),
        ]

        python_files = list(self.backend_path.rglob("*.py"))

        for pattern, desc, severity in weak_hash_patterns:
            for py_file in python_files:
                if "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(pattern, content):
                        self.report.add_finding(Finding(
                            vulnerability_id="A02-001",
                            title="Weak Cryptographic Algorithm",
                            severity=severity,
                            status=VulnerabilityStatus.VULNERABLE,
                            description=desc,
                            file_path=str(py_file),
                            recommendation="Use SHA-256 or stronger algorithms",
                        ))
                except Exception:
                    pass

        secret_patterns = [
            (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded password"),
            (r'(?:api_key|apikey|api-key)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key"),
            (r'(?:secret|token)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret/token"),
            (r'(?:sk-|pk_live_|pk_test_)[a-zA-Z0-9]{20,}', "Exposed API key pattern"),
        ]

        for pattern, desc in secret_patterns:
            for py_file in python_files:
                if "test" in str(py_file).lower() or "example" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        if not any(x in content for x in ["os.environ", "os.getenv", "settings."]):
                            self.report.add_finding(Finding(
                                vulnerability_id="A02-002",
                                title="Potential Hardcoded Secret",
                                severity=Severity.CRITICAL,
                                status=VulnerabilityStatus.NEEDS_REVIEW,
                                description=desc,
                                file_path=str(py_file),
                                recommendation="Use environment variables or secret management",
                                evidence=str(matches[:2]),
                            ))
                except Exception:
                    pass

        config_file = self.backend_path / "core" / "config.py"
        if config_file.exists():
            content = config_file.read_text(encoding="utf-8", errors="ignore")
            if "SSL" in content or "TLS" in content or "HTTPS" in content:
                self.report.add_finding(Finding(
                    vulnerability_id="A02-003",
                    title="TLS/SSL Configuration Present",
                    severity=Severity.INFO,
                    status=VulnerabilityStatus.SECURE,
                    description="TLS/SSL configuration found in settings",
                    file_path=str(config_file),
                ))

        print("  [OK] A02 scan complete")

    async def scan_a03_injection(self) -> None:
        """A03:2021 - Injection (SQL, Command, etc.)"""
        print("\n[A03] Injection Vulnerabilities Scan...")

        python_files = list(self.backend_path.rglob("*.py"))

        sql_injection_patterns = [
            (r'execute\s*\(\s*f["\']', "f-string in SQL execute"),
            (r'execute\s*\(\s*["\'].*%s.*%\s*\(', "String formatting in SQL"),
            (r'\.format\s*\(.*\).*execute', "format() before execute"),
            (r'cursor\.execute\s*\(\s*[^,]+\+', "String concatenation in SQL"),
        ]

        for pattern, desc in sql_injection_patterns:
            for py_file in python_files:
                if "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(pattern, content):
                        self.report.add_finding(Finding(
                            vulnerability_id="A03-001",
                            title="Potential SQL Injection",
                            severity=Severity.CRITICAL,
                            status=VulnerabilityStatus.NEEDS_REVIEW,
                            description=desc,
                            file_path=str(py_file),
                            recommendation="Use parameterized queries with SQLAlchemy ORM",
                        ))
                except Exception:
                    pass

        cmd_patterns = [
            (r'os\.system\s*\(', "os.system usage"),
            (r'subprocess\.call\s*\([^,]+shell\s*=\s*True', "subprocess with shell=True"),
            (r'subprocess\.run\s*\([^,]+shell\s*=\s*True', "subprocess.run with shell=True"),
            (r'eval\s*\(', "eval() usage"),
            (r'exec\s*\(', "exec() usage"),
        ]

        for pattern, desc in cmd_patterns:
            for py_file in python_files:
                if "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(pattern, content):
                        self.report.add_finding(Finding(
                            vulnerability_id="A03-002",
                            title="Potential Command Injection",
                            severity=Severity.HIGH,
                            status=VulnerabilityStatus.NEEDS_REVIEW,
                            description=desc,
                            file_path=str(py_file),
                            recommendation="Avoid shell=True and use subprocess with argument lists",
                        ))
                except Exception:
                    pass

        sql_security = self.backend_path / "core" / "sql_injection_prevention.py"
        if sql_security.exists():
            self.report.add_finding(Finding(
                vulnerability_id="A03-003",
                title="SQL Injection Prevention Module",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description="SQL injection prevention module is implemented",
                file_path=str(sql_security),
            ))

        print("  [OK] A03 scan complete")

    async def scan_a04_insecure_design(self) -> None:
        """A04:2021 - Insecure Design"""
        print("\n[A04] Insecure Design Scan...")

        rate_limit_files = list(self.backend_path.glob("core/*rate*.py"))
        if rate_limit_files:
            self.report.add_finding(Finding(
                vulnerability_id="A04-001",
                title="Rate Limiting Implementation",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description="Rate limiting is implemented",
                file_path=str(rate_limit_files[0]),
            ))
        else:
            self.report.add_finding(Finding(
                vulnerability_id="A04-001",
                title="Missing Rate Limiting",
                severity=Severity.MEDIUM,
                status=VulnerabilityStatus.VULNERABLE,
                description="No rate limiting implementation found",
                recommendation="Implement rate limiting to prevent abuse",
            ))

        api_files = list(self.backend_path.glob("api/*.py"))
        pydantic_usage = 0

        for api_file in api_files:
            content = api_file.read_text(encoding="utf-8", errors="ignore")
            if "BaseModel" in content or "pydantic" in content:
                pydantic_usage += 1

        if pydantic_usage > len(api_files) * 0.5:
            self.report.add_finding(Finding(
                vulnerability_id="A04-002",
                title="Input Validation with Pydantic",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description=f"Pydantic validation found in {pydantic_usage}/{len(api_files)} API files",
            ))
        else:
            self.report.add_finding(Finding(
                vulnerability_id="A04-002",
                title="Insufficient Input Validation",
                severity=Severity.MEDIUM,
                status=VulnerabilityStatus.NEEDS_REVIEW,
                description="Some API files may lack proper input validation",
                recommendation="Use Pydantic models for all API inputs",
            ))

        print("  [OK] A04 scan complete")

    async def scan_a05_security_misconfiguration(self) -> None:
        """A05:2021 - Security Misconfiguration"""
        print("\n[A05] Security Misconfiguration Scan...")

        config_file = self.backend_path / "core" / "config.py"
        if config_file.exists():
            content = config_file.read_text(encoding="utf-8", errors="ignore")

            if re.search(r'DEBUG\s*[=:]\s*True', content):
                self.report.add_finding(Finding(
                    vulnerability_id="A05-001",
                    title="DEBUG Mode Enabled",
                    severity=Severity.HIGH,
                    status=VulnerabilityStatus.NEEDS_REVIEW,
                    description="DEBUG mode appears to be enabled in config",
                    file_path=str(config_file),
                    recommendation="Ensure DEBUG is False in production",
                ))
            elif re.search(r'DEBUG.*os\.environ|os\.getenv.*DEBUG', content, re.IGNORECASE):
                self.report.add_finding(Finding(
                    vulnerability_id="A05-001",
                    title="DEBUG Mode Configured via Environment",
                    severity=Severity.INFO,
                    status=VulnerabilityStatus.SECURE,
                    description="DEBUG mode is controlled by environment variable",
                    file_path=str(config_file),
                ))

        cors_patterns = [
            (r'allow_origins\s*=\s*\[\s*["\']?\*["\']?\s*\]', "CORS allows all origins"),
            (r'Access-Control-Allow-Origin.*\*', "CORS header allows all origins"),
        ]

        main_file = self.backend_path / "main.py"
        if main_file.exists():
            content = main_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in cors_patterns:
                if re.search(pattern, content):
                    self.report.add_finding(Finding(
                        vulnerability_id="A05-002",
                        title="Overly Permissive CORS",
                        severity=Severity.MEDIUM,
                        status=VulnerabilityStatus.NEEDS_REVIEW,
                        description=desc,
                        file_path=str(main_file),
                        recommendation="Restrict CORS to specific trusted origins",
                    ))

        security_headers = self.backend_path / "core" / "security_headers.py"
        if security_headers.exists():
            content = security_headers.read_text(encoding="utf-8", errors="ignore")
            required_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy",
            ]
            missing_headers = [h for h in required_headers if h not in content]
            if missing_headers:
                self.report.add_finding(Finding(
                    vulnerability_id="A05-003",
                    title="Missing Security Headers",
                    severity=Severity.MEDIUM,
                    status=VulnerabilityStatus.NEEDS_REVIEW,
                    description=f"Missing headers: {', '.join(missing_headers)}",
                    file_path=str(security_headers),
                    recommendation="Add all recommended security headers",
                ))
            else:
                self.report.add_finding(Finding(
                    vulnerability_id="A05-003",
                    title="Security Headers Configured",
                    severity=Severity.INFO,
                    status=VulnerabilityStatus.SECURE,
                    description="All recommended security headers are configured",
                    file_path=str(security_headers),
                ))

        print("  [OK] A05 scan complete")

    async def scan_a06_vulnerable_components(self) -> None:
        """A06:2021 - Vulnerable and Outdated Components"""
        print("\n[A06] Vulnerable Components Scan...")

        requirements_file = self.backend_path / "requirements.txt"
        if requirements_file.exists():
            content = requirements_file.read_text(encoding="utf-8", errors="ignore")

            unpinned = re.findall(r'^([a-zA-Z0-9_-]+)\s*$', content, re.MULTILINE)
            if unpinned:
                self.report.add_finding(Finding(
                    vulnerability_id="A06-001",
                    title="Unpinned Dependencies",
                    severity=Severity.MEDIUM,
                    status=VulnerabilityStatus.NEEDS_REVIEW,
                    description=f"Found {len(unpinned)} unpinned dependencies",
                    file_path=str(requirements_file),
                    recommendation="Pin all dependencies to specific versions",
                    evidence=", ".join(unpinned[:10]),
                ))

            vulnerable_packages = {
                "pyyaml<5.4": "CVE-2020-14343",
                "urllib3<1.26.5": "CVE-2021-33503",
                "pillow<8.3.2": "CVE-2021-23437",
                "django<3.2.4": "CVE-2021-33571",
            }

            for pkg_pattern, cve in vulnerable_packages.items():
                pkg_name = pkg_pattern.split("<")[0]
                if pkg_name.lower() in content.lower():
                    self.report.add_finding(Finding(
                        vulnerability_id="A06-002",
                        title="Potentially Vulnerable Package",
                        severity=Severity.HIGH,
                        status=VulnerabilityStatus.NEEDS_REVIEW,
                        description=f"Package {pkg_name} found - check for {cve}",
                        file_path=str(requirements_file),
                        recommendation="Run 'pip-audit' or 'safety check' for detailed CVE scan",
                    ))

        self.report.add_finding(Finding(
            vulnerability_id="A06-003",
            title="Dependency Audit Recommendation",
            severity=Severity.INFO,
            status=VulnerabilityStatus.NEEDS_REVIEW,
            description="Run 'pip-audit' for comprehensive vulnerability scan",
            recommendation="pip install pip-audit && pip-audit",
        ))

        print("  [OK] A06 scan complete")

    async def scan_a07_authentication_failures(self) -> None:
        """A07:2021 - Identification and Authentication Failures"""
        print("\n[A07] Authentication Failures Scan...")

        jwt_file = self.backend_path / "core" / "jwt_auth.py"
        if jwt_file.exists():
            content = jwt_file.read_text(encoding="utf-8", errors="ignore")

            if "HS256" in content and "RS256" not in content:
                self.report.add_finding(Finding(
                    vulnerability_id="A07-001",
                    title="JWT Using Symmetric Algorithm",
                    severity=Severity.MEDIUM,
                    status=VulnerabilityStatus.NEEDS_REVIEW,
                    description="JWT uses HS256 symmetric algorithm",
                    file_path=str(jwt_file),
                    recommendation="Consider using RS256 asymmetric algorithm for better security",
                ))

            if "exp" in content or "expire" in content.lower():
                self.report.add_finding(Finding(
                    vulnerability_id="A07-002",
                    title="JWT Expiration Configured",
                    severity=Severity.INFO,
                    status=VulnerabilityStatus.SECURE,
                    description="JWT token expiration is configured",
                    file_path=str(jwt_file),
                ))
            else:
                self.report.add_finding(Finding(
                    vulnerability_id="A07-002",
                    title="JWT Expiration Not Found",
                    severity=Severity.HIGH,
                    status=VulnerabilityStatus.NEEDS_REVIEW,
                    description="JWT token expiration configuration not found",
                    file_path=str(jwt_file),
                    recommendation="Implement JWT token expiration",
                ))

        auth_files = list(self.backend_path.glob("core/*auth*.py"))
        secure_hash_found = False

        for auth_file in auth_files:
            content = auth_file.read_text(encoding="utf-8", errors="ignore")
            if any(h in content for h in ["bcrypt", "argon2", "pbkdf2", "passlib"]):
                secure_hash_found = True
                self.report.add_finding(Finding(
                    vulnerability_id="A07-003",
                    title="Secure Password Hashing",
                    severity=Severity.INFO,
                    status=VulnerabilityStatus.SECURE,
                    description="Secure password hashing algorithm found",
                    file_path=str(auth_file),
                ))
                break

        if not secure_hash_found:
            self.report.add_finding(Finding(
                vulnerability_id="A07-003",
                title="Password Hashing Not Verified",
                severity=Severity.HIGH,
                status=VulnerabilityStatus.NEEDS_REVIEW,
                description="Could not verify secure password hashing",
                recommendation="Use bcrypt, argon2, or PBKDF2 for password hashing",
            ))

        twofa_file = self.backend_path / "core" / "two_factor_auth.py"
        if twofa_file.exists():
            self.report.add_finding(Finding(
                vulnerability_id="A07-004",
                title="Two-Factor Authentication",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description="2FA implementation found",
                file_path=str(twofa_file),
            ))

        print("  [OK] A07 scan complete")

    async def scan_a08_data_integrity_failures(self) -> None:
        """A08:2021 - Software and Data Integrity Failures"""
        print("\n[A08] Data Integrity Failures Scan...")

        python_files = list(self.backend_path.rglob("*.py"))

        unsafe_patterns = [
            (r'pickle\.loads?\s*\(', "Unsafe pickle usage"),
            (r'yaml\.load\s*\([^,]+\)', "Unsafe YAML load (no Loader)"),
            (r'marshal\.loads?\s*\(', "Unsafe marshal usage"),
        ]

        for pattern, desc in unsafe_patterns:
            for py_file in python_files:
                if "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(pattern, content):
                        self.report.add_finding(Finding(
                            vulnerability_id="A08-001",
                            title="Unsafe Deserialization",
                            severity=Severity.HIGH,
                            status=VulnerabilityStatus.NEEDS_REVIEW,
                            description=desc,
                            file_path=str(py_file),
                            recommendation="Use safe alternatives (json, yaml.safe_load)",
                        ))
                except Exception:
                    pass

        self.report.add_finding(Finding(
            vulnerability_id="A08-002",
            title="Data Integrity Verification",
            severity=Severity.INFO,
            status=VulnerabilityStatus.NEEDS_REVIEW,
            description="Manual review needed for data integrity checks",
            recommendation="Ensure checksums/signatures for critical data transfers",
        ))

        print("  [OK] A08 scan complete")

    async def scan_a09_logging_failures(self) -> None:
        """A09:2021 - Security Logging and Monitoring Failures"""
        print("\n[A09] Logging Failures Scan...")

        audit_files = list(self.backend_path.glob("core/*audit*.py"))
        if audit_files:
            self.report.add_finding(Finding(
                vulnerability_id="A09-001",
                title="Audit Logging Implementation",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description=f"Found {len(audit_files)} audit logging module(s)",
                file_path=str(audit_files[0]),
            ))
        else:
            self.report.add_finding(Finding(
                vulnerability_id="A09-001",
                title="Missing Audit Logging",
                severity=Severity.MEDIUM,
                status=VulnerabilityStatus.VULNERABLE,
                description="No dedicated audit logging found",
                recommendation="Implement security event logging",
            ))

        logger_file = self.backend_path / "core" / "structured_logger.py"
        if logger_file.exists():
            self.report.add_finding(Finding(
                vulnerability_id="A09-002",
                title="Structured Logging",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description="Structured logging is implemented",
                file_path=str(logger_file),
            ))

        python_files = list(self.backend_path.rglob("*.py"))
        sensitive_log_patterns = [
            (r'log.*password', "Password in log"),
            (r'log.*token', "Token in log"),
            (r'log.*secret', "Secret in log"),
            (r'print\s*\(.*password', "Password in print"),
        ]

        for pattern, desc in sensitive_log_patterns:
            for py_file in python_files:
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(pattern, content, re.IGNORECASE):
                        self.report.add_finding(Finding(
                            vulnerability_id="A09-003",
                            title="Potential Sensitive Data Logging",
                            severity=Severity.MEDIUM,
                            status=VulnerabilityStatus.NEEDS_REVIEW,
                            description=desc,
                            file_path=str(py_file),
                            recommendation="Never log passwords, tokens, or secrets",
                        ))
                except Exception:
                    pass

        print("  [OK] A09 scan complete")

    async def scan_a10_ssrf(self) -> None:
        """A10:2021 - Server-Side Request Forgery"""
        print("\n[A10] SSRF Scan...")

        python_files = list(self.backend_path.rglob("*.py"))

        ssrf_patterns = [
            (r'requests\.(get|post|put|delete)\s*\([^)]*\+', "URL concatenation in requests"),
            (r'httpx\.(get|post|put|delete)\s*\([^)]*\+', "URL concatenation in httpx"),
            (r'aiohttp\..*\(\s*f["\']', "f-string URL in aiohttp"),
            (r'urllib\.request\.urlopen\s*\(', "urllib.request usage"),
        ]

        for pattern, desc in ssrf_patterns:
            for py_file in python_files:
                if "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(pattern, content):
                        self.report.add_finding(Finding(
                            vulnerability_id="A10-001",
                            title="Potential SSRF Vulnerability",
                            severity=Severity.HIGH,
                            status=VulnerabilityStatus.NEEDS_REVIEW,
                            description=desc,
                            file_path=str(py_file),
                            recommendation="Validate and whitelist external URLs",
                        ))
                except Exception:
                    pass

        url_validation_found = False
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if any(v in content for v in ["validate_url", "url_validator", "AnyUrl", "HttpUrl"]):
                    url_validation_found = True
                    break
            except Exception:
                pass

        if url_validation_found:
            self.report.add_finding(Finding(
                vulnerability_id="A10-002",
                title="URL Validation Present",
                severity=Severity.INFO,
                status=VulnerabilityStatus.SECURE,
                description="URL validation mechanism found",
            ))
        else:
            self.report.add_finding(Finding(
                vulnerability_id="A10-002",
                title="URL Validation Not Found",
                severity=Severity.MEDIUM,
                status=VulnerabilityStatus.NEEDS_REVIEW,
                description="No URL validation mechanism found",
                recommendation="Implement URL validation and whitelisting",
            ))

        print("  [OK] A10 scan complete")

    def export_report(self, output_path: str) -> None:
        """Export audit report to JSON and Markdown"""
        json_path = Path(output_path) / "security_audit_report.json"
        report_dict = {
            "scan_date": self.report.scan_date,
            "scanner_version": self.report.scanner_version,
            "target": self.report.target,
            "summary": self.report.summary,
            "findings": [
                {
                    "id": f.vulnerability_id,
                    "title": f.title,
                    "severity": f.severity.value,
                    "status": f.status.value,
                    "description": f.description,
                    "file_path": f.file_path,
                    "recommendation": f.recommendation,
                    "evidence": f.evidence,
                }
                for f in self.report.findings
            ],
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        md_path = Path(output_path) / "SECURITY_AUDIT_REPORT.md"
        md_content = self._generate_markdown_report()

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"\n[REPORT] Reports exported to:")
        print(f"   - {json_path}")
        print(f"   - {md_path}")

    def _generate_markdown_report(self) -> str:
        """Generate Markdown format report"""
        summary = self.report.summary

        md = f"""# KIRO2 Security Audit Report

**Scan Date:** {self.report.scan_date}
**Scanner Version:** {self.report.scanner_version}
**Target:** {self.report.target}

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Findings | {summary.get('total_findings', 0)} |
| CRITICAL | {summary.get('critical', 0)} |
| HIGH | {summary.get('high', 0)} |
| MEDIUM | {summary.get('medium', 0)} |
| LOW | {summary.get('low', 0)} |
| INFO | {summary.get('info', 0)} |

### Status Distribution

| Status | Count |
|--------|-------|
| Vulnerable | {summary.get('vulnerable', 0)} |
| Secure | {summary.get('secure', 0)} |
| Needs Review | {summary.get('needs_review', 0)} |

---

## Detailed Findings

"""
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]

        for severity in severity_order:
            findings = [f for f in self.report.findings if f.severity == severity]
            if findings:
                md += f"\n### {severity.value} Severity\n\n"
                for f in findings:
                    status_icon = "[VULNERABLE]" if f.status == VulnerabilityStatus.VULNERABLE else "[SECURE]" if f.status == VulnerabilityStatus.SECURE else "[REVIEW]"
                    md += f"""#### {f.vulnerability_id}: {f.title} {status_icon}

- **Status:** {f.status.value}
- **Description:** {f.description}
"""
                    if f.file_path:
                        md += f"- **File:** `{f.file_path}`\n"
                    if f.recommendation:
                        md += f"- **Recommendation:** {f.recommendation}\n"
                    if f.evidence:
                        md += f"- **Evidence:** `{f.evidence[:200]}`\n"
                    md += "\n"

        md += """---

## Recommendations Summary

1. **Immediately Address:** All CRITICAL and HIGH findings marked as VULNERABLE
2. **Review Soon:** All MEDIUM findings and items marked NEEDS_REVIEW
3. **Best Practice:** Address LOW and INFO items as part of ongoing security hygiene

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)

---

*Report generated by KIRO2 Security Audit Scanner*
"""
        return md


async def main():
    """Main entry point"""
    backend_path = Path(__file__).parent.parent.parent
    output_path = Path(__file__).parent

    scanner = OWASPTop10Scanner(str(backend_path))
    report = await scanner.run_full_scan()

    print("\n" + "=" * 60)
    print("[SUMMARY] SCAN COMPLETE")
    print("=" * 60)

    summary = report.summary
    print(f"Total Findings: {summary['total_findings']}")
    print(f"  CRITICAL: {summary['critical']}")
    print(f"  HIGH: {summary['high']}")
    print(f"  MEDIUM: {summary['medium']}")
    print(f"  LOW: {summary['low']}")
    print(f"  INFO: {summary['info']}")
    print()
    print(f"  Vulnerable: {summary['vulnerable']}")
    print(f"  Secure: {summary['secure']}")
    print(f"  Needs Review: {summary['needs_review']}")

    scanner.export_report(str(output_path))

    if summary['critical'] > 0 or summary['vulnerable'] > 3:
        print("\n[WARNING] SECURITY ISSUES FOUND - Review required!")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
