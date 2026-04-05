import subprocess, re, sys
sys.stdout.reconfigure(encoding='utf-8')

result = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'cat', '/usr/share/nginx/html/index.html'],
    capture_output=True, timeout=10
)
html = result.stdout.decode('utf-8', errors='replace')

# Hangi JS dosyalari yukleniyor?
js_refs = re.findall(r'(?:src|href)=["\']([^"\']*\.js)["\']', html)
css_refs = re.findall(r'(?:src|href)=["\']([^"\']*\.css)["\']', html)

print("=== index.html'in yukledigij JS dosyalari ===")
for j in js_refs:
    print(f"  {j}")

print("\n=== CSS dosyalari ===")
for c in css_refs:
    print(f"  {c}")

print("\n=== index.html ilk 20 satir ===")
for i, line in enumerate(html.splitlines()[:20], 1):
    print(f"{i}: {line[:120]}")
