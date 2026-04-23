"""
SQL Injection Prevention Audit Tool - Task 51.5
Comprehensive audit tool to detect SQL injection vulnerabilities

Features:
- Static code analysis for SQL injection patterns
- Query parameter validation
- ORM usage verification
- Dangerous pattern detection
- Automated security report generation
"""
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class VulnerabilityLevel(str, Enum):
    """Vulnerability severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SQLInjectionFinding:
    """Represents a potential SQL injection vulnerability"""

    file_path: str
    line_number: int
    severity: VulnerabilityLevel
    pattern: str
    code_snippet: str
    description: str
    recommendation: str


@dataclass
class AuditReport:
    """Complete audit report"""

    total_files_scanned: int = 0
    total_lines_scanned: int = 0
    findings: list[SQLInjectionFinding] = field(default_factory=list)
    safe_patterns_found: int = 0
    files_with_issues: set[str] = field(default_factory=set)

    def get_summary(self) -> dict:
        """Get summary statistics"""
        severity_counts = dict.fromkeys(VulnerabilityLevel, 0)
        for finding in self.findings:
            severity_counts[finding.severity] += 1

        return {
            "total_files_scanned": self.total_files_scanned,
            "total_lines_scanned": self.total_lines_scanned,
            "total_findings": len(self.findings),
            "files_with_issues": len(self.files_with_issues),
            "severity_breakdown": {
                level.value: count for level, count in severity_counts.items()
            },
            "safe_patterns": self.safe_patterns_found,
            "risk_score": self._calculate_risk_score(),
        }

    def _calculate_risk_score(self) -> int:
        """Calculate overall risk score (0-100)"""
        weights = {
            VulnerabilityLevel.CRITICAL: 25,
            VulnerabilityLevel.HIGH: 15,
            VulnerabilityLevel.MEDIUM: 8,
            VulnerabilityLevel.LOW: 3,
            VulnerabilityLevel.INFO: 1,
        }

        score = 0
        for finding in self.findings:
            score += weights.get(finding.severity, 0)

        return min(score, 100)


class SQLInjectionAuditor:
    """
    SQL Injection vulnerability auditor

    Scans Python code for potential SQL injection vulnerabilities:
    - String concatenation in SQL queries
    - f-strings in SQL queries
    - % formatting in SQL queries
    - Unsafe execute() calls
    - Missing parameter binding
    """

    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or os.getcwd()
        self.report = AuditReport()

        # Dangerous patterns
        self.dangerous_patterns = [
            # String concatenation
            (
                r"execute\s*\([^)]*\+",
                VulnerabilityLevel.CRITICAL,
                "String concatenation in SQL execute()",
                "Use parameterized queries: execute(query, params)",
            ),
            # f-strings
            (
                r'execute\s*\(\s*f["\']',
                VulnerabilityLevel.CRITICAL,
                "f-string used in SQL execute()",
                "Use parameterized queries with placeholders",
            ),
            # % formatting
            (
                r"execute\s*\([^)]*%\s*\(",
                VulnerabilityLevel.HIGH,
                "% formatting in SQL execute()",
                "Use parameterized queries instead of % formatting",
            ),
            # .format()
            (
                r"\.format\s*\([^)]*\)\s*\)",
                VulnerabilityLevel.HIGH,
                ".format() used in SQL query",
                "Use parameterized queries",
            ),
            # Raw SQL with variables
            (
                r'(SELECT|INSERT|UPDATE|DELETE)[^"\']*\{',
                VulnerabilityLevel.HIGH,
                "Variable interpolation in raw SQL",
                "Use ORM or parameterized queries",
            ),
            # String building
            (
                r"sql\s*\+=",
                VulnerabilityLevel.MEDIUM,
                "SQL string concatenation",
                "Build queries using ORM or safe query builders",
            ),
        ]

        # Safe patterns (to reduce false positives)
        self.safe_patterns = [
            r"\.execute\s*\([^)]*,\s*\{",  # Parameterized with dict
            r"\.execute\s*\([^)]*,\s*\[",  # Parameterized with list
            r"\.execute\s*\([^)]*,\s*\(",  # Parameterized with tuple
            r"select\s*\(",  # SQLAlchemy select()
            r"insert\s*\(",  # SQLAlchemy insert()
            r"update\s*\(",  # SQLAlchemy update()
            r"delete\s*\(",  # SQLAlchemy delete()
        ]

        # ORM indicators (good patterns)
        self.orm_patterns = [
            r"\.query\s*\(",
            r"\.filter\s*\(",
            r"\.filter_by\s*\(",
            r"\.select\s*\(",
            r"session\.execute\s*\(\s*select\s*\(",
        ]

    def audit_file(self, file_path: Path) -> list[SQLInjectionFinding]:
        """Audit a single Python file"""
        findings = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            self.report.total_lines_scanned += len(lines)

            # Check for ORM usage (safe)
            has_orm = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in self.orm_patterns
            )

            # Scan each line
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()

                # Skip comments and empty lines
                if line.strip().startswith("#") or not line.strip():
                    continue

                # Check for dangerous patterns
                for (
                    pattern,
                    severity,
                    description,
                    recommendation,
                ) in self.dangerous_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if it's actually a safe pattern
                        is_safe = any(
                            re.search(safe_pattern, line, re.IGNORECASE)
                            for safe_pattern in self.safe_patterns
                        )

                        if not is_safe:
                            finding = SQLInjectionFinding(
                                file_path=str(file_path),
                                line_number=line_num,
                                severity=severity,
                                pattern=pattern,
                                code_snippet=line.strip(),
                                description=description,
                                recommendation=recommendation,
                            )
                            findings.append(finding)
                            self.report.files_with_issues.add(str(file_path))

                # Count safe patterns
                for safe_pattern in self.safe_patterns:
                    if re.search(safe_pattern, line, re.IGNORECASE):
                        self.report.safe_patterns_found += 1

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

        return findings

    def audit_directory(self, directory: Path = None) -> AuditReport:
        """Audit all Python files in directory"""
        if directory is None:
            directory = Path(self.root_dir)

        python_files = list(directory.rglob("*.py"))

        # Exclude virtual environments and migrations
        python_files = [
            f
            for f in python_files
            if "venv" not in str(f)
            and "migrations" not in str(f)
            and "__pycache__" not in str(f)
        ]

        print(f"Scanning {len(python_files)} Python files...")

        for file_path in python_files:
            self.report.total_files_scanned += 1
            findings = self.audit_file(file_path)
            self.report.findings.extend(findings)

            if findings:
                print(f"  {file_path.name}: {len(findings)} findings")

        return self.report

    def generate_report(self, output_file: str = "sql_injection_audit_report.md"):
        """Generate markdown report"""
        summary = self.report.get_summary()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# SQL Injection Security Audit Report\n\n")
            f.write(
                f"**Generated**: {__import__('datetime').datetime.now().isoformat()}\n\n"
            )

            # Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Files Scanned**: {summary['total_files_scanned']}\n")
            f.write(f"- **Lines Scanned**: {summary['total_lines_scanned']}\n")
            f.write(f"- **Total Findings**: {summary['total_findings']}\n")
            f.write(f"- **Files with Issues**: {summary['files_with_issues']}\n")
            f.write(f"- **Safe Patterns**: {summary['safe_patterns']}\n")
            f.write(f"- **Risk Score**: {summary['risk_score']}/100\n\n")

            # Severity breakdown
            f.write("## Severity Breakdown\n\n")
            for severity, count in summary["severity_breakdown"].items():
                if count > 0:
                    emoji = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🔵",
                        "info": "⚪",
                    }.get(severity, "")
                    f.write(f"- {emoji} **{severity.upper()}**: {count}\n")

            # Risk assessment
            f.write("\n## Risk Assessment\n\n")
            risk_score = summary["risk_score"]
            if risk_score >= 75:
                f.write("⛔ **CRITICAL RISK** - Immediate action required\n\n")
            elif risk_score >= 50:
                f.write("⚠️ **HIGH RISK** - Address vulnerabilities soon\n\n")
            elif risk_score >= 25:
                f.write("⚡ **MEDIUM RISK** - Review and fix when possible\n\n")
            else:
                f.write("✅ **LOW RISK** - Good security posture\n\n")

            # Detailed findings
            f.write("## Detailed Findings\n\n")

            # Group by severity
            by_severity = {}
            for finding in self.report.findings:
                if finding.severity not in by_severity:
                    by_severity[finding.severity] = []
                by_severity[finding.severity].append(finding)

            # Sort by severity
            severity_order = [
                VulnerabilityLevel.CRITICAL,
                VulnerabilityLevel.HIGH,
                VulnerabilityLevel.MEDIUM,
                VulnerabilityLevel.LOW,
                VulnerabilityLevel.INFO,
            ]

            for severity in severity_order:
                if severity in by_severity:
                    findings = by_severity[severity]
                    f.write(
                        f"### {severity.value.upper()} ({len(findings)} findings)\n\n"
                    )

                    for i, finding in enumerate(findings, 1):
                        f.write(f"#### {i}. {finding.description}\n\n")
                        f.write(f"- **File**: `{finding.file_path}`\n")
                        f.write(f"- **Line**: {finding.line_number}\n")
                        f.write(f"- **Code**: `{finding.code_snippet}`\n")
                        f.write(f"- **Recommendation**: {finding.recommendation}\n\n")

            # Best practices
            f.write("## Security Best Practices\n\n")
            f.write("1. **Always use parameterized queries**\n")
            f.write("   ```python\n")
            f.write("   # BAD\n")
            f.write('   query = f"SELECT * FROM users WHERE id = {user_id}"\n')
            f.write("   session.execute(query)\n\n")
            f.write("   # GOOD\n")
            f.write('   query = "SELECT * FROM users WHERE id = :id"\n')
            f.write('   session.execute(query, {"id": user_id})\n')
            f.write("   ```\n\n")

            f.write("2. **Prefer ORM over raw SQL**\n")
            f.write("   ```python\n")
            f.write("   # Use SQLAlchemy ORM\n")
            f.write(
                "   user = session.query(User).filter(User.id == user_id).first()\n"
            )
            f.write("   ```\n\n")

            f.write("3. **Validate and sanitize all user inputs**\n\n")
            f.write("4. **Use prepared statements**\n\n")
            f.write("5. **Implement input validation with Pydantic**\n\n")

        print(f"\nReport generated: {output_file}")


def run_audit():
    """Run SQL injection audit"""
    print("=" * 70)
    print("SQL Injection Prevention Audit - Task 51.5")
    print("=" * 70)
    print()

    # Audit backend directory
    backend_dir = Path(__file__).parent.parent
    auditor = SQLInjectionAuditor(str(backend_dir))

    print(f"Auditing directory: {backend_dir}\n")
    report = auditor.audit_directory()

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

    summary = report.get_summary()
    print("\n📊 Summary:")
    print(f"  Files scanned: {summary['total_files_scanned']}")
    print(f"  Lines scanned: {summary['total_lines_scanned']:,}")
    print(f"  Total findings: {summary['total_findings']}")
    print(f"  Risk score: {summary['risk_score']}/100")

    print("\n🎯 Severity breakdown:")
    for severity, count in summary["severity_breakdown"].items():
        if count > 0:
            print(f"  {severity.upper()}: {count}")

    # Generate report
    auditor.generate_report()

    return summary["risk_score"]


if __name__ == "__main__":
    risk_score = run_audit()

    # Exit with error code if high risk
    import sys

    if risk_score >= 50:
        sys.exit(1)  # CI/CD will fail
    else:
        sys.exit(0)
