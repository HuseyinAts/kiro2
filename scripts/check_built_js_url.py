import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

# Docker frontend JS dosyalarinda VITE_API_URL degerini bul
import subprocess

# Docker'daki en buyuk JS dosyasinda API URL ara
result = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'sh', '-c',
     'ls -S /usr/share/nginx/html/js/*.js 2>/dev/null | head -3'],
    capture_output=True, timeout=10
)
files = result.stdout.decode().strip().splitlines()
print("En buyuk JS dosyalari:", files[:3])

for fpath in files[:2]:
    result2 = subprocess.run(
        ['docker', 'exec', 'kiro2-frontend', 'sh', '-c', f'cat "{fpath}"'],
        capture_output=True, timeout=15
    )
    content = result2.stdout.decode('utf-8', errors='replace')
    # teknofest ya da localhost ara
    found = re.findall(r'https?://[a-zA-Z0-9._:-]{5,60}', content)
    unique = list(dict.fromkeys(found))
    # sadece API gibi gorunenler
    api_urls = [u for u in unique if any(k in u for k in ['localhost', 'teknofest', '8000', '8001', 'api.'])]
    print(f"\n{os.path.basename(fpath)}:")
    print("  API URL'ler:", api_urls[:10])
