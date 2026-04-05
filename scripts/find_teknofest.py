import os, sys
sys.stdout.reconfigure(encoding='utf-8')
fe_root = r'C:\Users\husey\kiro2\frontend'

print("=== FRONTEND'DE teknofest-egitim ARAMASI ===")
for root, dirs, files in os.walk(fe_root):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'dist']]
    for f in files:
        if not f.endswith(('.ts', '.tsx', '.js', '.json', '.env', '.env.production',
                           '.env.development', '.env.local', 'vite.config.ts')):
            continue
        fpath = os.path.join(root, f)
        try:
            txt = open(fpath, encoding='utf-8', errors='replace').read()
        except: continue
        if 'teknofest-egitim' in txt:
            rel = fpath.replace(fe_root, '').lstrip(os.sep)
            print(f"\n{rel}:")
            for i, line in enumerate(txt.splitlines(), 1):
                if 'teknofest-egitim' in line:
                    print(f"  {i}: {line.rstrip()[:100]}")
