import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

tests = [
    ('gtts import', ['python', '-c', 'import gtts; print(gtts.__version__)']),
    ('pyttsx3 import', ['python', '-c', 'import pyttsx3; e=pyttsx3.init(); print(len(e.getProperty("voices")))']),
    ('gtts in pip list', ['pip', 'show', 'gtts']),
]
for label, cmd in tests:
    r = subprocess.run(['docker', 'exec', 'kiro2-backend'] + cmd,
                        capture_output=True, timeout=15)
    out = r.stdout.decode('utf-8', errors='replace').strip()
    err = r.stderr.decode('utf-8', errors='replace').strip()
    print(f"{label}: {out[:100] or err[:100]}")

# TTS api endpoint detay
import json, urllib.request
def post(url, body):
    req = urllib.request.Request('http://localhost:8000' + url,
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

auth, _ = post('/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
tok = auth.get('access_token', '')

def get(url, tok=None):
    h = {}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request('http://localhost:8000' + url, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

tts_r, tts_s = get('/api/v1/tts/voices', tok)
print(f"\nTTS voices endpoint ({tts_s}):")
print(json.dumps(tts_r, ensure_ascii=False, indent=2)[:400])
