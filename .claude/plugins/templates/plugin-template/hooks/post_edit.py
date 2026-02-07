#!/usr/bin/env python3
"""
PostToolUse Hook Handler

Edit/Write tool kullanımından sonra çalışır.
Dosya validasyonu ve kalite kontrolü yapar.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_hook(event_data: dict) -> int:
    """
    PostToolUse hook handler.

    Args:
        event_data: Hook event data containing:
            - tool_name: "Edit" or "Write"
            - file_path: Modified file path
            - content: File content (for Write)
            - old_string: Replaced text (for Edit)
            - new_string: New text (for Edit)

    Returns:
        Exit code:
            0 = Success, continue
            2 = Blocking error, stop and report to Claude
            Other = Warning, show to user but continue
    """
    tool_name = event_data.get("tool_name", "")
    file_path = event_data.get("file_path", "")

    logger.info(f"PostToolUse hook: {tool_name} on {file_path}")

    if not file_path:
        return 0

    path = Path(file_path)

    # Python file checks
    if path.suffix == ".py":
        return validate_python_file(path, event_data)

    # TypeScript/JavaScript checks
    if path.suffix in (".ts", ".tsx", ".js", ".jsx"):
        return validate_typescript_file(path, event_data)

    # YAML checks
    if path.suffix in (".yaml", ".yml"):
        return validate_yaml_file(path, event_data)

    # JSON checks
    if path.suffix == ".json":
        return validate_json_file(path, event_data)

    return 0


def validate_python_file(path: Path, event_data: dict) -> int:
    """
    Python dosyası validasyonu.

    Kontroller:
    - Syntax hatası yok mu?
    - Reward hacking pattern yok mu?
    - Type hints var mı?
    """
    new_string = event_data.get("new_string", "")
    content = event_data.get("content", "")

    text = new_string or content

    # Reward hacking pattern kontrolü
    reward_hacking_patterns = [
        "assert True",
        "assert true",
        "ASSERT_TRUE(true)",
        "pass # placeholder",
        "return None # stub",
        "# pragma: no cover",
    ]

    for pattern in reward_hacking_patterns:
        if pattern in text:
            logger.error(f"Reward hacking pattern detected: {pattern}")
            print(json.dumps({
                "error": "Reward hacking pattern detected",
                "pattern": pattern,
                "file": str(path),
                "action": "Remove the pattern and implement properly"
            }))
            return 2  # Blocking error

    # Syntax check (basic)
    try:
        compile(text, str(path), "exec")
    except SyntaxError as e:
        logger.error(f"Syntax error: {e}")
        print(json.dumps({
            "error": "Python syntax error",
            "details": str(e),
            "file": str(path)
        }))
        return 2  # Blocking error

    logger.info(f"Python file validated: {path}")
    return 0


def validate_typescript_file(path: Path, event_data: dict) -> int:
    """
    TypeScript/JavaScript dosyası validasyonu.

    Kontroller:
    - Reward hacking pattern yok mu?
    - Console.log var mı? (warning)
    """
    new_string = event_data.get("new_string", "")
    content = event_data.get("content", "")

    text = new_string or content

    # Reward hacking patterns
    if "expect(true).toBe(true)" in text:
        logger.error("Reward hacking pattern detected")
        print(json.dumps({
            "error": "Reward hacking pattern detected",
            "pattern": "expect(true).toBe(true)",
            "file": str(path)
        }))
        return 2

    # Console.log warning
    if "console.log" in text:
        logger.warning("console.log found - consider removing for production")
        print(json.dumps({
            "warning": "console.log found",
            "file": str(path),
            "action": "Consider removing for production"
        }))
        return 1  # Warning

    return 0


def validate_yaml_file(path: Path, event_data: dict) -> int:
    """YAML dosyası validasyonu."""
    try:
        import yaml

        content = event_data.get("content", "")
        if content:
            yaml.safe_load(content)

    except Exception as e:
        logger.error(f"YAML parse error: {e}")
        print(json.dumps({
            "error": "Invalid YAML syntax",
            "details": str(e),
            "file": str(path)
        }))
        return 2

    return 0


def validate_json_file(path: Path, event_data: dict) -> int:
    """JSON dosyası validasyonu."""
    try:
        content = event_data.get("content", "")
        if content:
            json.loads(content)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        print(json.dumps({
            "error": "Invalid JSON syntax",
            "details": str(e),
            "file": str(path)
        }))
        return 2

    return 0


if __name__ == "__main__":
    # Read event data from stdin
    try:
        event_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        event_data = {}

    exit_code = handle_hook(event_data)
    sys.exit(exit_code)
