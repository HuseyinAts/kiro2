import subprocess, sys, re
sys.stdout.reconfigure(encoding='utf-8')

# Docker backend startup logu - ERROR/WARN satirlari
result = subprocess.run(
    ['docker', 'logs', 'kiro2-backend', '--tail', '500'],
    capture_output=True
)
log = result.stdout.decode('utf-8', errors='replace') + result.stderr.decode('utf-8', errors='replace')

errors = [l for l in log.splitlines() if re.search(r'ERROR|WARN|CRITICAL|Exception|Traceback|Failed|failed|error', l, re.I)]
print(f"=== {len(errors)} ERROR/WARN SATIRI ===")
for l in errors[:60]:
    print(l[:150])

# Ayrica Loaded/Failed router sayisini bul
loaded = [l for l in log.splitlines() if 'Loaded:' in l or 'Failed:' in l]
print(f"\n=== ROUTER DURUMU ===")
for l in loaded:
    print(l.strip())
