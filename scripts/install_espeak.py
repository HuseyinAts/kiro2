import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
# apt-get update
r = subprocess.run(['docker', 'exec', '-u', 'root', 'kiro2-backend',
                     'apt-get', 'update', '-qq'], capture_output=True, timeout=60)
print("apt-get update:", r.returncode)

# espeak-ng kur
r2 = subprocess.run(['docker', 'exec', '-u', 'root', 'kiro2-backend',
                      'apt-get', 'install', '-y', 'espeak-ng'], capture_output=True, timeout=120)
out = r2.stdout.decode('utf-8', errors='replace')
err = r2.stderr.decode('utf-8', errors='replace')
print("espeak-ng install:", r2.returncode)
print(out[-200:] if out else err[-200:])

# pyttsx3 testi
r3 = subprocess.run(['docker', 'exec', 'kiro2-backend', 'python', '-c',
                      'import pyttsx3; e=pyttsx3.init(); voices=e.getProperty("voices"); print("voices:", len(voices))'],
                     capture_output=True, timeout=15)
print("pyttsx3 test:", r3.stdout.decode()[:100] or r3.stderr.decode()[:100])
