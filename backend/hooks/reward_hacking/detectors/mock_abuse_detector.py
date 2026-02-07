"""
Mock Abuse Detector - Detects excessive mocking.

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
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


class MockAbuseDetector(BaseDetector):
    """
    Detects excessive mock usage in tests.

    Patterns detected:
    - Mock ratio > 80%
    - Missing mock verification (assert_called_once)
    - Static mock return values
    - Multiple consecutive @patch decorators
    """

    name = "MockAbuseDetector"
    pattern_type = PatternType.MOCK_ABUSE
    default_severity = SeverityLevel.WARNING  # Warning by default

    # Threshold for mock abuse
    MOCK_RATIO_THRESHOLD = 0.8  # 80%

    def get_patterns(self) -> List[str]:
        """Get regex patterns for mock abuse detection."""
        return REWARD_HACKING_PATTERNS.get("mock_abuse", [])

    async def detect(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect mock abuse patterns.

        Args:
            file_path: Path to file being analyzed
            content: File content

        Returns:
            List of DetectionResult objects
        """
        if not self.is_enabled():
            return []

        # Only analyze test files
        if not self._is_test_file(file_path):
            return []

        results: List[DetectionResult] = []

        # Initialize context analyzer
        context_analyzer = ContextAnalyzer(content, file_path)

        # 1. Check mock ratio using AST
        if file_path.endswith('.py'):
            ratio_results = await self._check_mock_ratio(file_path, content)
            results.extend(ratio_results)

        # 2. Regex-based detection for specific patterns
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="Mock abuse pattern detected: {pattern}"
        )

        for result in regex_results:
            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier
            if result.confidence >= self.config.min_confidence:
                results.append(result)

        # 3. Check for missing mock verification
        verification_results = self._check_mock_verification(file_path, content)
        results.extend(verification_results)

        # 4. Check for static return values
        static_results = self._check_static_returns(file_path, content)
        results.extend(static_results)

        return results

    async def _check_mock_ratio(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Check if mock usage ratio exceeds threshold.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult if ratio exceeded
        """
        results: List[DetectionResult] = []

        try:
            ast_analyzer = ASTAnalyzer(content, file_path)
            ast_analyzer.parse()

            mock_count, total_calls = ast_analyzer.count_mock_usage()

            if total_calls > 0:
                ratio = mock_count / total_calls

                if ratio > self.MOCK_RATIO_THRESHOLD:
                    results.append(self._create_result(
                        file_path=file_path,
                        line_number=1,
                        code_snippet=f"Mock ratio: {ratio:.0%} ({mock_count}/{total_calls})",
                        message=f"High mock ratio ({ratio:.0%}) - consider integration tests",
                        confidence=0.85
                    ))

        except ASTParseError:
            pass
        except Exception:
            pass

        return results

    def _check_mock_verification(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Check for mocks without verification.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for unverified mocks
        """
        results: List[DetectionResult] = []

        # Count @patch decorators
        patch_pattern = r'@patch\s*\('
        patches = list(re.finditer(patch_pattern, content))

        # Count mock verifications
        verify_patterns = [
            r'\.assert_called',
            r'\.assert_not_called',
            r'\.call_args',
            r'\.call_count',
            r'\.called',
        ]

        verify_count = sum(
            len(re.findall(pattern, content))
            for pattern in verify_patterns
        )

        # If many patches but few verifications, flag it
        if len(patches) > 3 and verify_count < len(patches) // 2:
            results.append(self._create_result(
                file_path=file_path,
                line_number=1,
                code_snippet=f"Patches: {len(patches)}, Verifications: {verify_count}",
                message="Many mocks without verification - add assert_called checks",
                confidence=0.75
            ))

        return results

    def _check_static_returns(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Check for static mock return values.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for static returns
        """
        results: List[DetectionResult] = []

        # Patterns for trivial return values
        static_patterns = [
            (r'return_value\s*=\s*True\s*[,\)]', 'Mock always returns True'),
            (r'return_value\s*=\s*False\s*[,\)]', 'Mock always returns False'),
            (r'return_value\s*=\s*None\s*[,\)]', 'Mock always returns None'),
            (r'return_value\s*=\s*\[\s*\]\s*[,\)]', 'Mock always returns empty list'),
            (r'return_value\s*=\s*\{\s*\}\s*[,\)]', 'Mock always returns empty dict'),
        ]

        lines = content.split('\n')

        for pattern, message in static_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                results.append(self._create_result(
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    message=message,
                    confidence=0.7
                ))

        return results

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        file_lower = file_path.lower()
        test_indicators = ['test_', '_test.py', '/tests/', '/test/', 'conftest.py']
        return any(indicator in file_lower for indicator in test_indicators)
