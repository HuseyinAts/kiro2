"""
Assert True Detector - Detects fake assertions.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
"""

from __future__ import annotations

from typing import List

from ..base_detector import BaseDetector
from ..models.enums import SeverityLevel, PatternType
from ..models.detection_result import DetectionResult
from ..analyzers.ast_analyzer import ASTAnalyzer
from ..analyzers.context_analyzer import ContextAnalyzer
from ..config.patterns import REWARD_HACKING_PATTERNS
from ..exceptions import ASTParseError


class AssertTrueDetector(BaseDetector):
    """
    Detects assert True and similar fake assertion patterns.

    Patterns detected:
    - assert True
    - ASSERT_TRUE(true)
    - self.assertTrue(True)
    - Tautology assertions (assert 1 == 1)
    """

    name = "AssertTrueDetector"
    pattern_type = PatternType.ASSERT_TRUE
    default_severity = SeverityLevel.CRITICAL

    def get_patterns(self) -> List[str]:
        """Get regex patterns for assert True detection."""
        return REWARD_HACKING_PATTERNS.get("assert_true", [])

    async def detect(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect assert True patterns using both regex and AST analysis.

        Args:
            file_path: Path to file being analyzed
            content: File content

        Returns:
            List of DetectionResult objects
        """
        if not self.is_enabled():
            return []

        results: List[DetectionResult] = []

        # Initialize context analyzer for false positive reduction
        context_analyzer = ContextAnalyzer(content, file_path)

        # 1. Regex-based detection
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="Fake assertion detected: {pattern}"
        )

        # Filter using context analyzer
        for result in regex_results:
            if not context_analyzer.should_ignore(result.line_number, "assert_true"):
                # Apply confidence modifier
                modifier = context_analyzer.get_confidence_modifier(result.line_number)
                result.confidence *= modifier
                if result.confidence >= self.config.min_confidence:
                    results.append(result)

        # 2. AST-based detection (for Python files)
        if file_path.endswith('.py'):
            ast_results = await self._ast_detect(file_path, content, context_analyzer)
            results.extend(ast_results)

        # Remove duplicates (same line)
        return self._deduplicate(results)

    async def _ast_detect(
        self,
        file_path: str,
        content: str,
        context_analyzer: ContextAnalyzer
    ) -> List[DetectionResult]:
        """
        Perform AST-based detection for deeper analysis.

        Args:
            file_path: Path to file
            content: File content
            context_analyzer: Context analyzer instance

        Returns:
            List of DetectionResult objects
        """
        results: List[DetectionResult] = []

        try:
            ast_analyzer = ASTAnalyzer(content, file_path)
            ast_analyzer.parse()

            # Find assert True statements
            for match in ast_analyzer.find_assert_true():
                # Skip if context says ignore
                if context_analyzer.should_ignore(match.line_number, "assert_true"):
                    continue

                # Apply confidence modifier
                confidence = match.confidence * context_analyzer.get_confidence_modifier(
                    match.line_number
                )

                if confidence >= self.config.min_confidence:
                    results.append(self._create_result(
                        file_path=file_path,
                        line_number=match.line_number,
                        code_snippet=match.code,
                        message=f"AST analysis: {match.message}",
                        confidence=confidence,
                        column_number=match.column
                    ))

        except ASTParseError:
            # Skip AST analysis for files with syntax errors
            pass
        except Exception:
            # Don't fail on unexpected errors
            pass

        return results

    def _deduplicate(self, results: List[DetectionResult]) -> List[DetectionResult]:
        """Remove duplicate detections on the same line."""
        seen_lines: set = set()
        unique_results: List[DetectionResult] = []

        for result in results:
            key = (result.file_path, result.line_number)
            if key not in seen_lines:
                seen_lines.add(key)
                unique_results.append(result)

        return unique_results
