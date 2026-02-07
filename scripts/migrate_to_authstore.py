#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication Migration Script
Migrates from useAuth hook to authStore (Zustand)

Usage:
    python scripts/migrate_to_authstore.py --dry-run
    python scripts/migrate_to_authstore.py --dry-run --delete-useauth
    python scripts/migrate_to_authstore.py --execute
    python scripts/migrate_to_authstore.py --execute --delete-useauth
"""

import os
import re
import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Set
import shutil
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class AuthStoreMigrator:
    def __init__(self, dry_run: bool = True, delete_useauth: bool = False):
        self.dry_run = dry_run
        self.delete_useauth = delete_useauth
        self.frontend_dir = Path('frontend/src')
        self.changes: List[Tuple[str, str]] = []
        self.files_to_delete: List[str] = []

        # Files to exclude from migration
        self.exclude_patterns = [
            '__tests__',
            '.test.',
            '.spec.',
            'node_modules',
            'dist',
            'build'
        ]

    def should_exclude(self, file_path: str) -> bool:
        """Check if file should be excluded from migration"""
        return any(pattern in file_path for pattern in self.exclude_patterns)

    def find_files_with_useauth(self) -> List[Path]:
        """Find all files that import or use useAuth"""
        files = []

        # Search for both .ts and .tsx files
        for extension in ['*.ts', '*.tsx']:
            for file_path in self.frontend_dir.rglob(extension):
                if self.should_exclude(str(file_path)):
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8')

                    # Check for useAuth imports or usage
                    if re.search(r"from\s+['\"].*useAuth['\"]", content) or \
                       re.search(r"import.*useAuth", content) or \
                       re.search(r"useAuth\(\)", content):
                        files.append(file_path)

                except Exception as e:
                    print(f"⚠️  Error reading {file_path}: {e}")

        return files

    def find_useauth_files(self) -> List[Path]:
        """Find the useAuth hook files to be deleted"""
        patterns = [
            'hooks/useAuth.ts',
            'hooks/useAuth.tsx',
            'hooks/useAuth.js',
            'hooks/useAuth.jsx'
        ]

        files = []
        for pattern in patterns:
            file_path = self.frontend_dir / pattern
            if file_path.exists():
                files.append(file_path)

        return files

    def migrate_file(self, file_path: Path) -> Tuple[str, bool]:
        """Migrate a single file from useAuth to authStore"""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content

            # Step 1: Replace useAuth import with authStore import
            content = re.sub(
                r"import\s+\{?\s*useAuth\s*\}?\s+from\s+['\"]([^'\"]*useAuth.*?)['\"]",
                "import { useAuthStore } from '@/store/authStore'",
                content
            )

            # Step 2: Replace useAuth() calls with useAuthStore()
            content = re.sub(
                r"const\s+\{([^}]+)\}\s+=\s+useAuth\(\)",
                r"const { \1 } = useAuthStore()",
                content
            )

            # Step 3: Handle destructured properties mapping
            # Common patterns to fix:

            # user -> user (stays the same)
            # login -> login (stays the same)
            # logout -> logout (stays the same)
            # isAuthenticated -> isAuthenticated (stays the same)
            # token -> token (stays the same)

            # Step 4: Replace any remaining useAuth() calls
            content = re.sub(
                r"useAuth\(\)",
                "useAuthStore()",
                content
            )

            # Step 5: Fix any useAuth references in comments or JSDoc
            content = re.sub(
                r"@see useAuth",
                "@see useAuthStore",
                content
            )
            content = re.sub(
                r"Uses useAuth",
                "Uses useAuthStore",
                content
            )

            changed = content != original_content

            return content, changed

        except Exception as e:
            print(f"❌ Error migrating {file_path}: {e}")
            return "", False

    def backup_file(self, file_path: Path):
        """Create backup of file before modifying"""
        backup_dir = Path('frontend/src/.migration-backup')
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        relative_path = file_path.relative_to(self.frontend_dir)
        backup_path = backup_dir / f"{relative_path}_{timestamp}.bak"

        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)

        return backup_path

    def run(self):
        """Run the migration"""
        print("=" * 80)
        print("🔄 Authentication Migration: useAuth → authStore")
        print("=" * 80)
        print()

        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
        else:
            print("⚠️  EXECUTION MODE - Files will be modified!")

        if self.delete_useauth:
            print("🗑️  DELETE MODE - useAuth files will be removed")

        print()

        # Step 1: Find all files using useAuth
        print("📂 Searching for files using useAuth...")
        files = self.find_files_with_useauth()
        print(f"   Found {len(files)} files to migrate")
        print()

        # Step 2: Preview or execute migration
        print("📝 Files to migrate:")
        print("-" * 80)

        migrated_count = 0
        unchanged_count = 0

        for file_path in files:
            new_content, changed = self.migrate_file(file_path)

            if changed:
                migrated_count += 1
                relative_path = file_path.relative_to(Path('.'))

                print(f"✏️  {relative_path}")

                if not self.dry_run:
                    # Backup original
                    backup_path = self.backup_file(file_path)
                    print(f"   📦 Backup: {backup_path.relative_to(Path('.'))}")

                    # Write modified content
                    file_path.write_text(new_content, encoding='utf-8')
                    print(f"   ✅ Modified")

                self.changes.append((str(file_path), 'migrated'))
            else:
                unchanged_count += 1

        print()
        print("-" * 80)
        print(f"📊 Summary:")
        print(f"   • Files to migrate: {migrated_count}")
        print(f"   • Files unchanged: {unchanged_count}")
        print()

        # Step 3: Handle useAuth file deletion
        if self.delete_useauth:
            print("🗑️  useAuth Files to Delete:")
            print("-" * 80)

            useauth_files = self.find_useauth_files()

            if useauth_files:
                for file_path in useauth_files:
                    relative_path = file_path.relative_to(Path('.'))
                    print(f"🗑️  {relative_path}")

                    if not self.dry_run:
                        # Backup before deletion
                        backup_path = self.backup_file(file_path)
                        print(f"   📦 Backup: {backup_path.relative_to(Path('.'))}")

                        # Delete file
                        file_path.unlink()
                        print(f"   ✅ Deleted")

                    self.files_to_delete.append(str(file_path))
            else:
                print("   No useAuth files found to delete")

            print()
            print("-" * 80)
            print(f"📊 Deletion Summary:")
            print(f"   • Files to delete: {len(useauth_files)}")
            print()

        # Step 4: Final summary
        print("=" * 80)
        print("✨ Migration Complete!")
        print("=" * 80)
        print()

        if self.dry_run:
            print("🔍 This was a DRY RUN - no files were modified")
            print()
            print("To execute the migration, run:")
            print("   python scripts/migrate_to_authstore.py --execute")

            if self.delete_useauth:
                print("   python scripts/migrate_to_authstore.py --execute --delete-useauth")
        else:
            print("✅ Migration executed successfully!")
            print()
            print("📦 Backups saved to: frontend/src/.migration-backup/")
            print()
            print("🔍 Next steps:")
            print("   1. Review the changes with: git diff")
            print("   2. Test the application thoroughly")
            print("   3. Run TypeScript compiler: npm run type-check")
            print("   4. Run tests: npm test")
            print("   5. If issues occur, restore from backups")

        print()

        return migrated_count, len(useauth_files) if self.delete_useauth else 0


def main():
    parser = argparse.ArgumentParser(
        description='Migrate authentication from useAuth to authStore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without modifying files
  python scripts/migrate_to_authstore.py --dry-run

  # Preview changes including useAuth file deletion
  python scripts/migrate_to_authstore.py --dry-run --delete-useauth

  # Execute migration
  python scripts/migrate_to_authstore.py --execute

  # Execute migration and delete useAuth files
  python scripts/migrate_to_authstore.py --execute --delete-useauth
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the migration (modifies files)'
    )

    parser.add_argument(
        '--delete-useauth',
        action='store_true',
        help='Delete useAuth hook files after migration'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")

    if args.dry_run and args.execute:
        parser.error("Cannot specify both --dry-run and --execute")

    # Run migration
    migrator = AuthStoreMigrator(
        dry_run=args.dry_run,
        delete_useauth=args.delete_useauth
    )

    try:
        migrated_count, deleted_count = migrator.run()

        if args.execute:
            print(f"✅ Successfully migrated {migrated_count} files")
            if args.delete_useauth and deleted_count > 0:
                print(f"✅ Successfully deleted {deleted_count} useAuth files")

    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
