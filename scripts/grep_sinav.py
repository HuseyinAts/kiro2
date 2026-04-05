import subprocess, sys

# sinav.py'deki ExamQuestion ve soru secimi satirlari
result = subprocess.run(
    ['python', '-c', '''
import re
txt = open(r'C:\\Users\\husey\\kiro2\\backend\\api\\sinav.py', encoding='utf-8', errors='replace').read()
lines = txt.splitlines()
for i, line in enumerate(lines, 1):
    lo = line.lower()
    if any(k in lo for k in ['exam_question', 'question_bank', '"questions"', "from questions",
                              'soru_sec', 'select_quest', 'question_id', 'insert.*exam']):
        print(f"{i:4}: {line.rstrip()[:110]}")
'''],
    capture_output=True, text=True, cwd=r'C:\Users\husey\kiro2'
)
print(result.stdout[:4000])
if result.stderr: print('ERR:', result.stderr[:500])
