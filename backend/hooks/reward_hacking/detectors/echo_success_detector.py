"""
Echo Success Detector - Detects fake success messages.

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

from __future__ import annotations

from typing import List

from ..base_detector import BaseDetector
from ..models.enums import SeverityLevel, PatternType
from ..models.detection_result import DetectionResult
from ..analyzers.context_analyzer import ContextAnalyzer
from ..config.patterns import REWARD_HACKING_PATTERNS


class EchoSuccessDetector(BaseDetector):
    """
    Detects echo Success and similar fake success messages.

    Patterns detected:
    - echo Success
    - print("Success")
    - console.log("Success")
    - Success messages without actual validation
    """

    name = "EchoSuccessDetector"
    pattern_type = PatternType.ECHO_SUCCESS
    default_severity = SeverityLevel.CRITICAL

    def get_patterns(self) -> List[str]:
        """Get regex patterns for echo success detection."""
        return REWARD_HACKING_PATTERNS.get("echo_success", [])

    async def detect(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect echo success patterns.

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

        # Regex-based detection
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="Fake success message detected: {pattern}"
        )

        # Filter and enhance results
        for result in regex_results:
            if context_analyzer.should_ignore(result.line_number, "echo_success"):
                continue

            # Check for validation before success message
            has_validation = self._check_validation_before(
                content, result.line_number
            )

            if has_validation:
                # Lower severity if there's validation
                result.confidence *= 0.5
                continue

            # Check for combined return 0 + echo Success (higher severity)
            if self._has_return_zero_nearby(content, result.line_number):
                result.message = f"{result.message} (combined with return 0 - high risk)"

            # Apply confidence modifier
            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier

            if result.confidence >= self.config.min_confidence:
                results.append(result)

        return results

    def _check_validation_before(self, content: str, line_number: int) -> bool:
        """
        Check if there's actual validation before the success message.

        Args:
            content: File content
            line_number: Line number of success message

        Returns:
            True if validation exists
        """
        lines = content.split('\n')

        # Look at 5 lines before for validation patterns
        start = max(0, line_number - 6)
        end = line_number - 1

        validation_patterns = [
            'if ', 'elif ', 'test ', '[ ', '[[ ',
            'assert', 'verify', 'check', 'validate',
            '$?', 'exit_code', 'return_code'
        ]

        for i in range(start, end):
            if i < len(lines):
                line_lower = lines[i].lower()
                if any(pattern in line_lower for pattern in validation_patterns):
                    return True

        return False

    def _has_return_zero_nearby(self, content: str, line_number: int) -> bool:
        """
        Check if there's a return 0 near the success message.

        Args:
            content: File content
            line_number: Line number of success message

        Returns:
            True if return 0 is nearby
        """
        lines = content.split('\n')

        # Look at 3 lines before and after
        start = max(0, line_number - 4)
        end = min(len(lines), line_number + 3)

        return_patterns = ['return 0', 'exit 0', 'exit(0)', 'return 0;']

        for i in range(start, end):
            if i < len(lines):
                line_lower = lines[i].lower()
                if any(pattern in line_lower for pattern in return_patterns):
                    return True

        return False
