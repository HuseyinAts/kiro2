"""PostToolUse hook: Taxonomy validation after question edit.

Triggers on Edit/Write of question-related files.
Checks taxonomy consistency and warns if score is below threshold.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Backend services path
_backend_path = str(Path(__file__).resolve().parents[5] / "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

# Files that trigger validation
QUESTION_FILE_PATTERNS = [
    r".*soru.*\.py$",
    r".*question.*\.py$",
    r".*sorular.*\.json$",
]

CONSISTENCY_ALERT_THRESHOLD = 0.5


def should_validate(file_path: str) -> bool:
    """Check if file edit should trigger taxonomy validation."""
    return any(re.search(p, file_path, re.IGNORECASE) for p in QUESTION_FILE_PATTERNS)


def validate(file_path: str, content: str) -> dict:
    """Run taxonomy validation on edited content.

    Returns:
        dict with status, warnings, and suggestions.
    """
    if not should_validate(file_path):
        return {"status": "skipped", "reason": "not a question file"}

    # Extract question text from content (basic heuristic)
    question_text = _extract_question_text(content)
    if not question_text:
        return {"status": "skipped", "reason": "no question text found"}

    try:
        from services.taxonomy.multi_taxonomy_analyzer import analyze_all

        result = analyze_all(question_text)

        warnings = []
        if result.consistency_score < CONSISTENCY_ALERT_THRESHOLD:
            warnings.append(
                f"Taxonomy consistency score low: {result.consistency_score:.2f}"
            )
            for inc in result.inconsistencies:
                warnings.append(f"  - {inc}")

        return {
            "status": "validated",
            "consistency_score": round(result.consistency_score, 3),
            "warnings": warnings,
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def _extract_question_text(content: str) -> str:
    """Extract question text from Python/JSON content (heuristic)."""
    # Try JSON: look for "metin" or "question_text" keys
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data.get("metin", data.get("question_text", ""))
    except (json.JSONDecodeError, ValueError):
        pass

    # Try Python: look for string assignments
    patterns = [
        r'metin\s*=\s*["\'](.+?)["\']',
        r'question_text\s*=\s*["\'](.+?)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)

    return ""
