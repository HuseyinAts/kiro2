"""
Automated Timezone-Naive DateTime Fix Script

CRITICAL: This script fixes 500+ files with timezone-naive datetime usage.

Fixes applied:
1. datetime.now() → datetime.now(timezone.utc)
2. datetime.now(timezone.utc) → datetime.now(timezone.utc)  # Deprecated in Python 3.12+
3. Adds timezone import if missing

Usage:
    python backend/fix_timezone_naive_datetime.py [--dry-run]

Options:
    --dry-run: Show what would be changed without modifying files
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class TimezoneFixer:
    """Automated timezone-naive datetime fixer"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.files_processed = 0
        self.files_modified = 0
        self.total_fixes = 0

    def fix_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Fix a single file

        Returns:
            (was_modified, number_of_fixes)
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            fixes_in_file = 0

            # Check if file uses datetime
            if 'datetime' not in content:
                return False, 0

            # Pattern 1: datetime.now() → datetime.now(timezone.utc)
            # But NOT datetime.now(timezone.utc) (already fixed)
            pattern1 = r'datetime\.now\(\)(?!\s*#\s*TIMEZONE)'
            if re.search(pattern1, content):
                # Check if it's in Field(default_factory=datetime.now)
                if 'Field(default_factory=datetime.now)' in content:
                    content = content.replace(
                        'Field(default_factory=datetime.now)',
                        'Field(default_factory=lambda: datetime.now(timezone.utc))'
                    )
                    fixes_in_file += content.count('Field(default_factory=lambda: datetime.now(timezone.utc))') - \
                                     original_content.count('Field(default_factory=lambda: datetime.now(timezone.utc))')

                # Regular datetime.now() calls
                content = re.sub(
                    r'datetime\.now\(\)(?!\s*#)',
                    'datetime.now(timezone.utc)  # TIMEZONE FIX',
                    content
                )
                fixes_in_file += len(re.findall(pattern1, original_content))

            # Pattern 2: datetime.utcnow() → datetime.now(timezone.utc)
            # utcnow() is DEPRECATED in Python 3.12+
            pattern2 = r'datetime\.utcnow\(\)'
            if re.search(pattern2, content):
                content = re.sub(
                    pattern2,
                    'datetime.now(timezone.utc)  # DEPRECATED FIX: utcnow() → now(timezone.utc)',
                    content
                )
                fixes_in_file += len(re.findall(pattern2, original_content))

            # Add timezone import if needed
            if fixes_in_file > 0:
                # Check if timezone is already imported
                if 'from datetime import' in content and 'timezone' not in content:
                    # Find the datetime import line
                    import_pattern = r'from datetime import ([^\n]+)'
                    match = re.search(import_pattern, content)
                    if match:
                        imports = match.group(1)
                        if 'timezone' not in imports:
                            # Add timezone to the import
                            new_imports = imports.rstrip() + ', timezone'
                            content = re.sub(
                                import_pattern,
                                f'from datetime import {new_imports}',
                                content,
                                count=1
                            )

            if content != original_content:
                if not self.dry_run:
                    file_path.write_text(content, encoding='utf-8')
                return True, fixes_in_file

            return False, 0

        except Exception as e:
            print(f"ERROR processing {file_path}: {e}")
            return False, 0

    def fix_directory(self, directory: Path, pattern: str = "*.py") -> None:
        """Fix all Python files in directory recursively"""
        print(f"\n{'DRY RUN: ' if self.dry_run else ''}Scanning {directory} for timezone-naive datetime usage...")

        python_files = list(directory.rglob(pattern))
        print(f"Found {len(python_files)} Python files")

        for file_path in python_files:
            self.files_processed += 1
            was_modified, fixes = self.fix_file(file_path)

            if was_modified:
                self.files_modified += 1
                self.total_fixes += fixes
                status = "[DRY RUN] Would fix" if self.dry_run else "✅ Fixed"
                print(f"{status}: {file_path.relative_to(directory)} ({fixes} locations)")

        print(f"\n{'DRY RUN ' if self.dry_run else ''}SUMMARY:")
        print(f"  Files processed: {self.files_processed}")
        print(f"  Files modified: {self.files_modified}")
        print(f"  Total fixes: {self.total_fixes}")

        if self.dry_run:
            print("\nRun without --dry-run to apply changes")


def main():
    """Main entry point"""
    dry_run = "--dry-run" in sys.argv

    backend_dir = Path(__file__).parent
    fixer = TimezoneFixer(dry_run=dry_run)

    # Fix backend directory
    fixer.fix_directory(backend_dir)

    if fixer.files_modified > 0:
        print("\n⚠️  IMPORTANT: After fixing, run tests to ensure nothing broke:")
        print("  pytest backend/tests/")

    sys.exit(0 if fixer.total_fixes == 0 else 1)


if __name__ == "__main__":
    main()
