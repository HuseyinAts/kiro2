#!/usr/bin/env python
"""Add ondelete='CASCADE' to all ForeignKey definitions"""
import re
from pathlib import Path

def add_cascade_to_foreignkeys(file_path):
    """Add ondelete='CASCADE' to ForeignKey definitions if missing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern to match ForeignKey without ondelete parameter
        # Matches: ForeignKey("table.column") or ForeignKey("table.column", other_params)
        # But NOT if it already has ondelete=

        def replace_fk(match):
            fk_content = match.group(1)
            # If already has ondelete, don't modify
            if 'ondelete=' in fk_content:
                return match.group(0)

            # Find the closing parenthesis
            # Add ondelete="CASCADE" before the last )
            if ')' in fk_content:
                # Insert before the closing paren
                parts = fk_content.rsplit(')', 1)
                if len(parts) == 2:
                    # Has other parameters
                    new_fk = f'{parts[0]}, ondelete="CASCADE"){parts[1]}'
                else:
                    new_fk = fk_content
            else:
                # Simple ForeignKey("table.column")
                new_fk = fk_content[:-1] + ', ondelete="CASCADE"' + fk_content[-1]

            return f'ForeignKey({new_fk})'

        # Match ForeignKey with its full parameter list
        pattern = r'ForeignKey\(([^)]+(?:\([^)]*\)[^)]*)*)\)'

        # Simpler approach: replace ForeignKey("x") with ForeignKey("x", ondelete="CASCADE")
        # if it doesn't already have ondelete
        new_content = content

        # Find all ForeignKey occurrences
        for match in re.finditer(r'ForeignKey\("([^"]+)"(?:,\s*([^)]+))?\)', content):
            full_match = match.group(0)
            table_col = match.group(1)
            extra_params = match.group(2)

            # Skip if already has ondelete
            if 'ondelete' in full_match:
                continue

            # Build replacement
            if extra_params:
                replacement = f'ForeignKey("{table_col}", {extra_params}, ondelete="CASCADE")'
            else:
                replacement = f'ForeignKey("{table_col}", ondelete="CASCADE")'

            new_content = new_content.replace(full_match, replacement)

        # Only write if changed
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

def main():
    models_dir = Path('backend/models')
    fixed_count = 0

    # Process model files
    for py_file in models_dir.glob('*.py'):
        if py_file.name == '__init__.py':
            continue

        if add_cascade_to_foreignkeys(py_file):
            fixed_count += 1
            print(f"✓ Added CASCADE to {py_file}")
        else:
            print(f"  No changes needed in {py_file}")

    print(f"\n✅ Added CASCADE to {fixed_count} files")

if __name__ == '__main__':
    main()
