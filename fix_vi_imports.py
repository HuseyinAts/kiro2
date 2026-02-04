#!/usr/bin/env python3
"""
Fix missing vi imports in test files
Adds 'import { vi } from 'vitest'' to test files that use vi but don't import it
"""

import os
import re
from pathlib import Path

def needs_vi_import(content):
    """Check if file uses vi but doesn't import it"""
    has_vi_usage = re.search(r'\bvi\.', content)
    has_vi_import = re.search(r'import.*\bvi\b.*from.*[\'"]vitest[\'"]', content)
    return has_vi_usage and not has_vi_import

def add_vi_import(content):
    """Add vi import after other imports"""
    # Find the last import statement
    import_pattern = r'^import\s+.*from\s+[\'"].*[\'"];?\s*$'
    lines = content.split('\n')

    last_import_index = -1
    for i, line in enumerate(lines):
        if re.match(import_pattern, line.strip()):
            last_import_index = i

    if last_import_index >= 0:
        # Insert after last import
        lines.insert(last_import_index + 1, "import { vi } from 'vitest';")
        return '\n'.join(lines)
    else:
        # No imports found, add at top after initial comments
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('/*'):
                lines.insert(i, "import { vi } from 'vitest';")
                return '\n'.join(lines)

    return content

def fix_test_file(filepath):
    """Fix a single test file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if needs_vi_import(content):
            fixed_content = add_vi_import(content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    frontend_dir = Path('frontend/src')
    fixed_count = 0
    checked_count = 0

    print("Scanning test files for missing vi imports...")

    for test_file in frontend_dir.rglob('*.test.ts*'):
        checked_count += 1
        if fix_test_file(test_file):
            print(f"Fixed: {test_file}")
            fixed_count += 1

    print(f"\nSummary:")
    print(f"   Checked: {checked_count} test files")
    print(f"   Fixed: {fixed_count} files")
    print(f"   Done!")

if __name__ == '__main__':
    main()
