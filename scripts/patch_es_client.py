import re

f = r'C:\Users\husey\kiro2\backend\core\elasticsearch_client.py'
content = open(f, encoding='utf-8').read()

# Find and replace get_elasticsearch_client function body
old = ('def get_elasticsearch_client() -> ElasticsearchClient:\n'
       '    """Get global Elasticsearch client instance"""\n'
       '    global _elasticsearch_client\n'
       '\n'
       '    if _elasticsearch_client is None:\n'
       '        _elasticsearch_client = ElasticsearchClient()\n'
       '\n'
       '    return _elasticsearch_client')

new = ('def get_elasticsearch_client() -> ElasticsearchClient:\n'
       '    """Get global Elasticsearch client instance"""\n'
       '    global _elasticsearch_client\n'
       '\n'
       '    if _elasticsearch_client is None:\n'
       '        import os\n'
       '        es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")\n'
       '        _elasticsearch_client = ElasticsearchClient(hosts=[es_url])\n'
       '\n'
       '    return _elasticsearch_client')

if old in content:
    content = content.replace(old, new)
    open(f, 'w', encoding='utf-8').write(content)
    print('OK: env-aware get_elasticsearch_client')
else:
    idx = content.find('def get_elasticsearch_client')
    print('NOT FOUND, snippet:')
    print(repr(content[idx:idx+250]))
