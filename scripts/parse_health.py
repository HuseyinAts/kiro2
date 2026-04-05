import sys, json
d = json.load(sys.stdin)
for c in d['components']:
    mark = 'OK  ' if c['component_status'] == 'healthy' else 'WARN' if c['component_status'] == 'degraded' else 'FAIL'
    msg = str(c.get('message') or c.get('error') or '')[:70]
    name = c['name']
    print(f"[{mark}] {name:20s}: {msg}")
print()
print("Overall:", d['health_status'].upper())
