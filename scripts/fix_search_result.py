f = r'C:\Users\husey\kiro2\backend\core\elasticsearch_client.py'
content = open(f, encoding='utf-8').read()

old = ('@dataclass\n'
       'class SearchResult:\n'
       '    """Elasticsearch search result"""\n'
       '\n'
       '    hits: List[Dict[str, Any]]\n'
       '    total: int\n'
       '    took: int\n'
       '    max_score: Optional[float] = None')

new = ('@dataclass\n'
       'class SearchResult:\n'
       '    """Elasticsearch search result"""\n'
       '\n'
       '    hits: List[Dict[str, Any]]\n'
       '    total: int\n'
       '    took: int\n'
       '    max_score: Optional[float] = None\n'
       '\n'
       '    @property\n'
       '    def results(self):\n'
       '        """Alias for hits — backwards compat"""\n'
       '        return self.hits')

if old in content:
    content = content.replace(old, new)
    open(f, 'w', encoding='utf-8').write(content)
    print('OK: SearchResult.results property added')
else:
    print('NOT FOUND, showing dataclass:')
    idx = content.find('class SearchResult')
    print(repr(content[idx:idx+200]))
