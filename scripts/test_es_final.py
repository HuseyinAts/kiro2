import sys, os, urllib.request, json
os.environ['PYTHONIOENCODING'] = 'utf-8'

BASE = 'http://localhost:8000'
body = json.dumps({'email':'admin@kiro2.com','password':'Kiro2Beta2026@x'}).encode()
req = urllib.request.Request(BASE+'/api/v1/auth/giris', data=body,
      headers={'Content-Type':'application/json'}, method='POST')
token = json.loads(urllib.request.urlopen(req).read())['token']
H = {'Authorization':'Bearer '+token, 'Content-Type':'application/json'}

tests = [
    ('logaritma', None),
    ('integral', 'AYT'),
    ('mitoz bolunme', None),
    ('osmanli devlet', None),
    ('newton kuvvet', 'TYT'),
]

print("=== ES Search API Test ===")
for q, exam in tests:
    payload = {'query': q, 'size': 3}
    if exam:
        payload['exam_type'] = exam
    req = urllib.request.Request(
        BASE+'/api/v1/elasticsearch/questions/search',
        data=json.dumps(payload).encode(), headers=H, method='POST')
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=10).read())
        total = d.get('total', 0)
        results = d.get('results', [])
        r0 = results[0] if results else {}
        src = r0.get('source', r0)
        exam_t = src.get('exam_type', '?')
        subj = src.get('subject_area', '?')
        qt = str(src.get('question_text', '')).encode('ascii', 'replace').decode()[:55]
        label = f"{exam or 'ANY':3s}"
        print(f"  [{label}] '{q:20s}' -> {total:5d} hit | {exam_t}/{subj} | {qt}")
    except Exception as e:
        print(f"  '{q}': ERROR {e}")

print("\n=== ES Health ===")
req = urllib.request.Request(BASE+'/api/v1/elasticsearch/health', headers=H)
d = json.loads(urllib.request.urlopen(req).read())
print(f"  status={d.get('status')} cluster={d.get('cluster_status','?')} docs={d.get('total_documents', d.get('doc_count','?'))}")
