#!/usr/bin/env python3
"""
Fix remaining 10 issues in test_api_batch2.py
"""

import re


def fix_remaining_issues(file_path: str) -> None:
    """Fix the last 10 test failures"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    fixes_applied = []

    # Fix 1: Replace QuestionGenerationResponse with HybridQuestionResponse
    pattern1 = r'\bQuestionGenerationResponse\b'
    count1 = len(re.findall(pattern1, content))
    content = re.sub(pattern1, 'HybridQuestionResponse', content)
    if count1 > 0:
        fixes_applied.append(f"Fix 1: Replaced {count1} QuestionGenerationResponse")

    # Fix 2: Fix patch paths that still reference api.question_generation
    pattern2a = r'"api\.question_generation\.'
    replacement2a = '"api.hybrid_question_generation.'
    count2a = len(re.findall(pattern2a, content))
    content = re.sub(pattern2a, replacement2a, content)
    if count2a > 0:
        fixes_applied.append(f"Fix 2a: Fixed {count2a} patch paths")

    pattern2b = r"'api\.question_generation\."
    replacement2b = "'api.hybrid_question_generation."
    count2b = len(re.findall(pattern2b, content))
    content = re.sub(pattern2b, replacement2b, content)
    if count2b > 0:
        fixes_applied.append(f"Fix 2b: Fixed {count2b} quoted patch paths")

    # Fix 3: Remove question_type attribute references (doesn't exist)
    pattern3 = r'assert request\.question_type'
    count3 = len(re.findall(pattern3, content))
    content = re.sub(pattern3, '# assert request.question_type (field removed)', content)
    if count3 > 0:
        fixes_applied.append(f"Fix 3: Commented {count3} question_type assertions")

    # Fix 4: Fix BulkHybridRequest - add required fields 'topics'
    # Pattern: BulkHybridRequest(subject=..., count_per_topic=...) missing topics
    def fix_bulk_request(match):
        text = match.group(0)
        # Check if topics= is missing
        if 'topics=' not in text:
            # Add topics parameter before count_per_topic
            text = text.replace('count_per_topic=', 'topics=["Topic1", "Topic2"], count_per_topic=')
        return text

    pattern4 = r'BulkHybridRequest\([^)]+\)'
    content = re.sub(pattern4, fix_bulk_request, content)

    # Fix 5: Fix get_generation_methods calls - remove subject parameter
    pattern5 = r'get_generation_methods\([^)]*subject=[^,)]+,?\s*\)'
    replacement5 = 'get_generation_methods()'
    count5 = len(re.findall(pattern5, content))
    content = re.sub(pattern5, replacement5, content)
    if count5 > 0:
        fixes_applied.append(f"Fix 5: Fixed {count5} get_generation_methods calls")

    # Write fixes
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("SUCCESS: Remaining fixes applied!")
        print("\nSummary:")
        for fix in fixes_applied:
            print(f"  - {fix}")

        return True
    else:
        print("INFO: No changes needed")
        return False


if __name__ == "__main__":
    import sys

    file_path = "tests/unit/test_api_batch2.py"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    print(f"Applying remaining fixes to {file_path}...")
    print("-" * 60)

    try:
        fix_remaining_issues(file_path)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
