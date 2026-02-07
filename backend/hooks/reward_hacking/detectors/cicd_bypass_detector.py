"""
CI/CD Bypass Detector - Detects CI/CD bypass attempts.

Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

from __future__ import annotations

import re
from typing import List

from ..base_detector import BaseDetector
from ..models.enums import SeverityLevel, PatternType
from ..models.detection_result import DetectionResult
from ..analyzers.ast_analyzer import ASTAnalyzer
from ..analyzers.context_analyzer import ContextAnalyzer
from ..config.patterns import REWARD_HACKING_PATTERNS
from ..exceptions import ASTParseError


class CICDBypassDetector(BaseDetector):
    """
    Detects CI/CD bypass patterns.

    Patterns detected:
    - [skip ci] / [ci skip] in commit messages
    - --no-verify flag
    - @pytest.mark.skip without reason
    - Quality gate disable attempts
    """

    name = "CICDBypassDetector"
    pattern_type = PatternType.CICD_BYPASS
    default_severity = SeverityLevel.CRITICAL

    def get_patterns(self) -> List[str]:
        """Get regex patterns for CI/CD bypass detection."""
        return REWARD_HACKING_PATTERNS.get("cicd_bypass", [])

    async def detect(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect CI/CD bypass patterns.

        Args:
            file_path: Path to file being analyzed
            content: File content

        Returns:
            List of DetectionResult objects
        """
        if not self.is_enabled():
            return []

        results: List[DetectionResult] = []

        # Initialize context analyzer
        context_analyzer = ContextAnalyzer(content, file_path)

        # 1. Regex-based detection
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="CI/CD bypass detected: {pattern}"
        )

        for result in regex_results:
            if context_analyzer.should_ignore(result.line_number, "cicd_bypass"):
                continue

            # Check for documented reason
            if self._has_documented_reason(content, result.line_number):
                result.severity = SeverityLevel.INFO
                result.message += " (with documented reason)"

            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier

            if result.confidence >= self.config.min_confidence:
                results.append(result)

        # 2. AST-based detection for skip decorators (Python only)
        if file_path.endswith('.py'):
            ast_results = await self._detect_skip_decorators(file_path, content, context_analyzer)
            results.extend(ast_results)

        # 3. Detect quality gate disabling
        quality_gate_results = self._detect_quality_gate_bypass(file_path, content)
        results.extend(quality_gate_results)

        return results

    async def _detect_skip_decorators(
        self,
        file_path: str,
        content: str,
        context_analyzer: ContextAnalyzer
    ) -> List[DetectionResult]:
        """
        Detect skip decorators without reason using AST.

        Args:
            file_path: Path to file
            content: File content
            context_analyzer: Context analyzer instance

        Returns:
            List of DetectionResult for skip decorators
        """
        results: List[DetectionResult] = []

        try:
            ast_analyzer = ASTAnalyzer(content, file_path)
            ast_analyzer.parse()

            for match in ast_analyzer.find_skip_decorators():
                if context_analyzer.should_ignore(match.line_number, "cicd_bypass"):
                    continue

                confidence = match.confidence * context_analyzer.get_confidence_modifier(
                    match.line_number
                )

                if confidence >= self.config.min_confidence:
                    results.append(self._create_result(
                        file_path=file_path,
                        line_number=match.line_number,
                        code_snippet=match.code,
                        message=f"Skip decorator without reason: {match.message}",
                        confidence=confidence,
                        column_number=match.column
                    ))

        except ASTParseError:
            pass
        except Exception:
            pass

        return results

    def _has_documented_reason(self, content: str, line_number: int) -> bool:
        """
        Check if bypass has a documented reason.

        Args:
            content: File content
            line_number: Line number of bypass

        Returns:
            True if reason is documented
        """
        lines = content.split('\n')

        if line_number <= len(lines):
            line = lines[line_number - 1]

            # Check for reason parameter
            if 'reason=' in line or 'reason =' in line:
                return True

            # Check for inline comment
            if '#' in line:
                comment = line.split('#')[1].strip()
                # Reason should have at least some explanation
                if len(comment) > 10:
                    return True

        # Check line before for comment
        if line_number > 1:
            prev_line = lines[line_number - 2].strip()
            if prev_line.startswith('#') and len(prev_line) > 10:
                return True

        return False

    def _detect_quality_gate_bypass(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect attempts to disable quality gates.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for quality gate bypasses
        """
        results: List[DetectionResult] = []

        # Patterns for quality gate bypassing
        bypass_patterns = [
            (r'DISABLE_LINT\s*=\s*[Tt]rue', 'Lint disabled'),
            (r'SKIP_TESTS\s*=\s*[Tt]rue', 'Tests disabled'),
            (r'DISABLE_TYPE_CHECK\s*=\s*[Tt]rue', 'Type checking disabled'),
            (r'COVERAGE_THRESHOLD\s*=\s*0', 'Coverage threshold set to 0'),
            (r'fail_under\s*=\s*0', 'Coverage fail_under set to 0'),
            (r'--no-strict', 'Strict mode disabled'),
            (r'--allow-empty', 'Empty results allowed'),
        ]

        lines = content.split('\n')

        for pattern, message in bypass_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                results.append(self._create_result(
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    message=f"Quality gate bypass: {message}",
                    confidence=0.9
                ))

        return results

    def detect_in_commit_message(self, commit_message: str) -> List[DetectionResult]:
        """
        Detect CI skip patterns in commit messages.

        This is a special method for analyzing commit messages
        rather than file content.

        Args:
            commit_message: Git commit message

        Returns:
            List of DetectionResult for bypass attempts
        """
        results: List[DetectionResult] = []

        skip_patterns = [
            (r'\[skip\s*ci\]', '[skip ci] in commit message'),
            (r'\[ci\s*skip\]', '[ci skip] in commit message'),
            (r'\[no\s*ci\]', '[no ci] in commit message'),
            (r'\[skip\s*tests?\]', '[skip test(s)] in commit message'),
            (r'\[wip\]', '[wip] - work in progress commit'),
        ]

        for pattern, message in skip_patterns:
            if re.search(pattern, commit_message, re.IGNORECASE):
                results.append(self._create_result(
                    file_path="COMMIT_MESSAGE",
                    line_number=1,
                    code_snippet=commit_message[:100],
                    message=message,
                    confidence=0.95
                ))

        return results
