f = r'C:\Users\husey\kiro2\backend\core\elasticsearch_client.py'
content = open(f, encoding='utf-8').read()

# Add _ensure_connected helper after __init__
old_connect = '    async def connect(self) -> None:'
new_before_connect = '''    async def _ensure_connected(self) -> None:
        """Lazy-init the AsyncElasticsearch client if not already done"""
        if self._client is None:
            import os
            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            if self.hosts == ["http://localhost:9200"] and es_url != "http://localhost:9200":
                self.hosts = [es_url]
            if self.username and self.password:
                self._client = AsyncElasticsearch(
                    self.hosts,
                    basic_auth=(self.username, self.password),
                    verify_certs=self.verify_certs,
                )
            else:
                self._client = AsyncElasticsearch(self.hosts)

    async def connect(self) -> None:'''

if old_connect in content and '_ensure_connected' not in content:
    content = content.replace(old_connect, new_before_connect)
    print('OK: _ensure_connected added')
else:
    print('Already patched or not found')

# Add _ensure_connected() call to create_index, index_document, search, delete_index, get_index_stats
methods_to_patch = [
    ('    async def create_index(\n        self,\n        index_name: str,\n        mappings: Optional[Dict[str, Any]] = None,\n        settings: Optional[Dict[str, Any]] = None,\n    ) -> bool:\n        """Create an index with optional mappings and settings"""\n        try:\n            body = {}',
     '    async def create_index(\n        self,\n        index_name: str,\n        mappings: Optional[Dict[str, Any]] = None,\n        settings: Optional[Dict[str, Any]] = None,\n    ) -> bool:\n        """Create an index with optional mappings and settings"""\n        await self._ensure_connected()\n        try:\n            body = {}'),
    ('    async def index_document(\n        self,\n        index_name: str,\n        document: Dict[str, Any],\n        doc_id: Optional[str] = None,\n    ) -> bool:\n        """Index a document"""\n        try:',
     '    async def index_document(\n        self,\n        index_name: str,\n        document: Dict[str, Any],\n        doc_id: Optional[str] = None,\n    ) -> bool:\n        """Index a document"""\n        await self._ensure_connected()\n        try:'),
    ('    async def search(\n        self,\n        index_name: str,\n        query: Dict[str, Any],\n        size: int = 10,\n        from_: int = 0,\n    ) -> SearchResult:\n        """Search documents"""\n        try:',
     '    async def search(\n        self,\n        index_name: str,\n        query: Dict[str, Any],\n        size: int = 10,\n        from_: int = 0,\n    ) -> SearchResult:\n        """Search documents"""\n        await self._ensure_connected()\n        try:'),
    ('    async def delete_index(self, index_name: str) -> bool:\n        """Delete an index"""\n        try:',
     '    async def delete_index(self, index_name: str) -> bool:\n        """Delete an index"""\n        await self._ensure_connected()\n        try:'),
    ('    async def get_index_stats(self, index_name: str) -> Optional[IndexStats]:\n        """Get index statistics"""\n        try:',
     '    async def get_index_stats(self, index_name: str) -> Optional[IndexStats]:\n        """Get index statistics"""\n        await self._ensure_connected()\n        try:'),
]

for old, new in methods_to_patch:
    if old in content:
        content = content.replace(old, new)
        print(f'Patched: {old.split(chr(10))[0].strip()[:60]}')
    else:
        # Already patched or slightly different
        print(f'Skip (already patched?): {old.split(chr(10))[0].strip()[:60]}')

open(f, 'w', encoding='utf-8').write(content)
print('Done.')
