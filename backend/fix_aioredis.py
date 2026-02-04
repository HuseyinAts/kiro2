"""
aioredis → redis.asyncio Migration Script
Automatically converts aioredis imports to redis.asyncio
"""
import re
from pathlib import Path

# Files to fix based on grep results
files_to_fix = [
    "core/message_queue_system.py",
    "core/context_manager.py",
    "analytics/realtime_exam_monitoring.py",
    "tests/integration/test_message_queue_system.py",
    "tests/integration/test_framework.py",
]

def fix_aioredis(file_path: Path):
    """Fix aioredis to redis.asyncio imports"""
    print(f"Processing: {file_path}")

    content = file_path.read_text(encoding='utf-8')
    original = content

    # Fix import: import aioredis -> import redis.asyncio as redis
    content = re.sub(
        r'import\s+aioredis\b',
        'import redis.asyncio as redis',
        content
    )

    # Fix from import: from aioredis import X -> from redis.asyncio import X
    content = re.sub(
        r'from\s+aioredis\s+import',
        'from redis.asyncio import',
        content
    )

    # Fix usage: aioredis.Redis -> redis.Redis
    content = re.sub(
        r'\baioredis\.Redis\b',
        'redis.Redis',
        content
    )

    # Fix usage: aioredis.create_redis -> redis.from_url
    content = re.sub(
        r'\baioredis\.create_redis(_pool)?\b',
        'redis.from_url',
        content
    )

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
            if fix_aioredis(file_path):
                fixed_count += 1
        else:
            print(f"  [!] Not found: {file_path}")

    print(f"\n[OK] Fixed {fixed_count} files")
