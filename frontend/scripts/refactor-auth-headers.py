#!/usr/bin/env python3
"""
Automatic Auth Header Refactoring Script
Converts manual Authorization headers to getAuthHeaders() calls in api.ts

Usage: python refactor-auth-headers.py
"""

import re
import sys
from pathlib import Path

def refactor_auth_headers(file_path: Path) -> tuple[int, list[str]]:
    """
    Refactor manual Authorization headers to use getAuthHeaders()

    Returns:
        tuple: (number_of_changes, list_of_changed_functions)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = []
    change_count = 0

    # Pattern 1: headers with Authorization only (single quotes)
    pattern1 = re.compile(
        r"headers:\s*\{\s*'Authorization':\s*`Bearer\s*\$\{localStorage\.getItem\('access_token'\)\}`\s*\}",
        re.MULTILINE | re.DOTALL
    )
    matches1 = pattern1.findall(content)
    content = pattern1.sub("headers: getAuthHeaders()", content)
    change_count += len(matches1)

    # Pattern 2: Content-Type first, then Authorization (multiline)
    pattern2 = re.compile(
        r"headers:\s*\{\s*\n?\s*'Content-Type':\s*'application/json',\s*\n?\s*'Authorization':\s*`Bearer\s*\$\{localStorage\.getItem\('access_token'\)\}`,?\s*\n?\s*\}",
        re.MULTILINE | re.DOTALL
    )
    matches2 = pattern2.findall(content)
    content = pattern2.sub("headers: getAuthHeaders({ 'Content-Type': 'application/json' })", content)
    change_count += len(matches2)

    # Pattern 3: Authorization first, then Content-Type
    pattern3 = re.compile(
        r"headers:\s*\{\s*\n?\s*'Authorization':\s*`Bearer\s*\$\{localStorage\.getItem\('access_token'\)\}`,\s*\n?\s*'Content-Type':\s*'application/json',?\s*\n?\s*\}",
        re.MULTILINE | re.DOTALL
    )
    matches3 = pattern3.findall(content)
    content = pattern3.sub("headers: getAuthHeaders({ 'Content-Type': 'application/json' })", content)
    change_count += len(matches3)

    # Pattern 4: Only Authorization (no Content-Type) - multiline
    pattern4 = re.compile(
        r"headers:\s*\{\s*\n\s*'Authorization':\s*`Bearer\s*\$\{localStorage\.getItem\('access_token'\)\}`,?\s*\n\s*\}",
        re.MULTILINE | re.DOTALL
    )
    matches4 = pattern4.findall(content)
    content = pattern4.sub("headers: getAuthHeaders()", content)
    change_count += len(matches4)

    if content != original_content:
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[+] Refactored {change_count} auth headers in {file_path.name}")
        return change_count, changes
    else:
        print(f"[i] No changes needed in {file_path.name}")
        return 0, []

def main():
    # Get api.ts path
    script_dir = Path(__file__).parent
    api_file = script_dir.parent / 'src' / 'api.ts'

    if not api_file.exists():
        print(f"[ERROR] {api_file} not found!")
        sys.exit(1)

    print("[*] Starting automatic auth header refactoring...")
    print(f"[*] Target file: {api_file}")
    print()

    # Backup original file
    backup_file = api_file.with_suffix('.ts.backup')
    import shutil
    shutil.copy2(api_file, backup_file)
    print(f"[*] Backup created: {backup_file}")
    print()

    # Perform refactoring
    count, functions = refactor_auth_headers(api_file)

    print()
    print("=" * 60)
    print(f"[+] Refactoring complete! Changed {count} occurrences.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review changes: diff src/api.ts src/api.ts.backup")
    print("2. Test: npm run type-check")
    print("3. If good, delete backup: rm src/api.ts.backup")
    print("4. If bad, restore: mv src/api.ts.backup src/api.ts")

    return 0

if __name__ == '__main__':
    sys.exit(main())
