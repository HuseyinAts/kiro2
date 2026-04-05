content = open(r'C:\Users\husey\kiro2\backend\core\redis_cache_docker.py', encoding='utf-8', errors='replace').read()
for i, line in enumerate(content.splitlines(), 1):
    if 'localhost' in line or 'REDIS' in line or 'redis_url' in line.lower() or 'host=' in line:
        print(f"{i}: {line.rstrip()[:120]}")
