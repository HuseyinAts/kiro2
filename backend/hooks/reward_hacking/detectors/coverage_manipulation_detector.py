"""
Coverage Manipulation Detector - Detects coverage manipulation.

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

from __future__ import annotations

import re
from typing import List

from ..base_detector import BaseDetector
from ..models.enums import SeverityLevel, PatternType
from ..models.detection_result import DetectionResult
from ..analyzers.context_analyzer import ContextAnalyzer
from ..config.patterns import REWARD_HACKING_PATTERNS


class CoverageManipulationDetector(BaseDetector):
    """
    Detects coverage manipulation patterns.

    Patterns detected:
    - # pragma: no cover (without reason)
    - # type: ignore (excessive use)
    - # noqa (without code)
    - @pytest.mark.skip (without reason)
    """

    name = "CoverageManipulationDetector"
    pattern_type = PatternType.COVERAGE_MANIPULATION
    default_severity = SeverityLevel.CRITICAL

    def get_patterns(self) -> List[str]:
        """Get regex patterns for coverage manipulation detection."""
        return REWARD_HACKING_PATTERNS.get("coverage_manipulation", [])

    async def detect(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect coverage manipulation patterns.

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
            message_template="Coverage manipulation detected: {pattern}"
        )

        # Filter and classify results
        for result in regex_results:
            if context_analyzer.should_ignore(result.line_number, "coverage_manipulation"):
                continue

            code_lower = result.code_snippet.lower()

            # Check if pragma: no cover has a documented reason
            if 'pragma' in code_lower and 'no cover' in code_lower:
                if self._has_documented_reason(result.code_snippet):
                    # With documented reason - just info
                    result.severity = SeverityLevel.INFO
                    result.message = "pragma: no cover with documented reason"
                else:
                    result.severity = SeverityLevel.CRITICAL
                    result.message = "pragma: no cover without documented reason"

            # Check type: ignore specificity
            if 'type:' in code_lower and 'ignore' in code_lower:
                if self._has_specific_ignore_code(result.code_snippet):
                    # Specific ignore (e.g., type: ignore[arg-type]) is OK
                    result.severity = SeverityLevel.INFO
                    result.message = "type: ignore with specific error code"
                else:
                    result.severity = SeverityLevel.WARNING
                    result.message = "type: ignore without specific error code"

            # Apply confidence modifier
            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier

            if result.confidence >= self.config.min_confidence:
                results.append(result)

        # Count type: ignore usage for excessive use warning
        type_ignore_count = self._count_type_ignores(content)
        if type_ignore_count > 10:
            results.append(self._create_result(
                file_path=file_path,
                line_number=1,
                code_snippet=f"Total type: ignore count: {type_ignore_count}",
                message=f"Excessive type: ignore usage ({type_ignore_count} occurrences)",
                confidence=0.8
            ))

        return results

    def _has_documented_reason(self, code: str) -> bool:
        """
        Check if pragma: no cover has a documented reason.

        Args:
            code: Code snippet

        Returns:
            True if reason is documented
        """
        # Look for comment after pragma: no cover
        # Valid: # pragma: no cover  # defensive code
        # Invalid: # pragma: no cover

        pattern = r'pragma:\s*no\s*cover\s*#\s*\w{3,}'
        return bool(re.search(pattern, code, re.IGNORECASE))

    def _has_specific_ignore_code(self, code: str) -> bool:
        """
        Check if type: ignore has a specific error code.

        Args:
            code: Code snippet

        Returns:
            True if specific error code present
        """
        # Valid: # type: ignore[arg-type]
        # Invalid: # type: ignore

        pattern = r'type:\s*ignore\s*\[\w+.*?\]'
        return bool(re.search(pattern, code, re.IGNORECASE))

    def _count_type_ignores(self, content: str) -> int:
        """
        Count total type: ignore occurrences.

        Args:
            content: File content

        Returns:
            Count of type: ignore
        """
        pattern = r'#\s*type:\s*ignore'
        return len(re.findall(pattern, content, re.IGNORECASE))
