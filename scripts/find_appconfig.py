import os, sys
sys.stdout.reconfigure(encoding='utf-8')
fe_src = r'C:\Users\husey\kiro2\frontend\src'
# api.ts dosyasinda appConfig'in import satiri
api_ts = os.path.join(fe_src, 'api.ts')
if os.path.exists(api_ts):
    txt = open(api_ts, encoding='utf-8', errors='replace').read()
    for i, line in enumerate(txt.splitlines(), 1):
        if 'import' in line and 'appConfig' in line:
            print(f"api.ts:{i}: {line.rstrip()}")
        if i < 20:
            print(f"api.ts:{i}: {line.rstrip()[:100]}")
