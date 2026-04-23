"""
Regex-based analyzer for pattern matching.

Provides efficient regex pattern matching with compiled patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern

from ..config.patterns import LEGITIMATE_EXCEPTIONS, REWARD_HACKING_PATTERNS


@dataclass
class RegexMatch:
    """Result of a regex pattern match."""
    pattern_type: str
    pattern: str
    line_number: int
    column: int
    matched_text: str
    line_content: str
    confidence: float = 0.95


class RegexAnalyzer:
    """
    Regex-based pattern analyzer.

    Compiles and caches patterns for efficient matching.
    """

    def __init__(self):
        """Initialize regex analyzer with compiled patterns."""
        self._compiled_patterns: dict[str, list[Pattern]] = {}
        self._compiled_exceptions: dict[str, list[Pattern]] = {}
        self._compile_all_patterns()

    def _compile_all_patterns(self) -> None:
        """Compile all patterns at initialization."""
        # Compile detection patterns
        for pattern_type, patterns in REWARD_HACKING_PATTERNS.items():
            self._compiled_patterns[pattern_type] = []
            for pattern in patterns:
                try:
                    compiled = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                    self._compiled_patterns[pattern_type].append(compiled)
                except re.error:
                    continue

        # Compile exception patterns
        for pattern_type, patterns in LEGITIMATE_EXCEPTIONS.items():
            self._compiled_exceptions[pattern_type] = []
            for pattern in patterns:
                try:
                    compiled = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                    self._compiled_exceptions[pattern_type].append(compiled)
                except re.error:
                    continue

    def find_patterns(
        self,
        content: str,
        pattern_type: str
    ) -> list[RegexMatch]:
        """
        Find all matches of a specific pattern type in content.

        Args:
            content: Text content to search
            pattern_type: Type of pattern to search for

        Returns:
            List of RegexMatch objects
        """
        if pattern_type not in self._compiled_patterns:
            return []

        results: list[RegexMatch] = []
        lines = content.split('\n')

        for pattern in self._compiled_patterns[pattern_type]:
            for match in pattern.finditer(content):
                # Calculate line number
                line_num = content[:match.start()].count('\n') + 1

                # Get line content
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                # Calculate column
                line_start = content.rfind('\n', 0, match.start()) + 1
                column = match.start() - line_start

                # Check for exceptions
                if self._is_exception(line_content, pattern_type):
                    continue

                results.append(RegexMatch(
                    pattern_type=pattern_type,
                    pattern=pattern.pattern,
                    line_number=line_num,
                    column=column,
                    matched_text=match.group(0),
                    line_content=line_content,
                    confidence=0.95
                ))

        return results

    def find_all_patterns(self, content: str) -> dict[str, list[RegexMatch]]:
        """
        Find all patterns of all types in content.

        Args:
            content: Text content to search

        Returns:
            Dictionary mapping pattern type to list of matches
        """
        results: dict[str, list[RegexMatch]] = {}

        for pattern_type in self._compiled_patterns:
            matches = self.find_patterns(content, pattern_type)
            if matches:
                results[pattern_type] = matches

        return results

    def _is_exception(self, line: str, pattern_type: str) -> bool:
        """
        Check if line matches a legitimate exception pattern.

        Args:
            line: Line content to check
            pattern_type: Type of pattern being matched

        Returns:
            True if this is a legitimate exception
        """
        if pattern_type not in self._compiled_exceptions:
            return False

        for pattern in self._compiled_exceptions[pattern_type]:
            if pattern.search(line):
                return True

        return False

    def has_pattern(self, content: str, pattern_type: str) -> bool:
        """
        Quick check if content contains any pattern of given type.

        Args:
            content: Text content to search
            pattern_type: Type of pattern to search for

        Returns:
            True if any pattern matches
        """
        if pattern_type not in self._compiled_patterns:
            return False

        for pattern in self._compiled_patterns[pattern_type]:
            if pattern.search(content):
                return True

        return False

    def count_patterns(self, content: str, pattern_type: str) -> int:
        """
        Count occurrences of a pattern type.

        Args:
            content: Text content to search
            pattern_type: Type of pattern to count

        Returns:
            Number of matches
        """
        return len(self.find_patterns(content, pattern_type))

    @staticmethod
    def compile_custom_pattern(pattern: str) -> Pattern | None:
        """
        Compile a custom pattern.

        Args:
            pattern: Regex pattern string

        Returns:
            Compiled pattern or None if invalid
        """
        try:
            return re.compile(pattern, re.MULTILINE | re.IGNORECASE)
        except re.error:
            return None
