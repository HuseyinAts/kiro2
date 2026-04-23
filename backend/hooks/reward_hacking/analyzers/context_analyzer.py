"""
Context Analyzer for false positive reduction.

Analyzes code context to determine if a pattern match is legitimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContextType(str, Enum):
    """Types of code context."""
    COMMENT = "comment"
    DOCSTRING = "docstring"
    STRING_LITERAL = "string_literal"
    TEST_FILE = "test_file"
    EXAMPLE_CODE = "example_code"
    PRODUCTION_CODE = "production_code"


@dataclass
class ContextInfo:
    """Information about code context at a specific location."""
    context_type: ContextType
    is_in_docstring: bool
    is_in_comment: bool
    is_in_string: bool
    is_test_file: bool
    surrounding_code: str
    function_name: str | None = None
    class_name: str | None = None


class ContextAnalyzer:
    """
    Analyzes code context for false positive reduction.

    Determines if a pattern match is in a legitimate context
    where it should not be flagged as reward hacking.
    """

    # Keywords that indicate legitimate use
    LEGITIMATE_KEYWORDS: set[str] = {
        'example', 'demo', 'tutorial', 'documentation',
        'doc', 'docstring', 'comment', 'note', 'warning',
        'fixme', 'todo', 'hack', 'workaround'
    }

    # Test file patterns
    TEST_FILE_PATTERNS: set[str] = {
        'test_', '_test.py', 'tests/', 'test/', 'spec_',
        '_spec.py', 'conftest.py'
    }

    def __init__(self, content: str, file_path: str = ""):
        """
        Initialize context analyzer.

        Args:
            content: File content as string
            file_path: Path to the file
        """
        self.content = content
        self.file_path = file_path
        self._lines = content.split('\n')
        self._is_test_file = self._detect_test_file()

    def _detect_test_file(self) -> bool:
        """Determine if this is a test file."""
        file_lower = self.file_path.lower()
        return any(pattern in file_lower for pattern in self.TEST_FILE_PATTERNS)

    def get_context(self, line_number: int) -> ContextInfo:
        """
        Get context information for a specific line.

        Args:
            line_number: 1-indexed line number

        Returns:
            ContextInfo object describing the context
        """
        if line_number < 1 or line_number > len(self._lines):
            return ContextInfo(
                context_type=ContextType.PRODUCTION_CODE,
                is_in_docstring=False,
                is_in_comment=False,
                is_in_string=False,
                is_test_file=self._is_test_file,
                surrounding_code=""
            )

        line = self._lines[line_number - 1]

        # Check if in docstring
        is_in_docstring = self._is_in_docstring(line_number)

        # Check if in comment
        is_in_comment = self._is_in_comment(line)

        # Check if in string literal
        is_in_string = self._is_in_string(line_number)

        # Get surrounding code (3 lines before and after)
        start = max(0, line_number - 4)
        end = min(len(self._lines), line_number + 3)
        surrounding_code = '\n'.join(self._lines[start:end])

        # Determine context type
        if is_in_docstring:
            context_type = ContextType.DOCSTRING
        elif is_in_comment:
            context_type = ContextType.COMMENT
        elif is_in_string:
            context_type = ContextType.STRING_LITERAL
        elif self._is_test_file:
            context_type = ContextType.TEST_FILE
        else:
            context_type = ContextType.PRODUCTION_CODE

        # Get function and class names
        function_name, class_name = self._get_enclosing_scope(line_number)

        return ContextInfo(
            context_type=context_type,
            is_in_docstring=is_in_docstring,
            is_in_comment=is_in_comment,
            is_in_string=is_in_string,
            is_test_file=self._is_test_file,
            surrounding_code=surrounding_code,
            function_name=function_name,
            class_name=class_name
        )

    def _is_in_docstring(self, line_number: int) -> bool:
        """Check if line is inside a docstring."""
        in_docstring = False
        docstring_char = None

        for i, line in enumerate(self._lines[:line_number], 1):
            # Check for docstring markers
            if '"""' in line:
                count = line.count('"""')
                if count == 2 and i == line_number:
                    # Single line docstring on current line
                    return True
                if count % 2 == 1:
                    in_docstring = not in_docstring
                    docstring_char = '"""'
            elif "'''" in line:
                count = line.count("'''")
                if count == 2 and i == line_number:
                    return True
                if count % 2 == 1:
                    in_docstring = not in_docstring
                    docstring_char = "'''"

        return in_docstring

    def _is_in_comment(self, line: str) -> bool:
        """Check if the main content of line is a comment."""
        stripped = line.strip()
        return stripped.startswith('#')

    def _is_in_string(self, line_number: int) -> bool:
        """Check if line is inside a multi-line string."""
        # Simplified check - looks for unclosed quotes
        line = self._lines[line_number - 1]
        single_quotes = line.count("'") - line.count("\\'")
        double_quotes = line.count('"') - line.count('\\"')

        # If odd number of quotes, might be in string
        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)

    def _get_enclosing_scope(self, line_number: int) -> tuple[str | None, str | None]:
        """Get the function and class names that enclose this line."""
        function_name = None
        class_name = None

        # Simple heuristic - look backwards for def/class
        for i in range(line_number - 1, -1, -1):
            line = self._lines[i].strip()

            if line.startswith('def ') and function_name is None:
                # Extract function name
                parts = line[4:].split('(')
                if parts:
                    function_name = parts[0].strip()

            if line.startswith('class ') and class_name is None:
                # Extract class name
                parts = line[6:].split('(')
                if not parts:
                    parts = line[6:].split(':')
                if parts:
                    class_name = parts[0].strip()

            if function_name and class_name:
                break

        return function_name, class_name

    def should_ignore(self, line_number: int, pattern_type: str) -> bool:
        """
        Determine if a match at this location should be ignored.

        Args:
            line_number: Line number of the match
            pattern_type: Type of pattern matched

        Returns:
            True if the match should be ignored (is legitimate)
        """
        context = self.get_context(line_number)

        # Always ignore matches in docstrings
        if context.is_in_docstring:
            return True

        # Ignore matches in comments (except for TODO/FIXME patterns)
        if context.is_in_comment and pattern_type != 'placeholder':
            return True

        # Check for legitimate keywords in surrounding code
        surrounding_lower = context.surrounding_code.lower()
        if any(keyword in surrounding_lower for keyword in self.LEGITIMATE_KEYWORDS):
            # This might be example/documentation code
            if context.is_in_docstring or 'example' in surrounding_lower:
                return True

        return False

    def get_confidence_modifier(self, line_number: int) -> float:
        """
        Get a confidence modifier based on context.

        Lower values mean the detection is less certain.

        Args:
            line_number: Line number of the match

        Returns:
            Confidence modifier (0.0 to 1.0)
        """
        context = self.get_context(line_number)

        # In docstring - very low confidence
        if context.is_in_docstring:
            return 0.1

        # In comment - low confidence
        if context.is_in_comment:
            return 0.3

        # In test file - normal confidence
        if context.is_test_file:
            return 1.0

        # Production code - high confidence
        return 1.0
