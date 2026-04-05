import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

r = subprocess.run(['docker', 'logs', 'kiro2-backend', '--tail', '200'],
                   capture_output=True, timeout=30)
log = r.stdout.decode('utf-8', errors='replace') + r.stderr.decode('utf-8', errors='replace')
lines = log.splitlines()

keywords = ['gtts', 'pyttsx3', 'espeak', 'ERROR', 'CRITICAL',
            'Loaded:', 'Failed:', 'Redis not available', 'refresh_token',
            'Successfully started', 'Backend Started']

print("=== KRITIK LOG SATIRLARI ===")
for l in lines:
    if any(k in l for k in keywords):
        print(l[:150])

print("\n=== SON 10 SATIR ===")
for l in lines[-10:]:
    print(l[:150])
