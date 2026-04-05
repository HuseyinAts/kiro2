import urllib.request, urllib.error, json, sys

BASE = "http://localhost:8000"

# 1. Login
body = json.dumps({"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}).encode()
req = urllib.request.Request(f"{BASE}/api/v1/auth/giris", data=body,
      headers={"Content-Type":"application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=10) as r:
    token = json.loads(r.read())["token"]
print(f"Login: OK (token {token[:20]}...)")

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 2. ES question search
tests = [
    {"query":"türev fonksiyon", "size":3},
    {"query":"logaritma", "size":3, "exam_type":"TYT"},
    {"query":"hücre bölünme mitoz", "size":3},
]

for payload in tests:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/api/v1/elasticsearch/questions/search",
          data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            hits = d.get("hits") or d.get("results") or []
            total = d.get("total") or d.get("count") or len(hits)
            print(f"\nQuery: '{payload['query']}' -> total={total}")
            for h in hits[:2]:
                txt = h.get("question_text") or h.get("text") or h.get("_source",{}).get("question_text","?")
                print(f"  [{h.get('subject_area','')}] {str(txt)[:70]}")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"\nQuery '{payload['query']}': HTTP {e.code} -> {body_err[:150]}")

# 3. ES health endpoint
req = urllib.request.Request(f"{BASE}/api/v1/elasticsearch/health",
      headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req, timeout=10) as r:
    d = json.loads(r.read())
    print(f"\nES /health: status={d.get('status')} docs={d.get('doc_count') or d.get('total_documents','?')}")

# 4. ES index stats
req = urllib.request.Request(f"{BASE}/api/v1/elasticsearch/admin/indices/stats",
      headers={"Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
        for idx, info in d.items():
            dc = info.get("doc_count",0)
            sz = info.get("size_in_bytes",0)
            print(f"Index '{idx}': {dc:,} docs, {sz//1024:,} KB")
except urllib.error.HTTPError as e:
    print(f"Stats: HTTP {e.code}")
