"""
Hardcoded Test Data Detector - Detects hardcoded test values.

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""

from __future__ import annotations

import re
from typing import List

from ..base_detector import BaseDetector
from ..models.enums import SeverityLevel, PatternType
from ..models.detection_result import DetectionResult
from ..analyzers.context_analyzer import ContextAnalyzer
from ..config.patterns import REWARD_HACKING_PATTERNS


class HardcodedTestDataDetector(BaseDetector):
    """
    Detects hardcoded test data patterns.

    Patterns detected:
    - Magic numbers (user_id = 1)
    - Hardcoded email/password
    - Static API keys/secrets
    - Lack of test data variety
    """

    name = "HardcodedTestDataDetector"
    pattern_type = PatternType.HARDCODED_TEST_DATA
    default_severity = SeverityLevel.WARNING  # Warning by default

    # Magic number threshold - below this is suspicious
    MAGIC_NUMBER_THRESHOLD = 5

    def get_patterns(self) -> List[str]:
        """Get regex patterns for hardcoded test data detection."""
        return REWARD_HACKING_PATTERNS.get("hardcoded_test_data", [])

    async def detect(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect hardcoded test data patterns.

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

        # 1. Regex-based detection
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="Hardcoded test data detected: {pattern}"
        )

        for result in regex_results:
            if context_analyzer.should_ignore(result.line_number, "hardcoded_test_data"):
                continue

            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier

            if result.confidence >= self.config.min_confidence:
                results.append(result)

        # 2. Detect magic numbers
        magic_results = self._detect_magic_numbers(file_path, content)
        results.extend(magic_results)

        # 3. Detect hardcoded credentials
        credential_results = self._detect_hardcoded_credentials(file_path, content)
        results.extend(credential_results)

        # 4. Check test data variety
        variety_results = self._check_test_variety(file_path, content)
        results.extend(variety_results)

        return results

    def _detect_magic_numbers(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect magic numbers in test assertions.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for magic numbers
        """
        results: List[DetectionResult] = []

        # Patterns for suspicious magic numbers in test context
        magic_patterns = [
            (r'\b(user_id|id)\s*=\s*(\d+)', 'Magic ID number'),
            (r'\bassert.*==\s*(\d+)\s*$', 'Magic number in assertion'),
            (r'\bcount\s*=\s*(\d+)', 'Magic count number'),
            (r'\bindex\s*=\s*(\d+)', 'Magic index number'),
        ]

        lines = content.split('\n')

        for pattern, message in magic_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                # Extract the number
                groups = match.groups()
                if groups:
                    num = int(groups[-1]) if groups[-1].isdigit() else 0
                    if num <= self.MAGIC_NUMBER_THRESHOLD:
                        results.append(self._create_result(
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=line_content.strip(),
                            message=f"{message}: {num} - use fixtures/factories",
                            confidence=0.7
                        ))

        return results

    def _detect_hardcoded_credentials(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect hardcoded credentials in tests.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for hardcoded credentials
        """
        results: List[DetectionResult] = []

        # Credential patterns
        credential_patterns = [
            (r'email\s*=\s*["\']test@test\.com["\']', 'Hardcoded test email'),
            (r'email\s*=\s*["\']admin@', 'Hardcoded admin email'),
            (r'password\s*=\s*["\']password["\']', 'Hardcoded weak password'),
            (r'password\s*=\s*["\']123', 'Hardcoded numeric password'),
            (r'password\s*=\s*["\']test', 'Hardcoded test password'),
            (r'api_key\s*=\s*["\']test', 'Hardcoded test API key'),
            (r'secret\s*=\s*["\']secret', 'Hardcoded secret'),
            (r'token\s*=\s*["\']test', 'Hardcoded test token'),
        ]

        lines = content.split('\n')

        for pattern, message in credential_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                results.append(self._create_result(
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    message=f"{message} - use faker/factories",
                    confidence=0.8
                ))

        return results

    def _check_test_variety(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Check if tests have sufficient data variety.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for low variety
        """
        results: List[DetectionResult] = []

        # Count test functions
        test_count = len(re.findall(r'def test_\w+', content))

        # Count @pytest.mark.parametrize
        parametrize_count = len(re.findall(r'@pytest\.mark\.parametrize', content))

        # If many tests but no parametrize, suggest it
        if test_count > 5 and parametrize_count == 0:
            results.append(self._create_result(
                file_path=file_path,
                line_number=1,
                code_snippet=f"Tests: {test_count}, Parametrize: {parametrize_count}",
                message="Consider using @pytest.mark.parametrize for test variety",
                confidence=0.6
            ))

        # Suggest Hypothesis for property-based testing
        if 'hypothesis' not in content.lower() and test_count > 10:
            results.append(self._create_result(
                file_path=file_path,
                line_number=1,
                code_snippet=f"Test count: {test_count}",
                message="Consider Hypothesis for property-based testing",
                confidence=0.5
            ))

        return results

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        file_lower = file_path.lower()
        test_indicators = ['test_', '_test.py', '/tests/', '/test/', 'conftest.py']
        return any(indicator in file_lower for indicator in test_indicators)
