import os, sys
sys.stdout.reconfigure(encoding='utf-8')
root = r'C:\Users\husey\kiro2\backend'
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.venv', 'venv', 'node_modules']]
    for f in files:
        if not f.endswith('.py'): continue
        fpath = os.path.join(dirpath, f)
        try:
            txt = open(fpath, encoding='utf-8', errors='replace').read()
        except: continue
        if 'localhost:6379' in txt or 'localhost", 6379' in txt or "localhost', 6379" in txt:
            lines = txt.splitlines()
            for i, line in enumerate(lines, 1):
                if 'localhost' in line and ('6379' in line or 'redis' in line.lower()):
                    rel = fpath.replace(root, '').lstrip(os.sep)
                    print(f"{rel}:{i}: {line.strip()[:100]}")
