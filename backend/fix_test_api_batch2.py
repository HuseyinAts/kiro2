#!/usr/bin/env python3
"""
Fix test_api_batch2.py - Comprehensive Fixer
Fixes:
1. api.question_generation -> api.hybrid_question_generation
2. api.monitoring.cache_manager -> core.cache.cache_manager
3. api.monitoring.LogAnalyzer -> core.logging_config.LogAnalyzer
4. ReviewFlashcardRequest validation (response_time_ms is required)
"""

import re
import sys


def fix_test_file(file_path: str) -> None:
    """Fix all issues in test_api_batch2.py"""

    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    original_content = content
    fixes_applied = []

    # Fix 1: Replace api.question_generation with api.hybrid_question_generation
    pattern1 = r'from api\.question_generation import'
    replacement1 = 'from api.hybrid_question_generation import'
    count1 = len(re.findall(pattern1, content))
    content = re.sub(pattern1, replacement1, content)
    if count1 > 0:
        fixes_applied.append(f"Fix 1: Replaced {count1} occurrences of 'from api.question_generation import'")

    pattern1b = r'import api\.question_generation'
    replacement1b = 'import api.hybrid_question_generation'
    count1b = len(re.findall(pattern1b, content))
    content = re.sub(pattern1b, replacement1b, content)
    if count1b > 0:
        fixes_applied.append(f"Fix 1b: Replaced {count1b} occurrences of 'import api.question_generation'")

    # Fix 1c: Replace 'from api import question_generation' with 'from api import hybrid_question_generation as question_generation'
    pattern1c = r'from api import question_generation\b'
    replacement1c = 'from api import hybrid_question_generation as question_generation'
    count1c = len(re.findall(pattern1c, content))
    content = re.sub(pattern1c, replacement1c, content)
    if count1c > 0:
        fixes_applied.append(f"Fix 1c: Replaced {count1c} occurrences of 'from api import question_generation'")

    # Fix 2: Replace api.monitoring.cache_manager with core.cache.cache_manager
    pattern2 = r'"api\.monitoring\.cache_manager'
    replacement2 = '"core.cache.cache_manager'
    count2 = len(re.findall(pattern2, content))
    content = re.sub(pattern2, replacement2, content)
    if count2 > 0:
        fixes_applied.append(f"Fix 2: Replaced {count2} occurrences of 'api.monitoring.cache_manager' patch paths")

    # Fix 3: Replace api.monitoring.LogAnalyzer with core.logging_config.LogAnalyzer
    pattern3 = r'"api\.monitoring\.LogAnalyzer"'
    replacement3 = '"core.logging_config.LogAnalyzer"'
    count3 = len(re.findall(pattern3, content))
    content = re.sub(pattern3, replacement3, content)
    if count3 > 0:
        fixes_applied.append(f"Fix 3: Replaced {count3} occurrences of 'api.monitoring.LogAnalyzer' patch paths")

    # Fix 4: Add response_time_ms to ReviewFlashcardRequest calls that are missing it
    # Pattern: ReviewFlashcardRequest(grade=X) without response_time_ms
    def add_response_time(match):
        grade = match.group(1)
        return f'ReviewFlashcardRequest(grade={grade}, response_time_ms=5000)'

    pattern4 = r'ReviewFlashcardRequest\(grade=(\d+)\)(?!\s*,\s*response_time_ms)'
    matches4 = re.findall(pattern4, content)
    content = re.sub(pattern4, add_response_time, content)
    if matches4:
        fixes_applied.append(f"Fix 4: Added response_time_ms to {len(matches4)} ReviewFlashcardRequest calls")

    # Fix 5: Fix analytics endpoint mocking to handle 500 errors properly
    # The analytics endpoints may return 500 if helper functions aren't mocked
    # This is handled by the existing patches, but we need to ensure they're comprehensive

    # Write the fixed content
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("SUCCESS: Fixes applied successfully!")
        print("\nSummary:")
        for fix in fixes_applied:
            print(f"  - {fix}")

        return True
    print("INFO: No changes needed - file is already correct")
    return False


if __name__ == "__main__":
    file_path = "tests/unit/test_api_batch2.py"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    print(f"Fixing {file_path}...")
    print("-" * 60)

    try:
        fix_test_file(file_path)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
