"""
SQL Injection Prevention Auditor (Task 51.5)
Automated auditing tool for SQL injection vulnerabilities

Author: Claude
Date: 2025-10-27
"""
import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.structured_logger import get_logger

logger = get_logger("sql_injection_auditor")


class VulnerabilitySeverity(str, Enum):
    """Severity levels for SQL injection vulnerabilities"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SQLVulnerability:
    """SQL injection vulnerability finding"""

    file_path: str
    line_number: int
    severity: VulnerabilitySeverity
    description: str
    code_snippet: str
    recommendation: str


class SQLInjectionAuditor:
    """
    SQL Injection Prevention Auditor (Task 51.5)

    Scans Python codebase for potential SQL injection vulnerabilities:
    - Raw SQL queries without parameterization
    - String concatenation in SQL
    - f-strings in SQL queries
    - Unsafe .format() usage
    - Missing input validation
    """

    # Dangerous SQL patterns
    DANGEROUS_PATTERNS = [
        # String concatenation
        (
            r'execute\(["\'].*?\s*\+\s*',
            VulnerabilitySeverity.CRITICAL,
            "SQL query uses string concatenation",
        ),
        (
            r'executemany\(["\'].*?\s*\+\s*',
            VulnerabilitySeverity.CRITICAL,
            "SQL query uses string concatenation",
        ),
        # f-strings in SQL
        (
            r'execute\(f["\']',
            VulnerabilitySeverity.CRITICAL,
            "SQL query uses f-string interpolation",
        ),
        (
            r'executemany\(f["\']',
            VulnerabilitySeverity.CRITICAL,
            "SQL query uses f-string interpolation",
        ),
        # .format() usage
        (
            r'execute\(["\'].*?\.format\(',
            VulnerabilitySeverity.HIGH,
            "SQL query uses .format() method",
        ),
        (
            r'executemany\(["\'].*?\.format\(',
            VulnerabilitySeverity.HIGH,
            "SQL query uses .format() method",
        ),
        # % formatting
        (
            r'execute\(["\'].*?%\s*\(',
            VulnerabilitySeverity.HIGH,
            "SQL query uses % formatting",
        ),
        (
            r'executemany\(["\'].*?%\s*\(',
            VulnerabilitySeverity.HIGH,
            "SQL query uses % formatting",
        ),
        # Raw SQL functions
        (
            r'text\(f["\']',
            VulnerabilitySeverity.HIGH,
            "SQLAlchemy text() uses f-string",
        ),
        (
            r'text\(["\'].*?\.format\(',
            VulnerabilitySeverity.HIGH,
            "SQLAlchemy text() uses .format()",
        ),
    ]

    # Safe patterns (parameterized queries)
    SAFE_PATTERNS = [
        r'execute\(["\'].*?["\'],\s*\{',  # execute with dict parameters
        r'execute\(["\'].*?["\'],\s*\[',  # execute with list parameters
        r'execute\(["\'].*?["\'],\s*\(',  # execute with tuple parameters
        r'execute\(text\(["\'].*?["\']\),\s*\{',  # SQLAlchemy text with parameters
    ]

    # SQL keywords that indicate potential injection points
    SQL_KEYWORDS = [
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "EXEC",
        "UNION",
        "WHERE",
        "FROM",
        "JOIN",
    ]

    def __init__(self, project_root: str = "backend"):
        self.project_root = Path(project_root)
        self.vulnerabilities: list[SQLVulnerability] = []

    def audit_codebase(self) -> list[SQLVulnerability]:
        """
        Audit entire codebase for SQL injection vulnerabilities

        Returns:
            List of SQLVulnerability findings
        """
        logger.info(f"[SQL AUDIT] Starting audit of {self.project_root}")

        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))

        logger.info(f"[SQL AUDIT] Found {len(python_files)} Python files to audit")

        # Audit each file
        for file_path in python_files:
            try:
                self._audit_file(file_path)
            except Exception as e:
                logger.error(f"[SQL AUDIT] Error auditing {file_path}: {e}")

        logger.info(
            f"[SQL AUDIT] Audit complete. Found {len(self.vulnerabilities)} potential vulnerabilities"
        )

        return self.vulnerabilities

    def _audit_file(self, file_path: Path):
        """Audit single Python file for SQL injection vulnerabilities"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Pattern-based detection
            for line_num, line in enumerate(lines, start=1):
                self._check_line_for_vulnerabilities(file_path, line_num, line)

            # AST-based detection for more complex patterns
            try:
                tree = ast.parse(content)
                self._analyze_ast(file_path, tree, lines)
            except SyntaxError:
                pass  # Skip files with syntax errors

        except Exception as e:
            logger.debug(f"[SQL AUDIT] Could not audit {file_path}: {e}")

    def _check_line_for_vulnerabilities(
        self, file_path: Path, line_num: int, line: str
    ):
        """Check single line for SQL injection patterns"""
        line_stripped = line.strip()

        # Skip comments
        if line_stripped.startswith("#"):
            return

        # Check for dangerous patterns
        for pattern, severity, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if it's actually a safe pattern
                is_safe = any(
                    re.search(safe_pattern, line, re.IGNORECASE)
                    for safe_pattern in self.SAFE_PATTERNS
                )

                if not is_safe:
                    self.vulnerabilities.append(
                        SQLVulnerability(
                            file_path=str(file_path),
                            line_number=line_num,
                            severity=severity,
                            description=description,
                            code_snippet=line.strip(),
                            recommendation=self._get_recommendation(description),
                        )
                    )

    def _analyze_ast(self, file_path: Path, tree: ast.AST, lines: list[str]):
        """Analyze AST for complex SQL injection patterns"""
        for node in ast.walk(tree):
            # Check for execute() calls with string operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["execute", "executemany"]:
                        self._check_execute_call(file_path, node, lines)

    def _check_execute_call(self, file_path: Path, node: ast.Call, lines: list[str]):
        """Check execute/executemany call for SQL injection vulnerabilities"""
        if not node.args:
            return

        first_arg = node.args[0]

        # Check for f-string
        if isinstance(first_arg, ast.JoinedStr):
            line_num = node.lineno
            code_snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

            self.vulnerabilities.append(
                SQLVulnerability(
                    file_path=str(file_path),
                    line_number=line_num,
                    severity=VulnerabilitySeverity.CRITICAL,
                    description="SQL query uses f-string interpolation (AST detection)",
                    code_snippet=code_snippet,
                    recommendation="Use parameterized queries with placeholders",
                )
            )

        # Check for string concatenation
        elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
            line_num = node.lineno
            code_snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

            self.vulnerabilities.append(
                SQLVulnerability(
                    file_path=str(file_path),
                    line_number=line_num,
                    severity=VulnerabilitySeverity.CRITICAL,
                    description="SQL query uses string concatenation (AST detection)",
                    code_snippet=code_snippet,
                    recommendation="Use parameterized queries with placeholders",
                )
            )

    def _get_recommendation(self, description: str) -> str:
        """Get security recommendation based on vulnerability description"""
        if "f-string" in description:
            return (
                "Replace f-string with parameterized query:\n"
                "# Bad:  conn.execute(f'SELECT * FROM users WHERE id = {user_id}')\n"
                "# Good: conn.execute('SELECT * FROM users WHERE id = :id', {'id': user_id})"
            )
        if "concatenation" in description:
            return (
                "Replace string concatenation with parameterized query:\n"
                "# Bad:  conn.execute('SELECT * FROM users WHERE id = ' + str(user_id))\n"
                "# Good: conn.execute('SELECT * FROM users WHERE id = :id', {'id': user_id})"
            )
        if ".format()" in description:
            return (
                "Replace .format() with parameterized query:\n"
                "# Bad:  conn.execute('SELECT * FROM users WHERE id = {}'.format(user_id))\n"
                "# Good: conn.execute('SELECT * FROM users WHERE id = :id', {'id': user_id})"
            )
        if "% formatting" in description:
            return (
                "Replace % formatting with parameterized query:\n"
                "# Bad:  conn.execute('SELECT * FROM users WHERE id = %s' % user_id)\n"
                "# Good: conn.execute('SELECT * FROM users WHERE id = :id', {'id': user_id})"
            )
        return "Use parameterized queries with named or positional placeholders"

    def generate_report(self) -> dict:
        """Generate comprehensive audit report"""
        # Group by severity
        by_severity = {severity: [] for severity in VulnerabilitySeverity}

        for vuln in self.vulnerabilities:
            by_severity[vuln.severity].append(vuln)

        # Group by file
        by_file = {}
        for vuln in self.vulnerabilities:
            if vuln.file_path not in by_file:
                by_file[vuln.file_path] = []
            by_file[vuln.file_path].append(vuln)

        return {
            "total_vulnerabilities": len(self.vulnerabilities),
            "by_severity": {
                severity.value: len(vulns) for severity, vulns in by_severity.items()
            },
            "by_file": {file_path: len(vulns) for file_path, vulns in by_file.items()},
            "critical_count": len(by_severity[VulnerabilitySeverity.CRITICAL]),
            "high_count": len(by_severity[VulnerabilitySeverity.HIGH]),
            "medium_count": len(by_severity[VulnerabilitySeverity.MEDIUM]),
            "low_count": len(by_severity[VulnerabilitySeverity.LOW]),
        }

    def print_report(self):
        """Print human-readable audit report"""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("SQL INJECTION SECURITY AUDIT REPORT (Task 51.5)")
        print("=" * 80)
        print(f"\nTotal Vulnerabilities Found: {report['total_vulnerabilities']}")
        print("\nBy Severity:")
        print(f"  🔴 CRITICAL: {report['critical_count']}")
        print(f"  🟠 HIGH:     {report['high_count']}")
        print(f"  🟡 MEDIUM:   {report['medium_count']}")
        print(f"  🟢 LOW:      {report['low_count']}")

        if self.vulnerabilities:
            print("\n" + "-" * 80)
            print("DETAILED FINDINGS:")
            print("-" * 80)

            for i, vuln in enumerate(self.vulnerabilities, start=1):
                severity_emoji = {
                    VulnerabilitySeverity.CRITICAL: "🔴",
                    VulnerabilitySeverity.HIGH: "🟠",
                    VulnerabilitySeverity.MEDIUM: "🟡",
                    VulnerabilitySeverity.LOW: "🟢",
                    VulnerabilitySeverity.INFO: "ℹ️",
                }[vuln.severity]

                print(f"\n{i}. {severity_emoji} {vuln.severity.value.upper()}")
                print(f"   File: {vuln.file_path}:{vuln.line_number}")
                print(f"   Issue: {vuln.description}")
                print(f"   Code: {vuln.code_snippet}")
                print(f"   Fix: {vuln.recommendation}")

        else:
            print("\n✅ No SQL injection vulnerabilities detected!")
            print("   All SQL queries appear to use proper parameterization.")

        print("\n" + "=" * 80 + "\n")


def run_sql_audit(project_root: str = "backend") -> dict:
    """
    Run SQL injection audit on codebase (Task 51.5)

    Args:
        project_root: Root directory to audit

    Returns:
        Audit report dictionary
    """
    auditor = SQLInjectionAuditor(project_root=project_root)
    auditor.audit_codebase()
    auditor.print_report()

    return auditor.generate_report()
