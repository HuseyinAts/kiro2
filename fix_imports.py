#!/usr/bin/env python
"""Fix all 'from backend.' imports to direct imports"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Replace 'from backend.' with 'from ' in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace 'from backend.' with 'from '
        new_content = re.sub(r'from backend\.', 'from ', content)

        # Only write if changed
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

def main():
    backend_dir = Path('backend')
    fixed_count = 0
    total_files = 0

    # Process all .py files
    for py_file in backend_dir.rglob('*.py'):
        total_files += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
            print(f"Fixed: {py_file}")

    print(f"\n✅ Fixed {fixed_count} files out of {total_files} total files")

if __name__ == '__main__':
    main()
