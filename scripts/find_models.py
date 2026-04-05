import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

# cat_sessions ve irt_parameters icin model dosyalarini bul
result = subprocess.run(
    ['python', '-c', '''
import os
root = r'C:\\Users\\husey\\kiro2\\backend'
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['__pycache__','.git','node_modules']]
    for f in files:
        if not f.endswith('.py'): continue
        fpath = os.path.join(dirpath, f)
        try:
            txt = open(fpath, encoding='utf-8', errors='replace').read()
        except: continue
        if '__tablename__' in txt and any(k in txt for k in ['cat_session', 'irt_param', 'flashcard']):
            rel = fpath.replace(root, '').lstrip(os.sep)
            for i, line in enumerate(txt.splitlines(), 1):
                if '__tablename__' in line and any(k in line for k in ['cat_session', 'irt_param', 'flashcard']):
                    print(f"{rel}:{i}: {line.strip()}")
'''],
    capture_output=True, timeout=30, cwd=r'C:\Users\husey\kiro2'
)
print(result.stdout.decode('utf-8', errors='replace'))
if result.stderr:
    print("ERR:", result.stderr.decode()[:200])
