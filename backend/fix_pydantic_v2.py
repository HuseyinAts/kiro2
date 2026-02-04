"""
Pydantic V2 Migration Script
Automatically converts @validator to @field_validator in remaining files
"""
import re
from pathlib import Path

# Files to fix based on grep results
files_to_fix = [
    "test_user_registration_authentication_flow.py",
    "models/zpd_maarif.py",
    "models/ebatv_content.py",
    "models/irt_morfoloji.py",
    "api/youtube_routes.py",
    "api/bionic_reading.py",
]

def fix_pydantic_v2(file_path: Path):
    """Fix Pydantic V1 to V2 patterns in a file"""
    print(f"Processing: {file_path}")

    content = file_path.read_text(encoding='utf-8')
    original = content

    # Fix import: validator -> field_validator
    content = re.sub(
        r'from pydantic import (.*?)\bvalidator\b(.*?)',
        lambda m: f'from pydantic import {m.group(1)}field_validator{m.group(2)}',
        content
    )

    # Fix @validator("field") -> @field_validator("field") + @classmethod
    # Pattern: @validator(...) followed by def method(cls, v):
    pattern = r'(\s+)@validator\((.*?)\)\s+def\s+(\w+)\(cls,'
    replacement = r'\1@field_validator(\2)\n\1@classmethod\n\1def \3(cls,'
    content = re.sub(pattern, replacement, content)

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [OK] Fixed: {file_path}")
        return True
    else:
        print(f"  [-] No changes: {file_path}")
        return False

if __name__ == "__main__":
    backend_dir = Path(__file__).parent
    fixed_count = 0

    for file_rel in files_to_fix:
        file_path = backend_dir / file_rel
        if file_path.exists():
            if fix_pydantic_v2(file_path):
                fixed_count += 1
        else:
            print(f"  [!] Not found: {file_path}")

    print(f"\n[OK] Fixed {fixed_count} files")
