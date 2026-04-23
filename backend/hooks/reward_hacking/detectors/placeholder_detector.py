"""
Placeholder Code Detector - Detects incomplete code.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

from __future__ import annotations

from ..analyzers.ast_analyzer import ASTAnalyzer
from ..analyzers.context_analyzer import ContextAnalyzer
from ..base_detector import BaseDetector
from ..config.patterns import REWARD_HACKING_PATTERNS
from ..exceptions import ASTParseError
from ..models.detection_result import DetectionResult
from ..models.enums import PatternType, SeverityLevel


class PlaceholderDetector(BaseDetector):
    """
    Detects placeholder code patterns.

    Patterns detected:
    - pass # placeholder
    - # TODO: implement
    - # FIXME: implement
    - raise NotImplementedError
    - ... (Ellipsis as placeholder)
    - return None # stub
    """

    name = "PlaceholderDetector"
    pattern_type = PatternType.PLACEHOLDER
    default_severity = SeverityLevel.CRITICAL

    def get_patterns(self) -> list[str]:
        """Get regex patterns for placeholder detection."""
        return REWARD_HACKING_PATTERNS.get("placeholder", [])

    async def detect(
        self,
        file_path: str,
        content: str
    ) -> list[DetectionResult]:
        """
        Detect placeholder code patterns.

        Args:
            file_path: Path to file being analyzed
            content: File content

        Returns:
            List of DetectionResult objects
        """
        if not self.is_enabled():
            return []

        results: list[DetectionResult] = []

        # Initialize context analyzer
        context_analyzer = ContextAnalyzer(content, file_path)

        # 1. Regex-based detection for TODO/FIXME and explicit placeholders
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="Placeholder code detected: {pattern}"
        )

        # Classify results - TODO/FIXME are warnings, others are critical
        for result in regex_results:
            if context_analyzer.should_ignore(result.line_number, "placeholder"):
                continue

            # Adjust severity for TODO/FIXME (warning) vs actual placeholders (critical)
            code_lower = result.code_snippet.lower()
            if 'todo' in code_lower or 'fixme' in code_lower:
                # Check if it has a tracking reference (e.g., JIRA ticket)
                if self._has_tracking_reference(result.code_snippet):
                    # Tracked TODOs are just info
                    result.severity = SeverityLevel.INFO
                    result.message = "Tracked TODO/FIXME (has reference)"
                else:
                    result.severity = SeverityLevel.WARNING
                    result.message = "Untracked TODO/FIXME - consider adding ticket reference"

            # Apply confidence modifier
            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier

            if result.confidence >= self.config.min_confidence:
                results.append(result)

        # 2. AST-based detection for empty functions and NotImplementedError
        if file_path.endswith('.py'):
            ast_results = await self._ast_detect(file_path, content, context_analyzer)
            results.extend(ast_results)

        return results

    async def _ast_detect(
        self,
        file_path: str,
        content: str,
        context_analyzer: ContextAnalyzer
    ) -> list[DetectionResult]:
        """
        Perform AST-based detection for empty functions and NotImplementedError.

        Args:
            file_path: Path to file
            content: File content
            context_analyzer: Context analyzer instance

        Returns:
            List of DetectionResult objects
        """
        results: list[DetectionResult] = []

        try:
            ast_analyzer = ASTAnalyzer(content, file_path)
            ast_analyzer.parse()

            # Find empty functions
            for match in ast_analyzer.find_empty_functions():
                if context_analyzer.should_ignore(match.line_number, "placeholder"):
                    continue

                confidence = match.confidence * context_analyzer.get_confidence_modifier(
                    match.line_number
                )

                if confidence >= self.config.min_confidence:
                    results.append(self._create_result(
                        file_path=file_path,
                        line_number=match.line_number,
                        code_snippet=match.code,
                        message=f"Empty function body: {match.message}",
                        confidence=confidence,
                        column_number=match.column
                    ))

            # Find raise NotImplementedError
            for match in ast_analyzer.find_raise_not_implemented():
                if context_analyzer.should_ignore(match.line_number, "placeholder"):
                    continue

                confidence = match.confidence * context_analyzer.get_confidence_modifier(
                    match.line_number
                )

                if confidence >= self.config.min_confidence:
                    results.append(self._create_result(
                        file_path=file_path,
                        line_number=match.line_number,
                        code_snippet=match.code,
                        message="NotImplementedError - implement or remove",
                        confidence=confidence,
                        column_number=match.column
                    ))

        except ASTParseError:
            pass
        except Exception:
            pass

        return results

    def _has_tracking_reference(self, code: str) -> bool:
        """
        Check if TODO/FIXME has a tracking reference (ticket number).

        Args:
            code: Code snippet

        Returns:
            True if tracking reference found
        """
        import re

        # Common patterns for ticket references
        tracking_patterns = [
            r'[A-Z]+-\d+',           # JIRA style: PROJ-123
            r'#\d+',                  # GitHub style: #123
            r'GH-\d+',               # GitHub explicit: GH-123
            r'BUG-\d+',              # Bug tracking: BUG-123
            r'ISSUE-\d+',            # Issue tracking: ISSUE-123
        ]

        for pattern in tracking_patterns:
            if re.search(pattern, code):
                return True

        return False
