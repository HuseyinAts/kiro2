import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

js_dir = r'C:\Users\husey\kiro2\frontend\dist\js'
if not os.path.exists(js_dir):
    print("dist/js yok!")
    exit()

files = sorted([f for f in os.listdir(js_dir) if f.startswith('index-') and f.endswith('.js')],
               key=lambda f: os.path.getmtime(os.path.join(js_dir, f)), reverse=True)

print("index- dosyalari (yeni > eski):")
for f in files:
    fpath = os.path.join(js_dir, f)
    mtime = os.path.getmtime(fpath)
    size = os.path.getsize(fpath)
    import datetime
    t = datetime.datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
    content = open(fpath, encoding='utf-8', errors='replace').read()
    has_tek = 'teknofest-egitim.com' in content
    has_empty_api = "''" in content or '""' in content  # bos string
    print(f"  {f} ({size//1024}KB) @ {t}  teknofest:{has_tek}")

# Timestamp kontrolu - build ne zaman bitti?
log_path = r'C:\Users\husey\kiro2\frontend_build.log'
if os.path.exists(log_path):
    import datetime
    mtime = os.path.getmtime(log_path)
    print(f"\nBuild log son degisim: {datetime.datetime.fromtimestamp(mtime).strftime('%H:%M:%S')}")
    last_lines = open(log_path, encoding='utf-8', errors='replace').read().splitlines()[-5:]
    for l in last_lines:
        print(f"  {l}")
