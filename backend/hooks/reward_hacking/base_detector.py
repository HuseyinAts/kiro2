"""
Base Detector abstract class for Reward Hacking Prevention.

All detectors inherit from this class and implement the detect() method.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List, Optional

from .models.enums import SeverityLevel, PatternType
from .models.detection_result import DetectionResult, DetectorConfig
from .config.patterns import REMEDIATION_SUGGESTIONS


class BaseDetector(ABC):
    """
    Abstract base class for reward hacking pattern detectors.

    All detectors must implement:
    - detect(): Main detection method
    - get_patterns(): Returns regex patterns for this detector
    - pattern_type: Class attribute for pattern type
    - default_severity: Class attribute for default severity
    """

    # Subclasses must define these
    pattern_type: PatternType
    default_severity: SeverityLevel = SeverityLevel.CRITICAL
    name: str = "BaseDetector"

    def __init__(self, config: Optional[DetectorConfig] = None):
        """
        Initialize detector with optional configuration.

        Args:
            config: Optional detector configuration. If not provided,
                   default configuration will be used.
        """
        self.config = config or DetectorConfig()
        self._compiled_patterns: List[re.Pattern] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        all_patterns = self.get_patterns()
        if self.config.patterns:
            all_patterns.extend(self.config.patterns)

        self._compiled_patterns = []
        for pattern in all_patterns:
            try:
                self._compiled_patterns.append(
                    re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                )
            except re.error:
                # Skip invalid patterns
                continue

    @abstractmethod
    def get_patterns(self) -> List[str]:
        """
        Get regex patterns for this detector.

        Returns:
            List of regex pattern strings
        """
        pass

    @abstractmethod
    async def detect(
        self,
        file_path: str,
        content: str
    ) -> List[DetectionResult]:
        """
        Detect reward hacking patterns in file content.

        Args:
            file_path: Path to the file being analyzed
            content: File content as string

        Returns:
            List of DetectionResult objects for each detection
        """
        pass

    def _is_in_exception(self, line: str, line_num: int, content: str) -> bool:
        """
        Check if match is a legitimate exception (false positive reduction).

        Args:
            line: The line containing the match
            line_num: Line number in the file
            content: Full file content

        Returns:
            True if this is a legitimate use (should be ignored)
        """
        # Skip comments
        stripped = line.strip()
        if stripped.startswith('#') and 'assert' not in stripped.lower():
            return True

        # Skip docstrings
        lines = content.split('\n')
        in_docstring = False
        for i, l in enumerate(lines):
            if '"""' in l or "'''" in l:
                in_docstring = not in_docstring
            if i == line_num - 1 and in_docstring:
                return True

        return False

    def _get_remediation(self) -> str:
        """Get remediation suggestion for this pattern type."""
        return REMEDIATION_SUGGESTIONS.get(
            self.pattern_type.value,
            "Review and fix the detected pattern."
        )

    def _create_result(
        self,
        file_path: str,
        line_number: int,
        code_snippet: str,
        message: str,
        confidence: float = 0.95,
        column_number: Optional[int] = None
    ) -> DetectionResult:
        """
        Create a DetectionResult object.

        Args:
            file_path: Path to file with issue
            line_number: Line number of issue
            code_snippet: Code snippet showing the issue
            message: Human-readable message
            confidence: Detection confidence (0.0-1.0)
            column_number: Optional column number

        Returns:
            DetectionResult object
        """
        severity = self.config.severity if self.config else self.default_severity

        return DetectionResult(
            detector_name=self.name,
            pattern_type=self.pattern_type,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_snippet.strip(),
            message=message,
            remediation=self._get_remediation(),
            confidence=confidence,
        )

    def _regex_detect(
        self,
        file_path: str,
        content: str,
        message_template: str
    ) -> List[DetectionResult]:
        """
        Perform regex-based detection using compiled patterns.

        Args:
            file_path: Path to file being analyzed
            content: File content
            message_template: Message template with {pattern} placeholder

        Returns:
            List of DetectionResult objects
        """
        results: List[DetectionResult] = []

        for pattern in self._compiled_patterns:
            for match in pattern.finditer(content):
                # Calculate line number
                line_num = content[:match.start()].count('\n') + 1

                # Get the line content
                lines = content.split('\n')
                if line_num <= len(lines):
                    line_content = lines[line_num - 1]
                else:
                    line_content = match.group(0)

                # Check for false positives
                if self._is_in_exception(line_content, line_num, content):
                    continue

                # Skip if below confidence threshold
                if self.config.min_confidence > 0.9:
                    continue

                results.append(self._create_result(
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content,
                    message=message_template.format(pattern=pattern.pattern),
                    confidence=0.95,
                    column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
                ))

        return results

    def is_enabled(self) -> bool:
        """Check if detector is enabled."""
        return self.config.enabled if self.config else True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(pattern_type={self.pattern_type}, enabled={self.is_enabled()})>"
