import os, sys

root = r'C:\Users\husey\kiro2\backend'
hits = {}

for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['__pycache__','.git','node_modules','.venv','venv']]
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            txt = open(fpath, encoding='utf-8', errors='replace').read()
        except:
            continue
        lines = txt.splitlines()
        for i, line in enumerate(lines, 1):
            # questions tablosuna referans (question_bank degil)
            if ('from questions' in line or
                '"questions"' in line or
                "'questions'" in line or
                'table="questions"' in line or
                "table='questions'" in line or
                ('select' in line.lower() and 'from questions' in line.lower()) or
                ('Question' in line and 'QuestionBank' not in line and 'import' in line)):
                key = fpath.replace(root, '').lstrip('\\/')
                if key not in hits:
                    hits[key] = []
                hits[key].append((i, line.strip()[:100]))

for f, lines in sorted(hits.items()):
    print(f'\n=== {f} ===')
    for ln, txt in lines[:5]:
        print(f'  {ln}: {txt}')
