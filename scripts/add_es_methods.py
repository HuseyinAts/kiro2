f = r'C:\Users\husey\kiro2\backend\core\elasticsearch_client.py'
content = open(f, encoding='utf-8').read()

# Inject missing methods before @property is_connected
INJECTION_POINT = '    @property\n    def is_connected(self) -> bool:'

METHODS = '''    async def turkish_full_text_search(
        self,
        index_name: str,
        query_text: str,
        fields: list = None,
        size: int = 10,
        from_: int = 0,
        filters: dict = None,
    ) -> SearchResult:
        """Turkish full-text search with multi-field support"""
        if not self._client:
            import os
            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            self._client = AsyncElasticsearch([es_url])
        try:
            search_fields = fields or ["question_text^2", "option_a", "option_b",
                                       "option_c", "option_d", "option_e", "explanation"]
            must = [{"multi_match": {"query": query_text, "fields": search_fields,
                                     "type": "best_fields", "fuzziness": "AUTO"}}]
            filter_clauses = []
            if filters:
                for k, v in filters.items():
                    if v is not None:
                        filter_clauses.append({"term": {k: v}})
            query = {"bool": {"must": must, "filter": filter_clauses}} if filter_clauses else {"bool": {"must": must}}
            response = await self._client.search(
                index=index_name, query=query, size=size, from_=from_)
            return SearchResult(
                hits=[{"id": h["_id"], **h["_source"]} for h in response["hits"]["hits"]],
                total=response["hits"]["total"]["value"],
                took=response["took"],
                max_score=response["hits"].get("max_score"),
            )
        except Exception as e:
            logger.error(f"Turkish full-text search failed: {e}")
            return SearchResult(hits=[], total=0, took=0)

    async def get_document(self, index_name: str, doc_id: str) -> dict:
        """Get a single document by ID"""
        if not self._client:
            import os
            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            self._client = AsyncElasticsearch([es_url])
        try:
            response = await self._client.get(index=index_name, id=doc_id)
            return response["_source"] if response["found"] else None
        except Exception as e:
            logger.error(f"Get document failed: {e}")
            return None

    async def bulk_index(self, index_name: str, documents: list) -> dict:
        """Bulk index a list of documents"""
        if not self._client:
            import os
            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            self._client = AsyncElasticsearch([es_url])
        try:
            operations = []
            for doc in documents:
                doc_id = doc.get("id")
                operations.append({"index": {"_index": index_name, "_id": doc_id}})
                operations.append(doc)
            response = await self._client.bulk(operations=operations, refresh=True)
            errors = [i for i in response["items"] if i.get("index", {}).get("error")]
            return {"indexed": len(documents) - len(errors), "errors": len(errors)}
        except Exception as e:
            logger.error(f"Bulk index failed: {e}")
            return {"indexed": 0, "errors": len(documents)}

    @property
    def client(self):
        """Expose raw AsyncElasticsearch client"""
        return self._client

'''

if INJECTION_POINT in content:
    content = content.replace(INJECTION_POINT,
                              METHODS.rstrip('\n').rstrip() + '\n\n' + INJECTION_POINT)
    open(f, 'w', encoding='utf-8').write(content)
    print('OK: added turkish_full_text_search, get_document, bulk_index, client property')
else:
    print('INJECTION_POINT not found:')
    print(repr(content[content.find('is_connected')-30:content.find('is_connected')+50]))
