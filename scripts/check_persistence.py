import subprocess, sys, os
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 55)
print("KALICILIK KONTROLÜ")
print("=" * 55)

checks = []

# 1. Dockerfile.minimal espeak var mi?
df = open(r'C:\Users\husey\kiro2\backend\Dockerfile.minimal', encoding='utf-8').read()
checks.append(('Dockerfile.minimal espeak-ng', 'espeak-ng' in df))

# 2. requirements-minimal.txt gtts/pyttsx3 var mi?
req = open(r'C:\Users\husey\kiro2\backend\requirements-minimal.txt', encoding='utf-8').read()
checks.append(('requirements-minimal.txt gtts', 'gtts' in req))
checks.append(('requirements-minimal.txt pyttsx3', 'pyttsx3' in req))
checks.append(('requirements-minimal.txt python-jose', 'python-jose' in req))

# 3. exam_db.py runtime import var mi?
edb = open(r'C:\Users\husey\kiro2\backend\models\exam_db.py', encoding='utf-8').read()
checks.append(('exam_db.py runtime QuestionBankItem import', 'from .question_bank import QuestionBankItem' in edb and 'TYPE_CHECKING' not in edb.split('from .question_bank')[0].split('\n')[-1]))

# 4. auth.py async refresh token var mi?
auth = open(r'C:\Users\husey\kiro2\backend\api\auth.py', encoding='utf-8').read()
checks.append(('auth.py async INSERT refresh_token', 'INSERT INTO refresh_tokens' in auth and 'jose_jwt' in auth))
checks.append(('auth.py eski sync_session kaldirildi', 'if hasattr(db.bind, "sync_engine"):' not in auth))

# 5. config.py redis_host parse var mi?
cfg = open(r'C:\Users\husey\kiro2\backend\core\config.py', encoding='utf-8').read()
checks.append(('config.py REDIS_URL host parse', '_redis_host_env' in cfg))

# 6. .env.production dogru mu?
prod = open(r'C:\Users\husey\kiro2\frontend\.env.production', encoding='utf-8').read()
checks.append(('.env.production VITE_API_URL bos', 'VITE_API_URL=' in prod and 'teknofest' not in prod))

# 7. frontend/src/config/index.ts dogru mu?
cfg_ts = open(r'C:\Users\husey\kiro2\frontend\src\config\index.ts', encoding='utf-8').read()
checks.append(('frontend config.ts empty default', "(import.meta.env.VITE_API_URL ?? '')" in cfg_ts))

print(f"\n{'':40} {'DURUM':10}")
print("-" * 52)
all_ok = True
for label, ok in checks:
    sym = '✓' if ok else '✗'
    if not ok: all_ok = False
    print(f"  {sym}  {label:<40}")

print("\n" + ("=" * 20 + " TÜMÜ TAMAM " + "=" * 20 if all_ok else "BAZI KONTROLLER BAŞARISIZ"))

print("\n" + "=" * 55)
print("SONRAKI docker-compose up --build KOMUTUNDA:")
print("=" * 55)
print("  - espeak-ng apt'ten kurulacak")
print("  - gtts, pyttsx3, python-jose pip'ten kurulacak")
print("  - auth.py async refresh token aktif olacak")
print("  - exam_db.py mapper hatası olmayacak")
print("  - Redis host REDIS_URL'den parse edilecek")
print("  - Frontend relative URL kullanacak (nginx proxy)")
