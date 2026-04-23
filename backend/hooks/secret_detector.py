#!/usr/bin/env python3
"""
KIRO2 Custom Secret Detector
Pre-commit hook for detecting hardcoded secrets

Exit Codes (Daisy Stanton Standards):
- 0: Success (no secrets found)
- 2: Blocking error (secrets detected - must fix before commit)

Usage:
    python backend/hooks/secret_detector.py [file1] [file2] ...

Or via pre-commit:
    - repo: local
      hooks:
        - id: kiro2-secret-detector
          name: KIRO2 Secret Detector
          entry: python backend/hooks/secret_detector.py
          language: system
          types: [python]
"""

import re
import sys
from pathlib import Path

# Secret patterns to detect
SECRET_PATTERNS: list[tuple[str, str]] = [
    # Anthropic API Keys
    (r'sk-ant-api\d+-[A-Za-z0-9_-]{20,}', 'Anthropic API Key'),

    # OpenAI API Keys
    (r'sk-proj-[A-Za-z0-9_-]{20,}', 'OpenAI Project Key'),
    (r'sk-[A-Za-z0-9]{48,}', 'OpenAI API Key'),

    # KIRO2 Specific Passwords
    (r'TeknoFest\d+SecurePass', 'KIRO2 Database Password'),
    (r'teknofest-\d+-super-secret[A-Za-z0-9_-]*', 'KIRO2 JWT Secret'),

    # HuggingFace Tokens
    (r'hf_[A-Za-z0-9]{34,}', 'HuggingFace Token'),

    # Google API Keys
    (r'AIza[A-Za-z0-9_-]{35}', 'Google API Key'),

    # Generic Patterns
    (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded Password'),
    (r'api_key\s*=\s*["\']sk-[^"\']+["\']', 'Hardcoded API Key'),
]

# Files to skip
ALLOWED_FILES = [
    '.env.example',
    'CLAUDE.md',
    '.secrets.baseline',
    'secret_detector.py',  # This file
    'SECRETS_MANAGEMENT.md',
]

# Directories to skip
SKIP_DIRS = [
    '__pycache__',
    '.git',
    'node_modules',
    '.venv',
    'venv',
]


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    # Skip allowed files
    if filepath.name in ALLOWED_FILES:
        return True

    # Skip directories
    for skip_dir in SKIP_DIRS:
        if skip_dir in filepath.parts:
            return True

    return False


def scan_file(filepath: Path) -> list[tuple[int, str, str]]:
    """
    Scan file for secrets.

    Returns:
        List of (line_number, secret_type, preview)
    """
    if should_skip_file(filepath):
        return []

    findings = []

    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Skip comment lines
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue

            for pattern, secret_type in SECRET_PATTERNS:
                if re.search(pattern, line):
                    # Truncate preview for security
                    preview = line[:60] + '...' if len(line) > 60 else line
                    findings.append((line_num, secret_type, preview))
                    break  # One finding per line is enough

    except Exception:
        # Silently skip files that can't be read
        pass

    return findings


def main() -> int:
    """Main entry point."""
    files = sys.argv[1:]

    if not files:
        print("Usage: python secret_detector.py <file1> [file2] ...")
        return 0

    has_secrets = False
    total_findings = 0

    for filepath_str in files:
        filepath = Path(filepath_str)

        if not filepath.exists():
            continue

        findings = scan_file(filepath)

        for line_num, secret_type, preview in findings:
            print(f"\n[SECRET DETECTED] {filepath}:{line_num}")
            print(f"  Type: {secret_type}")
            print(f"  Preview: {preview}")
            has_secrets = True
            total_findings += 1

    if has_secrets:
        print("\n" + "=" * 60)
        print(f"[ERROR] {total_findings} hardcoded secret(s) detected!")
        print("=" * 60)
        print("\nFix instructions:")
        print("1. Move secrets to .env file")
        print("2. Use os.getenv() or Settings class")
        print("3. Never commit secrets to git")
        print("\nExample:")
        print('  # BAD:  api_key = "sk-ant-api03-..."')
        print('  # GOOD: api_key = os.getenv("ANTHROPIC_API_KEY")')
        print("\nSee: docs/SECRETS_MANAGEMENT.md")
        return 2  # Exit code 2 = blocking error

    return 0


if __name__ == "__main__":
    sys.exit(main())
