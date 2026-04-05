import re

f = r'C:\Users\husey\kiro2\backend\core\comprehensive_health_check.py'
content = open(f, encoding='utf-8').read()

old = '            es = AsyncElasticsearch(\n                ["http://localhost:9200"],\n                request_timeout=2,\n                retry_on_timeout=False,\n            )'

new = ('            import os\n'
       '            _es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")\n'
       '            es = AsyncElasticsearch(\n'
       '                [_es_url],\n'
       '                request_timeout=2,\n'
       '                retry_on_timeout=False,\n'
       '            )')

if old in content:
    content = content.replace(old, new)
    open(f, 'w', encoding='utf-8').write(content)
    print('OK: hardcoded localhost:9200 -> env var')
else:
    print('NOT FOUND, showing context:')
    idx = content.find('AsyncElasticsearch(')
    print(repr(content[idx:idx+200]))
