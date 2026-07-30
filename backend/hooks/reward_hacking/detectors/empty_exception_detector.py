"""
Empty Exception Handler Detector - Detects empty exception handlers.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from __future__ import annotations

from ..analyzers.ast_analyzer import ASTAnalyzer
from ..analyzers.context_analyzer import ContextAnalyzer
from ..base_detector import BaseDetector
from ..config.patterns import REWARD_HACKING_PATTERNS
from ..exceptions import ASTParseError
from ..literal_spans import satir_bastirilmali
from ..models.detection_result import DetectionResult
from ..models.enums import PatternType, SeverityLevel


class EmptyExceptionDetector(BaseDetector):
    """
    Detects empty exception handlers.

    Patterns detected:
    - except: pass
    - except Exception: pass
    - bare except: without specific exception
    - Silent exception swallowing
    """

    name = "EmptyExceptionDetector"
    pattern_type = PatternType.EMPTY_EXCEPTION
    default_severity = SeverityLevel.CRITICAL

    def get_patterns(self) -> list[str]:
        """Get regex patterns for empty exception detection."""
        return REWARD_HACKING_PATTERNS.get("empty_exception", [])

    async def detect(self, file_path: str, content: str) -> list[DetectionResult]:
        """
        Detect empty exception handler patterns.

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

        # 1. Regex-based detection
        regex_results = self._regex_detect(
            file_path=file_path,
            content=content,
            message_template="Empty exception handler detected: {pattern}",
        )

        for result in regex_results:
            if context_analyzer.should_ignore(result.line_number, "empty_exception"):
                continue

            # Check if exception is being logged or documented
            if self._has_logging_or_comment(content, result.line_number):
                result.severity = SeverityLevel.INFO
                result.message = "Exception handler with logging/comment"

            modifier = context_analyzer.get_confidence_modifier(result.line_number)
            result.confidence *= modifier

            if result.confidence >= self.config.min_confidence:
                results.append(result)

        # 2. AST-based detection for Python files
        if file_path.endswith(".py"):
            ast_results = await self._ast_detect(file_path, content, context_analyzer)
            results.extend(ast_results)

        # 3. Detect bare except (without specific exception type)
        bare_except_results = self._detect_bare_except(file_path, content)
        results.extend(bare_except_results)

        return self._deduplicate(results)

    async def _ast_detect(
        self, file_path: str, content: str, context_analyzer: ContextAnalyzer
    ) -> list[DetectionResult]:
        """
        Perform AST-based detection for empty exception handlers.

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

            for match in ast_analyzer.find_empty_except_handlers():
                if context_analyzer.should_ignore(match.line_number, "empty_exception"):
                    continue

                confidence = (
                    match.confidence
                    * context_analyzer.get_confidence_modifier(match.line_number)
                )

                if confidence >= self.config.min_confidence:
                    results.append(
                        self._create_result(
                            file_path=file_path,
                            line_number=match.line_number,
                            code_snippet=match.code,
                            message=f"AST analysis: {match.message}",
                            confidence=confidence,
                            column_number=match.column,
                        )
                    )

        except ASTParseError as hata:
            # 30 Tem 2026 (bandit B110): bekcinin KENDISI sessizce yutuyordu.
            # Parse hatasi normaldir (kismi/bozuk dosya) ama GORUNMEZ olmamali:
            # AST yolu duserse tespit sessizce zayiflar ve kimse fark etmez.
            print(f"Warning: {self.name} AST parse edemedi {file_path}: {hata}")
        except Exception as hata:
            print(f"Warning: {self.name} AST analizi basarisiz {file_path}: {hata}")

        return results

    def _has_logging_or_comment(self, content: str, line_number: int) -> bool:
        """
        Check if exception handler has logging or explanatory comment.

        Args:
            content: File content
            line_number: Line number of except clause

        Returns:
            True if logging or comment present
        """
        lines = content.split("\n")

        # Look at 3 lines after the except
        start = line_number
        end = min(len(lines), line_number + 4)

        logging_patterns = [
            "logger.",
            "logging.",
            "log.",
            "print(",
            "# intentionally",
            "# silently",
            "# expected",
            "# ignore",
            "# suppress",
        ]

        for i in range(start, end):
            if i < len(lines):
                line_lower = lines[i].lower()
                if any(pattern in line_lower for pattern in logging_patterns):
                    return True

        return False

    def _detect_bare_except(
        self, file_path: str, content: str
    ) -> list[DetectionResult]:
        """
        Detect bare except: clauses without specific exception type.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult for bare excepts
        """
        import re

        results: list[DetectionResult] = []

        # Pattern for bare except (not followed by Exception type)
        pattern = r"^\s*except\s*:\s*$"

        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                # Fixture string'i icindeki bare except TEST VERISIDIR (30 Tem 2026).
                if satir_bastirilmali(file_path, content, i + 1, pattern):
                    continue
                results.append(
                    self._create_result(
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        message="Bare except: - use specific exception type",
                        confidence=0.95,
                    )
                )

        return results

    def _deduplicate(self, results: list[DetectionResult]) -> list[DetectionResult]:
        """Remove duplicate detections on the same line."""
        seen_lines: set = set()
        unique_results: list[DetectionResult] = []

        for result in results:
            key = (result.file_path, result.line_number)
            if key not in seen_lines:
                seen_lines.add(key)
                unique_results.append(result)

        return unique_results
