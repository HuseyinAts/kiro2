import json, glob, os

files = sorted(glob.glob(r'C:\Users\husey\d-dataset\output\final\eslesmis_*.jsonl'))
biggest = max(files, key=os.path.getsize)

for enc in ['utf-8', 'utf-8-sig', 'cp1254', 'cp1252', 'latin-1']:
    try:
        with open(biggest, encoding=enc) as f:
            line = f.readline()
        d = json.loads(line)
        txt = d["text"][:80]
        print(f"{enc}: {txt}")
    except Exception as e:
        print(f"{enc}: ERROR {e}")
